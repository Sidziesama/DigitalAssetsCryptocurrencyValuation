import unittest
from datetime import date

from src.pipeline.binance_klines import klines_url, normalize, select_pairs


class BinanceKlinesTests(unittest.TestCase):
    def test_selects_quote_by_declared_priority(self):
        assets = [{"asset_id": "btc", "symbol": "BTC"}]
        info = {"symbols": [{"symbol": "BTCUSDC", "baseAsset": "BTC", "quoteAsset": "USDC"}, {"symbol": "BTCUSDT", "baseAsset": "BTC", "quoteAsset": "USDT"}]}
        resolved, _ = select_pairs(assets, info)
        self.assertEqual(resolved["btc"]["symbol"], "BTCUSDT")

    def test_url_is_utc_daily_and_bounded(self):
        url = klines_url("https://example.test/api/v3", "BTCUSDT", date(2026, 1, 1), date(2026, 1, 2))
        self.assertIn("interval=1d", url); self.assertIn("limit=1000", url); self.assertIn("symbol=BTCUSDT", url)

    def test_normalizes_quote_volume(self):
        payload = [[1767225600000, "1", "2", "0.5", "1.5", "10", 0, "15", 7, "6", "9", "0"]]
        rows = normalize(payload, date(2026, 1, 1), date(2026, 1, 1))
        self.assertEqual(rows[0]["volume_quote"], 15.0); self.assertEqual(rows[0]["trade_count"], 7)


if __name__ == "__main__": unittest.main()
