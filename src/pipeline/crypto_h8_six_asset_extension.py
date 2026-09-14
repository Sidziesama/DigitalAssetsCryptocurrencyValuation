from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from pathlib import Path
from typing import Any

from .crypto_h8_breadth_pilot import correlation, ranks, read_csv, slope


def validate(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1 or spec.get("status") != "frozen_before_extension_estimation":
        raise ValueError("unsupported H8 six-asset extension specification")
    assets = spec.get("assets", [])
    if len(assets) != 6 or len(set(assets)) != 6 or "crypto_bnb" not in assets:
        raise ValueError("H8 extension requires the frozen six-asset core universe including BNB")
    if not spec.get("selection_rule") or not spec.get("interpretation"):
        raise ValueError("H8 extension requires selection and interpretation guardrails")


def build(spec: dict[str, Any], readiness: list[dict[str, str]], market: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    validate(spec)
    expected = set(spec["assets"])
    ready = {row["asset_id"]:int(row["h8_value_accrual_breadth"]) for row in readiness
             if row["asset_id"] in expected and row["h8_design_ready"] == "1"}
    if set(ready) != expected:
        raise ValueError("every frozen H8 extension asset must have all ten classifications verified")
    observations: dict[str, list[float]] = {asset:[] for asset in expected}
    for row in market:
        if row["asset_id"] in observations and row.get("market_cap_usd"):
            value=float(row["market_cap_usd"])
            if value > 0: observations[row["asset_id"]].append(math.log(value))
    if any(not values for values in observations.values()):
        raise ValueError("every H8 extension asset requires positive market-cap observations")
    rows=[{"asset_id":asset,"h8_value_accrual_breadth":ready[asset],"market_cap_days":len(observations[asset]),
           "mean_log_market_cap_usd":sum(observations[asset])/len(observations[asset])} for asset in sorted(expected)]
    x=[float(row["h8_value_accrual_breadth"]) for row in rows]; y=[float(row["mean_log_market_cap_usd"]) for row in rows]
    observed_slope=slope(x,y); observed_rank=correlation(ranks(x),ranks(y)); permutations=list(itertools.permutations(x))
    slope_null=[slope(list(values),y) for values in permutations]
    rank_null=[correlation(ranks(list(values)),ranks(y)) for values in permutations]
    loo=[]
    for omitted,row in enumerate(rows):
        loo.append({"excluded_asset":row["asset_id"],"slope":slope([v for i,v in enumerate(x) if i!=omitted],[v for i,v in enumerate(y) if i!=omitted])})
    summary={"status":"exploratory_six_asset_h8_extension_complete","specification_version":spec["document_version"],
             "freeze_date":spec["freeze_date"],"assets":6,"asset_ids":sorted(expected),"outcome":spec["outcome"],"predictor":spec["predictor"],
             "slope":observed_slope,"exact_permutation_p_two_sided":sum(abs(v)>=abs(observed_slope)-1e-12 for v in slope_null)/len(permutations),
             "spearman_rank_correlation":observed_rank,"exact_rank_permutation_p_two_sided":sum(abs(v)>=abs(observed_rank)-1e-12 for v in rank_null)/len(permutations),
             "permutations":len(permutations),"leave_one_asset_out":loo,"leave_one_asset_out_positive":sum(row["slope"]>0 for row in loo),
             "comparison_guardrail":spec["interpretation"],"selection_rule":spec["selection_rule"]}
    return rows,summary


def run(repo: Path) -> dict[str, Any]:
    spec=json.loads((repo/"config/crypto_h8_six_asset_extension.json").read_text(encoding="utf-8"))
    rows,summary=build(spec,read_csv(repo/"data/processed/01_classification/crypto_h2_h8_pilot_readiness.csv"),
                       read_csv(repo/"data/processed/02_valuation/crypto_h2_exploratory_daily.csv"))
    out=repo/"data/processed/02_valuation"; out.mkdir(parents=True,exist_ok=True)
    with (out/"crypto_h8_six_asset_extension.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]),lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    (out/"crypto_h8_six_asset_extension.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Estimate the separately frozen six-asset exploratory H8 extension")
    parser.add_argument("--repo",type=Path,default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
