from __future__ import annotations

import argparse,csv,json
from pathlib import Path

from .registry import load_json,validate_asset_config


def build_rows(assets: list[dict[str,str]], coinpaprika_assets: set[str] | None = None, binance_assets: set[str] | None = None)->list[dict[str,str]]:
    coinpaprika_assets = coinpaprika_assets or set()
    binance_assets = binance_assets or set()
    rows=[]
    for a in assets:
        stable=a["universe"]=="stablecoin"
        rows.extend([
            {"asset_id":a["asset_id"],"metric":"price_daily","source":"defillama_coin_prices","availability":"implemented","constraint":"price only"},
            {"asset_id":a["asset_id"],"metric":"market_cap_daily","source":"coinpaprika" if a["asset_id"] in coinpaprika_assets else "none_selected","availability":"implemented_recent" if a["asset_id"] in coinpaprika_assets else "blocked","constraint":"free rolling one-year history; full 2019-2026 history unavailable" if a["asset_id"] in coinpaprika_assets else "no verified free provider mapping"},
            {"asset_id":a["asset_id"],"metric":"volume_daily","source":"coinpaprika" if a["asset_id"] in coinpaprika_assets else "none_selected","availability":"implemented_recent" if a["asset_id"] in coinpaprika_assets else "blocked","constraint":"free rolling one-year history; full 2019-2026 history unavailable" if a["asset_id"] in coinpaprika_assets else "no verified free provider mapping"},
            {"asset_id":a["asset_id"],"metric":"circulating_supply_daily","source":"defillama_stablecoins" if stable and a.get("defillama_id") else "none_selected","availability":"implemented" if stable and a.get("defillama_id") else "blocked","constraint":"USD-valued circulation" if stable and a.get("defillama_id") else ("source-specific token supply history required" if not stable else "commodity issuer source required")}
            ,{"asset_id":a["asset_id"],"metric":"venue_ohlcv_daily","source":"binance_spot" if a["asset_id"] in binance_assets else "none_selected","availability":"implemented_partial" if a["asset_id"] in binance_assets else "blocked","constraint":"venue-specific stablecoin-quoted spot data; listing-window coverage varies" if a["asset_id"] in binance_assets else "no verified supported Binance spot pair"}
        ])
    return rows


def build(repo: Path)->list[dict[str,str]]:
    audit=repo/"data"/"processed"/"historical"/"coinpaprika_identifier_audit.csv"
    resolved:set[str]=set()
    if audit.exists():
        with audit.open(newline="",encoding="utf-8") as f:
            resolved={row["asset_id"] for row in csv.DictReader(f) if row["status"]=="resolved"}
    binance_audit=repo/"data"/"processed"/"historical"/"binance_pair_audit.csv"
    binance_resolved:set[str]=set()
    if binance_audit.exists():
        with binance_audit.open(newline="",encoding="utf-8") as f:
            binance_resolved={row["asset_id"] for row in csv.DictReader(f) if row["status"]=="resolved"}
    return build_rows(validate_asset_config(load_json(repo/"config"/"assets.json")),resolved,binance_resolved)


def render_findings(rows:list[dict[str,str]])->str:
    def count(metric,status):return sum(r["metric"]==metric and r["availability"]==status for r in rows)
    return f"""# Metric Source Availability

## Implemented

- Daily price: {count('price_daily','implemented')} assets.
- Daily stablecoin USD-valued circulation: {count('circulating_supply_daily','implemented')} assets.
- Recent daily market capitalization (free rolling window): {count('market_cap_daily','implemented_recent')} assets.
- Recent daily trading volume (free rolling window): {count('volume_daily','implemented_recent')} assets.
- Venue-specific daily OHLCV (partial listing windows): {count('venue_ohlcv_daily','implemented_partial')} assets.

## Blocked under current unauthenticated sources

- Daily market capitalization: {count('market_cap_daily','blocked')} assets.
- Daily trading volume: {count('volume_daily','blocked')} assets.
- Daily circulating supply: {count('circulating_supply_daily','blocked')} assets.
- Venue-specific daily OHLCV: {count('venue_ohlcv_daily','blocked')} assets.

The recent CoinPaprika fields do not satisfy the full 2019–2026 research window. Remaining blocked fields require a defensible alternate source; none are reconstructed from price alone. The machine-readable asset-by-metric matrix is stored at `data/processed/source_availability.csv`.
"""


def main()->None:
    p=argparse.ArgumentParser();p.add_argument("--repo",type=Path,default=Path.cwd());a=p.parse_args();rows=build(a.repo.resolve());out=a.repo.resolve()/"data"/"processed"/"source_availability.csv";out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=["asset_id","metric","source","availability","constraint"]);w.writeheader();w.writerows(rows)
    counts={};
    for r in rows:counts[(r["metric"],r["availability"])]=counts.get((r["metric"],r["availability"]),0)+1
    finding=a.repo.resolve()/"research"/"findings"/"metric-source-availability.md";finding.write_text(render_findings(rows),encoding="utf-8")
    print(json.dumps({f"{k[0]}::{k[1]}":v for k,v in sorted(counts.items())},indent=2))


if __name__=="__main__":main()
