import unittest
from datetime import date
from unittest.mock import patch
import urllib.error

from src.pipeline.coinpaprika_market import historical_url, normalize_daily, request_json, resolve_provider_ids


class CoinPaprikaMarketTests(unittest.TestCase):
    def test_historical_url(self):
        url = historical_url("https://example.test/v1", "btc-bitcoin", date(2026, 1, 1), date(2026, 1, 2))
        self.assertIn("btc-bitcoin", url)
        self.assertIn("interval=1d", url)
        self.assertIn("quote=usd", url)

    def test_normalizes_utc_and_last_observation(self):
        payload = [
            {"timestamp": "2026-01-01T00:00:00Z", "price": 1, "market_cap": 10, "volume_24h": 3},
            {"timestamp": "2026-01-01T12:00:00Z", "price": 2, "market_cap": 20, "volume_24h": 4},
        ]
        self.assertEqual(normalize_daily(payload), [{"date": "2026-01-01", "price_usd": 2, "market_cap_usd": 20, "volume_24h_usd": 4}])

    def test_resolver_requires_unique_symbol_or_exact_name(self):
        assets = [{"asset_id": "btc", "symbol": "BTC", "name": "Bitcoin"}, {"asset_id": "x", "symbol": "X", "name": "Unknown"}]
        coins = [
            {"id": "btc-bitcoin", "symbol": "BTC", "name": "Bitcoin", "is_active": True},
            {"id": "x-one", "symbol": "X", "name": "One", "is_active": True},
            {"id": "x-two", "symbol": "X", "name": "Two", "is_active": True},
        ]
        resolved, unresolved = resolve_provider_ids(assets, coins)
        self.assertEqual(resolved["btc"], "btc-bitcoin")
        self.assertEqual(unresolved["x"], "ambiguous")

    @patch("src.pipeline.coinpaprika_market.urllib.request.urlopen")
    def test_non_retryable_http_error_is_raised(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError("https://example.test", 402, "payment", {}, None)
        with self.assertRaises(urllib.error.HTTPError):
            request_json("https://example.test")


if __name__ == "__main__":
    unittest.main()
