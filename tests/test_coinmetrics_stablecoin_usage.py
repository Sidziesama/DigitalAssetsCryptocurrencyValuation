import unittest
from datetime import date

from src.pipeline.coinmetrics_stablecoin_usage import coverage, normalize, timeseries_url


class CoinMetricsStablecoinUsageTests(unittest.TestCase):
    def test_url_has_explicit_metrics_and_daily_frequency(self):
        url = timeseries_url("https://example.test/v4", "usdc", date(2026, 1, 1), date(2026, 1, 2))
        self.assertIn("assets=usdc", url)
        self.assertIn("frequency=1d", url)
        self.assertIn("AdrActCnt%2CTxCnt%2CTxTfrCnt", url)

    def test_normalize_requires_exact_provider_asset(self):
        payload = {"data": [
            {"asset": "usdc", "time": "2026-01-01T00:00:00Z", "AdrActCnt": "10", "TxCnt": "20", "TxTfrCnt": "30"},
            {"asset": "usdt", "time": "2026-01-01T00:00:00Z", "AdrActCnt": "99"},
        ]}
        rows = normalize("stable_usdc", "usdc", payload, date(2026, 1, 1), date(2026, 1, 1))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["active_addresses"], 10)
        self.assertEqual(rows[0]["token_transfer_count"], 30)

    def test_unsupported_is_explicit(self):
        row = coverage("stable_x", None, [], date(2026, 1, 1), date(2026, 1, 2))
        self.assertEqual(row["status"], "unsupported")
        self.assertEqual(row["supported"], 0)


if __name__ == "__main__":
    unittest.main()
