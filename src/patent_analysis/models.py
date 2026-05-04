from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class FeatureCandidate:
    raw_feature_text: str
    normalized_feature: str
    confidence: float
    evidence_span: str
    extraction_method: str = "rule"
    extraction_notes: str = ""


@dataclass(slots=True)
class PatentDocumentInput:
    title: str
    patent_number: str
    source: str
    partner_domain: str
    sections: dict[str, str]


@dataclass(slots=True)
class ProductDesignInput:
    name: str
    raw_description: str


@dataclass(slots=True)
class MatchCandidate:
    design_feature: str
    patent_feature_id: int
    patent_feature_text: str
    match_type: str
    match_score: float
    evidence: str


@dataclass(slots=True)
class SuggestionCandidate:
    suggestion_text: str
    rationale: str
    feasibility_note: str


@dataclass(slots=True)
class InnovationInsightCandidate:
    scope: str
    pattern_summary: str
    gap_summary: str
    recommendation: str
    recurring_features: list[str] = field(default_factory=list)
    whitespace_themes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SourceBundle:
    patents: list[PatentDocumentInput] = field(default_factory=list)
    product_designs: list[ProductDesignInput] = field(default_factory=list)
