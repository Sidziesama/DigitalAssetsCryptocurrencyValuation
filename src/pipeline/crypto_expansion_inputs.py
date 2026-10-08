"""Descriptive input coverage for expansion assets; never assigns a code."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

from .historical import write_rows


def read(path):
    return json.loads(path.read_text())


def archive(root, name, url):
    path = root / name
    if path.exists():
        return read(path)
    with urllib.request.urlopen(url, timeout=30) as response:
        raw = response.read()
    payload = json.loads(raw)
    root.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(raw)
    metadata = {'url': url, 'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                'sha256': hashlib.sha256(raw).hexdigest()}
    with path.with_suffix('.metadata.json').open('x') as handle:
        json.dump(metadata, handle, indent=2)
        handle.write('\n')
    return payload


def normalize(payload, asset_id, provider_id, start, end):
    rows = {}
    for point in payload.get('data', []):
        day = str(point['time'])[:10]
        date.fromisoformat(day)
        if point.get('asset') != provider_id:
            raise ValueError('unexpected provider asset')
        if not start <= day <= end:
            continue
        if day in rows:
            raise ValueError('duplicate asset day')
        row = {'asset_id': asset_id, 'date': day}
        for metric, field in [('AdrActCnt', 'active_addresses'), ('TxCnt', 'transaction_count')]:
            value = point.get(metric)
            value = float(value) if value is not None else None
            if value is not None and (not math.isfinite(value) or value < 0):
                raise ValueError('invalid activity count')
            row[field] = value
        rows[day] = row
    return [rows[day] for day in sorted(rows)]


def run(repo: Path, collect=False):
    spec = read(repo / 'config/crypto_expansion_inputs.json')
    window = read(repo / 'config/crypto_monetary_evidence.json')['activity_window']
    start, end = window['start'], window['end']
    expected = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
    root = repo / spec['snapshot_directory']
    if collect:
        archive(root, 'catalog.json', spec['catalog_url'])
    with (repo / 'data/processed/00_foundation/market_daily_coinpaprika.csv').open() as handle:
        caps = list(csv.DictReader(handle))
    with (repo / 'data/processed/01_classification/crypto_collateral_protocol_detail.csv').open() as handle:
        collateral = list(csv.DictReader(handle))
    candidate_path = repo / 'data/processed/01_classification/crypto_expansion_collateral_daily.csv'
    candidates = []
    if candidate_path.exists():
        with candidate_path.open() as handle:
            candidates = list(csv.DictReader(handle))
    daily, summary = [], []
    for asset in spec['assets']:
        aid, pid = asset['asset_id'], asset['provider_id']
        query = urllib.parse.urlencode({'assets': pid, 'metrics': ','.join(asset['metrics']),
            'frequency': '1d', 'start_time': start, 'end_time': end, 'page_size': 10000})
        url = 'https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?' + query if pid else ''
        name = f'{aid}_{start}_{end}.json'
        error = ''
        payload = read(root / name) if (root / name).exists() else {}
        if collect and pid and not payload:
            try:
                payload = archive(root, name, url)
            except (OSError, ValueError) as exc:
                error = str(exc)
                # Keep failed attempts reproducible without storing an empty success snapshot.
                root.mkdir(parents=True, exist_ok=True)
                failure = root / f'{aid}_{start}_{end}.error.json'
                if not failure.exists():
                    with failure.open('x') as handle:
                        json.dump({'url': url, 'error': error}, handle, indent=2)
        failure = root / f'{aid}_{start}_{end}.error.json'
        if not payload and failure.exists():
            error = read(failure)['error']
        if payload.get('next_page_url'):
            raise ValueError('unexpected pagination: refusing an incomplete snapshot')
        rows = normalize(payload, aid, pid, start, end)
        daily.extend(rows)
        active = [r['active_addresses'] for r in rows if r['active_addresses'] is not None]
        tx = [r['transaction_count'] for r in rows if r['transaction_count'] is not None]
        cap_days = {r['date'] for r in caps if r['asset_id'] == aid and start <= r['date'] <= end
                    and r.get('market_cap_usd') and math.isfinite(float(r['market_cap_usd'])) and float(r['market_cap_usd']) > 0}
        collateral_days = {r['date'] for r in collateral if r['asset_id'] == aid and start <= r['date'] <= end}
        summary.append({'asset_id': aid, 'start_date': start, 'end_date': end,
            'expected_days': expected, 'active_address_days': len(active), 'transaction_days': len(tx),
            'median_active_addresses': statistics.median(active) if active else None,
            'median_transactions': statistics.median(tx) if tx else None,
            'market_cap_days': len(cap_days), 'existing_collateral_proxy_days': len(collateral_days),
            'expansion_candidate_balance_days': len({r['date'] for r in candidates if r['asset_id'] == aid and start <= r['date'] <= end}),
            'activity_coverage': 'complete' if len(active) == len(tx) == expected else 'partial' if rows else 'missing',
            'activity_source_url': url, 'collection_error': error,
            'next_action': ('Review monetary purpose and activity composition. ' if len(active) == len(tx) == expected else 'Collect missing activity measures. ')
                           + 'Collect dated collateral eligibility and daily collateral balances.',
            'scope_note': asset['scope_note'], 'collection_note': asset['collection_note']})
    out = repo / 'data/processed/01_classification'
    write_rows(out / 'crypto_expansion_activity_daily.csv', daily,
               ['asset_id', 'date', 'active_addresses', 'transaction_count'])
    write_rows(out / 'crypto_expansion_input_coverage.csv', summary, list(summary[0]))
    components = []
    for component in spec.get('activity_components', []):
        pid = component['provider_id']
        name = f'{pid}_{start}_{end}.json'
        query = urllib.parse.urlencode({'assets': pid, 'metrics': ','.join(component['metrics']),
            'frequency': '1d', 'start_time': start, 'end_time': end, 'page_size': 10000})
        url = 'https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?' + query
        payload = read(root / name) if (root / name).exists() else {}
        if collect and not payload:
            payload = archive(root, name, url)
        if payload.get('next_page_url'):
            raise ValueError('unexpected component pagination')
        for row in normalize(payload, component['asset_id'], pid, start, end):
            components.append(dict(row, component=pid, source_url=url, scope_note=component['scope_note']))
    write_rows(out / 'crypto_expansion_activity_components.csv', components,
               ['asset_id', 'date', 'component', 'active_addresses', 'transaction_count', 'source_url', 'scope_note'])
    return {'assets': len(summary), 'daily_rows': len(daily),
            'component_rows': len(components),
            'complete_activity_assets': [r['asset_id'] for r in summary if r['activity_coverage'] == 'complete'],
            'interpretation': 'Coverage only. No monetary or collateral codes assigned.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    parser.add_argument('--collect', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(args.repo.resolve(), args.collect), indent=2))
