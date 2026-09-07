# Data Pipeline Method

## Purpose

The pipeline creates stable identifiers and auditable coverage diagnostics before historical market or on-chain data is analyzed.

## Inputs

- `config/assets.json`: canonical pilot-universe configuration.
- `data/raw/<date>/coingecko_markets.json`: market snapshot.
- `data/raw/<date>/coingecko_global.json`: global market totals.
- `data/raw/<date>/defillama_stablecoins.json`: stablecoin snapshot.

Raw files are immutable. Their SHA-256 hashes are recorded in every coverage summary.

## Outputs

- `data/processed/<date>/identifier_registry.csv`
- `data/processed/<date>/snapshot_coverage.csv`
- `data/processed/<date>/coverage_summary.json`

## Coverage rule

For non-stable cryptoassets, the initial snapshot passes when CoinGecko supplies numeric market capitalization and 24-hour volume. For stablecoins, the snapshot must additionally include numeric DeFiLlama circulating peg-USD supply. A review result is a diagnostic flag, not an instruction to remove or replace the asset.

This first audit validates the frozen cross-sectional snapshot only. Historical daily and intraday coverage are separate later gates.

## Historical market collector

`src.pipeline.historical` retrieves CoinGecko market-chart ranges into immutable per-asset cache files, stores retrieval metadata and checksums, normalizes observations to UTC dates, and writes daily market and coverage tables. Existing cache files are reused unless `--force` is explicitly passed.

The historical pass threshold is at least 95% daily price coverage over the requested interval. Missing assets are flagged for review and are never automatically deleted from the research universe.

Because unauthenticated CoinGecko access rejects the early 2019 range, `src.pipeline.llama_history` provides the long-history fallback. It requests DeFiLlama coin-price history one asset at a time using the canonical CoinGecko namespace IDs, caches every response in yearly partitions, and reports both full-window coverage and coverage from the first observed date. This source contains price only; it is not used to fabricate historical market capitalization, supply, or volume.

DeFiLlama daily observations can drift by seconds around midnight. The normalizer assigns each observation to the nearest UTC calendar day rather than flooring the timestamp. This preserves the provider's intended daily cadence and avoids artificial skipped/duplicate dates without interpolating prices.

`src.pipeline.stablecoin_supply` retrieves the DeFiLlama token history for each supported stablecoin and retains `circulating.peggedUSD` under that explicit name. The field is a USD-valued circulation measure, not necessarily native token units. Commodity-referenced PAXG is excluded from this USD-stablecoin endpoint and requires a separate issuer source.

`src.pipeline.source_availability` records metric-level source status. Historical market capitalization and volume remain blocked under the unauthenticated source configuration; they are not inferred from price history.

`src.pipeline.stablecoin_risk` calculates strict and diagnostic partial scores from dated, evidence-linked component inputs. Strict composites require 100% component completeness. Reserve quality and transparency are higher-is-better; redemption friction is higher-is-worse. Partial scores are never promoted to headline results.
