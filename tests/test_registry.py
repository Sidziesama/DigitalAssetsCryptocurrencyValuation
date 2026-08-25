import json
import tempfile
import unittest
from pathlib import Path

from src.pipeline.registry import build_rows, load_coingecko_snapshots, render_findings, validate_asset_config, write_csv


class AssetConfigTests(unittest.TestCase):
    def test_rejects_duplicate_asset_id(self):
        asset = {"asset_id":"x","symbol":"X","name":"X","universe":"crypto","tier":"market_core","coingecko_id":"x"}
        with self.assertRaisesRegex(ValueError, "duplicate asset_id"):
            validate_asset_config({"schema_version":1,"assets":[asset, {**asset,"coingecko_id":"y"}]})

    def test_rejects_duplicate_provider_id(self):
        a = {"asset_id":"a","symbol":"A","name":"A","universe":"crypto","tier":"market_core","coingecko_id":"same"}
        b = {"asset_id":"b","symbol":"B","name":"B","universe":"crypto","tier":"market_core","coingecko_id":"same"}
        with self.assertRaisesRegex(ValueError, "duplicate coingecko_id"):
            validate_asset_config({"schema_version":1,"assets":[a,b]})


class CoverageTests(unittest.TestCase):
    def test_stablecoin_requires_both_sources(self):
        assets=[{"asset_id":"stable_u","symbol":"U","name":"U","universe":"stablecoin","tier":"market_core","coingecko_id":"u","defillama_symbol":"U"}]
        cg=[{"id":"u","market_cap":100,"total_volume":10,"market_cap_rank":1}]
        llama={"peggedAssets":[{"symbol":"U","circulating":{"peggedUSD":100},"circulatingPrevMonth":{"peggedUSD":80}}]}
        row=build_rows(assets,cg,llama)[0]
        self.assertEqual(row["coverage_status"],"pass")
        self.assertAlmostEqual(row["stablecoin_month_growth"],0.25)

    def test_missing_market_row_is_review(self):
        assets=[{"asset_id":"crypto_x","symbol":"X","name":"X","universe":"crypto","tier":"market_core","coingecko_id":"x"}]
        row=build_rows(assets,[],{"peggedAssets":[]})[0]
        self.assertEqual(row["coverage_status"],"review")
        self.assertEqual(row["required_snapshot_coverage"],0)

    def test_csv_is_machine_readable(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"rows.csv"
            write_csv(path,[{"a":1,"b":"x"}],["a","b"])
            self.assertEqual(path.read_text(encoding="utf-8"),"a,b\n1,x\n")

    def test_findings_identify_review_assets(self):
        summary={"snapshot_date":"2026-08-22","asset_count":2,"crypto_count":1,"stablecoin_count":1,"pass_count":1,"review_count":1,"indicative_combined_coverage":0.9,"review_assets":["stable_x"]}
        findings=render_findings(summary)
        self.assertIn("90.00%",findings)
        self.assertIn("`stable_x`",findings)

    def test_findings_report_clean_resolution(self):
        summary={"snapshot_date":"2026-08-22","asset_count":1,"crypto_count":1,"stablecoin_count":0,"pass_count":1,"review_count":0,"indicative_combined_coverage":0.9,"review_assets":[]}
        findings=render_findings(summary)
        self.assertIn("All frozen-universe assets",findings)
        self.assertNotIn("The six review observations",findings)

    def test_commodity_asset_can_skip_defillama_requirement(self):
        assets=[{"asset_id":"stable_gold","symbol":"GOLD","name":"Gold","universe":"stablecoin","tier":"structural_coverage","coingecko_id":"gold","defillama_required":False}]
        cg=[{"id":"gold","market_cap":100,"total_volume":10}]
        row=build_rows(assets,cg,{"peggedAssets":[]})[0]
        self.assertEqual(row["coverage_status"],"pass")

    def test_expanded_snapshot_overrides_base(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/"expanded").mkdir()
            (root/"coingecko_markets.json").write_text(json.dumps([{"id":"x","market_cap":1}]))
            (root/"expanded"/"coingecko_x.json").write_text(json.dumps([{"id":"x","market_cap":2}]))
            rows, paths=load_coingecko_snapshots(root)
            self.assertEqual(rows[0]["market_cap"],2)
            self.assertEqual(len(paths),2)


if __name__ == "__main__":
    unittest.main()
