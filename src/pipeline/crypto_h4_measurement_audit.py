from __future__ import annotations

import argparse, json
from pathlib import Path
from typing import Any


def build(readiness: dict[str,Any]) -> dict[str,Any]:
    positive=[r for r in readiness["audit"] if r["va_stake"]==1]
    rows=[]
    for row in positive:
        role="consensus_native_stake" if row["asset_id"] in {"crypto_eth","crypto_bnb"} else "legacy_aave_token_risk_stake_case_study"
        complete=row["staking_history_days"]>=row["minimum_history_days"]
        rows.append({"asset_id":row["asset_id"],"measurement_role":role,"observed_days":row["staking_history_days"],"required_days":row["minimum_history_days"],"coverage_share":row["staking_history_days"]/row["minimum_history_days"],"history_complete":complete,"ready_for_primary_h4":row["positive_staking_history_ready"]})
    return {"status":"h4_measurement_audit_complete","series":rows,"consensus_assets_ready":sum(r["ready_for_primary_h4"] for r in rows if r["measurement_role"]=="consensus_native_stake"),"case_studies_ready":sum(r["history_complete"] for r in rows if r["measurement_role"]!="consensus_native_stake"),"pooled_estimation_ready":readiness["identification_ready"],"boundary_decision":"Umbrella USDC, USDT, WETH, and GHO stake is protocol backstop capital but is not AAVE-denominated stake. It is excluded from the AAVE-token staking series.","next_required":"Configure a 365-day archival ETH active-effective-balance series; BNB is complete for consensus stake and legacy stkAAVE is complete as a separate case study."}


def chart(result: dict[str,Any]) -> str:
    width,height=860,285; left,plot=180,590; colors={"crypto_eth":"#b6534c","crypto_bnb":"#d99a2b","crypto_aave":"#3478b8"}; labels={"crypto_eth":"ETH consensus","crypto_bnb":"BNB consensus","crypto_aave":"AAVE legacy risk stake"}
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="H4 staking history coverage versus the 365 day requirement">','<rect width="100%" height="100%" fill="#ffffff"/>','<text x="24" y="30" font-family="Arial" font-size="20" font-weight="600" fill="#17212b">H4 historical staking coverage</text>','<text x="24" y="53" font-family="Arial" font-size="12" fill="#647383">Required history: 365 days. BNB and legacy stkAAVE are complete; ETH remains missing.</text>']
    for i,row in enumerate(result["series"]):
        y=82+i*55; w=plot*min(1,row["coverage_share"]); parts += [f'<text x="{left-12}" y="{y+19}" text-anchor="end" font-family="Arial" font-size="13" fill="#17212b">{labels[row["asset_id"]]}</text>',f'<rect x="{left}" y="{y}" width="{plot}" height="25" rx="3" fill="#d7dde3" opacity="0.45"/>',f'<rect x="{left}" y="{y}" width="{w:.1f}" height="25" rx="3" fill="{colors[row["asset_id"]]}"/>',f'<text x="{left+w+8}" y="{y+18}" font-family="Arial" font-size="12" font-weight="600" fill="#17212b">{row["observed_days"]} days</text>']
    parts += [f'<text x="{left+plot}" y="{height-25}" text-anchor="end" font-family="Arial" font-size="12" fill="#647383">365-day gate</text>','</svg>']; return "\n".join(parts)+"\n"


def run(repo: Path):
    readiness=json.loads((repo/"data/processed/01_classification/crypto_h4_source_readiness.json").read_text()); result=build(readiness)
    (repo/"data/processed/01_classification/crypto_h4_measurement_audit.json").write_text(json.dumps(result,indent=2)+"\n")
    (repo/"research/figures/crypto-h4-staking-coverage.svg").write_text(chart(result),encoding="utf-8"); return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--repo",type=Path,default=Path.cwd()); print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
