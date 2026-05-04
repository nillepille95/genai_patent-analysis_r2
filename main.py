from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from patent_analysis.bootstrap import bootstrap_demo_data
from patent_analysis.config import load_settings
from patent_analysis.database import initialize_database
from patent_analysis.repository import PatentAnalysisRepository
from patent_analysis.services.extraction import FeatureExtractor
from patent_analysis.services.llm import OpenRouterClient
from patent_analysis.services.normalization import TextNormalizer


def create_app_entry():
    from patent_analysis.app import create_app

    return create_app(load_settings())


def _build_runtime():
    settings = load_settings()
    initialize_database(settings.database.path)
    repository = PatentAnalysisRepository(settings.database.path)
    normalizer = TextNormalizer(settings.analysis.canonical_terms)
    llm_client = OpenRouterClient(settings.openrouter)
    extractor = FeatureExtractor(settings, normalizer, llm_client)
    return settings, repository, extractor


def run_server(reload: bool = False) -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "Missing web dependencies. Install them with: pip install -r requirements.txt"
        ) from exc

    settings = load_settings()
    uvicorn.run(
        "main:create_app_entry",
        host=settings.app.host,
        port=settings.app.port,
        factory=True,
        reload=reload,
    )


def init_db() -> None:
    settings = load_settings()
    initialize_database(settings.database.path)
    print(f"Database initialized at {settings.database.path}")


def seed_demo() -> None:
    settings, repository, extractor = _build_runtime()
    bootstrap_demo_data(settings, repository, extractor)
    print("Demo patents and product designs are available.")


def test_openrouter() -> None:
    settings = load_settings()

    client = OpenRouterClient(settings.openrouter)
    if not client.is_configured():
        raise SystemExit(
            "OpenRouter is not configured. Check config/settings.local.toml and set enabled=true with a valid key and model."
        )

    response = client.generate_text(
        system_prompt=(
            "You are validating a patent-analysis prototype. "
            "Reply in one short paragraph and mention whether the request reached the model."
        ),
        user_prompt=(
            "Confirm the live OpenRouter integration is working for the patent analysis project. "
            "Mention the configured model identifier exactly once."
        ),
        temperature=0.1,
    )
    if not response:
        error_message = client.last_error or "Unknown OpenRouter error."
        raise SystemExit(f"OpenRouter test failed: {error_message}")

    print("OpenRouter test succeeded.")
    print(f"Model: {settings.openrouter.model}")
    print(response)


def test_patent_extraction() -> None:
    settings = load_settings()
    normalizer = TextNormalizer(settings.analysis.canonical_terms)
    llm_client = OpenRouterClient(settings.openrouter)
    extractor = FeatureExtractor(settings, normalizer, llm_client)

    sample_claims = (
        "1. A laminated vehicle windshield comprising an outer glass ply, an inner glass ply, "
        "a transparent conductive heating layer embedded adjacent to the polymer interlayer, "
        "edge busbars electrically coupled to the conductive heating layer, and a controller "
        "configured to energize only a predefined wiper-rest heating zone."
    )
    features = extractor.extract_patent_section_features(sample_claims, "claims")
    if not features:
        raise SystemExit("No patent features were extracted.")

    print("Patent extraction test succeeded.")
    for feature in features:
        print(
            f"- {feature.raw_feature_text} | normalized={feature.normalized_feature} "
            f"| confidence={feature.confidence} | method={feature.extraction_method} "
            f"| trace={feature.extraction_notes}"
        )


def reextract_patents() -> None:
    settings, repository, extractor = _build_runtime()
    patents = repository.list_patents(limit=None)
    updated_patents = 0
    updated_features = 0

    for patent in patents:
        detail = repository.get_patent_detail(int(patent["id"]))
        if detail is None:
            continue
        extracted_features_by_section = {
            section["section_type"]: extractor.extract_patent_section_features(
                section["section_text"], section["section_type"]
            )
            for section in detail["sections"]
            if str(section["section_text"]).strip()
        }
        updated_features += repository.replace_patent_features(
            int(patent["id"]), extracted_features_by_section
        )
        updated_patents += 1

    print(
        f"Re-extracted features for {updated_patents} patents using the current extraction settings. "
        f"Updated feature rows: {updated_features}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patent analysis prototype runner")
    subcommands = parser.add_subparsers(dest="command")

    runserver = subcommands.add_parser("runserver", help="Start the web application")
    runserver.add_argument("--reload", action="store_true", help="Enable auto reload")

    subcommands.add_parser("init-db", help="Create the SQLite schema")
    subcommands.add_parser("seed-demo", help="Load the synthetic demo dataset")
    subcommands.add_parser("test-openrouter", help="Run a live OpenRouter connectivity test")
    subcommands.add_parser(
        "test-patent-extraction",
        help="Run a patent feature extraction probe using the current extraction settings",
    )
    subcommands.add_parser(
        "reextract-patents",
        help="Rebuild stored patent features using the current extraction settings",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    command = args.command or "runserver"

    if command == "runserver":
        run_server(reload=getattr(args, "reload", False))
    elif command == "init-db":
        init_db()
    elif command == "seed-demo":
        seed_demo()
    elif command == "test-openrouter":
        test_openrouter()
    elif command == "test-patent-extraction":
        test_patent_extraction()
    elif command == "reextract-patents":
        reextract_patents()
    else:
        raise SystemExit(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
