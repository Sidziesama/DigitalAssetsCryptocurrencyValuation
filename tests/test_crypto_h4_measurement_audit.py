import unittest
from src.pipeline.crypto_h4_measurement_audit import build, chart

class Tests(unittest.TestCase):
    def test_audit_separates_consensus_and_aave_case(self):
        audit=[{"asset_id":"crypto_eth","va_stake":1,"staking_history_days":0,"minimum_history_days":365,"positive_staking_history_ready":False},{"asset_id":"crypto_bnb","va_stake":1,"staking_history_days":90,"minimum_history_days":365,"positive_staking_history_ready":False},{"asset_id":"crypto_aave","va_stake":1,"staking_history_days":90,"minimum_history_days":365,"positive_staking_history_ready":False}]
        result=build({"audit":audit,"identification_ready":False})
        self.assertFalse(result["pooled_estimation_ready"]); self.assertIn("not AAVE-denominated",result["boundary_decision"])
        self.assertIn('role="img"',chart(result))

if __name__=="__main__": unittest.main()
