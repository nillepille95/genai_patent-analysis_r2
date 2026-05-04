from __future__ import annotations

from collections import OrderedDict
import re


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "wherein",
    "thereof",
    "that",
    "this",
    "near",
    "only",
}


class TextNormalizer:
    def __init__(self, canonical_terms: dict[str, list[str]] | None = None):
        self.canonical_terms = canonical_terms or {}
        variant_map: dict[str, str] = {}
        for canonical, variants in self.canonical_terms.items():
            canonical_lower = canonical.lower().strip()
            variant_map[canonical_lower] = canonical_lower
            for variant in variants:
                variant_map[variant.lower().strip()] = canonical_lower
        self.variant_map = variant_map
        self.sorted_variants = sorted(self.variant_map, key=len, reverse=True)

    @staticmethod
    def _clean(text: str) -> str:
        normalized = text.lower()
        normalized = re.sub(r"[^a-z0-9\s-]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    @staticmethod
    def _singularize(token: str) -> str:
        if token.endswith("ies") and len(token) > 4:
            return token[:-3] + "y"
        if token.endswith("s") and len(token) > 4 and not token.endswith("ss"):
            return token[:-1]
        return token

    def normalize_phrase(self, text: str) -> str:
        normalized = self._clean(text)
        for variant in self.sorted_variants:
            normalized = normalized.replace(variant, self.variant_map[variant])

        tokens = []
        for token in normalized.split():
            singular = self._singularize(token)
            if singular and singular not in STOPWORDS:
                tokens.append(singular)

        deduplicated = OrderedDict.fromkeys(tokens)
        return " ".join(deduplicated)

    def tokens(self, text: str) -> list[str]:
        return [token for token in self.normalize_phrase(text).split() if token]

    def shared_terms(self, left: str, right: str) -> list[str]:
        left_tokens = set(self.tokens(left))
        right_tokens = set(self.tokens(right))
        shared = sorted(left_tokens & right_tokens)
        return shared

