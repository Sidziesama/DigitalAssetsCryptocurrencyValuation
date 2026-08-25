import unittest

from src.pipeline.stablecoin_trading_activity import build_rows


class StablecoinTradingActivityTests(unittest.TestCase):
    def test_turnover_and_join(self):
        adoption = [{"asset_id": "x", "date": "2026-01-01", "circulating_peg_usd": "100", "pilot_observed_supply_share": ".2", "absolute_peg_error_bps": "1", "breach_50bps": "0"}]
        market = [{"asset_id": "x", "date": "2026-01-01", "volume_24h_usd": "50", "market_cap_usd": "101"}]
        row = build_rows(adoption, market)[0]
        self.assertAlmostEqual(row["volume_to_reported_market_cap"], 50 / 101); self.assertEqual(row["cross_provider_volume_to_supply"], .5); self.assertEqual(row["market_cap_to_supply_ratio"], 1.01)

    def test_non_primary_market_rows_do_not_enter(self):
        self.assertEqual(build_rows([], [{"asset_id": "x", "date": "2026-01-01"}]), [])


if __name__ == "__main__": unittest.main()
