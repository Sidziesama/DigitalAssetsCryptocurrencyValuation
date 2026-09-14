import json
import tempfile
import unittest
from pathlib import Path

from src.pipeline.checkpoint_readiness import build_readiness


class CheckpointReadinessTests(unittest.TestCase):
    def test_repository_checkpoint_reconciles(self):
        repo = Path(__file__).resolve().parents[1]
        result = build_readiness(repo)
        self.assertEqual(result["status"], "commit_ready_frozen_exploratory_h2_checkpoint")
        self.assertEqual(result["crypto_evidence"]["pending_decisions"], 0)
        self.assertEqual(len(result["crypto_evidence"]["unresolved"]), 0)
        self.assertTrue(all(result["checks"].values()))

    def test_checkpoint_rejects_verified_mismatch(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp)
            for source in [
                "data/processed/01_classification/crypto_design_evidence_tranche_1_summary.json",
                "data/processed/01_classification/crypto_design_evidence_tranche_1.csv",
                "data/processed/01_classification/crypto_monetary_assessment.json",
                "data/processed/01_classification/crypto_collateral_screen_summary.json",
                "data/processed/01_classification/aave_collateral_state_summary.json",
                "data/processed/01_classification/crypto_mechanism_state_summary.json",
                "data/processed/00_foundation/crypto_fundamentals_summary.json",
                "data/processed/04_stablecoin_deferred/stablecoin_h5_h6_temporal_readiness.json",
                "data/processed/01_classification/crypto_h2_h8_pilot_readiness.json",
                "data/processed/02_valuation/crypto_h2_exploratory_summary.json",
                "data/processed/01_classification/crypto_h8_evidence_plan_summary.json",
                "data/processed/00_foundation/crypto_fee_fundamentals_summary.json",
                "data/processed/02_valuation/crypto_h2_estimator_diagnostics.json",
                "data/processed/02_valuation/crypto_h2_exploratory_estimates.json",
                "data/processed/01_classification/crypto_evidence_blockers_summary.json",
                "data/processed/02_valuation/crypto_h2_small_cluster_inference.json",
                "data/processed/02_valuation/crypto_h2_nonoverlap_sensitivity.json",
                "data/processed/01_classification/crypto_h2_expansion_readiness.json",
                "data/processed/01_classification/crypto_h2_expansion_evidence_summary.json",
                "data/processed/01_classification/independent_review_summary.json",
                "data/processed/01_classification/crypto_research_scope.json",
                "data/processed/02_valuation/crypto_h8_breadth_pilot.json",
                "data/processed/02_valuation/crypto_h8_six_asset_extension.json",
                "data/processed/02_valuation/crypto_h1_activity_pilot.json",
                "data/processed/02_valuation/crypto_h3_supply_pilot.json",
                "data/processed/01_classification/crypto_h4_source_readiness.json",
                "data/processed/01_classification/crypto_h4_aave_legacy_stake_summary.json",
                "data/processed/01_classification/crypto_h4_bnb_stake_summary.json",
                "data/processed/01_classification/crypto_h4_eth_stake_summary.json",
                "data/processed/01_classification/crypto_phase1_taxonomy_summary.json",
            ]:
                target = copy / source
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((repo / source).read_bytes())
            path = copy / "data/processed/01_classification/crypto_design_evidence_tranche_1_summary.json"
            summary = json.loads(path.read_text())
            summary["verified_mismatches"] = 1
            path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(ValueError, "crypto_no_verified_mismatches"):
                build_readiness(copy)


if __name__ == "__main__":
    unittest.main()
