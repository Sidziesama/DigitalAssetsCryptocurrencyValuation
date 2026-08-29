import json
import tempfile
import unittest
from pathlib import Path

from src.pipeline.checkpoint_readiness import build_readiness


class CheckpointReadinessTests(unittest.TestCase):
    def test_repository_checkpoint_reconciles(self):
        repo = Path(__file__).resolve().parents[1]
        result = build_readiness(repo)
        self.assertEqual(result["status"], "commit_ready_methodology_checkpoint_not_model_ready")
        self.assertEqual(result["crypto_evidence"]["pending_decisions"], 5)
        self.assertEqual(len(result["crypto_evidence"]["unresolved"]), 5)
        self.assertTrue(all(result["checks"].values()))

    def test_checkpoint_rejects_verified_mismatch(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp)
            for source in [
                "data/processed/evidence/crypto_design_evidence_tranche_1_summary.json",
                "data/processed/evidence/crypto_design_evidence_tranche_1.csv",
                "data/processed/evidence/crypto_monetary_assessment.json",
                "data/processed/evidence/crypto_collateral_screen_summary.json",
                "data/processed/evidence/aave_collateral_state_summary.json",
                "data/processed/evidence/crypto_mechanism_state_summary.json",
                "data/processed/empirical/crypto_fundamentals_summary.json",
                "data/processed/evidence/stablecoin_h5_h6_temporal_readiness.json",
                "data/processed/evidence/crypto_h2_h8_pilot_readiness.json",
            ]:
                target = copy / source
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((repo / source).read_bytes())
            path = copy / "data/processed/evidence/crypto_design_evidence_tranche_1_summary.json"
            summary = json.loads(path.read_text())
            summary["verified_mismatches"] = 1
            path.write_text(json.dumps(summary))
            with self.assertRaisesRegex(ValueError, "crypto_no_verified_mismatches"):
                build_readiness(copy)


if __name__ == "__main__":
    unittest.main()
