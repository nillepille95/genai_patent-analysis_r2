from __future__ import annotations

import json

from ..models import PatentDocumentInput, ProductDesignInput, SourceBundle
from .base import PatentSource


class DemoJsonPatentSource(PatentSource):
    name = "demo_json"

    def __init__(self, patents_path, designs_path):
        self.patents_path = patents_path
        self.designs_path = designs_path

    def load_bundle(self) -> SourceBundle:
        with self.patents_path.open("r", encoding="utf-8") as handle:
            patent_items = json.load(handle)
        with self.designs_path.open("r", encoding="utf-8") as handle:
            design_items = json.load(handle)

        patents = [
            PatentDocumentInput(
                title=item["title"],
                patent_number=item.get("patent_number", ""),
                source=item.get("source", "demo"),
                partner_domain=item.get("partner_domain", "general"),
                sections=item.get("sections", {}),
            )
            for item in patent_items
        ]

        designs = [
            ProductDesignInput(
                name=item["name"],
                raw_description=item["raw_description"],
            )
            for item in design_items
        ]

        return SourceBundle(patents=patents, product_designs=designs)

