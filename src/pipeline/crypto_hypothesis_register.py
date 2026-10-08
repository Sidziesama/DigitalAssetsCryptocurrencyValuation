from __future__ import annotations

import argparse, csv, json
from pathlib import Path
from typing import Any


QUESTIONS = {
    "H1": "Is greater network usage associated with higher network value?",
    "H2": "Is usage more valuable when fees reach the token or its holders?",
    "H3": "Is greater circulating-supply growth associated with weaker returns?",
    "H4": "Does staking reduce liquid float and affect liquidity or risk?",
    "H8": "Do theory-defined economic-function groups explain valuation better than raw function breadth?",
}


def build(findings: dict[str, Any], strict: dict[str, Any]) -> list[dict[str, Any]]:
    f=findings["findings"]
    strict_pooled=next(row for row in strict["results"] if row["specification"]=="pooled_market_cap")
    rows=[
        {"hypothesis":"H1","sample":"4 assets","test_state":"estimated_exploratory","result":"suggestive_not_confirmed",
         "key_statistic":f"transactions coefficient={f['H1']['transaction_count_coefficient']:.4f}; p={f['H1']['transaction_count_exact_p']:.4f}",
         "advisory_interpretation":"Usage is economically relevant to monitor, but the present sample cannot establish a general valuation relationship.",
         "next_action":"Expand primary-source activity coverage without selecting assets from observed returns."},
        {"hypothesis":"H2","sample":"11 assets","test_state":"estimated_exploratory_definition_sensitive","result":"not_robust_to_strict_capture_rule",
         "key_statistic":f"broad interaction={f['H2']['pooled_market_cap_interaction']:.4f}, p={f['H2']['pooled_market_cap_exact_p']:.4f}; strict interaction={strict_pooled['strict_coefficient']:.4f}, p={strict_pooled['strict_p']:.4f}",
         "advisory_interpretation":"Fee activity alone is insufficient; the definition and path of holder capture materially change the result.",
         "next_action":"Retain both specifications and seek an out-of-sample period rather than redefining capture again."},
        {"hypothesis":"H3","sample":(f"{f['H3']['supply_events_estimated']} events from one asset" if f['H3'].get('supply_events_estimated') else f"{f['H3']['assets']} assets; {f['H3']['assets_with_within_supply_variation']} vary"),"test_state":"descriptive_event_result_not_identification_ready","result":"not_supported",
         "key_statistic":(f"mean [-1,+1] abnormal return={f['H3']['supply_event_mean_primary_car']:.4f}; predicted-negative events={f['H3']['supply_events_matching_negative_sign']}/{f['H3']['supply_events_estimated']}" if f['H3'].get('supply_events_estimated') else f"supply-growth coefficient={f['H3']['supply_growth_coefficient']:.4f}; p={f['H3']['exact_p']:.4f}"),
         "advisory_interpretation":"Current daily supply data do not identify a dilution effect.",
         "next_action":"Add a second qualifying asset before pooled inference; preserve the single-asset ARB result as descriptive."},
        {"hypothesis":"H4","sample":f"{f['H4']['assets']} planned assets","test_state":"blocked_on_historical_staking_coverage","result":"not_yet_tested",
         "key_statistic":f"complete positive-staking histories={f['H4']['positive_assets_with_historical_staking']}",
         "advisory_interpretation":"Staking classification is usable descriptively, but its liquidity effect cannot yet be estimated.",
         "next_action":"Complete archival ETH consensus and current Aave Umbrella staking histories."},
        {"hypothesis":"H8","sample":f"{f['H8']['verified_universe_assets']} classified assets; 22 primary-outcome eligible","test_state":"estimated_post_pilot_exploratory","result":f['H8']['verified_universe_decision'],
         "key_statistic":f"best={f['H8']['verified_universe_best_group']}; RMSE={f['H8']['verified_universe_best_group_loo_rmse']:.4f} vs breadth={f['H8']['verified_universe_raw_breadth_loo_rmse']:.4f}",
         "advisory_interpretation":"Which functions an asset performs appears more informative than simply counting functions; financial integration is strongest in this sample.",
         "next_action":"Treat as hypothesis-generating and validate on a later fixed universe or time window."},
    ]
    for row in rows: row["research_question"]=QUESTIONS[row["hypothesis"]]
    return rows


def render(rows: list[dict[str,Any]]) -> str:
    out=["# Crypto hypothesis evidence register","","Generated from reproducible outputs. Exploratory associations are not causal findings or investment recommendations.","","| ID | Research question | Current answer | Evidence state | Next action |","|---|---|---|---|---|"]
    for r in rows: out.append(f"| {r['hypothesis']} | {r['research_question']} | {r['advisory_interpretation']} | {r['test_state']} — {r['key_statistic']} | {r['next_action']} |")
    return "\n".join(out)+"\n"


def run(repo: Path) -> dict[str,Any]:
    load=lambda path: json.loads((repo/path).read_text(encoding="utf-8"))
    rows=build(load("data/processed/02_valuation/crypto_findings_summary.json"),load("data/processed/02_valuation/crypto_h2_strict_capture_sensitivity.json"))
    out=repo/"data/processed/02_valuation"; fields=list(rows[0])
    with (out/"crypto_hypothesis_evidence_register.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    summary={"status":"crypto_hypothesis_evidence_register_complete","hypotheses":len(rows),"estimated":sum(r["test_state"].startswith("estimated") for r in rows),"blocked":[r["hypothesis"] for r in rows if "blocked" in r["test_state"]],"guardrail":"Exploratory associations are not causal findings or investment recommendations."}
    (out/"crypto_hypothesis_evidence_register.json").write_text(json.dumps({"summary":summary,"hypotheses":rows},indent=2)+"\n",encoding="utf-8")
    (repo/"research/findings/crypto-hypothesis-evidence-register.md").write_text(render(rows),encoding="utf-8")
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--repo",type=Path,default=Path.cwd()); print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
