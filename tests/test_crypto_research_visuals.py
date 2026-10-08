import unittest
from src.pipeline.crypto_research_visuals import build

class Tests(unittest.TestCase):
    def test_builds_three_accessible_svgs(self):
        groups={"group_counts":{"monetary_store":2,"holder_capture":1}}
        h8=[{"outcome":"mean_log_market_cap_usd","model_id":"raw_function_breadth","loo_rmse":"2"},{"outcome":"mean_log_market_cap_usd","model_id":"bundle_monetary_store","loo_rmse":"1.5","fdr_10pct_reject":"1"}]
        register=[{"hypothesis":h,"sample":"sample"} for h in ("H1","H2","H3","H4","H8")]
        result=build(groups,h8,register)
        self.assertEqual(len(result),3)
        self.assertTrue(all('role="img"' in svg and svg.endswith("</svg>\n") for svg in result.values()))

if __name__=="__main__": unittest.main()
