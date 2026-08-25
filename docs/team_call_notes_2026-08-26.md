# Digital Asset Valuation — Team Call Notes

**Call date:** August 26, 2026  
**Current stage:** Research design and data foundation completed; stablecoin empirical work partially analysis-ready; scope and preregistration decisions required before headline estimation.

## Opening update — 60 seconds

“The project asks whether the economic design of a digital asset—how it creates demand, captures value, controls supply, grants rights, and manages backing or redemption—helps explain valuation, adoption, liquidity, and risk. We have moved from a conceptual taxonomy to a reproducible research system. We now have a high-coverage pilot universe, formal classification rules, source-controlled pipelines, a stablecoin daily panel, depeg episodes, adoption and global-share measures, chain-distribution measures, and initial liquidity and DeFi-integration snapshots. The main decision now is whether to make stablecoins the empirical core of the thesis and freeze H5–H7 before estimation.”

## What to show on the call

### 1. Start with the project map

Screen-share `README.md` and explain the flow:

> Economic taxonomy → formal classifications → immutable source data → validated panels → descriptive atlas → preregistration → empirical tests.

Emphasize that the contribution is not simply collecting crypto prices. It is connecting economic mechanisms to testable variables while preserving effective dates, missingness, source definitions, and failure cases.

### 2. Show the pilot-universe decision

Open `research/findings/2026-08-22-pilot-universe.md`.

- 25 non-stable cryptoassets.
- 16 stable-value assets.
- Approximately 84.5% of the non-stable crypto market at selection.
- Approximately 95.5% indicative combined market coverage.
- Includes market leaders, a limited growth sleeve, structurally different assets, and USTC as a failure control.

Talking point: “We selected by market relevance, volume, data accessibility, economic-design coverage, and growth relevance—not by personal preference.”

### 3. Show the stablecoin descriptive chart

Open `outputs/generated/stablecoin_median_ape.svg`.

Explain that it presents median absolute peg error and is descriptive rather than causal. FRAX currently has the highest primary-sample median absolute peg error and the most mechanically identified 50-bps episodes.

### 4. Show the depeg-event results

Open `research/findings/stablecoin-daily-panel-and-depeg-events.md`.

- 23,384 asset-day observations.
- 15 USD-target stablecoins, including USTC as a failure control.
- 3,670 daily 50-bps breach observations.
- 533 depeg episodes using a 50-bps onset and 25-bps recovery rule.
- 465 primary-sample episodes after excluding USTC.
- 519 recovered and 14 right-censored episodes.
- Eight extreme episodes retained in a review queue.

Talking point: “The episode rules are mechanical and reproducible. Missing days censor an event instead of being silently bridged, and extreme observations are reviewed rather than automatically deleted.”

### 5. Show adoption and global market coverage

Open `research/findings/stablecoin-adoption-panel.md`.

- 21,249 stablecoin asset-days across 14 primary assets.
- 20,933 observations with exact-date global pegged-USD share.
- Latest pilot circulation: approximately $286.4 billion.
- Pilot coverage: approximately 92.8% of DeFiLlama's global pegged-USD circulation.
- Global denominator coverage: 2,791 of 2,791 requested days.

Talking point: “We can now measure actual global pegged-USD share rather than only a share of our selected sample.”

### 6. Show chain distribution and H7 readiness

Open `research/findings/stablecoin-chain-distribution.md`, followed by `research/findings/stablecoin-h7-readiness.md`.

- 21,652 chain-distribution asset-days.
- All 14 primary assets covered.
- 97.2% of comparable chain totals reconcile within ±5% of reported supply.
- Recent H7 joined panel: 5,005 complete rows out of 5,068.
- All 14 assets meet the proposed 80% recent-coverage threshold for currently implemented variables.

Clarify that chain distribution is a breadth and concentration measure, not transaction usage or protocol adoption.

### 7. Show the new liquidity and integration work

Open:

- `research/findings/stablecoin-market-depth.md`
- `research/findings/stablecoin-yield-integrations.md`

Market depth:

- Spread, 10/25/50-bps order-book depth, fixed-size price impact, and fill rates are implemented.
- Nine of 14 stablecoins have supported Binance pairs.
- Current observations are venue-specific snapshots, not historical liquidity panels.

Yield integrations:

- 16,844 DeFiLlama yield pools inspected.
- All 14 primary stablecoins have at least one matched yield project.
- 5,033 matched asset-pool rows.
- Matching uses exact symbol components and avoids substring matches.
- Contract-address validation and historical snapshots are still required.

## Progress by phase

| Phase | Status | Evidence |
|---|---|---|
| Economic taxonomy and classification architecture | Substantially complete | Formal economic-function, value-accrual, claims, backing, and redemption rules |
| Pilot-universe construction | Complete for current checkpoint | 41 selected assets with high indicative market coverage |
| Identifier registry and provenance | Implemented | Provider IDs, immutable raw files, timestamps, metadata, and checksums |
| Historical price and supply data | Strong for stablecoins; mixed for other variables | Long DeFiLlama histories plus explicit coverage audits |
| Stablecoin peg and event panel | Complete for descriptive work | Daily peg errors, breach bands, recovery rules, event table, anomaly review |
| Stablecoin adoption/global share | Strong | Long supply growth and exact-date global pegged-USD share |
| Chain-distribution measures | Strong | Full primary-sample coverage and 97.2% reconciliation rate |
| Recent trading activity | Implemented for recent window | CoinPaprika market cap and reported volume |
| Market depth | Snapshot stage | Binance order-book measures for nine assets |
| Protocol integrations | Proxy snapshot stage | DeFiLlama yield-pool project/chain/pool counts |
| Transaction activity and address activity | Partial | Long free histories for USDT, USDC, DAI, and TUSD; ten primary assets unsupported |
| Reserve/redemption scoring | Partially implemented | Some strict reserve and transparency scores; redemption scores incomplete |
| Preregistration and estimation | Draft only | H5–H7 draft exists but is not frozen |

## Research questions and readiness

### Broader crypto questions

- **H1:** Does economically meaningful network usage explain market capitalization?
- **H2:** Do fees and revenue matter more when an active token mechanism captures that value?
- **H3:** Do issuance and unlocks predict lower forward returns?
- **H4:** How does staking affect liquid float, spreads, returns, and volatility?
- **H8:** Do multiple active and material token functions produce a valuation premium?

These have a developed taxonomy and sample, but their production fundamentals panels are not yet complete.

### Stablecoin questions

- **H5:** Does higher reserve quality reduce peg error, depeg probability, severity, and recovery time?
- **H6:** Does greater redemption friction worsen deviations, particularly during stress?
- **H7:** Do liquidity, integrations, usage, and supply growth explain stablecoin market share and inflows?

H5 and H6 are blocked by point-in-time evidence and second coding. H7 uses a fixed two-tier design: all 14 assets remain in the primary supply/share analysis, while USDT, USDC, DAI, and TUSD form a separate exploratory usage panel. Historical liquidity and validated integrations remain incomplete.

## What we have learned so far

1. A carefully chosen 41-asset universe captures most of the relevant market while retaining meaningful economic diversity.
2. Stablecoins offer the clearest empirical route because supply, peg behavior, and depeg episodes can be measured consistently over a long period.
3. Depeg behavior is heterogeneous; failures cannot be understood from the “stablecoin” label alone.
4. The primary stablecoin sample accounts for most global pegged-USD circulation.
5. Cross-chain breadth is measurable and well reconciled, but it cannot substitute for actual usage.
6. Liquidity differs materially across assets and venues, but repeated order-book observations are needed before formal inference.
7. Free data are sufficient for a strong project if provider definitions and time limitations remain explicit.
8. Current classifications or disclosures cannot be backfilled historically without introducing look-ahead bias.

These are preliminary and descriptive findings. The project has not yet confirmed or rejected H1–H8.

## What not to claim

- Do not call correlations causal.
- Do not call reported volume executable liquidity.
- Do not call chain count protocol integrations or users.
- Do not call the DeFiLlama denominator every stable-value asset; it is the pegged-USD universe.
- Do not describe current Binance snapshots as historical or market-wide liquidity.
- Do not describe yield-pool matches as exhaustive DeFi integrations.
- Do not present current reserve scores as historical.
- Do not call the H5–H7 preregistration frozen.

## Recommended project reflection point

This is a good formal checkpoint. The research system works, the stablecoin descriptive dataset is substantial, and the remaining limitations are clearly identified. Before collecting more variables or running regressions, the team should decide what the thesis must answer most convincingly.

Recommended direction:

> Make stablecoin design, depeg risk, and adoption—H5 through H7—the empirical center. Retain H1–H4 and H8 as the broader valuation framework and a future extension.

This produces a coherent master's project and prevents the effort from becoming an overly broad data-platform exercise.

## Decisions to request from the team

1. Should H5–H7 become the primary empirical thesis scope?
2. Should H7 use a recent high-quality common window, while H5/H6 retain the longer peg and supply history?
3. Is a Binance-supported liquidity subsample acceptable, or is multi-venue coverage required?
4. What minimum number and frequency of order-book snapshots will qualify market depth for analysis?
5. Confirm the recorded decision that transaction/address activity remains a four-asset exploratory extension rather than a requirement for the 14-asset primary specification.
6. Who will independently second-code the taxonomy and stablecoin risk inputs?
7. When should the sample, exclusions, outcomes, and model families be frozen?

## Next development steps

### Immediate

1. Preserve the fixed four-asset exploratory usage subsample; do not expand or replace it based on observed results.
2. Validate yield-pool matches using chain-qualified contract addresses.
3. Accumulate repeated order-book and integration snapshots.
4. Complete point-in-time reserve and redemption evidence.
5. Produce the independent second-coder worksheet and agreement statistics.

### Before estimation

1. Resolve the USDG anomaly and named stress-event review queue.
2. Select the final analysis window and minimum coverage thresholds.
3. Freeze primary outcomes, lag structures, exclusions, controls, and robustness tests.
4. Freeze the H5–H7 preregistration.
5. Run descriptive correlations and diagnostics without treating them as headline tests.

### Final empirical stage

1. Estimate H5 reserve-quality models.
2. Estimate H6 redemption-friction and stress-interaction models.
3. Estimate H7 market-share and inflow models.
4. Report effect sizes, confidence intervals, diagnostics, multiple-testing adjustments, and out-of-sample results.

## Suggested 20-minute call structure

1. **2 minutes:** research objective and why economic design matters.
2. **4 minutes:** taxonomy, sample, and reproducible architecture.
3. **6 minutes:** stablecoin panel, depeg, adoption, and chain findings.
4. **3 minutes:** liquidity and integration snapshots.
5. **2 minutes:** limitations and readiness gates.
6. **3 minutes:** request the seven scope and methodology decisions.

## Closing line

“We now have more than an idea and more than a collection of APIs: we have a reproducible research design that connects economic mechanisms to measurable outcomes. The next step should be to narrow and freeze the question we want to answer, then complete only the data required for that answer.”
