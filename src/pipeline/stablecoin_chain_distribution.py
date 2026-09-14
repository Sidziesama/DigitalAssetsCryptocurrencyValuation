from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .historical import read_csv, write_rows
from .registry import load_json


MATERIAL_USD = 1_000_000


def chain_observations(asset_id: str, payload: dict[str, Any]) -> dict[str, dict[str, float]]:
    by_date: dict[str, dict[str, float]] = defaultdict(dict)
    for chain, history in payload.get("chainBalances", {}).items():
        tokens = history.get("tokens", []) if isinstance(history, dict) else []
        for item in tokens:
            timestamp = item.get("date"); value = (item.get("circulating") or {}).get("peggedUSD")
            if not isinstance(timestamp, (int, float)) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                continue
            day = datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat()
            by_date[day][chain] = float(value)
    return by_date


def distribution_metrics(asset_id: str, by_date: dict[str, dict[str, float]], total_supply: dict[tuple[str, str], float | None]) -> list[dict[str, Any]]:
    output = []
    for day, balances in sorted(by_date.items()):
        positive = {chain: value for chain, value in balances.items() if value > 0}
        chain_total = sum(positive.values()); shares = {chain: value / chain_total for chain, value in positive.items()} if chain_total > 0 else {}
        hhi = sum(share ** 2 for share in shares.values()) if shares else None
        reported = total_supply.get((asset_id, day)); ratio = chain_total / reported if reported is not None and reported > 0 else None
        top_chain = max(shares, key=shares.get) if shares else ""
        output.append({
            "asset_id": asset_id, "date": day, "chain_supply_sum_usd": chain_total,
            "reported_circulating_peg_usd": reported, "chain_to_reported_supply_ratio": ratio,
            "active_chain_count": len(positive), "material_chain_count_1m_usd": sum(value >= MATERIAL_USD for value in positive.values()),
            "chain_hhi": hhi, "effective_chain_count": 1 / hhi if hhi else None,
            "top_chain": top_chain, "top_chain_share": shares.get(top_chain) if top_chain else None,
        })
    return output


def run(repo: Path) -> dict[str, Any]:
    adoption = read_csv(repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_adoption_daily.csv")
    supply_index = {(row["asset_id"], row["date"]): float(row["circulating_peg_usd"]) if row.get("circulating_peg_usd") not in (None, "") else None for row in adoption}
    asset_ids = sorted({row["asset_id"] for row in adoption}); rows: list[dict[str, Any]] = []; unsupported = []
    for asset_id in asset_ids:
        path = repo / "data" / "raw" / "defillama_stablecoin_history" / f"{asset_id}.json"
        if not path.exists(): unsupported.append(asset_id); continue
        by_date = chain_observations(asset_id, load_json(path))
        if not by_date: unsupported.append(asset_id); continue
        rows.extend(distribution_metrics(asset_id, by_date, supply_index))
    rows.sort(key=lambda row: (row["asset_id"], row["date"]))
    out = repo / "data" / "processed" / "04_stablecoin_deferred"; fields = ["asset_id", "date", "chain_supply_sum_usd", "reported_circulating_peg_usd", "chain_to_reported_supply_ratio", "active_chain_count", "material_chain_count_1m_usd", "chain_hhi", "effective_chain_count", "top_chain", "top_chain_share"]
    write_rows(out / "stablecoin_chain_distribution_daily.csv", rows, fields)
    reconciled = [row for row in rows if row["chain_to_reported_supply_ratio"] is not None]
    within_tolerance = sum(.95 <= row["chain_to_reported_supply_ratio"] <= 1.05 for row in reconciled)
    summary = {
        "rows": len(rows), "assets": len({row["asset_id"] for row in rows}), "unsupported_assets": unsupported,
        "reconciled_rows": len(reconciled), "within_5pct_reconciliation_rows": within_tolerance,
        "within_5pct_reconciliation_rate": within_tolerance / len(reconciled) if reconciled else None,
        "interpretation": "cross-chain distribution proxy; not protocol integration count, transaction volume, or user activity",
    }
    (out / "stablecoin_chain_distribution_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    findings = repo / "research" / "findings" / "stablecoin-chain-distribution.md"
    findings.write_text(f"""# Stablecoin Chain Distribution

- Assets with chain-level histories: {summary['assets']} of {len(asset_ids)} primary assets.
- Asset-day chain-distribution rows: {summary['rows']:,}.
- Rows comparable to reported total supply: {summary['reconciled_rows']:,}.
- Chain sums within ±5% of reported supply: {summary['within_5pct_reconciliation_rate']:.1%}.
- Unsupported assets: {', '.join(summary['unsupported_assets']) or 'None'}.

The panel measures distribution across chains using positive and $1 million material-balance thresholds, chain HHI, effective chain count, and top-chain share. It is a distribution-breadth proxy only. It must not be described as protocol integrations, transaction volume, active users, or settlement usage. Reconciliation differences remain visible and require robustness filtering before headline H7 estimation.
""", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build daily stablecoin cross-chain distribution proxies"); parser.add_argument("--repo", type=Path, default=Path.cwd()); args = parser.parse_args(); print(json.dumps(run(args.repo.resolve()), indent=2))


if __name__ == "__main__": main()
