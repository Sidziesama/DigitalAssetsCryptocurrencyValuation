import unittest

from src.pipeline.crypto_h4_bnb_stake import decode_get_validators, decode_uint, encode_get_validators, validate


def word(value: int) -> str: return f"{value:064x}"
def address(value: int) -> str: return word(value)


class CryptoH4BnbStakeTests(unittest.TestCase):
    def test_call_encoding(self):
        self.assertEqual(encode_get_validators("0xbff02e20",0,1000),"0xbff02e20"+word(0)+word(1000))

    def test_decodes_dynamic_validator_arrays(self):
        # Head: first array at word 3, second at word 6, total length 2.
        payload="0x"+word(96)+word(192)+word(2)+word(2)+address(1)+address(2)+word(2)+address(3)+address(4)
        operators,credits,total=decode_get_validators(payload)
        self.assertEqual(operators,["0x"+"0"*39+"1","0x"+"0"*39+"2"])
        self.assertEqual(credits,["0x"+"0"*39+"3","0x"+"0"*39+"4"])
        self.assertEqual(total,2)

    def test_uint_and_fixed_configuration(self):
        self.assertEqual(decode_uint(hex(5*10**18)),5*10**18)
        spec={"schema_version":1,"universe_policy":"fixed_existing_six_assets_no_expansion","bnb_consensus_stake":{
            "asset_id":"crypto_bnb","stake_hub_address":"0x0000000000000000000000000000000000002002",
            "get_validators_selector":"0xbff02e20","total_pooled_bnb_selector":"0x15d1f898",
            "rpc_url":"https://rpc.test","block_lookup_base":"https://blocks.test"}}
        self.assertEqual(validate(spec)["asset_id"],"crypto_bnb")


if __name__ == "__main__": unittest.main()
