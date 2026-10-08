# H4 staking measurement audit — 8 October 2026

## What the audit corrected

H4 requires 365 daily or protocol-epoch observations. The earlier readiness implementation accepted a collector's `unblocks_h4` flag without checking the number of observed days, causing BNB's complete **90-day collection job** to be mislabeled as complete for the **365-day research design**. The corrected gate checks both conditions.

![H4 coverage](../figures/crypto-h4-staking-coverage.svg)

## Current coverage

- ETH consensus stake: 0/365 days. The exact active-effective-balance collector is ready but requires an archival Beacon API endpoint.
- BNB consensus stake: 365/365 days, ranging from approximately 23.92 million to 26.84 million BNB.
- Legacy stkAAVE: 365/365 days, ranging from approximately 1.90 million to 3.01 million AAVE, retained as a separate protocol-risk-stake case study.

## Aave boundary decision

Aave Umbrella is relevant protocol backstop capital, but its initial Ethereum pools stake USDC, USDT, WETH aTokens and GHO—not AAVE. Those balances cannot be added to an AAVE-denominated staked-supply series. Official Aave documentation confirms the supported assets and the distinct legacy stkAAVE system. [Aave Umbrella documentation](https://aave.com/help/umbrella/umbrella)

Therefore, Umbrella contract discovery is not the missing H4 measurement. Legacy stkAAVE remains the relevant AAVE-token series and must be analyzed separately from native consensus staking.

## Status

BNB now meets the frozen history rule and legacy stkAAVE is complete for its separate case study. Comparative consensus-staking estimation remains blocked until ETH reaches 365 days. This is a data-readiness result, not evidence for or against the staking-liquidity hypothesis.
