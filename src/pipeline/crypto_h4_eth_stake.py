from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from src.pipeline.historical import request_json, write_rows
from src.pipeline.registry import load_json, sha256


ACTIVE_STATUSES = {"active_ongoing", "active_exiting", "active_slashed"}


def load_local_env(repo: Path) -> None:
    path = repo / ".env"
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip(); value = value.strip().strip("\"").strip("'")
        if key == "ETH_BEACON_ARCHIVE_API_URL" and value:
            os.environ.setdefault(key, value)


def validate(spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("schema_version") != 1 or spec.get("universe_policy") != "fixed_existing_six_assets_no_expansion":
        raise ValueError("unsupported H4 staking-source configuration")
    source = spec.get("eth_consensus_stake", {})
    if source.get("asset_id") != "crypto_eth" or source.get("component_id") != "active_validator_effective_balance":
        raise ValueError("unexpected ETH consensus-stake configuration")
    if source.get("validator_statuses") != sorted(ACTIVE_STATUSES):
        raise ValueError("ETH collector must include every active consensus status")
    if source.get("genesis_timestamp") != 1606824023 or source.get("seconds_per_slot") != 12:
        raise ValueError("unexpected Ethereum slot constants")
    if not source.get("public_probe_url", "").startswith("https://"):
        raise ValueError("ETH public probe must use HTTPS")
    return source


def date_slot(day: date, source: dict[str, Any]) -> int:
    stamp = int(datetime.combine(day, time(int(source["snapshot_hour_utc"])), timezone.utc).timestamp())
    if stamp < int(source["genesis_timestamp"]):
        raise ValueError("snapshot predates Beacon Chain genesis")
    return (stamp - int(source["genesis_timestamp"])) // int(source["seconds_per_slot"])


def provider_label(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname:
        raise ValueError("ETH archive endpoint must be HTTPS")
    return parts.hostname


def normalize(payload: dict[str, Any], day: date, slot: int, provider: str) -> dict[str, Any]:
    records = payload.get("data")
    if not isinstance(records, list) or not records:
        raise ValueError("historical validator response has no data")
    active = [row for row in records if row.get("status") in ACTIVE_STATUSES]
    if not active:
        raise ValueError("historical validator response has no active validators")
    total_gwei = 0
    for row in active:
        validator = row.get("validator", {})
        value = validator.get("effective_balance")
        if not isinstance(value, str) or not value.isdigit():
            raise ValueError("invalid validator effective balance")
        total_gwei += int(value)
    return {
        "asset_id": "crypto_eth", "date": day.isoformat(), "beacon_slot": slot,
        "active_validators": len(active), "total_staked_native_units": total_gwei / 1e9,
        "measurement_role": "consensus_active_effective_balance", "provider": provider,
    }


def probe(repo: Path, endpoint: str | None = None) -> dict[str, Any]:
    source = validate(load_json(repo / "config/crypto_h4_staking_sources.json"))
    load_local_env(repo)
    configured = endpoint or os.environ.get(source["api_url_env"], "")
    result = {
        "status": "eth_collector_ready_archive_endpoint_required" if not configured else "eth_collector_ready_archive_endpoint_configured",
        "asset_id": "crypto_eth", "measurement_role": source["measurement_role"],
        "archive_endpoint_configured": bool(configured),
        "provider": provider_label(configured) if configured else None,
        "public_probe_url": source["public_probe_url"],
        "public_probe_limitation": "The tested no-key public endpoint serves head data but rejected historical validator states; it cannot supply the study window.",
        "exact_measure": "Sum effective_balance for active_ongoing, active_exiting, and active_slashed validators at the daily UTC snapshot slot.",
        "approximation_rejected": "Active validator count multiplied by 32 ETH is not used because EIP-7251 permits larger effective balances.",
        "unblocks_h4": False, "limitation": source["limitation"],
    }
    path = repo / "data/processed/evidence/crypto_h4_eth_stake_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def collect(repo: Path, start: date, end: date, endpoint: str | None = None, force: bool = False,
            fetch: Callable[[str], dict[str, Any]] = request_json) -> dict[str, Any]:
    source = validate(load_json(repo / "config/crypto_h4_staking_sources.json"))
    load_local_env(repo)
    api_url = endpoint or os.environ.get(source["api_url_env"], "")
    if not api_url:
        return probe(repo)
    provider = provider_label(api_url); raw_root = repo / "data/raw/crypto_h4_staking/eth_active_effective_balance"
    rows: list[dict[str, Any]] = []; failures: list[dict[str, Any]] = []; day = start
    while day <= end:
        slot = date_slot(day, source); raw_path = raw_root / f"{day.isoformat()}.json"
        try:
            if raw_path.exists() and not force:
                payload = load_json(raw_path)
            else:
                statuses = "&".join(f"status={value}" for value in source["validator_statuses"])
                payload = fetch(f"{api_url.rstrip('/')}/eth/v1/beacon/states/{slot}/validators?{statuses}")
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
                raw_path.with_suffix(".metadata.json").write_text(json.dumps({
                    "provider": provider, "beacon_slot": slot, "measurement_role": source["measurement_role"],
                    "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "sha256": sha256(raw_path),
                }, indent=2) + "\n", encoding="utf-8")
            rows.append(normalize(payload, day, slot, provider))
        except Exception as exc:
            failures.append({"date": day.isoformat(), "beacon_slot": slot, "error": str(exc)})
        day += timedelta(days=1)
    expected = (end - start).days + 1; out = repo / "data/processed/historical"
    write_rows(out / "crypto_h4_eth_stake_daily.csv", rows, [
        "asset_id", "date", "beacon_slot", "active_validators", "total_staked_native_units", "measurement_role", "provider"])
    complete = len(rows) == expected and not failures
    result = {
        "status": "eth_consensus_stake_window_complete" if complete else "eth_consensus_stake_window_partial",
        "asset_id": "crypto_eth", "measurement_role": source["measurement_role"], "provider": provider,
        "start_date": start.isoformat(), "end_date": end.isoformat(), "expected_days": expected,
        "observed_days": len(rows), "failures": failures,
        "minimum_staked_native_units": min((row["total_staked_native_units"] for row in rows), default=None),
        "maximum_staked_native_units": max((row["total_staked_native_units"] for row in rows), default=None),
        "unblocks_h4": complete, "limitation": source["limitation"],
    }
    path = repo / "data/processed/evidence/crypto_h4_eth_stake_summary.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect exact historical active ETH consensus effective balance")
    parser.add_argument("--repo", type=Path, default=Path.cwd()); parser.add_argument("--start", type=date.fromisoformat)
    parser.add_argument("--end", type=date.fromisoformat); parser.add_argument("--endpoint"); parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if (args.start is None) != (args.end is None): parser.error("--start and --end must be supplied together")
    if args.start and args.end and args.end < args.start: parser.error("--end must be on or after --start")
    result = collect(args.repo.resolve(), args.start, args.end, args.endpoint, args.force) if args.start else probe(args.repo.resolve(), args.endpoint)
    print(json.dumps(result, indent=2))
