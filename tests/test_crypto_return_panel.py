import math
import unittest
from datetime import date, timedelta

from src.pipeline.crypto_return_panel import build


def spec():
    return {"schema_version":1,"document_version":"test","status":"frozen_before_return_estimation","freeze_date":"2026-09-07",
            "source":"x","quote_asset":"USDT","start_date":"2024-01-01","end_date":"2026-12-31","minimum_asset_days":30,"max_gap_days":3,
            "risk_free_rate":"zero","interpretation":"test"}


def rows(days=60, gap_day=None):
    out=[]; first=date(2024,1,1)
    for asset,growth in (("crypto_btc",0.01),("crypto_eth",0.02),("short",0.0)):
        n=days if asset!="short" else 10
        for i in range(n):
            if gap_day is not None and i==gap_day and asset=="crypto_eth": continue
            out.append({"asset_id":asset,"date":(first+timedelta(days=i)).isoformat(),"quote_asset":"USDT",
                        "close_quote":str(100*math.exp(growth*i)),"volume_quote":"1000"})
    return out


class CryptoReturnPanelTests(unittest.TestCase):
    def test_returns_market_and_exclusions(self):
        panel,summary=build(spec(),rows())
        self.assertEqual(summary["assets_included"],2); self.assertEqual(summary["assets_excluded"],1)
        btc=[r for r in panel if r["asset_id"]=="crypto_btc"]
        self.assertAlmostEqual(btc[0]["log_return"],0.01); self.assertAlmostEqual(btc[0]["market_ew_log_return"],0.015)
        self.assertAlmostEqual(btc[0]["btc_log_return"],0.01); self.assertAlmostEqual(btc[0]["forward_log_return_7d"],0.07)
        self.assertIsNone(btc[-1]["forward_log_return_7d"]); self.assertAlmostEqual(btc[40]["momentum_30d_skip7"],0.30)

    def test_gap_breaks_return(self):
        panel,_=build(spec(),rows(gap_day=5))
        eth={r["date"]:r for r in panel if r["asset_id"]=="crypto_eth"}
        self.assertNotIn("2024-01-06",eth); self.assertIn("2024-01-07",eth)
        self.assertAlmostEqual(eth["2024-01-07"]["log_return"],0.04)

    def test_wrong_quote_is_ignored(self):
        bad=[dict(r,quote_asset="BUSD") for r in rows()]
        with self.assertRaisesRegex(ValueError,"at least one asset"):
            build(spec(),bad)


if __name__=="__main__": unittest.main()
