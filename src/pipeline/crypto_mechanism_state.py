from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from .crypto_economic_design import CODES,load_json
from .historical import write_rows


ALLOWED={"VA_BURN","VA_PROTOCOL"}


def resolve(events_spec:dict[str,Any],design:dict[str,Any])->tuple[list[dict[str,Any]],dict[str,Any]]:
    if events_spec.get("schema_version")!=1: raise ValueError("unsupported mechanism-event schema")
    as_of=date.fromisoformat(events_spec["as_of"]); seen=set(); grouped={}
    for event in events_spec.get("events",[]):
        key=(event.get("asset_id"),event.get("code"),event.get("effective_from"))
        if key in seen: raise ValueError("duplicate effective-dated mechanism event")
        seen.add(key)
        if event.get("code") not in ALLOWED or event.get("value") not in {0,1}: raise ValueError("invalid mechanism event")
        if not str(event.get("source_url","")).startswith("https://") or not event.get("rationale"): raise ValueError("mechanism event requires source and rationale")
        effective=date.fromisoformat(event["effective_from"])
        if effective<=as_of:
            group=(event["asset_id"],event["code"])
            if group not in grouped or effective>date.fromisoformat(grouped[group]["effective_from"]): grouped[group]=event
    design_index={row["asset_id"]:dict(zip(CODES,row["codes"])) for row in design["assets"]}
    rows=[]
    for (asset_id,code),event in sorted(grouped.items()):
        if asset_id not in design_index: raise ValueError("mechanism event asset missing from design")
        value=design_index[asset_id][code]
        rows.append({**event,"as_of":as_of.isoformat(),"design_value":value,"matches_design":int(value==event["value"])})
    mismatches=[r for r in rows if not r["matches_design"]]
    summary={"as_of":as_of.isoformat(),"resolved_asset_code_states":len(rows),"mismatches":len(mismatches),"status":"pass" if not mismatches else "blocked_design_state_mismatch","rule":"Use the latest evidenced event effective on or before the observation date; inactive or paused mechanisms are zero even if a future option remains."}
    return rows,summary


def run(repo:Path)->dict[str,Any]:
    rows,summary=resolve(load_json(repo/"config"/"crypto_mechanism_events.json"),load_json(repo/"config"/"crypto_economic_design.json")); out=repo/"data"/"processed"/"01_classification"; fields=list(dict.fromkeys(key for row in rows for key in row)); write_rows(out/"crypto_mechanism_state_asof.csv",rows,fields); (out/"crypto_mechanism_state_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8"); return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Resolve effective-dated burn and protocol-capture state"); parser.add_argument("--repo",type=Path,default=Path.cwd()); print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
