import unittest
from datetime import date, timedelta

from src.pipeline.crypto_return_factor_baseline import build, max_drawdown, newey_west_t

ASSETS=["crypto_btc","crypto_eth","crypto_bnb","crypto_uni","crypto_aave","crypto_arb"]+[f"o{i}" for i in range(6)]


def spec():
    return {"schema_version":1,"document_version":"test","status":"frozen_before_baseline_estimation","freeze_date":"2026-09-07",
            "panel":"p","profiles":"q","market_model":{"factor":"market_ew_log_return","minimum_days":10},
            "fama_macbeth":{"outcome":"log_return","predictors":["market_beta_180d_lag1"],"lag_predictors_one_day":True,"minimum_assets_per_day":5,"newey_west_lags":2},
            "function_sorts":{"assets":ASSETS[:6],"bundles":["bundle_monetary_store","bundle_flat"],"common_window_rule":"r","newey_west_lags":2},
            "selection_rule":"s","interpretation":"i"}


def panel(days=40):
    rows=[]; first=date(2024,1,1)
    for i in range(days):
        market=0.01*((i%3)-1)
        for j,asset in enumerate(ASSETS):
            beta=0.5+0.1*j
            rows.append({"asset_id":asset,"date":(first+timedelta(days=i)).isoformat(),"log_return":str(beta*market+0.001*j),
                         "market_ew_log_return":str(market),"market_beta_180d_lag1":str(beta)})
    return rows


def profiles():
    return [{"asset_id":a,"bundle_monetary_store":"1" if a in ("crypto_btc","crypto_eth") else "0","bundle_flat":"1"} for a in ASSETS[:6]]


class CryptoReturnFactorBaselineTests(unittest.TestCase):
    def test_market_models_recover_betas(self):
        summary=build(spec(),panel(),profiles())
        models={m["asset_id"]:m for m in summary["market_model"]["per_asset"]}
        self.assertAlmostEqual(models["crypto_btc"]["market_beta"],0.5,places=6)
        self.assertAlmostEqual(models["o5"]["market_beta"],1.6,places=6)
        self.assertEqual(summary["fama_macbeth"]["cross_sections"],39)
        sorts={s["bundle"]:s for s in summary["function_sorts"]["sorts"]}
        self.assertEqual(sorts["bundle_flat"]["status"],"no_variation")
        self.assertEqual(sorts["bundle_monetary_store"]["positive_assets"],["crypto_btc","crypto_eth"])
        self.assertEqual(summary["function_sorts"]["common_days"],40)

    def test_helpers(self):
        self.assertAlmostEqual(max_drawdown([0.1,-0.3,0.1]),-0.3)
        mean,se,t=newey_west_t([1.0,1.0,1.0,1.0],1)
        self.assertEqual(mean,1.0); self.assertEqual(se,0.0)

    def test_missing_profile_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"profile for every"):
            build(spec(),panel(),profiles()[:3])


if __name__=="__main__": unittest.main()
