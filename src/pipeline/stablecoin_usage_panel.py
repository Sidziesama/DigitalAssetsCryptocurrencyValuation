from __future__ import annotations

import argparse
import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .historical import read_csv, write_rows


USAGE_ASSETS = ("stable_usdt", "stable_usdc", "stable_dai", "stable_tusd")
USAGE_FIELDS = ("active_addresses", "ledger_transaction_count", "token_transfer_count")


def numeric(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) and result >= 0 else None


def build_panel(adoption: list[dict[str, Any]], usage: list[dict[str, Any]], allowed_assets: set[str] | None = None) -> list[dict[str, Any]]:
    allowed = allowed_assets or set(USAGE_ASSETS)
    usage_index = {(row["asset_id"], row["date"]): row for row in usage if row["asset_id"] in allowed}
    output: list[dict[str, Any]] = []
    for base in adoption:
        asset_id = base["asset_id"]
        if asset_id not in allowed:
            continue
        lag_day = (date.fromisoformat(base["date"]) - timedelta(days=1)).isoformat()
        source = usage_index.get((asset_id, lag_day), {})
        row: dict[str, Any] = {
            "asset_id": asset_id, "date": base["date"], "usage_date_lag1": lag_day,
            "log_circulating_peg_usd": numeric(base.get("log_circulating_peg_usd")),
            "global_peggedusd_supply_share": numeric(base.get("global_peggedusd_supply_share")),
            "supply_growth_30d": numeric(base.get("supply_growth_30d")),
            "absolute_peg_error_bps": numeric(base.get("absolute_peg_error_bps")),
            "breach_50bps": base.get("breach_50bps"),
            "provider": "coinmetrics_community", "analysis_role": "exploratory_usage_subsample",
        }
        for field in USAGE_FIELDS:
            value = numeric(source.get(field))
            row[f"{field}_lag1"] = value
            row[f"log1p_{field}_lag1"] = math.log1p(value) if value is not None else None
        row["complete_usage_row"] = int(all(row[f"{field}_lag1"] is not None for field in USAGE_FIELDS) and row["global_peggedusd_supply_share"] is not None)
        output.append(row)
    output.sort(key=lambda row: (row["asset_id"], row["date"]))
    return output


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    assets = sorted({row["asset_id"] for row in rows})
    by_asset = []
    for asset_id in assets:
        selected = [row for row in rows if row["asset_id"] == asset_id]
        complete = sum(row["complete_usage_row"] for row in selected)
        by_asset.append({"asset_id": asset_id, "rows": len(selected), "complete_rows": complete, "complete_ratio": complete / len(selected) if selected else 0})
    return {
        "analysis_role": "exploratory_usage_subsample", "assets": assets, "asset_count": len(assets),
        "rows": len(rows), "complete_rows": sum(row["complete_usage_row"] for row in rows),
        "first_date": min((row["date"] for row in rows), default=None), "last_date": max((row["date"] for row in rows), default=None),
        "coverage_by_asset": by_asset,
        "scope_rule": "does not replace or determine the primary 14-asset H7 supply/share sample",
    }


def run(repo: Path) -> dict[str, Any]:
    adoption = read_csv(repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_adoption_daily.csv")
    usage = read_csv(repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_usage_daily_coinmetrics.csv")
    rows = build_panel(adoption, usage)
    out = repo / "data" / "processed" / "04_stablecoin_deferred"
    fields = ["asset_id", "date", "usage_date_lag1", "log_circulating_peg_usd", "global_peggedusd_supply_share", "supply_growth_30d", "absolute_peg_error_bps", "breach_50bps", *[name for field in USAGE_FIELDS for name in (f"{field}_lag1", f"log1p_{field}_lag1")], "complete_usage_row", "provider", "analysis_role"]
    write_rows(out / "stablecoin_h7_usage_exploratory_daily.csv", rows, fields)
    summary = summarize(rows)
    (out / "stablecoin_h7_usage_exploratory_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    findings = repo / "research" / "findings" / "stablecoin-h7-usage-subsample.md"
    coverage_lines = "\n".join(f"- `{row['asset_id']}`: {row['complete_rows']:,}/{row['rows']:,} complete ({row['complete_ratio']:.1%})." for row in summary["coverage_by_asset"])
    findings.write_text(f"""# H7 Exploratory Usage Subsample

- Analysis role: `{summary['analysis_role']}`.
- Assets: {', '.join(summary['assets'])}.
- Asset-day rows: {summary['rows']:,}.
- Complete exact-lag usage rows: {summary['complete_rows']:,}.
- Window: {summary['first_date']} through {summary['last_date']}.

## Coverage

{coverage_lines}

Active addresses, ledger transactions, and token transfers are lagged by one exact calendar day. Missing lag dates remain null. This source-defined four-asset panel is exploratory and does not replace, shrink, or determine the primary 14-asset H7 supply/share sample. Active addresses are not unique users, and results must not be generalized to unsupported stablecoins.
""", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the preregistered exploratory four-asset H7 usage panel")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(run(args.repo.resolve()), indent=2))


if __name__ == "__main__":
    main()
