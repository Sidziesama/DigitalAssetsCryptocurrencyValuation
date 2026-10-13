from __future__ import annotations

import argparse
import csv
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


def url(base: str, provider_id: str, metrics: list[str], start: str, end: str) -> str:
    query = urllib.parse.urlencode({"assets": provider_id, "metrics": ",".join(metrics), "frequency": "1d", "start_time": start, "end_time": end, "page_size": 10000})
    return f"{base.rstrip('/')}/timeseries/asset-metrics?{query}"


def normalize(payload: dict[str, Any], asset_id: str, provider_id: str, start: str, end: str) -> list[dict[str, Any]]:
    rows = {}
    for item in payload.get("data", []):
        day = str(item.get("time", ""))[:10]
        try: date.fromisoformat(day)
        except ValueError: continue
        if item.get("asset") != provider_id or not start <= day <= end: continue
        try:
            addresses = float(item["AdrActCnt"]) if item.get("AdrActCnt") is not None else None
            transactions = float(item["TxCnt"]) if item.get("TxCnt") is not None else None
        except (TypeError, ValueError):
            addresses = transactions = None
        rows[day] = {"asset_id": asset_id, "date": day, "active_addresses": addresses, "transaction_count": transactions, "provider": "coinmetrics_community", "provider_id": provider_id}
    return [rows[day] for day in sorted(rows)]


def collect(repo: Path, refresh: bool = False) -> dict[str, Any]:
    spec = json.loads((repo / "config/crypto_h1_activity_history.json").read_text())
    if spec.get("status") != "frozen_before_history_collection_and_estimation":
        raise ValueError("H1 history design must be frozen")
    start, end = spec["window"]["start"], spec["window"]["end"]
    expected = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
    raw_root = repo / spec["raw_directory"]
    all_rows, coverage = [], []
    for mapping in spec["assets"]:
        asset_id, provider_id = mapping["asset_id"], mapping["provider_id"]
        request_url = url(spec["base_url"], provider_id, spec["metrics"], start, end)
        raw_path = raw_root / asset_id / f"{start}_{end}.json"
        if raw_path.exists() and not refresh:
            payload = json.loads(raw_path.read_text())
        else:
            with urllib.request.urlopen(request_url, timeout=60) as response: raw = response.read()
            payload = json.loads(raw)
            if payload.get("next_page_url"): raise ValueError("unexpected pagination in H1 history response")
            raw_path.parent.mkdir(parents=True, exist_ok=True); raw_path.write_bytes(raw + (b"" if raw.endswith(b"\n") else b"\n"))
            digest = hashlib.sha256(raw_path.read_bytes()).hexdigest()
            raw_path.with_suffix(".metadata.json").write_text(json.dumps({"asset_id": asset_id, "provider_id": provider_id, "url": request_url, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "sha256": digest}, indent=2) + "\n")
        rows = normalize(payload, asset_id, provider_id, start, end); all_rows.extend(rows)
        address_days = sum(row["active_addresses"] is not None for row in rows); transaction_days = sum(row["transaction_count"] is not None for row in rows)
        coverage.append({"asset_id": asset_id, "provider_id": provider_id, "expected_days": expected, "observed_days": len(rows), "active_address_days": address_days, "transaction_days": transaction_days, "complete": int(address_days == transaction_days == expected)})
    out = repo / "data/processed/00_foundation"; out.mkdir(parents=True, exist_ok=True)
    for path, rows in ((out / "crypto_h1_activity_history_coinmetrics.csv", all_rows), (out / "crypto_h1_activity_history_coverage.csv", coverage)):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    summary = {"status": "h1_activity_history_collected", "window": spec["window"], "assets": len(coverage), "rows": len(all_rows), "complete_assets": sum(row["complete"] for row in coverage), "expected_days_per_asset": expected}
    (out / "crypto_h1_activity_history_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect frozen one-year H1 activity histories")
    parser.add_argument("--repo", type=Path, default=Path.cwd()); parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    print(json.dumps(collect(args.repo.resolve(), args.refresh), indent=2))
