import unittest

from src.pipeline.crypto_h8_six_asset_extension import build


def spec():
    return {"schema_version":1,"document_version":"test","status":"frozen_before_extension_estimation","freeze_date":"2026-09-06",
            "assets":["crypto_bnb","a","b","c","d","e"],"outcome":"market","predictor":"breadth",
            "selection_rule":"Evidence-first frozen selection.","interpretation":"Exploratory extension only."}


class CryptoH8SixAssetExtensionTests(unittest.TestCase):
    def test_exact_six_asset_extension(self):
        readiness=[{"asset_id":asset,"h8_design_ready":"1","h8_value_accrual_breadth":str(i+1)} for i,asset in enumerate(spec()["assets"])]
        market=[{"asset_id":asset,"market_cap_usd":str(100*(i+1))} for i,asset in enumerate(spec()["assets"]) for _ in range(2)]
        rows,summary=build(spec(),readiness,market)
        self.assertEqual(len(rows),6); self.assertEqual(summary["permutations"],720); self.assertGreater(summary["slope"],0)

    def test_missing_complete_asset_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"every frozen"):
            build(spec(),[],[])


if __name__=="__main__": unittest.main()
