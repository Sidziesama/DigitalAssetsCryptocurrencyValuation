import unittest

from src.pipeline.aave_collateral_state import decode_configuration,encode_call,validate


class AaveCollateralStateTests(unittest.TestCase):
    def test_call_encoding_pads_address(self):
        data=encode_call("0xc44b11f7","0x"+"12"*20)
        self.assertEqual(len(data),2+8+64); self.assertTrue(data.endswith("12"*20))

    def test_decodes_positive_ltv_and_flags(self):
        bitmap=8050 | (8300<<16) | (10500<<32) | (18<<48) | (1<<56)
        row=decode_configuration(hex(bitmap))
        self.assertEqual(row["ltv_bps"],8050); self.assertEqual(row["active"],1); self.assertEqual(row["paused"],0)

    def test_rejects_unexpected_selector(self):
        spec={"schema_version":1,"chain":"ethereum","pool_address":"0x"+"1"*40,"rpc_url":"https://rpc.test","block_lookup_base":"https://blocks.test","method":"getConfiguration(address)","selector":"0xdeadbeef","assets":[{"asset_id":"crypto_x","reserve_symbol":"X","reserve_address":"0x"+"2"*40}]}
        with self.assertRaisesRegex(ValueError,"selector"): validate(spec)

    def test_rejects_unsafe_snapshot_namespace(self):
        spec={"schema_version":1,"snapshot_namespace":"../bad","chain":"ethereum","pool_address":"0x"+"1"*40,"rpc_url":"https://rpc.test","block_lookup_base":"https://blocks.test","method":"getConfiguration(address)","selector":"0xc44b11f7","assets":[{"asset_id":"crypto_x","reserve_symbol":"X","reserve_address":"0x"+"2"*40}]}
        with self.assertRaisesRegex(ValueError,"namespace"): validate(spec)


if __name__=="__main__": unittest.main()
