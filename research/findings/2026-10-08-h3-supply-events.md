# H3 supply-event checkpoint — 8 October 2026

## Question and frozen rule

H3 asks whether material increases in economically available token supply are followed by negative market-adjusted returns. The design was frozen in commit `7fd4329` before estimation. Events require an exact effective date, primary-source evidence, and a gross impact of at least 0.5% of pre-event circulating supply.

## Evidence decisions

Arbitrum qualifies because its official documentation specifies the allocation, first cliff, and subsequent monthly cadence on the 16th. The remaining team, contributor, and investor allocation implies approximately 92.65 million ARB per monthly event. [Arbitrum token-supply documentation](https://docs.arbitrum.foundation/token-supply)

Sui is retained as an excluded candidate. Its Foundation publishes an unusually useful free monthly circulation API, but explicitly describes the observations as month-end amounts. That does not establish the exact intra-month release date required by the frozen event rule. [Sui release-schedule documentation](https://www.sui.io/blog/token-release-schedule), [official circulation API](https://sui-circulation.suiexplorer.com/api/sui_circulation)

## Descriptive result

Twelve ARB events meet the materiality and market-data rules. Their mean cumulative abnormal log return over trading days −1 through +1 is **+0.0155**, rather than the predicted negative value. Only **5 of 12** events have the predicted negative sign.

This does not establish a positive unlock effect. All observations come from one asset and recur monthly, so they are statistically dependent. The frozen rule requires at least two assets before pooled inference; accordingly, no pooled p-value is produced.

## Next gate

Locate at least one additional active-universe asset with primary-source event dates, evidenced quantities, and sufficient return history. Until then, H3 remains unsupported and not identification-ready.
