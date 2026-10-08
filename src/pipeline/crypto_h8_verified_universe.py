from __future__ import annotations

import argparse, csv, json, math, random, statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .crypto_h2_exploratory_estimates import solve
from .crypto_function_risk_exposure import benjamini_hochberg, max_drawdown


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle: return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields=sorted({key for row in rows for key in row})
    with path.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,lineterminator="\n"); writer.writeheader(); writer.writerows(rows)


def number(value: Any) -> float | None:
    try: result = float(value)
    except (TypeError, ValueError): return None
    return result if math.isfinite(result) else None


def validate(spec: dict[str, Any]) -> None:
    if spec.get("status") != "frozen_before_verified_universe_estimation": raise ValueError("H8 specification is not frozen")
    if spec.get("expected_assets") != 23 or len(spec.get("group_models", [])) != 8: raise ValueError("frozen universe/groups changed")
    if spec.get("primary_comparison_metric") != "leave_one_asset_out_root_mean_squared_prediction_error": raise ValueError("unsupported metric")


def ols(x: list[list[float]], y: list[float]) -> list[float] | None:
    if not x or len(x) != len(y): return None
    design = [[1.0, *row] for row in x]; k = len(design[0])
    if len(design) <= k: return None
    xtx = [[sum(row[i]*row[j] for row in design) for j in range(k)] for i in range(k)]
    xty = [sum(row[i]*value for row, value in zip(design, y)) for i in range(k)]
    try: return solve(xtx, xty)
    except (ValueError, ZeroDivisionError): return None


def loo_rmse(x: list[list[float]], y: list[float]) -> float | None:
    errors=[]
    for omitted in range(len(y)):
        fit=ols([r for i,r in enumerate(x) if i!=omitted],[v for i,v in enumerate(y) if i!=omitted])
        if fit is None: return None
        prediction=fit[0]+sum(c*v for c,v in zip(fit[1:],x[omitted])); errors.append((prediction-y[omitted])**2)
    return math.sqrt(statistics.fmean(errors))


def ranks(values: list[float]) -> list[float]:
    result=[0.0]*len(values); order=sorted(range(len(values)),key=values.__getitem__); i=0
    while i<len(order):
        j=i+1
        while j<len(order) and values[order[j]]==values[order[i]]: j+=1
        for index in order[i:j]: result[index]=(i+j-1)/2+1
        i=j
    return result


def winsorize(values: list[float], share: float=.05) -> list[float]:
    ordered=sorted(values); low=ordered[max(0,math.ceil(share*len(values))-1)]; high=ordered[min(len(values)-1,math.ceil((1-share)*len(values))-1)]
    return [min(high,max(low,value)) for value in values]


def collect_outcomes(spec: dict[str,Any], market: list[dict[str,str]], panel: list[dict[str,str]], asset_ids: set[str]):
    window=spec["measurement_window"]; start,end=window["start"],window["end"]
    expected=(date.fromisoformat(end)-date.fromisoformat(start)).days+1; minimum=math.ceil(expected*float(window["minimum_coverage_share"]))
    caps=defaultdict(list)
    for row in market:
        value=number(row.get("market_cap_usd"))
        if row.get("asset_id") in asset_ids and start<=row.get("date","")<=end and value and value>0: caps[row["asset_id"]].append(math.log(value))
    series=defaultdict(list)
    for row in panel:
        ret=number(row.get("log_return"))
        if row.get("asset_id") in asset_ids and start<=row.get("date","")<=end and ret is not None:
            series[row["asset_id"]].append((row["date"],ret,number(row.get("market_ew_log_return")),number(row.get("log_dollar_volume"))))
    outcomes=defaultdict(dict)
    for asset,values in caps.items():
        if len(values)>=minimum: outcomes[asset]["mean_log_market_cap_usd"]=statistics.fmean(values)
    for asset,observations in series.items():
        observations.sort()
        if len(observations)<minimum: continue
        returns=[r[1] for r in observations]; volumes=[r[3] for r in observations if r[3] is not None]; paired=[(r[1],r[2]) for r in observations if r[2] is not None]
        if volumes: outcomes[asset]["mean_log_dollar_volume"]=statistics.fmean(volumes)
        if len(paired)>=minimum:
            fit=ols([[m] for _,m in paired],[a for a,_ in paired])
            if fit: outcomes[asset]["market_beta"]=fit[1]
        outcomes[asset]["realized_volatility_annualized"]=statistics.pstdev(returns)*math.sqrt(365)
        outcomes[asset]["max_drawdown_log"]=max_drawdown(returns)
    names=[spec["primary_outcome"],*spec["secondary_outcomes"]]
    coverage={name:{"eligible_assets":sorted(a for a in asset_ids if name in outcomes.get(a,{})),"missing_assets":sorted(a for a in asset_ids if name not in outcomes.get(a,{}))} for name in names}
    return outcomes,{"expected_calendar_days":expected,"minimum_observations":minimum,"by_outcome":coverage}


def architecture_controls(rows):
    categories=sorted({r["architecture_context"] for r in rows})[1:]
    return {r["asset_id"]:[float(r["architecture_context"]==c) for c in categories] for r in rows}


def estimate(assets,profiles,outcomes,outcome,predictors,transform="level",controls=None):
    eligible=[a for a in assets if outcome in outcomes.get(a,{})]; y=[outcomes[a][outcome] for a in eligible]
    if transform=="rank": y=ranks(y)
    elif transform=="winsor": y=winsorize(y)
    x=[[float(profiles[a][p]) for p in predictors]+((controls or {}).get(a,[])) for a in eligible]; fit=ols(x,y)
    return {"assets":eligible,"n":len(eligible),"fit":fit,"loo_rmse":loo_rmse(x,y),"x":x,"y":y}


def permutation_p(result,draws,rng):
    if result["fit"] is None: return None
    observed=abs(result["fit"][1]); exceed=0; shuffled=list(result["y"])
    for _ in range(draws):
        rng.shuffle(shuffled); null=ols(result["x"],shuffled)
        if null is not None and abs(null[1])>=observed-1e-12: exceed+=1
    return (exceed+1)/(draws+1)


def build(spec,profile_rows,market,panel):
    validate(spec)
    if len(profile_rows)!=23 or any(r.get("classification_status")!="complete_human_verified" for r in profile_rows): raise ValueError("H8 requires 23 complete human-verified profiles")
    profiles={r["asset_id"]:r for r in profile_rows}; assets=sorted(profiles); outcomes,coverage=collect_outcomes(spec,market,panel,set(assets))
    models=[*spec["benchmark_models"],*({"id":n,"predictors":[n]} for n in spec["group_models"]),*spec["predeclared_nested_models"]]
    rows=[]; rng=random.Random(spec["inference"]["random_seed"]); draws=int(spec["inference"]["monte_carlo_draws_when_exact_enumeration_is_infeasible"])
    for outcome in [spec["primary_outcome"],*spec["secondary_outcomes"]]:
        for model in models:
            result=estimate(assets,profiles,outcomes,outcome,model["predictors"])
            row={"outcome":outcome,"model_id":model["id"],"predictors":"|".join(model["predictors"]),"n":result["n"],"estimable":int(result["fit"] is not None),"loo_rmse":result["loo_rmse"]}
            if result["fit"]:
                row["intercept"]=result["fit"][0]; row["coefficients"]="|".join(str(v) for v in result["fit"][1:1+len(model["predictors"])])
                if outcome==spec["primary_outcome"] and model["id"] in spec["group_models"]: row["permutation_p_two_sided"]=permutation_p(result,draws,rng); row["permutation_draws"]=draws
            rows.append(row)
    groups=[r for r in rows if r["outcome"]==spec["primary_outcome"] and r["model_id"] in spec["group_models"]]
    for row,q in zip(groups,benjamini_hochberg([float(r["permutation_p_two_sided"]) for r in groups])): row["bh_q_value"]=q; row["fdr_10pct_reject"]=int(q<=.10)
    controls=architecture_controls(profile_rows); sensitivities=[]; base={r["model_id"]:r for r in groups}
    variants=[("rank_based_outcomes",assets,"rank",None),("market_core_only",[a for a in assets if profiles[a]["selection_tier"]=="market_core"],"level",None),("exclude_application_tokens",[a for a in assets if profiles[a]["architecture_context"]!="NA"],"level",None),("architecture_indicator_controls",assets,"level",controls),("winsorize_continuous_outcomes_at_5_and_95_percent",assets,"winsor",None)]
    for name,subset,transform,control in variants:
        for predictor in spec["group_models"]:
            result=estimate(subset,profiles,outcomes,spec["primary_outcome"],[predictor],transform,control); coefficient=result["fit"][1] if result["fit"] else None; baseline=float(base[predictor]["coefficients"].split("|")[0])
            sensitivities.append({"sensitivity":name,"model_id":predictor,"n":result["n"],"coefficient":coefficient,"loo_rmse":result["loo_rmse"],"same_direction_as_baseline":int(coefficient is not None and (coefficient>=0)==(baseline>=0))})
    primary=[r for r in rows if r["outcome"]==spec["primary_outcome"]]; breadth=next(r for r in primary if r["model_id"]=="raw_function_breadth"); best=min(groups,key=lambda r:r["loo_rmse"]); stable={n:sum(r["same_direction_as_baseline"] for r in sensitivities if r["model_id"]==n) for n in spec["group_models"]}
    summary={"status":"post_pilot_exploratory_h8_verified_universe_complete","specification_version":spec["document_version"],"assets_in_classification_universe":len(assets),"coverage":coverage,"primary_outcome":spec["primary_outcome"],"raw_breadth_loo_rmse":breadth["loo_rmse"],"best_single_group_model":best["model_id"],"best_single_group_loo_rmse":best["loo_rmse"],"best_group_beats_raw_breadth":best["loo_rmse"]<breadth["loo_rmse"],"fdr_10pct_rejections":[r["model_id"] for r in groups if r["fdr_10pct_reject"]],"direction_stability_out_of_five":stable,"decision_rule_result":"theory_groups_favored" if best["loo_rmse"]<breadth["loo_rmse"] and stable[best["model_id"]]>=4 else "theory_groups_not_favored","interpretation":"Exploratory cross-sectional association and prediction only; no causal claim."}
    return rows,sensitivities,summary


def run(repo: Path):
    spec=json.loads((repo/"config/crypto_h8_verified_universe.json").read_text()); rows,sensitivities,summary=build(spec,read_csv(repo/spec["classification_input"]),read_csv(repo/"data/processed/00_foundation/market_daily_coinpaprika.csv"),read_csv(repo/spec["market_input"]))
    out=repo/"data/processed/02_valuation"; out.mkdir(parents=True,exist_ok=True)
    write_csv(out/"crypto_h8_verified_universe_results.csv",rows)
    write_csv(out/"crypto_h8_verified_universe_sensitivities.csv",sensitivities)
    (out/"crypto_h8_verified_universe_summary.json").write_text(json.dumps(summary,indent=2)+"\n"); return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--repo",type=Path,default=Path.cwd()); print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
