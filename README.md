# Patent Analysis Prototype

This repository now contains the first working scaffold for the Fuyao patent analysis project described in the `readme/` folder. The implementation focuses on the documented Phase 1 and Phase 2 requirements first:

- patent ingestion and section splitting,
- technical feature extraction with evidence traces,
- structured storage in SQLite,
- product design input and feature normalization,
- explainable patent-to-product risk analysis,
- a localhost web UI for browsing, review, and demo runs.

## Why this stack

- `FastAPI`: lightweight Python web framework for local development and later private deployment.
- `Jinja2` templates: simple server-rendered frontend that runs well on localhost and can be hosted behind a private reverse proxy later.
- `SQLite` now: fast, file-based prototype database with a clean path to PostgreSQL later.
- Rule-based extraction and scoring remain available as a fallback path for stability and explainability.
- `OpenRouter` integration is now live for AI-assisted patent feature extraction and design-around suggestions when enabled in local config.

## Project structure

```text
config/                  Editable settings, including OpenRouter configuration
data/                    Demo patents, demo product designs, SQLite database, future live imports
docs/                    Architecture and extension notes
src/patent_analysis/     Application package
tests/                   Core service smoke tests
main.py                  Python entrypoint for running the server or setup tasks
```

## Local setup

1. Create or reuse your virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Adjust the local configuration in `config/settings.local.toml`.
4. Start the app:

```bash
python main.py
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Commands

```bash
python main.py              # run the web app
python main.py runserver    # run the web app explicitly
python main.py init-db      # create the SQLite schema
python main.py seed-demo    # load demo patents and demo designs
python main.py test-openrouter
python main.py test-patent-extraction
python main.py reextract-patents
python -m unittest discover -s tests
```

## Current demo scope

- Text-based patent ingestion via the UI
- AI-assisted patent feature extraction for claims and descriptions when enabled
- Synthetic automotive glazing patents for development and evaluation
- Product design comparison with transparent scoring logic
- Structured design-around suggestions from detected overlaps
- Early multi-patent innovation summary

## Next recommended steps

1. Validate AI-assisted extraction quality on a few real partner-approved patent texts.
2. Add manual accept/edit workflows for extracted features in the review UI.
3. Add one real live data adapter, for example a watched folder of partner-approved patent exports.
4. Replace SQLite with PostgreSQL when multi-user deployment becomes necessary.

Architecture details are documented in [docs/architecture.md](docs/architecture.md).
