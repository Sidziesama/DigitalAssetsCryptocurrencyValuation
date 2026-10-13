from __future__ import annotations

import argparse, csv, json
from datetime import date
from pathlib import Path
from typing import Any


def add_month(value: date) -> date:
    return date(value.year+(value.month==12),1 if value.month==12 else value.month+1,value.day)


def market_supply(rows: list[dict[str,str]], asset: str, event_day: date) -> tuple[float|None,str|None]:
    eligible=[]
    for row in rows:
        if row.get("asset_id")!=asset or row.get("date","")>event_day.isoformat(): continue
        try:
            price=float(row["price_usd"]); cap=float(row["market_cap_usd"])
            if price>0 and cap>0: eligible.append((row["date"],cap/price))
        except (TypeError,ValueError,KeyError): pass
    return (eligible[-1][1],eligible[-1][0]) if eligible else (None,None)


def build(spec: dict[str,Any], sources: dict[str,Any], market: list[dict[str,str]]) -> tuple[list[dict[str,Any]],dict[str,Any]]:
    if spec.get("status")!="frozen_before_supply_event_collection_and_estimation": raise ValueError("H3 event design must be frozen")
    threshold=float(spec["event_selection"]["minimum_impact_share_of_pre_event_circulating_supply"]); start=date.fromisoformat(spec["market_window"]["start"]); end=date.fromisoformat(spec["market_window"]["end"])
    rows=[]
    for source in sources["sources"]:
        source_type=source.get("source_type","")
        if source_type=="official_unlock_formula" or (source["asset_id"]=="crypto_arb" and "first_monthly_post_cliff_date" in source):
            asset=source["asset_id"]
            prefix=source.get("event_id_prefix",asset.removeprefix("crypto_"))
            amount=source["locked_allocation_tokens"]*(1-source["initial_cliff_share"])/source["remaining_monthly_periods"]
            day=date.fromisoformat(source["first_monthly_post_cliff_date"]); last=date.fromisoformat(source["last_monthly_date"])
            while day<=last:
                if start<=day<=end:
                    supply,supply_date=market_supply(market,asset,day); share=amount/supply if supply else None; material=share is not None and share>=threshold
                    rows.append({"event_id":f"{prefix}_monthly_unlock_{day.isoformat()}","asset_id":asset,"event_date":day.isoformat(),"event_type":source.get("event_type","scheduled_unlock"),"supply_shock_direction":"increase","expected_return_sign":"negative","gross_token_impact":amount,"pre_event_circulating_supply":supply,"supply_measurement_date":supply_date,"impact_share":share,"primary_source_url":source["source_url"],"exact_date_verified":1,"quantity_verified":1,"material":int(material),"contaminated":0,"primary_eligible":int(material),"exclusion_reason":"" if material else "below_materiality_or_missing_supply_denominator"})
                day=add_month(day)
        elif source.get("candidate_status","").startswith("excluded_") or (source["asset_id"]=="crypto_sui" and "events" not in source):
            rows.append({"event_id":source.get("candidate_id",f'{source["asset_id"].removeprefix("crypto_")}_excluded_candidate'),"asset_id":source["asset_id"],"event_date":"","event_type":source.get("event_type",""),"supply_shock_direction":source.get("supply_shock_direction","increase"),"expected_return_sign":source.get("expected_return_sign","negative"),"gross_token_impact":"","pre_event_circulating_supply":"","supply_measurement_date":"","impact_share":"","primary_source_url":source["source_url"],"exact_date_verified":0,"quantity_verified":int(bool(source.get("quantity_verified",1))),"material":"","contaminated":"","primary_eligible":0,"exclusion_reason":source.get("exclusion_reason","official_source_has_no_exact_effective_date_and_quantity")})
        elif source_type=="official_completed_event_records" or "events" in source:
            for event in source["events"]:
                day=date.fromisoformat(event["event_date"])
                if not start<=day<=end: continue
                amount=float(event["gross_token_impact"])
                asset=source["asset_id"]
                supply,supply_date=market_supply(market,asset,day); share=amount/supply if supply else None; material=share is not None and share>=threshold
                direction=event.get("supply_shock_direction",source.get("supply_shock_direction","decrease"))
                expected=event.get("expected_return_sign",source.get("expected_return_sign","positive" if direction=="decrease" else "negative"))
                rows.append({"event_id":event["event_id"],"asset_id":asset,"event_date":day.isoformat(),"event_type":event.get("event_type",source.get("event_type","one_time_burn")),"supply_shock_direction":direction,"expected_return_sign":expected,"gross_token_impact":amount,"pre_event_circulating_supply":supply,"supply_measurement_date":supply_date,"impact_share":share,"primary_source_url":event["source_url"],"exact_date_verified":1,"quantity_verified":1,"material":int(material),"contaminated":int(bool(event.get("contaminated",0))),"primary_eligible":int(material and not event.get("contaminated",0)),"exclusion_reason":"" if material and not event.get("contaminated",0) else ("known_event_window_contamination" if event.get("contaminated",0) else "below_materiality_or_missing_supply_denominator")})
    eligible=[r for r in rows if r["primary_eligible"]==1]
    assets=sorted({r["asset_id"] for r in eligible})
    summary={"status":"h3_supply_event_ledger_ready","candidate_rows":len(rows),"eligible_events":len(eligible),"eligible_assets":assets,"excluded_candidates":sum(r["primary_eligible"]==0 for r in rows),"event_dates_observed_before_outcomes":True,"next_gate":("Multiasset gate passed; estimate with asset-level randomization so repeated events are not treated as independent." if len(assets)>=2 else "At least two assets with eligible, uncontaminated events are required for pooled H3 inference; single-asset estimates remain descriptive.")}
    return rows,summary


def run(repo: Path) -> dict[str,Any]:
    spec=json.loads((repo/"config/crypto_h3_supply_event_study.json").read_text()); sources=json.loads((repo/"config/crypto_h3_supply_sources.json").read_text())
    with (repo/"data/processed/00_foundation/market_daily_coinpaprika.csv").open(newline="",encoding="utf-8") as handle: market=list(csv.DictReader(handle))
    rows,summary=build(spec,sources,market); out=repo/"data/processed/02_valuation"; fields=list(rows[0])
    with (out/"crypto_h3_supply_event_ledger.csv").open("w",newline="",encoding="utf-8") as handle: writer=csv.DictWriter(handle,fieldnames=fields,lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    (out/"crypto_h3_supply_event_ledger.json").write_text(json.dumps(summary,indent=2)+"\n"); return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--repo",type=Path,default=Path.cwd()); print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
