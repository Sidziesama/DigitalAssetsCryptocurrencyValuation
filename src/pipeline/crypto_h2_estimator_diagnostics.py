from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


POOLED_COLUMNS = (
    "log1p_fees_usd_lag1",
    "h2_active_capture",
    "fees_x_capture",
    "fees_x_application_scope",
)
CHAIN_COLUMNS = ("log1p_fees_usd_lag1", "fees_x_capture")


def number(value: Any) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def matrix_rank(matrix: list[list[float]], tolerance: float = 1e-10) -> int:
    if not matrix:
        return 0
    work = [row[:] for row in matrix]
    rows, columns = len(work), len(work[0])
    scale = max((abs(value) for row in work for value in row), default=0.0)
    threshold = tolerance * max(1.0, scale)
    rank = pivot_row = 0
    for column in range(columns):
        pivot = max(range(pivot_row, rows), key=lambda row: abs(work[row][column]), default=pivot_row)
        if pivot_row >= rows or abs(work[pivot][column]) <= threshold:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        pivot_value = work[pivot_row][column]
        for row in range(pivot_row + 1, rows):
            factor = work[row][column] / pivot_value
            if abs(factor) <= threshold:
                continue
            for later_column in range(column, columns):
                work[row][later_column] -= factor * work[pivot_row][later_column]
        rank += 1
        pivot_row += 1
        if pivot_row == rows:
            break
    return rank


def two_way_demean(rows: list[dict[str, Any]], columns: tuple[str, ...]) -> list[list[float]]:
    asset_values: dict[str, list[list[float]]] = defaultdict(list)
    date_values: dict[str, list[list[float]]] = defaultdict(list)
    vectors=[]
    for row in rows:
        vector=[float(row[column]) for column in columns]
        vectors.append(vector); asset_values[row["asset_id"]].append(vector); date_values[row["date"]].append(vector)
    overall=[statistics.fmean(vector[index] for vector in vectors) for index in range(len(columns))]
    asset_means={key:[statistics.fmean(vector[index] for vector in values) for index in range(len(columns))] for key,values in asset_values.items()}
    date_means={key:[statistics.fmean(vector[index] for vector in values) for index in range(len(columns))] for key,values in date_values.items()}
    return [[vector[index]-asset_means[row["asset_id"]][index]-date_means[row["date"]][index]+overall[index] for index in range(len(columns))] for row,vector in zip(rows,vectors)]


def eligible(rows:list[dict[str,str]],outcome:str,scope:str|None=None)->list[dict[str,Any]]:
    selected=[]
    for row in rows:
        if scope and row.get("fee_scope")!=scope: continue
        fields=(outcome,*POOLED_COLUMNS,"h2_active_capture","application_protocol_scope")
        values={field:number(row.get(field)) for field in fields}
        if any(value is None for value in values.values()): continue
        selected.append({**row,**values})
    return selected


def diagnose(name:str,rows:list[dict[str,Any]],columns:tuple[str,...])->dict[str,Any]:
    assets=sorted({row["asset_id"] for row in rows}); scopes=sorted({row["fee_scope"] for row in rows})
    dates=sorted({row["date"] for row in rows}); per_asset={asset:sum(row["asset_id"]==asset for row in rows) for asset in assets}; per_date={day:sum(row["date"]==day for row in rows) for day in dates}
    balanced=bool(rows) and len(set(per_asset.values()))==1 and len(set(per_date.values()))==1 and len(rows)==len(assets)*len(dates)
    transformed=two_way_demean(rows,columns); rank=matrix_rank(transformed)
    nonzero=[sum(value*value for value in column)>1e-12 for column in zip(*transformed)] if transformed else []
    return {"specification":name,"rows":len(rows),"assets":len(assets),"dates":len(dates),"balanced_panel":balanced,"asset_ids":assets,"scopes":scopes,"columns":list(columns),"two_way_fe_rank":rank,"expected_rank":len(columns),"nonzero_within_columns":dict(zip(columns,nonzero)),"full_rank":rank==len(columns)}


def build(rows:list[dict[str,str]])->tuple[list[dict[str,Any]],dict[str,Any]]:
    coverage=[]
    for asset_id in sorted({row["asset_id"] for row in rows}):
        asset_rows=[row for row in rows if row["asset_id"]==asset_id and number(row.get("log1p_fees_usd_lag1")) is not None]
        fees=[number(row["log1p_fees_usd_lag1"]) for row in asset_rows]
        coverage.append({"asset_id":asset_id,"fee_scope":next((row["fee_scope"] for row in asset_rows),""),"fee_rows":len(asset_rows),"first_date":min((row["date"] for row in asset_rows),default=""),"last_date":max((row["date"] for row in asset_rows),default=""),"log_fee_sd":statistics.stdev(fees) if len(fees)>1 else None,"capture_values":"|".join(str(value) for value in sorted({int(float(row["h2_active_capture"])) for row in asset_rows if row.get("h2_active_capture") not in {None,""}}))})

    level=eligible(rows,"log_market_cap_usd"); forward=eligible(rows,"forward_log_return_7d")
    diagnostics=[
        diagnose("pooled_market_cap",level,POOLED_COLUMNS),
        diagnose("pooled_forward_return",forward,POOLED_COLUMNS),
        diagnose("chain_market_cap",eligible(rows,"log_market_cap_usd","chain"),CHAIN_COLUMNS),
        diagnose("chain_forward_return",eligible(rows,"forward_log_return_7d","chain"),CHAIN_COLUMNS),
    ]
    application_level=eligible(rows,"log_market_cap_usd","application_protocol")
    leave_one_out=[]
    for asset_id in sorted({row["asset_id"] for row in level}):
        subset=[row for row in level if row["asset_id"]!=asset_id]
        result=diagnose(f"pooled_market_cap_without_{asset_id}",subset,POOLED_COLUMNS)
        leave_one_out.append({"excluded_asset":asset_id,"rows":result["rows"],"assets":result["assets"],"balanced_panel":result["balanced_panel"],"scopes":result["scopes"],"two_way_fe_rank":result["two_way_fe_rank"],"full_rank":result["full_rank"]})
    primary_pass=all(item["full_rank"] and item["balanced_panel"] for item in diagnostics)
    loo_pass=all(item["full_rank"] and item["balanced_panel"] and len(item["scopes"])==2 for item in leave_one_out)
    summary={
        "status":"pass_with_small_sample_limits" if primary_pass and loo_pass else "blocked_design_matrix_failure",
        "rows":len(rows),"assets":len(coverage),"scope_counts":{"chain":sum(row["fee_scope"]=="chain" for row in coverage),"application_protocol":sum(row["fee_scope"]=="application_protocol" for row in coverage)},
        "diagnostics":diagnostics,"leave_one_asset_out":leave_one_out,
        "application_scope":{"assets":len({row["asset_id"] for row in application_level}),"rows":len(application_level),"inference":"descriptive_only"},
        "guardrails":["Rank checks use asset-and-date-demeaned regressors and do not estimate hypothesis coefficients.","Two application assets cannot support reliable clustered inference.",f"{len(coverage)} total asset clusters still require wild-cluster-bootstrap inference and exploratory interpretation."]
    }
    return coverage,summary


def read_rows(path:Path)->list[dict[str,str]]:
    with path.open(newline="",encoding="utf-8") as handle: return list(csv.DictReader(handle))


def run(repo:Path)->dict[str,Any]:
    coverage,summary=build(read_rows(repo/"data/processed/empirical/crypto_h2_exploratory_daily.csv"))
    out=repo/"data/processed/empirical"; out.mkdir(parents=True,exist_ok=True)
    with (out/"crypto_h2_estimator_diagnostics.csv").open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(coverage[0]),lineterminator="\n"); writer.writeheader(); writer.writerows(coverage)
    (out/"crypto_h2_estimator_diagnostics.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Audit H2 estimator feasibility without estimating hypothesis coefficients")
    parser.add_argument("--repo",type=Path,default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
