import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.pipeline.crypto_h4_eth_stake import date_slot, load_local_env, normalize, provider_label, validate


def source():
    return {"asset_id":"crypto_eth","component_id":"active_validator_effective_balance",
            "api_url_env":"ETH_BEACON_ARCHIVE_API_URL","public_probe_url":"https://public.test",
            "genesis_timestamp":1606824023,"seconds_per_slot":12,"snapshot_hour_utc":12,
            "validator_statuses":["active_exiting","active_ongoing","active_slashed"]}


class CryptoH4EthStakeTests(unittest.TestCase):
    def test_fixed_configuration_and_slot(self):
        spec={"schema_version":1,"universe_policy":"fixed_existing_six_assets_no_expansion","eth_consensus_stake":source()}
        checked=validate(spec)
        self.assertEqual(date_slot(date(2020,12,2),checked),7198)

    def test_sums_only_active_effective_balance(self):
        payload={"data":[
            {"status":"active_ongoing","validator":{"effective_balance":"32000000000"}},
            {"status":"active_exiting","validator":{"effective_balance":"64000000000"}},
            {"status":"pending_queued","validator":{"effective_balance":"32000000000"}},
        ]}
        row=normalize(payload,date(2026,8,1),123,"archive.test")
        self.assertEqual(row["active_validators"],2)
        self.assertEqual(row["total_staked_native_units"],96.0)

    def test_provider_label_redacts_path_and_rejects_insecure_url(self):
        self.assertEqual(provider_label("https://archive.test/v2/secret-token"),"archive.test")
        with self.assertRaises(ValueError): provider_label("http://archive.test")

    def test_invalid_effective_balance_rejected(self):
        with self.assertRaises(ValueError):
            normalize({"data":[{"status":"active_slashed","validator":{"effective_balance":1}}]},date(2026,8,1),1,"x")

    def test_loads_only_named_local_endpoint_without_overwriting_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            repo=Path(folder); (repo/".env").write_text("OTHER_SECRET=nope\nETH_BEACON_ARCHIVE_API_URL=https://archive.test/token\n")
            os.environ.pop("ETH_BEACON_ARCHIVE_API_URL",None); load_local_env(repo)
            self.assertEqual(os.environ["ETH_BEACON_ARCHIVE_API_URL"],"https://archive.test/token")
            os.environ["ETH_BEACON_ARCHIVE_API_URL"]="https://preferred.test"; load_local_env(repo)
            self.assertEqual(os.environ["ETH_BEACON_ARCHIVE_API_URL"],"https://preferred.test")
            os.environ.pop("ETH_BEACON_ARCHIVE_API_URL",None)


if __name__ == "__main__": unittest.main()
