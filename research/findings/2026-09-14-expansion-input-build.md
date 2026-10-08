# Expansion evidence build — 14 September 2026

The researcher approved applying the existing BTC fee rule. BCH, DOGE, LTC and ZEC now have VA_GAS=0: relay policy does not meet the working protocol-required fee criterion. These are sourced decisions, not independently reviewed decisions. The relay-fee consistency case is resolved.

The matrix now contains **182 evidence-backed, 40 pending and 28 provisional cells**. Tranche A has 68 of 70 resolved; LINK and OP protocol capture remain pending.

## Data collected

Observation window: **25 May–22 August 2026**, inherited from the existing monetary evidence configuration. This is a descriptive collection build. No new materiality threshold or monetary/collateral classification is applied.

Archived Coin Metrics responses contain 900 asset-day records: both activity measures for nine assets, and transaction counts only for XMR. The collector can rebuild its outputs offline. A successful data pull is not proof of material monetary use. Network transactions can include non-payment activity, and address coverage needs special care on privacy networks.

| Asset | Active-address days | Transaction days | Market-cap days already available |
|---|---:|---:|---:|
| ADA | 90 | 90 | 89 |
| AVAX | 0 | 0 | 89 |
| BCH | 90 | 90 | 89 |
| DOGE | 90 | 90 | 89 |
| HBAR | 0 | 0 | 89 |
| LINK | 90 | 90 | 89 |
| LTC | 90 | 90 | 89 |
| OP | 0 | 0 | 89 |
| SOL | 0 | 0 | 89 |
| SUI | 0 | 0 | 89 |
| TRX | 90 | 90 | 89 |
| XLM | 90 | 90 | 89 |
| XRP | 90 | 90 | 89 |
| ZEC | 90 | 90 | 89 |
| HYPE | 0 | 0 | 89 |
| XMR | 0 | 90 | 89 |
| TON | 0 | 0 | 0 |
| TAO | 0 | 0 | 89 |
| POL | 0 | 0 | 89 |

## What remains

1. Collect collateral-enabled balances and dated eligibility evidence for the 19 expansion assets. The existing collateral output contains no rows for these assets; that is a collection gap, not evidence of no collateral use.
2. Fill missing activity histories and check what the measures count. Avalanche needs reconciled chain coverage; XMR has no active-address measure in this catalog.
3. Complete market-cap history: 18 assets currently have 89 of 90 days in the existing CoinPaprika file; TON has none there.
4. Review monetary-purpose evidence, then apply the settled survey rules when responses are analyzed.

Outputs: [coverage table](../../data/processed/01_classification/crypto_expansion_input_coverage.csv), [daily activity](../../data/processed/01_classification/crypto_expansion_activity_daily.csv), and [color-coded matrix](../../data/reference/digital_asset_research_universe.xlsx).

Primary data source: [Coin Metrics public catalog](https://community-api.coinmetrics.io/v4/catalog/asset-metrics). Exact request URLs and retrieval hashes are archived beside the original responses in `data/raw/crypto_expansion_inputs/2026-09-14/`.

Frozen survey specifications, the pre-fielding prediction and downstream estimates were not changed.
