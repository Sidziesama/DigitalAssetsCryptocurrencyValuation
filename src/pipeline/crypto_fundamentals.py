from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.error
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .historical import request_json, write_rows
from .registry import load_json, sha256, validate_asset_config


BASE_URL = "https://community-api.coinmetrics.io/v4"
METRICS = ("AdrActCnt", "TxCnt", "TxTfrCnt", "CapMrktCurUSD", "SplyCur")
FIELD_MAP = {
    "AdrActCnt": "active_addresses", "TxCnt": "transaction_count",
    "TxTfrCnt": "transfer_count", "CapMrktCurUSD": "market_cap_usd", "SplyCur": "current_supply",
}


def timeseries_url(base_url: str, provider_id: str, start: date, end: date) -> str:
    query = urllib.parse.urlencode({"assets": provider_id, "metrics": ",".join(METRICS), "frequency": "1d", "start_time": start.isoformat(), "end_time": end.isoformat(), "page_size": 10000})
    return f"{base_url.rstrip('/')}/timeseries/asset-metrics?{query}"


def request_available(url: str) -> dict[str, Any]:
    try:
        return request_json(url)
    except urllib.error.HTTPError as error:
        if error.code not in {400, 403}:
            raise
        try: detail = json.loads(error.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError): detail = {"http_status": error.code}
        return {"data": [], "availability_error": detail}


def normalize(asset_id: str, provider_id: str, payload: dict[str, Any], start: date, end: date) -> list[dict[str, Any]]:
    rows = {}
    for item in payload.get("data", []):
        try: day = date.fromisoformat(str(item["time"])[:10])
        except (KeyError, TypeError, ValueError): continue
        if item.get("asset") != provider_id or not start <= day <= end: continue
        row: dict[str, Any] = {"asset_id": asset_id, "date": day.isoformat(), "coinmetrics_asset": provider_id, "provider": "coinmetrics_community"}
        for metric, field in FIELD_MAP.items():
            try: row[field] = float(item[metric]) if item.get(metric) is not None else None
            except (TypeError, ValueError): row[field] = None
        rows[day.isoformat()] = row
    return [rows[key] for key in sorted(rows)]


def coverage(asset_id: str, provider_id: str, rows: list[dict[str, Any]], start: date, end: date) -> dict[str, Any]:
    expected = (end - start).days + 1
    result: dict[str, Any] = {"asset_id":asset_id,"coinmetrics_asset":provider_id,"start_date":start.isoformat(),"end_date":end.isoformat(),"expected_days":expected,"observed_days":len(rows)}
    for field in FIELD_MAP.values():
        count = sum(row.get(field) is not None for row in rows)
        result[f"{field}_days"] = count; result[f"{field}_coverage_ratio"] = count / expected
    critical = (result["active_addresses_coverage_ratio"], result["transaction_count_coverage_ratio"], result["transfer_count_coverage_ratio"], result["market_cap_usd_coverage_ratio"])
    result["monetary_behavior_status"] = "pass" if min(critical) >= .95 else ("unsupported" if not rows else "partial")
    result["free_market_baseline_status"] = "pass" if min(result[f"{field}_coverage_ratio"] for field in ("market_cap_usd","current_supply")) >= .95 else ("unsupported" if not rows else "partial")
    return result


def validate_sources(spec: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, str]]:
    if spec.get("schema_version") != 1 or spec.get("provider") != "coinmetrics_community": raise ValueError("unsupported fundamentals source configuration")
    crypto_ids = {a["asset_id"] for a in validate_asset_config(registry) if a["universe"] == "crypto"}
    rows = spec.get("assets", []); ids = [r.get("asset_id") for r in rows]; providers = [r.get("provider_id") for r in rows]
    if not rows or len(ids) != len(set(ids)) or len(providers) != len(set(providers)): raise ValueError("source mappings must be non-empty and unique")
    if not set(ids) <= crypto_ids or any(not isinstance(p, str) or not p for p in providers): raise ValueError("invalid crypto fundamentals source mapping")
    return rows


def collect(repo: Path, start: date, end: date, force: bool=False, base_url: str=BASE_URL) -> dict[str, Any]:
    mappings = validate_sources(load_json(repo/"config"/"crypto_fundamentals_sources.json"), load_json(repo/"config"/"assets.json"))
    all_rows, audits = [], []; raw_root=repo/"data"/"raw"/"coinmetrics_crypto_fundamentals"
    for mapping in mappings:
        asset_id, provider_id = mapping["asset_id"], mapping["provider_id"]
        raw_path=raw_root/asset_id/f"{start.isoformat()}_{end.isoformat()}.json"
        if raw_path.exists() and not force: payload=load_json(raw_path)
        else:
            payload=request_available(timeseries_url(base_url,provider_id,start,end)); raw_path.parent.mkdir(parents=True,exist_ok=True)
            raw_path.write_text(json.dumps(payload,separators=(",",":"))+"\n",encoding="utf-8")
            raw_path.with_suffix(".metadata.json").write_text(json.dumps({"asset_id":asset_id,"coinmetrics_asset":provider_id,"provider":"coinmetrics_community","metrics":list(METRICS),"frequency":"1d","start":start.isoformat(),"end":end.isoformat(),"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"sha256":sha256(raw_path),"license_note":"Coin Metrics Community Data; verify current terms before redistribution"},indent=2,sort_keys=True)+"\n",encoding="utf-8")
        rows=normalize(asset_id,provider_id,payload,start,end); all_rows.extend(rows); audits.append(coverage(asset_id,provider_id,rows,start,end))
    out=repo/"data"/"processed"/"historical"
    row_fields=["asset_id","date","coinmetrics_asset",*FIELD_MAP.values(),"provider"]
    audit_fields=list(audits[0])
    write_rows(out/"crypto_fundamentals_daily_coinmetrics.csv",all_rows,row_fields); write_rows(out/"crypto_fundamentals_coverage_coinmetrics.csv",audits,audit_fields)
    summary={"assets":len(mappings),"daily_rows":len(all_rows),"monetary_behavior_coverage_pass":sum(a["monetary_behavior_status"]=="pass" for a in audits),"free_market_baseline_coverage_pass":sum(a["free_market_baseline_status"]=="pass" for a in audits),"unavailable_on_free_tier":["adjusted_transfer_value_usd","fees_usd","continuous_issuance_native"],"start_date":start.isoformat(),"end_date":end.isoformat(),"interpretation":"Address, transaction, and transfer counts can support one monetary-use behavioral test; they cannot alone establish VA_MONETARY. Collateral classification requires a separate protocol-level source."}
    empirical=repo/"data"/"processed"/"empirical"; empirical.mkdir(parents=True,exist_ok=True); (empirical/"crypto_fundamentals_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Collect free daily non-stable crypto fundamentals")
    parser.add_argument("--repo",type=Path,default=Path.cwd()); parser.add_argument("--start",type=date.fromisoformat,required=True); parser.add_argument("--end",type=date.fromisoformat,required=True); parser.add_argument("--force",action="store_true")
    args=parser.parse_args()
    if args.end < args.start: parser.error("--end must be on or after --start")
    print(json.dumps(collect(args.repo.resolve(),args.start,args.end,args.force),indent=2))
