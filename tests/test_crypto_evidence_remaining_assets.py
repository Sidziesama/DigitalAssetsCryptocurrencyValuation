import json
import unittest
from pathlib import Path

from src.pipeline.crypto_design_evidence import validate_evidence
from src.pipeline.classification_status import CODES, build
from src.pipeline.research_universe_workbook import collect

REPO = Path(__file__).resolve().parents[1]


class RemainingAssetTests(unittest.TestCase):
    def test_full_five_asset_scope_is_valid_and_visible(self):
        def load(name):
            return json.loads((REPO / 'config' / name).read_text())
        evidence = load('crypto_evidence_remaining_assets.json')
        rows = validate_evidence(evidence, load('crypto_economic_design.json'), load('assets.json'))
        self.assertEqual(set(evidence['assets']), {'crypto_hype', 'crypto_xmr', 'crypto_ton', 'crypto_tao', 'crypto_pol'})
        self.assertEqual(set(evidence['codes']), set(CODES))
        self.assertEqual(len(rows), 50)
        data = collect(REPO)
        excluded = {'crypto_xmr'}
        for row in rows:
            if row['asset_id'] in excluded:
                self.assertNotIn((row['asset_id'], row['code']), data['cells'])
                continue
            cell = data['cells'][row['asset_id'], row['code']]
            self.assertIn(cell[0], (0, 1))
            self.assertIn(cell[1], ('sourced', 'reviewed'))
            if row['status'] == 'pending':
                self.assertTrue(row['remaining_evidence'])
        counts = {status: sum(v[1] == status for v in data['cells'].values()) for status in build(REPO)['counts']}
        self.assertEqual(counts, build(REPO)['counts'])

    def test_later_evidence_has_no_overlap_with_prior_tranches(self):
        current = json.loads((REPO / 'config/crypto_evidence_remaining_assets.json').read_text())
        keys = {(r['asset_id'], r['code']) for r in current['decisions']}
        for name in ['crypto_evidence_tranche_a.json', 'crypto_evidence_tranche_c.json']:
            old = json.loads((REPO / 'config' / name).read_text())
            self.assertFalse(keys & {(r['asset_id'], r['code']) for r in old['decisions']})
