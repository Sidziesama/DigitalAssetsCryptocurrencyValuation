"""Extract expansion lending balance candidates without assigning classifications."""
from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .historical import write_rows


def read(path):
    return json.loads(path.read_text())


def extract(payload, slug, aliases, start, end):
    rows, days = [], set()
    for point in payload.get('tokensInUsd') or []:
        day = datetime.fromtimestamp(int(point['date']), timezone.utc).date().isoformat()
        if not start <= day <= end:
            continue
        if day in days:
            raise ValueError(f'duplicate protocol day: {slug} {day}')
        days.add(day)
        for token, raw in (point.get('tokens') or {}).items():
            if token not in aliases or raw is None:
                continue
            value = float(raw)
            if not math.isfinite(value) or value < 0:
                raise ValueError('invalid token balance')
            rows.append({'asset_id': aliases[token], 'date': day, 'protocol_slug': slug,
                         'token_alias': token, 'token_balance_proxy_usd': value,
                         'identity_status': 'candidate_symbol_match',
                         'historical_collateral_eligibility': 'unverified'})
    return rows


def run(repo: Path):
    spec = read(repo / 'config/crypto_expansion_collateral.json')
    window = read(repo / 'config/crypto_monetary_evidence.json')['activity_window']
    protocols = read(repo / 'config/crypto_collateral_sources.json')['protocols']
    aliases = {}
    for asset in spec['assets']:
        for alias in asset['candidate_token_aliases']:
            if alias in aliases:
                raise ValueError('ambiguous token alias')
            aliases[alias] = asset['asset_id']
    detail = []
    for protocol in protocols:
        path = repo / 'data/raw/defillama_protocol_collateral' / (protocol['slug'] + '.json')
        detail.extend(extract(read(path), protocol['slug'], aliases, window['start'], window['end']))
    totals = defaultdict(float)
    for row in detail:
        totals[row['asset_id'], row['date']] += row['token_balance_proxy_usd']
    daily = [{'asset_id': aid, 'date': day, 'token_balance_proxy_usd': balance}
             for (aid, day), balance in sorted(totals.items())]
    summary = []
    for asset in spec['assets']:
        aid = asset['asset_id']
        selected = [r for r in daily if r['asset_id'] == aid]
        values = [r['token_balance_proxy_usd'] for r in selected]
        summary.append({'asset_id': aid, 'observed_proxy_days': len(selected),
            'median_token_balance_proxy_usd': statistics.median(values) if values else None,
            'protocols_with_candidate_matches': '|'.join(sorted({r['protocol_slug'] for r in detail if r['asset_id'] == aid})),
            'status': 'candidate_balances_need_identity_and_eligibility_review' if selected else 'no_matching_data_in_selected_sample',
            'recommended_va_collateral': None})
    out = repo / 'data/processed/01_classification'
    write_rows(out / 'crypto_expansion_collateral_detail.csv', detail,
               ['asset_id', 'date', 'protocol_slug', 'token_alias', 'token_balance_proxy_usd', 'identity_status', 'historical_collateral_eligibility'])
    write_rows(out / 'crypto_expansion_collateral_daily.csv', daily,
               ['asset_id', 'date', 'token_balance_proxy_usd'])
    write_rows(out / 'crypto_expansion_collateral_coverage.csv', summary, list(summary[0]))
    root = repo / 'data/raw/crypto_expansion_collateral/2026-09-14'
    markets = read(root / 'venus-markets.json')
    if len(markets['result']) != markets['total']:
        raise ValueError('incomplete Venus market pagination')
    metadata = read(root / 'venus-markets.metadata.json')
    symbols = {a['asset_id'].removeprefix('crypto_').upper(): a['asset_id'] for a in spec['assets']}
    current = []
    for market in markets['result']:
        symbol = market['underlyingSymbol']
        if symbol not in symbols:
            continue
        current.append({'asset_id': symbols[symbol], 'chain_id': market['chainId'],
            'market_address': market['address'], 'underlying_address': market['underlyingAddress'],
            'pool_comptroller': market['poolComptrollerAddress'],
            'can_be_collateral_current': market.get('canBeCollateral'),
            'collateral_factor_current': int(market['collateralFactorMantissa']) / 1e18,
            'retrieved_at_utc': metadata['retrieved_at_utc'], 'source_url': metadata['url'],
            'historical_eligibility': 'unverified'})
    write_rows(out / 'crypto_expansion_venus_current_eligibility.csv', current,
               list(current[0]) if current else ['asset_id'])
    return {'assets': len(summary), 'assets_with_balance_candidates': sum(bool(r['observed_proxy_days']) for r in summary),
            'detail_rows': len(detail), 'daily_rows': len(daily),
            'interpretation': spec['interpretation']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
