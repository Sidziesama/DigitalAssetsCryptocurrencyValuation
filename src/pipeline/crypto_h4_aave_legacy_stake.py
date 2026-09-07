from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.pipeline.aave_collateral_state import post_rpc
from src.pipeline.historical import write_rows
from src.pipeline.registry import load_json, sha256


def validate(spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("schema_version") != 1 or spec.get("universe_policy") != "fixed_existing_six_assets_no_expansion":
        raise ValueError("unsupported H4 staking-source configuration")
    if len(spec.get("assets", [])) != 6 or len(set(spec["assets"])) != 6:
        raise ValueError("H4 staking source must retain the fixed six-asset universe")
    component = spec.get("aave_legacy_component", {})
    if component.get("asset_id") != "crypto_aave" or component.get("method") != "totalSupply()":
        raise ValueError("unexpected Aave staking component")
    if component.get("selector") != "0x18160ddd" or component.get("decimals") != 18:
        raise ValueError("unexpected ERC20 totalSupply encoding")
    if len(component.get("contract_address", "")) != 42 or not component.get("rpc_url", "").startswith("https://"):
        raise ValueError("invalid Aave legacy staking source")
    if component.get("measurement_role") != "legacy_component_only" or component.get("unblocks_h4") is not False:
        raise ValueError("legacy stkAAVE must not be treated as complete H4 coverage")
    return component


def decode_total_supply(value: str, decimals: int) -> float:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ValueError("invalid totalSupply response")
    return int(value, 16) / (10 ** decimals)


def normalize(component: dict[str, Any], day: str, block: int, response: dict[str, Any]) -> dict[str, Any] | None:
    if "result" not in response:
        return None
    return {
        "asset_id": component["asset_id"], "date": day, "ethereum_block": block,
        "staking_component": component["component_id"],
        "staked_native_units": decode_total_supply(response["result"], component["decimals"]),
        "measurement_role": component["measurement_role"], "provider": "ethereum_json_rpc",
    }


def collect(repo: Path, start: date, end: date, force: bool = False) -> dict[str, Any]:
    component = validate(load_json(repo / "config/crypto_h4_staking_sources.json"))
    raw_root = repo / "data/raw/crypto_h4_staking/aave_legacy_stkaave"
    block_root = repo / component["block_snapshot_root"]
    rows, missing_blocks, rpc_errors = [], [], []
    day = start
    while day <= end:
        block_path = block_root / f"{day.isoformat()}.json"
        if not block_path.exists():
            missing_blocks.append(day.isoformat()); day += timedelta(days=1); continue
        block = int(load_json(block_path)["block"])
        raw_path = raw_root / f"{day.isoformat()}.json"
        if raw_path.exists() and not force:
            payload = load_json(raw_path)
        else:
            request = {"jsonrpc":"2.0","id":day.isoformat(),"method":"eth_call",
                       "params":[{"to":component["contract_address"],"data":component["selector"]},hex(block)]}
            response = post_rpc(component["rpc_url"], request)
            payload = {"date":day.isoformat(),"block":block,"request":request,"response":response}
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
            raw_path.with_suffix(".metadata.json").write_text(json.dumps({
                "provider":"ethereum_json_rpc", "component":component["component_id"],
                "retrieved_at_utc":datetime.now(timezone.utc).isoformat(), "sha256":sha256(raw_path),
                "measurement_role":component["measurement_role"]}, indent=2) + "\n", encoding="utf-8")
        row = normalize(component, payload["date"], int(payload["block"]), payload["response"])
        if row is None: rpc_errors.append(day.isoformat())
        else: rows.append(row)
        day += timedelta(days=1)
    expected = (end - start).days + 1
    out = repo / "data/processed/historical"
    write_rows(out / "crypto_h4_aave_legacy_stake_daily.csv", rows,
               ["asset_id","date","ethereum_block","staking_component","staked_native_units","measurement_role","provider"])
    result = {
        "status": "aave_legacy_stake_component_complete" if len(rows) == expected else "aave_legacy_stake_component_partial",
        "asset_id": component["asset_id"], "component": component["component_id"],
        "measurement_role": component["measurement_role"], "unblocks_h4": False,
        "start_date": start.isoformat(), "end_date": end.isoformat(), "expected_days": expected,
        "observed_days": len(rows), "missing_block_days": missing_blocks, "rpc_error_days": rpc_errors,
        "minimum_staked_native_units": min((row["staked_native_units"] for row in rows), default=None),
        "maximum_staked_native_units": max((row["staked_native_units"] for row in rows), default=None),
        "limitation": component["limitation"],
    }
    empirical = repo / "data/processed/evidence/crypto_h4_aave_legacy_stake_summary.json"
    empirical.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect the legacy stkAAVE component at historical Ethereum blocks")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.end < args.start: parser.error("--end must be on or after --start")
    print(json.dumps(collect(args.repo.resolve(), args.start, args.end, args.force), indent=2))
