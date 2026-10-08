from __future__ import annotations

import argparse, csv, html, json, math, statistics
from datetime import date
from pathlib import Path
from typing import Any

from .crypto_h3_supply_event_ledger import build as build_ledger
from .crypto_h8_verified_universe import ols


def number(value: Any) -> float|None:
    try: result=float(value)
    except (TypeError,ValueError): return None
    return result if math.isfinite(result) else None


def build(spec: dict[str,Any], ledger: list[dict[str,str]], panel: list[dict[str,str]]):
    by_asset={}
    for row in panel:
        ret=number(row.get("log_return")); market=number(row.get("market_ew_log_return"))
        if ret is not None and market is not None: by_asset.setdefault(row["asset_id"],[]).append((date.fromisoformat(row["date"]),ret,market))
    for rows in by_asset.values(): rows.sort()
    primary=tuple(spec["estimation"]["primary_event_window_trading_days"]); secondary=[tuple(x) for x in spec["estimation"]["secondary_event_windows_trading_days"]]; windows=[primary,*secondary]
    event_rows=[]; paths=[]
    for event in ledger:
        if str(event.get("primary_eligible")) not in {"1","True","true"}: continue
        series=by_asset.get(event["asset_id"],[]); event_day=date.fromisoformat(event["event_date"]); position=next((i for i,row in enumerate(series) if row[0]>=event_day),None)
        if position is None: continue
        lo,hi=spec["estimation"]["estimation_window_trading_days"]; estimation=series[max(0,position+lo):max(0,position+hi+1)]
        if len(estimation)<spec["estimation"]["minimum_estimation_observations"]: continue
        fit=ols([[r[2]] for r in estimation],[r[1] for r in estimation])
        if fit is None: continue
        abnormal={offset:series[position+offset][1]-(fit[0]+fit[1]*series[position+offset][2]) for offset in range(-14,15) if 0<=position+offset<len(series)}
        paths.append({"event_id":event["event_id"],**abnormal})
        record={"event_id":event["event_id"],"asset_id":event["asset_id"],"event_date":event["event_date"],"impact_share":event["impact_share"],"estimation_observations":len(estimation),"market_beta":fit[1]}
        for start,end in windows:
            values=[abnormal[i] for i in range(start,end+1) if i in abnormal]; record[f"car_{start}_{end}"]=sum(values) if len(values)==end-start+1 else None
        record["primary_sign_matches_h3"]=int(record[f"car_{primary[0]}_{primary[1]}"]<0) if record[f"car_{primary[0]}_{primary[1]}"] is not None else ""
        event_rows.append(record)
    curve=[]
    for offset in range(-14,15):
        values=[]
        for path in paths:
            available=[path[i] for i in range(-14,offset+1) if i in path]
            if len(available)==offset+15: values.append(sum(available))
        curve.append({"event_time_trading_day":offset,"mean_cumulative_abnormal_log_return":statistics.fmean(values) if values else None,"events":len(values)})
    assets=sorted({r["asset_id"] for r in event_rows}); primary_key=f"car_{primary[0]}_{primary[1]}"; primary_values=[r[primary_key] for r in event_rows if r[primary_key] is not None]
    summary={"status":"h3_single_asset_descriptive_event_analysis_complete" if len(assets)<2 else "h3_multi_asset_event_analysis_ready","events_estimated":len(event_rows),"assets":assets,"pooled_inference_permitted":len(assets)>=2,"mean_primary_car":statistics.fmean(primary_values) if primary_values else None,"median_primary_car":statistics.median(primary_values) if primary_values else None,"events_matching_negative_h3_sign":sum(r["primary_sign_matches_h3"]==1 for r in event_rows),"primary_window":list(primary),"interpretation":"Repeated events from one asset are dependent observations. Until a second asset qualifies, estimates are descriptive and no pooled p-value is reported."}
    return event_rows,curve,summary


def chart(curve: list[dict[str,Any]], summary: dict[str,Any]) -> str:
    width,height=900,460; left,right,top,bottom=85,35,70,65; values=[r["mean_cumulative_abnormal_log_return"] for r in curve if r["mean_cumulative_abnormal_log_return"] is not None]; ymin,ymax=min(values+[0]),max(values+[0]); pad=max((ymax-ymin)*.12,.005); ymin-=pad; ymax+=pad
    x=lambda v:left+(v+14)/28*(width-left-right); y=lambda v:top+(ymax-v)/(ymax-ymin)*(height-top-bottom)
    points=" ".join(f"{x(r['event_time_trading_day']):.1f},{y(r['mean_cumulative_abnormal_log_return']):.1f}" for r in curve if r["mean_cumulative_abnormal_log_return"] is not None)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Mean cumulative abnormal return around Arbitrum monthly unlocks">','<rect width="100%" height="100%" fill="#ffffff"/>',f'<text x="24" y="30" font-family="Arial" font-size="20" font-weight="600" fill="#17212b">H3 descriptive event path: ARB monthly unlocks</text>',f'<text x="24" y="53" font-family="Arial" font-size="12" fill="#647383">{summary["events_estimated"]} repeated events from one asset; descriptive, not independent pooled evidence.</text>',f'<rect x="{left}" y="{top}" width="{width-left-right}" height="{height-top-bottom}" fill="none" stroke="#d7dde3"/>',f'<line x1="{left}" y1="{y(0):.1f}" x2="{width-right}" y2="{y(0):.1f}" stroke="#647383"/>',f'<line x1="{x(0):.1f}" y1="{top}" x2="{x(0):.1f}" y2="{height-bottom}" stroke="#d99a2b" stroke-width="2"/>',f'<polyline points="{points}" fill="none" stroke="#3478b8" stroke-width="3"/>']
    for tick in (-14,-7,0,7,14): parts.append(f'<text x="{x(tick):.1f}" y="{height-bottom+25}" text-anchor="middle" font-family="Arial" font-size="12" fill="#17212b">{tick}</text>')
    parts += [f'<text x="{(left+width-right)/2}" y="{height-15}" text-anchor="middle" font-family="Arial" font-size="12" fill="#647383">Trading days from unlock</text>',f'<text x="18" y="{(top+height-bottom)/2}" transform="rotate(-90 18 {(top+height-bottom)/2})" text-anchor="middle" font-family="Arial" font-size="12" fill="#647383">Mean cumulative abnormal log return</text>','</svg>']
    return "\n".join(parts)+"\n"


def run(repo: Path):
    spec=json.loads((repo/"config/crypto_h3_supply_event_study.json").read_text())
    with (repo/"data/processed/02_valuation/crypto_h3_supply_event_ledger.csv").open(newline="",encoding="utf-8") as h: ledger=list(csv.DictReader(h))
    with (repo/spec["market_input"]).open(newline="",encoding="utf-8") as h: panel=list(csv.DictReader(h))
    events,curve,summary=build(spec,ledger,panel); out=repo/"data/processed/02_valuation"
    for name,rows in [("crypto_h3_supply_event_estimates.csv",events),("crypto_h3_supply_event_curve.csv",curve)]:
        with (out/name).open("w",newline="",encoding="utf-8") as h: writer=csv.DictWriter(h,fieldnames=list(rows[0]),lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    (out/"crypto_h3_supply_event_analysis.json").write_text(json.dumps(summary,indent=2)+"\n")
    fig=repo/"research/figures/crypto-h3-supply-event-path.svg"; fig.write_text(chart(curve,summary),encoding="utf-8")
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--repo",type=Path,default=Path.cwd()); print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
