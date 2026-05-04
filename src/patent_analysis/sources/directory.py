from __future__ import annotations

from pathlib import Path
import json
import re

from ..models import PatentDocumentInput, SourceBundle
from .base import PatentSource


class DirectoryPatentSource(PatentSource):
    name = "directory"

    def __init__(self, directory: Path):
        self.directory = directory

    @staticmethod
    def _parse_marked_sections(raw_text: str) -> dict[str, str]:
        sections = {"abstract": "", "claims": "", "description": ""}
        current = "description"
        for line in raw_text.splitlines():
            lowered = line.strip().lower()
            if re.fullmatch(r"(#+\s*)?abstract:?", lowered):
                current = "abstract"
                continue
            if re.fullmatch(r"(#+\s*)?claims:?", lowered):
                current = "claims"
                continue
            if re.fullmatch(r"(#+\s*)?description:?", lowered):
                current = "description"
                continue
            sections[current] += line + "\n"
        return {key: value.strip() for key, value in sections.items() if value.strip()}

    def _load_json_file(self, path: Path) -> list[PatentDocumentInput]:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if isinstance(payload, dict):
            payload = [payload]

        documents: list[PatentDocumentInput] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            documents.append(
                PatentDocumentInput(
                    title=item.get("title", path.stem),
                    patent_number=item.get("patent_number", path.stem),
                    source=item.get("source", "directory-import"),
                    partner_domain=item.get("partner_domain", "unspecified"),
                    sections=item.get("sections", {}),
                )
            )
        return documents

    def _load_text_file(self, path: Path) -> PatentDocumentInput:
        raw_text = path.read_text(encoding="utf-8")
        sections = self._parse_marked_sections(raw_text)
        if not sections:
            sections = {"description": raw_text}
        return PatentDocumentInput(
            title=path.stem.replace("_", " ").replace("-", " ").title(),
            patent_number=path.stem,
            source="directory-import",
            partner_domain="unspecified",
            sections=sections,
        )

    def load_bundle(self) -> SourceBundle:
        self.directory.mkdir(parents=True, exist_ok=True)
        patents: list[PatentDocumentInput] = []
        for path in sorted(self.directory.iterdir()):
            if path.is_dir():
                continue
            if path.suffix.lower() == ".json":
                patents.extend(self._load_json_file(path))
            elif path.suffix.lower() in {".txt", ".md"}:
                patents.append(self._load_text_file(path))
        return SourceBundle(patents=patents, product_designs=[])

