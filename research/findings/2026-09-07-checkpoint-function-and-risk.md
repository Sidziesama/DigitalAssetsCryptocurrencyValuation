# Checkpoint: economic function and risk exposure

7 September 2026. Every figure below is reproducible from this repository; the artifact backing each claim is named in line. Two new frozen experiments were specified and estimated since the previous checkpoint, and nothing already frozen was modified.

## 1. What was added at this checkpoint

**P1_H6, the function-versus-risk test** (`config/crypto_function_risk_exposure.json`, estimated by `crypto_function_risk_exposure`). Specified and frozen before estimation and before any further asset is classification-verified, so it cannot be fitted to the descriptive sorts that motivated it, and later classification work cannot be steered by its outcome.

**Long-panel mechanism event study** (`config/crypto_mechanism_event_study_long.json`). The same event design applied to the 2019-2026 return panel under a stated transition rule, which admits a third event and roughly ten times the placebo evidence.

## 2. P1_H6: does economic function explain risk exposure?

### Design

All assets are measured on one common window, 24 March 2023 to 22 August 2026 (1,248 days, set by the ARB listing date), so that beta, volatility, and drawdown are comparable rather than reflecting different histories. Outcomes are market beta against the equal-weighted crypto market, annualized realized volatility, and maximum peak-to-trough log drawdown. Predictors are the eight theory-defined bundle flags plus raw function breadth. Every regression carries mean log dollar volume as a size control, because the largest assets are also the lowest-beta assets and the classification must be shown to add something beyond size.

Two samples are reported separately and never pooled. The **verified core** is the six assets whose ten-code classification is evidence-verified, with exact enumeration of all 720 permutations. The **provisional universe** is the twenty assets that meet the window-coverage rule, coded from the provisional design matrix, with fixed-seed Monte Carlo permutation (20,000 draws, seed 20260907). Provisional codes have not passed evidence review; those results are hypothesis-generating and must be re-estimated when classification completes.

Benjamini-Hochberg false-discovery-rate q-values are computed across all 27 predictor-by-outcome tests within each sample. This was declared in the specification, not added after seeing the results.

### Result

**The hypothesis is not supported at this checkpoint.** In the provisional universe, three of 27 tests reach p ≤ 0.05 against 1.35 expected by chance alone, and **none survive a 10 percent false-discovery rate** (smallest q = 0.405). In the verified core, no test reaches p ≤ 0.05; with six assets and binary predictors the smallest attainable exact p-value is 0.067, so that sample cannot reject anything.

The three strongest provisional associations, all leave-one-out sign-stable in 20 of 20 samples:

| Outcome | Predictor | Coefficient | p | q (FDR) |
|---|---|---|---|---|
| Max drawdown (log) | Transaction service demand | +0.911 | 0.027 | 0.405 |
| Max drawdown (log) | Monetary store | +0.836 | 0.032 | 0.405 |
| Market beta | Monetary store | −0.227 | 0.045 | 0.405 |

Signs point the way the descriptive sorts did: assets classified as money or as gas/utility tokens have shallower drawdowns and lower beta after controlling for size. Unadjusted group means in the provisional universe (`crypto_function_risk_assets.csv`):

| Bundle | n+ | beta+ | drawdown+ | n− | beta− | drawdown− |
|---|---|---|---|---|---|---|
| Monetary store | 14 | 0.93 | −1.44 | 6 | 1.19 | −2.37 |
| Transaction service demand | 15 | 0.97 | −1.48 | 5 | 1.10 | −2.42 |
| Financial integration | 9 | 0.91 | −1.48 | 11 | 1.08 | −1.91 |
| Control rights | 11 | 1.04 | −2.06 | 9 | 0.96 | −1.30 |
| Holder capture | 13 | 1.02 | −1.84 | 7 | 0.98 | −1.49 |

The ordering is consistent and the magnitudes are economically large (a drawdown gap of roughly 0.9 log points between monetary and non-monetary assets). The multiple-testing correction is what stops this from being a finding, and correcting was the right call: with 27 tests, three hits at the 5 percent level is close to what chance produces.

### What this rules out and what it leaves open

Holder capture, the mechanism at the center of H2, does not predict any risk outcome (p ≥ 0.35 for all three). Raw function breadth does not either. The signal, such as it is, sits entirely in the monetary and transaction-demand bundles, which is the same place the bundle comparison found its only usable predictor.

Two caveats sharpen the next step. First, in the verified core the size control and the classification are nearly collinear (BTC, ETH, BNB are simultaneously the largest, the lowest-beta, and the monetary-positive assets), so the six-asset coefficients are unstable, and the control-rights sign flips against the uncontrolled sort. Six assets cannot separate function from size. Second, the provisional matrix codes fourteen of twenty assets as monetary, including LTC, BCH, XLM, ZEC, and DOGE. That is exactly the generosity the verified rule is designed to remove, and it is why the provisional result cannot stand as evidence.

## 3. Long-panel mechanism event study

The transition rule admits only ledger events that differ from the preceding recorded state for the same asset and code. That excludes initial codings at founding dates and the TRON entry on the H2 panel's first day, and it admits the April 2025 Aave buyback activation, which falls outside the one-year H2 window but inside the return panel. Three events, each against twenty-two uncontaminated controls and roughly 280 non-overlapping calendar placebos.

| Event | Transition | Expected | Difference in differences | Sign | p (asset) | p (calendar) |
|---|---|---|---|---|---|---|
| Aave buyback activation, 9 Apr 2025 | activation | positive | +0.0107 | correct | 0.261 | 0.234 |
| UNIfication fee-to-burn, 27 Dec 2025 | activation | positive | −0.0088 | wrong | 0.217 | 0.248 |
| Aave buyback pause, 19 Apr 2026 | suspension | negative | +0.0010 | wrong | 0.739 | 0.922 |

One of three carries the expected sign; none reject at 10 percent. The Aave pause is the informative case: on the one-year market-cap panel it looked like the strongest event in the study (−13.4 percent, p = 0.18), and on the long return panel with twenty-two controls it is essentially zero with the wrong sign. A result that reverses under a different outcome measure and a larger control pool was never a finding. Both versions are retained side by side rather than the weaker one being dropped.

## 4. Where the research now stands

Defensible today:

1. Economic function can be classified reproducibly from dated primary evidence, reconciled by blind review (kappa 1.0 on the ten reviewed decisions), and it separates assets that share an architecture.
2. The fee-capture association in H2 is stable in sign and fragile in definition. Pooled interaction 0.132 (p = 0.082) under the broad treasury rule falls to 0.061 (p = 0.478) under the strict holder-capture rule.
3. A single market factor explains a median 60 percent of daily variation across 24 assets, and lagged beta is negatively priced (t = −2.1). Any function-based claim must clear that baseline.
4. Function-based risk differences run in a consistent direction and with large magnitudes, but do not survive multiple-testing correction on provisional classifications.

Not defensible, and stated as such: any claim that economic function predicts returns, and any market-wide claim about function and risk while nineteen assets remain unverified.

## 5. Next

1. Verify the nineteen remaining assets in three evidence tranches: rule-mechanical codes (gas, stake, scarcity, burn, protocol), ninety-day data-pull codes (collateral, monetary), and judgment codes (governance, utility, incentive) under the blind-review protocol. The generous provisional monetary coding is the specific thing this fixes.
2. Re-estimate the already-frozen P1_H6 on verified codes. The specification is locked; only the classification input changes.
3. Collect point-in-time unlock and issuance events so H3 becomes identification-ready.
4. Resume H4 once an archival Ethereum consensus endpoint is available.

## Artifacts

| Claim | Artifact |
|---|---|
| P1_H6 specification | `config/crypto_function_risk_exposure.json` |
| P1_H6 results and per-asset risk measures | `data/processed/empirical/crypto_function_risk_exposure.json`, `crypto_function_risk_tests.csv`, `crypto_function_risk_assets.csv` |
| Long-panel event study | `config/crypto_mechanism_event_study_long.json`, `data/processed/empirical/crypto_mechanism_event_study_long.json` |
| Verified classification | `data/processed/evidence/crypto_phase1_taxonomy_profiles.csv` |
| H2 and strict-rule sensitivity | `data/processed/empirical/crypto_h2_small_cluster_inference.json`, `crypto_h2_strict_capture_sensitivity.json` |
| Factor baseline | `data/processed/empirical/crypto_return_factor_baseline.json` |
| Full status | `data/processed/empirical/crypto_findings_summary.json` |

Reproduce with `python -m src.pipeline.run_stages --repo . --offline`.
