import unittest

from src.pipeline.crypto_h8_breadth_pilot import build, ranks


class CryptoH8BreadthPilotTests(unittest.TestCase):
    def test_five_asset_exact_permutation_pilot(self):
        readiness = [
            {"asset_id": f"a{i}", "h8_design_ready": "1", "h8_value_accrual_breadth": str(i + 1)}
            for i in range(5)
        ]
        market = [
            {"asset_id": f"a{i}", "market_cap_usd": str(100 * (i + 1))}
            for i in range(5) for _ in range(2)
        ]
        rows, summary = build(readiness, market)
        self.assertEqual(len(rows), 5)
        self.assertEqual(summary["permutations"], 120)
        self.assertGreater(summary["slope"], 0)
        self.assertEqual(summary["leave_one_asset_out_positive"], 5)

    def test_incomplete_cross_section_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly five"):
            build([], [])

    def test_tied_values_receive_average_rank(self):
        self.assertEqual(ranks([1, 1, 3]), [1.5, 1.5, 3.0])


if __name__ == "__main__":
    unittest.main()
