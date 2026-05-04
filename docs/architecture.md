# Architecture Notes

## 1. Prototype boundary

The first implementation slice intentionally covers the must-have flow from the requirements:

1. Ingest a patent as text.
2. Split it into sections.
3. Extract normalized technical features with source evidence.
4. Store the structured result in a database.
5. Accept a product design description.
6. Extract design features in the same format.
7. Compare product features against patent features.
8. Produce an explainable risk score and design-around suggestions.

That keeps the first usable version aligned with Phase 1 and Phase 2 while leaving extension points for Phase 3 and Phase 4.

## 2. Chosen libraries

### Backend

- `FastAPI`
  - Good fit for Python-first development.
  - Easy to host locally with `uvicorn`.
  - Clean future path for APIs, authentication, and private deployment.

### Frontend

- `Jinja2` server-rendered templates
  - Fast to prototype.
  - No separate frontend build pipeline needed.
  - Easy to host inside a private environment for the industry partner.
  - Good stepping stone if a richer React frontend is needed later.

### Storage

- `sqlite3` from the Python standard library
  - Zero extra dependency for the prototype.
  - Enough for a local single-user or small-team workflow.
  - Repository layer is isolated so it can later be replaced with PostgreSQL.

### AI integration

- Rule-based extraction and scoring first
  - More predictable and auditable for an academic prototype.
  - Easier to debug than a full LLM-first pipeline.

- Optional `OpenRouter` client
  - Wired in through config now.
  - Used as an enhancement path for richer design-around suggestions later.
  - The app still runs when no API key is configured.

## 3. Module layout

### Core application

- `src/patent_analysis/app.py`
  - FastAPI application, routes, dependency wiring.

- `src/patent_analysis/config.py`
  - Loads `settings.local.toml` or falls back to `settings.example.toml`.

- `src/patent_analysis/database.py`
  - SQLite schema creation and connection helpers.

- `src/patent_analysis/repository.py`
  - Central persistence layer for patents, features, product designs, assessments, and suggestions.

### Services

- `services/normalization.py`
  - Shared token cleanup and canonical term normalization.

- `services/extraction.py`
  - Heuristic feature extraction from claims, descriptions, and product text.

- `services/risk.py`
  - Patent-to-product comparison and explainable scoring.

- `services/suggestions.py`
  - Rule-based design-around suggestions, with optional OpenRouter augmentation.

- `services/innovation.py`
  - Early multi-patent theme and whitespace summary.

- `services/llm.py`
  - Small optional OpenRouter client.

### Data source adapters

- `sources/demo.py`
  - Loads the synthetic demo patents and designs.

- `sources/directory.py`
  - Reads future local patent import files from a folder.

This adapter pattern is the main extension point for future live sources.

## 4. Why this frontend choice

For this stage, a server-rendered web app is the best tradeoff:

- easy to test on `localhost`,
- easy to demo to supervisors,
- easier to package in Docker or deploy behind a private reverse proxy,
- keeps the whole project Python-centric while the data and analysis pipeline is still evolving.

If the partner later needs heavier workflow interaction, we can keep the FastAPI backend and replace only the UI layer.

## 5. How to add live patent databases later

The current code is prepared for three source classes:

1. `demo_json`
   - synthetic data for development and evaluation

2. `directory`
   - approved `.json`, `.txt`, or `.md` files dropped into `data/live_patents/`

3. future remote connectors
   - partner export API
   - internal document management system
   - database dump or scheduled ETL feed

To add a new live source cleanly:

1. Create a new adapter implementing the same source interface.
2. Normalize the incoming patent structure into the shared patent document model.
3. Register the adapter in the source registry.
4. Add source-specific config values in `settings.local.toml`.

That way, ingestion changes do not affect extraction, scoring, or the UI.

## 6. Data model direction

The SQLite schema mirrors the requirements:

- `patents`
- `patent_sections`
- `extracted_features`
- `product_designs`
- `product_features`
- `risk_assessments`
- `feature_matches`
- `design_suggestions`
- `innovation_insights`

This is intentionally close to the requirement document so we keep traceability between the written specification and the implementation.

## 7. Deployment path

### Local prototype now

- `python main.py`
- SQLite file in `data/`
- localhost access only

### Private industry deployment later

- same FastAPI app
- environment-specific config file
- Docker container or virtual machine deployment
- reverse proxy such as Nginx
- swap SQLite to PostgreSQL
- add authentication and access control

## 8. Intentional limitations of this first version

- no CAD-native integration yet
- no legal advice or legal automation
- no heavy embedding stack yet
- no multi-user auth yet
- live remote patent connectors are designed but not activated

That keeps the system aligned with the current scope and avoids premature complexity.
