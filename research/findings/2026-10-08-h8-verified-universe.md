# H8 verified-universe result — 8 October 2026

## Question

Do theory-defined economic-function groups explain cross-asset valuation better than simply counting how many functions a cryptocurrency performs?

## Design

The design was frozen in Git commit `dcd87ab` before estimation. It uses the 23 human-verified cryptoasset profiles, the 25 August 2025–22 August 2026 measurement window, leave-one-asset-out (LOAO) prediction error, 100,000 seeded outcome permutations, and Benjamini–Hochberg false-discovery control across all eight single-group tests. This is a post-pilot exploratory cross-section, not a causal test.

The primary market-cap outcome meets the pre-specified 80% coverage rule for 22 assets; TON remains in the classification universe but lacks sufficient selected-source market-cap observations. Risk and volume outcomes cover 22 assets; HYPE lacks sufficient observations in the selected return panel.

## Primary findings

- Raw function breadth has a LOAO RMSE of **1.811 log points**.
- The best single theory group is **financial integration** (collateral use), with a LOAO RMSE of **1.759**—a modest 2.8% improvement over raw breadth.
- Financial integration has the strongest valuation association: **+2.872 log market-cap units**, permutation p = **0.0027**, BH q = **0.0217**.
- Monetary/store-of-value use (**+2.035**, p = **0.0272**, q = **0.0925**) and supply absorption (**+1.804**, p = **0.0347**, q = **0.0925**) also pass the pre-specified 10% FDR threshold.
- The other five single groups do not pass FDR control. Control rights and subsidized participation have negative point estimates; these are reported rather than suppressed.
- Merely replacing raw breadth with the number of active bundles worsens prediction (RMSE **1.929**).
- Adding holder capture to raw breadth does not improve prediction (RMSE **1.869**). The service-demand-plus-capture model also underperforms (RMSE **2.185**).

## Sensitivity interpretation

Financial integration and supply absorption retain their coefficient direction in all five predeclared sensitivities. Monetary/store use is stable in four of five. This satisfies the frozen decision rule for favoring theory groups, but only narrowly: one group improves prediction modestly, and the sample remains small and heterogeneous.

## Plain-language conclusion

The evidence does **not** say that “more functions always mean more value.” It suggests that *which* economic job a token performs matters more than a raw function count. In this sample, integration into financial activity—especially usable collateral—contains the clearest valuation information. Monetary/store use and mechanisms that absorb circulating supply also show positive associations. These are descriptive and predictive relationships; they do not prove that adding one of these functions causes a token’s value to rise.

## Reproducible outputs

- `data/processed/02_valuation/crypto_h8_verified_universe_results.csv`
- `data/processed/02_valuation/crypto_h8_verified_universe_sensitivities.csv`
- `data/processed/02_valuation/crypto_h8_verified_universe_summary.json`
