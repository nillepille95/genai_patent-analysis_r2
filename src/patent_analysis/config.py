from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "config"


@dataclass(slots=True)
class AppConfig:
    name: str
    host: str
    port: int
    auto_init_db: bool
    auto_seed_demo: bool
    default_patent_source: str


@dataclass(slots=True)
class DatabaseConfig:
    path: Path


@dataclass(slots=True)
class AnalysisConfig:
    minimum_feature_tokens: int
    minimum_feature_confidence: float
    medium_risk_threshold: float
    high_risk_threshold: float
    max_feature_matches: int
    canonical_terms: dict[str, list[str]] = field(default_factory=dict)


@dataclass(slots=True)
class OpenRouterConfig:
    enabled: bool
    api_key: str
    model: str
    base_url: str
    site_url: str
    site_name: str
    request_timeout_seconds: int


@dataclass(slots=True)
class SourcesConfig:
    demo_patents_path: Path
    demo_designs_path: Path
    live_patent_directory: Path


@dataclass(slots=True)
class Settings:
    root_dir: Path
    app: AppConfig
    database: DatabaseConfig
    analysis: AnalysisConfig
    openrouter: OpenRouterConfig
    sources: SourcesConfig
    config_path: Path


def resolve_project_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return ROOT_DIR / path


def _pick_config_path(explicit_path: str | Path | None = None) -> Path:
    if explicit_path is not None:
        return resolve_project_path(explicit_path)

    candidates = [
        CONFIG_DIR / "settings.local.toml",
        CONFIG_DIR / "settings.toml",
        CONFIG_DIR / "settings.example.toml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No settings TOML file found in config/.")


def load_settings(explicit_path: str | Path | None = None) -> Settings:
    config_path = _pick_config_path(explicit_path)
    with config_path.open("rb") as handle:
        payload = tomllib.load(handle)

    app_payload = payload.get("app", {})
    database_payload = payload.get("database", {})
    analysis_payload = payload.get("analysis", {})
    openrouter_payload = payload.get("openrouter", {})
    sources_payload = payload.get("sources", {})

    canonical_terms: dict[str, list[str]] = {}
    for item in analysis_payload.get("canonical_terms", []):
        canonical = item.get("canonical", "").strip().lower()
        if not canonical:
            continue
        variants = [
            variant.strip().lower()
            for variant in item.get("variants", [])
            if variant and variant.strip()
        ]
        canonical_terms[canonical] = variants

    return Settings(
        root_dir=ROOT_DIR,
        config_path=config_path,
        app=AppConfig(
            name=app_payload.get("name", "Patent Analysis Prototype"),
            host=app_payload.get("host", "127.0.0.1"),
            port=int(app_payload.get("port", 8000)),
            auto_init_db=bool(app_payload.get("auto_init_db", True)),
            auto_seed_demo=bool(app_payload.get("auto_seed_demo", True)),
            default_patent_source=app_payload.get("default_patent_source", "demo_json"),
        ),
        database=DatabaseConfig(
            path=resolve_project_path(database_payload.get("path", "data/patent_analysis.sqlite3"))
        ),
        analysis=AnalysisConfig(
            minimum_feature_tokens=int(analysis_payload.get("minimum_feature_tokens", 3)),
            minimum_feature_confidence=float(analysis_payload.get("minimum_feature_confidence", 0.4)),
            medium_risk_threshold=float(analysis_payload.get("medium_risk_threshold", 35.0)),
            high_risk_threshold=float(analysis_payload.get("high_risk_threshold", 65.0)),
            max_feature_matches=int(analysis_payload.get("max_feature_matches", 6)),
            canonical_terms=canonical_terms,
        ),
        openrouter=OpenRouterConfig(
            enabled=bool(openrouter_payload.get("enabled", False)),
            api_key=openrouter_payload.get("api_key", "").strip(),
            model=openrouter_payload.get("model", "").strip(),
            base_url=openrouter_payload.get(
                "base_url", "https://openrouter.ai/api/v1/chat/completions"
            ).strip(),
            site_url=openrouter_payload.get("site_url", "http://localhost:8000").strip(),
            site_name=openrouter_payload.get("site_name", "Patent Analysis Prototype").strip(),
            request_timeout_seconds=int(openrouter_payload.get("request_timeout_seconds", 30)),
        ),
        sources=SourcesConfig(
            demo_patents_path=resolve_project_path(
                sources_payload.get("demo_patents_path", "data/demo_patents.json")
            ),
            demo_designs_path=resolve_project_path(
                sources_payload.get("demo_designs_path", "data/demo_designs.json")
            ),
            live_patent_directory=resolve_project_path(
                sources_payload.get("live_patent_directory", "data/live_patents")
            ),
        ),
    )

