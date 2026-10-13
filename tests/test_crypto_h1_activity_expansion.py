import unittest

from src.pipeline.crypto_h1_activity_expansion import build, build_panel, chart


def spec(assets):
    return {
        "status": "frozen_before_expansion_estimation",
        "window": {"start": "2026-01-01", "end": "2026-01-06"},
        "primary_assets": assets,
        "token_contract_sensitivity_assets": [],
        "reporting": ["association only"],
    }


class Tests(unittest.TestCase):
    def test_panel_uses_lag_and_never_zero_fills_missing_activity(self):
        cfg = spec(["a", "b", "c", "d"])
        activity = [[{"asset_id": "a", "date": "2026-01-01", "active_addresses": "4", "transaction_count": "9"}]]
        market = [{"asset_id": "a", "date": "2026-01-02", "market_cap_usd": "100"},
                  {"asset_id": "a", "date": "2026-01-03", "market_cap_usd": "101"}]
        rows = build_panel(cfg, activity, market)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["active_addresses_lag1"], 4)

    def test_frozen_balanced_primary_expansion_estimates(self):
        assets = ["a", "b", "c", "d"]
        cfg = spec(assets)
        activity, market = [], []
        for ai, asset in enumerate(assets):
            for day in range(1, 7):
                activity.append({"asset_id": asset, "date": f"2026-01-{day:02d}",
                                 "active_addresses": str((ai + 1) * day + (day % 2)),
                                 "transaction_count": str((ai + 2) * day * day + ((ai + day) % 3))})
                if day >= 2:
                    market.append({"asset_id": asset, "date": f"2026-01-{day:02d}",
                                   "market_cap_usd": str(1000 + 17 * ai + 11 * day + ai * day * day)})
        panel, result = build(cfg, [activity], market)
        self.assertEqual(len(panel), 20)
        self.assertEqual(result["primary"]["rows"], 20)
        self.assertEqual(result["primary"]["inference"]["log1p_transaction_count_lag1"]["bootstrap_assignments"], 16)
        self.assertIn('role="img"', chart(result))

    def test_unfrozen_design_is_rejected(self):
        cfg = spec(["a", "b", "c", "d"]); cfg["status"] = "draft"
        with self.assertRaisesRegex(ValueError, "frozen"):
            build_panel(cfg, [], [])


if __name__ == "__main__":
    unittest.main()
