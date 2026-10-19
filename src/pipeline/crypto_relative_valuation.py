"""Retrospective relative valuation with strictly held-out asset predictions."""
from __future__ import annotations

import argparse
import csv
import html
import json
import math
import statistics as st
from collections import defaultdict
from datetime import date
from pathlib import Path

from .crypto_h2_exploratory_estimates import solve
from .crypto_h8_verified_universe import number, read_csv, write_csv


def fit_predict(train, target, predictors, penalty, details=False):
    """Fit scaler and penalized regression using training observations alone."""
    means = [st.fmean(r[p] for r in train) for p in predictors]
    scales = [st.pstdev(r[p] for r in train) for p in predictors]
    def design(row):
        return [1.0] + [(row[p]-m)/s if s else 0.0 for p,m,s in zip(predictors,means,scales)]
    x = [design(r) for r in train]
    y = [r['mean_log_market_cap_usd'] for r in train]
    k = len(predictors)+1
    matrix = [[sum(r[i]*r[j] for r in x)+(penalty if i==j and i else 0) for j in range(k)] for i in range(k)]
    rhs = [sum(r[i]*v for r,v in zip(x,y)) for i in range(k)]
    coefficients = solve(matrix,rhs)
    terms={p:c*v for p,c,v in zip(predictors,coefficients[1:],design(target)[1:])}
    prediction=sum(c*v for c,v in zip(coefficients,design(target)))
    if details:
        return prediction, coefficients[0], terms
    return prediction


def collect(spec, profiles, market, fundamentals):
    if len(profiles)!=23 or len({r['asset_id'] for r in profiles})!=23 or any(r['classification_status']!='complete_human_verified' for r in profiles):
        raise ValueError('Requires 23 unique human-verified profiles')
    w=spec['window']; minimum=math.ceil(((date.fromisoformat(w['end'])-date.fromisoformat(w['start'])).days+1)*w['minimum_coverage_share'])
    caps=defaultdict(dict); vols=defaultdict(dict); fees=defaultdict(dict); holders=defaultdict(dict); scopes=defaultdict(set)
    for row in market:
        if w['start']<=row['date']<=w['end']:
            for field,store in [('market_cap_usd',caps),('volume_24h_usd',vols)]:
                value=number(row.get(field))
                if value is not None and value>0: store[row['asset_id']][row['date']]=value
    for row in fundamentals:
        if w['start']<=row['date']<=w['end']:
            for field,store in [('fees_usd_lag1',fees),('holders_revenue_usd_lag1',holders)]:
                value=number(row.get(field))
                if value is not None and value>=0: store[row['asset_id']][row['date']]=value
            if row.get('fee_scope'): scopes[row['asset_id']].add(row['fee_scope'])
    rows=[]; coverage=[]
    for profile in profiles:
        a=profile['asset_id']; coverage.append({'asset_id':a,'symbol':profile['symbol'],'cap_days':len(caps[a]),'volume_days':len(vols[a]),'fee_days':len(fees[a]),'minimum_days':minimum,'identity_eligible':int(len(caps[a])>=minimum),'fundamentals_eligible':int(len(caps[a])>=minimum and len(vols[a])>=minimum and len(fees[a])>=minimum and sum(fees[a].values())>0 and len(scopes[a])==1)})
        if not coverage[-1]['identity_eligible']: continue
        row={'asset_id':a,'symbol':profile['symbol'],'mean_log_market_cap_usd':st.fmean(math.log(v) for v in caps[a].values()),'raw_function_breadth':float(profile['raw_function_breadth']), **{g:float(profile[g]) for g in spec['groups']}}
        row['fundamentals_eligible']=coverage[-1]['fundamentals_eligible']
        row['fee_scope']=next(iter(scopes[a])) if len(scopes[a])==1 else ''
        if row['fundamentals_eligible']:
            row['log_mean_daily_fees']=math.log(st.fmean(fees[a].values()))
            row['log_mean_daily_volume']=math.log(st.fmean(vols[a].values()))
            row['application_scope']=float(row['fee_scope']=='application_protocol')
        for name,store in [('fees',fees),('holder_revenue',holders)]:
            common=set(caps[a]) & set(store[a])
            valid=[math.log(caps[a][d]/(365*store[a][d])) for d in sorted(common) if store[a][d]>0]
            row['log_multiple_'+name]=st.fmean(valid) if len(valid)>=minimum else None
        rows.append(row)
    return rows,coverage


def peer_multiples(spec, rows):
    results=[]
    for target in rows:
        own={g for g in spec['groups'] if target[g]}
        for metric in ['fees','holder_revenue']:
            applicable=bool(target['bundle_holder_capture']) if metric=='holder_revenue' else bool(target['bundle_transaction_service_demand'] or target['bundle_holder_capture'])
            candidates=[]
            for other in rows:
                if other['asset_id']==target['asset_id'] or not target['fee_scope'] or other['fee_scope']!=target['fee_scope']: continue
                if metric=='holder_revenue' and not other['bundle_holder_capture']: continue
                if metric=='fees' and not (other['bundle_transaction_service_demand'] or other['bundle_holder_capture']): continue
                groups={g for g in spec['groups'] if other[g]}; union=own|groups
                similarity=len(own&groups)/len(union) if union else 0
                if similarity>=spec['peers']['minimum_jaccard'] and other['log_multiple_'+metric] is not None: candidates.append(other)
            value=target['log_multiple_'+metric]
            status='not_applicable' if not applicable else 'target_data_unavailable' if value is None else 'insufficient_peers' if len(candidates)<spec['peers']['minimum_peers'] else 'measured'
            median=st.median(r['log_multiple_'+metric] for r in candidates) if status=='measured' else None
            results.append({'asset_id':target['asset_id'],'symbol':target['symbol'],'metric':metric,'state':status,'peers':'|'.join(sorted(r['symbol'] for r in candidates)),'peer_count':len(candidates),'own_multiple':math.exp(value) if applicable and value is not None else None,'peer_median_multiple':math.exp(median) if median is not None else None,'own_to_peer_ratio':math.exp(value-median) if median is not None else None})
    return results


def build(spec, profiles, market, fundamentals):
    if spec.get('status')!='frozen_before_relative_valuation_estimation' or spec['ridge_penalty']<=0: raise ValueError('Invalid frozen valuation specification')
    rows,coverage=collect(spec,profiles,market,fundamentals)
    estimates=[]; comparisons=[]
    for model in spec['models']:
        sample=[r for r in rows if model['sample']=='identity' or r['fundamentals_eligible']]
        if len(sample)<5: raise ValueError('At least five assets required for nested holdout diagnostics')
        predictors=spec['groups'] if model['predictors']==['all_groups'] else model['predictors']
        errors=[]
        for target in sample:
            train=[r for r in sample if r['asset_id']!=target['asset_id']]
            prediction,intercept,contributions=fit_predict(train,target,predictors,spec['ridge_penalty'],details=True)
            inner=sorted(abs(r['mean_log_market_cap_usd']-fit_predict([s for s in train if s['asset_id']!=r['asset_id']],r,predictors,spec['ridge_penalty'])) for r in train)
            band=inner[min(len(inner)-1,math.ceil(.9*len(inner))-1)]
            actual=target['mean_log_market_cap_usd']; error=actual-prediction; errors.append(error)
            estimates.append({'asset_id':target['asset_id'],'symbol':target['symbol'],'model_id':model['id'],'sample':model['sample'],'training_assets':len(train),'observed_geometric_mean_cap_usd':math.exp(actual),'held_out_implied_cap_usd':math.exp(prediction),'log_residual':error,'observed_to_model_ratio':math.exp(error),'empirical_band_low_usd':math.exp(prediction-band),'empirical_band_high_usd':math.exp(prediction+band),'empirical_band_log_halfwidth':band,'training_log_intercept':intercept,'centered_predictor_contributions_json':json.dumps(contributions,sort_keys=True)})
        comparisons.append({'model_id':model['id'],'sample':model['sample'],'assets':len(sample),'loao_rmse_log_cap':math.sqrt(st.fmean(e*e for e in errors)),'loao_mae_log_cap':st.fmean(abs(e) for e in errors)})
    for c in comparisons:
        benchmark=next(r for r in comparisons if r['model_id']==c['sample']+'_mean')
        c['rmse_improvement_vs_same_sample_mean']=1-c['loao_rmse_log_cap']/benchmark['loao_rmse_log_cap']
    return {'status':'exploratory_relative_valuation_complete','experiment_id':spec['experiment_id'],'freeze_date':spec['freeze_date'],'research_status':spec['research_status'],'window':spec['window'],'guardrails':spec['guardrails'],'uncertainty':spec['uncertainty'],'coverage':coverage,'models':comparisons,'asset_estimates':estimates,'peer_multiples':peer_multiples(spec,rows)}


def render(result):
    lines=['# Relative valuation: findings and asset models','',result['research_status'],'','The outcome is geometric mean market capitalization over the historical window. Each asset is excluded from its own model fit. Static classifications are retrospective descriptors; the result does not estimate a current price target.','','## What we tested','','Do economic functions improve prediction of relative network size, and does holder capture add information beyond fees, volume and fee scope? Fixed-penalty ridge regression limits model flexibility in these small samples.','','## What we found','','| Model | Assets | Held-out RMSE (log cap) | Improvement vs same-sample mean |','|---|---:|---:|---:|']
    for r in result['models']: lines.append(f"| {r['model_id']} | {r['assets']} | {r['loao_rmse_log_cap']:.3f} | {r['rmse_improvement_vs_same_sample_mean']:.1%} |")
    models={r['model_id']:r for r in result['models']}
    group_gain=1-models['identity_groups']['loao_rmse_log_cap']/models['identity_breadth']['loao_rmse_log_cap']
    capture_change=models['fundamentals_capture']['loao_rmse_log_cap']/models['fundamentals_activity']['loao_rmse_log_cap']-1
    identity=[r for r in result['asset_estimates'] if r['model_id']=='identity_groups']
    worst=max(identity,key=lambda r:abs(r['log_residual']))
    lines+=['',f"Economic groups reduce held-out error by {group_gain:.1%} relative to raw function count. Adding the static capture flag changes fundamentals-model error by {capture_change:+.1%} (positive means worse). These are new exploratory model comparisons; they do not replace H2 or H8.",'',f"The largest identity-model error is {worst['symbol']}: observed/model = {worst['observed_to_model_ratio']:.1f}x. This shows that function labels alone leave major asset-specific value unexplained. Treat this as model failure to explain the asset, rather than an investment opportunity.",'','Positive improvement means smaller held-out errors. Compare models within the same sample. These comparisons have no confirmatory p-values. All models are reported; no selected winner is deployed.','','![Held-out model comparison](../figures/crypto-relative-valuation.svg)','','## Asset estimates','','The table reports every asset under the identity-group model. Ratios above 1 mean observed historical size exceeds the held-out estimate. Error bands use inner held-out errors and have no calibrated coverage guarantee. Large bands signal weak valuation precision.','','| Asset | Observed mean cap ($bn) | Model-implied cap ($bn) | Observed/model | Empirical band ($bn) |','|---|---:|---:|---:|---|']
    for r in result['asset_estimates']:
        if r['model_id']=='identity_groups': lines.append(f"| {r['symbol']} | {r['observed_geometric_mean_cap_usd']/1e9:.2f} | {r['held_out_implied_cap_usd']/1e9:.2f} | {r['observed_to_model_ratio']:.2f}x | {r['empirical_band_low_usd']/1e9:.2f}–{r['empirical_band_high_usd']/1e9:.2f} |")
    lines+=['','## Fundamentals model estimates','','| Asset | Observed mean cap ($bn) | Activity model cap ($bn) | Observed/model | Largest centered predictor contribution (log units) |','|---|---:|---:|---:|---|']
    for r in result['asset_estimates']:
        if r['model_id']!='fundamentals_activity': continue
        terms=json.loads(r['centered_predictor_contributions_json']); driver=max(terms,key=lambda k:abs(terms[k]))
        lines.append(f"| {r['symbol']} | {r['observed_geometric_mean_cap_usd']/1e9:.2f} | {r['held_out_implied_cap_usd']/1e9:.2f} | {r['observed_to_model_ratio']:.2f}x | {driver}: {terms[driver]:+.2f} |")
    lines+=['','Contributions add to the training intercept to reconstruct the predicted log capitalization. They describe the fitted model, not causal economic effects. Full contributions and error bands for every model are included in the asset CSV.','','## Sample coverage','','| Asset | Market-cap days | Fee days | Identity eligible | Fundamentals eligible |','|---|---:|---:|---:|---:|']
    for r in result['coverage']: lines.append(f"| {r['symbol']} | {r['cap_days']} | {r['fee_days']} | {r['identity_eligible']} | {r['fundamentals_eligible']} |")
    lines+=['','## Peer multiples','','Peers exclude the target, require Jaccard economic-group similarity of at least 0.5, identical fee scope, and at least three eligible peers. Holder-revenue multiples also require verified capture in target and peers. The denominators retain provider definitions and are not automatically distributable cash flows.','','| Asset | Metric | State | Eligible peers | Own multiple | Peer median |','|---|---|---|---|---:|---:|']
    for r in result['peer_multiples']:
        own=f"{r['own_multiple']:.1f}x" if r['own_multiple'] is not None else '—'; median=f"{r['peer_median_multiple']:.1f}x" if r['peer_median_multiple'] is not None else '—'
        lines.append(f"| {r['symbol']} | {r['metric']} | {r['state']} | {r['peers'] or '—'} | {own} | {median} |")
    lines+=['','## What action follows','','Use residuals to identify assets needing closer explanation: adoption, liquidity, supply, data definitions and capture can account for deviations. Use wide bands and insufficient peers as evidence that precise valuation is not supported. Preserve the existing H1–H4/H8 results and obtain later data for independent validation.','','## Limitations','','The outcomes were previously examined; current classifications summarize historical assets retrospectively. Asset observations are dependent, fee scopes differ, volume may reflect speculation and provider coverage is uneven. Shrinkage biases coefficients by design. The empirical error bands are descriptive; they do not establish fair value, mispricing or a return forecast.','']
    return '\n'.join(lines)


def figure(result):
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="460" role="img" aria-label="Held-out valuation error by model">','<rect width="1040" height="460" fill="white"/>','<text x="24" y="32" font-family="Arial" font-size="22">How much error remains when valuing an unseen asset?</text>','<text x="24" y="58" font-family="Arial" font-size="13">Lower is better. Compare models within each sample; labels show improvement over its mean-only baseline.</text>']
    maximum=max(r['loao_rmse_log_cap'] for r in result['models'])*1.1
    for i,r in enumerate(result['models']):
        y=95+i*49; width=500*r['loao_rmse_log_cap']/maximum
        parts += [f'<text x="250" y="{y+18}" text-anchor="end" font-family="Arial" font-size="13">{html.escape(r["model_id"])}</text>',f'<rect x="265" y="{y}" width="{width:.2f}" height="26" fill="{"#3478b8" if r["sample"]=="identity" else "#b87924"}"/>',f'<text x="{275+width:.2f}" y="{y+18}" font-family="Arial" font-size="13">{r["loao_rmse_log_cap"]:.3f} ({r["rmse_improvement_vs_same_sample_mean"]:+.1%})</text>']
    return '\n'.join(parts+['<text x="265" y="430" font-family="Arial" font-size="13">RMSE in log market capitalization — historical exploratory sample</text>','</svg>'])+'\n'


def run(repo: Path):
    spec=json.loads((repo/'config/crypto_relative_valuation.json').read_text())
    result=build(spec,read_csv(repo/spec['classification_input']),read_csv(repo/spec['market_input']),read_csv(repo/spec['fundamentals_input']))
    out=repo/'data/processed/02_valuation'
    (out/'crypto_relative_valuation.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    write_csv(out/'crypto_relative_valuation_assets.csv',result['asset_estimates'])
    write_csv(out/'crypto_relative_valuation_models.csv',result['models'])
    (repo/'research/findings/crypto-relative-valuation.md').write_text(render(result))
    (repo/'research/figures/crypto-relative-valuation.svg').write_text(figure(result))
    return {k:result[k] for k in ['status','models']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--repo',type=Path,default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
