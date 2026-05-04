from __future__ import annotations

from collections import Counter

from ..models import InnovationInsightCandidate


THEME_BUCKETS = {
    "thermal control": {"heating", "conductive", "temperature", "busbar", "deicing"},
    "sensor integration": {"sensor", "mounting", "adhesive", "alignment", "bracket"},
    "optical correction": {"wedge", "display", "optical", "viewing", "zone"},
    "acoustic performance": {"acoustic", "damping", "noise"},
    "coating stack": {"coating", "infrared", "reflective"},
}


class InnovationService:
    def analyze(self, patents_with_features: list[dict]) -> InnovationInsightCandidate:
        patent_count = len(patents_with_features)
        if patent_count == 0:
            return InnovationInsightCandidate(
                scope="No patents loaded",
                pattern_summary="No innovation insight can be generated until patents are loaded.",
                gap_summary="No feature patterns available yet.",
                recommendation="Load at least two patents to begin cross-patent analysis.",
            )

        feature_counter: Counter[str] = Counter()
        bucket_counter: Counter[str] = Counter()

        for patent in patents_with_features:
            patent_tokens: set[str] = set()
            for feature in patent.get("features", []):
                normalized = str(feature.get("normalized_feature", "")).strip()
                if not normalized:
                    continue
                feature_counter[normalized] += 1
                patent_tokens.update(normalized.split())

            for bucket_name, bucket_terms in THEME_BUCKETS.items():
                if patent_tokens & bucket_terms:
                    bucket_counter[bucket_name] += 1

        recurring_features = [
            feature
            for feature, count in feature_counter.most_common(5)
            if count >= 2
        ]

        whitespace_themes = [
            bucket_name
            for bucket_name in THEME_BUCKETS
            if bucket_counter[bucket_name] == 0
        ]

        recurring_summary = (
            ", ".join(recurring_features)
            if recurring_features
            else "No single feature has repeated across multiple patents yet."
        )
        bucket_summary = ", ".join(
            f"{bucket} ({count}/{patent_count} patents)"
            for bucket, count in bucket_counter.most_common()
        ) or "No strong theme buckets detected."

        if whitespace_themes:
            gap_summary = (
                "Underrepresented opportunity themes: " + ", ".join(whitespace_themes) + "."
            )
            recommendation = (
                "Investigate whether one whitespace theme can be combined with an existing recurring theme "
                "to create a differentiated glazing concept."
            )
        else:
            gap_summary = (
                "All current theme buckets are represented at least once; the next opportunity is likely a new combination "
                "rather than a completely empty space."
            )
            recommendation = (
                "Prioritize feature combinations that bridge thermal control, optical correction, or service-friendly sensor integration."
            )

        return InnovationInsightCandidate(
            scope=f"{patent_count} patent records",
            pattern_summary=(
                f"Recurring normalized features: {recurring_summary}. Theme coverage: {bucket_summary}."
            ),
            gap_summary=gap_summary,
            recommendation=recommendation,
            recurring_features=recurring_features,
            whitespace_themes=whitespace_themes,
        )

