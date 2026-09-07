# Economic Functions and Cryptoasset Valuation

Draft abstract and progress report, 7 September 2026. Every number below is read from a committed artifact in `data/processed/` at commit `f7f625b`.

## Draft abstract

Cryptoassets are usually sorted by technical architecture or marketing label, neither of which identifies a valuation model. This paper builds a reproducible classification of cryptoassets by economic function and asks whether function explains value and risk. Ten binary functions (monetary use, gas demand, staking, burn, scarcity, collateral, governance, protocol capture, utility, and incentives) are defined by written rules, scored from dated primary evidence, reconciled through blind independent review, and grouped into eight theory-defined bundles fixed before estimation. Architecture is recorded as context and never as a function. On a six-asset verified core the classification separates assets that share an architecture and unites assets that do not, and it isolates one boundary that the literature blurs, namely that governance authority over a treasury is not value capture unless value mechanically terminates at the token. An eleven-asset daily panel over one year finds that fee activity is more strongly associated with market value when a live capture mechanism exists, with an exact wild-cluster p-value of 0.082 under the broad capture definition. That association halves and loses significance under the strict definition, so we report it as a definition-dependent exploratory result rather than a finding. Neither raw function breadth nor bundle count predicts value across the core. A twenty-four-asset daily return panel from 2019 to 2026 shows that a single market factor explains a median sixty percent of daily variation and that lagged beta is negatively priced, while descriptive sorts on the verified core show monetary and collateral functions identifying low-beta, shallow-drawdown assets and governance identifying the reverse. The contribution is an auditable path from economic theory to classification rules, effective-dated evidence, and falsifiable tests, together with the finding that the credible role of economic function is in explaining risk exposure rather than return.

## What has been built

The repository is a single reproducible pipeline of sixty-four modules organized in seven frozen stages, with 224 unit tests and a test that every module appears in exactly one stage. Every experiment has a specification file written before its estimation, and every classification carries a dated source.

### Classification architecture

Four layers. Architecture context (proof-of-work base layer, proof-of-stake base layer, application token, rollup governance token) is recorded and excluded from the economic codes. Ten economic functions each have a written rule, a set of value indicators, and a three-state verdict of verified positive, verified negative, or unresolved. Eight theory-defined bundles map every function to exactly one bundle. Value indicators are tied to what the repository can measure through a research map that records, for each of thirty-four indicators, whether it is an observed series, a proxy series, documentary evidence only, or not yet collected.

The six-asset core (BTC, ETH, BNB, UNI, AAVE, ARB) is fully verified at sixty of sixty decisions with no unresolved cells. Independent blind review of the ten capture decisions added for the H2 expansion reconciled at ten of ten with Cohen's kappa of 1.0 after one adjudication. Burn and protocol-capture states are effective-dated in a mechanism ledger covering eleven assets, so that later evidence is never backfilled into earlier observation dates.

### Verified profiles

| Asset | Architecture context | Functions active | Breadth | Bundles |
|---|---|---|---|---|
| BTC | proof-of-work base layer | monetary, scarcity, collateral | 3 | 2 |
| ETH | proof-of-stake base layer | monetary, gas, stake, burn, collateral, protocol, utility | 7 | 6 |
| BNB | proof-of-stake family base layer | all except scarcity | 9 | 8 |
| UNI | application token | burn, governance, protocol | 3 | 3 |
| AAVE | application token with protocol-risk staking | stake, collateral, governance, incentive | 4 | 4 |
| ARB | rollup governance token | governance, incentive | 2 | 2 |

### Measurement readiness

Monetary, gas, and collateral functions are measured by observed series. Staking, burn, and protocol capture are proxied (BNB consensus stake and legacy stkAAVE series, DeFiLlama holder revenue). Scarcity, governance, utility, and incentive remain documentary. Documentary functions classify assets but cannot yet enter a valuation test as continuous variables.

## What has been found

### The classification itself

Architecture and function are different axes. Two proof-of-stake base layers differ by two functions and two application tokens share one. Collateral and governance are the most common functions on the core (four of six) and scarcity the rarest (BTC only).

The governed-treasury boundary is the taxonomy's sharpest rule. ARB and ADA tokenholders control treasuries funded by network revenue, but evidenced spending funds ecosystem activity and never mechanically reaches the token. Both are coded as governance, not protocol capture. This one rule changes the headline H2 result, which is why it is reported as a sensitivity.

### H2, fee activity and value capture

Eleven assets, 3,971 asset-days, 26 August 2025 through 21 August 2026, two-way fixed effects, exact Rademacher wild-cluster inference over 2,048 assignments. Under the frozen broad capture definition the pooled fee-by-capture interaction is 0.132 (p = 0.082) and positive in every leave-one-asset-out sample; the nine-chain estimate is 0.141 (p = 0.125). Under the strict definition, applied to a copy of the panel through a pre-listed override, the pooled estimate is 0.061 (p = 0.478) and the chain estimate 0.060 (p = 0.555). No forward-return specification, overlapping or non-overlapping, rejects zero. The specification was frozen after pilot results were observed, so nothing here is confirmatory.

### H8 and the bundle comparison

Raw function breadth against mean log market value is positive but never significant (five-asset pilot p = 0.70; six-asset extension slope 0.48, p = 0.44, positive in all six leave-one-out samples). Bundle count does not beat raw breadth on either outcome because the two are nearly collinear on this core (rank correlation 0.96). The only predictor that lowers leave-one-out prediction error is the monetary-store bundle (Spearman 0.88, exact p = 0.10), and that result is partly a size story because the three monetary positives are the three largest assets.

### Mechanism events

Two effective-dated state changes fall inside the panel with full thirty-day windows. The UNIfication fee-to-burn activation (27 December 2025) shows a negative valuation difference against ten controls (about minus four percent, placebo p above 0.36). The Aave buyback pause (19 April 2026) shows the expected negative sign (about minus thirteen percent, asset-placebo p = 0.18, calendar-placebo p = 0.15) while fees moved the opposite way. Neither rejects at ten percent.

### Returns and risk

Twenty-four assets, 52,116 asset-days from 2019 to 2026. Median market beta 1.03 and median R-squared 0.60 against an equal-weighted market return. BTC is the low-beta asset (0.67) and the rollups the high-beta tail (ARB 1.27, OP 1.40, both with strongly negative alphas). Daily Fama-MacBeth cross-sections with Newey-West errors show a negative lagged-beta premium (t = minus 2.1), flat momentum, and no volatility premium. Descriptive sorts on the verified core over 2023 to 2026 show monetary-store positives at beta 0.70 with a maximum log drawdown of minus 0.89 against 1.21 and minus 2.13 for the negatives; collateral positives look the same; governance positives are the mirror image. With three assets on each side these are previews, not tests.

### H1, H3, H4

H1 (activity and value, four assets) has positive coefficients that do not reject zero under exact four-cluster inference. H3 (supply growth and returns) has the wrong sign and within-window variation only for BTC and ETH, so it is a data-readiness result. H4 (staking and float) is source-ready for BNB and partially for AAVE but blocked on an archival Ethereum consensus endpoint.

## What the evidence supports today

Three claims are defensible now. First, economic function can be classified reproducibly and separates assets that architecture groups together. Second, the fee-capture association is real in sign and fragile in definition, and the fragility is itself informative about where value capture begins. Third, the functions the taxonomy calls money and financial integration identify the low-beta, shallow-drawdown assets, which points the empirical program toward risk exposure rather than return prediction.

One claim is not yet defensible. Any statement about economic function and returns across the market needs the remaining nineteen assets classified. Six assets support description only.

## Next

1. Freeze a P1_H6 specification, economic function predicts market beta, realized volatility, and drawdown across the full universe with dollar volume as the size control, before any further asset is classified.
2. Verify the nineteen remaining assets in three evidence tranches (rule-mechanical codes, ninety-day data-pull codes, judgment codes) under the existing blind-review protocol.
3. Extend the mechanism event study to pre-2025 ledger events using the long return panel.
4. Resume H4 once an archival Ethereum consensus endpoint is available.
