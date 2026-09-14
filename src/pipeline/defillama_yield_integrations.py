from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .historical import request_json, write_rows
from .registry import load_json, sha256, validate_asset_config


URL = "https://yields.llama.fi/pools"


def symbol_components(symbol: Any) -> set[str]:
    """Return exact alphanumeric components; never use substring matching."""
    if not isinstance(symbol, str):
        return set()
    return {part for part in re.split(r"[^A-Z0-9]+", symbol.upper()) if part}


def match_pools(assets: list[dict[str, Any]], pools: list[dict[str, Any]], snapshot_utc: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    matched: list[dict[str, Any]] = []
    for pool in pools:
        components = symbol_components(pool.get("symbol"))
        for asset in assets:
            if asset["symbol"].upper() not in components:
                continue
            tvl = pool.get("tvlUsd")
            matched.append({
                "asset_id": asset["asset_id"], "snapshot_utc": snapshot_utc,
                "pool_id": pool.get("pool"), "project": pool.get("project"),
                "chain": pool.get("chain"), "pool_symbol": pool.get("symbol"),
                "pool_tvl_usd": tvl if isinstance(tvl, (int, float)) and tvl >= 0 else None,
                "pool_stablecoin_flag": pool.get("stablecoin"),
                "match_rule": "exact_alphanumeric_symbol_component",
                "provider": "defillama_yields",
            })
    summaries: list[dict[str, Any]] = []
    for asset in assets:
        rows = [row for row in matched if row["asset_id"] == asset["asset_id"]]
        projects = {row["project"] for row in rows if row["project"]}
        chains = {row["chain"] for row in rows if row["chain"]}
        tvls = [row["pool_tvl_usd"] for row in rows if row["pool_tvl_usd"] is not None]
        summaries.append({
            "asset_id": asset["asset_id"], "snapshot_utc": snapshot_utc,
            "yield_pool_count": len(rows), "yield_project_count": len(projects),
            "yield_chain_count": len(chains), "gross_matched_pool_tvl_usd": sum(tvls),
            "pools_with_tvl": len(tvls), "provider": "defillama_yields",
            "interpretation": "current yield-pool integration proxy; not exhaustive protocol adoption",
        })
    return matched, summaries


def collect(repo: Path) -> dict[str, Any]:
    assets = [a for a in validate_asset_config(load_json(repo / "config" / "assets.json")) if a["universe"] == "stablecoin" and a["tier"] != "failure_control" and a["asset_id"] != "stable_paxg"]
    retrieved = datetime.now(timezone.utc)
    snapshot_utc = retrieved.isoformat()
    stamp = retrieved.strftime("%Y%m%dT%H%M%S.%fZ")
    payload = request_json(URL)
    if not isinstance(payload, dict) or payload.get("status") != "success" or not isinstance(payload.get("data"), list):
        raise ValueError("unexpected DeFiLlama yields response schema")
    raw_dir = repo / "data" / "raw" / "defillama_yield_pools"
    raw_path = raw_dir / f"{stamp}.json"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    raw_path.with_suffix(".metadata.json").write_text(json.dumps({
        "provider": "defillama_yields", "endpoint": URL,
        "retrieved_at_utc": snapshot_utc, "http_status": 200,
        "sha256": sha256(raw_path), "pool_records": len(payload["data"]),
        "match_rule": "exact alphanumeric component of provider pool symbol",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    matches, summary_rows = match_pools(assets, payload["data"], snapshot_utc)
    out = repo / "data" / "processed" / "04_stablecoin_deferred"
    write_rows(out / "stablecoin_yield_pool_matches_latest.csv", matches, ["asset_id", "snapshot_utc", "pool_id", "project", "chain", "pool_symbol", "pool_tvl_usd", "pool_stablecoin_flag", "match_rule", "provider"])
    write_rows(out / "stablecoin_yield_integration_snapshot.csv", summary_rows, ["asset_id", "snapshot_utc", "yield_pool_count", "yield_project_count", "yield_chain_count", "gross_matched_pool_tvl_usd", "pools_with_tvl", "provider", "interpretation"])
    represented = sum(row["yield_project_count"] > 0 for row in summary_rows)
    summary = {
        "snapshot_utc": snapshot_utc, "provider_pool_records": len(payload["data"]),
        "eligible_assets": len(assets), "assets_with_matched_projects": represented,
        "matched_asset_pool_rows": len(matches),
        "readiness": "cross_sectional_proxy_only_not_historical_or_exhaustive",
        "limitations": ["symbol-component rather than contract-address matching", "yield-bearing pools only", "gross pool TVL is not token-specific TVL"],
    }
    (out / "stablecoin_yield_integration_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    findings = repo / "research" / "findings" / "stablecoin-yield-integrations.md"
    findings.write_text(f"""# Stablecoin Yield-Pool Integration Snapshot

- Provider pools inspected: {summary['provider_pool_records']:,}.
- Primary stablecoins evaluated: {summary['eligible_assets']}.
- Assets with at least one matched DeFiLlama yield project: {summary['assets_with_matched_projects']}.
- Matched asset-pool rows: {summary['matched_asset_pool_rows']:,}.
- Status: `{summary['readiness']}`.

This is a conservative current integration proxy. A pool matches only when the stablecoin symbol is an exact alphanumeric component of DeFiLlama's pool symbol; substring matches are prohibited. Counts cover yield-bearing pools listed by DeFiLlama, not every protocol integration. Gross matched-pool TVL is the full pool TVL and must not be interpreted as the stablecoin's token-specific balance. Contract-address validation and historical snapshots are required before this variable enters headline H7 estimation.
""", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a conservative DeFiLlama stablecoin yield-integration snapshot")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(collect(args.repo.resolve()), indent=2))


if __name__ == "__main__":
    main()
