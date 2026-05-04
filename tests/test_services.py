from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from patent_analysis.config import load_settings
from patent_analysis.services.extraction import FeatureExtractor
from patent_analysis.services.innovation import InnovationService
from patent_analysis.services.normalization import TextNormalizer
from patent_analysis.services.risk import RiskAnalyzer


class ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = load_settings()
        cls.normalizer = TextNormalizer(cls.settings.analysis.canonical_terms)
        cls.extractor = FeatureExtractor(cls.settings, cls.normalizer)
        cls.risk_analyzer = RiskAnalyzer(cls.settings, cls.normalizer)

    def test_feature_extractor_pulls_key_claim_features(self):
        claims = (
            "1. A laminated vehicle windshield comprising an outer glass ply, an inner glass ply, "
            "a transparent conductive heating layer embedded adjacent to the polymer interlayer, "
            "edge busbars electrically coupled to the conductive heating layer, and temperature sensors."
        )
        features = self.extractor.extract_section_features(claims, "claims")
        normalized = {feature.normalized_feature for feature in features}

        self.assertTrue(
            any(
                "conductive heating layer" in item and "polymer interlayer" in item
                for item in normalized
            )
        )
        self.assertTrue(any("edge busbar" in item for item in normalized))

    def test_risk_analyzer_flags_high_overlap_for_similar_design(self):
        design_features = [
            {
                "raw_feature_text": "transparent conductive mesh close to the interlayer",
                "normalized_feature": self.normalizer.normalize_phrase(
                    "transparent conductive mesh close to the interlayer"
                ),
            },
            {
                "raw_feature_text": "electrical busbars at the edge",
                "normalized_feature": self.normalizer.normalize_phrase(
                    "electrical busbars at the edge"
                ),
            },
        ]
        patent_features = [
            {
                "id": 1,
                "raw_feature_text": "transparent conductive heating layer embedded adjacent to the polymer interlayer",
                "normalized_feature": self.normalizer.normalize_phrase(
                    "transparent conductive heating layer embedded adjacent to the polymer interlayer"
                ),
                "evidence_span": "transparent conductive heating layer embedded adjacent to the polymer interlayer",
            },
            {
                "id": 2,
                "raw_feature_text": "edge busbars electrically coupled to the conductive heating layer",
                "normalized_feature": self.normalizer.normalize_phrase(
                    "edge busbars electrically coupled to the conductive heating layer"
                ),
                "evidence_span": "edge busbars electrically coupled to the conductive heating layer",
            },
        ]

        result = self.risk_analyzer.analyze(
            design_name="WinterShield Alpha",
            patent_title="Laminated Vehicle Glazing with Zoned Conductive Heating Layer",
            design_features=design_features,
            patent_features=patent_features,
        )

        self.assertGreaterEqual(result["risk_score"], 65.0)
        self.assertEqual(result["risk_level"], "High")
        self.assertGreaterEqual(len(result["matches"]), 2)

    def test_innovation_service_reports_theme_gaps(self):
        patents_with_features = [
            {"features": [{"normalized_feature": "conductive heating layer edge busbar"}]},
            {"features": [{"normalized_feature": "sensor mounting pad adhesive alignment"}]},
        ]
        insight = InnovationService().analyze(patents_with_features)

        self.assertIn("Underrepresented opportunity themes", insight.gap_summary)
        self.assertIn("optical correction", insight.whitespace_themes)


if __name__ == "__main__":
    unittest.main()
