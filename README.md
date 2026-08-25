# Digital Assets Valuation

Research and development repository for an NYU Financial Engineering master's project on the economic design, valuation, adoption, and risk of digital assets.

## Research objective

Build a reproducible economic taxonomy of stablecoins and cryptocurrencies, translate token design into measurable variables, and test whether usage, value-accrual mechanisms, supply, liquidity, security, reserve quality, and redemption design explain valuation and risk.

## Repository layout

- `docs/` — living research notebook and methodology documents.
- `data/raw/` — immutable dated source snapshots. Never edit these files in place.
- `data/reference/` — editable classification workbooks and research codebooks.
- `research/findings/` — dated findings, selection decisions, and analytical notes.
- `src/artifacts/` — reproducible builders for document and workbook artifacts.
- `src/pipeline/` — data acquisition, normalization, quality-control, and panel-building code.
- `tests/` — tests for identifiers, classifications, transformations, and empirical inputs.
- `outputs/` — generated analytical tables and figures; large/reproducible outputs may be ignored by Git.

## Current pilot universe

The Phase 2 pilot contains 25 non-stable cryptoassets and 16 stable-value assets. The dated 2026-08-22 snapshot provides approximately 95.5% indicative total-market coverage using CoinGecko and DeFiLlama inputs. It also includes a limited growth sleeve and historical UST as a failure control.

## Reproducibility rules

1. Raw data is stored in dated, immutable folders with source and retrieval metadata.
2. Symbols are not primary keys; use stable internal IDs and chain-qualified contract addresses.
3. Design classifications are effective-dated and retain evidence URLs, coder, reviewer, and confidence.
4. Unknown values remain null. A zero means the field was reviewed and the criterion was not met.
5. Every analytical table must be reproducible from frozen raw inputs and version-controlled transformations.
6. Market snapshots, issuer terms, protocol designs, and legal rights are treated as time-varying.

## Immediate workstream

1. Independent second-coder review of the pilot classifications.
2. Component-level stablecoin reserve-quality, transparency, and redemption-friction scoring.
3. Historical data-coverage audit for 2019–2026 daily panels and selected intraday depeg episodes.
4. Identifier registry and ingestion pipeline.
5. Descriptive atlas and preregistration freeze before headline hypothesis testing.

## Run the current pipeline

From the repository root:

```bash
python -m unittest discover -s tests -v
python -m src.pipeline.registry --repo . --snapshot-date 2026-08-22
python -m src.pipeline.historical --repo . --start 2026-07-24 --end 2026-08-22 --asset-id crypto_btc
python -m src.pipeline.llama_history --repo . --start 2019-01-01 --end 2026-08-22
python -m src.pipeline.stablecoin_supply --repo . --start 2019-01-01 --end 2026-08-22
python -m src.pipeline.stablecoin_global_market --repo . --start 2019-01-01 --end 2026-08-22
python -m src.pipeline.source_availability --repo .
python -m src.pipeline.stablecoin_risk --repo .
python -m src.pipeline.coinpaprika_market --repo . --start 2025-08-25 --end 2026-08-22
python -m src.pipeline.cryptocompare_volume --repo . --start 2019-01-01 --end 2026-08-22
python -m src.pipeline.binance_klines --repo . --start 2019-01-01 --end 2026-08-22
python -m src.pipeline.stablecoin_panel --repo . --breach-bps 50 --recovery-bps 25
python -m src.pipeline.stablecoin_atlas --repo .
python -m src.pipeline.preregistration --repo .
python -m src.pipeline.stablecoin_adoption --repo .
python -m src.pipeline.stablecoin_chain_distribution --repo .
python -m src.pipeline.stablecoin_trading_activity --repo .
python -m src.pipeline.binance_stablecoin_depth --repo .
python -m src.pipeline.defillama_yield_integrations --repo .
python -m src.pipeline.coinmetrics_stablecoin_usage --repo . --start 2019-01-01 --end 2026-08-24
python -m src.pipeline.stablecoin_usage_panel --repo .
python -m src.pipeline.h7_readiness --repo .
```

The registry command validates the asset configuration and frozen raw snapshots, records SHA-256 hashes, and writes the identifier registry and cross-sectional coverage audit to `data/processed/2026-08-22/`. It also writes a readable audit note to `research/findings/`.

The historical command performs a bounded example pull. The collector chunks long requests, caches immutable raw responses and retrieval metadata, normalizes data to UTC dates, merges incremental runs without discarding earlier assets, and writes daily data plus a missingness report to `data/processed/historical/`. Set `COINGECKO_API_KEY` when the selected CoinGecko plan requires authenticated historical access.

The DeFiLlama fallback command builds the long daily-price history when early CoinGecko access is unavailable. It uses one asset per provider request, yearly cache partitions, nearest-UTC-day normalization, and active-window coverage diagnostics. It supplies price only; historical market capitalization, volume, and circulating supply remain separate data workstreams.

The stablecoin-supply command collects DeFiLlama `circulating.peggedUSD` histories for supported assets. The source-availability command produces the explicit metric-by-asset matrix showing which histories are implemented or still blocked.

The stablecoin-risk command validates evidence-linked component inputs and calculates strict reserve-quality, transparency, and redemption-friction scores. Strict composites are withheld when any required component is unknown.

The CoinPaprika command builds a no-key, rolling recent-market panel containing daily price, reported market capitalization, and 24-hour volume. CoinPaprika's free tier exposes only the latest year of daily history, so this source is a recent-period and cross-source-validation layer rather than a substitute for the full 2019–2026 market-cap panel. Identifier ambiguity is surfaced in a separate audit and never resolved by symbol alone when multiple active candidates exist.

The CryptoCompare command builds a paginated 2019–2026 daily OHLCV panel for verified non-stable crypto symbols. Its `volume_quote_usd` field is CCCAGG pair volume converted to USD, not total global spot volume and not directly interchangeable with CoinPaprika's reported 24-hour volume. Provider zero-padding before an asset's observed history is discarded.

The Binance command uses the official keyless market-data host and records venue-specific daily candles, quote volume, trade counts, and taker volume for active USDT/USDC/FDUSD spot pairs. Quote-stablecoin units are retained as such and are not silently relabeled as exact USD.

The stablecoin-panel command joins the long daily price panel to supported circulation histories and strict design scores, calculates peg-error and threshold variables, and produces a daily depeg-event table. PAXG is excluded because a gold benchmark is required. Missing calendar days censor open episodes instead of being bridged.

The stablecoin-atlas command produces asset-level peg statistics, band-robustness rates, episode rankings, monthly stress concentration, an explicit extreme-observation review queue, and a reproducible SVG summary chart. USTC remains visible as a failure control but is excluded from primary-sample rankings.

The preregistration command validates and renders the machine-readable H5-H7 draft and records checksums for its current analytical inputs. The draft contains explicit readiness gates and remains labeled `draft_not_frozen` until point-in-time design evidence, second-coder review, and remaining H7 inputs are complete.

The stablecoin-global-market command archives and normalizes DeFiLlama's free aggregate `totalCirculatingUSD.peggedUSD` history without interpolation. The stablecoin-adoption command then constructs exact-date supply growth, pilot concentration, within-pilot share, and DeFiLlama global pegged-USD share. This denominator does not represent non-USD-pegged stable-value assets.

The stablecoin-chain-distribution command extracts daily chain balances already preserved in DeFiLlama raw histories and calculates chain breadth, concentration, effective chain count, and top-chain share. These are cross-chain distribution proxies, not transaction usage or protocol-integration counts.

The stablecoin-trading-activity command joins the recent CoinPaprika volume panel to supply and peg outcomes and calculates volume-to-supply turnover. It is a recent reported trading-activity proxy, not order-book liquidity or settlement usage.

The Binance stablecoin-depth command archives keyless spot order-book snapshots and measures quoted spread, executable bid/ask depth within 10/25/50 bps, and simulated price impact for 100,000 and 1,000,000 anchor-unit trades. Quote-oriented pairs are algebraically inverted into the target stablecoin's perspective. These are venue-specific point-in-time observations; repeated snapshots are required before they can enter H7 panel estimation.

The DeFiLlama yield-integrations command archives the current free yield-pool universe and constructs conservative exact-symbol-component counts of pools, projects, and chains for each primary stablecoin. It is a cross-sectional yield-integration proxy—not an exhaustive or historical protocol-integration measure—and gross matched-pool TVL is not token-specific TVL.

The Coin Metrics stablecoin-usage command collects free daily active-address, ledger-transaction, and token-transfer metrics for explicitly supported provider assets and emits a full 14-asset coverage audit. Active addresses are not unique users, and unsupported assets remain null rather than being inferred from chain-level totals.

The stablecoin usage-panel command applies the fixed two-tier H7 design: all 14 coverage-qualified assets remain in the primary supply/share specification, while USDT, USDC, DAI, and TUSD enter a separate exploratory usage panel with exact one-day lags. The usage subsample cannot replace or determine the primary sample.

The H7-readiness command constructs the lagged recent joined panel, variable-by-asset coverage matrix, objective sample gate, and pass/fail readiness report. It does not declare H7 ready while market depth, integrations, and usage remain unsourced.

This repository is for academic research. Classifications are not legal conclusions or investment recommendations.
