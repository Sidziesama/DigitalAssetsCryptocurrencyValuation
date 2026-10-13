import unittest
from src.pipeline.crypto_h1_activity_history import normalize, url


class Tests(unittest.TestCase):
    def test_url_and_normalization_preserve_scope(self):
        request = url("https://example.test/v4", "btc", ["AdrActCnt", "TxCnt"], "2026-01-01", "2026-01-02")
        self.assertIn("assets=btc", request); self.assertIn("AdrActCnt", request)
        payload = {"data": [{"asset": "btc", "time": "2026-01-01T00:00:00Z", "AdrActCnt": "5", "TxCnt": "8"}, {"asset": "eth", "time": "2026-01-01", "AdrActCnt": "9", "TxCnt": "9"}]}
        rows = normalize(payload, "crypto_btc", "btc", "2026-01-01", "2026-01-02")
        self.assertEqual(len(rows), 1); self.assertEqual(rows[0]["active_addresses"], 5)


if __name__ == "__main__": unittest.main()
