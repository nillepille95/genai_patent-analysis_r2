from __future__ import annotations

import re

from ..config import Settings
from ..models import FeatureCandidate
from .llm import OpenRouterClient
from .normalization import TextNormalizer


DOMAIN_HINTS = {
    "glass",
    "windshield",
    "glazing",
    "interlayer",
    "coating",
    "sensor",
    "controller",
    "adhesive",
    "busbar",
    "acoustic",
    "heating",
    "display",
}


class FeatureExtractor:
    def __init__(
        self,
        settings: Settings,
        normalizer: TextNormalizer | None = None,
        llm_client: OpenRouterClient | None = None,
    ):
        self.settings = settings
        self.normalizer = normalizer or TextNormalizer(settings.analysis.canonical_terms)
        self.llm_client = llm_client

    @staticmethod
    def _strip_boilerplate(text: str) -> str:
        cleaned = text.strip()
        cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
        cleaned = re.sub(r"^(wherein|and|or)\s+", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(
            r"^(a|an|the)\s+[^,.]{0,80}?\b(comprising|including|having|contains?)\b\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        return cleaned.strip(" ,.-")

    @staticmethod
    def _split_candidates(text: str) -> list[str]:
        normalized = text.replace("\r", "\n")
        normalized = re.sub(r"(?<!\w)(\d+)\.\s+", r"\n\1. ", normalized)
        fragments = re.split(r"[;\n]+", normalized)
        candidates: list[str] = []
        for fragment in fragments:
            sub_fragments = re.split(r",\s+", fragment)
            candidates.extend(sub_fragments)
        return [candidate.strip() for candidate in candidates if candidate.strip()]

    def _score_candidate(self, raw_text: str, section_type: str) -> float:
        base = 0.55 if section_type == "claims" else 0.45
        lowered = raw_text.lower()
        if any(trigger in lowered for trigger in ("configured to", "comprising", "including", "having")):
            base += 0.1
        if any(hint in lowered for hint in DOMAIN_HINTS):
            base += 0.08
        token_count = len(raw_text.split())
        if 3 <= token_count <= 14:
            base += 0.05
        return min(base, 0.95)

    def _finalize_candidates(
        self,
        raw_candidates: list[dict],
        extraction_method: str,
        extraction_notes: str,
        section_type: str,
    ) -> list[FeatureCandidate]:
        candidates: list[FeatureCandidate] = []
        seen_normalized: set[str] = set()

        for item in raw_candidates:
            raw_feature = str(item.get("raw_feature_text", "")).strip()
            evidence_span = str(item.get("evidence_span", raw_feature)).strip()
            if not raw_feature:
                continue

            normalized_feature = self.normalizer.normalize_phrase(raw_feature)
            token_count = len(normalized_feature.split())
            if token_count < self.settings.analysis.minimum_feature_tokens:
                continue
            if normalized_feature in seen_normalized:
                continue

            candidate_confidence = item.get("confidence")
            if candidate_confidence is None:
                confidence = self._score_candidate(raw_feature, section_type)
            else:
                try:
                    confidence = float(candidate_confidence)
                except (TypeError, ValueError):
                    confidence = self._score_candidate(raw_feature, section_type)
            confidence = max(0.0, min(confidence, 0.99))
            if confidence < self.settings.analysis.minimum_feature_confidence:
                continue

            seen_normalized.add(normalized_feature)
            candidates.append(
                FeatureCandidate(
                    raw_feature_text=raw_feature,
                    normalized_feature=normalized_feature,
                    confidence=round(confidence, 2),
                    evidence_span=evidence_span or raw_feature,
                    extraction_method=extraction_method,
                    extraction_notes=extraction_notes,
                )
            )

        return candidates

    def extract_section_features(self, section_text: str, section_type: str) -> list[FeatureCandidate]:
        raw_candidates: list[dict] = []
        for fragment in self._split_candidates(section_text):
            raw_feature = self._strip_boilerplate(fragment)
            raw_candidates.append(
                {
                    "raw_feature_text": raw_feature,
                    "evidence_span": fragment.strip(),
                    "confidence": self._score_candidate(raw_feature, section_type)
                    if raw_feature
                    else None,
                }
            )
        return self._finalize_candidates(
            raw_candidates=raw_candidates,
            extraction_method="rule",
            extraction_notes=f"section={section_type}",
            section_type=section_type,
        )

    def _extract_patent_section_features_with_llm(
        self, section_text: str, section_type: str
    ) -> list[FeatureCandidate]:
        if self.llm_client is None or not self.llm_client.is_configured():
            return []

        schema = {
            "type": "object",
            "properties": {
                "features": {
                    "type": "array",
                    "maxItems": self.settings.extraction.max_ai_features_per_section,
                    "items": {
                        "type": "object",
                        "properties": {
                            "raw_feature_text": {
                                "type": "string",
                                "description": "Concise technical feature phrase grounded in the patent section.",
                            },
                            "evidence_span": {
                                "type": "string",
                                "description": "Short exact evidence copied from the provided section.",
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Confidence between 0 and 1.",
                            },
                        },
                        "required": ["raw_feature_text", "evidence_span", "confidence"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["features"],
            "additionalProperties": False,
        }
        payload = self.llm_client.generate_json(
            schema_name="patent_feature_extraction",
            schema=schema,
            system_prompt=(
                "You extract technical patent features from one patent section. "
                "Only include concrete, product-relevant technical elements explicitly supported by the text. "
                "Avoid legal boilerplate, claim numbering, generic verbs, and repeated near-duplicates. "
                "Evidence spans must be copied exactly from the section."
            ),
            user_prompt=(
                f"Section type: {section_type}\n"
                "Extract technical features from the following patent section.\n"
                f"Section text:\n{section_text}"
            ),
            temperature=0.1,
        )
        if not isinstance(payload, dict):
            return []

        raw_features = payload.get("features", [])
        if not isinstance(raw_features, list):
            return []

        return self._finalize_candidates(
            raw_candidates=raw_features,
            extraction_method="openrouter",
            extraction_notes=f"model={self.llm_client.config.model}; section={section_type}",
            section_type=section_type,
        )

    def extract_patent_section_features(
        self, section_text: str, section_type: str
    ) -> list[FeatureCandidate]:
        section_type = section_type.strip().lower()
        use_ai = (
            self.settings.extraction.enable_ai_patent_extraction
            and section_type in self.settings.extraction.ai_patent_sections
        )
        if use_ai:
            llm_features = self._extract_patent_section_features_with_llm(
                section_text, section_type
            )
            if llm_features:
                return llm_features
            if not self.settings.extraction.fallback_to_rules:
                return []

        return self.extract_section_features(section_text, section_type)

    def extract_product_features(self, raw_description: str) -> list[FeatureCandidate]:
        return self.extract_section_features(raw_description, "product")
