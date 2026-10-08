import unittest

from src.pipeline.crypto_expansion_collateral import extract


class ExpansionCollateralTests(unittest.TestCase):
    def test_exact_aliases_exclude_derivatives_and_lp_tokens(self):
        payload = {'tokensInUsd': [{'date': 1779667200, 'tokens': {'LINK': 10, 'LINK/WETH UNI-V2': 99, 'SLINK': 99}}]}
        rows = extract(payload, 'test', {'LINK': 'crypto_link'}, '2026-05-25', '2026-08-22')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['token_balance_proxy_usd'], 10)

    def test_zero_is_observed_and_missing_is_absent(self):
        p = {'tokensInUsd': [{'date': 1779667200, 'tokens': {'LINK': 0, 'OP': None}}]}
        rows = extract(p, 'test', {'LINK': 'crypto_link', 'OP': 'crypto_op'}, '2026-05-25', '2026-08-22')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['token_balance_proxy_usd'], 0)

    def test_duplicate_days_are_not_double_counted(self):
        point = {'date': 1779667200, 'tokens': {'LINK': 1}}
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            extract({'tokensInUsd': [point, point]}, 'test', {'LINK': 'crypto_link'}, '2026-05-25', '2026-08-22')

    def test_negative_and_nonfinite_values_are_rejected(self):
        for value in [-1, 'NaN', 'Infinity']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                extract({'tokensInUsd': [{'date': 1779667200, 'tokens': {'LINK': value}}]},
                        'test', {'LINK': 'crypto_link'}, '2026-05-25', '2026-08-22')
