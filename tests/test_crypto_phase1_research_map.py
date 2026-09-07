import unittest
from pathlib import Path

from src.pipeline.crypto_phase1_research_map import CODES, build


def codebook():
    return [{"code":code,"bundle":"b","classification_rule":"r","value_indicators":f"{code.lower()}_ind"} for code in CODES]


def spec():
    observability={f"{code.lower()}_ind":{"state":"documentary_only","dataset":"config/x.json","note":"n"} for code in CODES}
    return {"schema_version":1,"as_of":"2026-09-07","observability_states":["observed_series","partial_series","documentary_only","not_collected"],
            "indicator_observability":observability,"experiment_use":{code:["P1_H1"] for code in CODES},
            "experiment_status":{"P1_H1":{"status":"s","artifact":"a","summary":"x"}}}


def registry():
    return {"experiments":[{"id":"P1_H1"}]}


def prevalence():
    return [{"code":code,"verified_assets":"6","positive_assets":"2"} for code in CODES]


def profiles():
    return [{"asset_id":"a",**{code.lower():"1" for code in CODES}},{"asset_id":"b",**{code.lower():"0" for code in CODES}}]


class CryptoPhase1ResearchMapTests(unittest.TestCase):
    def test_documentary_map_builds(self):
        code_rows,indicator_rows,summary=build(Path("/nonexistent"),spec(),codebook(),prevalence(),profiles(),registry())
        self.assertEqual(len(code_rows),10); self.assertEqual(len(indicator_rows),10)
        self.assertEqual(summary["documentary_codes"],CODES); self.assertEqual(code_rows[0]["positive_asset_ids"],"a")

    def test_series_claim_without_dataset_is_rejected(self):
        bad=spec(); bad["indicator_observability"]["va_gas_ind"]={"state":"observed_series","dataset":None,"measure":None}
        with self.assertRaisesRegex(ValueError,"claims a series"):
            build(Path("/nonexistent"),bad,codebook(),prevalence(),profiles(),registry())

    def test_unregistered_experiment_is_rejected(self):
        bad=spec(); bad["experiment_use"]["VA_GOV"]=["P1_H9"]
        with self.assertRaisesRegex(ValueError,"registered Phase 1 experiments"):
            build(Path("/nonexistent"),bad,codebook(),prevalence(),profiles(),registry())


if __name__=="__main__": unittest.main()
