from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from .historical import read_csv, write_rows


def numeric(value: Any) -> float | None:
    try: result = float(value)
    except (TypeError, ValueError): return None
    return result if math.isfinite(result) else None


def build_rows(adoption: list[dict[str, Any]], market: list[dict[str, Any]]) -> list[dict[str, Any]]:
    adoption_index = {(row["asset_id"], row["date"]): row for row in adoption}
    output = []
    for source in market:
        key = (source["asset_id"], source["date"]); base = adoption_index.get(key)
        if base is None: continue
        volume = numeric(source.get("volume_24h_usd")); market_cap = numeric(source.get("market_cap_usd")); supply = numeric(base.get("circulating_peg_usd"))
        output.append({
            "asset_id": key[0], "date": key[1], "volume_24h_usd_reported": volume,
            "log1p_volume_24h_usd": math.log1p(volume) if volume is not None and volume >= 0 else None,
            "reported_market_cap_usd": market_cap, "circulating_peg_usd": supply,
            "volume_to_reported_market_cap": volume / market_cap if volume is not None and market_cap is not None and market_cap > 0 else None,
            "cross_provider_volume_to_supply": volume / supply if volume is not None and supply is not None and supply > 0 else None,
            "market_cap_to_supply_ratio": market_cap / supply if market_cap is not None and supply is not None and supply > 0 else None,
            "pilot_observed_supply_share": numeric(base.get("pilot_observed_supply_share")),
            "absolute_peg_error_bps": numeric(base.get("absolute_peg_error_bps")), "breach_50bps": int(base["breach_50bps"]),
            "provider": "coinpaprika",
        })
    output.sort(key=lambda row: (row["asset_id"], row["date"]))
    return output


def run(repo: Path) -> dict[str, Any]:
    adoption = read_csv(repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_adoption_daily.csv")
    market = read_csv(repo / "data" / "processed" / "00_foundation" / "market_daily_coinpaprika.csv")
    rows = build_rows(adoption, market); out = repo / "data" / "processed" / "04_stablecoin_deferred"
    fields = ["asset_id", "date", "volume_24h_usd_reported", "log1p_volume_24h_usd", "reported_market_cap_usd", "circulating_peg_usd", "volume_to_reported_market_cap", "cross_provider_volume_to_supply", "market_cap_to_supply_ratio", "pilot_observed_supply_share", "absolute_peg_error_bps", "breach_50bps", "provider"]
    write_rows(out / "stablecoin_trading_activity_daily.csv", rows, fields)
    ratios = [row["market_cap_to_supply_ratio"] for row in rows if row["market_cap_to_supply_ratio"] is not None]
    audit = []
    for asset_id in sorted({row["asset_id"] for row in rows}):
        asset_ratios = [row["market_cap_to_supply_ratio"] for row in rows if row["asset_id"] == asset_id and row["market_cap_to_supply_ratio"] is not None]
        audit.append({"asset_id": asset_id, "comparable_rows": len(asset_ratios), "mean_market_cap_to_supply_ratio": sum(asset_ratios) / len(asset_ratios) if asset_ratios else None, "within_5pct_rows": sum(.95 <= value <= 1.05 for value in asset_ratios), "within_5pct_rate": sum(.95 <= value <= 1.05 for value in asset_ratios) / len(asset_ratios) if asset_ratios else None, "cross_provider_turnover_status": "diagnostic_only"})
    write_rows(out / "stablecoin_trading_activity_reconciliation.csv", audit, ["asset_id", "comparable_rows", "mean_market_cap_to_supply_ratio", "within_5pct_rows", "within_5pct_rate", "cross_provider_turnover_status"])
    summary = {
        "rows": len(rows), "assets": len({row["asset_id"] for row in rows}),
        "start_date": min((row["date"] for row in rows), default=None), "end_date": max((row["date"] for row in rows), default=None),
        "same_provider_turnover_rows": sum(row["volume_to_reported_market_cap"] is not None for row in rows),
        "cross_provider_turnover_rows": sum(row["cross_provider_volume_to_supply"] is not None for row in rows),
        "market_cap_supply_reconciliation_rows": len(ratios),
        "market_cap_supply_ratio_within_5pct_rate": sum(.95 <= value <= 1.05 for value in ratios) / len(ratios) if ratios else None,
        "interpretation": "provider-reported 24-hour trading activity proxy; not order-book depth, spread, price impact, or executable liquidity",
    }
    (out / "stablecoin_trading_activity_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    findings = repo / "research" / "findings" / "stablecoin-trading-activity.md"
    findings.write_text(f"""# Stablecoin Trading-Activity Proxy

- Assets: {summary['assets']}.
- Asset-day rows: {summary['rows']:,}.
- Window: {summary['start_date']} through {summary['end_date']}.
- Rows with same-provider volume-to-market-cap turnover: {summary['same_provider_turnover_rows']:,}.
- Rows with cross-provider volume-to-supply diagnostics: {summary['cross_provider_turnover_rows']:,}.
- Reported market cap within ±5% of circulation: {summary['market_cap_supply_ratio_within_5pct_rate']:.1%} of comparable rows.

The primary turnover proxy divides CoinPaprika's reported 24-hour volume by CoinPaprika's reported market cap, preserving a consistent provider definition. Volume divided by DeFiLlama circulation is retained as a diagnostic only because cross-provider market-cap/supply reconciliation is weak for several assets. Neither field measures order-book depth, bid-ask spread, price impact, venue-adjusted liquidity, or settlement usage. The free source covers only a rolling recent year and therefore cannot support full-period H7 claims.
""", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build recent stablecoin trading-activity proxies"); parser.add_argument("--repo", type=Path, default=Path.cwd()); args = parser.parse_args(); print(json.dumps(run(args.repo.resolve()), indent=2))


if __name__ == "__main__": main()
