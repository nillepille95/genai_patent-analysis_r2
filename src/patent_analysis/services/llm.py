from __future__ import annotations

import json
import re
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import OpenRouterConfig
from ..models import SuggestionCandidate


class OpenRouterClient:
    def __init__(self, config: OpenRouterConfig):
        self.config = config
        self.last_error = ""

    @staticmethod
    def _build_ssl_context():
        try:
            import certifi
        except ImportError:
            return None
        return ssl.create_default_context(cafile=certifi.where())

    def is_configured(self) -> bool:
        return (
            self.config.enabled
            and bool(self.config.api_key)
            and "replace-with" not in self.config.api_key.lower()
            and bool(self.config.model)
            and "replace-with" not in self.config.model.lower()
        )

    def _extract_json_string(self, content: str) -> str:
        stripped = content.strip()
        if stripped.startswith("```"):
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL)
            if match:
                return match.group(1).strip()
        return stripped

    def _post_chat_completion(self, payload: dict) -> str:
        if not self.is_configured():
            self.last_error = "OpenRouter is not configured."
            return ""

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
            ssl_context = self._build_ssl_context()
            urlopen_kwargs = {"timeout": self.config.request_timeout_seconds}
            if ssl_context is not None:
                urlopen_kwargs["context"] = ssl_context
            with urlopen(request, **urlopen_kwargs) as response:
                raw_response = response.read().decode("utf-8")
        except HTTPError as exc:
            error_body = ""
            if exc.fp is not None:
                error_body = exc.fp.read().decode("utf-8", errors="ignore")
            self.last_error = f"HTTP {exc.code}: {error_body or exc.reason}"
            return ""
        except (URLError, TimeoutError) as exc:
            self.last_error = str(exc)
            return ""

        try:
            parsed_payload = json.loads(raw_response)
            content = parsed_payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            self.last_error = f"Unexpected response format: {exc}"
            return ""

        self.last_error = ""
        return str(content)

    def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        return self._post_chat_completion(payload)

    def generate_suggestions(self, prompt: str) -> list[SuggestionCandidate]:
        content = self.generate_text(
            system_prompt=(
                "You generate structured patent design-around suggestions. "
                "Return only a JSON array with up to three objects. "
                "Each object must contain suggestion_text, rationale, and feasibility_note."
            ),
            user_prompt=prompt,
            temperature=0.2,
        )
        if not content:
            return []

        try:
            suggestions = json.loads(self._extract_json_string(content))
        except json.JSONDecodeError as exc:
            self.last_error = f"Could not parse suggestion JSON: {exc}"
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
