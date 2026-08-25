import unittest

from src.pipeline.stablecoin_adoption import build_adoption_panel


class StablecoinAdoptionTests(unittest.TestCase):
    def test_share_and_exact_date_growth(self):
        panel = [
            {"asset_id": "a", "date": "2026-01-01", "failure_control": "0", "circulating_peg_usd": "100", "absolute_peg_error_bps": "1", "breach_50bps": "0"},
            {"asset_id": "b", "date": "2026-01-01", "failure_control": "0", "circulating_peg_usd": "300", "absolute_peg_error_bps": "1", "breach_50bps": "0"},
            {"asset_id": "a", "date": "2026-01-31", "failure_control": "0", "circulating_peg_usd": "120", "absolute_peg_error_bps": "1", "breach_50bps": "0"},
        ]
        global_market = [{"date": "2026-01-01", "global_peggedusd_circulating_usd": "1000"}]
        rows, market = build_adoption_panel(panel, global_market)
        first = [row for row in rows if row["asset_id"] == "a" and row["date"] == "2026-01-01"][0]
        later = [row for row in rows if row["date"] == "2026-01-31"][0]
        self.assertEqual(first["pilot_observed_supply_share"], .25); self.assertAlmostEqual(later["supply_growth_30d"], .2)
        self.assertEqual(first["global_peggedusd_supply_share"], .1)
        self.assertEqual(market[0]["pilot_coverage_of_global_peggedusd"], .4)
        self.assertEqual(market[0]["pilot_supply_hhi"], .625)

    def test_failure_control_excluded(self):
        panel = [{"asset_id": "ustc", "date": "2026-01-01", "failure_control": "1", "circulating_peg_usd": "1", "absolute_peg_error_bps": "9000", "breach_50bps": "1"}]
        rows, market = build_adoption_panel(panel); self.assertEqual(rows, []); self.assertEqual(market, [])


if __name__ == "__main__": unittest.main()
