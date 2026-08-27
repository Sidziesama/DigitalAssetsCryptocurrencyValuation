from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from .historical import request_json, write_rows
from .registry import load_json, sha256


def validate(spec:dict[str,Any])->None:
    if spec.get("schema_version")!=1 or spec.get("chain")!="ethereum": raise ValueError("unsupported Aave collateral-state configuration")
    if spec.get("method")!="getConfiguration(address)" or spec.get("selector")!="0xc44b11f7": raise ValueError("unexpected Aave Pool configuration selector")
    for field in ("pool_address","rpc_url","block_lookup_base"):
        if not str(spec.get(field,"")).startswith(("0x","https://")): raise ValueError(f"invalid {field}")
    ids=[a.get("asset_id") for a in spec.get("assets",[])]
    if not ids or len(ids)!=len(set(ids)): raise ValueError("Aave reserve assets must be non-empty and unique")
    for asset in spec["assets"]:
        if len(asset.get("reserve_address",""))!=42 or not asset.get("reserve_symbol"): raise ValueError("invalid reserve mapping")


def encode_call(selector:str,address:str)->str:
    return selector+address.lower().removeprefix("0x").rjust(64,"0")


def decode_configuration(value:str)->dict[str,Any]:
    if not isinstance(value,str) or not value.startswith("0x"): raise ValueError("invalid reserve configuration result")
    bitmap=int(value,16)
    return {"ltv_bps":bitmap & 0xFFFF,"liquidation_threshold_bps":(bitmap>>16)&0xFFFF,"liquidation_bonus_bps":(bitmap>>32)&0xFFFF,"decimals":(bitmap>>48)&0xFF,"active":int(bool((bitmap>>56)&1)),"frozen":int(bool((bitmap>>57)&1)),"paused":int(bool((bitmap>>60)&1))}


def post_rpc(url:str,payload:dict[str,Any])->dict[str,Any]:
    request=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={"content-type":"application/json","user-agent":"digital-assets-valuation-research/1.0"},method="POST")
    with urllib.request.urlopen(request,timeout=60) as response: return json.load(response)


def day_timestamp(day:date)->int:
    return int(datetime.combine(day,time(12),timezone.utc).timestamp())


def collect(repo:Path,start:date,end:date,force:bool=False)->dict[str,Any]:
    spec=load_json(repo/"config"/"aave_collateral_state.json"); validate(spec)
    raw_root=repo/"data"/"raw"/"aave_collateral_state"; rows=[]; day=start
    while day<=end:
        raw_path=raw_root/f"{day.isoformat()}.json"
        if raw_path.exists() and not force: payload=load_json(raw_path)
        else:
            block_payload=request_json(f"{spec['block_lookup_base'].rstrip('/')}/{day_timestamp(day)}"); block=int(block_payload["height"]); calls=[]
            for asset in spec["assets"]:
                rpc={"jsonrpc":"2.0","id":asset["asset_id"],"method":"eth_call","params":[{"to":spec["pool_address"],"data":encode_call(spec["selector"],asset["reserve_address"])},hex(block)]}
                response=post_rpc(spec["rpc_url"],rpc); calls.append({"asset_id":asset["asset_id"],"reserve_symbol":asset["reserve_symbol"],"response":response})
            payload={"date":day.isoformat(),"block":block,"block_timestamp":block_payload.get("timestamp"),"calls":calls}; raw_path.parent.mkdir(parents=True,exist_ok=True); raw_path.write_text(json.dumps(payload,separators=(",",":"))+"\n",encoding="utf-8")
            raw_path.with_suffix(".metadata.json").write_text(json.dumps({"provider":"ethereum_json_rpc","rpc_url":spec["rpc_url"],"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"sha256":sha256(raw_path)},indent=2)+"\n",encoding="utf-8")
        for call in payload["calls"]:
            response=call["response"]
            if "result" not in response: continue
            decoded=decode_configuration(response["result"]); rows.append({"asset_id":call["asset_id"],"reserve_symbol":call["reserve_symbol"],"date":payload["date"],"ethereum_block":payload["block"],**decoded,"collateral_enabled":int(decoded["ltv_bps"]>0 and decoded["active"] and not decoded["paused"])})
        day+=timedelta(days=1)
    summaries=[]; expected=(end-start).days+1
    for asset in spec["assets"]:
        selected=[r for r in rows if r["asset_id"]==asset["asset_id"]]
        enabled=sum(r["collateral_enabled"] for r in selected)
        summaries.append({"asset_id":asset["asset_id"],"expected_days":expected,"observed_days":len(selected),"collateral_enabled_days":enabled,"minimum_ltv_bps":min((r["ltv_bps"] for r in selected),default=None),"maximum_ltv_bps":max((r["ltv_bps"] for r in selected),default=None),"eligibility_pass":int(len(selected)==expected and enabled==expected)})
    out=repo/"data"/"processed"/"evidence"; write_rows(out/"aave_collateral_state_daily.csv",rows,list(rows[0]) if rows else ["asset_id"]); write_rows(out/"aave_collateral_state_summary.csv",summaries,list(summaries[0]))
    result={"assets":len(spec["assets"]),"expected_days_per_asset":expected,"daily_state_rows":len(rows),"eligibility_pass_assets":[s["asset_id"] for s in summaries if s["eligibility_pass"]],"start_date":start.isoformat(),"end_date":end.isoformat(),"rule":"Positive LTV, active reserve, and not paused on every daily historical block in the materiality window."}; (out/"aave_collateral_state_summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Verify daily historical Aave collateral eligibility by archive-state reads"); parser.add_argument("--repo",type=Path,default=Path.cwd()); parser.add_argument("--start",type=date.fromisoformat,required=True); parser.add_argument("--end",type=date.fromisoformat,required=True); parser.add_argument("--force",action="store_true"); args=parser.parse_args()
    if args.end<args.start: parser.error("--end must be on or after --start")
    print(json.dumps(collect(args.repo.resolve(),args.start,args.end,args.force),indent=2))
