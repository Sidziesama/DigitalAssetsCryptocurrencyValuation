import math
import unittest

from src.pipeline.crypto_h1_activity_pilot import build, eligible


class CryptoH1ActivityPilotTests(unittest.TestCase):
    def test_missing_activity_is_excluded_not_zero_filled(self):
        rows = [{"asset_id": "a", "date": "2026-01-01", "log_market_cap_usd": "1",
                 "log1p_active_addresses_lag1": "", "log1p_transaction_count_lag1": "2"}]
        self.assertEqual(eligible(rows), [])

    def test_fixed_four_asset_panel_estimates_and_enumerates(self):
        rows = []
        for asset in range(4):
            for day in range(5):
                x1 = (asset + 1) * (day + 1) + (asset == day % 4)
                x2 = (asset + 2) * (day + 1) ** 2 + ((asset + day) % 3)
                y = 0.4 * x1 - 0.2 * x2 + 0.05 * asset * day
                rows.append({"asset_id": f"a{asset}", "date": f"2026-01-{day+1:02d}",
                             "log_market_cap_usd": str(y), "log1p_active_addresses_lag1": str(x1),
                             "log1p_transaction_count_lag1": str(x2)})
        result = build(rows)
        self.assertEqual(result["status"], "exploratory_four_asset_h1_complete")
        self.assertEqual(result["rows"], 20)
        self.assertTrue(all(item["bootstrap_assignments"] == 16 for item in result["inference"].values()))

    def test_non_four_asset_sample_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "four-asset"):
            build([])


if __name__ == "__main__":
    unittest.main()
