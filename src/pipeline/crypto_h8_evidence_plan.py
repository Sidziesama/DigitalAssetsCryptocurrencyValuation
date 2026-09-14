from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from src.pipeline.crypto_economic_design import CODES


EXPECTED_CODES = ("VA_GAS","VA_STAKE","VA_SCARCITY","VA_GOV","VA_UTILITY","VA_INCENTIVE")


def validate(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1:
        raise ValueError("unsupported H8 evidence-plan schema")
    assets=spec.get("assets",[]); codes=spec.get("codes",{})
    if len(assets)!=6 or len(assets)!=len(set(assets)):
        raise ValueError("H8 pilot plan requires six unique assets")
    if tuple(codes) != EXPECTED_CODES or not set(codes)<=set(CODES):
        raise ValueError("H8 plan must contain the six remaining value-accrual codes in canonical order")
    for code,rule in codes.items():
        if not all(rule.get(field) for field in ("positive_rule","negative_rule","required_evidence")):
            raise ValueError(f"incomplete classification rule for {code}")
    if not spec.get("review_rule"):
        raise ValueError("review rule is required")


def validate_evidence(evidence: dict[str,Any],spec:dict[str,Any])->None:
    if evidence.get("schema_version")!=1 or evidence.get("assets")!=spec["assets"]:
        raise ValueError("invalid H8 evidence tranche identity")
    codes=evidence.get("codes",[]); expected={(asset,code) for asset in spec["assets"] for code in codes}
    if not codes or not set(codes)<=set(spec["codes"]): raise ValueError("invalid H8 evidence tranche codes")
    decisions=evidence.get("decisions",[]); keys={(row.get("asset_id"),row.get("code")) for row in decisions}
    if len(decisions)!=len(keys) or keys!=expected: raise ValueError("H8 evidence tranche must contain a complete asset-code grid")
    as_of=date.fromisoformat(evidence["as_of"])
    for row in decisions:
        verified=row.get("status")=="verified"
        if verified and row.get("recommended_value") not in {0,1}: raise ValueError("verified H8 decisions require binary values")
        if not verified and row.get("recommended_value") is not None: raise ValueError("pending H8 decisions must remain null")
        if not str(row.get("source_url","")).startswith("https://"): raise ValueError("H8 decisions require HTTPS sources")
        if date.fromisoformat(row["source_date"])>as_of: raise ValueError("future H8 evidence is prohibited")
        if row.get("date_basis") not in {"published","effective","retrieved_as_of"}: raise ValueError("invalid H8 evidence date basis")
        if not row.get("rationale"): raise ValueError("H8 decisions require rationale")


def merge_evidence(spec:dict[str,Any],tranches:list[dict[str,Any]])->dict[str,Any]:
    """Validate independently authored tranches and reject overlapping decisions."""
    decisions=[]; codes=[]; keys=set()
    for tranche in tranches:
        validate_evidence(tranche,spec)
        for code in tranche["codes"]:
            if code not in codes: codes.append(code)
        for row in tranche["decisions"]:
            key=(row["asset_id"],row["code"])
            if key in keys: raise ValueError(f"duplicate H8 evidence decision: {key[0]} {key[1]}")
            keys.add(key); decisions.append(row)
    return {"schema_version":1,"as_of":spec["as_of"],"assets":spec["assets"],"codes":codes,"decisions":decisions}


def build(spec: dict[str, Any],evidence:dict[str,Any]|None=None,design:dict[str,Any]|None=None) -> tuple[list[dict[str, Any]], list[dict[str,Any]], dict[str, Any]]:
    validate(spec)
    if evidence: validate_evidence(evidence,spec)
    decisions={(row["asset_id"],row["code"]):row for row in (evidence or {}).get("decisions",[])}
    design_index={}
    if design:
        design_index={row["asset_id"]:dict(zip(CODES,row["codes"])) for row in design["assets"]}
    audit=[]; review=[]; verified=0; mismatches=0
    for asset_id in spec["assets"]:
        for code,rule in spec["codes"].items():
            decision=decisions.get((asset_id,code)); status=decision["status"] if decision else "planned_not_extracted"
            value=decision["recommended_value"] if decision else None; provisional=design_index.get(asset_id,{}).get(code)
            if status=="verified": verified+=1; mismatches+=int(provisional is not None and provisional!=value)
            audit.append({"asset_id":asset_id,"code":code,"status":status,"recommended_value":value,"provisional_value":provisional,"verified_matches_design":"" if status!="verified" or provisional is None else int(provisional==value),"source_url":decision["source_url"] if decision else "","source_date":decision["source_date"] if decision else "","date_basis":decision["date_basis"] if decision else "","rationale":decision["rationale"] if decision else ""})
            if status=="verified": continue
            review.append({
                "asset_id":asset_id,"code":code,"positive_rule":rule["positive_rule"],
                "negative_rule":rule["negative_rule"],"required_evidence":rule["required_evidence"],
                "reviewer_value":"","source_url":"","source_date":"","date_basis":"","reviewer":"","rationale":""
            })
    targeted=len(spec["assets"])*len(spec["codes"])
    return audit,review,{
        "status":"six_code_evidence_complete" if verified==targeted else "evidence_extraction_in_progress",
        "assets":len(spec["assets"]),"codes":len(spec["codes"]),"targeted_decisions":targeted,
        "verified_decisions":verified,"pending_decisions":targeted-verified,"verified_mismatches":mismatches,
        "guardrail":"The blind worksheet contains rules but excludes every provisional design value. H8 breadth remains null until all ten codes are verified per asset."
    }


def run(repo:Path)->dict[str,Any]:
    spec=json.loads((repo/"config/crypto_h8_evidence_plan.json").read_text())
    tranches=[json.loads(path.read_text()) for path in sorted((repo/"config").glob("crypto_h8_evidence_tranche_*.json"))]
    evidence=merge_evidence(spec,tranches)
    design=json.loads((repo/"config/crypto_economic_design.json").read_text())
    audit,rows,summary=build(spec,evidence,design); out=repo/"data/processed/01_classification"; out.mkdir(parents=True,exist_ok=True)
    with (out/"crypto_h8_evidence_audit.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(audit[0]),lineterminator="\n"); writer.writeheader(); writer.writerows(audit)
    with (out/"crypto_h8_evidence_review.csv").open("w",newline="",encoding="utf-8") as handle:
        fields=["asset_id","code","positive_rule","negative_rule","required_evidence","reviewer_value","source_url","source_date","date_basis","reviewer","rationale"]
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    (out/"crypto_h8_evidence_plan_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Build the blind six-code H8 evidence-extension plan")
    parser.add_argument("--repo",type=Path,default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
