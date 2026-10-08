# Collateral collection — 14 September 2026

The first expansion collateral screen is built from the eight lending-protocol snapshots already archived for the project. It contains 1,394 protocol/token/day observations and 764 asset/day totals. Eight assets have candidate balance observations on all 90 days; POL has 44 days. The other ten have no exact matches in this selected sample. Missing matches do not establish absence of collateral use.

## Balance coverage

Period: 25 May–22 August 2026. These are DeFiLlama protocol token-balance proxies, not measured collateral pledged by borrowers. Token symbols are candidate identity matches; wrappers, migrations and addresses require verification before classification. Only protocol-level totals are read, avoiding addition of chain totals to parent totals. Legacy MATIC/WMATIC, staking derivatives and LP positions are excluded pending separate identity evidence.

| Asset | Days | Protocols with matches |
|---|---:|---|
| ADA | 90 | venus-core-pool |
| AVAX | 90 | aave, silo-v2 |
| DOGE | 90 | venus-core-pool |
| LINK | 90 | aave, compound-v3, dolomite, radiant-v2, venus-core-pool |
| LTC | 90 | venus-core-pool |
| OP | 90 | aave, compound-v3, venus-core-pool |
| SOL | 90 | venus-core-pool |
| XRP | 90 | venus-core-pool |
| POL | 44 | dolomite |

## Eligibility evidence

The official Venus API snapshot is complete for its BSC market query (90 records). It currently identifies SOL and XRP as collateral-enabled in the core pool. ADA, DOGE, LTC, LINK and legacy MATIC currently have zero collateral factors in that pool. This is a September 14 snapshot, not an observation of the May–August study window and not a statement about other lending markets. Legacy MATIC is retained in the raw response but is not mapped automatically to POL.

Historical read attempts used the project’s archived May 25 BSC block. Blast and PublicNode returned HTTP 403. The BNB Chain endpoint returned `missing trie node` for every requested market, so no historical eligibility observation was obtained. The returned blockchain errors are archived; the two HTTP failures are recorded here. No need to repeat the failed requests across the full window.

Primary references: [Venus API documentation](https://github.com/venusprotocol/venus-protocol-documentation/blob/main/services/api.md), [official market snapshot endpoint](https://api.venus.io/markets?chainId=56&limit=100&page=0), and [Venus liquidation and collateral-factor documentation](https://docs-v4.venus.io/guides/liquidation).

## Activity extension

Downloaded 270 observations covering Avalanche C-, P- and X-chains separately, 90 days each, from the Coin Metrics public API. No address totals are added across chains; that would require a deduplication rule. These component observations do not by themselves establish monetary use.

## Remaining work

1. Verify underlying-token identities and historical collateral settings, starting with the markets now identified.
2. Expand the lending-market sample for the ten assets with no matches; the original sample was designed for the six-asset core.
3. Resolve remaining activity and market-cap gaps. Apply the survey-set rules only after the panel analysis.

The classification matrix remains **182 evidence-backed, 40 pending, 28 provisional**. No survey input, prediction or frozen estimator was changed.

Outputs: [balance coverage](../../data/processed/01_classification/crypto_expansion_collateral_coverage.csv), [current Venus eligibility](../../data/processed/01_classification/crypto_expansion_venus_current_eligibility.csv), [Avalanche activity components](../../data/processed/01_classification/crypto_expansion_activity_components.csv).
