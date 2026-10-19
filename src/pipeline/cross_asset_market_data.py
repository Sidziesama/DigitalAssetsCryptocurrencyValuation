"""Archive public benchmark responses; rebuild normalized prices offline."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .crypto_h8_verified_universe import write_csv


def normalize(payload, symbol):
    error=payload.get('chart',{}).get('error')
    if error: raise ValueError(f'{symbol}: provider error {error}')
    result=payload['chart']['result'][0]
    values=result['indicators']['adjclose'][0]['adjclose']
    timestamps=result['timestamp']
    if len(values)!=len(timestamps): raise ValueError('Timestamp/adjusted-close length mismatch')
    if result['meta'].get('currency')!='USD': raise ValueError('Expected USD benchmark')
    rows=[]; seen=set()
    for timestamp,value in zip(timestamps,values):
        if value is None: continue
        value=float(value)
        if not math.isfinite(value) or value<=0: raise ValueError('Invalid adjusted close')
        day=datetime.fromtimestamp(timestamp,timezone.utc).astimezone(ZoneInfo('America/New_York')).date().isoformat()
        if day in seen: raise ValueError('Duplicate benchmark session date')
        seen.add(day)
        rows.append({'symbol':symbol,'date':day,'adjusted_close_usd':value,'provider':'yahoo_chart','return_basis':'vendor_adjusted_close'})
    return sorted(rows,key=lambda r:r['date'])


def run(repo: Path, offline=False):
    spec=json.loads((repo/'config/crypto_cross_asset.json').read_text())
    start=date.fromisoformat(spec['window']['start'])-timedelta(days=14)
    end=date.fromisoformat(spec['window']['end'])+timedelta(days=1)
    root=repo/'data/raw/cross_asset_benchmarks'; root.mkdir(parents=True,exist_ok=True)
    rows=[]; manifest=[]
    for benchmark in spec['benchmarks']:
        symbol=benchmark['symbol']; path=root/f'{symbol}_{start}_{end}.json'
        url=f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={int(datetime.combine(start,datetime.min.time(),timezone.utc).timestamp())}&period2={int(datetime.combine(end,datetime.min.time(),timezone.utc).timestamp())}&interval=1d&events=div%2Csplits&includeAdjustedClose=true'
        if not path.exists():
            if offline: raise ValueError(f'Missing archived benchmark snapshot: {path}')
            request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (research; digital-assets-valuation)','Accept':'application/json'})
            with urllib.request.urlopen(request,timeout=40) as response: raw=response.read()
            payload=json.loads(raw); normalize(payload,symbol)
            path.write_bytes(raw)
            metadata={'symbol':symbol,'url':url,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(raw).hexdigest(),'official_instrument_source':benchmark['official_source']}
            path.with_suffix('.metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
        payload=json.loads(path.read_bytes()); normalized=normalize(payload,symbol)
        metadata=json.loads(path.with_suffix('.metadata.json').read_text())
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=metadata['sha256']: raise ValueError('Benchmark archive checksum mismatch')
        rows.extend(normalized)
        manifest.append({'symbol':symbol,'rows':len(normalized),'first_date':normalized[0]['date'],'last_date':normalized[-1]['date'],'raw_path':str(path.relative_to(repo)),**metadata})
    out=repo/'data/processed/00_foundation'
    write_csv(out/'cross_asset_benchmarks_daily.csv',rows)
    summary={'status':'cross_asset_benchmarks_complete','instruments':manifest,'proxy_warning':spec['market_source']}
    (out/'cross_asset_benchmarks_manifest.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--repo',type=Path,default=Path.cwd()); parser.add_argument('--offline',action='store_true')
    args=parser.parse_args(); print(json.dumps(run(args.repo.resolve(),args.offline),indent=2))
