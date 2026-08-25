from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .historical import request_json, write_rows
from .registry import load_json, sha256


URL = "https://stablecoins.llama.fi/stablecoincharts/all"


def normalize(payload: list[dict[str, Any]], start: date, end: date) -> list[dict[str, Any]]:
    """Normalize DeFiLlama's aggregate pegged-USD history without interpolation."""
    output: dict[str, dict[str, Any]] = {}
    for item in payload:
        timestamp = item.get("date")
        value = (item.get("totalCirculatingUSD") or {}).get("peggedUSD")
        try:
            day = datetime.fromtimestamp(int(timestamp), timezone.utc).date()
            amount = float(value)
        except (TypeError, ValueError, OverflowError):
            continue
        if start <= day <= end and amount >= 0:
            output[day.isoformat()] = {
                "date": day.isoformat(),
                "global_peggedusd_circulating_usd": amount,
                "provider": "defillama",
                "source_field": "totalCirculatingUSD.peggedUSD",
            }
    return [output[key] for key in sorted(output)]


def coverage(rows: list[dict[str, Any]], start: date, end: date) -> dict[str, Any]:
    expected = (end - start).days + 1
    observed = len({row["date"] for row in rows})
    return {
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "expected_days": expected, "observed_days": observed,
        "coverage_ratio": observed / expected if expected else 0,
        "first_observed_date": rows[0]["date"] if rows else None,
        "last_observed_date": rows[-1]["date"] if rows else None,
        "status": "pass" if observed / expected >= .95 else "review",
    }


def collect(repo: Path, start: date, end: date, force: bool = False) -> dict[str, Any]:
    raw_dir = repo / "data" / "raw" / "defillama_global_stablecoin_history"
    raw_path = raw_dir / "global.json"
    meta_path = raw_dir / "global.metadata.json"
    if raw_path.exists() and not force:
        payload = load_json(raw_path)
    else:
        payload = request_json(URL)
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
        meta_path.write_text(json.dumps({
            "provider": "defillama", "endpoint": URL,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "http_status": 200, "sha256": sha256(raw_path),
            "universe_definition": "DeFiLlama aggregate peggedUSD assets",
            "normalized_field": "totalCirculatingUSD.peggedUSD",
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not isinstance(payload, list):
        raise ValueError("expected a list from DeFiLlama stablecoincharts/all")
    rows = normalize(payload, start, end)
    out = repo / "data" / "processed" / "historical"
    write_rows(out / "stablecoin_global_market_daily.csv", rows, ["date", "global_peggedusd_circulating_usd", "provider", "source_field"])
    audit = coverage(rows, start, end)
    (out / "stablecoin_global_market_coverage.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect DeFiLlama aggregate pegged-USD circulation history")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    print(json.dumps(collect(args.repo.resolve(), args.start, args.end, args.force), indent=2))


if __name__ == "__main__":
    main()
