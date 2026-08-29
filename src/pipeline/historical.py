from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .registry import load_env_file, load_json, sha256, validate_asset_config


def unix_seconds(value: date, end_of_day: bool = False) -> int:
    clock = datetime.max.time().replace(microsecond=0) if end_of_day else datetime.min.time()
    return int(datetime.combine(value, clock, timezone.utc).timestamp())


def request_json(url: str, api_key: str | None = None, retries: int = 4) -> Any:
    headers = {"Accept": "application/json", "User-Agent": "digital-assets-valuation-research/0.1"}
    if api_key:
        headers["x-cg-demo-api-key"] = api_key
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def market_chart_url(base_url: str, coin_id: str, start: date, end: date) -> str:
    query = urllib.parse.urlencode({
        "vs_currency": "usd", "from": unix_seconds(start),
        "to": unix_seconds(end, end_of_day=True), "precision": "full"
    })
    return f"{base_url.rstrip('/')}/coins/{urllib.parse.quote(coin_id)}/market_chart/range?{query}"


def normalize_daily(payload: dict[str, Any]) -> list[dict[str, Any]]:
    series = {name: values for name, values in payload.items() if name in {"prices", "market_caps", "total_volumes"}}
    by_date: dict[str, dict[str, Any]] = defaultdict(dict)
    field_map = {"prices":"price_usd", "market_caps":"market_cap_usd", "total_volumes":"volume_24h_usd"}
    for source_field, values in series.items():
        if not isinstance(values, list):
            continue
        for item in values:
            if not isinstance(item, list) or len(item) < 2:
                continue
            day = datetime.fromtimestamp(item[0] / 1000, timezone.utc).date().isoformat()
            by_date[day][field_map[source_field]] = item[1]
    return [{"date": day, **by_date[day]} for day in sorted(by_date)]


def longest_missing_run(observed: set[date], start: date, end: date) -> int:
    longest = current = 0
    day = start
    while day <= end:
        if day in observed:
            current = 0
        else:
            current += 1
            longest = max(longest, current)
        day += timedelta(days=1)
    return longest


def chunk_ranges(start: date, end: date, chunk_days: int) -> list[tuple[date, date]]:
    if chunk_days < 1:
        raise ValueError("chunk_days must be positive")
    chunks=[]
    cursor=start
    while cursor <= end:
        chunk_end=min(end,cursor+timedelta(days=chunk_days-1))
        chunks.append((cursor,chunk_end))
        cursor=chunk_end+timedelta(days=1)
    return chunks


def coverage_record(asset_id: str, rows: list[dict[str, Any]], start: date, end: date) -> dict[str, Any]:
    observed = {date.fromisoformat(row["date"]) for row in rows if start <= date.fromisoformat(row["date"]) <= end}
    expected = (end - start).days + 1
    price_days = sum(1 for row in rows if start <= date.fromisoformat(row["date"]) <= end and isinstance(row.get("price_usd"), (int, float)))
    return {
        "asset_id": asset_id, "start_date": start.isoformat(), "end_date": end.isoformat(),
        "expected_days": expected, "observed_days": len(observed), "price_days": price_days,
        "coverage_ratio": len(observed) / expected if expected else 0,
        "price_coverage_ratio": price_days / expected if expected else 0,
        "longest_missing_run_days": longest_missing_run(observed, start, end),
        "status": "pass" if price_days / expected >= 0.95 else "review",
    }


def write_rows(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="",encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def merge_rows(existing: list[dict[str, Any]], new: list[dict[str, Any]], key_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    merged={tuple(str(row.get(field,"")) for field in key_fields):row for row in existing}
    for row in new:
        merged[tuple(str(row.get(field,"")) for field in key_fields)]=row
    return [merged[key] for key in sorted(merged)]


def collect(repo: Path, start: date, end: date, asset_ids: set[str] | None, force: bool = False, chunk_days: int = 365) -> list[dict[str, Any]]:
    load_env_file(repo / ".env")
    config = load_json(repo / "config" / "assets.json")
    assets = validate_asset_config(config)
    if asset_ids:
        unknown = asset_ids - {asset["asset_id"] for asset in assets}
        if unknown:
            raise ValueError(f"unknown asset ids: {sorted(unknown)}")
        assets = [asset for asset in assets if asset["asset_id"] in asset_ids]
    base_url = os.getenv("COINGECKO_API_BASE", "https://api.coingecko.com/api/v3")
    api_key = os.getenv("COINGECKO_API_KEY")
    coverage=[]
    all_rows=[]
    for asset in assets:
        raw_dir=repo/"data"/"raw"/"coingecko_market_chart"/asset["asset_id"]
        asset_rows=[]
        for chunk_start,chunk_end in chunk_ranges(start,end,chunk_days):
            raw_path=raw_dir/f"{chunk_start.isoformat()}_{chunk_end.isoformat()}.json"
            meta_path=raw_dir/f"{chunk_start.isoformat()}_{chunk_end.isoformat()}.metadata.json"
            if raw_path.exists() and not force:
                payload=load_json(raw_path)
            else:
                url=market_chart_url(base_url,asset["coingecko_id"],chunk_start,chunk_end)
                payload=request_json(url,api_key=api_key)
                raw_dir.mkdir(parents=True,exist_ok=True)
                raw_path.write_text(json.dumps(payload,separators=(",",":"))+"\n",encoding="utf-8")
                meta={"asset_id":asset["asset_id"],"provider_id":asset["coingecko_id"],"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"start":chunk_start.isoformat(),"end":chunk_end.isoformat(),"sha256":sha256(raw_path)}
                meta_path.write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n",encoding="utf-8")
                time.sleep(1.2)
            asset_rows.extend(normalize_daily(payload))
        rows=list({row["date"]:row for row in asset_rows}.values())
        rows.sort(key=lambda row:row["date"])
        for row in rows: all_rows.append({"asset_id":asset["asset_id"],**row})
        coverage.append(coverage_record(asset["asset_id"],rows,start,end))
    out=repo/"data"/"processed"/"historical"
    daily_path=out/"market_daily.csv"; coverage_path=out/"market_coverage.csv"
    all_rows=merge_rows(read_csv(daily_path),all_rows,("asset_id","date"))
    coverage=merge_rows(read_csv(coverage_path),coverage,("asset_id","start_date","end_date"))
    write_rows(daily_path,all_rows,["asset_id","date","price_usd","market_cap_usd","volume_24h_usd"])
    write_rows(coverage_path,coverage,["asset_id","start_date","end_date","expected_days","observed_days","price_days","coverage_ratio","price_coverage_ratio","longest_missing_run_days","status"])
    return coverage


def main() -> None:
    parser=argparse.ArgumentParser(description="Collect cached CoinGecko history and create a missingness audit")
    parser.add_argument("--repo",type=Path,default=Path.cwd())
    parser.add_argument("--start",type=date.fromisoformat,required=True)
    parser.add_argument("--end",type=date.fromisoformat,required=True)
    parser.add_argument("--asset-id",action="append",dest="asset_ids")
    parser.add_argument("--force",action="store_true")
    parser.add_argument("--chunk-days",type=int,default=365)
    args=parser.parse_args()
    if args.end < args.start: parser.error("--end must be on or after --start")
    print(json.dumps(collect(args.repo.resolve(),args.start,args.end,set(args.asset_ids or []),args.force,args.chunk_days),indent=2))


if __name__ == "__main__": main()
