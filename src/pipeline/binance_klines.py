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


BASE_URL = "https://data-api.binance.vision/api/v3"


def request_json(url: str, retries: int = 4) -> Any:
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "digital-assets-valuation-research/0.1"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code not in {418, 429, 500, 502, 503, 504} or attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def klines_url(base_url: str, symbol: str, start: date, end: date) -> str:
    start_ms = int(datetime.combine(start, datetime.min.time(), timezone.utc).timestamp() * 1000)
    end_ms = int(datetime.combine(end, datetime.max.time(), timezone.utc).timestamp() * 1000)
    query = urllib.parse.urlencode({"symbol": symbol, "interval": "1d", "startTime": start_ms, "endTime": end_ms, "limit": 1000})
    return f"{base_url.rstrip('/')}/klines?{query}"


def normalize(payload: list[list[Any]], start: date, end: date) -> list[dict[str, Any]]:
    rows = []
    for item in payload:
        if not isinstance(item, list) or len(item) < 11:
            continue
        day = datetime.fromtimestamp(item[0] / 1000, timezone.utc).date()
        if start <= day <= end:
            rows.append({
                "date": day.isoformat(), "open_quote": float(item[1]), "high_quote": float(item[2]),
                "low_quote": float(item[3]), "close_quote": float(item[4]), "volume_base": float(item[5]),
                "volume_quote": float(item[7]), "trade_count": int(item[8]),
                "taker_buy_base": float(item[9]), "taker_buy_quote": float(item[10]),
            })
    return rows


def select_pairs(assets: list[dict[str, Any]], exchange_info: dict[str, Any]) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    symbols = exchange_info.get("symbols", [])
    resolved: dict[str, dict[str, str]] = {}
    unresolved: dict[str, str] = {}
    quote_priority = {"USDT": 0, "USDC": 1, "FDUSD": 2}
    for asset in assets:
        candidates = [row for row in symbols if row.get("baseAsset") == asset["symbol"] and row.get("quoteAsset") in quote_priority]
        candidates.sort(key=lambda row: quote_priority[row["quoteAsset"]])
        if candidates:
            resolved[asset["asset_id"]] = {"symbol": candidates[0]["symbol"], "quote_asset": candidates[0]["quoteAsset"]}
        else:
            unresolved[asset["asset_id"]] = "no_active_supported_quote_pair"
    return resolved, unresolved


def collect(repo: Path, start: date, end: date, force: bool = False, base_url: str = BASE_URL) -> dict[str, Any]:
    assets = [asset for asset in validate_asset_config(load_json(repo / "config" / "assets.json")) if asset["universe"] == "crypto"]
    raw_root = repo / "data" / "raw" / "binance_spot"
    info_path = raw_root / "exchange_info.json"
    if info_path.exists() and not force:
        info = load_json(info_path)
    else:
        info = request_json(f"{base_url.rstrip('/')}/exchangeInfo")
        raw_root.mkdir(parents=True, exist_ok=True)
        info_path.write_text(json.dumps(info, separators=(",", ":")) + "\n", encoding="utf-8")
    resolved, unresolved = select_pairs(assets, info)
    all_rows: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for asset in assets:
        pair = resolved.get(asset["asset_id"])
        if not pair:
            continue
        cursor = start
        rows: list[dict[str, Any]] = []
        while cursor <= end:
            batch_end = min(end, cursor + timedelta(days=999))
            raw_path = raw_root / asset["asset_id"] / f"{cursor.isoformat()}_{batch_end.isoformat()}.json"
            if raw_path.exists() and not force:
                payload = load_json(raw_path)
            else:
                payload = request_json(klines_url(base_url, pair["symbol"], cursor, batch_end))
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
                metadata = {"asset_id": asset["asset_id"], **pair, "provider": "binance_spot", "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "start": cursor.isoformat(), "end": batch_end.isoformat(), "sha256": sha256(raw_path)}
                raw_path.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                time.sleep(0.08)
            rows.extend(normalize(payload, cursor, batch_end))
            cursor = batch_end + timedelta(days=1)
        rows = list({row["date"]: row for row in rows}.values())
        rows.sort(key=lambda row: row["date"])
        all_rows.extend({"asset_id": asset["asset_id"], "pair": pair["symbol"], "quote_asset": pair["quote_asset"], **row} for row in rows)
        record = coverage_record(asset["asset_id"], [{"date": row["date"], "price_usd": row["close_quote"]} for row in rows], start, end)
        record.update({"provider": "binance_spot", "pair": pair["symbol"], "quote_asset": pair["quote_asset"], "volume_days": len(rows)})
        coverage.append(record)
    out = repo / "data" / "processed" / "historical"
    daily = out / "ohlcv_daily_binance_spot.csv"
    cover = out / "ohlcv_coverage_binance_spot.csv"
    fields = ["asset_id", "date", "pair", "quote_asset", "open_quote", "high_quote", "low_quote", "close_quote", "volume_base", "volume_quote", "trade_count", "taker_buy_base", "taker_buy_quote"]
    all_rows = merge_rows(read_csv(daily), all_rows, ("asset_id", "date"))
    coverage = merge_rows(read_csv(cover), coverage, ("asset_id", "start_date", "end_date"))
    write_rows(daily, all_rows, fields)
    write_rows(cover, coverage, ["asset_id", "provider", "pair", "quote_asset", "start_date", "end_date", "expected_days", "observed_days", "price_days", "volume_days", "coverage_ratio", "price_coverage_ratio", "longest_missing_run_days", "status"])
    audit = out / "binance_pair_audit.csv"
    with audit.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["asset_id", "pair", "quote_asset", "status"]); writer.writeheader()
        for asset in assets:
            pair = resolved.get(asset["asset_id"], {})
            writer.writerow({"asset_id": asset["asset_id"], "pair": pair.get("symbol", ""), "quote_asset": pair.get("quote_asset", ""), "status": "resolved" if pair else unresolved[asset["asset_id"]]})
    return {"requested_assets": len(assets), "resolved_pairs": len(resolved), "unresolved": unresolved, "coverage_records": len(coverage), "daily_rows": len(all_rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect keyless Binance Spot daily venue OHLCV")
    parser.add_argument("--repo", type=Path, default=Path.cwd()); parser.add_argument("--start", type=date.fromisoformat, required=True); parser.add_argument("--end", type=date.fromisoformat, required=True); parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.end < args.start: parser.error("--end must be on or after --start")
    print(json.dumps(collect(args.repo.resolve(), args.start, args.end, args.force), indent=2))


if __name__ == "__main__": main()
