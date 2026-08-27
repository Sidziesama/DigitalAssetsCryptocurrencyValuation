import unittest
from datetime import date

from src.pipeline.crypto_collateral import aggregate,longest_consecutive,normalize_protocol,validate_config


class CryptoCollateralTests(unittest.TestCase):
    def test_normalize_uses_exact_alias_and_positive_balance(self):
        payload={"tokensInUsd":[{"date":1735689600,"tokens":{"WETH":120.0,"STETH":999.0,"ETH":-1}}]}
        rows=normalize_protocol("aave",payload,{"WETH":"crypto_eth"},date(2025,1,1),date(2025,1,1))
        self.assertEqual(len(rows),1); self.assertEqual(rows[0]["supplied_balance_usd"],120)

    def test_longest_streak_breaks_on_missing_day(self):
        days=[date(2026,1,1),date(2026,1,2),date(2026,1,4)]
        self.assertEqual(longest_consecutive(days),2)

    def test_absolute_or_ratio_rule_is_applied(self):
        rows=[{"asset_id":"crypto_x","date":"2026-01-01","supplied_balance_usd":2_000_000}]
        daily,summary=aggregate(rows,[{"asset_id":"crypto_x"}],{("crypto_x","2026-01-01"):100_000_000},{"absolute_usd":100_000_000,"market_cap_ratio":.01,"minimum_consecutive_days":1})
        self.assertEqual(daily[0]["material_proxy"],1); self.assertEqual(summary[0]["balance_proxy_pass"],1)

    def test_rejects_non_lending_protocol(self):
        registry={"schema_version":1,"assets":[{"asset_id":"crypto_x","symbol":"X","name":"X","universe":"crypto","tier":"x","coingecko_id":"x"}]}
        spec={"schema_version":1,"provider":"defillama","protocols":[{"slug":"dex","category":"dex"}],"assets":[{"asset_id":"crypto_x","token_aliases":["X"]}],"primary_rule":{"absolute_usd":1,"market_cap_ratio":.01,"minimum_consecutive_days":90}}
        with self.assertRaisesRegex(ValueError,"lending"):
            validate_config(spec,registry)


if __name__=="__main__": unittest.main()
