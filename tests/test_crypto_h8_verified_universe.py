import unittest
from src.pipeline.crypto_h8_verified_universe import loo_rmse, ols, ranks, validate, winsorize

class Tests(unittest.TestCase):
    def test_validate_requires_frozen_design(self):
        with self.assertRaises(ValueError): validate({"status":"draft","expected_assets":23,"group_models":list(range(8)),"primary_comparison_metric":"leave_one_asset_out_root_mean_squared_prediction_error"})
    def test_ols_and_loo_recover_line(self):
        x=[[float(i)] for i in range(1,7)]; y=[1+2*r[0] for r in x]
        self.assertEqual(ols(x,y),[1.0,2.0]); self.assertAlmostEqual(loo_rmse(x,y),0.0)
    def test_rank_ties_and_winsorization(self):
        self.assertEqual(ranks([3,1,1]),[3,1.5,1.5]); self.assertEqual(winsorize([0,1,2,3,100],.2),[0,1,2,3,3])

if __name__=="__main__": unittest.main()
