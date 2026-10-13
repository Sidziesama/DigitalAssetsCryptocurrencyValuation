# Active cryptocurrency hypotheses and exact tests

This file is generated from the active research scope and empirical outputs. It distinguishes how the classification matrix enters each test; the matrix is not used identically in every hypothesis.

| ID | State | Observation unit | Matrix role |
|---|---|---|---|
| H1 | estimated_expanded_exploratory_scope_sensitive | asset-day | The classification matrix defines the researched asset universe but is not a regressor in H1. |
| H2 | estimated_exploratory_definition_sensitive | asset-day | VA_PROTOCOL and VA_BURN evidence determine the effective-dated capture state; the fee-by-capture interaction is the coefficient of interest. |
| H3 | estimated_multiasset_low_power | asset-level mean of repeated supply events | VA_BURN and VA_SCARCITY motivate the supply mechanism, but exact event quantities and dates—not binary codes—enter the test. |
| H4 | measurement_blocked | asset-day once three comparable positive-staking histories are complete | VA_STAKE selects positive-staking assets and structural non-staking controls; measured staked units must supply time variation. |
| H8 | estimated_exploratory_validation_window_frozen | asset cross-section | The complete 23 x 10 matrix is transformed into raw breadth and eight pre-specified group indicators; these are the regressors being compared. |

## H1 — Is greater network usage associated with higher network value?

**Sample.** 9 native networks; 792 observations across 88 common dates

**Outcome.** log market capitalization

**Predictors.** lagged log(1 + active addresses); lagged log(1 + transaction count)

**Controls.** asset fixed effects; date fixed effects

**Model.** `log(MarketCap_it) = asset_i + date_t + beta1*log1p(ActiveAddresses_i,t-1) + beta2*log1p(Transactions_i,t-1) + error_it`

**Inference.** Exact wild-cluster sign enumeration across 9 asset clusters, plus leave-one-asset-out sign stability.

**Exact inputs.** `data/processed/00_foundation/crypto_fundamentals_daily_coinmetrics.csv`, `data/processed/01_classification/crypto_expansion_activity_daily.csv`, `data/processed/00_foundation/market_daily_coinpaprika.csv`

**Exact outputs.** `data/processed/02_valuation/crypto_h1_activity_expansion.json`, `data/processed/02_valuation/crypto_h1_activity_expansion_panel.csv`

**Current result.** Active-address coefficient 0.0378, exact p=0.3438; transaction coefficient -0.0420, exact p=0.1367; neither confirmed.

**Main limitation.** Provider activity definitions differ across networks, addresses are not users, and active-address sign stability fails when XLM is omitted.

**Next gate.** Collect a longer fixed common window and preserve native-network versus token-contract scope separation.

## H2 — Is usage more valuable when fees mechanically reach the token or holders?

**Sample.** 11 chain and application systems; 3,971 fee-level observations

**Outcome.** log market capitalization; seven-day forward log return is secondary

**Predictors.** log(1 + fees); capture active; fees x capture; scope interactions

**Controls.** asset fixed effects; date fixed effects; chain-versus-application scope

**Model.** `Y_it = asset_i + date_t + beta1*Fees_it + beta2*Capture_it + beta3*(Fees_it*Capture_it) + scope terms + error_it`

**Inference.** Exact wild-cluster sign enumeration across 11 assets (2,048 assignments), leave-one-asset-out checks, non-overlapping return sensitivity, and strict-capture sensitivity.

**Exact inputs.** `data/processed/02_valuation/crypto_h2_exploratory_daily.csv`, `data/processed/01_classification/crypto_mechanism_state_asof.csv`

**Exact outputs.** `data/processed/02_valuation/crypto_h2_exploratory_estimates.json`, `data/processed/02_valuation/crypto_h2_small_cluster_inference.json`, `data/processed/02_valuation/crypto_h2_strict_capture_sensitivity.json`

**Current result.** Broad fee-capture interaction 0.1322, p=0.0820; strict interaction 0.0612, p=0.4775.

**Main limitation.** The result changes materially with the capture definition and is not a causal or return-prediction result.

**Next gate.** Preserve both definitions and seek a later non-overlapping outcome window.

## H3 — Do material supply increases weaken returns and material burns strengthen returns?

**Sample.** 17 events: 12 ARB unlocks, 4 BNB burns, and 1 UNI burn

**Outcome.** three-trading-day cumulative abnormal log return, direction-adjusted so positive supports H3

**Predictors.** event direction; gross token impact; impact share of pre-event circulating supply

**Controls.** asset return model estimated on the equal-weight crypto market over trading days -120 to -31

**Model.** `CAR_e[-1,+1] = sum(actual return - market-model expected return); unlock CAR is multiplied by -1 and burn CAR by +1`

**Inference.** Exact sign-flip randomization of asset-level mean direction-adjusted CARs; 8 assignments for 3 assets.

**Exact inputs.** `data/processed/02_valuation/crypto_h3_supply_event_ledger.csv`, `data/processed/03_risk/crypto_return_panel_daily.csv`

**Exact outputs.** `data/processed/02_valuation/crypto_h3_supply_event_estimates.csv`, `data/processed/02_valuation/crypto_h3_supply_event_analysis.json`

**Current result.** Mean direction-adjusted CAR -0.0113; 8/17 events match; exact asset-level p=0.2500.

**Main limitation.** 3 independent asset units yield valid but low-powered inference; scheduled and pre-announced events may be anticipated.

**Next gate.** Add official exact-date events from additional assets without selecting them from returns.

## H4 — Does staking reduce liquid float and affect liquidity or risk?

**Sample.** Fixed six-asset design: ETH, BNB, AAVE, BTC, UNI, and ARB

**Outcome.** turnover/liquidity proxy, volatility, and drawdown

**Predictors.** lagged staked share; staking entry/exit constraints

**Controls.** asset effects; date effects; market size and common market risk as predeclared in the eventual estimation specification

**Model.** `LiquidityOrRisk_it = asset_i + date_t + beta*StakedShare_i,t-1 + controls_it + error_it`

**Inference.** Not run. Estimation remains prohibited until the measurement-readiness rule is met and a final model specification is frozen.

**Exact inputs.** `data/processed/00_foundation/crypto_h4_bnb_stake_daily.csv`, `data/processed/00_foundation/crypto_h4_aave_legacy_stake_daily.csv`, `data/processed/01_classification/crypto_h4_eth_stake_daily.csv`

**Exact outputs.** `data/processed/01_classification/crypto_h4_measurement_audit.json`

**Current result.** Consensus assets ready=1; separate case studies ready=1; pooled estimation ready=False.

**Main limitation.** ETH has no 365-day active-effective-balance history because no archival Beacon endpoint is configured; legacy stkAAVE is not comparable consensus stake.

**Next gate.** Configure ETH_BEACON_ARCHIVE_API_URL and collect the exact 365-day ETH series.

## H8 — Do theory-defined economic-function groups explain valuation better than a raw function count?

**Sample.** 23 classified assets; 22 meet the primary market-cap outcome coverage rule

**Outcome.** mean log market capitalization over 25 August 2025 to 22 August 2026

**Predictors.** raw ten-function breadth; eight theory-defined group indicators

**Controls.** predeclared architecture and sample sensitivities; no causal controls in the primary single-predictor comparison

**Model.** `log(MarketCap_i) = alpha + beta*FunctionMeasure_i + error_i; compare leave-one-asset-out RMSE across measures`

**Inference.** Seeded 100,000-draw outcome permutations, 10% Benjamini-Hochberg FDR across eight group tests, leave-one-asset-out RMSE, and five predeclared sensitivities.

**Exact inputs.** `data/processed/01_classification/crypto_verified_universe_profiles.csv`, `data/processed/00_foundation/market_daily_coinpaprika.csv`, `data/processed/03_risk/crypto_return_panel_daily.csv`

**Exact outputs.** `data/processed/02_valuation/crypto_h8_verified_universe_results.csv`, `data/processed/02_valuation/crypto_h8_verified_universe_summary.json`, `data/processed/02_valuation/crypto_h8_oos_readiness.json`

**Current result.** Best group bundle_financial_integration; LOAO RMSE 1.7594 versus breadth 1.8109.

**Main limitation.** The group was selected in the discovery sample; this is not independent validation or a causal valuation model.

**Next gate.** Wait for the fixed 23 August 2026 to 22 August 2027 validation window and do not retune the group or metric.
