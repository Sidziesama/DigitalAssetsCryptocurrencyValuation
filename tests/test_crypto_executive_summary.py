import unittest

from src.pipeline.crypto_executive_summary import build, render


class Tests(unittest.TestCase):
    def test_summary_translates_results_into_actions(self):
        findings={"findings":{"H8":{"verified_universe_best_group_loo_rmse":1.75,"verified_universe_raw_breadth_loo_rmse":1.80},"H3":{"supply_events_estimated":17,"supply_event_assets":["a","b","c"],"supply_events_matching_predicted_sign":8}}}
        result=build(findings)
        self.assertEqual(len(result["rows"]),5)
        self.assertIn("due-diligence",result["headline"])
        self.assertIn("Do not use an unlock",render(result))
        self.assertEqual(result["rows"][-1]["strength"],"not_tested")


if __name__ == "__main__": unittest.main()
