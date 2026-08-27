import unittest
import urllib.error
from datetime import date

from unittest.mock import patch

from src.pipeline.crypto_fundamentals import coverage, normalize, request_available, timeseries_url, validate_sources


class CryptoFundamentalsTests(unittest.TestCase):
    def test_url_declares_daily_metrics(self):
        url=timeseries_url("https://example.test/v4","btc",date(2026,1,1),date(2026,1,2))
        self.assertIn("assets=btc",url); self.assertIn("AdrActCnt",url); self.assertIn("frequency=1d",url)

    def test_normalize_calculates_transfer_to_market_cap(self):
        payload={"data":[{"asset":"btc","time":"2026-01-01T00:00:00Z","AdrActCnt":"1","TxCnt":"2","TxTfrCnt":"25","CapMrktCurUSD":"100","SplyCur":"5"}]}
        row=normalize("crypto_btc","btc",payload,date(2026,1,1),date(2026,1,1))[0]
        self.assertEqual(row["transfer_count"],25)

    def test_coverage_does_not_treat_partial_as_pass(self):
        rows=[{"active_addresses":1,"transaction_count":2,"transfer_count":3,"market_cap_usd":4,"current_supply":5}]
        result=coverage("crypto_x","x",rows,date(2026,1,1),date(2026,1,1))
        self.assertEqual(result["monetary_behavior_status"],"pass"); self.assertEqual(result["free_market_baseline_status"],"pass")

    def test_source_mapping_must_reference_crypto_registry(self):
        registry={"schema_version":1,"assets":[{"asset_id":"stable_x","symbol":"X","name":"X","universe":"stablecoin","tier":"x","coingecko_id":"x"}]}
        spec={"schema_version":1,"provider":"coinmetrics_community","assets":[{"asset_id":"stable_x","provider_id":"x"}]}
        with self.assertRaisesRegex(ValueError,"invalid"):
            validate_sources(spec,registry)

    def test_provider_unsupported_asset_becomes_explicit_empty_payload(self):
        error=urllib.error.HTTPError("https://example.test",400,"bad",{},None)
        error.read=lambda: b'{"error":{"message":"unsupported"}}'
        with patch("src.pipeline.crypto_fundamentals.request_json",side_effect=error):
            payload=request_available("https://example.test")
        self.assertEqual(payload["data"],[])
        self.assertIn("availability_error",payload)


if __name__ == "__main__": unittest.main()
