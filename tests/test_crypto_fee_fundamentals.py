import unittest
from datetime import date

from src.pipeline.crypto_fee_fundamentals import build_url, normalize, validate


class CryptoFeeFundamentalsTests(unittest.TestCase):
    def test_url_declares_metric(self):
        url=build_url("overview/fees/bitcoin","dailyRevenue")
        self.assertIn("dataType=dailyRevenue",url); self.assertIn("excludeTotalDataChartBreakdown=true",url)

    def test_normalize_preserves_zero_and_scope(self):
        payload={"totalDataChart":[[1735689600,0],[1735776000,-1]]}
        rows=normalize({"asset_id":"crypto_x","scope":"chain","economic_system":"X"},"dailyFees","fees_usd",payload,date(2025,1,1),date(2025,1,2))
        self.assertEqual(len(rows),1); self.assertEqual(rows[0]["value_usd"],0); self.assertEqual(rows[0]["scope"],"chain")

    def test_rejects_scope_drift(self):
        spec={"schema_version":1,"provider":"defillama_free_fees_api","assets":[{"asset_id":f"x{i}","scope":"token","endpoint":"x","economic_system":"x"} for i in range(6)],"metrics":{"dailyFees":"fees_usd","dailyRevenue":"protocol_revenue_usd","dailyHoldersRevenue":"holders_revenue_usd"},"interpretation":"x"}
        with self.assertRaisesRegex(ValueError,"scope"): validate(spec)


if __name__=="__main__": unittest.main()
