import copy
import unittest

from src.pipeline.review_adjudication import audit_crypto, audit_stablecoin, cohen_kappa


class ReviewAdjudicationTests(unittest.TestCase):
    def test_crypto_pending_review_is_not_freeze_eligible(self):
        evidence = {"decisions": [{"asset_id": "a", "code": "VA_BURN", "recommended_value": 1}]}
        rows, summary = audit_crypto([{"asset_id": "a", "code": "VA_BURN", "reviewer_value": "",
                                      "reviewer_source_url": "", "reviewer_rationale": ""}], evidence)
        self.assertEqual(summary["status"], "independent_review_pending")
        self.assertFalse(summary["freeze_eligible"])
        self.assertEqual(rows[0]["agreement"], "")

    def test_crypto_complete_disagreement_requires_adjudication(self):
        evidence = {"decisions": [{"asset_id": "a", "code": "VA_BURN", "recommended_value": 1}]}
        _, summary = audit_crypto([{"asset_id": "a", "code": "VA_BURN", "reviewer_value": "0",
                                    "reviewer_source_url": "https://example.test", "reviewer_rationale": "No burn."}], evidence)
        self.assertEqual(summary["status"], "complete_adjudication_pending")
        self.assertEqual(summary["disagreements"], 1)

    def test_stablecoin_complete_agreement_is_freeze_eligible(self):
        scorecard = {"assets": [{"asset_id": "s", "scores": {"quality": 4}}]}
        row = {"asset_id": "s", "dimension": "quality", "reviewer_score_0_to_4": "4",
               "reviewer_confidence": "high", "reviewer_rationale": "Matches rubric.",
               "reviewer_name_or_id": "reviewer-1", "review_date": "2026-08-31"}
        _, summary = audit_stablecoin([row], scorecard)
        self.assertEqual(summary["status"], "complete_no_disagreements")
        self.assertTrue(summary["freeze_eligible"])
        self.assertEqual(summary["cohen_kappa"], 1.0)

    def test_altered_grid_is_rejected(self):
        evidence = {"decisions": [{"asset_id": "a", "code": "VA_BURN", "recommended_value": 1}]}
        with self.assertRaisesRegex(ValueError, "predeclared decision"):
            audit_crypto([], evidence)

    def test_kappa_known_example(self):
        self.assertAlmostEqual(cohen_kappa([(0, 0), (0, 1), (1, 1), (1, 1)], [0, 1]), 0.5)


if __name__ == "__main__":
    unittest.main()
