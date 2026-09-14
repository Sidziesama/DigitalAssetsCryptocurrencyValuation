from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .historical import coverage_record, merge_rows, read_csv, write_rows
from .registry import load_json, sha256, validate_asset_config


BASE_URL = "https://min-api.cryptocompare.com/data"
MAX_POINTS = 2000


def request_json(url: str, retries: int = 4) -> Any:
    headers = {"Accept": "application/json", "User-Agent": "digital-assets-valuation-research/0.1"}
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
                payload = json.load(response)
            if payload.get("Response") == "Error":
                raise ValueError(payload.get("Message", "CryptoCompare provider error"))
            return payload
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def histoday_url(base_url: str, symbol: str, end: date, limit: int) -> str:
    if not 1 <= limit <= MAX_POINTS:
        raise ValueError(f"limit must be between 1 and {MAX_POINTS}")
    to_ts = int(datetime.combine(end, datetime.min.time(), timezone.utc).timestamp())
    query = urllib.parse.urlencode({
        "fsym": symbol.upper(), "tsym": "USD", "limit": limit, "toTs": to_ts,
        "e": "CCCAGG", "aggregate": 1, "tryConversion": "true",
        "extraParams": "digital_assets_valuation_nyu",
    })
    return f"{base_url.rstrip('/')}/v2/histoday?{query}"


def response_rows(payload: dict[str, Any], start: date, end: date) -> list[dict[str, Any]]:
    values = payload.get("Data", {}).get("Data", [])
    rows: dict[str, dict[str, Any]] = {}
    for item in values:
        timestamp = item.get("time")
        if not isinstance(timestamp, (int, float)):
            continue
        day = datetime.fromtimestamp(timestamp, timezone.utc).date()
        if not start <= day <= end:
            continue
        ohlc = [item.get(field) for field in ("open", "high", "low", "close")]
        if not any(isinstance(value, (int, float)) and value > 0 for value in ohlc):
            continue
        rows[day.isoformat()] = {
            "date": day.isoformat(), "open_usd": item.get("open"), "high_usd": item.get("high"),
            "low_usd": item.get("low"), "close_usd": item.get("close"),
            "volume_base": item.get("volumefrom"), "volume_quote_usd": item.get("volumeto"),
            "conversion_type": item.get("conversionType"), "conversion_symbol": item.get("conversionSymbol"),
        }
    return [rows[day] for day in sorted(rows)]


def resolve_symbols(assets: list[dict[str, Any]], coinlist: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    provider_rows = coinlist.get("Data", {})
    resolved: dict[str, str] = {}
    unresolved: dict[str, str] = {}
    for asset in assets:
        explicit = asset.get("cryptocompare_symbol")
        if explicit:
            resolved[asset["asset_id"]] = explicit.upper()
            continue
        symbol = asset["symbol"].upper()
        row = provider_rows.get(symbol)
        if not isinstance(row, dict):
            unresolved[asset["asset_id"]] = "not_found"
            continue
        provider_name = str(row.get("CoinName", "")).casefold()
        asset_name = asset["name"].casefold()
        if provider_name == asset_name or provider_name in asset_name or asset_name in provider_name:
            resolved[asset["asset_id"]] = symbol
        else:
            unresolved[asset["asset_id"]] = "name_mismatch"
    return resolved, unresolved


def batch_ranges(start: date, end: date) -> list[tuple[date, date]]:
    batches: list[tuple[date, date]] = []
    cursor = end
    while cursor >= start:
        batch_start = max(start, cursor - timedelta(days=MAX_POINTS - 1))
        batches.append((batch_start, cursor))
        cursor = batch_start - timedelta(days=1)
    return batches


def collect(repo: Path, start: date, end: date, asset_ids: set[str] | None = None, force: bool = False, base_url: str = BASE_URL) -> dict[str, Any]:
    assets = [asset for asset in validate_asset_config(load_json(repo / "config" / "assets.json")) if asset["universe"] == "crypto"]
    if asset_ids:
        unknown = asset_ids - {asset["asset_id"] for asset in assets}
        if unknown:
            raise ValueError(f"unknown crypto asset ids: {sorted(unknown)}")
        assets = [asset for asset in assets if asset["asset_id"] in asset_ids]
    raw_root = repo / "data" / "raw" / "cryptocompare"
    coinlist_path = raw_root / "coinlist.json"
    if coinlist_path.exists() and not force:
        coinlist = load_json(coinlist_path)
    else:
        coinlist = request_json(f"{base_url.rstrip('/')}/all/coinlist?summary=true")
        raw_root.mkdir(parents=True, exist_ok=True)
        coinlist_path.write_text(json.dumps(coinlist, separators=(",", ":")) + "\n", encoding="utf-8")
    resolved, unresolved = resolve_symbols(assets, coinlist)
    errors: dict[str, str] = {}
    all_rows: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for asset in assets:
        symbol = resolved.get(asset["asset_id"])
        if not symbol:
            continue
        asset_rows: list[dict[str, Any]] = []
        for batch_start, batch_end in batch_ranges(start, end):
            raw_path = raw_root / asset["asset_id"] / f"{batch_start.isoformat()}_{batch_end.isoformat()}.json"
            if raw_path.exists() and not force:
                payload = load_json(raw_path)
            else:
                try:
                    payload = request_json(histoday_url(base_url, symbol, batch_end, (batch_end - batch_start).days + 1))
                except (urllib.error.HTTPError, ValueError) as exc:
                    errors[asset["asset_id"]] = str(exc)
                    break
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
                metadata = {
                    "asset_id": asset["asset_id"], "provider": "cryptocompare", "symbol": symbol,
                    "market": "CCCAGG", "quote": "USD", "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                    "start": batch_start.isoformat(), "end": batch_end.isoformat(), "sha256": sha256(raw_path),
                }
                raw_path.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                time.sleep(0.35)
            asset_rows.extend(response_rows(payload, batch_start, batch_end))
        rows = list({row["date"]: row for row in asset_rows}.values())
        rows.sort(key=lambda row: row["date"])
        all_rows.extend({"asset_id": asset["asset_id"], **row} for row in rows)
        record = coverage_record(asset["asset_id"], [{"date": row["date"], "price_usd": row["close_usd"]} for row in rows], start, end)
        record.update({
            "provider": "cryptocompare", "provider_symbol": symbol,
            "volume_days": sum(isinstance(row.get("volume_quote_usd"), (int, float)) for row in rows),
            "direct_conversion_days": sum(row.get("conversion_type") == "direct" for row in rows),
        })
        coverage.append(record)
    out = repo / "data" / "processed" / "00_foundation"
    daily_path = out / "ohlcv_daily_cryptocompare.csv"
    coverage_path = out / "ohlcv_coverage_cryptocompare.csv"
    fields = ["asset_id", "date", "open_usd", "high_usd", "low_usd", "close_usd", "volume_base", "volume_quote_usd", "conversion_type", "conversion_symbol"]
    all_rows = merge_rows(read_csv(daily_path), all_rows, ("asset_id", "date"))
    coverage = merge_rows(read_csv(coverage_path), coverage, ("asset_id", "start_date", "end_date"))
    write_rows(daily_path, all_rows, fields)
    write_rows(coverage_path, coverage, ["asset_id", "provider", "provider_symbol", "start_date", "end_date", "expected_days", "observed_days", "price_days", "volume_days", "direct_conversion_days", "coverage_ratio", "price_coverage_ratio", "longest_missing_run_days", "status"])
    audit_path = out / "cryptocompare_identifier_audit.csv"
    with audit_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["asset_id", "cryptocompare_symbol", "status"])
        writer.writeheader()
        for asset in assets:
            asset_id = asset["asset_id"]
            writer.writerow({"asset_id": asset_id, "cryptocompare_symbol": resolved.get(asset_id, ""), "status": "resolved" if asset_id in resolved else unresolved[asset_id]})
    return {"requested_assets": len(assets), "resolved_assets": len(resolved), "unresolved": unresolved, "provider_errors": errors, "coverage_records": len(coverage)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect free paginated CryptoCompare CCCAGG daily OHLCV")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--asset-id", action="append", dest="asset_ids")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    print(json.dumps(collect(args.repo.resolve(), args.start, args.end, set(args.asset_ids or []), args.force), indent=2))


if __name__ == "__main__":
    main()
