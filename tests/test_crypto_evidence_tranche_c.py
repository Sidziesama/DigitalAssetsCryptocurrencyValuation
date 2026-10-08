import copy
import csv
import json
import unittest
from pathlib import Path

from src.pipeline.crypto_design_evidence import validate_evidence
from src.pipeline.research_universe_workbook import collect

REPO = Path(__file__).resolve().parents[1]


class TrancheCIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.evidence = json.loads((REPO / 'config/crypto_evidence_tranche_c.json').read_text())
        self.design = json.loads((REPO / 'config/crypto_economic_design.json').read_text())
        self.registry = json.loads((REPO / 'config/assets.json').read_text())

    def test_complete_scope_and_workbook_overlay(self):
        rows = validate_evidence(self.evidence, self.design, self.registry)
        self.assertEqual(len(rows), 42)
        self.assertEqual(set(self.evidence['codes']), {'VA_GOV', 'VA_UTILITY', 'VA_INCENTIVE'})
        cells = collect(REPO)['cells']
        with (REPO / 'data/processed/01_classification/crypto_economic_design_targeted_review.csv').open(newline='') as handle:
            final = {(r['asset_id'], r['code']): int(r['decision_0_or_1'])
                     for r in csv.DictReader(handle) if r['decision_0_or_1'] in {'0', '1'}}
        excluded = {'crypto_doge'}
        for row in rows:
            if row['asset_id'] in excluded:
                self.assertNotIn((row['asset_id'], row['code']), cells)
                continue
            actual = cells[row['asset_id'], row['code']]
            self.assertEqual(actual[0], final[row['asset_id'], row['code']])
            self.assertIn(actual[1], ('sourced', 'reviewed'))
            if row['status'] == 'pending':
                self.assertTrue(row['remaining_evidence'])

    def test_pending_cannot_silently_become_zero(self):
        bad = copy.deepcopy(self.evidence)
        next(r for r in bad['decisions'] if r['status'] == 'pending')['recommended_value'] = 0
        with self.assertRaisesRegex(ValueError, 'pending decisions'):
            validate_evidence(bad, self.design, self.registry)

    def test_missing_cell_is_rejected(self):
        bad = copy.deepcopy(self.evidence)
        bad['decisions'].pop()
        with self.assertRaisesRegex(ValueError, 'exactly one decision'):
            validate_evidence(bad, self.design, self.registry)
