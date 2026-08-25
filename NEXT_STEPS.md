# Next Steps

## Stage 1 — Classification validation

- Produce a blind second-coder worksheet from the frozen codebook.
- Independently code all 41 assets.
- Calculate Cohen's kappa for each `VA_*` and claims field.
- Adjudicate disagreements and append effective-dated revisions.

**Exit criterion:** complete evidence trail and acceptable agreement, with low-agreement rules revised before empirical work.

## Stage 2 — Stablecoin scoring

- Archive current terms, reserve reports, attestations/audits, and protocol documentation.
- Extract reserve weights, duration/liquidity proxies, credit quality, concentration, segregation, bankruptcy-remoteness evidence, and assurance quality.
- Extract redemption eligibility, minimums, fees, settlement time, operating hours, intermediaries, suspension rights, and in-kind rights.
- Calculate component and composite reserve-quality, transparency, and redemption-friction scores.

**Exit criterion:** every score is reconstructible from visible components and dated evidence.

## Stage 3 — Data-coverage audit

- Map canonical CoinGecko IDs, chain IDs, contracts, migrations, aliases, and wrapped representations.
- Test daily price, market cap, supply, volume, fees, revenue, TVL, staking, and network-activity coverage from 2019 through 2026.
- Test intraday price and liquidity coverage for stablecoin stress episodes.
- Produce a missingness matrix and flag assets below the preregistered coverage threshold.

**Exit criterion:** final sample rule can be applied without outcomes-based substitutions.

### Free-source implementation status

- DeFiLlama supplies the full active-window daily price panel and supported stablecoin circulation histories.
- CoinPaprika supplies a no-key rolling one-year panel of daily price, reported market cap, and 24-hour volume, with an explicit provider-ID audit.
- Binance supplies keyless venue-specific daily OHLCV for 24 of 25 non-stable crypto assets; listing-window coverage and quote-stablecoin units remain explicit.
- CryptoCompare pagination is implemented, but its live service now requires an API key and therefore remains inactive until credentials are supplied.
- Full 2019–2026 market-cap and volume histories remain a separate coverage gap; recent free data must not be represented as full-period coverage.

## Stage 4 — Production pipeline

- Implement source-specific ingestion into immutable dated raw partitions.
- Add retrieval metadata, checksums, schema validation, UTC normalization, and source-version tracking.
- Build processed asset-day, stablecoin-day, and stablecoin-event panels.
- Add automated tests for uniqueness, continuity, stale prices, supply jumps, and cross-source tolerances.

**Exit criterion:** clean rebuild from frozen raw inputs.

## Stage 5 — Descriptive atlas and preregistration

- Create sample composition, coverage, missingness, distributions, and correlations.
- Create stablecoin depeg-event and recovery summaries.
- Evaluate value-accrual breadth and reserve/redemption score distributions.
- Freeze primary outcomes, specifications, exclusions, robustness tests, and hypothesis families.

**Exit criterion:** preregistration snapshot approved before headline estimation.

### Stablecoin empirical-panel implementation

- Build completed daily peg-error fields at 10/25/50/100/500-bps bands.
- Build completed primary daily episodes using 50-bps onset and 25-bps recovery, including recovery, censoring, maximum deviation, and area-under-deviation metrics.
- Next: review the event atlas, define named stress windows, add intraday sources, and preregister the H5–H7 daily and intraday specifications.
- H7 supply/adoption panel now includes exact-date 1/30/90-day growth, pilot share, total pilot supply, HHI, and DeFiLlama global pegged-USD supply share; market depth, integrations, and usage remain pending.
- H7 checkpoint audit joins exact-day lagged supply, chain-distribution, and recent trading proxies and emits objective asset/variable coverage gates; unresolved conceptual data classes remain hard failures.
- Binance keyless order-book snapshot collection now measures spreads, fixed-band depth, fill rates, and fixed-size price impact for supported primary/growth stablecoins. Next, schedule repeated observations and require a preregistered time-coverage threshold before using market depth in H7 estimation.
- DeFiLlama yield pools now provide a conservative current protocol-integration proxy using exact symbol components. Next, validate matches with chain-qualified contract addresses and accumulate historical snapshots before headline H7 use.
- H7 now uses a fixed two-tier design: the primary supply/share specification retains all 14 coverage-qualified stablecoins, and a separate exploratory usage specification is restricted to USDT, USDC, DAI, and TUSD. Do not broaden or replace this subsample based on results.

## Stage 6 — Empirical analysis

- H1/H2: network activity, fees, and active value capture.
- H3/H4: net issuance, unlocks, staking, liquidity, returns, and volatility.
- H5/H6: reserve quality, redemption friction, stress, depeg onset, and recovery.
- H7: stablecoin liquidity, integrations, usage, inflows, and market share.
- H8: active multi-function breadth and valuation premium.

Report effect sizes, confidence intervals, diagnostics, preregistered robustness results, and out-of-sample performance.
