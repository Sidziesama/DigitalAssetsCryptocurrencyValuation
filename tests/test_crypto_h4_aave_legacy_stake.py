import unittest

from src.pipeline.crypto_h4_aave_legacy_stake import decode_total_supply, normalize, validate


class CryptoH4AaveLegacyStakeTests(unittest.TestCase):
    def spec(self):
        return {"schema_version":1,"universe_policy":"fixed_existing_six_assets_no_expansion",
                "assets":["a","b","c","d","e","f"], "aave_legacy_component":{
                    "asset_id":"crypto_aave","component_id":"legacy_stkaave","method":"totalSupply()",
                    "selector":"0x18160ddd","decimals":18,"contract_address":"0x"+"1"*40,
                    "rpc_url":"https://rpc.test","measurement_role":"legacy_component_only",
                    "unblocks_h4":False,"limitation":"component only"}}

    def test_decodes_erc20_supply(self):
        self.assertEqual(decode_total_supply(hex(25 * 10**18), 18), 25.0)

    def test_normalize_keeps_component_label(self):
        component = validate(self.spec())
        row = normalize(component, "2026-01-01", 10, {"result":hex(3 * 10**18)})
        self.assertEqual(row["staked_native_units"], 3.0)
        self.assertEqual(row["measurement_role"], "legacy_component_only")

    def test_component_cannot_claim_to_unblock_h4(self):
        spec = self.spec(); spec["aave_legacy_component"]["unblocks_h4"] = True
        with self.assertRaisesRegex(ValueError, "must not"):
            validate(spec)


if __name__ == "__main__":
    unittest.main()
