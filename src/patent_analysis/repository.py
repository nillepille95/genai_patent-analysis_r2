from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import json
import sqlite3

from .database import get_connection
from .models import (
    FeatureCandidate,
    InnovationInsightCandidate,
    MatchCandidate,
    PatentDocumentInput,
    ProductDesignInput,
    SuggestionCandidate,
)


class PatentAnalysisRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    @contextmanager
    def connection(self):
        connection = get_connection(self.database_path)
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
        return dict(row) if row is not None else None

    def count_patents(self) -> int:
        with self.connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM patents").fetchone()
        return int(row["count"])

    def count_product_designs(self) -> int:
        with self.connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM product_designs").fetchone()
        return int(row["count"])

    def get_dashboard_metrics(self) -> dict[str, int]:
        with self.connection() as connection:
            patents = connection.execute("SELECT COUNT(*) AS count FROM patents").fetchone()["count"]
            features = connection.execute(
                "SELECT COUNT(*) AS count FROM extracted_features"
            ).fetchone()["count"]
            designs = connection.execute(
                "SELECT COUNT(*) AS count FROM product_designs"
            ).fetchone()["count"]
            assessments = connection.execute(
                "SELECT COUNT(*) AS count FROM risk_assessments"
            ).fetchone()["count"]
        return {
            "patents": int(patents),
            "features": int(features),
            "designs": int(designs),
            "assessments": int(assessments),
        }

    def list_patents(self, search_query: str = "", limit: int | None = None) -> list[dict]:
        query = """
            SELECT
                p.*,
                COUNT(DISTINCT s.id) AS section_count,
                COUNT(DISTINCT f.id) AS feature_count
            FROM patents p
            LEFT JOIN patent_sections s ON s.patent_id = p.id
            LEFT JOIN extracted_features f ON f.patent_id = p.id
        """
        params: list[object] = []
        if search_query:
            query += """
                WHERE
                    LOWER(p.title) LIKE ?
                    OR LOWER(COALESCE(p.patent_number, '')) LIKE ?
                    OR LOWER(COALESCE(p.source, '')) LIKE ?
            """
            search = f"%{search_query.lower()}%"
            params.extend([search, search, search])

        query += """
            GROUP BY p.id
            ORDER BY p.created_at DESC, p.id DESC
        """
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def list_recent_assessments(self, limit: int = 5) -> list[dict]:
        query = """
            SELECT
                ra.*,
                p.title AS patent_title,
                pd.name AS design_name
            FROM risk_assessments ra
            JOIN patents p ON p.id = ra.patent_id
            JOIN product_designs pd ON pd.id = ra.product_design_id
            ORDER BY ra.created_at DESC, ra.id DESC
            LIMIT ?
        """
        with self.connection() as connection:
            rows = connection.execute(query, (limit,)).fetchall()
        return [dict(row) for row in rows]

    def list_product_designs(self) -> list[dict]:
        query = """
            SELECT
                pd.*,
                COUNT(pf.id) AS feature_count
            FROM product_designs pd
            LEFT JOIN product_features pf ON pf.product_design_id = pd.id
            GROUP BY pd.id
            ORDER BY pd.created_at DESC, pd.id DESC
        """
        with self.connection() as connection:
            rows = connection.execute(query).fetchall()
        return [dict(row) for row in rows]

    def get_patent_detail(self, patent_id: int) -> dict | None:
        with self.connection() as connection:
            patent = connection.execute(
                "SELECT * FROM patents WHERE id = ?", (patent_id,)
            ).fetchone()
            if patent is None:
                return None
            sections = connection.execute(
                """
                SELECT * FROM patent_sections
                WHERE patent_id = ?
                ORDER BY CASE section_type
                    WHEN 'abstract' THEN 1
                    WHEN 'claims' THEN 2
                    WHEN 'description' THEN 3
                    ELSE 4
                END, id ASC
                """,
                (patent_id,),
            ).fetchall()
            features = connection.execute(
                """
                SELECT ef.*, ps.section_type
                FROM extracted_features ef
                JOIN patent_sections ps ON ps.id = ef.section_id
                WHERE ef.patent_id = ?
                ORDER BY ef.confidence DESC, ef.id ASC
                """,
                (patent_id,),
            ).fetchall()
        return {
            "patent": dict(patent),
            "sections": [dict(section) for section in sections],
            "features": [dict(feature) for feature in features],
        }

    def get_product_design(self, design_id: int) -> dict | None:
        with self.connection() as connection:
            design = connection.execute(
                "SELECT * FROM product_designs WHERE id = ?", (design_id,)
            ).fetchone()
            if design is None:
                return None
            features = connection.execute(
                """
                SELECT * FROM product_features
                WHERE product_design_id = ?
                ORDER BY confidence DESC, id ASC
                """,
                (design_id,),
            ).fetchall()
        design_dict = dict(design)
        design_dict["normalized_features"] = json.loads(design_dict["normalized_features"])
        return {
            "design": design_dict,
            "features": [dict(feature) for feature in features],
        }

    def get_patent_features(self, patent_id: int) -> list[dict]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT ef.*, ps.section_type
                FROM extracted_features ef
                JOIN patent_sections ps ON ps.id = ef.section_id
                WHERE ef.patent_id = ?
                ORDER BY ef.confidence DESC, ef.id ASC
                """,
                (patent_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_product_features(self, design_id: int) -> list[dict]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM product_features
                WHERE product_design_id = ?
                ORDER BY confidence DESC, id ASC
                """,
                (design_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_patent(
        self,
        document: PatentDocumentInput,
        extracted_features_by_section: dict[str, list[FeatureCandidate]],
    ) -> int:
        raw_text = "\n\n".join(
            f"{section_type.upper()}\n{section_text.strip()}"
            for section_type, section_text in document.sections.items()
            if section_text.strip()
        )
        with self.connection() as connection:
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO patents (title, patent_number, source, partner_domain, raw_text)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        document.title.strip(),
                        document.patent_number.strip() or None,
                        document.source.strip() or None,
                        document.partner_domain.strip() or None,
                        raw_text,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("Patent number already exists in the database.") from exc

            patent_id = int(cursor.lastrowid)
            section_ids: dict[str, int] = {}

            for section_type, section_text in document.sections.items():
                if not section_text.strip():
                    continue
                section_cursor = connection.execute(
                    """
                    INSERT INTO patent_sections (patent_id, section_type, section_text)
                    VALUES (?, ?, ?)
                    """,
                    (patent_id, section_type, section_text.strip()),
                )
                section_ids[section_type] = int(section_cursor.lastrowid)

            for section_type, features in extracted_features_by_section.items():
                section_id = section_ids.get(section_type)
                if section_id is None:
                    continue
                for feature in features:
                    connection.execute(
                        """
                        INSERT INTO extracted_features (
                            patent_id,
                            section_id,
                            raw_feature_text,
                            normalized_feature,
                            confidence,
                            evidence_span,
                            extraction_method,
                            extraction_notes
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            patent_id,
                            section_id,
                            feature.raw_feature_text,
                            feature.normalized_feature,
                            feature.confidence,
                            feature.evidence_span,
                            feature.extraction_method,
                            feature.extraction_notes,
                        ),
                    )

        return patent_id

    def create_product_design(
        self, design: ProductDesignInput, extracted_features: list[FeatureCandidate]
    ) -> int:
        normalized_features = [feature.normalized_feature for feature in extracted_features]
        with self.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO product_designs (name, raw_description, normalized_features)
                VALUES (?, ?, ?)
                """,
                (
                    design.name.strip(),
                    design.raw_description.strip(),
                    json.dumps(normalized_features),
                ),
            )
            design_id = int(cursor.lastrowid)
            for feature in extracted_features:
                connection.execute(
                    """
                    INSERT INTO product_features (
                        product_design_id,
                        raw_feature_text,
                        normalized_feature,
                        confidence,
                        evidence_span,
                        extraction_method,
                        extraction_notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        design_id,
                        feature.raw_feature_text,
                        feature.normalized_feature,
                        feature.confidence,
                        feature.evidence_span,
                        feature.extraction_method,
                        feature.extraction_notes,
                    ),
                )

        return design_id

    def replace_patent_features(
        self, patent_id: int, extracted_features_by_section: dict[str, list[FeatureCandidate]]
    ) -> int:
        with self.connection() as connection:
            section_rows = connection.execute(
                "SELECT id, section_type FROM patent_sections WHERE patent_id = ?",
                (patent_id,),
            ).fetchall()
            section_ids = {str(row["section_type"]): int(row["id"]) for row in section_rows}
            connection.execute("DELETE FROM extracted_features WHERE patent_id = ?", (patent_id,))

            inserted_count = 0
            for section_type, features in extracted_features_by_section.items():
                section_id = section_ids.get(section_type)
                if section_id is None:
                    continue
                for feature in features:
                    connection.execute(
                        """
                        INSERT INTO extracted_features (
                            patent_id,
                            section_id,
                            raw_feature_text,
                            normalized_feature,
                            confidence,
                            evidence_span,
                            extraction_method,
                            extraction_notes
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            patent_id,
                            section_id,
                            feature.raw_feature_text,
                            feature.normalized_feature,
                            feature.confidence,
                            feature.evidence_span,
                            feature.extraction_method,
                            feature.extraction_notes,
                        ),
                    )
                    inserted_count += 1

        return inserted_count

    def create_risk_assessment(
        self,
        product_design_id: int,
        patent_id: int,
        risk_score: float,
        risk_level: str,
        reasoning_summary: str,
        matches: list[MatchCandidate],
        suggestions: list[SuggestionCandidate],
    ) -> int:
        with self.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO risk_assessments (
                    product_design_id,
                    patent_id,
                    risk_score,
                    risk_level,
                    reasoning_summary
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    product_design_id,
                    patent_id,
                    risk_score,
                    risk_level,
                    reasoning_summary,
                ),
            )
            assessment_id = int(cursor.lastrowid)

            for match in matches:
                connection.execute(
                    """
                    INSERT INTO feature_matches (
                        risk_assessment_id,
                        design_feature,
                        patent_feature_id,
                        match_type,
                        match_score,
                        evidence
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        assessment_id,
                        match.design_feature,
                        match.patent_feature_id,
                        match.match_type,
                        match.match_score,
                        match.evidence,
                    ),
                )

            for suggestion in suggestions:
                connection.execute(
                    """
                    INSERT INTO design_suggestions (
                        risk_assessment_id,
                        suggestion_text,
                        rationale,
                        feasibility_note
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        assessment_id,
                        suggestion.suggestion_text,
                        suggestion.rationale,
                        suggestion.feasibility_note,
                    ),
                )

        return assessment_id

    def get_assessment_detail(self, assessment_id: int) -> dict | None:
        query = """
            SELECT
                ra.*,
                p.title AS patent_title,
                p.patent_number,
                pd.name AS design_name,
                pd.raw_description AS design_description
            FROM risk_assessments ra
            JOIN patents p ON p.id = ra.patent_id
            JOIN product_designs pd ON pd.id = ra.product_design_id
            WHERE ra.id = ?
        """
        with self.connection() as connection:
            assessment = connection.execute(query, (assessment_id,)).fetchone()
            if assessment is None:
                return None

            matches = connection.execute(
                """
                SELECT
                    fm.*,
                    ef.raw_feature_text AS patent_feature_text,
                    ef.normalized_feature AS patent_feature_normalized,
                    ef.evidence_span AS patent_evidence
                FROM feature_matches fm
                JOIN extracted_features ef ON ef.id = fm.patent_feature_id
                WHERE fm.risk_assessment_id = ?
                ORDER BY fm.match_score DESC, fm.id ASC
                """,
                (assessment_id,),
            ).fetchall()

            suggestions = connection.execute(
                """
                SELECT * FROM design_suggestions
                WHERE risk_assessment_id = ?
                ORDER BY id ASC
                """,
                (assessment_id,),
            ).fetchall()

        return {
            "assessment": dict(assessment),
            "matches": [dict(match) for match in matches],
            "suggestions": [dict(suggestion) for suggestion in suggestions],
        }

    def list_patents_with_features(self) -> list[dict]:
        patents = self.list_patents(limit=None)
        for patent in patents:
            patent["features"] = self.get_patent_features(int(patent["id"]))
        return patents

    def save_innovation_insight(self, insight: InnovationInsightCandidate) -> int:
        with self.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO innovation_insights (scope, pattern_summary, gap_summary, recommendation)
                VALUES (?, ?, ?, ?)
                """,
                (
                    insight.scope,
                    insight.pattern_summary,
                    insight.gap_summary,
                    insight.recommendation,
                ),
            )
        return int(cursor.lastrowid)

    def get_latest_innovation_insight(self) -> dict | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM innovation_insights
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
        return self._row_to_dict(row)
