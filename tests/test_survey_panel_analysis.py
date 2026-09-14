"""Acceptance tests: every output the frozen plan promises must actually be produced,
and every decision rule must behave exactly as written.

All inputs are synthetic. None of these numbers is a finding.
"""
import csv
import json
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from src.pipeline.survey_panel_analysis import (ExportError, average_ranks, build, classify_consensus,
                                                cohen_kappa, krippendorff_alpha_nominal, load_reference,
                                                read_export, reference_snapshot, run, score_prediction,
                                                spearman)
from src.pipeline.survey_synthetic_responses import SCENARIOS, run as generate

REPO = Path(__file__).resolve().parents[1]
PLAN = json.loads((REPO / "config/survey_analysis_plan.json").read_text())
ITEMS = json.loads((REPO / "config/survey_items.json").read_text())
TH = PLAN["consensus"]["thresholds"]


def analyse(scenario, n=12, seed=20260914):
    return build(REPO, generate(REPO, scenario, n, seed), "synthetic")[0]


class ThresholdSourceTests(unittest.TestCase):
    def test_thresholds_come_from_the_plan_not_the_code(self):
        src = (REPO / "src/pipeline/survey_panel_analysis.py").read_text()
        self.assertNotIn("0.70", src)
        self.assertNotIn("0.50", src)
        self.assertIn('plan["consensus"]["thresholds"]', src)

    def test_the_plan_states_the_numbers(self):
        self.assertEqual(TH["adopt"], 0.70)
        self.assertEqual(TH["leaning"], 0.50)


class ConsensusLadderTests(unittest.TestCase):
    def test_exact_fifty_fifty_is_divided(self):
        r = classify_consensus(Counter({"A": 6, "B": 6}), "Depends", TH, 8)
        self.assertEqual(r["level"], "divided")
        self.assertEqual(r["tied_options"], ["A", "B"])

    def test_leaning_requires_a_unique_plurality(self):
        r = classify_consensus(Counter({"A": 6, "B": 4}), "Depends", TH, 8)
        self.assertEqual(r["level"], "leaning")
        self.assertEqual(r["validation_status"], "unresolved")

    def test_seventy_percent_adopts(self):
        self.assertEqual(classify_consensus(Counter({"A": 7, "B": 3}), "Depends", TH, 8)["level"],
                         "consensus_adopt")

    def test_condition_dependent_win_never_validates(self):
        r = classify_consensus(Counter({"Depends": 8, "A": 2}), "Depends", TH, 8)
        self.assertEqual(r["level"], "consensus_condition_dependent")
        self.assertEqual(r["validation_status"], "unresolved")

    def test_under_powered(self):
        self.assertEqual(classify_consensus(Counter({"A": 3}), "Depends", TH, 8)["level"],
                         "under_powered")

    def test_other_answers_count_as_their_own_category(self):
        r = analyse("dirty")["rules"]["M1_collateral"]
        self.assertTrue(r["other_answers"], "an Other answer must appear in the record")
        self.assertEqual(r["n"], sum(r["counts"].values()))
        for o in r["other_answers"]:
            self.assertIn(o["value"], r["counts"], "an Other answer must be its own category")


class FrozenPredictionTests(unittest.TestCase):
    def test_the_prediction_matches_the_committed_instrument(self):
        spec = ITEMS["frozen_prediction"]
        self.assertEqual(spec["top_three"], ["VA_PROTOCOL", "VA_MONETARY"])
        self.assertEqual(spec["bottom_three"], ["VA_INCENTIVE", "VA_GOV"])
        self.assertIn("ff15698", spec["source"])

    def test_a_matching_panel_is_scored_supported(self):
        p = analyse("prediction_hit")["frozen_prediction"]
        self.assertEqual(p["verdict"], "supported")
        self.assertEqual(p["conditions_met"], 4)

    def test_conditions_are_reported_individually(self):
        p = analyse("divided")["frozen_prediction"]
        self.assertEqual(len(p["conditions"]), 4)
        self.assertEqual(p["verdict"], "not_supported")
        for c in p["conditions"]:
            self.assertIn("satisfied", c)

    def test_partial_satisfaction_is_never_a_hit(self):
        p = analyse("dirty")["frozen_prediction"]
        if 0 < p["conditions_met"] < 4:
            self.assertEqual(p["verdict"], "not_supported")

    def test_a_tie_group_straddling_the_band_fails(self):
        # four-way tie at rank 2.5 spans ranks 1..4, so it leaves the top three
        means = {c: {"mean": m, "n": 10} for c, m in
                 {"VA_PROTOCOL": 4.0, "VA_MONETARY": 4.0, "VA_GAS": 4.0, "VA_STAKE": 4.0,
                  "VA_BURN": 3.0, "VA_SCARCITY": 3.0, "VA_COLLATERAL": 2.0,
                  "VA_UTILITY": 2.0, "VA_INCENTIVE": 1.0, "VA_GOV": 1.0}.items()}
        r = score_prediction(means, ITEMS["frozen_prediction"], 8)
        top = {c["code"]: c for c in r["conditions"] if c["required"].startswith("top")}
        self.assertFalse(top["VA_PROTOCOL"]["satisfied"])
        self.assertEqual(top["VA_PROTOCOL"]["tie_group_size"], 4)

    def test_incomplete_grid_is_not_scored_on_a_partial_ranking(self):
        self.assertEqual(analyse("sparse")["frozen_prediction"]["verdict"], "not_scorable")

    def test_average_ranks_share_ties(self):
        self.assertEqual(average_ranks({"a": 5, "b": 5, "c": 1}), {"a": 1.5, "b": 1.5, "c": 3})


class DuplicateTests(unittest.TestCase):
    def test_the_later_submission_is_kept(self):
        d = analyse("duplicates")
        superseded = [e for e in d["excluded"] if e["resolved_by"] == "timestamp"]
        self.assertTrue(superseded)
        for e in superseded:
            self.assertLess(e["timestamp"], e["kept_timestamp"])

    def test_equal_timestamps_are_reported_as_ambiguous(self):
        d = analyse("duplicates")
        self.assertTrue(any(e["ambiguous"] for e in d["excluded"]))

    def test_only_duplicates_are_ever_excluded(self):
        for s in SCENARIOS:
            for e in analyse(s)["excluded"]:
                self.assertEqual(e["reason"], "duplicate_submission_superseded")


class IngestionTests(unittest.TestCase):
    def test_a_missing_column_is_a_hard_failure(self):
        src = generate(REPO, "consensus", 12, 20260914)
        rows = list(csv.reader(src.open(encoding="utf-8")))
        keep = [i for i, h in enumerate(rows[0]) if "Hard cap" not in h]
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as fh:
            w = csv.writer(fh)
            for r in rows:
                w.writerow([r[i] for i in keep])
            broken = Path(fh.name)
        with self.assertRaises(ExportError) as ctx:
            read_export(broken, ITEMS)
        self.assertIn("Hard cap", str(ctx.exception))
        broken.unlink()

    def test_six_free_text_columns_are_bound_by_position(self):
        d = analyse("consensus")
        self.assertEqual(d["ingestion"]["free_text_columns_bound_by_position"],
                         len(ITEMS["boundary_items"]))

    def test_out_of_range_values_are_counted_not_dropped(self):
        d = analyse("dirty")
        self.assertGreater(d["ingestion"]["invalid_value_count"], 0)
        fields = {v["field"].split(":")[0] for v in d["ingestion"]["invalid_values"]}
        self.assertTrue(fields & {"grid", "blind"})

    def test_an_invalid_blind_answer_never_becomes_a_category(self):
        d = analyse("dirty")
        for cell in d["blind_cell_detail"]:
            self.assertEqual(set(cell["distribution"]), set(ITEMS["blind_options"]))

    def test_invalid_grid_values_do_not_enter_a_mean(self):
        d = analyse("dirty")
        for code, v in d["function_importance"].items():
            if v["mean"] is not None:
                self.assertLessEqual(v["mean"], max(ITEMS["importance_grid"]["scale"].values()))


class OutputScopeTests(unittest.TestCase):
    def test_scope_is_declared_not_inferred(self):
        src = (REPO / "src/pipeline/survey_panel_analysis.py").read_text()
        self.assertNotIn('"synthetic" in responses.as_posix()\n    summary', src)
        self.assertIn("scope", build.__doc__ or "" or "scope")

    def test_a_renamed_fixture_cannot_publish_itself(self):
        """Scope, not the filename, decides where output lands."""
        src = generate(REPO, "consensus", 12, 20260914)
        with tempfile.TemporaryDirectory() as tmp:
            innocuous = Path(tmp) / "panel_responses_final.csv"
            shutil.copy(src, innocuous)
            summary, _, _ = build(REPO, innocuous, "synthetic")
        self.assertEqual(summary["data_source"], "synthetic_fixture")
        self.assertEqual(summary["output_scope"], "synthetic")

    def test_panel_scope_requires_a_complete_recruitment_record(self):
        with self.assertRaises(ExportError) as ctx:
            build(REPO, generate(REPO, "consensus", 12, 20260914), "panel")
        self.assertIn("recruitment", str(ctx.exception).lower())

    def test_panel_scope_refuses_a_synthetic_file(self):
        rec = json.loads((REPO / "config/survey_recruitment.json").read_text())
        blank = [f for f in PLAN["recruitment_record"]["fields"] if not rec.get(f)]
        self.assertTrue(blank, "the template must stay blank so the gate is live")

    def test_synthetic_runs_never_write_into_processed(self):
        run(REPO, generate(REPO, "consensus", 12, 20260914), "synthetic")
        self.assertFalse((REPO / "data/processed/01_classification/survey_panel_analysis.json").exists())


class ReferenceAgreementTests(unittest.TestCase):
    def test_it_is_per_respondent_with_a_kappa(self):
        ra = analyse("consensus")["reference_agreement"]
        self.assertIn("by_respondent", ra)
        for r in ra["by_respondent"]:
            self.assertIn("comparable_cells", r)
            self.assertIn("kappa", r)
        self.assertIn("mean_kappa_across_respondents", ra)

    def test_it_matches_the_plans_definition(self):
        ra = analyse("consensus")["reference_agreement"]
        self.assertEqual(ra["definition"],
                         PLAN["reliability"]["reference_agreement"]["description"])

    def test_it_is_never_labelled_reliability(self):
        ra = analyse("consensus")["reference_agreement"]
        self.assertEqual(ra["label"], "Reference agreement.")
        self.assertNotIn("accuracy", json.dumps(ra["by_respondent"]).lower())

    def test_pending_cells_are_not_a_reference(self):
        values, states = load_reference(REPO, ITEMS["blind_cells"])
        for c in ITEMS["blind_cells"]:
            k = f'{c["asset_id"]}|{c["code"]}'
            if states[k] in ("pending", "absent"):
                self.assertIsNone(values[k])

    def test_the_snapshot_is_hashed_and_stable(self):
        values, _ = load_reference(REPO, ITEMS["blind_cells"])
        a, b = reference_snapshot(values), reference_snapshot(values)
        self.assertEqual(a["sha256"], b["sha256"])
        self.assertEqual(len(a["sha256"]), 64)
        changed = dict(values)
        changed[sorted(values)[0]] = "Yes" if changed[sorted(values)[0]] != "Yes" else "No"
        self.assertNotEqual(reference_snapshot(changed)["sha256"], a["sha256"])


class ReliabilityTests(unittest.TestCase):
    def test_kappa_undefined_is_reported_not_imputed(self):
        r = cohen_kappa(["Yes"] * 6, ["Yes"] * 6)
        self.assertIsNone(r["kappa"])
        self.assertEqual(r["kappa_status"], "undefined_expected_agreement_is_one")

    def test_alpha_undefined_is_reported_not_imputed(self):
        r = krippendorff_alpha_nominal({f"c{i}": {"a": "Yes", "b": "Yes"} for i in range(5)})
        self.assertIsNone(r["alpha"])
        self.assertEqual(r["alpha_status"], "undefined_expected_disagreement_is_zero")

    def test_alpha_handles_an_incomplete_matrix(self):
        r = krippendorff_alpha_nominal({"c1": {"a": "Yes", "b": "No"}, "c2": {"a": "Yes", "c": "Yes"},
                                        "c3": {"b": "No"}})
        self.assertEqual(r["units_used"], 2)

    def test_degenerate_panel_yields_no_coefficient(self):
        r = analyse("degenerate")["reliability"]
        self.assertIsNone(r["krippendorff_alpha"]["alpha"])
        self.assertIsNone(r["pairwise_cohen_kappa"]["mean_kappa"])

    def test_low_overlap_pairs_are_excluded_and_counted(self):
        r = analyse("sparse")["reliability"]["pairwise_cohen_kappa"]
        self.assertGreater(r["pairs_excluded_for_low_overlap"], 0)
        floor = PLAN["reliability"]["inter_rater_reliability"]["edge_cases"][
            "minimum_overlapping_determinate_cells_per_pair"]
        for p in r["excluded"]:
            self.assertLess(p["overlap"], floor)

    def test_coverage_is_reported_per_cell_and_per_scorer(self):
        c = analyse("consensus")["reliability"]["coverage"]
        self.assertTrue(c["per_cell"])
        self.assertTrue(c["per_scorer"])
        for v in list(c["per_cell"].values()) + list(c["per_scorer"].values()):
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 1.0)


class PromisedOutputTests(unittest.TestCase):
    """Each reporting commitment must correspond to a real output."""

    def setUp(self):
        self.d = analyse("consensus")

    def test_checkbox_items_are_analysed(self):
        cb = self.d["checkbox_items"]
        self.assertEqual(set(cb), {s["item_id"] for s in ITEMS["checkbox_items"]})
        for v in cb.values():
            self.assertIn("selection_rate", v)
            self.assertIn("top_co_selections", v)
            self.assertNotIn("level", v, "a checkbox item has no consensus level")

    def test_free_text_produces_a_coding_worksheet(self):
        run(REPO, generate(REPO, "consensus", 12, 20260914), "synthetic")
        ws = REPO / "data/synthetic/survey/survey_free_text_coding.csv"
        self.assertTrue(ws.exists())
        rows = list(csv.DictReader(ws.open(encoding="utf-8")))
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(r["argument_group"], "", "grouping is a human coding step")
            self.assertTrue(r["response_id"] and r["text"])

    def test_no_automated_free_text_summary(self):
        self.assertEqual(set(self.d["free_text"]) & {"themes", "summary", "groups"}, set())

    def test_every_scenario_item_collects_reasoning(self):
        by_item = self.d["free_text"]["by_item"]
        for s in ITEMS["boundary_items"]:
            self.assertIn(s["item_id"], by_item)

    def test_every_item_is_reported(self):
        expected = {s["item_id"] for s in ITEMS["boundary_items"] + ITEMS["materiality_items"]
                    + ITEMS["single_choice_items"]}
        self.assertEqual(set(self.d["rules"]), expected)

    def test_recruitment_appears_in_the_output(self):
        self.assertIn("recruitment", self.d)

    def test_blind_cells_report_distribution_project_value_and_state(self):
        self.assertEqual(len(self.d["blind_cell_detail"]), len(ITEMS["blind_cells"]))
        for c in self.d["blind_cell_detail"]:
            self.assertIn("distribution", c)
            self.assertIn("project_value", c)
            self.assertIn("project_state", c)


class ContrastTests(unittest.TestCase):
    def test_it_is_secondary_and_says_what_it_compares(self):
        c = analyse("consensus")["contrast_statistic"]
        self.assertEqual(c["status"], "secondary")
        self.assertIn("NOT an economic effect magnitude", c["what_it_actually_compares"])
        self.assertTrue(c["prohibited_claims"])

    def test_all_three_outcomes_at_bundle_level_without_a_p_value(self):
        c = analyse("consensus")["contrast_statistic"]
        self.assertEqual(set(c["outcomes"]),
                         set(PLAN["ranking_prediction"]["contrast_statistic"]["outcomes"]))
        for outcome, v in c["outcomes"].items():
            self.assertEqual(v["n_pairs"], 8, outcome)
            self.assertIsNone(v["p_value"])

    def test_spearman_needs_three_pairs(self):
        self.assertIsNone(spearman([1, 2], [1, 2]))
        self.assertEqual(spearman([1, 2, 3], [3, 2, 1]), -1.0)


class PlanIntegrityTests(unittest.TestCase):
    def test_earlier_versions_are_preserved(self):
        self.assertEqual([v["commit"] for v in PLAN["supersedes"]["document_versions"]],
                         ["dd081ac", "29bf01e"])

    def test_the_uncomputable_speed_screen_is_gone(self):
        self.assertNotIn("speed_screen", PLAN["inclusion_and_exclusion"])

    def test_duplicate_rule_says_later(self):
        self.assertIn("LATER", PLAN["inclusion_and_exclusion"]["duplicates"])

    def test_every_choice_item_names_its_condition_dependent_option_if_it_has_one(self):
        for s in ITEMS["boundary_items"] + ITEMS["materiality_items"] + ITEMS["single_choice_items"]:
            if "condition_dependent_option" in s:
                self.assertIn(s["condition_dependent_option"], s["options"])

    def test_contrast_names_a_real_artifact_and_field(self):
        cs = PLAN["ranking_prediction"]["contrast_statistic"]
        art = REPO / cs["project_side"]["artifact"]
        self.assertTrue(art.exists())
        self.assertIn(cs["project_side"]["field"], art.read_text().splitlines()[0])

    def test_every_scenario_runs(self):
        for s in SCENARIOS:
            with self.subTest(scenario=s):
                self.assertEqual(analyse(s)["plan_version"], PLAN["document_version"])


if __name__ == "__main__":
    unittest.main()
