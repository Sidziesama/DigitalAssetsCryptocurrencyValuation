import unittest
from datetime import date
import tempfile
from pathlib import Path

from src.pipeline.crypto_collateral import aggregate,longest_consecutive,market_caps,normalize_protocol,validate_config


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

    def test_complete_below_threshold_screen_is_explicit_negative(self):
        rows=[{"asset_id":"crypto_x","date":f"2026-01-0{day}","supplied_balance_usd":10} for day in range(1,4)]
        caps={("crypto_x",f"2026-01-0{day}"):10_000 for day in range(1,4)}
        _,summary=aggregate(rows,[{"asset_id":"crypto_x"}],caps, {"absolute_usd":100,"market_cap_ratio":.01,"minimum_consecutive_days":3},True)
        self.assertEqual(summary[0]["classification_status"],"verified_below_threshold_in_selected_protocol_sample")

    def test_missing_market_cap_prevents_negative_classification(self):
        rows=[{"asset_id":"crypto_x","date":f"2026-01-0{day}","supplied_balance_usd":10} for day in range(1,4)]
        _,summary=aggregate(rows,[{"asset_id":"crypto_x"}],{}, {"absolute_usd":100,"market_cap_ratio":.01,"minimum_consecutive_days":3},True)
        self.assertEqual(summary[0]["classification_status"],"proxy_threshold_not_met_or_insufficient_history")

    def test_market_cap_fallback_does_not_overwrite_primary(self):
        with tempfile.TemporaryDirectory() as tmp:
            first=Path(tmp)/"first.csv"; second=Path(tmp)/"second.csv"
            first.write_text("asset_id,date,market_cap_usd\ncrypto_x,2026-01-01,100\n")
            second.write_text("asset_id,date,market_cap_usd\ncrypto_x,2026-01-01,200\ncrypto_x,2026-01-02,300\n")
            caps=market_caps([first,second])
            self.assertEqual(caps[("crypto_x","2026-01-01")],100)
            self.assertEqual(caps[("crypto_x","2026-01-02")],300)

    def test_rejects_non_lending_protocol(self):
        registry={"schema_version":1,"assets":[{"asset_id":"crypto_x","symbol":"X","name":"X","universe":"crypto","tier":"x","coingecko_id":"x"}]}
        spec={"schema_version":1,"provider":"defillama","protocols":[{"slug":"dex","category":"dex"}],"assets":[{"asset_id":"crypto_x","token_aliases":["X"]}],"primary_rule":{"absolute_usd":1,"market_cap_ratio":.01,"minimum_consecutive_days":90}}
        with self.assertRaisesRegex(ValueError,"lending"):
            validate_config(spec,registry)


if __name__=="__main__": unittest.main()
