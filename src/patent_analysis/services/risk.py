from __future__ import annotations

from difflib import SequenceMatcher

from ..config import Settings
from ..models import MatchCandidate
from .normalization import TextNormalizer


class RiskAnalyzer:
    def __init__(self, settings: Settings, normalizer: TextNormalizer | None = None):
        self.settings = settings
        self.normalizer = normalizer or TextNormalizer(settings.analysis.canonical_terms)

    def _similarity(self, left: str, right: str) -> tuple[float, list[str], float]:
        left_tokens = set(self.normalizer.tokens(left))
        right_tokens = set(self.normalizer.tokens(right))
        if not left_tokens or not right_tokens:
            return 0.0, [], 0.0

        shared = sorted(left_tokens & right_tokens)
        union = left_tokens | right_tokens
        jaccard = len(shared) / len(union)
        ratio = SequenceMatcher(None, left, right).ratio()
        token_coverage = max(
            len(shared) / len(left_tokens),
            len(shared) / len(right_tokens),
        )
        containment = 1.0 if left in right or right in left else 0.0
        score = (
            (0.35 * jaccard)
            + (0.35 * token_coverage)
            + (0.20 * ratio)
            + (0.10 * containment)
        )
        return score, shared, jaccard

    @staticmethod
    def _match_type(score: float, jaccard: float, shared_terms: list[str], left: str, right: str) -> str:
        if left == right or left in right or right in left or jaccard >= 0.82:
            return "direct"
        if score >= 0.5 and len(shared_terms) >= 2:
            return "semantic"
        return "partial"

    def analyze(
        self,
        design_name: str,
        patent_title: str,
        design_features: list[dict],
        patent_features: list[dict],
    ) -> dict:
        best_matches: list[MatchCandidate] = []
        scores: list[float] = []

        for design_feature in design_features:
            best_match: MatchCandidate | None = None
            best_score = 0.0

            for patent_feature in patent_features:
                score, shared_terms, jaccard = self._similarity(
                    design_feature["normalized_feature"],
                    patent_feature["normalized_feature"],
                )
                if score < 0.32:
                    continue
                if score <= best_score:
                    continue

                evidence = (
                    f"Shared terms: {', '.join(shared_terms) if shared_terms else 'none'}. "
                    f"Patent evidence: {patent_feature['evidence_span']}"
                )
                best_match = MatchCandidate(
                    design_feature=design_feature["raw_feature_text"],
                    patent_feature_id=int(patent_feature["id"]),
                    patent_feature_text=patent_feature["raw_feature_text"],
                    match_type=self._match_type(
                        score,
                        jaccard,
                        shared_terms,
                        design_feature["normalized_feature"],
                        patent_feature["normalized_feature"],
                    ),
                    match_score=round(score * 100, 1),
                    evidence=evidence,
                )
                best_score = score

            scores.append(best_score)
            if best_match is not None:
                best_matches.append(best_match)

        best_matches.sort(key=lambda item: item.match_score, reverse=True)
        matched_count = len(best_matches)
        total_design_features = max(len(design_features), 1)
        coverage = matched_count / total_design_features
        average_score = sum(scores) / total_design_features
        risk_score = round(((0.75 * average_score) + (0.25 * coverage)) * 100, 1)

        if risk_score >= self.settings.analysis.high_risk_threshold:
            risk_level = "High"
        elif risk_score >= self.settings.analysis.medium_risk_threshold:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        top_matches = best_matches[:3]
        if top_matches:
            highlights = "; ".join(
                f"{match.design_feature} -> {match.patent_feature_text}"
                for match in top_matches
            )
        else:
            highlights = "No meaningful overlap features were detected."

        reasoning_summary = (
            f"{matched_count} of {total_design_features} design features in {design_name} overlap "
            f"with patent features from {patent_title}. Strongest evidence: {highlights}"
        )

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "reasoning_summary": reasoning_summary,
            "matches": best_matches[: self.settings.analysis.max_feature_matches],
        }
