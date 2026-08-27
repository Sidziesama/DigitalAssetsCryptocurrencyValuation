import unittest

from src.pipeline.stablecoin_scorecard import evaluate, normalized, validate


def config():
    dimensions = {"quality": {"evidence_class": "reserve", "direction": "higher_is_better", "weight": 100}}
    rubric = {"quality": {str(i): f"level {i}" for i in range(5)}}
    return {
        "schema_version": 1, "methodology_version": "x", "as_of_date": "2026-01-01",
        "scale": {"minimum": 0, "maximum": 4}, "dimensions": dimensions, "rubric": rubric,
        "derived_scores": {"redemption_friction": {"quality_inputs": {"redemption_access_quality": 60, "operational_resilience": 40}}},
        "assets": [{"asset_id": f"stable_{i}", "confidence": "high", "available_from_date": "2026-01-01", "availability_basis": "Dated report.", "scores": {"quality": i % 5}, "rationale": "Evidence-based rating."} for i in range(8)],
    }


def evidence():
    return {"extractions": [{"asset_id": f"stable_{i}", "evidence_class": "reserve", "verification_status": "verified_extracted", "publication_or_effective_date": "2026-01-01"} for i in range(8)]}


class StablecoinScorecardTests(unittest.TestCase):
    def test_normalizes_ordinal_score(self):
        self.assertEqual(normalized(3, 0, 4), 75)

    def test_evaluates_complete_scorecard(self):
        rows = evaluate(config(), evidence())
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[4]["overall_design_quality_score"], 100)
        self.assertEqual(rows[0]["available_from_date"], "2026-01-01")

    def test_rejects_score_without_verified_evidence(self):
        value = evidence(); value["extractions"].pop()
        with self.assertRaisesRegex(ValueError, "missing verified evidence"):
            validate(config(), value)

    def test_rejects_incomplete_rubric(self):
        value = config(); value["rubric"]["quality"].pop("4")
        with self.assertRaisesRegex(ValueError, "incomplete rubric"):
            validate(value, evidence())


if __name__ == "__main__":
    unittest.main()
