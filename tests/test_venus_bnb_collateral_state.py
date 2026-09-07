import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.pipeline.venus_bnb_collateral_state import decode_market, materiality_days, validate


class VenusBnbCollateralStateTests(unittest.TestCase):
    def test_decode_listed_positive_factor(self):
        payload="0x"+f"{1:064x}"+f"{8*10**17:064x}"+f"{1:064x}"
        result=decode_market(payload)
        self.assertEqual(result["listed"],1); self.assertEqual(result["collateral_factor"],0.8)
        self.assertEqual(result["collateral_enabled"],1)

    def test_decode_rejects_short_or_invalid_flag(self):
        with self.assertRaises(ValueError): decode_market("0x01")
        with self.assertRaises(ValueError): decode_market("0x"+f"{2:064x}"+f"{1:064x}")

    def test_materiality_preserves_daily_threshold(self):
        with tempfile.TemporaryDirectory() as folder:
            repo=Path(folder); path=repo/"data/processed/evidence/crypto_collateral_daily_proxy.csv"
            path.parent.mkdir(parents=True); path.write_text("asset_id,date,material_proxy\ncrypto_bnb,2026-01-01,1\ncrypto_eth,2026-01-01,1\n")
            self.assertEqual(materiality_days(repo,date(2026,1,1),date(2026,1,1)),{"2026-01-01":1})

    def test_configuration_requires_official_https_sources(self):
        value={"schema_version":1,"chain":"bsc","asset_id":"crypto_bnb","method":"markets(address)","selector":"0x8e8f294b",
               "rpc_url":"https://x","block_lookup_base":"https://x","official_deployment_source":"https://x","official_method_source":"https://x",
               "comptroller_address":"0x"+"1"*40,"vtoken_address":"0x"+"2"*40}
        validate(value); value["official_method_source"]="http://x"
        with self.assertRaises(ValueError): validate(value)


if __name__ == "__main__": unittest.main()
