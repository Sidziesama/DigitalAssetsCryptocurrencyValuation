# Digital Asset Valuation Project — Team Meeting Brief

**Meeting date:** 2026-08-25  
**Project stage:** Phase 1 taxonomy substantially developed; Phase 2 data engineering and stablecoin descriptive work at a formal reflection checkpoint.

## 1. Sixty-second project summary

This project studies digital assets through economic design rather than labels such as “coin,” “token,” or “Layer 1.” It converts monetary function, value-accrual mechanisms, supply design, rights and claims, backing, redemption, and risk into reproducible variables. The empirical objective is to test whether those mechanisms explain crypto valuation and stablecoin adoption, peg stability, depeg severity, and recovery.

The project now has a documented taxonomy, a frozen pilot universe, reproducible data collectors, identifier and evidence controls, stablecoin daily and event panels, a descriptive atlas, and explicit hypothesis-readiness gates. It is not yet at the headline-regression stage. That restraint is deliberate: the pipeline identifies which variables are genuinely source-ready and which remain incomplete.

## 2. What has been built

### Research design

- Defined hypotheses H1–H8 and translated the taxonomy into machine-readable schemas.
- Formalized value-accrual classifications including monetary use, gas demand, staking, burn, scarcity, collateral, governance, protocol economics, utility, and incentives.
- Defined stablecoin backing, redemption, reserve-quality, transparency, redemption-friction, and depeg-risk frameworks.
- Added effective-date rules so current token designs and risk scores are not backfilled into earlier periods.
- Created a machine-readable H5–H7 preregistration draft with objective readiness gates.

### Pilot universe

- 25 non-stable cryptoassets and 16 stable-value assets.
- Approximately 84.5% of the non-stable crypto market by the selection snapshot.
- Approximately 95.5% indicative combined market coverage.
- Includes market leaders, an intentionally limited growth sleeve, economic-design coverage assets, and UST/USTC as a failure control.

### Data and reproducibility

- Immutable raw API responses, retrieval timestamps, provider identifiers, and SHA-256 checksums.
- Daily long-price history from DeFiLlama and recent market-cap/volume data from CoinPaprika.
- Stablecoin circulation and global pegged-USD denominator histories from DeFiLlama.
- Binance venue OHLCV plus a new order-book snapshot layer.
- Explicit missingness, reconciliation, source-anomaly, and unsupported-asset audits.
- 66 automated tests currently pass.

## 3. Findings worth sharing

### Market coverage and adoption

- Stablecoin adoption panel: 21,249 asset-days across 14 primary assets.
- Exact-date global-share observations: 20,933.
- Latest primary-pilot circulation: approximately **$286.4 billion**.
- The pilot represents approximately **92.8%** of DeFiLlama's global pegged-USD circulation on the latest date.
- The DeFiLlama aggregate denominator covers all 2,791 requested calendar days from 2019-01-01 through 2026-08-22 without interpolation.

### Peg behavior and depeg episodes

- Stablecoin daily panel: 23,384 asset-day observations across 15 USD-target assets, including USTC as a failure control.
- 3,670 daily observations outside the 50-bps band.
- 533 mechanically identified depeg episodes using a 50-bps onset and 25-bps recovery rule.
- 465 episodes remain after excluding USTC from the primary sample.
- 519 episodes recovered and 14 were right-censored.
- Eight extreme episodes were flagged for source review rather than silently removed.
- FRAX has the highest primary-sample median absolute peg error and the most 50-bps episodes in the current descriptive atlas. This is descriptive, not causal.

### Chain distribution and trading

- Chain-distribution panel: 21,652 asset-days across all 14 primary assets.
- Chain-level sums reconcile within ±5% of reported supply on 97.2% of comparable rows.
- Recent CoinPaprika panel supplies 14,480 observations with market cap and volume across the broader asset universe, but only for a rolling one-year window.
- The H7 recent joined panel has 5,005 complete observations out of 5,068 across all 14 proposed assets.

### Market depth

- The free Binance collector now measures spreads, depth within 10/25/50 bps, fixed-size price impact, and fill rates.
- Nine of 14 primary stablecoins have an active Binance pair against USDT, USDC, or FDUSD.
- DAI, USDG, PYUSD, USDD, and GHO are explicitly unsupported by this venue-specific source.
- Current depth data are point-in-time snapshots and are not yet suitable for daily panel estimation.

### Stablecoin design scores

- Strict reserve-quality scores are currently available for USDC, PYUSD, and RLUSD; transparency scores are available for those assets and USDT.
- Redemption-friction scores remain withheld because required components are incomplete.
- These preliminary scores should not be presented as final results until point-in-time evidence and independent second coding are complete.

## 4. What the project can and cannot claim today

### Defensible claims

- The project has a reproducible economic-design taxonomy and a high-market-coverage pilot universe.
- It has a strong long stablecoin supply, peg, depeg-event, and chain-distribution foundation.
- Global pegged-USD supply share is source-audited and available.
- The recent H7 development panel has high coverage for supply, global share, chain distribution, and reported trading activity.
- Missing or conceptually different variables are kept separate rather than relabeled as usable substitutes.

### Claims to avoid

- Do not describe descriptive relationships as causal findings.
- Do not call reported volume “liquidity,” chain count “protocol integrations,” or chain balances “usage.”
- Do not describe a single Binance snapshot as historical or market-wide depth.
- Do not call the DeFiLlama denominator the universe of every stable-value asset; it is the global `peggedUSD` universe.
- Do not use current reserve or redemption scores for earlier dates.
- Do not present H5–H7 as analysis-ready or the preregistration as frozen.

## 5. Current hypothesis readiness

| Hypothesis area | Current status | Main blocker |
|---|---|---|
| H1–H4 and H8: crypto valuation/value accrual | Taxonomy and universe developed | Network, fee, revenue, staking, issuance, unlock, and valuation panels still need production coverage |
| H5: reserve quality and peg risk | Blocked | Point-in-time reserve scores and second-coder review |
| H6: redemption friction and recovery | Blocked | Incomplete strict redemption-friction components |
| H7: adoption, liquidity, integrations, usage | Partially ready | Historical market depth and validated integrations; usage is fixed as a separate four-asset exploratory analysis |

## 6. Recommended stopping and reflection point

**Stop after formalizing the current checkpoint; do not move directly into headline regressions.**

This is a good stopping point because the project has crossed from exploratory setup into a functioning research system. Continuing to add sources without a design review risks expanding the scope faster than the thesis can support. The next work should be governed by a narrowed empirical priority rather than by API availability.

Before resuming development:

1. Freeze and commit the current reproducible checkpoint, including generated manifests and test results.
2. Review whether the thesis should lead with stablecoins/H5–H7 or attempt balanced coverage of all H1–H8.
3. Confirm the primary analysis window: full 2019–2026 history, recent common window, or a two-tier design.
4. Confirm whether H7's headline sample must contain all 14 primary stablecoins or may use a source-defined liquidity subsample.
5. Complete an independent second-coder pass before design variables enter estimation.
6. Freeze outcome definitions, exclusions, stress windows, coverage thresholds, and model families before running headline tests.

### Recommended scope decision

For a master's project, the strongest defensible path is to make **stablecoin design, depeg risk, and adoption (H5–H7)** the empirical core. The broader crypto taxonomy and H1–H4/H8 can remain a valuable framework, descriptive atlas, and future-research extension. This produces a coherent thesis while preserving the larger platform already built.

## 7. Decisions to request from the team

1. Should stablecoins be the primary empirical thesis and the broader crypto valuation framework become a secondary contribution?
2. Is a recent, high-quality common window acceptable for H7, with long-history peg and supply analysis retained for H5/H6?
3. Should the H7 liquidity specification use a Binance-supported subsample, or must another venue/source be added to cover all 14 assets?
4. What minimum time coverage should order-book data meet before being considered analysis-ready?
5. Who will perform the independent classification and stablecoin-risk second coding?
6. Are protocol integrations and active users essential headline covariates, or may they be robustness/extension variables?

## 8. Suggested 25-minute meeting structure

1. **2 minutes — Research question:** economic design as the link between token structure and observable valuation/risk.
2. **5 minutes — What was built:** taxonomy, universe, schemas, reproducible pipelines, and preregistration gates.
3. **6 minutes — Evidence so far:** market coverage, stablecoin panel, depeg episodes, global share, and chain reconciliation.
4. **4 minutes — Methodological discipline:** effective dates, failure controls, missingness, anomaly review, and what is not yet claimed.
5. **5 minutes — Scope decision:** recommend stablecoins/H5–H7 as the empirical center.
6. **3 minutes — Assignments and next checkpoint:** second coding, data priorities, and preregistration freeze.

## 9. Likely questions and concise answers

**Why not run regressions now?**  
Several headline explanatory variables are incomplete or only cross-sectional. Running models now would allow source availability to determine the specification and could introduce look-ahead bias from current design scores.

**Why include USTC?**  
It is a failure control that reduces survivorship bias and validates whether the measurement system recognizes a known regime failure. It is excluded from primary-model rankings.

**Why use multiple providers?**  
No free provider supplies every required historical variable. Provider definitions are kept explicit, and cross-provider combinations are either reconciled or labeled diagnostic only.

**Is market share truly global?**  
It is global within DeFiLlama's `peggedUSD` universe. The terminology is deliberately narrower than “all stable-value assets.”

**What is the main contribution right now?**  
A transparent bridge from economic token design to reproducible empirical variables, combined with a stablecoin event and adoption dataset that makes readiness and limitations auditable.

**What is the next concrete deliverable after reflection?**  
A narrowed, second-coded, frozen preregistration and analysis dataset for the selected H5–H7 specifications.

## 10. Closing statement for the meeting

“The key progress is not merely that we collected crypto data. We built a system that distinguishes economic mechanisms, preserves point-in-time information, measures stablecoin failures consistently, and refuses to treat convenient proxies as concepts they do not measure. The decision now is not whether we can add more data; it is which empirical question we want this thesis to answer most convincingly.”
