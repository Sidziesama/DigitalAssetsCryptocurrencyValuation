import unittest

from src.pipeline.h5_h6_readiness import build_blind_review, join_temporally_valid, temporal_readiness


class H5H6ReadinessTests(unittest.TestCase):
    def test_temporal_join_prohibits_backfill(self):
        scores = [{"asset_id": "a", "as_of_date": "2026-01-03", "available_from_date": "2026-01-02"}]
        outcomes = [{"asset_id": "a", "date": "2026-01-01"}, {"asset_id": "a", "date": "2026-01-02"}]
        result = temporal_readiness(scores, outcomes)
        self.assertEqual(result["post_score_outcome_rows"], 1)
        self.assertEqual(result["pre_score_rows_prohibited_from_backfill"], 1)
        self.assertEqual(result["status"], "temporal_overlap_ready")

    def test_incomplete_asset_overlap_blocks_estimation(self):
        scores = [{"asset_id": "a", "as_of_date": "2026-01-01"}, {"asset_id": "b", "as_of_date": "2026-01-01"}]
        result = temporal_readiness(scores, [{"asset_id": "a", "date": "2026-01-02"}])
        self.assertEqual(result["status"], "blocked_temporal_overlap")

    def test_temporal_panel_never_backfills(self):
        scores = [{"asset_id": "a", "as_of_date": "2026-01-03", "available_from_date": "2026-01-02", "backing_quality_score": "75"}]
        outcomes = [{"asset_id": "a", "date": "2026-01-01"}, {"asset_id": "a", "date": "2026-01-02"}]
        rows = join_temporally_valid(scores, outcomes)
        self.assertEqual([row["date"] for row in rows], ["2026-01-02"])
        self.assertEqual(rows[0]["backing_quality_score"], "75")

    def test_temporal_panel_selects_effective_interval(self):
        scores = [
            {"asset_id": "a", "effective_from": "2026-01-01", "effective_to": "2026-01-02", "backing_quality_score": "50"},
            {"asset_id": "a", "effective_from": "2026-01-03", "effective_to": "", "backing_quality_score": "75"},
        ]
        outcomes = [{"asset_id": "a", "date": "2026-01-02"}, {"asset_id": "a", "date": "2026-01-03"}]
        rows = join_temporally_valid(scores, outcomes)
        self.assertEqual([row["backing_quality_score"] for row in rows], ["50", "75"])

    def test_review_is_blind_to_primary_score(self):
        config = {
            "dimensions": {"quality": {"evidence_class": "reserve"}},
            "rubric": {"quality": {str(i): f"level {i}" for i in range(5)}},
            "assets": [{"asset_id": "a", "scores": {"quality": 4}}],
        }
        evidence = {"extractions": [{"asset_id": "a", "evidence_class": "reserve", "source_title": "Report", "source_url": "https://example.test", "publication_or_effective_date": "2026-01-01", "locator": "p. 1", "evidence_summary": "Summary", "limitations": "Limit"}]}
        row = build_blind_review(config, evidence)[0]
        self.assertNotIn("primary_score", row)
        self.assertEqual(row["reviewer_score_0_to_4"], "")


if __name__ == "__main__":
    unittest.main()
