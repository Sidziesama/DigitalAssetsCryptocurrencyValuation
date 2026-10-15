from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROHIBITED = {"return", "price", "car", "abnormal_return", "market_outcome"}


def validate(spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("schema_version") != 1 or spec.get("hypothesis") != "H3":
        raise ValueError("unsupported H3 candidate screen")
    if spec.get("universe_policy") != "existing_active_assets_only" or spec.get("minimum_materiality_share") != 0.005:
        raise ValueError("H3 universe or materiality rule changed")
    if spec.get("outcome_data_prohibited") is not True:
        raise ValueError("H3 screen must prohibit outcome data")
    candidates=spec.get("candidates",[])
    if not candidates: raise ValueError("H3 screen has no candidates")
    for row in candidates:
        if PROHIBITED.intersection(row):
            raise ValueError("outcome data entered the evidence-only H3 screen")
        if not row.get("official_source_url","").startswith("https://"):
            raise ValueError("candidate lacks official HTTPS evidence")
        share=row.get("materiality_share")
        if row["decision"]=="eligible_for_preregistered_addition" and (share is None or share < 0.005 or not row["exact_event_date_available"]):
            raise ValueError("eligible candidate fails the frozen H3 rule")
    eligible=[row["asset_id"] for row in candidates if row["decision"]=="eligible_for_preregistered_addition"]
    return {
        "status":"h3_fourth_asset_screen_complete_no_qualifying_candidate" if not eligible else "h3_fourth_asset_candidate_ready_for_approval",
        "screen_date":spec["screen_date"], "candidates_screened":len(candidates), "eligible_assets":eligible,
        "outcome_data_used":False, "minimum_materiality_share":spec["minimum_materiality_share"],
        "decisions":{row["asset_id"]:row["decision"] for row in candidates},
        "next_action":"Preserve the current three-asset H3 result. Add no asset until official evidence satisfies exact date, direction, amount, denominator, and 0.5% materiality without consulting returns."
    }


def render(spec: dict[str,Any], result: dict[str,Any]) -> str:
    lines=["# H3 fourth-asset evidence screen — 15 October 2026", "", "This screen uses protocol evidence only. No price, return, or event-study output was consulted.", "", f"**Result:** {len(result['eligible_assets'])} of {result['candidates_screened']} candidates qualifies under the unchanged 0.5% materiality and exact-event rule.", "", "| Asset | Evidence-only assessment | Decision |", "|---|---|---|"]
    for row in spec["candidates"]:
        lines.append(f"| {row['symbol']} | {row['evidence']} [Official source]({row['official_source_url']}) | `{row['decision']}` |")
    lines += ["", "## Action", "", result["next_action"], "", "This is a selection-integrity result, not evidence for or against H3.", ""]
    return "\n".join(lines)


def run(repo: Path) -> dict[str,Any]:
    spec=json.loads((repo/"config/crypto_h3_fourth_asset_screen.json").read_text())
    result=validate(spec)
    out=repo/"data/processed/02_valuation/crypto_h3_fourth_asset_screen.json"; out.write_text(json.dumps(result,indent=2)+"\n")
    report=repo/"research/findings/2026-10-15-h3-fourth-asset-screen.md"; report.write_text(render(spec,result))
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--repo",type=Path,default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
