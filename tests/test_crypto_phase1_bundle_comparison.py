import unittest

from src.pipeline.crypto_phase1_bundle_comparison import build

ASSETS=["a","b","c","d","e","f"]


def spec():
    return {"schema_version":1,"document_version":"test","status":"frozen_before_comparison_estimation","freeze_date":"2026-09-07",
            "experiment_id":"P1_H3","assets":ASSETS,"profiles":"p","panel":"q",
            "outcomes":{"mean_log_market_cap_usd":"x","mean_log_market_cap_to_daily_fees":"y"},"withheld_outcomes":{},
            "models":[{"id":"raw_breadth","predictors":["raw_function_breadth"],"role":"benchmark_count"},
                      {"id":"active_bundle_count","predictors":["active_bundle_count"],"role":"bundle_count"},
                      {"id":"bundle_holder_capture","predictors":["bundle_holder_capture"],"role":"single_bundle"},
                      {"id":"flat","predictors":["bundle_flat"],"role":"single_bundle"},
                      {"id":"raw_breadth_plus_holder_capture","predictors":["raw_function_breadth","bundle_holder_capture"],"role":"nested_theory_addition"}],
            "nested_pair":{"restricted":"raw_breadth","extended":"raw_breadth_plus_holder_capture","reason":"r"},
            "comparison_metric":"loo","selection_rule":"s","interpretation":"i"}


def profiles(status="complete_verified"):
    return [{"asset_id":a,"classification_status":status,"raw_function_breadth":str(i+1),"active_bundle_count":str(i+1),
             "bundle_holder_capture":str(i%2),"bundle_flat":"1"} for i,a in enumerate(ASSETS)]


def panel():
    rows=[]
    for i,a in enumerate(ASSETS):
        for _ in range(3):
            rows.append({"asset_id":a,"market_cap_usd":str(10**(i+3)),"fees_usd_lag1":"10"})
    return rows


class CryptoPhase1BundleComparisonTests(unittest.TestCase):
    def test_builds_and_flags_unestimable_model(self):
        rows,summary=build(spec(),profiles(),panel())
        self.assertEqual(summary["unestimable_models"],["flat"])
        self.assertEqual(len(rows),10)
        breadth=[r for r in rows if r["model_id"]=="raw_breadth" and r["outcome"]=="mean_log_market_cap_usd"][0]
        self.assertAlmostEqual(breadth["spearman_rank_correlation"],1.0)
        self.assertLess(breadth["leave_one_out_rmse"],0.5)
        self.assertEqual(len(summary["comparison"]),2)

    def test_incomplete_profile_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"complete verified"):
            build(spec(),profiles(status="partial"),panel())

    def test_nested_pair_must_be_listed(self):
        bad=spec(); bad["nested_pair"]["extended"]="missing"
        with self.assertRaisesRegex(ValueError,"nested pair"):
            build(bad,profiles(),panel())


if __name__=="__main__": unittest.main()
