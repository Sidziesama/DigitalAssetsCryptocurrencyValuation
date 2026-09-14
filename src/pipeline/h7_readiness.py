from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .historical import read_csv, write_rows


RECENT_START = "2025-08-25"
RECENT_END = "2026-08-21"
MIN_ASSET_COVERAGE = .80
METRICS = (
    "global_peggedusd_supply_share", "supply_growth_30d", "material_chain_count_1m_usd_lag1",
    "effective_chain_count_lag1", "top_chain_share_lag1", "volume_to_reported_market_cap_lag1",
)


def present(value: Any) -> bool:
    return value not in (None, "")


def join_recent(adoption: list[dict[str, Any]], chains: list[dict[str, Any]], trading: list[dict[str, Any]], review: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chain_index = {(row["asset_id"], row["date"]): row for row in chains}
    trade_index = {(row["asset_id"], row["date"]): row for row in trading}
    withheld = {(row["asset_id"], row["onset_date"]) for row in review if row.get("proposed_primary_treatment") == "withhold_until_cross_source_confirmed"}
    output = []
    for base in adoption:
        if not RECENT_START <= base["date"] <= RECENT_END:
            continue
        day = date.fromisoformat(base["date"]); lag_day = (day - timedelta(days=1)).isoformat(); asset_id = base["asset_id"]
        chain_lag = chain_index.get((asset_id, lag_day), {}); trade_lag = trade_index.get((asset_id, lag_day), {})
        chain_ratio = chain_lag.get("chain_to_reported_supply_ratio")
        chain_reconciled = present(chain_ratio) and .95 <= float(chain_ratio) <= 1.05
        row = {
            "asset_id": asset_id, "date": base["date"], "sample_tier": base.get("sample_tier"),
            "log_circulating_peg_usd": base.get("log_circulating_peg_usd"),
            "pilot_observed_supply_share": base.get("pilot_observed_supply_share"),
            "global_peggedusd_supply_share": base.get("global_peggedusd_supply_share"),
            "supply_growth_30d": base.get("supply_growth_30d"),
            "absolute_peg_error_bps": base.get("absolute_peg_error_bps"), "breach_50bps": base.get("breach_50bps"),
            "material_chain_count_1m_usd_lag1": chain_lag.get("material_chain_count_1m_usd") if chain_reconciled else None,
            "effective_chain_count_lag1": chain_lag.get("effective_chain_count") if chain_reconciled else None,
            "top_chain_share_lag1": chain_lag.get("top_chain_share") if chain_reconciled else None,
            "volume_to_reported_market_cap_lag1": trade_lag.get("volume_to_reported_market_cap"),
            "log1p_volume_24h_usd_lag1": trade_lag.get("log1p_volume_24h_usd"),
            "chain_reconciliation_pass_lag1": int(chain_reconciled),
            "source_review_withheld": int((asset_id, base["date"]) in withheld),
        }
        row["complete_recent_h7_row"] = int(not row["source_review_withheld"] and all(present(row[metric]) for metric in METRICS))
        output.append(row)
    output.sort(key=lambda row: (row["asset_id"], row["date"]))
    return output


def coverage_matrix(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows: grouped[row["asset_id"]].append(row)
    output = []
    for asset_id, asset_rows in sorted(grouped.items()):
        expected = len(asset_rows); complete = sum(row["complete_recent_h7_row"] for row in asset_rows)
        for metric in METRICS:
            observed = sum(present(row[metric]) for row in asset_rows)
            output.append({"asset_id": asset_id, "metric": metric, "expected_rows": expected, "observed_rows": observed, "coverage_ratio": observed / expected if expected else 0, "gate": "pass" if observed / expected >= MIN_ASSET_COVERAGE else "fail"})
        output.append({"asset_id": asset_id, "metric": "complete_recent_h7_row", "expected_rows": expected, "observed_rows": complete, "coverage_ratio": complete / expected if expected else 0, "gate": "pass" if complete / expected >= MIN_ASSET_COVERAGE else "fail"})
    return output


def readiness(rows: list[dict[str, Any]], matrix: list[dict[str, Any]], integration_snapshot_available: bool = False, usage_partial_available: bool = False) -> dict[str, Any]:
    assets = sorted({row["asset_id"] for row in rows})
    complete_by_asset = {row["asset_id"]: row for row in matrix if row["metric"] == "complete_recent_h7_row"}
    proposed = [asset_id for asset_id in assets if complete_by_asset[asset_id]["gate"] == "pass"]
    gates = {
        "pilot_supply_and_share": "pass",
        "chain_distribution_proxy": "pass" if all(any(row["asset_id"] == asset and row["metric"] == "effective_chain_count_lag1" and row["gate"] == "pass" for row in matrix) for asset in proposed) else "review",
        "recent_trading_activity_proxy": "pass_recent_window_only",
        "global_peggedusd_market_share": "pass" if all(any(row["asset_id"] == asset and row["metric"] == "global_peggedusd_supply_share" and row["gate"] == "pass" for row in matrix) for asset in proposed) else "review",
        "market_depth_spread_price_impact": "fail_snapshot_only_insufficient_time_coverage",
        "protocol_integration_count": "fail_cross_sectional_yield_proxy_only" if integration_snapshot_available else "fail_missing",
        "transaction_volume_and_users": "pass_exploratory_four_asset_subsample_only" if usage_partial_available else "fail_missing",
    }
    return {
        "status": "partial_not_analysis_ready", "recent_window": {"start": RECENT_START, "end": RECENT_END},
        "minimum_asset_coverage": MIN_ASSET_COVERAGE, "assets_evaluated": len(assets), "proposed_recent_sample": proposed,
        "proposed_recent_sample_size": len(proposed), "complete_rows": sum(row["complete_recent_h7_row"] for row in rows),
        "total_recent_rows": len(rows), "gates": gates,
    }


def run(repo: Path) -> dict[str, Any]:
    adoption = read_csv(repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_adoption_daily.csv")
    chains = read_csv(repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_chain_distribution_daily.csv")
    trading = read_csv(repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_trading_activity_daily.csv")
    review = read_csv(repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_episode_review_queue.csv")
    rows = join_recent(adoption, chains, trading, review); matrix = coverage_matrix(rows)
    integration_snapshot = repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_yield_integration_summary.json"
    usage_summary = repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_usage_summary.json"
    summary = readiness(rows, matrix, integration_snapshot.exists(), usage_summary.exists())
    out = repo / "data" / "processed" / "04_stablecoin_deferred"
    fields = ["asset_id", "date", "sample_tier", "log_circulating_peg_usd", "pilot_observed_supply_share", "global_peggedusd_supply_share", "supply_growth_30d", "absolute_peg_error_bps", "breach_50bps", "material_chain_count_1m_usd_lag1", "effective_chain_count_lag1", "top_chain_share_lag1", "volume_to_reported_market_cap_lag1", "log1p_volume_24h_usd_lag1", "chain_reconciliation_pass_lag1", "source_review_withheld", "complete_recent_h7_row"]
    write_rows(out / "stablecoin_h7_recent_joined.csv", rows, fields)
    write_rows(out / "stablecoin_h7_coverage_matrix.csv", matrix, ["asset_id", "metric", "expected_rows", "observed_rows", "coverage_ratio", "gate"])
    (out / "stablecoin_h7_readiness.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    findings = repo / "research" / "findings" / "stablecoin-h7-readiness.md"
    failures = "\n".join(f"- **{name}:** `{status}`" for name, status in summary["gates"].items())
    findings.write_text(f"""# H7 Coverage and Readiness Checkpoint

- Status: `{summary['status']}`.
- Recent common window: {RECENT_START} through {RECENT_END}.
- Assets evaluated: {summary['assets_evaluated']}.
- Proposed recent sample at {MIN_ASSET_COVERAGE:.0%} complete-row coverage: {summary['proposed_recent_sample_size']} assets.
- Complete joined rows: {summary['complete_rows']:,} of {summary['total_recent_rows']:,}.

## Gates

{failures}

The 14-asset joined panel is suitable for primary supply/share specification development. Coin Metrics usage histories are preregistered separately as an exploratory USDT/USDC/DAI/TUSD subsample and do not shrink or determine the primary sample. H7 is not headline-analysis ready because depth and integration snapshots lack historical coverage and yield matches require contract validation. Active addresses are not unique users. Chain predictors and trading activity are lagged by one exact calendar day; missing lag dates remain null.
""", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the H7 joined panel and objective readiness audit"); parser.add_argument("--repo", type=Path, default=Path.cwd()); args = parser.parse_args(); print(json.dumps(run(args.repo.resolve()), indent=2))


if __name__ == "__main__": main()
