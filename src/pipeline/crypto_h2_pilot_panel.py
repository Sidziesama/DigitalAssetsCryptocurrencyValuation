from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from src.pipeline.historical import write_rows


def validate_spec(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1 or spec.get("status") != "draft_not_frozen":
        raise ValueError("unsupported H2/H8 pilot preregistration")
    start=date.fromisoformat(spec["analysis_window"]["start"]); end=date.fromisoformat(spec["analysis_window"]["end"])
    if end < start or end > date.fromisoformat(spec["as_of"]):
        raise ValueError("invalid or forward-looking analysis window")
    market=spec.get("sample",{}).get("market_assets",[]); activity=spec.get("sample",{}).get("activity_assets",[])
    if len(market)!=6 or len(market)!=len(set(market)) or not set(activity)<=set(market):
        raise ValueError("invalid frozen pilot samples")
    if spec["sample"].get("no_outcome_based_replacement") is not True:
        raise ValueError("outcome-based asset replacement must be prohibited")
    if spec.get("H2",{}).get("primary_status") != "candidate_fee_layer_ready_preregistration_freeze_pending":
        raise ValueError("primary H2 must remain blocked pending preregistration freeze")
    h2=spec["H2"]; scope=h2.get("scope_design",{}); models=h2.get("models",{}); errors=h2.get("standard_errors",{})
    if scope.get("scope_indicator")!="application_protocol_scope" or len(scope.get("sensitivities",[]))!=4 or not scope.get("pooling_guardrail"):
        raise ValueError("H2 fee-scope design must predeclare the indicator, four sensitivities, and pooling guardrail")
    if set(models)!={"market_cap","forward_return","secondary"}:
        raise ValueError("H2 models must predeclare market-cap, forward-return, and secondary specifications")
    if "wild-cluster-bootstrap" not in errors.get("primary","") or "six assets" not in errors.get("small_sample_guardrail",""):
        raise ValueError("H2 standard errors must address six-cluster pilot inference")
    if spec.get("H8",{}).get("status") != "blocked_until_all_ten_codes_are_evidence_backed":
        raise ValueError("H8 must remain blocked until all ten codes are evidenced")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(value: Any, allow_zero: bool = False) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) and (result >= 0 if allow_zero else result > 0) else None
    except (TypeError, ValueError):
        return None


def mechanism_state(events: list[dict[str, Any]], asset_id: str, code: str, day: date) -> int | None:
    eligible = [event for event in events if event["asset_id"] == asset_id and event["code"] == code and date.fromisoformat(event["effective_from"]) <= day]
    if not eligible:
        return None
    return int(max(eligible, key=lambda event: event["effective_from"])["value"])


def build(spec: dict[str, Any], market_rows: list[dict[str, str]], activity_rows: list[dict[str, str]], events: list[dict[str, Any]], fee_rows:list[dict[str,str]]|None=None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    validate_spec(spec)
    start = date.fromisoformat(spec["analysis_window"]["start"]); end = date.fromisoformat(spec["analysis_window"]["end"])
    market_assets = set(spec["sample"]["market_assets"]); activity_assets = set(spec["sample"]["activity_assets"])
    market = {(row["asset_id"], date.fromisoformat(row["date"])): row for row in market_rows if row["asset_id"] in market_assets and start <= date.fromisoformat(row["date"]) <= end}
    activity = {(row["asset_id"], date.fromisoformat(row["date"])): row for row in activity_rows if row["asset_id"] in activity_assets}
    fees = {(row["asset_id"], date.fromisoformat(row["date"])): row for row in (fee_rows or [])}
    output=[]
    for (asset_id, day), row in sorted(market.items()):
        price=number(row.get("price_usd")); cap=number(row.get("market_cap_usd"))
        previous=market.get((asset_id,day-timedelta(days=1))); future=market.get((asset_id,day+timedelta(days=7)))
        previous_price=number(previous.get("price_usd")) if previous else None; future_price=number(future.get("price_usd")) if future else None
        daily_return=math.log(price/previous_price) if price and previous_price else None
        forward_return=math.log(future_price/price) if price and future_price else None
        trailing=[]
        for offset in range(29,-1,-1):
            current_day=day-timedelta(days=offset); current=market.get((asset_id,current_day)); prior=market.get((asset_id,current_day-timedelta(days=1)))
            current_price=number(current.get("price_usd")) if current else None; prior_price=number(prior.get("price_usd")) if prior else None
            if current_price and prior_price: trailing.append(math.log(current_price/prior_price))
        volatility=statistics.stdev(trailing)*math.sqrt(365) if len(trailing)==30 else None
        lag=activity.get((asset_id,day-timedelta(days=1))); addresses=number(lag.get("active_addresses"),True) if lag else None; transactions=number(lag.get("transaction_count"),True) if lag else None
        fee_lag=fees.get((asset_id,day-timedelta(days=1))); fee_value=number(fee_lag.get("fees_usd"),True) if fee_lag else None; revenue=number(fee_lag.get("protocol_revenue_usd"),True) if fee_lag else None; holder_revenue=number(fee_lag.get("holders_revenue_usd"),True) if fee_lag else None
        burn=mechanism_state(events,asset_id,"VA_BURN",day); protocol=mechanism_state(events,asset_id,"VA_PROTOCOL",day)
        capture=int(bool(burn or protocol)) if burn is not None and protocol is not None else None
        log_addresses=math.log1p(addresses) if addresses is not None else None; log_transactions=math.log1p(transactions) if transactions is not None else None
        log_fees=math.log1p(fee_value) if fee_value is not None else None; log_revenue=math.log1p(revenue) if revenue is not None else None; log_holder_revenue=math.log1p(holder_revenue) if holder_revenue is not None else None
        output.append({
            "asset_id":asset_id,"date":day.isoformat(),"price_usd":price,"market_cap_usd":cap,
            "log_market_cap_usd":math.log(cap) if cap else None,"daily_log_return":daily_return,
            "forward_log_return_7d":forward_return,"realized_volatility_30d_annualized":volatility,
            "va_burn_effective":burn,"va_protocol_effective":protocol,"h2_active_capture":capture,
            "active_addresses_lag1":addresses,"transaction_count_lag1":transactions,
            "log1p_active_addresses_lag1":log_addresses,"log1p_transaction_count_lag1":log_transactions,
            "active_addresses_x_capture":log_addresses*capture if log_addresses is not None and capture is not None else None,
            "transaction_count_x_capture":log_transactions*capture if log_transactions is not None and capture is not None else None,
            "fee_scope":fee_lag.get("scope") if fee_lag else None,"economic_system":fee_lag.get("economic_system") if fee_lag else None,
            "application_protocol_scope":int(fee_lag.get("scope")=="application_protocol") if fee_lag else None,
            "fees_usd_lag1":fee_value,"protocol_revenue_usd_lag1":revenue,"holders_revenue_usd_lag1":holder_revenue,
            "log1p_fees_usd_lag1":log_fees,"log1p_protocol_revenue_usd_lag1":log_revenue,"log1p_holders_revenue_usd_lag1":log_holder_revenue,
            "fees_x_capture":log_fees*capture if log_fees is not None and capture is not None else None,
            "fees_x_application_scope":log_fees*int(fee_lag.get("scope")=="application_protocol") if log_fees is not None and fee_lag else None,
            "h2_exploratory_level_eligible":int(cap is not None and log_addresses is not None and log_transactions is not None and capture is not None),
            "h2_exploratory_forward_return_eligible":int(forward_return is not None and log_addresses is not None and log_transactions is not None and capture is not None),
            "h2_fee_level_eligible":int(cap is not None and log_fees is not None and capture is not None),
            "h2_fee_forward_return_eligible":int(forward_return is not None and log_fees is not None and capture is not None),
        })
    per_asset=defaultdict(lambda:{"rows":0,"activity_rows":0,"forward_return_rows":0,"fee_rows":0,"fee_forward_return_rows":0})
    for row in output:
        item=per_asset[row["asset_id"]]; item["rows"]+=1; item["activity_rows"]+=row["h2_exploratory_level_eligible"]; item["forward_return_rows"]+=row["h2_exploratory_forward_return_eligible"]; item["fee_rows"]+=row["h2_fee_level_eligible"]; item["fee_forward_return_rows"]+=row["h2_fee_forward_return_eligible"]
    summary={
        "status":"candidate_h2_fee_panel_ready_preregistration_freeze_pending",
        "market_assets":len(market_assets),"activity_assets":len(activity_assets),"rows":len(output),
        "level_eligible_rows":sum(row["h2_exploratory_level_eligible"] for row in output),
        "forward_return_eligible_rows":sum(row["h2_exploratory_forward_return_eligible"] for row in output),
        "fee_level_eligible_rows":sum(row["h2_fee_level_eligible"] for row in output),
        "fee_forward_return_eligible_rows":sum(row["h2_fee_forward_return_eligible"] for row in output),
        "per_asset":dict(sorted(per_asset.items())),
        "scope_design_predeclared":True,
        "primary_h2_blocker":"Scope design and estimator diagnostics are complete, but the draft must remain exploratory until the preregistration is frozen.",
        "guardrail":"Do not pool chain and application observations without the predeclared scope indicator and interactions; fees, protocol revenue, and holder revenue remain separate variables."
    }
    return output,summary


def run(repo: Path) -> dict[str, Any]:
    spec=json.loads((repo/"config/preregistration_h2_h8_pilot.json").read_text())
    events=json.loads((repo/"config/crypto_mechanism_events.json").read_text())["events"]
    rows,summary=build(spec,read_csv(repo/"data/processed/historical/market_daily_coinpaprika.csv"),read_csv(repo/"data/processed/historical/crypto_fundamentals_daily_coinmetrics.csv"),events,read_csv(repo/"data/processed/empirical/crypto_fee_fundamentals_daily.csv"))
    out=repo/"data/processed/empirical"; out.mkdir(parents=True,exist_ok=True)
    write_rows(out/"crypto_h2_exploratory_daily.csv",rows,list(rows[0]))
    (out/"crypto_h2_exploratory_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Build a no-look-ahead exploratory H2 activity-capture panel")
    parser.add_argument("--repo",type=Path,default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
