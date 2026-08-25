from __future__ import annotations

import argparse,csv,json
from pathlib import Path
from typing import Any

from .registry import load_json


def validate_weights(weights:dict[str,float])->None:
    if set(weights)==set():raise ValueError("weights cannot be empty")
    if any(not isinstance(v,(int,float)) or v<=0 for v in weights.values()):raise ValueError("weights must be positive")
    if abs(sum(weights.values())-100)>1e-9:raise ValueError("weights must sum to 100")


def score_block(values:dict[str,Any],weights:dict[str,float])->dict[str,Any]:
    validate_weights(weights);missing=[name for name in weights if values.get(name) is None]
    invalid=[name for name in weights if values.get(name) is not None and (not isinstance(values[name],(int,float)) or not 0<=values[name]<=100)]
    if invalid:raise ValueError(f"invalid component scores: {invalid}")
    observed=[name for name in weights if values.get(name) is not None]
    observed_weight=sum(weights[name] for name in observed)
    partial=sum(values[name]*weights[name] for name in observed)/observed_weight if observed_weight else None
    strict=partial if not missing else None
    return {"strict_score":strict,"partial_score":partial,"completeness":observed_weight/100,"missing_components":missing}


def evaluate(config:dict[str,Any])->list[dict[str,Any]]:
    if config.get("schema_version")!=1:raise ValueError("unsupported schema version")
    weights=config["weights"]
    for block in weights.values():validate_weights(block)
    output=[]
    for asset in config.get("assets",[]):
        if not asset.get("evidence_urls") or not asset.get("evidence_date"):raise ValueError(f"missing evidence: {asset.get('asset_id')}")
        row={"asset_id":asset["asset_id"],"methodology_version":config["methodology_version"],"evidence_date":asset["evidence_date"],"confidence":asset.get("confidence"),"evidence_urls":" | ".join(asset["evidence_urls"]),"rationale":asset.get("rationale","")}
        for dimension in ("reserve_quality","transparency","redemption_friction"):
            result=score_block(asset.get(dimension,{}),weights[dimension])
            row[f"{dimension}_score"]=result["strict_score"]
            row[f"{dimension}_partial_score"]=result["partial_score"]
            row[f"{dimension}_completeness"]=result["completeness"]
            row[f"{dimension}_missing"]=";".join(result["missing_components"])
        output.append(row)
    return output


def render_findings(rows:list[dict[str,Any]])->str:
    lines=[]
    for r in rows:
        def fmt(x):return "withheld" if x is None else f"{x:.1f}"
        lines.append(f"- `{r['asset_id']}` — reserve quality {fmt(r['reserve_quality_score'])}; transparency {fmt(r['transparency_score'])}; redemption friction {fmt(r['redemption_friction_score'])} ({r['redemption_friction_completeness']:.0%} complete).")
    return "# Preliminary Stablecoin Risk Scores\n\n## Strict-score results\n\n"+"\n".join(lines)+"\n\n## Interpretation\n\nReserve quality and transparency are higher-is-better; redemption friction is higher-is-worse. A strict composite is withheld whenever any required component is missing. Partial scores are retained in the machine-readable output for diagnostics only and must not be used as headline results. Inputs are analyst-coded from dated official disclosures and remain subject to second-coder review.\n"


def main()->None:
    p=argparse.ArgumentParser();p.add_argument("--repo",type=Path,default=Path.cwd());a=p.parse_args();repo=a.repo.resolve();rows=evaluate(load_json(repo/"config"/"stablecoin_risk_inputs.json"));out=repo/"data"/"processed"/"stablecoin_risk_scores.csv";out.parent.mkdir(parents=True,exist_ok=True)
    fields=list(rows[0]);
    with out.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    (repo/"research"/"findings"/"preliminary-stablecoin-risk-scores.md").write_text(render_findings(rows),encoding="utf-8");print(json.dumps(rows,indent=2))


if __name__=="__main__":main()
