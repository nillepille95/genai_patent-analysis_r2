from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import OpenRouterConfig
from ..models import SuggestionCandidate


class OpenRouterClient:
    def __init__(self, config: OpenRouterConfig):
        self.config = config

    def is_configured(self) -> bool:
        return (
            self.config.enabled
            and bool(self.config.api_key)
            and "replace-with" not in self.config.api_key.lower()
            and bool(self.config.model)
            and "replace-with" not in self.config.model.lower()
        )

    def generate_suggestions(self, prompt: str) -> list[SuggestionCandidate]:
        if not self.is_configured():
            return []

        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You generate structured patent design-around suggestions. "
                        "Return only a JSON array with up to three objects. "
                        "Each object must contain suggestion_text, rationale, and feasibility_note."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        request = Request(
            self.config.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.config.site_url,
                "X-Title": self.config.site_name,
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.config.request_timeout_seconds) as response:
                raw_response = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError):
            return []

        try:
            payload = json.loads(raw_response)
            content = payload["choices"][0]["message"]["content"]
            suggestions = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            return []

        results: list[SuggestionCandidate] = []
        for item in suggestions:
            if not isinstance(item, dict):
                continue
            suggestion_text = str(item.get("suggestion_text", "")).strip()
            rationale = str(item.get("rationale", "")).strip()
            feasibility_note = str(item.get("feasibility_note", "")).strip()
            if not suggestion_text or not rationale:
                continue
            results.append(
                SuggestionCandidate(
                    suggestion_text=suggestion_text,
                    rationale=rationale,
                    feasibility_note=feasibility_note or "Engineering review required.",
                )
            )
        return results[:3]

