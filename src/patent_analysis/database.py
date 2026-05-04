from __future__ import annotations

from pathlib import Path
import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS patents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    patent_number TEXT,
    source TEXT,
    partner_domain TEXT,
    raw_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_patents_number ON patents (patent_number);
CREATE INDEX IF NOT EXISTS idx_patents_source ON patents (source);

CREATE TABLE IF NOT EXISTS patent_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patent_id INTEGER NOT NULL,
    section_type TEXT NOT NULL,
    section_text TEXT NOT NULL,
    FOREIGN KEY(patent_id) REFERENCES patents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sections_patent ON patent_sections (patent_id);

CREATE TABLE IF NOT EXISTS extracted_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patent_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    raw_feature_text TEXT NOT NULL,
    normalized_feature TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence_span TEXT NOT NULL,
    extraction_method TEXT NOT NULL DEFAULT 'rule',
    extraction_notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY(patent_id) REFERENCES patents(id) ON DELETE CASCADE,
    FOREIGN KEY(section_id) REFERENCES patent_sections(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_features_patent ON extracted_features (patent_id);
CREATE INDEX IF NOT EXISTS idx_features_normalized ON extracted_features (normalized_feature);

CREATE TABLE IF NOT EXISTS product_designs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    raw_description TEXT NOT NULL,
    normalized_features TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_design_id INTEGER NOT NULL,
    raw_feature_text TEXT NOT NULL,
    normalized_feature TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence_span TEXT NOT NULL,
    extraction_method TEXT NOT NULL DEFAULT 'rule',
    extraction_notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY(product_design_id) REFERENCES product_designs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_features_design ON product_features (product_design_id);

CREATE TABLE IF NOT EXISTS risk_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_design_id INTEGER NOT NULL,
    patent_id INTEGER NOT NULL,
    risk_score REAL NOT NULL,
    risk_level TEXT NOT NULL,
    reasoning_summary TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(product_design_id) REFERENCES product_designs(id) ON DELETE CASCADE,
    FOREIGN KEY(patent_id) REFERENCES patents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_risk_patent ON risk_assessments (patent_id);
CREATE INDEX IF NOT EXISTS idx_risk_design ON risk_assessments (product_design_id);

CREATE TABLE IF NOT EXISTS feature_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_assessment_id INTEGER NOT NULL,
    design_feature TEXT NOT NULL,
    patent_feature_id INTEGER NOT NULL,
    match_type TEXT NOT NULL,
    match_score REAL NOT NULL,
    evidence TEXT NOT NULL,
    FOREIGN KEY(risk_assessment_id) REFERENCES risk_assessments(id) ON DELETE CASCADE,
    FOREIGN KEY(patent_feature_id) REFERENCES extracted_features(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_matches_assessment ON feature_matches (risk_assessment_id);

CREATE TABLE IF NOT EXISTS design_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_assessment_id INTEGER NOT NULL,
    suggestion_text TEXT NOT NULL,
    rationale TEXT NOT NULL,
    feasibility_note TEXT NOT NULL,
    FOREIGN KEY(risk_assessment_id) REFERENCES risk_assessments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_suggestions_assessment ON design_suggestions (risk_assessment_id);

CREATE TABLE IF NOT EXISTS innovation_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,
    pattern_summary TEXT NOT NULL,
    gap_summary TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

MIGRATIONS: dict[str, list[tuple[str, str]]] = {
    "extracted_features": [
        ("extraction_method", "TEXT NOT NULL DEFAULT 'rule'"),
        ("extraction_notes", "TEXT NOT NULL DEFAULT ''"),
    ],
    "product_features": [
        ("extraction_method", "TEXT NOT NULL DEFAULT 'rule'"),
        ("extraction_notes", "TEXT NOT NULL DEFAULT ''"),
    ],
}


def get_connection(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def initialize_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(database_path) as connection:
        connection.executescript(SCHEMA)
        for table_name, column_specs in MIGRATIONS.items():
            existing_columns = {
                row["name"]
                for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
            }
            for column_name, column_spec in column_specs:
                if column_name in existing_columns:
                    continue
                connection.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_spec}"
                )
        connection.commit()
