import unittest

from src.pipeline.crypto_economic_design import CODES, apply_review, build_profiles, build_review, validate


def registry():
    return {"assets": [{"asset_id": "crypto_x", "symbol": "X", "universe": "crypto", "tier": "market_core"}]}


def spec(codes=None):
    return {"schema_version": 1, "as_of": "2026-08-22", "status": "provisional", "value_accrual_codes": list(CODES), "assets": [{"asset_id": "crypto_x", "consensus": "PoS", "codes": codes or [0] * 10}]}


class CryptoEconomicDesignTests(unittest.TestCase):
    def test_requires_exact_frozen_crypto_universe(self):
        bad = spec(); bad["assets"][0]["asset_id"] = "crypto_y"
        with self.assertRaisesRegex(ValueError, "universe mismatch"):
            validate(bad, registry())

    def test_rejects_nonbinary_or_incomplete_codes(self):
        with self.assertRaisesRegex(ValueError, "ten binary"):
            validate(spec([0] * 9 + [2]), registry())

    def test_builds_h2_capture_and_h8_breadth_without_conflating_stake(self):
        values = [0] * 10; values[CODES.index("VA_STAKE")] = 1; values[CODES.index("VA_PROTOCOL")] = 1
        row = build_profiles(spec(values), registry())[0]
        self.assertEqual(row["va_breadth_count"], 2)
        self.assertEqual(row["direct_capture_active"], 1)
        self.assertEqual(row["va_stake"], 1)

    def test_review_is_blind_to_provisional_decision(self):
        rows = build_review(spec([1] * 10), registry())
        self.assertEqual(len(rows), 10)
        self.assertNotIn("provisional_decision", rows[0])
        self.assertEqual(rows[0]["decision_0_or_1"], "")

    def test_completed_review_overrides_provisional_profile(self):
        review = build_review(spec([0] * 10), registry())
        for row in review:
            row.update(decision_0_or_1="1", confidence_low_medium_high="high",
                       evidence_url="https://example.com", evidence_date="2026-08-22",
                       reviewer_note="Human verified against the rule.")
        profiles = apply_review(build_profiles(spec([0] * 10), registry()), review, spec([0] * 10))
        self.assertEqual(profiles[0]["va_breadth_count"], 10)
        self.assertEqual(profiles[0]["classification_status"], "complete_human_verified")


if __name__ == "__main__":
    unittest.main()
