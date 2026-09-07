import unittest

from src.pipeline.crypto_h2_strict_capture_sensitivity import relabel, validate


def spec():
    return {"schema_version":1,"status":"frozen_before_sensitivity_estimation","specifications":["pooled_market_cap"],
            "overrides":[{"asset_id":"x","code":"VA_PROTOCOL","value":0,"applies_from":"2026-01-01"}],
            "selection_rule":"s","interpretation":"i"}


class CryptoH2StrictCaptureSensitivityTests(unittest.TestCase):
    def test_relabel_recomputes_capture_and_interaction(self):
        rows=[{"asset_id":"x","date":"2026-02-01","va_burn_effective":"0","va_protocol_effective":"1","h2_active_capture":"1",
               "log1p_fees_usd_lag1":"2.0","fees_x_capture":"2.0"},
              {"asset_id":"x","date":"2025-12-01","va_burn_effective":"0","va_protocol_effective":"1","h2_active_capture":"1",
               "log1p_fees_usd_lag1":"2.0","fees_x_capture":"2.0"},
              {"asset_id":"y","date":"2026-02-01","va_burn_effective":"1","va_protocol_effective":"0","h2_active_capture":"1",
               "log1p_fees_usd_lag1":"3.0","fees_x_capture":"3.0"}]
        out,changed=relabel(rows,spec()["overrides"])
        self.assertEqual(changed,1)
        self.assertEqual((out[0]["va_protocol_effective"],out[0]["h2_active_capture"],out[0]["fees_x_capture"]),("0","0","0.0"))
        self.assertEqual(out[1]["fees_x_capture"],"2.0")
        self.assertEqual(out[2]["fees_x_capture"],"3.0")

    def test_invalid_specification_is_rejected(self):
        bad=spec(); bad["specifications"]=["unknown"]
        with self.assertRaisesRegex(ValueError,"unknown H2 specification"):
            validate(bad)


if __name__=="__main__": unittest.main()
