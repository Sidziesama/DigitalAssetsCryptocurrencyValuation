# The math behind the evidence, explained

7 September 2026. Every technique used in this project, why it was chosen over the obvious alternative, and what it is doing. Written for someone who knows what a regression is but has not spent time with cluster-robust inference or randomization tests.

---

## The one idea that runs through everything

We have very few assets. Six fully classified, eleven in the fee panel, twenty in the risk test, twenty-four with prices. Almost every standard statistical tool in finance assumes you have many independent units and can lean on large-sample approximations. We cannot.

So the entire statistical design is built around one question: **what can you defend when the sample is small?** The answer is nearly always the same. Stop approximating and start counting. Instead of asking "what would the t-distribution say", ask "of all the ways this data could have been arranged, in how many would I have seen something this extreme?" That is a question you can answer exactly by enumeration, and the answer does not depend on any assumption about normality.

That is why you see factorials and powers of two throughout: 720 permutations, 2,048 sign flips, 512 sign flips. Those are not simulation counts. They are the complete set of possibilities.

---

## 1. Effective dating: the algebra of "what was true then"

Every classification is a value $c_{i,k}(t)$ for asset $i$, function $k$, date $t$. It comes from a ledger of dated events, and the rule is:

$$c_{i,k}(t) = \text{the value of the most recent event on or before } t$$

That is the whole mechanism, and it is deliberately boring. What matters is what it forbids. If Uniswap turned on a fee burn in December 2025, then for every date before that, the burn code reads zero. You cannot accidentally use it to explain 2024 prices, because the resolution function cannot see events dated after $t$.

Two derived quantities:

$$\text{bundle } B_{i,b}(t) = \max_{k \in \mathcal{B}_b} c_{i,k}(t) \qquad \text{breadth } N_i(t) = \sum_{k=1}^{10} c_{i,k}(t)$$

A bundle is on if any function in it is on. Breadth is just a count of jobs.

---

## 2. Cohen's kappa: is the classification reproducible?

Two people score the same cells independently. Raw agreement is misleading, because if a code is 90% zeros, two people guessing "zero" always agree 81% of the time by luck. Kappa strips that out:

$$\kappa = \frac{p_o - p_e}{1 - p_e}$$

$p_o$ is how often they actually agreed, $p_e$ is how often they would have agreed by chance given each reviewer's own tendency to say yes or no. The numerator is agreement above chance; the denominator is the maximum possible agreement above chance. So $\kappa = 1$ means perfect, $\kappa = 0$ means no better than luck.

We got $\kappa = 1.00$ on the ten reviewed decisions after one adjudication. On the conventional Landis–Koch scale that is "almost perfect", though with ten decisions it is a modest claim. The point is not the number, it is that the number exists at all. Almost no crypto classification work reports one.

---

## 3. Two-way fixed effects: removing the things you cannot measure

The H2 regression is:

$$y_{it} = \alpha_i + \gamma_t + \beta_1 F_{i,t-1} + \beta_2 C_{it} + \beta_3 (F_{i,t-1} \times C_{it}) + \beta_4 (F_{i,t-1} \times A_i) + \varepsilon_{it}$$

The two things to understand are $\alpha_i$ and $\gamma_t$.

$\alpha_i$ is an intercept for each asset. It absorbs everything permanently different about that asset: Bitcoin is big, Arbitrum is small, Ethereum has a huge developer base. We do not have to measure any of it. $\gamma_t$ is an intercept for each date, absorbing everything that hit the whole market that day. If crypto fell 8% on a Tuesday, that Tuesday's intercept eats it.

What remains is *within-asset, market-adjusted* variation. Mechanically this is a **within transformation**:

$$\tilde{x}_{it} = x_{it} - \bar{x}_{i\cdot} - \bar{x}_{\cdot t} + \bar{x}$$

Subtract the asset's own mean, subtract the day's mean, add back the grand mean once because you subtracted it twice. Run ordinary least squares on the transformed variables and you get the same slopes as if you had included hundreds of dummy variables, at a fraction of the cost.

**Why the interaction is the whole point.** $\beta_1$ says "more fees, higher value". $\beta_3$ says "and that relationship is *steeper* when a capture mechanism is live". The hypothesis is not that fees matter. It is that fees matter *more* when there is a pipe connecting them to the token. $\beta_3$ is that pipe.

**A subtlety worth knowing.** $\beta_4$ interacts fees with whether the asset's fees are measured at chain level or application level. There is no standalone $A_i$ term, because scope never changes for an asset, so $\alpha_i$ has already absorbed it. Including it would produce a singular matrix. $C_{it}$ *does* appear on its own, because Aave and Uniswap changed capture state inside the window, so it varies within asset.

---

## 4. Cluster-robust standard errors, and why they are not enough

Observations within an asset are correlated. Bitcoin's Tuesday error tells you something about Bitcoin's Wednesday error. Treating 3,971 asset-days as 3,971 independent observations would make standard errors far too small.

The cluster-robust (CR1) variance groups errors by asset:

$$\widehat{V} = \frac{G}{G-1}\cdot\frac{N-1}{N-K}\,(X'X)^{-1}\Big(\sum_{g=1}^{G} X_g'\hat{u}_g\hat{u}_g'X_g\Big)(X'X)^{-1}$$

The sandwich structure is standard. The middle sums *within each cluster first*, letting errors correlate freely inside an asset while assuming independence across assets. The leading fraction is a small-sample correction.

**Here is the problem.** This formula is justified by an argument that works as the *number of clusters* goes to infinity. We have eleven. At that size the cluster-robust t-statistic does not follow a t-distribution, and the resulting p-values are known to be too small, sometimes badly. Reporting $p = 0.03$ from this formula with eleven clusters would be misleading, and reviewers in econometrics know it.

---

## 5. The wild cluster bootstrap: counting instead of approximating

So we stop trusting the distribution and build our own, by enumeration.

The logic: **assume the null is true, then see how unusual our result looks among all the results the null could have produced.**

1. Impose $\beta_3 = 0$. Re-estimate without the interaction. Keep the fitted values $\hat{y}^r$ and residuals $\hat{u}^r$. This is a world where the hypothesis is false by construction.
2. Pick a sign for each *asset*: $v_g \in \{-1, +1\}$. Flip that asset's entire residual series:
   $$y^*_{it} = \hat{y}^r_{it} + v_{g(i)} \hat{u}^r_{it}$$
   Flipping by cluster, not by observation, is what preserves the within-asset correlation structure. This is the "cluster" in wild cluster bootstrap.
3. Re-estimate on the fake data, compute the t-statistic.
4. Do this for **every possible sign vector**. With 11 assets that is $2^{11} = 2{,}048$. With 9 chains, $2^9 = 512$.
5. The p-value is simply the fraction at least as extreme as what we actually saw:
   $$p = \frac{1}{2^G}\sum_b \mathbf{1}\{|t^*_b| \ge |t_{\text{obs}}|\}$$

Because we enumerate *all* of them, this is exact, not simulated. Run it twice and you get the identical number.

**The cost.** With 2,048 possibilities, the smallest p-value you can ever observe is $2/2048 \approx 0.001$, and the grid is coarse. Our $p = 0.082$ means 168 of 2,048 sign assignments produced something as extreme. That is a real, countable statement.

**Why Rademacher signs.** Flipping between $-1$ and $+1$ preserves the mean, the variance, and the third moment of the residuals. It is the standard choice; the literature (Cameron–Gelbach–Miller, MacKinnon–Webb) shows it performs best in small-cluster settings.

---

## 6. Overlapping returns, and the fix

A seven-day forward return starting Monday shares six days with the one starting Tuesday. Consecutive observations are mechanically correlated, which inflates apparent significance.

Rather than modelling the overlap, we sidestep it. Take every seventh day. Monday-only gives a set of returns that never overlap each other. But which Monday? Choosing one is a researcher degree of freedom. So we run **all seven** offsets and report them all. If the result only shows up on Thursdays, you have found a Thursday, not an effect. In our case no offset rejects at 10%, on any starting day.

---

## 7. Permutation tests: exact inference on six assets

For cross-sectional questions ("do assets with more functions have higher value?") we have six to twenty data points. No asymptotic theory applies. Fisher's randomization logic does.

If the classification carries no information, then which asset got which label is arbitrary. So shuffle the labels across assets, recompute the statistic, and repeat for **every possible shuffle**:

$$p = \frac{1}{n!}\sum_{\pi \in S_n}\mathbf{1}\{|\theta(x_\pi, y)| \ge |\theta(x, y)|\}$$

With six assets, $6! = 720$. Every one is computed. With twenty assets, $20!$ is about $2.4 \times 10^{18}$, so we draw 20,000 random shuffles with a fixed seed, which is reproducible and precise to about $\pm 0.003$.

**What this buys you.** No normality assumption, no variance estimate, no degrees-of-freedom argument. Just counting. **What it costs you.** With six assets and a yes/no predictor splitting 3-3, the smallest attainable p-value is 0.10. The test *cannot* reject at 5% no matter how strong the effect. That is not a flaw in the test, it is an honest statement about how much six observations can tell you, and it is why the verified-core results are reported as descriptive.

---

## 8. Leave-one-out: stability, not significance

For each asset, drop it, refit, record the coefficient. Two uses:

**Sign stability.** If the slope keeps the same sign in every leave-one-out subsample, one asset is not driving the result. This is reported everywhere and is a different question from significance. In the verified 19-asset risk refresh, the strongest monetary/store associations are 19-for-19 sign stable and still fail the multiple-testing threshold. Both facts matter.

**Honest prediction error.** For model comparison we use leave-one-out RMSE:

$$\text{RMSE}_{\text{LOO}} = \sqrt{\tfrac{1}{n}\sum_i (\hat{y}_i^{(-i)} - y_i)^2}$$

where $\hat{y}_i^{(-i)}$ is the prediction for asset $i$ from a model that never saw asset $i$. In-sample fit always improves when you add variables. Out-of-sample prediction does not. This is how we caught that adding holder capture to the breadth model makes it *worse* (RMSE 3.49 → 4.35), which in-sample $R^2$ would have concealed.

---

## 9. Benjamini–Hochberg: the correction that killed our result

We ran 27 tests in P1_H6 (9 predictors × 3 outcomes). If nothing is real, each has a 5% chance of looking significant, so you expect $27 \times 0.05 = 1.35$ false positives. The original provisional run produced three. The completed-classification refresh produces only one, fewer than the number expected by chance.

Bonferroni would demand $p < 0.05/27 = 0.0019$, which is far too conservative. Benjamini–Hochberg instead controls the **false discovery rate**: among the tests you call significant, what fraction are wrong?

Sort the p-values, then:

$$q_{(j)} = \min_{\ell \ge j}\ \min\Big\{1,\ \frac{m\,p_{(\ell)}}{\ell}\Big\}$$

Read it this way: for the $j$-th smallest p-value out of $m$, scale it up by $m/j$. The smallest p-value gets multiplied by 27; the tenth by 2.7; the last by 1. The outer running minimum enforces monotonicity so a later q-value never falls below an earlier one.

In the verified refresh, the best result is monetary/store membership against maximum drawdown: $p = 0.0128$ but $q = 0.3443$. It is economically interpretable and sign-stable, but it is not a false-discovery-controlled finding.

**This is the correction that turned P1_H6 from a positive result into a null**, and it was written into the specification before the test ran, precisely so we could not decide afterwards to skip it.

---

## 10. Fama–MacBeth with Newey–West: the factor baseline

To ask "is beta priced?" across 24 assets over seven years, Fama and MacBeth's procedure is:

**Step one.** For each day separately, run a cross-sectional regression of that day's returns on yesterday's characteristics:
$$r_{it} = \lambda_{0t} + \sum_k \lambda_{kt}\,x_{i,k,t-1} + e_{it}$$
This gives 2,596 daily estimates of each $\lambda_k$ — the return earned that day per unit of the characteristic.

**Step two.** Average them: $\bar{\lambda}_k = \frac{1}{T}\sum_t \lambda_{kt}$. The clever part is that the *time series* of $\lambda$ estimates gives you the standard error directly, sidestepping cross-sectional correlation entirely.

**The correction.** Those daily estimates are autocorrelated, so the naive standard error is too small. Newey–West fixes it:

$$\widehat{\text{Var}}(\bar{\lambda}) = \frac{1}{T}\Big[\hat{\gamma}_0 + 2\sum_{\ell=1}^{L}\Big(1 - \frac{\ell}{L+1}\Big)\hat{\gamma}_\ell\Big]$$

$\hat{\gamma}_0$ is the variance, $\hat{\gamma}_\ell$ the autocovariance at lag $\ell$. The weights $(1 - \ell/(L+1))$ decline linearly (the Bartlett kernel) and guarantee a positive variance estimate. We use $L = 7$.

**Result:** lagged beta earns $-0.0030$ per day with $t = -2.12$. Higher-beta crypto earns *less*, the same betting-against-beta anomaly Frazzini and Pedersen documented in equities. Momentum and volatility are flat.

---

## 11. Difference-in-differences with two placebo distributions

For a mechanism activation on date $\tau$:

$$\Delta_j = \underbrace{\frac{1}{W}\sum_{t=\tau+1}^{\tau+W} y_{jt}}_{\text{after}} - \underbrace{\frac{1}{W}\sum_{t=\tau-W}^{\tau-1} y_{jt}}_{\text{before}}, \qquad \text{DiD} = \Delta_{\text{treated}} - \frac{1}{|\mathcal{C}|}\sum_{j\in\mathcal{C}}\Delta_j$$

The first difference removes anything permanent about the asset. The second removes anything that happened to the whole market in that window. Controls are only assets with no ledger event of their own in the window, so a contaminated control cannot pollute the comparison.

With three events there is no asymptotic distribution to appeal to, so we build two reference distributions:

- **Asset placebo.** Pretend each control was treated on the real date. If the true event is indistinguishable from 22 assets that had nothing happen, it is noise.
- **Calendar placebo.** Pretend the real asset was treated on other dates, shifted by multiples of seven days to non-overlapping windows. About 280 of these per event.

$$p = \frac{\#\{|\text{DiD}_{\text{placebo}}| \ge |\text{DiD}_{\text{obs}}|\} + 1}{\#\text{placebos} + 1}$$

The $+1$ on both sides includes the observed statistic in its own reference set, which is the standard convention and prevents $p = 0$.

**Why we also test fees.** If a valuation move coincides with a usage move, the mechanism is not the story. Running the identical statistic on lagged fees is the check. For the Aave pause, fees moved the *opposite* way from value, which is informative.

---

## 12. Where the math actually bit

Three places where the technique changed the answer, and all three made the answer weaker.

| Technique | What it caught |
|---|---|
| Effective dating | A classification correction applied to the wrong date silently did nothing, because the panel resolved the older event. Caught by inspecting the resolved panel, not the config. |
| Strict capture definition | Fee-capture interaction $0.132 \to 0.061$, $p$ $0.082 \to 0.478$. The result depends on a definition, not on the data. |
| Benjamini–Hochberg | Three tests at $p \le 0.05$ became zero discoveries at a 10% false-discovery rate. |

A fourth, from the event study: the Aave pause measured $-13\%$ with $p = 0.18$ on a one-year market-cap panel and $+0.1\%$ with $p = 0.74$ on the seven-year return panel with 22 controls. Same event, better test, opposite conclusion.

If the machinery only ever confirmed what we hoped, it would not be evidence of anything. The value of building it this way is that it is capable of saying no.
