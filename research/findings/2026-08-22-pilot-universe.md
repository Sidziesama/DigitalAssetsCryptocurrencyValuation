# Pilot Universe Selection — 2026-08-22

## Decision

Freeze a pilot universe of 25 non-stable cryptoassets and 16 stable-value assets. Selection prioritizes market capitalization, meaningful trading volume, public-data accessibility, economic-design coverage, and a deliberately limited growth sleeve.

## Indicative coverage

- Total crypto market capitalization: approximately $2.617 trillion.
- Selected non-stable cryptoassets: approximately $2.211 trillion, or 84.5% of the total market.
- Selected stable-value assets: approximately $287.9 billion.
- Indicative combined coverage: approximately 95.5%.

The combined estimate uses contemporaneous but cross-provider snapshots. Production coverage must be recomputed from synchronized extracts because supply methodologies and retrieval times can differ.

## Non-stable cryptoassets

### Market core

BTC, ETH, BNB, XRP, SOL, TRX, DOGE, ZEC, LINK, ADA, XMR.

### Economic-mechanism coverage

XLM, BCH, LTC, HBAR, AVAX, TON, UNI, AAVE, ARB, OP, POL.

### Growth sleeve

HYPE, SUI, TAO.

## Stable-value assets

### Market core

USDT, USDC, USDS, DAI, USDe, USD1, USDG.

### Growth sleeve

RLUSD, PYUSD, USDD, GHO.

### Structural coverage

FDUSD, TUSD, FRAX, PAXG.

### Failure control

USTC / historical UST.

## Inclusion hierarchy

1. Market core: large capitalization and meaningful trading volume.
2. Growth sleeve: expanding capitalization, supply, adoption, or economic relevance with accessible history.
3. Economic coverage: distinct value-accrual, consensus, privacy, governance, backing, or redemption mechanism.
4. Failure control: failed/reflexive designs required to control survivorship bias.

## Open validation items

- Perform independent second-coder review of every `VA_*` and claim variable.
- Extract component-level stablecoin reserve and redemption disclosures.
- Test historical coverage and vendor consistency before the final universe is locked.
- Decide with the faculty adviser whether memecoins and tokenized real-world assets require dedicated strata.

## Sources

- CoinGecko Markets API: https://api.coingecko.com/api/v3/coins/markets
- CoinGecko Global API: https://api.coingecko.com/api/v3/global
- DeFiLlama Stablecoins API: https://stablecoins.llama.fi/stablecoins?includePrices=true
