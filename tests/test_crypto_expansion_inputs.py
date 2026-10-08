import unittest

from src.pipeline.crypto_expansion_inputs import normalize


class ExpansionInputTests(unittest.TestCase):
    def test_missing_measure_is_not_zero_and_zero_is_preserved(self):
        rows = normalize({'data': [{'asset': 'xmr', 'time': '2026-05-25T00:00:00Z', 'TxCnt': '0'}]},
                         'crypto_xmr', 'xmr', '2026-05-25', '2026-08-22')
        self.assertIsNone(rows[0]['active_addresses'])
        self.assertEqual(rows[0]['transaction_count'], 0)

    def test_duplicates_cannot_inflate_coverage(self):
        point = {'asset': 'bch', 'time': '2026-05-25T00:00:00Z'}
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            normalize({'data': [point, point]}, 'crypto_bch', 'bch', '2026-05-25', '2026-08-22')

    def test_invalid_numbers_and_wrong_asset_are_rejected(self):
        for point in [{'asset': 'bch', 'AdrActCnt': 'NaN'}, {'asset': 'bch', 'TxCnt': '-1'}, {'asset': 'btc'}]:
            with self.subTest(point=point), self.assertRaises(ValueError):
                normalize({'data': [dict(point, time='2026-05-25')]},
                          'crypto_bch', 'bch', '2026-05-25', '2026-08-22')

    def test_outside_window_is_excluded(self):
        self.assertEqual(normalize({'data': [{'asset': 'bch', 'time': '2026-05-24'}]},
                                   'crypto_bch', 'bch', '2026-05-25', '2026-08-22'), [])
