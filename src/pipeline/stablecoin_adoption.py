from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .historical import read_csv, write_rows


LAGS = (1, 30, 90)


def numeric(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def build_adoption_panel(panel: list[dict[str, Any]], global_market: list[dict[str, Any]] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    global_index = {row["date"]: numeric(row.get("global_peggedusd_circulating_usd")) for row in (global_market or [])}
    primary = [row for row in panel if not int(row.get("failure_control", 0))]
    supply_index = {(row["asset_id"], row["date"]): numeric(row.get("circulating_peg_usd")) for row in primary}
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in primary: by_date[row["date"]].append(row)
    daily_totals: dict[str, dict[str, Any]] = {}
    for day, rows in by_date.items():
        observed = [(row["asset_id"], numeric(row.get("circulating_peg_usd"))) for row in rows]
        observed = [(asset_id, value) for asset_id, value in observed if value is not None and value >= 0]
        total = sum(value for _, value in observed)
        shares = [value / total for _, value in observed] if total > 0 else []
        daily_totals[day] = {
            "date": day, "pilot_total_circulating_peg_usd": total if observed else None,
            "assets_with_supply": len(observed), "pilot_supply_hhi": sum(share ** 2 for share in shares) if shares else None,
            "global_peggedusd_circulating_usd": global_index.get(day),
        }
    output: list[dict[str, Any]] = []
    for row in primary:
        asset_id, day_text = row["asset_id"], row["date"]
        day = date.fromisoformat(day_text); supply = numeric(row.get("circulating_peg_usd")); totals = daily_totals[day_text]
        result: dict[str, Any] = {
            "asset_id": asset_id, "date": day_text, "sample_tier": row.get("sample_tier"),
            "circulating_peg_usd": supply, "log_circulating_peg_usd": math.log(supply) if supply is not None and supply > 0 else None,
            **totals,
            "pilot_observed_supply_share": supply / totals["pilot_total_circulating_peg_usd"] if supply is not None and totals["pilot_total_circulating_peg_usd"] else None,
            "global_peggedusd_supply_share": supply / totals["global_peggedusd_circulating_usd"] if supply is not None and totals["global_peggedusd_circulating_usd"] else None,
            "absolute_peg_error_bps": numeric(row.get("absolute_peg_error_bps")), "breach_50bps": int(row["breach_50bps"]),
        }
        for lag in LAGS:
            lag_day = (day - timedelta(days=lag)).isoformat(); lag_supply = supply_index.get((asset_id, lag_day))
            result[f"supply_lag_{lag}d"] = lag_supply
            result[f"supply_growth_{lag}d"] = supply / lag_supply - 1 if supply is not None and lag_supply is not None and lag_supply > 0 else None
        output.append(result)
    output.sort(key=lambda row: (row["asset_id"], row["date"]))
    market_rows = []
    for day, totals in sorted(daily_totals.items()):
        current = totals["pilot_total_circulating_peg_usd"]
        result = dict(totals)
        result["pilot_coverage_of_global_peggedusd"] = current / result["global_peggedusd_circulating_usd"] if current is not None and result["global_peggedusd_circulating_usd"] else None
        for lag in LAGS:
            lag_total = daily_totals.get((date.fromisoformat(day) - timedelta(days=lag)).isoformat(), {}).get("pilot_total_circulating_peg_usd")
            result[f"pilot_total_supply_growth_{lag}d"] = current / lag_total - 1 if current is not None and lag_total is not None and lag_total > 0 else None
        market_rows.append(result)
    return output, market_rows


def summarize(rows: list[dict[str, Any]], market: list[dict[str, Any]]) -> dict[str, Any]:
    usable_30d = sum(row["supply_growth_30d"] is not None for row in rows)
    share_rows = sum(row["pilot_observed_supply_share"] is not None for row in rows)
    global_share_rows = sum(row["global_peggedusd_supply_share"] is not None for row in rows)
    return {
        "asset_days": len(rows), "assets": len({row["asset_id"] for row in rows}), "market_days": len(market),
        "share_rows": share_rows, "global_share_rows": global_share_rows, "growth_30d_rows": usable_30d,
        "latest_date": market[-1]["date"] if market else None,
        "latest_pilot_total_circulating_peg_usd": market[-1]["pilot_total_circulating_peg_usd"] if market else None,
        "latest_assets_with_supply": market[-1]["assets_with_supply"] if market else 0,
        "share_definition": "asset supply divided by observed primary-pilot supply on the same date; not global market share",
        "global_share_definition": "asset circulating.peggedUSD divided by DeFiLlama totalCirculatingUSD.peggedUSD on the same UTC date",
    }


def run(repo: Path) -> dict[str, Any]:
    panel = read_csv(repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_daily.csv")
    global_market = read_csv(repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_global_market_daily.csv")
    rows, market = build_adoption_panel(panel, global_market); out = repo / "data" / "processed" / "04_stablecoin_deferred"
    fields = ["asset_id", "date", "sample_tier", "circulating_peg_usd", "log_circulating_peg_usd", "pilot_total_circulating_peg_usd", "assets_with_supply", "pilot_supply_hhi", "pilot_observed_supply_share", "global_peggedusd_circulating_usd", "global_peggedusd_supply_share", *[name for lag in LAGS for name in (f"supply_lag_{lag}d", f"supply_growth_{lag}d")], "absolute_peg_error_bps", "breach_50bps"]
    market_fields = ["date", "pilot_total_circulating_peg_usd", "assets_with_supply", "pilot_supply_hhi", "global_peggedusd_circulating_usd", "pilot_coverage_of_global_peggedusd", *[f"pilot_total_supply_growth_{lag}d" for lag in LAGS]]
    write_rows(out / "stablecoin_adoption_daily.csv", rows, fields); write_rows(out / "stablecoin_pilot_market_daily.csv", market, market_fields)
    summary = summarize(rows, market); (out / "stablecoin_adoption_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    findings = repo / "research" / "findings" / "stablecoin-adoption-panel.md"
    findings.write_text(f"""# Stablecoin Adoption Panel

- Primary-sample assets: {summary['assets']}.
- Asset-day rows: {summary['asset_days']:,}.
- Rows with within-pilot observed supply share: {summary['share_rows']:,}.
- Rows with DeFiLlama global pegged-USD supply share: {summary['global_share_rows']:,}.
- Rows with exact-date 30-day supply growth: {summary['growth_30d_rows']:,}.
- Latest market date: {summary['latest_date']} with {summary['latest_assets_with_supply']} assets reporting supply.
- Latest observed pilot supply: ${summary['latest_pilot_total_circulating_peg_usd']:,.0f}.

`pilot_observed_supply_share` is an internally consistent share of the observed primary pilot universe. `global_peggedusd_supply_share` uses the exact-date DeFiLlama `totalCirculatingUSD.peggedUSD` denominator and is therefore a share of DeFiLlama's pegged-USD universe, not every stable-value asset. Exact-date lags are used. USTC and PAXG are excluded under the preregistered primary-sample rules.
""", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the H7 stablecoin supply and pilot-share panel"); parser.add_argument("--repo", type=Path, default=Path.cwd()); args = parser.parse_args(); print(json.dumps(run(args.repo.resolve()), indent=2))


if __name__ == "__main__": main()
