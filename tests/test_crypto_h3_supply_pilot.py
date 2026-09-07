import math
import unittest

from src.pipeline.crypto_h3_supply_pilot import ASSETS, build, build_panel


class CryptoH3SupplyPilotTests(unittest.TestCase):
    def test_panel_uses_only_prior_supply_and_drops_missing_outcomes(self):
        fundamentals, market = [], []
        for asset in ASSETS:
            for day in range(1, 13):
                date = f"2026-01-{day:02d}"
                fundamentals.append({"asset_id": asset, "date": date, "current_supply": str(100 + day)})
                market.append({"asset_id": asset, "date": date, "forward_log_return_7d": "0.1",
                               "log1p_active_addresses_lag1": "1", "log1p_transaction_count_lag1": "2"})
        rows = build_panel(fundamentals, market)
        first = next(row for row in rows if row["asset_id"] == ASSETS[0])
        self.assertEqual(first["date"], "2026-01-09")
        self.assertAlmostEqual(first["circulating_supply_growth_7d_lag1"], math.log(108 / 101))

    def test_four_asset_panel_estimates_exact_inference(self):
        rows = []
        for asset_index, asset in enumerate(ASSETS):
            for day in range(12):
                supply = 0.002 * (asset_index + 1) * (day + 1) + 0.0001 * ((day + asset_index) % 3)
                address = 1 + 0.1 * asset_index * day + 0.03 * ((day + 1) % 2)
                tx = 2 + 0.02 * (asset_index + 1) * day ** 2 + 0.01 * ((day + asset_index) % 4)
                outcome = -0.4 * supply + 0.03 * address - 0.01 * tx + 0.001 * asset_index * day
                rows.append({"asset_id": asset, "date": f"2026-01-{day+1:02d}",
                             "circulating_supply_growth_7d_lag1": supply,
                             "log1p_active_addresses_lag1": address,
                             "log1p_transaction_count_lag1": tx,
                             "forward_log_return_7d": outcome})
        result = build(rows)
        self.assertEqual(result["status"], "h3_supply_proxy_diagnostic_complete_not_identification_ready")
        self.assertEqual(result["inference"]["bootstrap_assignments"], 16)
        self.assertEqual(len(result["leave_one_asset_out"]), 4)
        self.assertEqual(result["assets_with_within_supply_variation"], 4)

    def test_incomplete_asset_sample_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "four-asset"):
            build([])


if __name__ == "__main__":
    unittest.main()
