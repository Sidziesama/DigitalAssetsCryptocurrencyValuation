from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .historical import request_json, write_rows
from .registry import load_json, sha256, validate_asset_config


BASE_URL="https://api.llama.fi/protocol"


def validate_config(spec: dict[str,Any], registry: dict[str,Any])->None:
    if spec.get("schema_version")!=1 or spec.get("provider")!="defillama": raise ValueError("unsupported collateral source configuration")
    crypto={a["asset_id"] for a in validate_asset_config(registry) if a["universe"]=="crypto"}
    protocols=spec.get("protocols",[]); assets=spec.get("assets",[])
    if not protocols or len({p.get("slug") for p in protocols})!=len(protocols): raise ValueError("protocol slugs must be non-empty and unique")
    if any(p.get("category")!="lending" for p in protocols): raise ValueError("collateral screen is restricted to lending protocols")
    ids=[a.get("asset_id") for a in assets]
    if not assets or len(ids)!=len(set(ids)) or not set(ids)<=crypto: raise ValueError("invalid collateral asset mappings")
    for asset in assets:
        aliases=asset.get("token_aliases",[])
        if not aliases or len(aliases)!=len(set(aliases)) or any(not isinstance(x,str) or not x for x in aliases): raise ValueError("token aliases must be non-empty and unique")
    rule=spec.get("primary_rule",{})
    if rule.get("absolute_usd",0)<=0 or not 0<rule.get("market_cap_ratio",0)<1 or rule.get("minimum_consecutive_days",0)<2: raise ValueError("invalid collateral materiality rule")


def normalize_protocol(slug: str,payload: dict[str,Any],alias_index: dict[str,str],start: date,end: date)->list[dict[str,Any]]:
    rows=[]
    for point in payload.get("tokensInUsd") or []:
        try: day=datetime.fromtimestamp(int(point["date"]),timezone.utc).date()
        except (KeyError,TypeError,ValueError,OverflowError): continue
        if not start<=day<=end or not isinstance(point.get("tokens"),dict): continue
        for token,value in point["tokens"].items():
            asset_id=alias_index.get(token)
            if not asset_id: continue
            try: usd=float(value)
            except (TypeError,ValueError): continue
            if usd<=0: continue
            rows.append({"asset_id":asset_id,"date":day.isoformat(),"protocol_slug":slug,"token_alias":token,"supplied_balance_usd":usd,"provider":"defillama"})
    return rows


def market_caps(paths: list[Path])->dict[tuple[str,str],float]:
    result={}
    for path in paths:
        if not path.exists(): continue
        with path.open(newline="",encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                try:
                    key=(row["asset_id"],row["date"])
                    if key not in result and float(row["market_cap_usd"])>0: result[key]=float(row["market_cap_usd"])
                except (KeyError,TypeError,ValueError): pass
    return result


def longest_consecutive(days: list[date])->int:
    best=current=0; previous=None
    for day in sorted(set(days)):
        current=current+1 if previous and (day-previous).days==1 else 1
        best=max(best,current); previous=day
    return best


def aggregate(rows:list[dict[str,Any]],assets:list[dict[str,Any]],caps:dict[tuple[str,str],float],rule:dict[str,Any],screen_complete:bool=True)->tuple[list[dict[str,Any]],list[dict[str,Any]]]:
    totals=defaultdict(float)
    for row in rows: totals[(row["asset_id"],row["date"])]+=row["supplied_balance_usd"]
    daily=[]
    for (asset_id,day),balance in sorted(totals.items()):
        cap=caps.get((asset_id,day)); ratio=balance/cap if cap else None
        material=balance>=rule["absolute_usd"] or (ratio is not None and ratio>=rule["market_cap_ratio"])
        daily.append({"asset_id":asset_id,"date":day,"supplied_balance_usd":balance,"market_cap_usd":cap,"supplied_to_market_cap":ratio,"material_proxy":int(material)})
    summaries=[]
    for asset in assets:
        selected=[row for row in daily if row["asset_id"]==asset["asset_id"]]
        material_days=[date.fromisoformat(row["date"]) for row in selected if row["material_proxy"]]
        market_cap_days=sum(row["market_cap_usd"] is not None for row in selected)
        streak=longest_consecutive(material_days); passed=streak>=rule["minimum_consecutive_days"]
        if passed: status="requires_point_in_time_collateral_eligibility_validation"
        elif screen_complete and len(selected)==rule["minimum_consecutive_days"] and market_cap_days==rule["minimum_consecutive_days"]: status="verified_below_threshold_in_selected_protocol_sample"
        else: status="proxy_threshold_not_met_or_insufficient_history"
        summaries.append({"asset_id":asset["asset_id"],"observed_days":len(selected),"market_cap_days":market_cap_days,"material_days":len(material_days),"longest_material_streak_days":streak,"balance_proxy_pass":int(passed),"screen_complete":int(screen_complete),"classification_status":status})
    return daily,summaries


def collect(repo:Path,start:date,end:date,force:bool=False,base_url:str=BASE_URL)->dict[str,Any]:
    spec=load_json(repo/"config"/"crypto_collateral_sources.json"); registry=load_json(repo/"config"/"assets.json"); validate_config(spec,registry)
    alias_index={alias:a["asset_id"] for a in spec["assets"] for alias in a["token_aliases"]}
    detail=[]; raw_root=repo/"data"/"raw"/"defillama_protocol_collateral"; complete_protocols=[]; expected=(end-start).days+1
    for protocol in spec["protocols"]:
        raw=raw_root/f"{protocol['slug']}.json"
        if raw.exists() and not force: payload=load_json(raw)
        else:
            payload=request_json(f"{base_url.rstrip('/')}/{protocol['slug']}"); raw.parent.mkdir(parents=True,exist_ok=True); raw.write_text(json.dumps(payload,separators=(",",":"))+"\n",encoding="utf-8")
            raw.with_suffix(".metadata.json").write_text(json.dumps({"protocol_slug":protocol["slug"],"provider":"defillama","retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"sha256":sha256(raw)},indent=2)+"\n",encoding="utf-8")
        history_days={datetime.fromtimestamp(int(point["date"]),timezone.utc).date() for point in payload.get("tokensInUsd") or [] if point.get("date")}
        if sum(start<=day<=end for day in history_days)==expected: complete_protocols.append(protocol["slug"])
        detail.extend(normalize_protocol(protocol["slug"],payload,alias_index,start,end))
    caps=market_caps([repo/"data"/"processed"/"historical"/"crypto_fundamentals_daily_coinmetrics.csv",repo/"data"/"processed"/"historical"/"market_daily_coinpaprika.csv"])
    screen_complete=len(complete_protocols)==len(spec["protocols"])
    daily,summaries=aggregate(detail,spec["assets"],caps,spec["primary_rule"],screen_complete)
    out=repo/"data"/"processed"/"evidence"; write_rows(out/"crypto_collateral_protocol_detail.csv",detail,["asset_id","date","protocol_slug","token_alias","supplied_balance_usd","provider"]); write_rows(out/"crypto_collateral_daily_proxy.csv",daily,["asset_id","date","supplied_balance_usd","market_cap_usd","supplied_to_market_cap","material_proxy"]); write_rows(out/"crypto_collateral_screen_summary.csv",summaries,list(summaries[0]))
    negative=[s["asset_id"] for s in summaries if s["classification_status"]=="verified_below_threshold_in_selected_protocol_sample"]
    result={"assets":len(spec["assets"]),"protocols":len(spec["protocols"]),"complete_protocols":len(complete_protocols),"screen_complete":screen_complete,"detail_rows":len(detail),"daily_rows":len(daily),"proxy_pass_assets":[s["asset_id"] for s in summaries if s["balance_proxy_pass"]],"verified_below_threshold_assets":negative,"classification_ready_assets":len(negative),"start_date":start.isoformat(),"end_date":end.isoformat(),"selection_rule":spec["selection_rule"],"interpretation":spec["interpretation"]}
    (out/"crypto_collateral_screen_summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Build a conservative free-source crypto collateral materiality screen"); parser.add_argument("--repo",type=Path,default=Path.cwd()); parser.add_argument("--start",type=date.fromisoformat,required=True); parser.add_argument("--end",type=date.fromisoformat,required=True); parser.add_argument("--force",action="store_true"); args=parser.parse_args()
    if args.end<args.start: parser.error("--end must be on or after --start")
    print(json.dumps(collect(args.repo.resolve(),args.start,args.end,args.force),indent=2))
