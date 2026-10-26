"""Gated H4 estimator. Real-data inference requires both complete stake series."""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
from datetime import date,timedelta
from pathlib import Path

from .crypto_function_risk_exposure import benjamini_hochberg
from .crypto_h4_analysis_readiness import validate as validate_design
from .crypto_h8_verified_universe import number,read_csv,write_csv
from .crypto_h2_small_cluster_inference import wild_cluster_test


def index_rows(rows,fields):
    result={}
    for row in rows:
        key=(row['asset_id'],row['date'])
        if key in result: raise ValueError('Duplicate asset-date observation')
        result[key]={**row,**{field:number(row.get(field)) for field in fields}}
    return result


def outcome_values(series,asset,day):
    observations=[]
    for k in range(90):
        value=series.get((asset,(day-timedelta(days=k)).isoformat()),{}).get('price_usd')
        observations.append(value if value is not None and value>0 else None)
    volatility=None; drawdown=None
    if all(v is not None for v in observations[:31]):
        returns=[math.log(observations[k]/observations[k+1]) for k in range(30)]
        volatility=st.pstdev(returns)*math.sqrt(365)
    if all(v is not None for v in observations):drawdown=observations[0]/max(observations)-1
    return volatility,drawdown


def build(spec,design,market_rows,price_rows,eth_rows,bnb_rows):
    validate_design(design)
    if spec.get('status')!='frozen_before_h4_estimation' or spec['predictor']!='staked_share_lag1':raise ValueError('H4 estimation details must be frozen')
    start,end=date.fromisoformat(design['study_start']),date.fromisoformat(design['study_end'])
    dates=[(start+timedelta(days=k)).isoformat() for k in range((end-start).days+1)]
    positive=design['primary_sample']['consensus_staking_assets']; controls=design['primary_sample']['structural_nonstaking_controls']; assets=positive+controls
    market=index_rows([r for r in market_rows if r['asset_id'] in assets],['market_cap_usd','price_usd','volume_24h_usd'])
    prices=index_rows([r for r in price_rows if r['asset_id'] in assets],['price_usd'])
    stake={};coverage=[]
    for asset,rows,role in [('crypto_eth',eth_rows,'consensus_active_effective_balance'),('crypto_bnb',bnb_rows,'consensus_stake_all_validator_pools')]:
        parsed=index_rows(rows,['total_staked_native_units']); valid={}
        for (a,d),row in parsed.items():
            value=row['total_staked_native_units']
            if a!=asset or row.get('measurement_role')!=role or value is None or value<=0:raise ValueError('Invalid stake amount, asset or measurement role')
            valid[d]=value
        stake[asset]=valid
        observed=sum(d in valid for d in dates)
        coverage.append({'asset_id':asset,'observed_days':observed,'required_days':len(dates),'complete':observed==len(dates)})
    result={'status':'h4_estimation_blocked_missing_stake','design_frozen_on':design['design_frozen_on'],'estimation_frozen_on':spec['freeze_date'],'window':{'start':str(start),'end':str(end)},'primary_assets':assets,'stake_coverage':coverage,'estimation_allowed':False,'common_days':0,'results':[],'absorbed_controls':spec['absorbed_control'],'inference':spec['inference'],'uncertainty':spec['uncertainty'],'guardrails':spec['guardrails'],'next_required':'Configure ETH_BEACON_ARCHIVE_API_URL locally and collect exact active effective balance for every study date. Historical validator access is required; do not paste credentials into research files.'}
    available=[]
    for d in dates:
        previous=(date.fromisoformat(d)-timedelta(days=1)).isoformat()
        ready=True
        for asset in assets:
            current=market.get((asset,d),{}); cap=current.get('market_cap_usd'); volume=current.get('volume_24h_usd')
            if cap is None or cap<=0 or volume is None or volume<0 or any(v is None for v in outcome_values(prices,asset,date.fromisoformat(d))):ready=False;break
            if asset in positive:
                prior=market.get((asset,previous),{})
                if not prior.get('market_cap_usd') or not prior.get('price_usd'):ready=False;break
        if ready:available.append(d)
    result['common_market_and_price_days_excluding_stake']=len(available)
    if not all(r['complete'] for r in coverage):return [],result
    panel=[]; omissions=[]
    for d in dates:
        day=date.fromisoformat(d); previous=(day-timedelta(days=1)).isoformat(); pending=[]
        for asset in assets:
            current=market.get((asset,d),{}); cap=current.get('market_cap_usd'); volume=current.get('volume_24h_usd')
            if cap is None or cap<=0 or volume is None or volume<0:break
            share=0.0
            if asset in positive:
                prior=market.get((asset,previous),{}); prior_cap=prior.get('market_cap_usd'); prior_price=prior.get('price_usd'); amount=stake[asset].get(previous)
                if amount is None or prior_cap is None or prior_cap<=0 or prior_price is None or prior_price<=0:break
                share=amount/(prior_cap/prior_price)
                if not 0<=share<=1:raise ValueError('Staked share outside [0,1]; verify denominator and units')
            vol,draw=outcome_values(prices,asset,day)
            if vol is None or draw is None:break
            pending.append({'asset_id':asset,'date':d,'staked_share_lag1':share,'log_market_cap':math.log(cap),'volume_to_market_cap':volume/cap,'realized_volatility_30d_annualized':vol,'drawdown_from_90d_high':draw})
        if len(pending)==len(assets):panel.extend(pending)
        else:omissions.append(d)
    common=len(panel)//len(assets);result.update({'common_days':common,'omitted_dates':omissions})
    if common<design['minimum_common_days']:
        result.update({'status':'h4_estimation_blocked_insufficient_common_days','next_required':'Resolve market, lagged denominator or historical USD price gaps; preserve the frozen minimum common-day rule.'})
        return panel,result
    results=[]
    for outcome in design['outcomes']:
        estimate=wild_cluster_test(panel,outcome,('staked_share_lag1','log_market_cap'),target='staked_share_lag1')
        estimate.update({'outcome':outcome,'effect_per_one_percentage_point_stake_share':estimate['coefficient']*.01})
        results.append(estimate)
    for row,q in zip(results,benjamini_hochberg([r['wild_cluster_bootstrap_p_two_sided'] for r in results])):row['bh_q_value']=q
    result.update({'status':'h4_exploratory_estimation_complete','estimation_allowed':True,'rows':len(panel),'results':results,'next_required':'Review three results and q-values together, two-positive-asset identification and chain-measurement differences. Do not read the coefficients causally.'})
    return panel,result


def report(result):
    lines=['# H4: staking, turnover and risk','',f"Status: `{result['status']}`.",'','H4 asks whether a larger staked share is associated with turnover, volatility or drawdown. ETH and BNB are the two consensus-staking assets; BTC, UNI and ARB are structural controls. Legacy stkAAVE remains a separate case.','','| Required staking input | Observed days | Required days | Complete |','|---|---:|---:|---|']
    for r in result['stake_coverage']:lines.append(f"| {r['asset_id']} | {r['observed_days']} | {r['required_days']} | {r['complete']} |")
    lines+=['',f"Common complete analysis days: {result['common_days']}.",'','The model uses asset and date fixed effects, lagged staked share and log capitalization. BTC returns are common across assets and are absorbed by date fixed effects. Volatility and drawdown use consecutive archived USD prices, including the pre-study warmup. No day is filled across missing observations.','','Inference enumerates 32 Rademacher assignments across five asset clusters. Its two-sided p-value resolution is 0.0625, and only two assets have positive stake. Exhaustive enumeration does not guarantee reliable small-sample inference. The three outcomes receive Benjamini–Hochberg correction.']
    lines+=['',f"Common market/price days before the stake gate: {result['common_market_and_price_days_excluding_stake']}."]
    if result['results']:
        lines+=['','| Outcome | Stake-share coefficient | Effect per 1pp stake share | Bootstrap p | BH q |','|---|---:|---:|---:|---:|']
        for r in result['results']:lines.append(f"| {r['outcome']} | {r['coefficient']:.6g} | {r['effect_per_one_percentage_point_stake_share']:.6g} | {r['wild_cluster_bootstrap_p_two_sided']:.4f} | {r['bh_q_value']:.4f} |")
    else:lines+=['','No empirical H4 coefficients have been estimated. Synthetic-data tests verify the implementation only; they are not research findings.']
    lines+=['',result['next_required'],'','Turnover is trading volume divided by capitalization, not order-book liquidity. Staked share measures chain-specific stake divided by inferred circulating supply, not total unavailable economic float; liquid-staking instruments can keep exposure tradeable.','']
    return '\n'.join(lines)


def run(repo:Path):
    spec=json.loads((repo/'config/crypto_h4_estimation.json').read_text());design=json.loads((repo/spec['parent_design']).read_text())
    def rows(path):return read_csv(repo/path) if (repo/path).exists() else []
    panel,result=build(spec,design,rows(spec['market_input']),rows(spec['price_input']),rows(spec['eth_input']),rows(spec['bnb_input']))
    out=repo/'data/processed/02_valuation'
    (out/'crypto_h4_estimation.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    if panel:write_csv(out/'crypto_h4_estimation_panel.csv',panel)
    (repo/'research/findings/crypto-h4-estimation.md').write_text(report(result))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path,default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
