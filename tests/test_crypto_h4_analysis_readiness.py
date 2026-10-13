import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.pipeline.crypto_h4_analysis_readiness import build, chart, validate


class Tests(unittest.TestCase):
    def test_design_rejects_third_incomparable_positive_asset(self):
        spec = {
            "schema_version": 1, "hypothesis": "H4",
            "primary_sample": {"consensus_staking_assets": ["crypto_eth", "crypto_bnb", "crypto_aave"], "structural_nonstaking_controls": ["crypto_btc", "crypto_uni", "crypto_arb"]},
            "separate_case_study": ["crypto_aave"], "predictor": "lagged_staked_share_of_circulating_supply"
        }
        with self.assertRaises(ValueError):
            validate(spec)

    def test_missing_eth_blocks_estimation(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "config").mkdir(); (repo / "data/processed/00_foundation").mkdir(parents=True); (repo / "data/processed/01_classification").mkdir(parents=True)
            spec = json.loads(Path("config/crypto_h4_analysis.json").read_text())
            spec.update({"study_start": "2026-01-01", "study_end": "2026-01-02", "minimum_common_days": 2})
            (repo / "config/crypto_h4_analysis.json").write_text(json.dumps(spec))
            def write(path, fields, rows):
                with path.open("w", newline="") as f:
                    w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
            assets=["crypto_eth","crypto_bnb","crypto_btc","crypto_uni","crypto_arb","crypto_aave"]
            write(repo/"data/processed/00_foundation/market_daily_coinpaprika.csv",["asset_id","date"],[{"asset_id":a,"date":d} for a in assets for d in ["2026-01-01","2026-01-02"]])
            write(repo/"data/processed/00_foundation/crypto_h4_bnb_stake_daily.csv",["asset_id","date"],[{"asset_id":"crypto_bnb","date":d} for d in ["2026-01-01","2026-01-02"]])
            write(repo/"data/processed/00_foundation/crypto_h4_aave_legacy_stake_daily.csv",["asset_id","date"],[{"asset_id":"crypto_aave","date":d} for d in ["2026-01-01","2026-01-02"]])
            result=build(repo)
            self.assertFalse(result["estimation_allowed"])
            self.assertEqual(result["consensus_staking_assets_ready"],1)
            self.assertTrue(result["market_ready"])
            self.assertIn('role="img"', chart(result))


if __name__ == "__main__":
    unittest.main()
