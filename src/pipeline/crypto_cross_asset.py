"""Frozen cross-asset return alignment, dependence and sensitivity study."""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics as st
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from .crypto_h8_verified_universe import number, ranks, read_csv, write_csv

PRIMARY='Crypto equal-weight fixed basket'


def corr(x,y):
    if len(x)<3 or len(x)!=len(y): return None
    mx,my=st.fmean(x),st.fmean(y)
    xx=sum((v-mx)**2 for v in x); yy=sum((v-my)**2 for v in y)
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(xx*yy) if xx and yy else None


def quantile(values,p):
    values=sorted(values); index=(len(values)-1)*p; low=math.floor(index); high=math.ceil(index)
    return values[low]+(values[high]-values[low])*(index-low)


def block_interval(x,y,config):
    rng=random.Random(config['seed']); n=len(x); estimates=[]
    for _ in range(config['draws']):
        indices=[]
        while len(indices)<n:
            start=rng.randrange(n)
            indices.extend((start+j)%n for j in range(config['block_length_weeks']))
        estimate=corr([x[i] for i in indices[:n]],[y[i] for i in indices[:n]])
        if estimate is not None: estimates.append(estimate)
    tail=(1-config['confidence_level'])/2
    return quantile(estimates,tail),quantile(estimates,1-tail)


def prepare(spec,profiles,prices):
    start,end=spec['window']['start'],spec['window']['end']
    expected=(date.fromisoformat(end)-date.fromisoformat(start)).days+1
    source=defaultdict(dict)
    for r in prices:
        value=number(r.get('close_usdt'))
        if value is not None and value>0:
            a,d=r['asset_id'],r['date']
            if d in source[a]: raise ValueError('Duplicate crypto date')
            source[a][d]=value
    coverage=[]; eligible=[]
    for p in profiles:
        a=p['asset_id']; days=sum(start<=d<=end for d in source[a])
        included=days>=math.ceil(expected*spec['minimum_crypto_coverage'])
        coverage.append({'asset_id':a,'symbol':p['symbol'],'close_days':days,'expected_days':expected,'eligible':int(included)})
        if included: eligible.append(p)
    if len(eligible)<3: raise ValueError('Insufficient eligible crypto assets')
    daily={}
    for p in eligible:
        observations=source[p['asset_id']]; daily[p['symbol']]={}
        for day,value in observations.items():
            previous=(date.fromisoformat(day)-timedelta(days=1)).isoformat()
            if previous in observations: daily[p['symbol']][day]=value/observations[previous]-1
    members={PRIMARY:[p['symbol'] for p in eligible], 'Crypto ex BTC and ETH':[p['symbol'] for p in eligible if p['symbol'] not in {'BTC','ETH'}]}
    for g in [k for k in eligible[0] if k.startswith('bundle_')]:
        members['Group: '+g.removeprefix('bundle_')]=[p['symbol'] for p in eligible if p[g]=='1']
    for label,symbols in members.items():
        if not symbols: continue
        common=set.intersection(*(set(daily[s]) for s in symbols))
        daily[label]={day:st.fmean(daily[s][day] for s in symbols) for day in common}
    return daily,coverage,members


def endpoints(benchmarks,weekly):
    dates=sorted(set.intersection(*(set(v) for v in benchmarks.values())))
    if not weekly: return dates
    weeks={}
    for d in dates:
        calendar=date.fromisoformat(d).isocalendar()
        weeks[(calendar.year,calendar.week)]=d
    return sorted(weeks.values())


def matched(spec,daily,benchmarks,weekly=True,shift=0):
    dates=endpoints(benchmarks,weekly); rows=[]
    for previous,current in zip(dates,dates[1:]):
        if not spec['window']['start']<=current<=spec['window']['end']: continue
        gap=(date.fromisoformat(current)-date.fromisoformat(previous)).days
        if weekly and not 4<=gap<=10: continue
        if not weekly and not 1<=gap<=5: continue
        row={'date':current,'previous_date':previous}
        for label,series in benchmarks.items(): row[label]=series[current]/series[previous]-1
        shifted_start=date.fromisoformat(previous)+timedelta(days=shift)
        required=[(shifted_start+timedelta(days=k)).isoformat() for k in range(1,gap+1)]
        for label,series in daily.items():
            if all(d in series for d in required): row[label]=math.prod(1+series[d] for d in required)-1
        rows.append(row)
    return rows


def correlation_rows(rows,labels,benchmarks,minimum):
    results=[]
    for label in labels:
        for b in benchmarks:
            paired=[r for r in rows if label in r and b in r]
            x=[r[label] for r in paired]; y=[r[b] for r in paired]
            valid=len(paired)>=minimum
            results.append({'series':label,'benchmark':b,'pairs':len(paired),'state':'estimated' if valid else 'insufficient_pairs','pearson':corr(x,y) if valid else None,'spearman':corr(ranks(x),ranks(y)) if valid else None})
    return results


def performance(rows,label):
    valid=[r for r in rows if label in r]
    if not valid: return {'series':label,'state':'unavailable'}
    returns=[r[label] for r in valid]; wealth=1; peak=1; draw=0
    for r in returns:
        wealth*=1+r; peak=max(peak,wealth); draw=min(draw,wealth/peak-1)
    days=(date.fromisoformat(valid[-1]['date'])-date.fromisoformat(valid[0]['previous_date'])).days
    return {'series':label,'state':'estimated','weeks':len(valid),'total_return':wealth-1,'annualized_volatility':st.pstdev(returns)*math.sqrt(52),'sampled_max_drawdown':draw,'annualized_geometric_return':wealth**(365/days)-1,'first_endpoint':valid[0]['previous_date'],'last_endpoint':valid[-1]['date']}


def build(spec,profiles,prices,benchmark_rows):
    if spec.get('status')!='frozen_before_cross_asset_estimation': raise ValueError('Study must be frozen')
    if len(profiles)!=23 or len({p['asset_id'] for p in profiles})!=23 or any(p['classification_status']!='complete_human_verified' for p in profiles): raise ValueError('Requires 23 unique verified assets')
    daily,coverage,members=prepare(spec,profiles,prices)
    benchmarks={b['symbol']:{} for b in spec['benchmarks']}
    for row in benchmark_rows:
        if row['symbol'] not in benchmarks: continue
        d=row['date']; value=number(row['adjusted_close_usd'])
        if d in benchmarks[row['symbol']]: raise ValueError('Duplicate benchmark date')
        if value is None or value<=0: raise ValueError('Invalid benchmark price')
        benchmarks[row['symbol']][d]=value
    weekly=matched(spec,daily,benchmarks)
    if sum(PRIMARY in r for r in weekly)<spec['minimum_weekly_pairs']:
        raise ValueError('Insufficient complete weekly basket-benchmark observations')
    primary=correlation_rows(weekly,list(daily),benchmarks,spec['minimum_weekly_pairs'])
    for r in primary:
        if r['series']==PRIMARY and r['state']=='estimated':
            paired=[v for v in weekly if PRIMARY in v]
            r['bootstrap_low'],r['bootstrap_high']=block_interval([v[PRIMARY] for v in paired],[v[r['benchmark']] for v in paired],spec['uncertainty'])
    sensitivities=[]
    scenarios={'daily':matched(spec,daily,benchmarks,False),'weekly_crypto_shift_minus1':matched(spec,daily,benchmarks,True,-1),'weekly_crypto_shift_plus1':matched(spec,daily,benchmarks,True,1),'weekly_first_half':weekly[:len(weekly)//2],'weekly_second_half':weekly[len(weekly)//2:]}
    for scenario,rows in scenarios.items():
        minimum=20 if 'half' in scenario else spec['minimum_weekly_pairs']
        for r in correlation_rows(rows,[PRIMARY,'BTC','ETH','Crypto ex BTC and ETH'],benchmarks,minimum): sensitivities.append({'scenario':scenario,**r})
    regimes=[]
    cutoff=quantile([r['SPY'] for r in weekly],.2)
    for regime,rows in [('SPY_negative_week',[r for r in weekly if r['SPY']<0]),('SPY_bottom_quintile_week',[r for r in weekly if r['SPY']<=cutoff])]:
        for label in [PRIMARY,'BTC','ETH','Crypto ex BTC and ETH','GLD','SPY','IWM']:
            paired=[r for r in rows if label in r]
            valid=len(paired)>=spec['minimum_down_pairs']
            regimes.append({'regime':regime,'series':label,'weeks':len(paired),'state':'estimated' if valid else 'small_sample_descriptive_only','correlation_with_SPY':corr([r[label] for r in paired],[r['SPY'] for r in paired]) if valid else None,'mean_weekly_return':st.fmean(r[label] for r in paired) if paired else None,'share_negative':st.fmean(r[label]<0 for r in paired) if paired else None})
    daily_rows=scenarios['daily']; rolling=[]
    for i in range(59,len(daily_rows)):
        observations=daily_rows[i-59:i+1]
        for b in benchmarks:
            pairs=[r for r in observations if PRIMARY in r]
            rolling.append({'date':daily_rows[i]['date'],'benchmark':b,'pairs':len(pairs),'correlation':corr([r[PRIMARY] for r in pairs],[r[b] for r in pairs]) if len(pairs)==60 else None})
    labels=[PRIMARY,'BTC','ETH','Crypto ex BTC and ETH',*benchmarks]
    comparable=[r for r in weekly if all(label in r for label in labels)]
    summary={'status':'exploratory_cross_asset_complete','experiment_id':spec['experiment_id'],'window':spec['window'],'primary_frequency':spec['primary_frequency'],'timing':spec['timing'],'guardrails':spec['guardrails'],'uncertainty':spec['uncertainty'],'coverage':coverage,'members':members,'weekly_pairs':len(weekly),'correlations':primary,'robustness':sensitivities,'stress_regimes':regimes,'performance':[performance(comparable,label) for label in labels],'source_note':spec['market_source']}
    return summary,weekly,rolling


def run(repo:Path):
    spec=json.loads((repo/'config/crypto_cross_asset.json').read_text())
    result,weekly,rolling=build(spec,read_csv(repo/spec['classification_input']),read_csv(repo/spec['crypto_input']),read_csv(repo/'data/processed/00_foundation/cross_asset_benchmarks_daily.csv'))
    out=repo/'data/processed/03_risk'
    (out/'crypto_cross_asset.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    write_csv(out/'crypto_cross_asset_weekly.csv',weekly)
    write_csv(out/'crypto_cross_asset_correlations.csv',result['correlations'])
    write_csv(out/'crypto_cross_asset_robustness.csv',result['robustness'])
    write_csv(out/'crypto_cross_asset_rolling.csv',rolling)
    return {'status':result['status'],'weekly_pairs':len(weekly),'eligible_assets':sum(r['eligible'] for r in result['coverage']),'primary_correlations':[r for r in result['correlations'] if r['series']==PRIMARY]}


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--repo',type=Path,default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
