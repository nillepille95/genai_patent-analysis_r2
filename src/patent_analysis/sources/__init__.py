from __future__ import annotations

from ..config import Settings
from .demo import DemoJsonPatentSource
from .directory import DirectoryPatentSource


def build_source_registry(settings: Settings) -> dict[str, object]:
    return {
        "demo_json": DemoJsonPatentSource(
            settings.sources.demo_patents_path,
            settings.sources.demo_designs_path,
        ),
        "directory": DirectoryPatentSource(settings.sources.live_patent_directory),
    }

