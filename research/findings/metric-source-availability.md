# Metric Source Availability

## Implemented

- Daily price: 41 assets.
- Daily stablecoin USD-valued circulation: 15 assets.
- Recent daily market capitalization (free rolling window): 1 assets.
- Recent daily trading volume (free rolling window): 1 assets.
- Venue-specific daily OHLCV (partial listing windows): 24 assets.

## Blocked under current unauthenticated sources

- Daily market capitalization: 40 assets.
- Daily trading volume: 40 assets.
- Daily circulating supply: 26 assets.
- Venue-specific daily OHLCV: 17 assets.

The recent CoinPaprika fields do not satisfy the full 2019–2026 research window. Remaining blocked fields require a defensible alternate source; none are reconstructed from price alone. The machine-readable asset-by-metric matrix is stored at `data/processed/00_foundation/source_availability.csv`.
