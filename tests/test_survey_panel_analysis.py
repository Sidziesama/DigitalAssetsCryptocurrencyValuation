"""The frozen plan's decision rules must behave exactly as written.

Every case here is driven by synthetic responses. None of it touches real
responses, and none of these numbers is a finding.
"""
import json
import unittest
from collections import Counter
from pathlib import Path

from src.pipeline.survey_panel_analysis import (build, classify_consensus, cohen_kappa,
                                                krippendorff_alpha_nominal, load_reference, spearman)
from src.pipeline.survey_synthetic_responses import SCENARIOS, run as generate

REPO = Path(__file__).resolve().parents[1]
TH = {"adopt": 0.70, "leaning": 0.50}
PLAN = json.loads((REPO / "config/survey_analysis_plan.json").read_text())
ITEMS = json.loads((REPO / "config/survey_items.json").read_text())


class ConsensusLadderTests(unittest.TestCase):
    def test_exact_fifty_fifty_is_divided_not_leaning(self):
        r = classify_consensus(Counter({"A": 6, "B": 6}), "Depends", TH, 8)
        self.assertEqual(r["level"], "divided")
        self.assertIsNone(r["leader"])
        self.assertEqual(r["tied_options"], ["A", "B"])

    def test_leaning_requires_a_unique_plurality(self):
        r = classify_consensus(Counter({"A": 6, "B": 4}), "Depends", TH, 8)
        self.assertEqual(r["level"], "leaning")
        self.assertEqual(r["validation_status"], "unresolved")

    def test_seventy_percent_adopts(self):
        r = classify_consensus(Counter({"A": 7, "B": 3}), "Depends", TH, 8)
        self.assertEqual(r["level"], "consensus_adopt")
        self.assertEqual(r["validation_status"], "externally_validated")

    def test_condition_dependent_consensus_never_validates(self):
        r = classify_consensus(Counter({"Depends": 8, "A": 2}), "Depends", TH, 8)
        self.assertEqual(r["level"], "consensus_condition_dependent")
        self.assertEqual(r["validation_status"], "unresolved")

    def test_under_powered_below_minimum(self):
        r = classify_consensus(Counter({"A": 3}), "Depends", TH, 8)
        self.assertEqual(r["level"], "under_powered")
        self.assertEqual(r["validation_status"], "unresolved")

    def test_only_consensus_adopt_maps_to_external_validation(self):
        for label, spec in {l["label"]: l for l in PLAN["consensus"]["levels"]}.items():
            if label != "consensus_adopt":
                self.assertIn("UNRESOLVED", spec["effect"] + spec["rule"] + label.upper(),
                              f"{label} must not read as validated")


class CoefficientEdgeCaseTests(unittest.TestCase):
    def test_cohen_kappa_undefined_when_both_use_one_category(self):
        r = cohen_kappa(["Yes"] * 6, ["Yes"] * 6)
        self.assertIsNone(r["kappa"])
        self.assertEqual(r["kappa_status"], "undefined_expected_agreement_is_one")
        self.assertEqual(r["observed_agreement"], 1.0)

    def test_alpha_undefined_when_everyone_says_the_same_thing(self):
        r = krippendorff_alpha_nominal({f"c{i}": {"a": "Yes", "b": "Yes"} for i in range(5)})
        self.assertIsNone(r["alpha"])
        self.assertEqual(r["alpha_status"], "undefined_expected_disagreement_is_zero")

    def test_alpha_handles_an_incomplete_matrix(self):
        r = krippendorff_alpha_nominal({"c1": {"a": "Yes", "b": "No"},
                                        "c2": {"a": "Yes", "c": "Yes"},
                                        "c3": {"b": "No"}})
        self.assertEqual(r["units_used"], 2)          # c3 has one coder only
        self.assertEqual(r["alpha_status"], "estimated")

    def test_perfect_disagreement_is_negative(self):
        r = krippendorff_alpha_nominal({f"c{i}": {"a": "Yes", "b": "No"} for i in range(4)})
        self.assertLess(r["alpha"], 0)

    def test_spearman_needs_three_pairs(self):
        self.assertIsNone(spearman([1, 2], [1, 2]))
        self.assertEqual(spearman([1, 2, 3], [1, 2, 3]), 1.0)
        self.assertEqual(spearman([1, 2, 3], [3, 2, 1]), -1.0)


class EndToEndTests(unittest.TestCase):
    def analyse(self, scenario, n=12, seed=20260914):
        return build(REPO, generate(REPO, scenario, n, seed))

    def test_every_scenario_runs(self):
        for s in SCENARIOS:
            with self.subTest(scenario=s):
                self.assertEqual(self.analyse(s)["plan_version"], PLAN["document_version"])

    def test_duplicates_are_the_only_exclusion(self):
        r = self.analyse("consensus")
        self.assertEqual({d["reason"] for d in r["excluded"]}, {"duplicate_email"})

    def test_g1_cannot_pass_on_a_condition_dependent_sweep(self):
        r = self.analyse("depends")
        self.assertFalse(r["gate_g1"]["passes"])
        self.assertEqual(r["gate_g1"]["externally_validated"], 0)

    def test_g1_passes_only_when_every_boundary_rule_adopts(self):
        r = self.analyse("consensus")
        self.assertTrue(r["gate_g1"]["passes"])
        self.assertEqual(r["gate_g1"]["externally_validated"], len(ITEMS["boundary_items"]))

    def test_tie_scenario_reports_divided(self):
        r = self.analyse("tie")
        self.assertEqual(r["rules"]["B1_governed_treasury"]["level"], "divided")

    def test_degenerate_blind_scores_report_no_coefficient(self):
        r = self.analyse("degenerate")["reliability"]
        self.assertIsNone(r["krippendorff_alpha"]["alpha"])
        self.assertIsNone(r["pairwise_cohen_kappa"]["mean_kappa"])
        self.assertEqual(r["pairwise_cohen_kappa"]["pairs_estimated"], 0)

    def test_low_overlap_pairs_are_excluded_not_imputed(self):
        r = self.analyse("sparse")["reliability"]["pairwise_cohen_kappa"]
        self.assertGreater(r["pairs_excluded_for_low_overlap"], 0)
        for p in r["excluded"]:
            self.assertLess(p["overlap"], PLAN["reliability"]["inter_rater_reliability"]
                            ["edge_cases"]["minimum_overlapping_determinate_cells_per_pair"])

    def test_contrast_is_bundle_level_over_all_three_outcomes(self):
        c = self.analyse("consensus")["contrast_statistic"]
        self.assertEqual(set(c["outcomes"]), set(PLAN["ranking_prediction"]["contrast_statistic"]["outcomes"]))
        for outcome, v in c["outcomes"].items():
            self.assertEqual(v["n_pairs"], 8, outcome)
            self.assertIsNone(v["p_value"], "the contrast is descriptive; no p-value is reported")

    def test_pending_cells_carry_no_reference_value(self):
        ref = load_reference(REPO, ITEMS["blind_cells"])
        for c in ITEMS["blind_cells"]:
            k = f'{c["asset_id"]}|{c["code"]}'
            if ref[k + "|state"] in ("pending", "absent"):
                self.assertIsNone(ref[k], f"{k} is {ref[k + '|state']} and must not act as a reference")

    def test_reference_agreement_is_never_called_reliability(self):
        r = self.analyse("consensus")["reference_agreement"]
        self.assertEqual(r["label"], "Reference agreement.")
        self.assertNotIn("accuracy", json.dumps(r["by_cell"]).lower())


class PlanIntegrityTests(unittest.TestCase):
    def test_v1_1_preserves_the_v1_0_reference(self):
        self.assertEqual(PLAN["supersedes"]["commit"], "dd081ac")

    def test_the_uncomputable_speed_screen_is_gone(self):
        self.assertNotIn("speed_screen", PLAN["inclusion_and_exclusion"])
        self.assertNotIn("completion", json.dumps(PLAN["inclusion_and_exclusion"]).lower())

    def test_every_boundary_item_names_its_condition_dependent_option(self):
        for s in ITEMS["boundary_items"]:
            self.assertIn(s["condition_dependent_option"], s["options"])

    def test_contrast_names_a_real_artifact_and_field(self):
        cs = PLAN["ranking_prediction"]["contrast_statistic"]
        art = REPO / cs["project_side"]["artifact"]
        self.assertTrue(art.exists())
        self.assertIn(cs["project_side"]["field"], art.read_text().splitlines()[0])


if __name__ == "__main__":
    unittest.main()
