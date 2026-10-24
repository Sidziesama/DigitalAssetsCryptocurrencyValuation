# Digital assets for advisory and valuation: what we have learned and what comes next

Research review | 23 October 2026

This report summarizes the existing repository results. No new model is estimated here. The main valuation and benchmark evidence covers August 2025–August 2026; some risk analyses use longer histories. These are historical findings, not an assessment of market conditions on 23 October 2026.

## Executive assessment

We have built a usable research framework for explaining what a cryptocurrency does, how its economic activity could support value, and which assets are reasonable comparables. We have also tested several common investment narratives and documented where the evidence fails to support them.

Our strongest finding is methodological: **technical labels and network activity are insufficient descriptions of a token’s economics. The route from activity to the token or its holders must be specified and evidenced.** Our empirical results suggest that economic groups can improve comparisons, while also showing that classification alone cannot explain asset values precisely.

There is material for a focused working paper, an advisory whitepaper, or a practitioner article. A journal submission would need clearer differentiation from existing research, stronger external validation, and a tighter central question. We do not yet have a validated fair-value model or a reliable trading strategy.

## 1. What we have built

The project contains five connected pieces:

1. **An economic classification instrument.** We classify 23 active cryptoassets across ten functions: monetary use, gas, staking, burn, scarcity, collateral, governance, protocol capture, utility and incentives. All 230 decisions have supporting evidence. Architecture is recorded separately as technical context.
2. **An evidence and assumptions trail.** Decisions follow written rules, dated sources, materiality conventions and recorded adjudications. Missing evidence and a verified negative are different states. A completed matrix means the evidence requirements were addressed; it does not prove that every decision is objectively correct.
3. **Hypothesis tests.** H1, H2, H3 and H8 have exploratory results. H4 has a design and measurement work but remains blocked by missing Ethereum archival staking data.
4. **Relative valuation models.** Six models compare economic groups, function counts and measured fundamentals. There are 99 held-out asset estimates across the six models, with contributions, residuals and diagnostic error ranges.
5. **An advisory and market-risk layer.** The report combines the classifications and models with technical context and comparisons against gold, the S&P 500 and Russell 2000. The code, archived source data, estimates and charts are traceable in the repository.

The last completed code checkpoint passed 388 tests. These tests help establish that the software behaves as specified; they do not establish economic validity or publication readiness.

## 2. What we have discovered

### A. Architecture helps, but does not describe the whole economic asset

We compared all 253 pairs among the 23 assets. Same-architecture pairs share an average of 51.7% of their economic functions, versus 33.1% across different architectures. The architecture-label permutation test gives p = 0.00023. This is a test across asset labels; the 253 overlapping pairs are not 253 independent observations.

Architecture contains information, but it does not replace economic classification. Two assets can use different technical designs and still perform similar economic jobs.

**Advisory implication:** use architecture to understand operational design and use economic functions to select valuation metrics and peers. Shared functions remain a starting point: size, maturity, liquidity and business scope also matter.

### B. Usage and holder capture are separate questions

A network may attract transactions and collect fees without giving the token holder a direct economic claim. Governance over ecosystem spending is also different from a distribution, buyback or token burn that mechanically reaches the token or its holders.

This distinction materially affects H2. The broad fee-by-capture relationship has p = 0.082, while the stricter holder-directed definition gives p = 0.478. The evidence weakens when the capture rule is narrowed.

**What this means:** the conclusion is sensitive to the economic definition. We cannot claim that higher fees consistently create higher token-holder value. The defensible result is that the capture boundary changes the empirical conclusion.

**Advisory implication:** trace where the fee goes before using a protocol’s revenue to value its token. A provider’s “holder revenue” series is not automatically an enforceable or distributable cash-flow claim.

### C. More network activity sometimes accompanies higher value, but the result is fragile

The H1 one-year retrospective extension finds a positive transaction-count coefficient of approximately 0.321, with p = 0.078. However, the coefficient becomes negative when XLM is removed. The shorter frozen window also differs from the one-year result.

**What this means:** the association depends on the sample and window. Transaction counts are not standardized measures of real economic usage across networks, and addresses are not necessarily distinct users.

**Advisory implication:** use activity as one input. Establish whether it represents recurring economic demand, technical throughput or subsidized activity before interpreting it as valuation support.

### D. Supply events have not supported a simple trading rule

The event study contains 17 material events across ARB, BNB and UNI. Eight move in the hypothesized direction. All three asset-level average direction-adjusted returns oppose the prediction; the exact asset-level test gives p = 0.25.

There are only three independent asset units, and scheduled events may be anticipated. A separate evidence-only search did not identify an eligible fourth asset under the frozen rules.

**What this means:** we have not found support for “unlocks mean sell” or “burns mean buy” as standalone rules. Low power also prevents a general conclusion that supply mechanisms never matter.

### E. Economic groups improve relative comparison, but valuation precision is weak

Two distinct experiments must be kept separate:

| Experiment | Comparison | Finding |
|---|---|---|
| H8 | Best single economic group versus raw function count | Financial integration lowers held-out error by about 2.8%; selection occurred in the discovery sample |
| RV1 | Eight groups jointly versus raw function count, using fixed-penalty ridge regression | Held-out error falls by 19.1% on the same 22 assets |
| RV1 | Fees, trading volume and chain/application scope versus the same-sample mean | Held-out error falls by 44.6% on 11 assets |
| RV1 | Adding static holder capture to those fundamentals | Held-out error increases by 7.8% |

“Held out” means each asset is excluded from its own model fit and predictor scaling. It does not mean the model was tested on genuinely future market data. The outcomes had already been examined in earlier research.

The largest warning is BTC. Its observed historical capitalization is about 168 times the identity-group model’s estimate. Even the fundamentals model underpredicts it by roughly eleven times. That is evidence of substantial missing information or an unsuitable model for the asset, not proof of overvaluation.

Fees and trading volume help explain relative size, but volume and capitalization can move together because both reflect market attention and scale. The model does not establish that trading activity causes value. It estimates historical relative capitalization, not a current token price.

**Advisory implication:** use residuals as questions to investigate. The diagnostic error bands are wide and have no calibrated coverage guarantee, so they should not be presented as investment-grade price ranges.

### F. Crypto has shared market risk despite different economic roles

The cross-asset study uses a fixed, daily-rebalanced equal-weight basket of 21 eligible cryptoassets and 52 weekly returns. Gold, the S&P 500 and Russell 2000 are represented by GLD, SPY and IWM adjusted ETF prices. HYPE lacks crypto price history in this source; TON fails the predeclared coverage threshold.

| Benchmark | Weekly correlation with the crypto basket | Approximate 95% bootstrap interval |
|---|---:|---|
| Gold — GLD proxy | 0.11 | −0.19 to 0.41 |
| S&P 500 — SPY proxy | 0.36 | 0.08 to 0.65 |
| Russell 2000 — IWM proxy | 0.28 | −0.02 to 0.58 |

The main equity point estimates exceed the gold estimate, but relationships change across time windows and closing-time choices. Gold correlation changes sign between sample halves. The intervals are marginal estimates, not simultaneous tests proving which asset class has the strongest relationship.

During SPY-negative weeks, the crypto basket loses in two-thirds of observations and averages a weekly loss of about 3.3%. Low average correlation therefore does not establish reliable downside protection.

The eight economic-group baskets have SPY correlations around 0.33–0.38. In this sample, different economic functions coexist with broadly shared equity co-movement. The earlier function–risk tests also produced no result surviving the declared false-discovery correction.

**Advisory implication:** classification can distinguish economic value channels without creating independent sources of portfolio risk. Neither correlation nor momentum supplies a valuation by itself.

![Correlation estimates and uncertainty](../figures/crypto-cross-asset-correlations.svg)

## 3. Do we have publishable material?

**Yes: we have a credible publication candidate. We have not yet demonstrated a publication-ready empirical pricing model or established the novelty of the full contribution.** Acceptance depends on the final question, evidence, positioning and review.

| Output | Assessment today | Work needed |
|---|---|---|
| Advisory whitepaper or practitioner article | Strongest near-term format | Editorial review, independent checks on headline inputs, clear dates and limitations |
| Working paper on classification and capture | Enough material for a focused draft | Literature comparison, contribution statement, external rule feedback and a complete reproducibility package |
| Journal article on classification methodology | Plausible direction | Show what the decision rules add beyond prior taxonomies; test whether others can apply them on a defensible sample if reliability is claimed |
| Journal article claiming a superior valuation or return model | Current evidence is insufficient | Stronger fundamentals, appropriate benchmarks, later validation, clearer uncertainty and better asset coverage |

### Recommended first paper

**Working title: “Economic Functions and Token-Holder Capture: A Reproducible Framework for Cryptoasset Comparison.”**

The central question would be: *How can researchers distinguish what a token is used for from how economic value reaches the token or its holders, and what changes when that distinction is applied consistently?*

The paper would lead with the written rules, evidence, assumptions and boundary cases. The architecture comparison and capture-definition sensitivity would be supporting empirical demonstrations. RV1 and the traditional-market study could appear as limited applications or companion material, rather than expanding the main paper into several loosely connected projects.

### What may distinguish our contribution

The candidate contribution is the combination of explicit classification rules, dated evidence, materiality decisions, treatment of unresolved cases, the governance-versus-capture boundary, and an auditable link to advisory metric selection. Each element must be compared with earlier work; this review does not establish a first-in-literature claim.

The nearby literature makes that caution concrete:

- Zhang, Ibañez and Xu’s 2026 working paper already offers a multidimensional cryptoasset taxonomy and maps 100 assets. A new taxonomy by itself is not a sufficient novelty claim. [Crypto-asset Taxonomy for Investors and Regulators](https://arxiv.org/abs/2602.05098).
- Eska, Shi, Theissen and Uhrig-Homburg already link hand-collected design features to market values for 79 cryptocurrencies using regression and regularization. Our design-to-valuation question therefore has a direct precedent. [Design and valuation of cryptocurrencies](https://link.springer.com/article/10.1007/s11156-025-01447-9).
- Cong, Li and Wang develop a theoretical adoption-and-token-valuation framework. It provides a relevant foundation for why transactional demand and adoption require different treatment from conventional cash-flow claims. [Tokenomics: Dynamic Adoption and Valuation, author research page](https://www.linwilliamcong.com/research).

This is a targeted literature check, not a systematic novelty review. A comparison table should identify the exact rule, dataset or empirical distinction that our paper adds.

## 4. What currently limits stronger conclusions

The largest limitations are substantive:

- **Independent validation:** 220 of 230 cells are single-coded. A survey can validate boundary rules, but it is not an independent reconstruction of the matrix.
- **Sample size:** RV1 has 22 identity observations and 11 fundamentals observations. H3 has only three independent assets.
- **Time:** retrospective classifications and previously examined outcomes limit what can be called independent prediction. The fixed H8 validation window ends on 22 August 2027.
- **Measurement:** fees, protocol revenue, burns, buybacks and holder distributions are different objects. Their provider definitions and token linkages require verification.
- **Portfolio comparisons:** the benchmark study covers one year, uses asynchronous closes and ETF proxies, and has retrospective membership, USDT/USD basis differences and no independent second-vendor verification yet.
- **Economic identification:** predicting market capitalization is different from explaining intrinsic value, proving causality or forecasting excess returns.

These limitations do not invalidate the classification instrument. They constrain the empirical claims attached to it.

## 5. The next valuation process

The next goal should be to move from broad relative-size models to a small set of economically coherent asset models. This does not require treating every token as if it were a company with cash flows.

### Step 1 — Audit the economic denominator

For every modelling asset, document exactly what is being measured: gross fees, protocol-retained revenue, cash distributions, buybacks, burns, net issuance and incentives. Identify the recipient, date, units and whether the route was active at that time. Reconcile important figures to primary records where feasible and independently check key prices.

**Deliverable:** a reconciled fundamentals table with source definitions, observation dates, coverage and an explicit link from each metric to the token.

### Step 2 — Select the valuation lens by economic mechanism

| Asset mechanism | Next modelling lens | Key restriction |
|---|---|---|
| Monetary or store-of-value use | Adoption, settlement demand, liquidity, available supply and scenario-based monetary premium | A monetary premium must be measured or assumed transparently, not inferred from the binary code |
| Network and gas demand | Economic usage, fees, service demand and token supply | More transactions do not automatically imply value reaching holders |
| Measurable holder-directed distributions or buybacks | Capture-adjusted relative multiples; explicit scenarios for future holder benefits where the route is sufficiently evidenced | Separate legal claims, discretionary policies and mechanically executed routes |
| Usage-linked burns | Burn value, net issuance, demand and supply scenarios | A burn is not automatically equivalent to a cash dividend and cannot simply be discounted as one |
| Staking | Rewards from fees versus issuance, dilution, operating costs, exit constraints and loss exposure | Staking yield alone is not a fair-value formula; distinguish compensation from economic profit |
| Governance and utility | Control scope, accessible benefits, service demand and comparable economics | A protocol treasury is not token-holder net asset value unless the entitlement is established |

These are proposed lenses. The next experiment specification must fix the actual assets, variables and comparisons before estimation.

### Step 3 — Build a few asset case studies

Start with BTC, ETH and one sufficiently evidenced protocol-capture asset from the existing universe. These are contrasting economic cases, not selected because a residual looks attractive. The third asset should be chosen on data quality and a live capture mechanism. If those requirements are not met, report the gap.

For each case, show current economic mechanics at a stated date, historical fundamentals, a defensible peer set, scenario assumptions and the largest sources of model error. Keep historical model-implied capitalization distinct from a scenario valuation at a current date.

**Deliverable:** three readable valuation memos using the same “measurement → insight → implication → uncertainty” structure.

### Step 4 — Freeze and compare the next models

Pre-specify simple benchmarks, including size/liquidity and relevant architecture or maturity controls, alongside the function-based models. Comparisons must use the same eligible assets. Trading volume should not be treated as independent fundamental demand without a justification.

Where sample size supports it, test whether functions add information beyond those controls. Use training-only transformations and a genuinely later time split for forecasting claims. Preserve RV1 as the discovery-stage reference instead of changing its specification after seeing the errors.

**Deliverable:** a frozen model-comparison design and a clear explanation of what result would count as an improvement.

### Step 5 — Establish usable uncertainty and an advisory interpretation

Report scenario ranges, sensitivity to dominant assets, data uncertainty and predictive errors. If formal predictive intervals are introduced, state their assumptions and assess coverage on later data; do not relabel the existing empirical bands as calibrated intervals.

Only convert a capitalization scenario to a per-token price after specifying the valuation date, supply denominator, dilution and token-holder benefit mechanism. A positive or negative residual remains a prompt for investigation until supported by additional evidence.

## 6. Recommended next checkpoint

The next checkpoint should be **a fundamentals reconciliation and three-case valuation pack**, accompanied by a focused publication outline.

Completion would mean:

1. a literature comparison that states the proposed contribution and its limits;
2. a professor-reviewed outline for the classification-and-capture paper;
3. documented external-feedback plans for the decision rules;
4. reconciled economic metrics for BTC, ETH and an eligible capture asset;
5. a separately frozen next-model specification, with benchmarks and failure criteria;
6. a practical decision on whether to obtain ETH archive access for H4 now or leave H4 as clearly deferred.

The main human choices are the paper’s lead contribution, the external reviewers, and any paid archive access. Routine data audits and preparation of the valuation memos can proceed before those choices are finalized. H4, a fourth H3 asset and the future H8 window need not all be completed before a focused classification working paper is drafted.

## 7. Where to review the evidence

- [Full advisory report](crypto-advisory-report.md) and its [printable HTML edition](crypto-advisory-report.html).
- [Exact hypothesis methods and results](../methods/crypto_hypothesis_test_catalog.md).
- [RV1 model comparisons, asset estimates and peer multiples](crypto-relative-valuation.md).
- [Architecture and economic-similarity findings](crypto-architecture-economic-similarity.md).
- [Current open decisions](../open_decisions.md).
- [Research manuscript](../manuscript/main.tex).

The project is at a useful transition: we have a documented way to describe economic function and initial tests of its relevance. The next valuation work must explain mechanisms and improve measurement, rather than turn the existing residuals into price targets.
