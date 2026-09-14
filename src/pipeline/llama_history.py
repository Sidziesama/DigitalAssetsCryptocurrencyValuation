from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.error
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .historical import chunk_ranges, merge_rows, read_csv, request_json, write_rows
from .registry import load_json, sha256, validate_asset_config


def batches(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    if size < 1:
        raise ValueError("batch size must be positive")
    return [items[i:i+size] for i in range(0,len(items),size)]


def chart_url(base_url: str, assets: list[dict[str, Any]], start: date, end: date) -> str:
    if len(assets) != 1:
        raise ValueError("DeFiLlama chart endpoint accepts one coin per request")
    coins=",".join(f"coingecko:{asset['coingecko_id']}" for asset in assets)
    start_ts=int(datetime.combine(start,datetime.min.time(),timezone.utc).timestamp())
    span=(end-start).days+1
    query=urllib.parse.urlencode({"start":start_ts,"span":span,"period":"1d"})
    return f"{base_url.rstrip('/')}/chart/{coins}?{query}"


def nearest_utc_day(timestamp: int | float) -> str:
    """Assign near-midnight daily observations to the nearest UTC calendar day."""
    rounded_seconds=round(timestamp/86400)*86400
    return datetime.fromtimestamp(rounded_seconds,timezone.utc).date().isoformat()


def normalize(payload: dict[str, Any], assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    coins=payload.get("coins",{})
    output=[]
    for asset in assets:
        key=f"coingecko:{asset['coingecko_id']}"
        prices=(coins.get(key) or {}).get("prices",[])
        daily={}
        for item in prices:
            if not isinstance(item,dict) or not isinstance(item.get("timestamp"),(int,float)) or not isinstance(item.get("price"),(int,float)):
                continue
            day=nearest_utc_day(item["timestamp"])
            daily[day]=item["price"]
        output.extend({"asset_id":asset["asset_id"],"date":day,"price_usd":daily[day],"provider":"defillama"} for day in sorted(daily))
    return output


def coverage(asset_id: str, rows: list[dict[str, Any]], start: date, end: date) -> dict[str, Any]:
    dates=sorted({date.fromisoformat(row["date"]) for row in rows if start <= date.fromisoformat(row["date"]) <= end})
    full_expected=(end-start).days+1
    if dates:
        active_expected=(end-dates[0]).days+1
        active_ratio=len(dates)/active_expected
        trailing_gap=(end-dates[-1]).days
    else:
        active_expected=0; active_ratio=0; trailing_gap=full_expected
    return {
        "asset_id":asset_id,"provider":"defillama","start_date":start.isoformat(),"end_date":end.isoformat(),
        "first_observed_date":dates[0].isoformat() if dates else None,
        "last_observed_date":dates[-1].isoformat() if dates else None,
        "full_window_expected_days":full_expected,"observed_days":len(dates),
        "full_window_coverage_ratio":len(dates)/full_expected,
        "active_window_expected_days":active_expected,"active_window_coverage_ratio":active_ratio,
        "trailing_gap_days":trailing_gap,
        "status":"pass" if active_ratio >= .95 and trailing_gap <= 2 else "review",
    }


def collect(repo: Path,start: date,end: date,asset_ids: set[str] | None=None,chunk_days: int=365,batch_size: int=1,force: bool=False) -> list[dict[str, Any]]:
    assets=validate_asset_config(load_json(repo/"config"/"assets.json"))
    if asset_ids:
        unknown=asset_ids-{asset["asset_id"] for asset in assets}
        if unknown: raise ValueError(f"unknown asset ids: {sorted(unknown)}")
        assets=[asset for asset in assets if asset["asset_id"] in asset_ids]
    base_url="https://coins.llama.fi"
    if batch_size != 1:
        raise ValueError("DeFiLlama chart endpoint requires --batch-size 1")
    all_new=[]
    for chunk_start,chunk_end in chunk_ranges(start,end,chunk_days):
        for batch in batches(assets,batch_size):
            signature=",".join(asset["asset_id"] for asset in batch)
            batch_hash=hashlib.sha256(signature.encode()).hexdigest()[:12]
            raw_dir=repo/"data"/"raw"/"defillama_prices"/f"{chunk_start.isoformat()}_{chunk_end.isoformat()}"
            raw_path=raw_dir/f"batch_{batch_hash}.json"; meta_path=raw_dir/f"batch_{batch_hash}.metadata.json"
            if raw_path.exists() and not force:
                payload=load_json(raw_path)
            else:
                url=chart_url(base_url,batch,chunk_start,chunk_end)
                raw_dir.mkdir(parents=True,exist_ok=True)
                try:
                    payload=request_json(url)
                except urllib.error.HTTPError as exc:
                    error_meta={"provider":"defillama","asset_ids":[a["asset_id"] for a in batch],"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"start":chunk_start.isoformat(),"end":chunk_end.isoformat(),"http_status":exc.code,"error":str(exc)}
                    meta_path.write_text(json.dumps(error_meta,indent=2,sort_keys=True)+"\n",encoding="utf-8")
                    continue
                raw_path.write_text(json.dumps(payload,separators=(",",":"))+"\n",encoding="utf-8")
                meta={"provider":"defillama","asset_ids":[a["asset_id"] for a in batch],"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"start":chunk_start.isoformat(),"end":chunk_end.isoformat(),"sha256":sha256(raw_path),"http_status":200}
                meta_path.write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n",encoding="utf-8")
                time.sleep(.15)
            all_new.extend(normalize(payload,batch))
    out=repo/"data"/"processed"/"00_foundation"; daily_path=out/"price_daily_defillama.csv"
    requested_ids={asset["asset_id"] for asset in assets}
    existing=[]
    for row in read_csv(daily_path):
        row_date=date.fromisoformat(row["date"])
        if row["asset_id"] in requested_ids and start <= row_date <= end and row.get("provider")=="defillama":
            continue
        existing.append(row)
    all_rows=merge_rows(existing,all_new,("asset_id","date","provider"))
    write_rows(daily_path,all_rows,["asset_id","date","price_usd","provider"])
    requested=requested_ids; grouped={asset_id:[] for asset_id in requested}
    for row in all_rows:
        if row["asset_id"] in grouped: grouped[row["asset_id"]].append(row)
    results=[coverage(asset["asset_id"],grouped[asset["asset_id"]],start,end) for asset in assets]
    coverage_path=out/"price_coverage_defillama.csv"
    results=merge_rows(read_csv(coverage_path),results,("asset_id","provider","start_date","end_date"))
    fields=["asset_id","provider","start_date","end_date","first_observed_date","last_observed_date","full_window_expected_days","observed_days","full_window_coverage_ratio","active_window_expected_days","active_window_coverage_ratio","trailing_gap_days","status"]
    write_rows(coverage_path,results,fields)
    return [row for row in results if row["start_date"]==start.isoformat() and row["end_date"]==end.isoformat()]


def render_summary(rows: list[dict[str, Any]],start: date,end: date) -> str:
    passed=[r for r in rows if r["status"]=="pass"]; review=[r for r in rows if r["status"]=="review"]
    review_lines="\n".join(f"- `{r['asset_id']}`: first={r.get('first_observed_date') or 'none'}, last={r.get('last_observed_date') or 'none'}, active coverage={float(r['active_window_coverage_ratio']):.2%}" for r in review) or "- None"
    return f"""# Historical Price Coverage — {start.isoformat()} to {end.isoformat()}

## Result

- Provider: DeFiLlama coin-price history using CoinGecko namespace identifiers.
- Assets audited: {len(rows)}.
- Pass: {len(passed)}.
- Review: {len(review)}.
- Pass rule: at least 95% daily coverage from first observation through the requested end date, with no more than a two-day trailing gap.

The active-window metric avoids penalizing assets for dates before their first observed history. First observation is a data-availability boundary, not a verified launch date.

## Review queue

{review_lines}

## Scope limitation

This fallback provides price history only. Market capitalization, circulating supply, and volume require separately licensed or source-specific histories and must not be inferred from this table.
"""


def main() -> None:
    p=argparse.ArgumentParser(description="Collect batched DeFiLlama daily price history and audit coverage")
    p.add_argument("--repo",type=Path,default=Path.cwd()); p.add_argument("--start",type=date.fromisoformat,required=True); p.add_argument("--end",type=date.fromisoformat,required=True)
    p.add_argument("--asset-id",action="append",dest="asset_ids"); p.add_argument("--chunk-days",type=int,default=365); p.add_argument("--batch-size",type=int,default=1); p.add_argument("--force",action="store_true")
    args=p.parse_args()
    if args.end < args.start:p.error("--end must be on or after --start")
    rows=collect(args.repo.resolve(),args.start,args.end,set(args.asset_ids or []),args.chunk_days,args.batch_size,args.force)
    finding=args.repo.resolve()/"research"/"findings"/f"{args.end.isoformat()}-historical-price-coverage.md"
    finding.parent.mkdir(parents=True,exist_ok=True); finding.write_text(render_summary(rows,args.start,args.end),encoding="utf-8")
    print(json.dumps(rows,indent=2))


if __name__=="__main__":main()
