import unittest
from datetime import date

from src.pipeline.cryptocompare_volume import batch_ranges, histoday_url, response_rows, resolve_symbols


class CryptoCompareVolumeTests(unittest.TestCase):
    def test_batches_cover_long_window_without_overlap(self):
        batches = batch_ranges(date(2019, 1, 1), date(2026, 8, 22))
        self.assertEqual(batches[0][1], date(2026, 8, 22))
        self.assertEqual(batches[-1][0], date(2019, 1, 1))
        self.assertTrue(all((end - start).days + 1 <= 2000 for start, end in batches))
        self.assertTrue(all(batches[i][0] - date.resolution == batches[i + 1][1] for i in range(len(batches) - 1)))

    def test_url_has_research_market_definition(self):
        url = histoday_url("https://example.test/data", "btc", date(2026, 1, 2), 20)
        self.assertIn("fsym=BTC", url)
        self.assertIn("tsym=USD", url)
        self.assertIn("e=CCCAGG", url)
        self.assertIn("limit=20", url)

    def test_response_drops_provider_zero_padding(self):
        payload = {"Data": {"Data": [
            {"time": 1577836800, "open": 0, "high": 0, "low": 0, "close": 0, "volumeto": 0},
            {"time": 1577923200, "open": 1, "high": 2, "low": 1, "close": 2, "volumefrom": 3, "volumeto": 4, "conversionType": "direct", "conversionSymbol": ""},
        ]}}
        rows = response_rows(payload, date(2020, 1, 1), date(2020, 1, 2))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["volume_quote_usd"], 4)

    def test_name_check_rejects_symbol_collision(self):
        assets = [{"asset_id": "x", "symbol": "TON", "name": "Toncoin"}]
        resolved, unresolved = resolve_symbols(assets, {"Data": {"TON": {"CoinName": "Tokamak Network"}}})
        self.assertFalse(resolved)
        self.assertEqual(unresolved["x"], "name_mismatch")


if __name__ == "__main__":
    unittest.main()
