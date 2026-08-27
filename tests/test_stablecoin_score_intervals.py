import unittest

from src.pipeline.stablecoin_score_intervals import validate_and_build


def scorecard():
    dimensions = {name: {"weight": 20} for name in ("backing_quality", "verification_quality", "redemption_access_quality", "legal_protection_quality", "operational_resilience")}
    return {"methodology_version": "current", "scale": {"minimum": 0, "maximum": 4}, "dimensions": dimensions, "assets": [{"asset_id": f"a{i}", "available_from_date": "2026-01-02", "confidence": "high", "scores": {name: 4 for name in dimensions}, "rationale": "Current."} for i in range(8)]}


class StablecoinScoreIntervalTests(unittest.TestCase):
    def test_builds_historical_and_current_intervals(self):
        card = scorecard(); names = card["dimensions"]
        history = {"schema_version": 1, "methodology_version": "history", "intervals": [{"asset_id": "a0", "effective_from": "2026-01-01", "effective_to": "2026-01-01", "confidence": "high", "scores": {name: 3 for name in names}, "sources": [{"url": "https://example.test", "available_from_date": "2026-01-01"}], "rationale": "Historical."}]}
        rows = validate_and_build(card, history)
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[0]["overall_design_quality_score"], 75)

    def test_rejects_interval_before_source_availability(self):
        card = scorecard(); names = card["dimensions"]
        history = {"schema_version": 1, "methodology_version": "history", "intervals": [{"asset_id": "a0", "effective_from": "2025-12-31", "effective_to": "2026-01-01", "confidence": "high", "scores": {name: 3 for name in names}, "sources": [{"url": "https://example.test", "available_from_date": "2026-01-01"}], "rationale": "Historical."}]}
        with self.assertRaisesRegex(ValueError, "predates source"):
            validate_and_build(card, history)


if __name__ == "__main__":
    unittest.main()
