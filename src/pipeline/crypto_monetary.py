from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .historical import write_rows
from .registry import load_json


def validate(spec:dict[str,Any])->None:
    if spec.get("schema_version")!=1 or spec.get("minimum_tests_to_qualify")!=2: raise ValueError("unsupported monetary-evidence specification")
    window=spec.get("activity_window",{}); start=date.fromisoformat(window["start"]); end=date.fromisoformat(window["end"])
    if end<start or window.get("minimum_days",0)<30 or window.get("median_active_addresses",0)<=0 or window.get("median_transactions",0)<=0: raise ValueError("invalid monetary activity rule")
    as_of=date.fromisoformat(spec["as_of"]); ids=[]
    for asset in spec.get("assets",[]):
        ids.append(asset.get("asset_id")); status=asset.get("monetary_design_status"); value=asset.get("monetary_design_value")
        if status=="verified" and value not in {0,1}: raise ValueError("verified monetary design requires binary value")
        if status!="verified" and value is not None: raise ValueError("pending monetary design must remain null")
        if not str(asset.get("source_url","")).startswith("https://") or date.fromisoformat(asset["source_date"])>as_of: raise ValueError("invalid point-in-time monetary evidence")
    if not ids or len(ids)!=len(set(ids)): raise ValueError("monetary evidence assets must be unique")


def load_activity(path:Path)->list[dict[str,str]]:
    with path.open(newline="",encoding="utf-8") as handle: return list(csv.DictReader(handle))


def assess(spec:dict[str,Any],activity:list[dict[str,str]])->list[dict[str,Any]]:
    validate(spec); window=spec["activity_window"]; start,end=date.fromisoformat(window["start"]),date.fromisoformat(window["end"]); grouped=defaultdict(list)
    for row in activity:
        try: day=date.fromisoformat(row["date"])
        except (KeyError,ValueError): continue
        if start<=day<=end: grouped[row["asset_id"]].append(row)
    output=[]
    for evidence in spec["assets"]:
        rows=grouped[evidence["asset_id"]]
        active=[float(r["active_addresses"]) for r in rows if r.get("active_addresses")]; tx=[float(r["transaction_count"]) for r in rows if r.get("transaction_count")]
        med_active=statistics.median(active) if active else None; med_tx=statistics.median(tx) if tx else None
        activity_pass=int(len(rows)>=window["minimum_days"] and med_active is not None and med_tx is not None and med_active>=window["median_active_addresses"] and med_tx>=window["median_transactions"])
        design_pass=int(evidence["monetary_design_status"]=="verified" and evidence["monetary_design_value"]==1); tests=activity_pass+design_pass
        design_verified=evidence["monetary_design_status"]=="verified"
        complete_activity=len(rows)>=window["minimum_days"]
        recommendation=1 if design_verified and complete_activity and tests>=spec["minimum_tests_to_qualify"] else (0 if design_verified and evidence["monetary_design_value"]==0 else None)
        status="verified_positive" if recommendation==1 else ("verified_negative" if recommendation==0 else "unresolved_no_negative_inference")
        output.append({"asset_id":evidence["asset_id"],"observed_days":len(rows),"median_active_addresses":med_active,"median_transactions":med_tx,"activity_materiality_pass":activity_pass,"monetary_design_pass":design_pass,"tests_passed":tests,"recommended_va_monetary":recommendation,"status":status,"source_url":evidence["source_url"],"source_date":evidence["source_date"]})
    return output


def run(repo:Path)->dict[str,Any]:
    spec=load_json(repo/"config"/"crypto_monetary_evidence.json"); rows=assess(spec,load_activity(repo/"data"/"processed"/"historical"/"crypto_fundamentals_daily_coinmetrics.csv")); out=repo/"data"/"processed"/"evidence"; write_rows(out/"crypto_monetary_assessment.csv",rows,list(rows[0]))
    result={"assets":len(rows),"verified_positive_assets":[r["asset_id"] for r in rows if r["recommended_va_monetary"]==1],"verified_negative_assets":[r["asset_id"] for r in rows if r["recommended_va_monetary"]==0],"unresolved_assets":[r["asset_id"] for r in rows if r["recommended_va_monetary"] is None],"activity_rule":spec["activity_window"],"interpretation":"VA_MONETARY=1 requires both persistent material activity and verified monetary-design evidence. A zero requires primary-source review establishing no qualifying monetary function; generic activity cannot override a verified non-monetary design. Missing design evidence never becomes zero."}; (out/"crypto_monetary_assessment.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Apply the two-test crypto monetary-use classification rule"); parser.add_argument("--repo",type=Path,default=Path.cwd()); print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
