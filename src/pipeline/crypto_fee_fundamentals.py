from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from src.pipeline.historical import request_json, write_rows
from src.pipeline.registry import load_json, sha256


BASE_URL="https://api.llama.fi"


def validate(spec:dict[str,Any])->None:
    if spec.get("schema_version")!=1 or spec.get("provider")!="defillama_free_fees_api": raise ValueError("unsupported fee-source config")
    assets=spec.get("assets",[]); ids=[row.get("asset_id") for row in assets]
    if len(assets)!=6 or len(ids)!=len(set(ids)): raise ValueError("fee source requires six unique pilot assets")
    if any(row.get("scope") not in {"chain","application_protocol"} or not row.get("endpoint") or not row.get("economic_system") for row in assets): raise ValueError("invalid fee source scope")
    if spec.get("metrics")!={"dailyFees":"fees_usd","dailyRevenue":"protocol_revenue_usd","dailyHoldersRevenue":"holders_revenue_usd"}: raise ValueError("fee metric mapping drift")
    if not spec.get("interpretation"): raise ValueError("fee scope interpretation required")


def build_url(endpoint:str,metric:str,base_url:str=BASE_URL)->str:
    query=urllib.parse.urlencode({"dataType":metric,"excludeTotalDataChartBreakdown":"true"})
    return f"{base_url.rstrip('/')}/{endpoint}?{query}"


def normalize(asset:dict[str,Any],metric_name:str,field:str,payload:dict[str,Any],start:date,end:date)->list[dict[str,Any]]:
    rows=[]
    for point in payload.get("totalDataChart") or []:
        try: day=datetime.fromtimestamp(int(point[0]),timezone.utc).date(); value=float(point[1])
        except (TypeError,ValueError,IndexError,OverflowError): continue
        if start<=day<=end and value>=0:
            rows.append({"asset_id":asset["asset_id"],"date":day.isoformat(),"scope":asset["scope"],"economic_system":asset["economic_system"],"provider_metric":metric_name,"field":field,"value_usd":value})
    return rows


def collect(repo:Path,start:date,end:date,force:bool=False,base_url:str=BASE_URL)->dict[str,Any]:
    spec=load_json(repo/"config/crypto_fee_sources.json"); validate(spec)
    raw_root=repo/"data/raw/defillama_crypto_fees"; long=[]
    for asset in spec["assets"]:
        for metric,field in spec["metrics"].items():
            raw=raw_root/asset["asset_id"]/f"{metric}_{start}_{end}.json"
            if raw.exists() and not force: payload=load_json(raw)
            else:
                payload=request_json(build_url(asset["endpoint"],metric,base_url)); raw.parent.mkdir(parents=True,exist_ok=True); raw.write_text(json.dumps(payload,separators=(",",":"))+"\n",encoding="utf-8")
                raw.with_suffix(".metadata.json").write_text(json.dumps({"asset_id":asset["asset_id"],"scope":asset["scope"],"economic_system":asset["economic_system"],"provider_metric":metric,"source_url":build_url(asset["endpoint"],metric,base_url),"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"sha256":sha256(raw)},indent=2)+"\n",encoding="utf-8")
            long.extend(normalize(asset,metric,field,payload,start,end))
    keys={field for field in spec["metrics"].values()}; index={}
    for row in long:
        key=(row["asset_id"],row["date"]); item=index.setdefault(key,{"asset_id":row["asset_id"],"date":row["date"],"scope":row["scope"],"economic_system":row["economic_system"]})
        item[row["field"]]=row["value_usd"]
    daily=[]
    for item in index.values():
        for field in keys: item.setdefault(field,None)
        daily.append(item)
    daily.sort(key=lambda row:(row["asset_id"],row["date"])); expected=(end-start).days+1; coverage=[]
    for asset in spec["assets"]:
        selected=[row for row in daily if row["asset_id"]==asset["asset_id"]]
        coverage.append({"asset_id":asset["asset_id"],"scope":asset["scope"],"economic_system":asset["economic_system"],"expected_days":expected,"observed_days":len(selected),**{f"{field}_days":sum(row[field] is not None for row in selected) for field in keys}})
    out=repo/"data/processed/empirical"; write_rows(out/"crypto_fee_fundamentals_daily.csv",daily,["asset_id","date","scope","economic_system","fees_usd","protocol_revenue_usd","holders_revenue_usd"]); write_rows(out/"crypto_fee_fundamentals_coverage.csv",coverage,list(coverage[0]))
    result={"status":"free_fee_layer_ready_scope_comparability_review_pending","assets":len(spec["assets"]),"daily_rows":len(daily),"start_date":start.isoformat(),"end_date":end.isoformat(),"complete_fee_assets":sum(row["fees_usd_days"]==expected for row in coverage),"complete_revenue_assets":sum(row["protocol_revenue_usd_days"]==expected for row in coverage),"complete_holders_revenue_assets":sum(row["holders_revenue_usd_days"]==expected for row in coverage),"interpretation":spec["interpretation"]}
    (out/"crypto_fee_fundamentals_summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Collect free DeFiLlama crypto fee and revenue histories with explicit scope")
    parser.add_argument("--repo",type=Path,default=Path.cwd()); parser.add_argument("--start",type=date.fromisoformat,required=True); parser.add_argument("--end",type=date.fromisoformat,required=True); parser.add_argument("--force",action="store_true"); args=parser.parse_args()
    if args.end<args.start: parser.error("--end must be on or after --start")
    print(json.dumps(collect(args.repo.resolve(),args.start,args.end,args.force),indent=2))
