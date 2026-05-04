from __future__ import annotations

import re

from ..config import Settings
from ..models import FeatureCandidate
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
    def __init__(self, settings: Settings, normalizer: TextNormalizer | None = None):
        self.settings = settings
        self.normalizer = normalizer or TextNormalizer(settings.analysis.canonical_terms)

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

    def extract_section_features(self, section_text: str, section_type: str) -> list[FeatureCandidate]:
        candidates: list[FeatureCandidate] = []
        seen_normalized: set[str] = set()

        for fragment in self._split_candidates(section_text):
            raw_feature = self._strip_boilerplate(fragment)
            if not raw_feature:
                continue
            normalized_feature = self.normalizer.normalize_phrase(raw_feature)
            token_count = len(normalized_feature.split())
            if token_count < self.settings.analysis.minimum_feature_tokens:
                continue
            if normalized_feature in seen_normalized:
                continue

            confidence = self._score_candidate(raw_feature, section_type)
            if confidence < self.settings.analysis.minimum_feature_confidence:
                continue

            seen_normalized.add(normalized_feature)
            candidates.append(
                FeatureCandidate(
                    raw_feature_text=raw_feature,
                    normalized_feature=normalized_feature,
                    confidence=round(confidence, 2),
                    evidence_span=fragment.strip(),
                )
            )

        return candidates

    def extract_product_features(self, raw_description: str) -> list[FeatureCandidate]:
        return self.extract_section_features(raw_description, "product")

