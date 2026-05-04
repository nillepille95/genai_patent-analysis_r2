from __future__ import annotations

from ..models import MatchCandidate, SuggestionCandidate
from .llm import OpenRouterClient


PLAYBOOK = {
    "conductive heating layer": (
        "Replace the full conductive heating layer with a more localized heating strategy.",
        "The highest overlap comes from a heating layer embedded across the laminate. Shifting to edge heating, detachable de-icing modules, or a narrower zone can reduce direct similarity.",
        "Likely feasible if thermal performance is validated against winter visibility requirements.",
    ),
    "edge busbar": (
        "Re-route power delivery away from the same edge busbar layout.",
        "Using a different conductor placement or segmented power architecture can lower overlap with busbar-specific claims.",
        "Requires electrical and manufacturing review to confirm resistance and assembly impact.",
    ),
    "temperature sensor": (
        "Change the feedback strategy from local temperature sensors to an alternate control signal.",
        "If the patent depends on sensor-driven closed-loop control, using indirect thermal estimation or a different sensor position may reduce similarity.",
        "Feasible for a prototype, but controls tuning would need validation.",
    ),
    "sensor mounting pad": (
        "Move away from a fixed pad geometry by testing a detachable carrier or alternate reference structure.",
        "The overlap centers on the mounting pad plus adhesive and rib alignment combination. A different support architecture may reduce claim overlap.",
        "Should be reviewed together with optical alignment and serviceability constraints.",
    ),
    "wedge interlayer": (
        "Explore optical correction without the same wedge interlayer construction.",
        "A different correction strategy, zone layout, or laminate stack may preserve HUD performance while avoiding the same feature combination.",
        "Feasibility depends on optical simulation and lamination process limits.",
    ),
    "infrared reflective coating": (
        "Test a different thermal management layer placement or coating stack.",
        "Moving the reflective function to another layer or using a different stack design can reduce similarity to coating-specific claims.",
        "Would need coating durability and optical quality checks.",
    ),
}


class SuggestionService:
    def __init__(self, llm_client: OpenRouterClient | None = None):
        self.llm_client = llm_client

    def _heuristic_suggestions(
        self,
        patent_title: str,
        risk_level: str,
        matches: list[MatchCandidate],
    ) -> list[SuggestionCandidate]:
        suggestions: list[SuggestionCandidate] = []
        seen: set[str] = set()

        for match in matches:
            normalized_text = match.patent_feature_text.lower()
            for keyword, (suggestion_text, rationale, feasibility_note) in PLAYBOOK.items():
                if keyword not in normalized_text:
                    continue
                if suggestion_text in seen:
                    continue
                seen.add(suggestion_text)
                suggestions.append(
                    SuggestionCandidate(
                        suggestion_text=suggestion_text,
                        rationale=f"{rationale} Triggered by overlap with patent '{patent_title}'.",
                        feasibility_note=feasibility_note,
                    )
                )
                break

        if suggestions:
            return suggestions[:3]

        fallback = SuggestionCandidate(
            suggestion_text="Differentiate the highest-overlap feature combination before detailed engineering freeze.",
            rationale=(
                f"The current overlap profile is rated {risk_level.lower()} risk. "
                "The safest next move is to alter material choice, placement, activation logic, or assembly sequence "
                "for the strongest matched features."
            ),
            feasibility_note="Use this as a review action list with engineering and IP stakeholders.",
        )
        return [fallback]

    def build_suggestions(
        self,
        design_name: str,
        patent_title: str,
        risk_level: str,
        matches: list[MatchCandidate],
    ) -> list[SuggestionCandidate]:
        if self.llm_client is not None and self.llm_client.is_configured():
            prompt = (
                f"Design name: {design_name}\n"
                f"Patent title: {patent_title}\n"
                f"Risk level: {risk_level}\n"
                "Top overlaps:\n"
                + "\n".join(
                    f"- Design feature: {match.design_feature} | Patent feature: {match.patent_feature_text} | Evidence: {match.evidence}"
                    for match in matches[:4]
                )
            )
            llm_suggestions = self.llm_client.generate_suggestions(prompt)
            if llm_suggestions:
                return llm_suggestions

        return self._heuristic_suggestions(patent_title, risk_level, matches)

