from __future__ import annotations

import argparse
import json
import time
import urllib.error
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .historical import merge_rows, read_csv, request_json, write_rows
from .registry import load_json, sha256, validate_asset_config


def normalize(asset_id: str,payload: dict[str, Any],start: date,end: date) -> list[dict[str, Any]]:
    output={}
    for item in payload.get("tokens",[]):
        timestamp=item.get("date"); value=(item.get("circulating") or {}).get("peggedUSD")
        if not isinstance(timestamp,(int,float)) or not isinstance(value,(int,float)):continue
        day=datetime.fromtimestamp(timestamp,timezone.utc).date()
        if start <= day <= end:
            output[day.isoformat()]={"asset_id":asset_id,"date":day.isoformat(),"circulating_peg_usd":value,"provider":"defillama"}
    return [output[key] for key in sorted(output)]


def coverage(asset: dict[str, Any],rows: list[dict[str, Any]],start: date,end: date) -> dict[str, Any]:
    dates=sorted(date.fromisoformat(row["date"]) for row in rows)
    if dates:
        expected=(end-dates[0]).days+1; ratio=len(dates)/expected; trailing=(end-dates[-1]).days
    else:
        expected=0;ratio=0;trailing=(end-start).days+1
    supported=bool(asset.get("defillama_id"))
    return {"asset_id":asset["asset_id"],"provider":"defillama","start_date":start.isoformat(),"end_date":end.isoformat(),"supported":int(supported),"first_observed_date":dates[0].isoformat() if dates else None,"last_observed_date":dates[-1].isoformat() if dates else None,"active_window_expected_days":expected,"observed_days":len(dates),"active_window_coverage_ratio":ratio,"trailing_gap_days":trailing,"status":"pass" if supported and ratio>=.95 and trailing<=2 else ("unsupported" if not supported else "review")}


def collect(repo: Path,start: date,end: date,force: bool=False) -> list[dict[str, Any]]:
    assets=[asset for asset in validate_asset_config(load_json(repo/"config"/"assets.json")) if asset["universe"]=="stablecoin"]
    new_rows=[]
    for asset in assets:
        provider_id=asset.get("defillama_id")
        if not provider_id:continue
        raw_dir=repo/"data"/"raw"/"defillama_stablecoin_history";raw_path=raw_dir/f"{asset['asset_id']}.json";meta_path=raw_dir/f"{asset['asset_id']}.metadata.json"
        if raw_path.exists() and not force:payload=load_json(raw_path)
        else:
            raw_dir.mkdir(parents=True,exist_ok=True)
            try:payload=request_json(f"https://stablecoins.llama.fi/stablecoin/{provider_id}")
            except urllib.error.HTTPError as exc:
                meta_path.write_text(json.dumps({"asset_id":asset["asset_id"],"provider_id":provider_id,"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"http_status":exc.code,"error":str(exc)},indent=2)+"\n",encoding="utf-8");continue
            raw_path.write_text(json.dumps(payload,separators=(",",":"))+"\n",encoding="utf-8")
            meta_path.write_text(json.dumps({"asset_id":asset["asset_id"],"provider_id":provider_id,"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"http_status":200,"sha256":sha256(raw_path)},indent=2,sort_keys=True)+"\n",encoding="utf-8");time.sleep(.3)
        new_rows.extend(normalize(asset["asset_id"],payload,start,end))
    out=repo/"data"/"processed"/"historical";daily_path=out/"stablecoin_supply_daily.csv"
    ids={a["asset_id"] for a in assets};existing=[]
    for row in read_csv(daily_path):
        d=date.fromisoformat(row["date"])
        if row["asset_id"] in ids and start<=d<=end:continue
        existing.append(row)
    all_rows=merge_rows(existing,new_rows,("asset_id","date","provider"));write_rows(daily_path,all_rows,["asset_id","date","circulating_peg_usd","provider"])
    grouped={a["asset_id"]:[] for a in assets}
    for row in all_rows:
        if row["asset_id"] in grouped and start<=date.fromisoformat(row["date"])<=end:grouped[row["asset_id"]].append(row)
    results=[coverage(asset,grouped[asset["asset_id"]],start,end) for asset in assets]
    cov_path=out/"stablecoin_supply_coverage.csv";fields=["asset_id","provider","start_date","end_date","supported","first_observed_date","last_observed_date","active_window_expected_days","observed_days","active_window_coverage_ratio","trailing_gap_days","status"]
    write_rows(cov_path,results,fields);return results


def findings(rows: list[dict[str, Any]],start: date,end: date)->str:
    passed=[r for r in rows if r["status"]=="pass"];review=[r for r in rows if r["status"]!="pass"]
    queue="\n".join(f"- `{r['asset_id']}` — {r['status']}; active coverage {float(r['active_window_coverage_ratio']):.2%}" for r in review) or "- None"
    return f"""# Stablecoin Supply Coverage — {start} to {end}

## Result

- Stable-value assets audited: {len(rows)}.
- Pass: {len(passed)}.
- Review or unsupported: {len(review)}.
- Metric: DeFiLlama `circulating.peggedUSD`, retained explicitly as a USD-valued circulation measure rather than token units.

## Review queue

{queue}

PAXG is a commodity-referenced token and is not covered by the USD-stablecoin history endpoint. Its supply history requires an issuer or commodity-token source and is not imputed.
"""


def main()->None:
    p=argparse.ArgumentParser(description="Collect and audit DeFiLlama stablecoin circulation history");p.add_argument("--repo",type=Path,default=Path.cwd());p.add_argument("--start",type=date.fromisoformat,required=True);p.add_argument("--end",type=date.fromisoformat,required=True);p.add_argument("--force",action="store_true");a=p.parse_args()
    rows=collect(a.repo.resolve(),a.start,a.end,a.force);path=a.repo.resolve()/"research"/"findings"/f"{a.end}-stablecoin-supply-coverage.md";path.write_text(findings(rows,a.start,a.end),encoding="utf-8");print(json.dumps(rows,indent=2))


if __name__=="__main__":main()
