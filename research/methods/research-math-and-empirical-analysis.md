# The mathematics and empirical analysis behind this project

Current guide | 25 October 2026

This guide follows the implemented code and archived outputs through the H4 execution checkpoint. It explains existing calculations; no new empirical model is estimated here. Historical notes can contain earlier samples and superseded interpretations.

## 1. The distinction that makes the numbers understandable

Our calculations answer three different questions:

| Type | Question | Example |
|---|---|---|
| Measurement | What happened or what economic function exists? | Return, volatility, a verified capture route, group membership |
| Estimation | How are measured quantities related? | Relationship between lagged fees and market capitalization |
| Inference and validation | How uncertain, unusual or stable is the estimate? | Bootstrap p-value, permutation test, held-out prediction error |

A correlation is not a valuation, a regression coefficient is not a forecast, and a p-value is not the probability that the hypothesis is true. A model can improve relative prediction while remaining too inaccurate to support a price target.

Notation: $i$ denotes an asset, $t$ a date, $P$ a price, $M$ a market capitalization, $R$ a simple return and $r$ a log return. We use natural logarithms throughout.

## 2. Turning economic decisions into mathematical inputs

### Binary coding, breadth and overlapping groups

For an asset and function, the verified value is

$$c_{ik}\in\{0,1\}.$$

An unresolved decision remains missing; it is not converted to zero. The current matrix has 23 assets and ten resolved functions, giving $23\times10=230$ sourced cells. Binary codes record whether the written rule is satisfied. They do not measure how much value the mechanism creates.

Raw function breadth is

$$N_i=\sum_{k=1}^{10}c_{ik}.$$

For a pre-specified group of functions $\mathcal B_b$, membership is an OR rule:

$$B_{ib}=\max_{k\in\mathcal B_b}c_{ik}.$$

For example, a transaction/service group can be active through gas or utility. Assets can belong to several groups. Group membership is not an exclusive sector label, an economic weight or a valuation score.

Code: `src/pipeline/crypto_verified_universe.py`. Input/output: `data/processed/01_classification/crypto_verified_universe_profiles.csv`.

### Effective dating

Where the analysis uses the mechanism-event ledger, it takes the latest recorded decision whose effective date is on or before the observation date. A future activation cannot enter an earlier date.

That is different from RV1 and CA1, which use the current verified matrix as a retrospective description. Those models do not reconstruct every historical information set. Effective dating is an important property of particular panels, not a blanket claim about every calculation.

### Jaccard similarity and the architecture comparison

For two assets' positive-function sets $A_i,A_j$:

$$J(i,j)=\frac{|A_i\cap A_j|}{|A_i\cup A_j|}.$$

If two assets share three positive functions and have five distinct positive functions between them, similarity is $3/5=0.60$. Shared zeros do not increase similarity.

The architecture study uses all ten functions and all

$$\binom{23}{2}=\frac{23\times22}{2}=253$$

asset pairs. It compares mean similarity within the same architecture with mean similarity across architectures:

$$\Delta=0.51726-0.33089=0.18637.$$

That is an 18.6-percentage-point difference in similarity. Architecture labels are shuffled across assets 100,000 times, preserving label counts. The implementation reports 23 equally or more extreme draws, giving $23/100{,}000=0.00023$. This is a Monte Carlo permutation estimate. The overlapping 253 pairs are not treated as 253 independently labelled assets.

Economic peers in RV1 and the advisory profiles instead use overlap across the eight groups. The feature set and eligibility rules must therefore be stated when quoting a similarity score.

Code: `src/pipeline/crypto_architecture_similarity.py`, `src/pipeline/crypto_advisory_profiles.py` and `src/pipeline/crypto_relative_valuation.py`.

## 3. Financial measurement: returns, risk and valuation multiples

### Returns and compounding

Simple return and log return are

$$R_t=\frac{P_t}{P_{t-1}}-1,\qquad r_t=\log\left(\frac{P_t}{P_{t-1}}\right).$$

Simple returns compound multiplicatively:

$$1+R_{a:b}=\prod_{t=a}^{b}(1+R_t).$$

Log returns add:

$$r_{a:b}=\sum_{t=a}^{b}r_t,\qquad R_{a:b}=e^{r_{a:b}}-1.$$

A 10% gain followed by a 10% loss gives $1.1\times0.9-1=-1\%$, not zero. This is why cumulative simple returns cannot be added. Small log returns approximate percentages, but large log drawdowns must be converted before being described as percentage losses.

### Volatility

The implemented population standard deviation is

$$s_r=\sqrt{\frac1n\sum_{t=1}^{n}(r_t-\bar r)^2}.$$

Daily crypto log-return volatility is annualized as $s_r\sqrt{365}$. CA1 uses weekly simple-return volatility times $\sqrt{52}$. These are conventions for scaling realized variation; serial dependence or changing volatility can weaken the interpretation as a forecast of next year's risk. A value of 0.57 is 57% annualized volatility, not a prediction of a 57% loss.

### Drawdown

For wealth $W_t$, drawdown is

$$D_t=\frac{W_t}{\max_{s\le t}W_s}-1,\qquad MDD=\min_tD_t.$$

Some older risk outputs store log drawdown:

$$D_t^{\log}=\log W_t-\max_{s\le t}\log W_s.$$

Convert with $e^{D_t^{\log}}-1$. A log drawdown of $-1$ means approximately a 63.2% loss from the previous peak, not a 100% loss. CA1's drawdowns are sampled at weekly endpoints, so they can miss deeper losses between observations. H4's planned 90-day-high drawdown is another defined measurement, not the same as full-window maximum drawdown.

### Beta

In a regression with an intercept,

$$\beta_i=\frac{\operatorname{Cov}(r_i,r_m)}{\operatorname{Var}(r_m)}.$$

It measures sensitivity to a specified market return. A beta near 1.2 describes a fitted sensitivity, not a guarantee that every 1% market move produces a 1.2% asset move. The existing crypto-market factor uses an equal-weight observed-universe return; it is not a broad market-cap-weighted index and includes the asset itself. CA1 correlations with SPY are a separate calculation.

### Logs, geometric capitalization and multiples

RV1's outcome is mean log capitalization:

$$y_i=\frac1{T_i}\sum_t\log M_{it},\qquad M_i^{geo}=e^{y_i}.$$

The exponentiated outcome is a geometric historical mean. It is neither the arithmetic mean nor the current market capitalization.

RV1's fee multiple uses the geometric mean of daily annualized ratios:

$$V_i^{fee}=\exp\left[\frac1{T_i}\sum_t\log\left(\frac{M_{it}}{365F_{i,t-1}}\right)\right].$$

It requires positive observed denominators and the frozen coverage threshold. The holder-revenue multiple uses the corresponding holder-revenue series and requires eligible capture economics. Scope-matched peers and a minimum peer count further constrain comparison.

The earlier dashboard instead uses a latest-capitalization/trailing-average-flow snapshot formula. These two approaches measure different quantities and should not be mixed. A denominator labelled “holder revenue” retains the provider's definition; it is not automatically a legal cash entitlement.

Code: `crypto_return_panel.py`, `crypto_function_risk_exposure.py`, `crypto_cross_asset.py` and `crypto_relative_valuation.py` in `src/pipeline/`.

## 4. Regression: how H1 and H2 examine economic relationships

### Ordinary least squares

For outcome vector $y$ and predictor matrix $X$, OLS chooses coefficients to minimize

$$\sum_j(y_j-X_j\beta)^2.$$

When the design has full column rank,

$$\hat\beta=(X'X)^{-1}X'y.$$

The implementation solves the corresponding linear system and rejects unidentifiable designs. A coefficient is an association conditional on the included regressors. Missing confounders, reverse causality and measurement differences remain.

### H1: asset and date fixed effects

The primary H1 relationship is

$$\log M_{it}=\alpha_i+\delta_t+\beta_A\log(1+A_{i,t-1})+\beta_T\log(1+T_{i,t-1})+u_{it}.$$

$A$ is active addresses and $T$ is transaction count. Asset effects absorb time-invariant differences; date effects absorb a common daily intercept. This does not remove asset-specific time-varying confounders or heterogeneous market sensitivities.

For a balanced panel, the code removes the fixed effects through

$$\widetilde x_{it}=x_{it}-\bar x_{i\cdot}-\bar x_{\cdot t}+\bar x.$$

This one-step double demeaning is valid for the balanced samples used here; it should not be assumed sufficient for an arbitrary unbalanced panel.

The one-year transaction coefficient is about 0.321. Because both the outcome and transformed activity are logarithmic, it is approximately an elasticity at large activity counts: a 1% increase in transaction count is associated with roughly 0.32% higher capitalization within this fitted specification. It does not mean a 32% expected investment return. The coefficient changes sign without XLM, which limits the conclusion.

### H2: interaction between fees and capture

With $F=\log(1+\text{lagged daily fees})$, capture indicator $C$, and application-scope indicator $S$:

$$\log M_{it}=\alpha_i+\delta_t+\beta_1F_{it}+\beta_2C_{it}+\beta_3F_{it}C_{it}+\beta_4F_{it}S_i+u_{it}.$$

Within the same scope, the fee slope is $\beta_1$ without capture and $\beta_1+\beta_3$ with capture. Thus $\beta_3$ measures the difference in slopes; it is not the fee yield or the causal value of activating capture.

The broad-definition interaction is approximately 0.132 with bootstrap p = 0.082. Under the strict capture sensitivity it is approximately 0.061 with p = 0.478. Both versions are reported. Secondary seven-day forward-return models use the same framework, but results cannot be read as robust return prediction.

Code: `crypto_h1_activity_history_analysis.py`, `crypto_h2_estimator_diagnostics.py`, `crypto_h2_exploratory_estimates.py` and `crypto_h2_strict_capture_sensitivity.py`.

## 5. Inference: how we assess uncertainty

### Clustered errors

Several observations from the same asset can have related errors. Thousands of asset-days do not provide thousands of independent assets. The cluster covariance implemented in the panel tests has the sandwich form

$$\widehat V=c\,(X'X)^{-1}\left(\sum_gX_g'\hat u_g\hat u_g'X_g\right)(X'X)^{-1},$$

where the implementation's CR1 factor is $c=\frac{G}{G-1}\frac{N-1}{N-K}$ for the transformed design. It aggregates residual scores within an asset. Few clusters, cross-asset dependence, common shocks and fixed-effect degrees-of-freedom conventions still constrain inference.

The t statistic is $t=\hat\beta/\widehat{SE}(\hat\beta)$. A large ratio means a large coefficient relative to the estimated sampling variation. It does not establish economic significance.

### Null-imposed wild cluster bootstrap

For the coefficient being tested:

1. Fit a restricted model imposing that coefficient equals zero.
2. Retain fitted values and residuals from that restricted model.
3. Multiply each asset's entire residual series by a sign $v_g\in\{-1,+1\}$.
4. Refit and recompute the t statistic.
5. Compare the observed statistic with all enumerated bootstrap statistics.

$$y^*_{it}=\hat y^{restricted}_{it}+v_i\hat u^{restricted}_{it},$$

$$p=\frac{\#\{|t^*|\ge |t^{observed}|\}}{2^G}.$$

H1 has nine asset clusters and $2^9=512$ sign assignments. H2 has eleven and $2^{11}=2,048$. The broad H2 p-value is $168/2,048=0.08203125$.

“Exact enumeration” means every sign vector is computed. It does not make the statistical test distribution-free, assumption-free or automatically reliable with few clusters. Rademacher weights have mean zero and unit variance; their third moment is zero, so they do not generally preserve a residual distribution's nonzero skewness.

### Permutation tests

For the architecture, H8 and function-risk comparisons, labels, predictors or outcomes are shuffled as defined by each experiment, and the statistic is recomputed. The null question is whether the observed arrangement is unusual under that specific rearrangement scheme.

Small pilot samples can enumerate $6!=720$ permutations. Larger studies use seeded Monte Carlo draws. The H8 verified extension uses 100,000 draws for its declared group tests. Some implementations use $b/B$; others use the Monte Carlo correction $(b+1)/(B+1)$. The named output records the method and count.

Permutation validity depends on appropriate exchangeability under the null. Shuffling an observational predictor while holding a correlated control fixed is not automatically a valid conditional-independence test. The risk and valuation permutations are exploratory reference distributions, not randomized-treatment evidence.

### What a p-value means

A p-value assesses the extremeness of a statistic under a specified null/reference procedure. It is not the probability that the hypothesis is false, and p = 0.478 does not mean a 47.8% chance that capture matters. A large p-value can reflect no effect, low power, noise or weak identification.

### Benjamini–Hochberg correction

When $m$ hypotheses are examined, isolated small p-values can occur by chance. The verified function-risk study tests nine predictors against three outcomes, giving $9\times3=27$ tests. At a nominal 5% rate, 1.35 false rejections would be expected if all nulls were true and the tests were correctly sized.

For sorted p-values, BH adjusted values are

$$q_{(j)}=\min\left(1,\min_{\ell\ge j}\frac{m}{\ell}p_{(\ell)}\right).$$

The strongest verified risk association has p approximately 0.01275 but q approximately 0.34425. None passes the specified 10% false-discovery threshold. Formal FDR control has dependence assumptions; the correction cannot repair an invalid underlying test. “No discovery” does not prove all effects are exactly zero.

H8 corrects its declared eight single-group tests; H4's implemented plan corrects its three outcome tests when estimation becomes possible.

Code: `crypto_h2_small_cluster_inference.py`, `crypto_h8_verified_universe.py` and `crypto_function_risk_exposure.py`.

## 6. Valuation models: H8, ridge regression and held-out error

### H8 cross-sectional model comparison

H8 compares simple regressions across assets:

$$\overline{\log M_i}=a+bX_i+e_i.$$

$X_i$ can be raw breadth or a specified group indicator. The verified experiment also lists nested models and sensitivities. Its best single group, financial integration, has held-out RMSE 1.75935 versus 1.81091 for breadth: about 2.8% lower error. Selecting the best group within discovery data does not establish independently validated superiority.

### RV1 ridge regression

The joint-group and fundamentals models minimize

$$\sum_{i\in train}(y_i-a-z_i'\beta)^2+\lambda\sum_j\beta_j^2,\qquad\lambda=10.$$

The intercept is unpenalized. Each predictor is standardized with training-asset means and population standard deviations; a zero-variance training column becomes zero. The penalty shrinks slopes and allows correlated indicators to be included with fewer unstable coefficients. It does not establish which function causes value.

With standardized predictors, the solution uses

$$\hat\theta=(X'X+\lambda D)^{-1}X'y,$$

where $D$ has zero for the intercept and one for each slope. The code solves this linear system. The penalty is fixed rather than selected from the new results.

### Leave-one-asset-out prediction

For each asset, fit the model using the others and predict the held-out asset:

$$RMSE=\sqrt{\frac1n\sum_i(y_i-\hat y_i^{(-i)})^2},\qquad MAE=\frac1n\sum_i|y_i-\hat y_i^{(-i)}|.$$

The reported error improvement is

$$100\left(1-\frac{RMSE_{new}}{RMSE_{benchmark}}\right).$$

Using the full stored precision:

- Eight-group RV1 model versus breadth: $1-1.46898/1.81625\approx19.1\%$ lower error.
- Fundamentals versus its same-sample mean: $1-1.34673/2.43208\approx44.6\%$ lower error.
- Adding capture to fundamentals: $1.45227/1.34673-1\approx7.8\%$ higher error.

These are changes in prediction error, not investment returns or percentages of “correctly valued” assets. Log-cap RMSE is not measured in dollars. An RMSE of 1.469 corresponds to a multiplicative log-error scale of about $e^{1.469}=4.34$; it is not a guaranteed price band.

The models must be compared on identical assets. The identity sample has 22 assets, and the fundamentals sample has 11. An 11-asset model's lower error cannot establish superiority over a 22-asset model without a matched-sample comparison. Asset holdout is also not future-time validation: the historical outcomes were previously examined and assets share common conditions.

### Residuals and diagnostic bands

$$e_i=y_i-\hat y_i^{(-i)},\qquad\frac{M_i^{observed,geo}}{\hat M_i^{geo}}=e^{e_i}.$$

BTC's identity-model log residual of about 5.126 yields $e^{5.126}\approx168.3$. That is how the 168-times figure is calculated. It identifies a very large model error, not proven overpricing.

For each outer held-out asset, the code makes additional inner held-out predictions using only the outer training set. It takes the 90th-percentile absolute inner log error $q$ and displays

$$[\exp(\hat y_i-q),\ \exp(\hat y_i+q)].$$

These are empirical diagnostic bands. The implementation does not establish 90% or 95% predictive coverage, and it is not a calibrated conformal interval. Contributions to predicted log capitalization are the intercept plus each standardized predictor times its fitted coefficient.

Code: `crypto_h8_verified_universe.py` and `crypto_relative_valuation.py`.

## 7. Event studies: supply events and mechanism changes

### H3 market-adjusted event returns

First estimate an asset's normal market relationship before the event:

$$r_{it}=a_i+b_ir_{mt}+u_{it}.$$

The H3 estimation window is trading observations −120 to −31. Abnormal return is

$$AR_{it}=r_{it}-(\hat a_i+\hat b_ir_{mt}).$$

The primary cumulative abnormal log return is

$$CAR_e[-1,+1]=\sum_{t=-1}^{1}AR_{it}.$$

Burn CARs keep their sign; unlock CARs are multiplied by −1 so a positive direction-adjusted statistic supports the hypothesis. Eligibility uses official event dates and the fixed supply materiality threshold, not observed returns.

The 17 events contain 12 ARB unlocks, four BNB burns and one UNI burn. Eight match the predicted direction. The event-weighted mean direction-adjusted abnormal log return is about −0.0113.

For inference, repeated events are first averaged within each of the three assets. The test then flips the signs of these three asset means, giving $2^3=8$ assignments and p = $2/8=0.25$. The inference statistic gives equal weight to assets, whereas the pooled event mean gives equal weight to events; these are different summaries. Sign-flip validity requires an appropriate symmetric reference distribution, and three assets provide very low power.

### Before/after difference-in-differences and placebos

The separate mechanism-event analysis compares the treated asset's before/after change with controls:

$$DiD=(\bar y_{treated,post}-\bar y_{treated,pre})-(\bar y_{controls,post}-\bar y_{controls,pre}).$$

It uses asset placebos and alternative dates to contextualize the observed statistic. In the long-panel return output, $y$ is daily log return, so the statistic is a change in average daily return, not a cumulative monthly return. Placebo reference sets are not a substitute for credible parallel-trend and no-confounding assumptions. These event estimates are not causal proof that a token mechanism moved prices.

Code: `crypto_h3_supply_event_analysis.py` and `crypto_mechanism_event_study.py`. Exact current secondary output: `data/processed/02_valuation/crypto_mechanism_event_study_long.json`.

## 8. Cross-asset correlations: crypto, gold, S&P 500 and Russell 2000

### Constructing the crypto basket

CA1 fixes a 21-asset set using its coverage rule. HYPE and TON are excluded for source-history coverage, not for their correlations. Daily equal-weight simple return is

$$R_t^{basket}=\frac1{21}\sum_{i=1}^{21}R_{it}.$$

The basket is hypothetically rebalanced every day before costs. For matched ETF session endpoints, all intervening crypto daily simple returns are compounded, including weekends. Missing constituents do not get silently reweighted away. GLD, SPY and IWM use vendor-adjusted ETF prices; they are proxies for gold and the two indices.

### Pearson and Spearman correlation

$$\rho_{xy}=\frac{\sum_t(x_t-\bar x)(y_t-\bar y)}{\sqrt{\sum_t(x_t-\bar x)^2\sum_t(y_t-\bar y)^2}}.$$

Spearman correlation applies the Pearson formula to ranked returns, using average ranks for ties. We compare returns, not price levels.

The 52 weekly basket correlations are 0.110 with GLD, 0.361 with SPY and 0.282 with IWM. A correlation of 0.36 is not “36% of weeks moving together” or “36% of risk explained.” Squaring it gives about 13% explained sample variation in a simple one-benchmark regression with an intercept, but not a causal risk decomposition.

### Moving-block bootstrap uncertainty

To retain some time dependence, the code samples blocks of four consecutive paired weekly returns, wraps at the sample boundary, and joins blocks until 52 observations are obtained. It repeats this 2,000 times with a fixed seed and uses the 2.5th and 97.5th percentiles of the resampled correlations.

| Benchmark | Correlation | Marginal approximate 95% interval |
|---|---:|---|
| GLD | 0.110 | −0.189 to 0.411 |
| SPY | 0.361 | 0.077 to 0.653 |
| IWM | 0.282 | −0.018 to 0.580 |

The intervals reflect uncertainty under the resampling scheme and its stationarity approximation. They are not simultaneous intervals, proof of stable long-run relationships or a formal test that the equity correlations exceed the gold correlation.

### Rolling and stress analysis

The study also calculates 60-session rolling correlations, daily correlations, rank correlations, chronological halves and plus/minus-one-day crypto-close shifts. These reveal sensitivity to the time window and asynchronous market clocks.

For SPY-negative weeks, it computes conditional averages and loss frequencies:

$$\overline R^{crypto}_{SPY<0}=\frac{\sum_tR_t^{crypto}\,1\{R_t^{SPY}<0\}}{\sum_t1\{R_t^{SPY}<0\}}.$$

There are 21 such weeks. Crypto loses in 14 of them: $14/21=66.7\%$. Its conditional mean return is approximately −3.3%. This is descriptive stress behavior; neither that frequency nor low unconditional correlation establishes a reliable hedge. The 11 worst-quintile SPY weeks are too few for the declared regime-correlation threshold.

Code: `crypto_cross_asset.py` and `cross_asset_market_data.py`.

## 9. Other calculations and their empirical status

### Fama–MacBeth and Newey–West baseline

For each eligible day, the baseline regresses cross-sectional asset log returns on lagged characteristics:

$$r_{it}=\lambda_{0t}+\sum_k\lambda_{kt}x_{i,k,t-1}+e_{it}.$$

It then averages the daily slopes. A Newey–West variance with seven lags allows serial dependence in that slope time series:

$$\widehat{Var}(\bar\lambda)=\frac1T\left[\hat\gamma_0+2\sum_{\ell=1}^{7}\left(1-\frac{\ell}{8}\right)\hat\gamma_\ell\right].$$

The stored output contains 2,596 daily cross-sections. Its average beta coefficient is about −0.0030 with t approximately −2.12. This is an exploratory baseline estimate, not a validated implementable premium or a 0.3% daily strategy return. Momentum and volatility estimates are weaker in this baseline. The stored rolling beta already ends before its row date, and the cross-sectional implementation also shifts predictor rows by one observed date; exact timing should be checked before treating these variables as standard factor replications.

Code: `crypto_return_factor_baseline.py` and `crypto_return_panel.py`.

### Review agreement

For two genuinely independent coders, raw agreement is $p_o$ and marginal chance agreement is $p_e$:

$$\kappa=\frac{p_o-p_e}{1-p_e}.$$

Adjudicated agreement must not be represented as fresh independent agreement. The ten-cell review does not establish reproducibility of the 230-cell matrix. Kappa is a review statistic, not evidence that a valuation model works.

### H4: implemented, not empirically estimated

The code is ready for

$$Y_{it}=\alpha_i+\delta_t+\beta\frac{Stake_{i,t-1}}{CirculatingSupply_{i,t-1}}+\gamma\log M_{it}+u_{it}.$$

The outcomes are turnover, 30-day annualized volatility and drawdown from a 90-day high. Circulating units are inferred from capitalization/price. The BTC-return control is common across assets and absorbed by date effects.

ETH and BNB are the stake-positive assets; BTC, UNI and ARB are structural controls. Exact ETH history remains 0/362, BNB is 362/362 and other inputs support 361 days. No empirical coefficient or H4 p-value exists. Synthetic tests validate implementation only.

If the input gate passes, the code enumerates $2^5=32$ asset sign assignments. The two-sided p-value resolution is 0.0625 in nondegenerate cases. Only two assets carry positive stake, so information and power remain limited. Shared capitalization denominators and endogenous staking further limit causal interpretation.

Code: `crypto_h4_estimation.py`; current status: `data/processed/02_valuation/crypto_h4_estimation.json`.

## 10. Empirical-analysis inventory

| Study | Actual observation unit | Data used | Empirical work completed |
|---|---|---|---|
| Architecture | Asset labels and overlapping asset pairs | Verified ten-function matrix and architecture | Similarity comparison, label permutations |
| H1 | Asset-day, nine asset clusters | Active addresses, transactions, capitalization | Fixed effects, cluster bootstrap, asset exclusions, window comparison |
| H2 | Asset-day, eleven asset clusters | Fees, effective capture, scope, capitalization, returns | Interaction regressions, strict-rule check, cluster bootstrap, non-overlapping return offsets |
| H3 | Repeated events aggregated to three asset units for inference | Official supply events, circulating supply and market returns | Abnormal-return event study, asset sign flips |
| H8 | Cross-section of assets | Verified group/count features, mean log capitalization | OLS, LOAO error, permutations, declared sensitivities and group-test correction |
| Function-risk refresh | Nineteen eligible assets | Group membership, beta, volatility, drawdown and volume | Twenty-seven regressions/reference tests, asset exclusions, BH correction |
| RV1 | Twenty-two identity or eleven fundamentals assets | Groups, fees, volume, scope, capitalization | Six ridge/benchmark comparisons, 99 held-out estimates, diagnostic bands and peer multiples |
| CA1 | Fifty-two weekly matched returns | Twenty-one-asset basket and GLD/SPY/IWM adjusted prices | Correlations, block bootstrap, rolling/time-shift/split-sample/stress checks |
| Mechanism events | Asset-event comparisons | Dated activations/suspensions, returns and controls | Before/after/control differences and placebo comparisons |
| Return baseline | Daily asset cross-sections | Returns, rolling beta, momentum, volatility | Market regressions, Fama–MacBeth, Newey–West and descriptive sorts |
| H4 | Planned five-asset daily panel | Exact ETH/BNB stake, market denominators and USD prices | Implementation and synthetic tests only; real-data estimation blocked |

These methods measure associations, compare prediction errors and expose uncertainty. They do not yet establish intrinsic value, causal mechanisms, stable portfolio hedges or a validated trading strategy.
