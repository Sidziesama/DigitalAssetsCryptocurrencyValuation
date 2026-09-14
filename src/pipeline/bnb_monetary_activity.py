from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .historical import write_rows
from .registry import load_env_file, load_json, sha256


TERMINAL_FAILURES = {"QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED", "QUERY_STATE_EXPIRED"}


def validate(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1 or spec.get("asset_id") != "crypto_bnb" or spec.get("provider") != "dune":
        raise ValueError("unsupported BNB monetary-activity configuration")
    start, end = date.fromisoformat(spec["start_date"]), date.fromisoformat(spec["end_date"])
    if end < start or spec.get("expected_days") != (end - start).days + 1:
        raise ValueError("invalid BNB activity window")
    if not str(spec.get("api_base", "")).startswith("https://") or not str(spec.get("api_source", "")).startswith("https://"):
        raise ValueError("Dune sources must use HTTPS")
    sql = str(spec.get("sql", ""))
    for required in ("bnb.transactions", 'COUNT(DISTINCT address)', "transaction_count", "active_addresses"):
        if required not in sql:
            raise ValueError(f"SQL is missing required element: {required}")


def api_json(url: str, api_key: str, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers={
        "X-Dune-API-Key": api_key, "Content-Type": "application/json", "User-Agent": "digital-asset-valuation/1.0"
    })
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Dune API HTTP {exc.code}: {detail}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Dune API returned a non-object response")
    return payload


def normalize_rows(payload: dict[str, Any], spec: dict[str, Any]) -> list[dict[str, Any]]:
    source_rows = payload.get("result", {}).get("rows")
    if not isinstance(source_rows, list):
        raise ValueError("Dune result is missing result.rows")
    rows = []
    for source in source_rows:
        day = date.fromisoformat(str(source["date"])[:10])
        active, transactions = int(source["active_addresses"]), int(source["transaction_count"])
        if active < 0 or transactions < 0:
            raise ValueError("activity measures cannot be negative")
        rows.append({"asset_id":"crypto_bnb", "date":day.isoformat(), "active_addresses":active,
                     "transaction_count":transactions, "activity_provider":"dune",
                     "activity_definition":"distinct_from_or_to_addresses_and_transaction_count"})
    rows.sort(key=lambda row: row["date"])
    expected_dates = [(date.fromisoformat(spec["start_date"]) + timedelta(days=i)).isoformat() for i in range(spec["expected_days"])]
    observed = [row["date"] for row in rows]
    if len(observed) != len(set(observed)) or observed != expected_dates:
        raise ValueError(f"Dune result must contain exactly {spec['expected_days']} consecutive daily observations")
    return rows


def readiness(repo: Path, spec: dict[str, Any], status: str, **extra: Any) -> dict[str, Any]:
    result = {"status":status, "asset_id":"crypto_bnb", "provider":"dune", "start_date":spec["start_date"],
              "end_date":spec["end_date"], "expected_days":spec["expected_days"],
              "classification_effect":"none_until_complete_validated_activity_is_collected", **extra}
    output = repo / "data/processed/01_classification/bnb_monetary_activity_summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def collect(repo: Path) -> dict[str, Any]:
    spec = load_json(repo / "config/bnb_monetary_activity.json"); validate(spec)
    load_env_file(repo / ".env")
    api_key = os.environ.get("DUNE_API_KEY", "").strip()
    if not api_key:
        return readiness(repo, spec, "collector_ready_api_key_required", required_environment_variable="DUNE_API_KEY")
    base = spec["api_base"].rstrip("/")
    submitted = api_json(f"{base}/sql/execute", api_key, "POST", {"sql":spec["sql"], "performance":"medium"})
    execution_id = submitted.get("execution_id")
    if not execution_id:
        raise ValueError("Dune submission did not return execution_id")
    state = ""
    for _ in range(spec["maximum_polls"]):
        status_payload = api_json(f"{base}/execution/{execution_id}/status", api_key)
        state = str(status_payload.get("state", ""))
        if state == "QUERY_STATE_COMPLETED":
            break
        if state in TERMINAL_FAILURES:
            raise RuntimeError(f"Dune execution ended in {state}")
        time.sleep(spec["poll_seconds"])
    else:
        raise TimeoutError(f"Dune execution did not finish after {spec['maximum_polls']} polls")
    payload = api_json(f"{base}/execution/{execution_id}/results?limit=1000", api_key)
    rows = normalize_rows(payload, spec)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw = repo / f"data/raw/bnb_monetary_activity/{stamp}_{execution_id}.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    raw.with_suffix(".metadata.json").write_text(json.dumps({"provider":"dune", "execution_id":execution_id,
        "retrieved_at_utc":datetime.now(timezone.utc).isoformat(), "query_source":spec["query_source"],
        "methodology_source":spec["methodology_source"], "sha256":sha256(raw)}, indent=2) + "\n", encoding="utf-8")
    output = repo / "data/processed/00_foundation/bnb_monetary_activity_dune.csv"
    write_rows(output, rows, list(rows[0]))
    return readiness(repo, spec, "complete_validated_activity", observed_days=len(rows), execution_id=execution_id,
                     output_path=str(output.relative_to(repo)), raw_sha256=sha256(raw))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Collect exact daily BNB active-address and transaction activity from Dune")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(collect(parser.parse_args().repo.resolve()), indent=2))
