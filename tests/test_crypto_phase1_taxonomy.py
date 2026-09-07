import unittest

from src.pipeline.crypto_economic_design import CODES
from src.pipeline.crypto_phase1_taxonomy import build, validate


def spec():
    return {
        "schema_version":1,"phase":"phase_1_cryptoasset_economic_function_taxonomy",
        "verified_core_assets":[f"crypto_{x}" for x in "abcdef"],
        "architecture_context":{f"crypto_{x}":"test" for x in "abcdef"},
        "value_indicators":{code:["indicator"] for code in CODES},
        "bundles":{"money":["VA_MONETARY","VA_SCARCITY"],"demand":["VA_GAS","VA_UTILITY"],
                   "stake":["VA_STAKE"],"burn":["VA_BURN"],"collateral":["VA_COLLATERAL"],
                   "governance":["VA_GOV"],"capture":["VA_PROTOCOL"],"incentive":["VA_INCENTIVE"]},
        "experiments":[{"id":"x"},{"id":"y"},{"id":"z"}]
    }


class CryptoPhase1TaxonomyTests(unittest.TestCase):
    def test_bundles_must_partition_codes(self):
        value=spec(); value["bundles"]["stake"].append("VA_GAS")
        with self.assertRaisesRegex(ValueError,"partition"):
            validate(value)

    def test_unknown_is_preserved_and_blocks_breadth(self):
        decisions=[]
        for asset in spec()["verified_core_assets"]:
            for code in CODES:
                if asset == "crypto_a" and code == "VA_MONETARY": continue
                decisions.append({"asset_id":asset,"code":code,"status":"verified","recommended_value":int(code == "VA_GAS")})
        result=build(spec(),decisions,{asset:asset[-1].upper() for asset in spec()["verified_core_assets"]})
        first=result["profiles"][0]
        self.assertIsNone(first["va_monetary"])
        self.assertIsNone(first["raw_function_breadth"])
        self.assertEqual(first["classification_status"],"partial_unresolved")

    def test_verified_profiles_compute_breadth_and_bundles(self):
        decisions=[{"asset_id":asset,"code":code,"status":"verified","recommended_value":int(code in {"VA_GAS","VA_UTILITY"})}
                   for asset in spec()["verified_core_assets"] for code in CODES]
        first=build(spec(),decisions,{})["profiles"][0]
        self.assertEqual(first["raw_function_breadth"],2)
        self.assertEqual(first["bundle_demand"],1)
        self.assertEqual(first["active_bundle_count"],1)

    def test_duplicate_evidence_is_rejected(self):
        row={"asset_id":"crypto_a","code":"VA_GAS","status":"verified","recommended_value":1}
        with self.assertRaisesRegex(ValueError,"duplicate"):
            build(spec(),[row,row],{})


if __name__ == "__main__": unittest.main()
