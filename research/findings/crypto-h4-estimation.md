# H4: staking, turnover and risk

Status: `h4_estimation_blocked_missing_stake`.

H4 asks whether a larger staked share is associated with turnover, volatility or drawdown. ETH and BNB are the two consensus-staking assets; BTC, UNI and ARB are structural controls. Legacy stkAAVE remains a separate case.

| Required staking input | Observed days | Required days | Complete |
|---|---:|---:|---|
| crypto_eth | 0 | 362 | False |
| crypto_bnb | 362 | 362 | True |

Common complete analysis days: 0.

The model uses asset and date fixed effects, lagged staked share and log capitalization. BTC returns are common across assets and are absorbed by date fixed effects. Volatility and drawdown use consecutive archived USD prices, including the pre-study warmup. No day is filled across missing observations.

Inference enumerates 32 Rademacher assignments across five asset clusters. Its two-sided p-value resolution is 0.0625, and only two assets have positive stake. Exhaustive enumeration does not guarantee reliable small-sample inference. The three outcomes receive Benjamini–Hochberg correction.

Common market/price days before the stake gate: 361.

No empirical H4 coefficients have been estimated. Synthetic-data tests verify the implementation only; they are not research findings.

Configure ETH_BEACON_ARCHIVE_API_URL locally and collect exact active effective balance for every study date. Historical validator access is required; do not paste credentials into research files.

Turnover is trading volume divided by capitalization, not order-book liquidity. Staked share measures chain-specific stake divided by inferred circulating supply, not total unavailable economic float; liquid-staking instruments can keep exposure tradeable.
