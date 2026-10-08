import unittest
from src.pipeline.crypto_hypothesis_register import QUESTIONS, build

class Tests(unittest.TestCase):
    def test_register_covers_active_hypotheses(self):
        findings={"findings":{
            "H1":{"transaction_count_coefficient":1,"transaction_count_exact_p":.2},
            "H2":{"pooled_market_cap_interaction":.1,"pooled_market_cap_exact_p":.08},
            "H3":{"assets":4,"assets_with_within_supply_variation":2,"supply_growth_coefficient":1,"exact_p":.5},
            "H4":{"assets":6,"positive_assets_with_historical_staking":1},
            "H8":{"verified_universe_assets":23,"verified_universe_decision":"theory_groups_favored","verified_universe_best_group":"bundle_financial_integration","verified_universe_best_group_loo_rmse":1.7,"verified_universe_raw_breadth_loo_rmse":1.8}}}
        strict={"results":[{"specification":"pooled_market_cap","strict_coefficient":.05,"strict_p":.4}]}
        rows=build(findings,strict)
        self.assertEqual([r["hypothesis"] for r in rows],list(QUESTIONS))
        self.assertEqual(rows[-1]["result"],"theory_groups_favored")

if __name__=="__main__": unittest.main()
