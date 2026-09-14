# Digital Assets Valuation

**Can the economic jobs a cryptoasset performs explain what it is worth and how risky it is?**

This repository builds a reproducible way to answer that. It classifies cryptoassets by economic function rather than by technology or marketing label, proves every classification from dated primary sources, and tests whether those functions explain valuation and risk. Independent research developed at NYU Tandon (MS Financial Engineering), intended for publication.

Everything here is rebuildable. One command regenerates every processed artifact from archived raw snapshots, and 248 tests check the code that does it.

> **Working on this project?** Read [`CLAUDE.md`](CLAUDE.md) first. It carries the research rules that must not be broken, how to add a module or an experiment, and the traps that have already cost us once.

---

## 1. Motivation

To value a company you know what to look at. Revenue, costs, growth, what it returns to shareholders. The categories are agreed, and everyone understands that a bank and a software firm are different kinds of thing.

Cryptoassets have no such agreement. They get sorted by the technology underneath them, or by labels the projects choose for themselves. Neither says how the asset is supposed to accrue value.

The sorting is not just imprecise, it is actively misleading:

- **Bitcoin and Ethereum are both "Layer 1s"** — but Bitcoin has a fixed 21m supply and destroys no fees, while Ethereum has no supply cap and burns fees as they are paid. Opposite monetary designs, same label.
- **Uniswap and Aave are both "DeFi tokens"** — they share exactly one economic function out of ten.
- **Arbitrum and Ethereum both "capture value"** in common usage — but ARB holders vote on a treasury that funds grants, while every Ethereum transaction destroys ETH. Only one of those mechanically reaches the token.

So this project asks a different question. Not what technology is it, but **what economic jobs does it actually do, and can we prove it on a date?**

## 2. Research questions

1. Which economic functions is each asset performing, on each date, and does that carry information beyond what its architecture already tells you?
2. Does network usage explain what an asset is worth, over and above the market as a whole?
3. Does usage matter **more** when there is a live mechanism sending value back to the token?
4. Do assets doing several economic jobs at once command a premium over single-purpose assets?
5. Does economic function explain how **risky** an asset is, even where it fails to explain returns?

These become six registered experiments. Each has a specification file committed with a freeze date **before** its estimate is produced, so the test cannot be changed after seeing the answer.

| ID | Hypothesis | Status |
|---|---|---|
| P1_H1 | Usage is associated with higher network value | Estimated; positive, not significant |
| P1_H2 | Usage matters more when value capture is live | Estimated; **definition-dependent** |
| P1_H3 | Theory bundles beat a raw count of functions | Estimated; bundles do not improve on the count |
| P1_H4 | Staking reduces liquid float and affects liquidity | Source-ready; estimation blocked |
| P1_H5 | Turning a capture mechanism on or off moves value | Estimated; no effect detected |
| P1_H6 | Function predicts risk exposure, not return | Estimated; **not supported after correction** |

## 3. Architecture

Four layers, each doing one job.

**Layer 1 — technical context.** Proof of work, proof of stake, application token, rollup governance token. Recorded, then deliberately kept out of the economics. Architecture is a control variable, never an answer.

**Layer 2 — ten economic functions.** Each has a written rule, a list of the evidence that would satisfy it, and three possible verdicts: verified yes, verified no, or unresolved. A code is set to 1 only when the mechanism is *live at the observation date*, economically material, and backed by dated primary evidence.

| Code | The job it names |
|---|---|
| `VA_MONETARY` | Used as money, settlement, or a store of value |
| `VA_GAS` | Required to pay for using the network |
| `VA_STAKE` | Locked or economically at risk to secure something |
| `VA_BURN` | A live rule permanently destroys tokens |
| `VA_SCARCITY` | A hard cap that is exceptionally difficult to change |
| `VA_COLLATERAL` | Accepted as material collateral elsewhere |
| `VA_GOV` | Holding it confers real control |
| `VA_PROTOCOL` | Revenue mechanically reaches the token or its holders |
| `VA_UTILITY` | Required to buy an identifiable service |
| `VA_INCENTIVE` | A programme subsidises usage or participation |

**Layer 3 — eight bundles.** The ten functions group into eight economically distinct families (monetary store, transaction service demand, security commitment, supply absorption, financial integration, control rights, holder capture, subsidised participation). The grouping was fixed from theory *before* any estimation, so it cannot be tuned to a result.

**Layer 4 — measurement readiness.** For each of the 34 pieces of evidence the rules call for, the pipeline records whether it exists as a real time series, a proxy, a document only, or not at all. Three functions are measured, three proxied, four documentary. This is stated openly because a function you can only document cannot enter a valuation model as a variable.

### The sharpest rule: governance is not capture

The hardest boundary is between **having a vote** and **receiving value**.

Arbitrum's DAO receives network revenue and ARB holders control the treasury. Tempting to call that value capture. But the money funds grants, infrastructure and development — it never mechanically reaches the token. Compare Ethereum, where each transaction burns ETH, or Aave's buyback, which uses revenue to buy the token itself.

> **Governance authority over a treasury is not value capture unless value mechanically terminates at the token** — through a burn, a buyback, a distribution, or an enforceable claim. Voting on how to spend money is a right, not a cash flow.

This one rule is the difference between a headline result and no result (see §6).

## 4. Data universe

25 non-stable cryptoassets, selected on market capitalisation, volume, economic relevance and reproducible free-data access, plus 16 stable-value assets preserved for a deferred phase.

| Dataset | Coverage | Used for |
|---|---|---|
| Daily OHLCV | 24 assets, 2019-01-02 to 2026-08-22, 52,116 asset-days | Return panel, factor baseline, risk measures |
| Chain and protocol fees | 11 economic systems, 362 days | The usage variable in H2 |
| Network activity | 4–5 assets on free provider tiers | H1, H3 |
| Collateral balances | Daily protocol state reads, 90-day windows | `VA_COLLATERAL` evidence |
| Staking series | BNB validator pools, legacy stkAAVE, 90 days | H4 (blocked) |
| Classification evidence | Dated primary-source URL per decision | All ten codes |
| Mechanism ledger | Effective-dated burn and capture events, 11 assets | H2 treatment, event study |

Fee coverage is chain-level for nine assets and application-level for two. That distinction is carried through every model as a measurement attribute, never quietly collapsed.

**Classification coverage:** 119 of the 250 registry cells (25 assets × 10 functions) are evidence-verified — 60 on the fully verified six-asset core, 59 in the first tranche covering fourteen more assets.

## 5. Process and approach

### The rules the code enforces

1. **Freeze before you look.** Every experiment's specification is committed, with a freeze date, before its estimate exists.
2. **Never backfill.** What we know today cannot be applied to yesterday's prices. Every mechanism carries the date it became true, and the panel resolves the state prevailing on each day. Uniswap did not burn fees until December 2025, so for every earlier date that code reads zero.
3. **Unknown is not zero.** Missing evidence stays null. A zero means someone reviewed it and the criterion was not met.
4. **Correct for looking many times.** 27 tests get 27-test treatment.
5. **Report the weaker version.** Where two defensible specifications disagree, both are published side by side.
6. **Don't choose what to measure based on what showed a result.** Coding tranches are ordered by evidence difficulty, decided in advance.
7. **A rule adjudicated once applies everywhere.** The treasury boundary settled Arbitrum and Cardano together, and now settles Zcash's development fund the same way.

### How a classification becomes evidence

```
written rule  ->  coder drafts from dated primary source  ->  blind second reviewer scores
      ->  agreement + Cohen's kappa  ->  disagreements adjudicated by a written rule
      ->  verified value enters the design matrix
```

Reviewer worksheets carry no coder value, source or rationale, and a test enforces that. Completed worksheets live outside version control so regenerating a blank template can never overwrite a reviewer's work.

### Coding tranches

The remaining classification work is split by **how the evidence is obtained**, in an order fixed in advance:

| Tranche | Codes | Why grouped | Status |
|---|---|---|---|
| **A** | gas, stake, scarcity, burn, protocol | Fact check against protocol documentation | Drafted: 59 of 70 verified, 11 pending |
| **B** | collateral, monetary | Need a 90-day quantitative window and a materiality threshold | 28 decisions outstanding |
| **C** | governance, utility, incentive | Boundary calls needing blind review most | 42 decisions outstanding |

### The pipeline

67 modules in seven ordered stages. A test fails if any module is missing from the stage map.

| Stage | Network | What it does |
|---|---|---|
| `ingestion` | yes | Collects and archives raw snapshots from CoinGecko, DeFiLlama, CoinPaprika, Binance, Coin Metrics, Dune, and on-chain RPC reads. Some commands need keys in `.env`. |
| `crypto_classification` | no | Validates the ten-code matrix, audits evidence tranches, resolves effective-dated mechanism states, reconciles independent review, freezes the taxonomy and research map. |
| `crypto_h2` | no | Builds the eleven-asset fee-capture panel, runs diagnostics, frozen estimates, exact small-cluster inference, non-overlap and strict-rule sensitivities, and the mechanism event study. |
| `crypto_cross_section` | no | H1 activity pilot, H3 supply diagnostic, H4 source readiness, H8 breadth pilot and six-asset extension, bundle comparison. |
| `crypto_returns` | no | Daily return panel (24 assets, 2019-2026), factor baseline, and the frozen P1_H6 test of function against beta, volatility and drawdown. |
| `stablecoin_deferred` | no | Stablecoin H5-H7 work, preserved for a later phase and not an active gate. |
| `reporting` | no | Plain-language findings summary and the commit-readiness checkpoint. |

```bash
python -m src.pipeline.run_stages --repo . --list
python -m src.pipeline.run_stages --repo . --offline           # every non-network stage, in order
python -m src.pipeline.run_stages --repo . --stage crypto_h2   # one stage
python -m unittest discover -s tests                           # 248 tests
git status --short                                             # should be empty after a rebuild
```

An empty `git status` after a rebuild means the committed artifacts are exactly what the code produces. The rebuild is deterministic; repeat runs are byte-identical.

### Statistical approach

With six to twenty assets, large-sample approximations do not apply. So the design stops approximating and starts counting. Instead of trusting a t-distribution, we enumerate the possibilities: all 2,048 Rademacher sign assignments for the eleven-cluster wild bootstrap, all 720 permutations for a six-asset cross-section. The p-values are exact and reproducible to the digit. The cost is honest — with six assets and a 3-3 binary split, the smallest attainable p-value is 0.10, so that sample cannot reject at 5% however strong the effect.

Full walkthrough in [`research/findings/2026-09-07-the-math-explained.md`](research/findings/2026-09-07-the-math-explained.md).

## 6. Where the project stands

**The instrument works and the results are mostly null.** That is the honest state of this literature at this sample size.

- **Architecture does not predict economics.** Two PoS base layers in the verified core differ on two of ten functions; two application tokens share one.
- **The central capture result is definition-dependent.** Fee activity is more strongly associated with market value when a capture route is live: pooled interaction 0.132, exact p = 0.082, positive in all eleven leave-one-out samples. Apply the strict holder-capture rule and it halves to 0.061 with p = 0.478. **Whether a governed treasury counts as capture is the difference between a result and no result.**
- **Counting functions explains nothing.** Breadth slope 0.484, permutation p = 0.442. Bundle count does not improve on it.
- **Mechanism activations are not visibly priced.** Three events, 22 controls, ~280 calendar placebos each. One carries its expected sign; none rejects at 10%.
- **A single market factor dominates.** Median beta 1.03, median R² 0.60 across 24 assets. Lagged beta is negatively priced (t = −2.12).
- **Function and risk move together but do not survive correction.** Monetary assets average beta 0.93 and worst drawdown −1.44 against 1.19 and −2.37. Three of 27 tests reach p ≤ 0.05 against 1.35 expected by chance; none survives a 10% false-discovery rate.

Not defensible, and stated as such: any claim that economic function predicts returns, and any market-wide claim about function and risk while nineteen assets remain unverified.

### Immediate workstream

1. Complete tranches B and C and adjudicate the 11 pending cells, then re-estimate the already-frozen P1_H6 on verified codes. The specification must not be revised.
2. Collect point-in-time unlock and issuance events so H3 becomes identification-ready.
3. Resume H4 once an archival Ethereum consensus endpoint is available.
4. Extend the frozen H2 panel only under a separately versioned future specification.

Every decision that needs human judgment is registered in [`research/open_decisions.md`](research/open_decisions.md), with what changes if it flips and which result it blocks.

## 7. Repository layout

The project runs in phases. **Phase 1, economic classification, is the active phase**; see [`PROJECT_PLAN.md`](PROJECT_PLAN.md) for the phase breakdown, the gates between phases, and flowcharts of the programme and the Phase 1 workflow.

Processed data is grouped by the phase that owns it, so you can tell from the path which question a file belongs to:

```
data/
  raw/                              immutable dated snapshots, by source, never edited
  processed/
    00_foundation/                  shared market, price and activity series
    01_classification/   ← active   Phase 1 evidence, mechanism states, taxonomy
    02_valuation/                   H1 H2 H3 H8 and the event studies
    03_risk/                        return panel, factor baseline, P1_H6
    04_stablecoin_deferred/         H5-H7, preserved and parked
```

Every file in there is catalogued in [`DATA_MAP.md`](DATA_MAP.md) with the module that writes it and the modules that read it. That file is generated by the pipeline, so it cannot drift.

- `config/` — frozen specifications: asset registry, classification rules, evidence tranches, effective-dated mechanism ledger, and one JSON per experiment written before its estimation. `config/pipeline_stages.json` is the ordered map of every module.
- `src/pipeline/` — one module per command; `run_stages.py` executes them in frozen order.
- `src/artifacts/` — reproducible builders for document and workbook artifacts.
- `tests/` — unit tests for every module, including one that fails if the stage map misses a module and one that fails if any data file has no producer.
- `research/` — the human-readable layer: manuscript, findings notes, methods, preregistration, the open-decisions register and the survey instrument. Start at [`research/README.md`](research/README.md).
- `review_inputs/` (Git-ignored) — completed reviewer worksheets, kept out of version control on purpose.
- `docs/` (Git-ignored) — private working notebook and meeting notes.

## 8. Further reading

| Document | What it covers |
|---|---|
| [`research/findings/2026-09-07-research-program-explained.md`](research/findings/2026-09-07-research-program-explained.md) | The whole programme in plain language |
| [`research/findings/2026-09-07-the-math-explained.md`](research/findings/2026-09-07-the-math-explained.md) | Every statistical technique and why it was chosen |
| [`research/findings/2026-09-07-checkpoint-function-and-risk.md`](research/findings/2026-09-07-checkpoint-function-and-risk.md) | The most recent results |
| [`research/manuscript/main.tex`](research/manuscript/main.tex) | The paper |
| [`CLAUDE.md`](CLAUDE.md) | How to work on this without breaking it — rules, conventions, traps |
| [`PROJECT_PLAN.md`](PROJECT_PLAN.md) | Phases, gates, and the Phase 1 workflow |
| [`DATA_MAP.md`](DATA_MAP.md) | Every data file, its phase, producer and consumers |
| [`research/open_decisions.md`](research/open_decisions.md) | What still needs human judgment |
| [`research/survey_instrument.md`](research/survey_instrument.md) | The expert panel that unblocks Phase 1 |

---

*Classifications are research codes, not legal conclusions. Every result is an association, not a causal or investment claim.*

## Command reference

Every command accepts `--repo .` and can be run individually with `python -m src.pipeline.<module>`; `config/pipeline_stages.json` records the arguments used for the frozen snapshots. Commands that reach the network are listed under the `ingestion` stage. The descriptions below follow the stage order.

The registry command validates the asset configuration and frozen raw snapshots, records SHA-256 hashes, and writes the identifier registry and cross-sectional coverage audit to `data/processed/2026-08-22/`. It also writes a readable audit note to `research/findings/`.

The historical command performs a bounded example pull. The collector chunks long requests, caches immutable raw responses and retrieval metadata, normalizes data to UTC dates, merges incremental runs without discarding earlier assets, and writes daily data plus a missingness report to `data/processed/historical/`. Set `COINGECKO_API_KEY` when the selected CoinGecko plan requires authenticated historical access.

For local authenticated APIs, copy `.env.example` to `.env` and add keys there. The CoinGecko historical collector loads the repository `.env` automatically; existing shell environment variables take precedence. `.env` is excluded from Git and must never contain credentials intended for sharing.

The DeFiLlama fallback command builds the long daily-price history when early CoinGecko access is unavailable. It uses one asset per provider request, yearly cache partitions, nearest-UTC-day normalization, and active-window coverage diagnostics. It supplies price only; historical market capitalization, volume, and circulating supply remain separate data workstreams.

The stablecoin-supply command collects DeFiLlama `circulating.peggedUSD` histories for supported assets. The source-availability command produces the explicit metric-by-asset matrix showing which histories are implemented or still blocked.

The stablecoin-risk command validates evidence-linked component inputs and calculates strict reserve-quality, transparency, and redemption-friction scores. Strict composites are withheld when any required component is unknown.

The stablecoin-evidence command enforces the focused eight-asset H5/H6 evidence plan and separates source discovery from verified point-in-time extraction. Verified, dated summaries and reconstructible locators live in `config/stablecoin_evidence_extractions.json`; the command audits five required evidence classes per asset and prohibits treating an undated or merely discovered source as score-ready evidence.

The stablecoin-scorecard command applies a versioned 0--4 ordinal rubric to the five verified evidence classes and produces an eight-asset point-in-time scorecard. It validates that every component has matching dated evidence, reports confidence, and keeps developmental design scores distinct from estimated H5/H6 results.

The stablecoin-score-intervals command combines current scores with independently evidenced historical intervals, validates source availability and non-overlap, and prohibits gaps between explicitly consecutive regimes for the same asset.

The H5-H6 readiness command generates a blind, 40-row targeted component-review worksheet and audits temporal overlap between score dates and peg outcomes. It explicitly blocks retrospective use of later design scores, preventing look-ahead bias before model estimation.

The crypto-economic-design command validates the provisional ten-code value-accrual matrix against the frozen 25-asset non-stable universe. It creates an asset-level H2/H8 profile and a blind 250-decision review worksheet; provisional classifications cannot be treated as frozen research inputs until evidence-backed review is complete.

The crypto-Phase-1-taxonomy command consolidates the evidence-backed six-asset core into a three-state classification matrix: verified positive, verified negative, or unresolved. It keeps technical architecture separate from economic function, maps all ten functions into eight theory-defined bundles, publishes value indicators and prevalence, and freezes five falsifiable Phase 1 experiments before new estimation. Raw function breadth is withheld for incomplete assets. Under the adjudicated strict holder-capture rule, governed ecosystem spending alone is `VA_GOV`, not `VA_PROTOCOL`; therefore Phase 1 records ARB `VA_PROTOCOL=0`. The frozen exploratory H2 pilot retains its older broad treasury definition as historical output and is not relabeled as a strict-rule result.

The crypto-Phase-1-research-map command joins the frozen ten-code taxonomy to what the repository can actually measure. For every code it records the bundle, rule, six-asset prevalence, each value indicator's observability state (observed series, partial or proxy series, documentary only, or not collected, with the dataset and column that back any series claim), and the registered Phase 1 experiments that use it. Monetary, gas, and collateral functions are measured; staking, burn, and protocol capture are proxied; scarcity, governance, utility, and incentive remain documentary. Documentary indicators support classification only and never enter valuation tests unlabeled.

The crypto-mechanism-event-study command estimates the frozen Phase 1 P1_H5 experiment: every effective-dated burn or protocol-capture state change in the mechanism ledger whose full thirty-day pre and post window lies inside the frozen H2 panel. That rule admits the UNIfication fee-to-burn activation (2025-12-27) and the Aave buyback pause (2026-04-19); the TRON entry on the first panel day has no pre-window and is excluded by rule. Each event reports a difference in mean log market value against uncontaminated control assets, an exact asset-placebo p-value from reassigning treatment to each control, a calendar-placebo p-value from non-overlapping shifted windows, and the same statistic for lagged fees so a valuation move is not attributed to capture when usage moved too. Two events are exploratory sensitivity evidence, not causal estimates.

The crypto-Phase-1-bundle-comparison command estimates the frozen P1_H3 experiment on the six verified assets. Eleven pre-listed models (raw breadth, active bundle count, each of the eight bundles alone, and raw breadth plus holder capture as the one pre-declared theory addition) are compared by leave-one-asset-out prediction error for mean log market value and a market-cap-to-daily-fees multiple; single predictors also get exact 720-permutation rank tests. The activity multiple is withheld because free activity data covers only four assets. Raw breadth and bundle count are nearly collinear on this core (rank correlation 0.96), bundle count does not beat breadth, and only the monetary-store bundle lowers prediction error. Six assets support description, not confirmation.

The crypto-H2-strict-capture-sensitivity command re-estimates the two frozen H2 valuation specifications after relabeling capture states under the Phase 1 strict holder-capture rule, using only a pre-listed override (ARB `VA_PROTOCOL=0`) applied to a copy of the panel. The frozen pilot, its evidence files, and its event ledger are untouched. Under the strict rule the pooled interaction falls from 0.132 ($p=0.082$) to 0.061 ($p=0.478$) and the chain estimate from 0.141 to 0.060; the frozen headline does not survive the stricter capture definition and is reported beside it as a robustness result.

The crypto-return-panel command builds the first daily return panel for the research universe from archived Binance USDT closes: 24 assets, 2019 through August 2026, about 52,000 asset-days. Fields are predeclared (daily log return with a three-day gap rule, seven- and thirty-day forward returns, thirty-day momentum skipping the last week, thirty-day realized volatility, log dollar volume, an equal-weighted market return, the BTC return, and a lagged 180-day rolling market beta). The risk-free rate is set to zero and declared as such. The panel supports description and factor baselines; daily crypto returns are close to unpredictable, so the intended findings concern risk exposure and behaviour conditional on economic function.

The crypto-return-factor-baseline command establishes what is already known before any economic-function return test. Per-asset market models give a median beta near one and a median R-squared of 0.60, so the common factor explains most daily variation. Daily Fama-MacBeth cross-sections with Newey-West standard errors show a negative lagged-beta premium, flat momentum, and no volatility premium. Equal-weighted sorts of the six verified assets by bundle are descriptive previews on the 2023-2026 common window: monetary-store and financial-integration positives carry lower beta and shallower drawdowns than negatives, control-rights positives the reverse. Three-versus-three portfolios cannot support inference; the sorts show what the classification will be tested on once the remaining universe is verified.

The crypto-function-risk-exposure command estimates the frozen P1_H6 experiment: whether economic function predicts market beta, realized volatility, and maximum drawdown. All assets are measured on one common window (24 March 2023 to 22 August 2026, set by the ARB listing) so the three risk measures are comparable, and every regression carries mean log dollar volume as a size control. Two samples are reported separately: the six evidence-verified assets with exact 720-assignment permutation inference, and twenty provisional-matrix assets with fixed-seed Monte Carlo permutation. Benjamini-Hochberg q-values cover all 27 predictor-by-outcome tests within each sample, and predictors without cross-asset variation are reported as unestimable rather than dropped. In the provisional universe three tests reach $p \le 0.05$ against 1.35 expected by chance and none survive a 10 percent false-discovery rate.

The long-panel variant of the mechanism event study (`--spec config/crypto_mechanism_event_study_long.json`) applies the same design to the 2019-2026 daily return panel. A stated transition rule admits only ledger events that differ from the preceding recorded state, which adds the April 2025 Aave buyback activation that falls outside the one-year H2 window, and expands each event's placebo pool to twenty-two control assets and roughly 280 non-overlapping calendar placebos. One of three events carries its expected sign and none reject at 10 percent.

The crypto-evidence-tranche-A command audits the first evidence tranche for the fourteen return-panel assets that are not yet classification-verified, covering the five rule-mechanical codes (gas, stake, scarcity, burn, protocol capture) whose determination is a fact check against protocol documentation. Tranche order is fixed by evidence difficulty before estimation and explicitly not by which bundle showed signal in P1_H6, because selecting codes by outcome would compromise that frozen test. Of 70 drafted decisions 59 are verified against dated primary sources and 11 are held pending; a pending cell never defaults to zero. The command reports disagreements with the provisional design matrix, emits a blind worksheet that carries no coder value or rationale, and refuses any consistency case that does not name a genuinely pending cell. Verified values may be written into the design matrix only after independent review and adjudication.

The crypto-design-evidence command audits the first prioritized H2/H8 evidence tranche. It requires a complete asset-code grid, dated HTTPS sources, binary values only for verified decisions, and explicit nulls for unresolved quantitative or mechanism tests.

The crypto-fundamentals command collects the Coin Metrics Community fields confirmed to be free: daily addresses, transactions, transfer count, market capitalization, and supply for the first evidence tranche. Coverage is audited per metric; activity supplies at most one `VA_MONETARY` behavioral test and never substitutes for separate acceptance or holding evidence. Adjusted transfer value, fees, and issuance are explicitly reported as unavailable on this free tier.

The crypto-collateral command screens exact token balances across a named eight-protocol, chain-relevant lending sample against the preregistered 1%-of-market-cap or $100m-for-90-days rule. Every selected protocol must cover the full window before a below-threshold result can support zero. DeFiLlama supplied-token TVL remains a screening proxy: a passing asset still requires effective-dated proof that the balance was collateral-enabled before `VA_COLLATERAL=1` can be frozen.

The Aave collateral-state command resolves daily Ethereum blocks and performs historical read-only `Pool.getConfiguration` calls for WBTC and WETH. Eligibility passes only when LTV is positive, the reserve is active, and it is not paused on every day of the 90-day materiality window; raw RPC responses and hashes are archived.

The Venus-BNB-collateral-state command resolves daily BNB Chain blocks and reads the official Venus Core Pool `markets(vBNB)` state. BNB is classified as material collateral only when vBNB is listed with a positive collateral factor on every date and the separately collected supplied-balance proxy passes the preregistered threshold throughout the same 90-day window.

The crypto-monetary command implements the two-test `VA_MONETARY` rule: 90 days of material address/transaction activity plus independent, dated primary evidence of monetary or payment design. Missing provider data and failure of this pilot screen remain unresolved rather than being converted into negative classifications.

The crypto-mechanism-state command resolves burn and protocol-capture classifications from effective-dated activation, pause, and deactivation events. The latest event known by the observation date must match the design matrix; promised, paused, or inactive mechanisms remain zero.

The crypto-H2/H8-readiness command creates a six-asset pilot design panel without filling unevidenced fields from the provisional matrix. H2 capture is released only when burn and protocol capture are verified; H8 breadth stays null until all ten value-accrual codes are verified.

The crypto-fee-fundamentals command archives DeFiLlama's free daily fees, protocol revenue, and holder revenue for eleven associated economic systems. Primary fee coverage is complete for nine chains and two application protocols; secondary protocol-revenue and holder-revenue coverage is incomplete and must use observed-sample models. Scope and accounting concepts are retained explicitly and never treated as interchangeable.

The crypto-H2-pilot-panel command joins eleven-asset CoinPaprika market outcomes, four-asset Coin Metrics activity, free fee/revenue histories, and effective-dated capture events without backfilling later classifications. Exact one-day explanatory lags and exact seven-day forward returns preserve gaps. The candidate H2 panel carries an application-scope indicator and predeclared pooled, chain-only, application-only, and leave-one-asset-out sensitivities. Eleven clusters improve resolution but remain too few for unguarded conventional asymptotics.

The crypto-H2-expansion-readiness command proves that SOL, AVAX, TRX, XRP, and ADA independently pass the predeclared market-coverage, complete-fee-history, and effective-dated mechanism-evidence gates. It explicitly prohibits selecting expansion assets from model outcomes.

The crypto-H2-expansion-evidence command reconciles the five added assets' ten burn/protocol decisions exactly to the effective-dated event ledger and official source URLs. The completed focused review and Cardano adjudication now reconcile 10 of 10 decisions; the eleven-asset specification is frozen post-pilot for reproducibility while remaining exploratory.

The crypto-research-scope command makes H1, H2, H3, H4, and H8 the active research program and preserves H5-H7 as a deferred stablecoin phase. This prevents unfinished stablecoin review or coverage work from blocking crypto classification, discovery, and reporting.

The crypto-findings-summary command produces the single plain-language status artifact for the active phase. It reports the H1, frozen exploratory H2, H3 diagnostic, and H8 evidence, distinguishes the H3 data limitation and unestimated H4 from completed pilots, records the resolved Cardano rule, and keeps stablecoin work visibly deferred.

The crypto-H8-breadth-pilot command tests the verified raw ten-function breadth count against average log market value for the five complete-case assets. It enumerates all 120 assignments, reports rank association and leave-one-asset-out slopes, and prohibits outcome-tuned weights or claims of reliable inference from the tiny cross-section.

The crypto-H1-activity-pilot command estimates a two-way fixed-effect association between market value, active addresses, and transaction count for the fixed BTC/ETH/UNI/AAVE common-coverage sample. It exhaustively enumerates all 16 four-cluster sign assignments and treats active addresses as ledger addresses rather than users. The source-defined pilot cannot be generalized to the broader universe.

The crypto-H3-supply-pilot command tests lagged seven-day Coin Metrics circulating-supply growth against the next seven-day return for the same fixed four-asset sample, controlling for lagged activity with asset and date effects. It reports the effect per basis point, exact four-cluster inference, leave-one-out estimates, and a variation audit. Because only BTC and ETH vary under the free provider measure, the output is explicitly not an identification-ready issuance or unlock event study.

The crypto-H4-readiness command reconciles the six verified `VA_STAKE` decisions to an official-source plan and recent market-turnover coverage. It blocks estimation until historical staking participation exists for at least three positive-staking assets, and it prohibits pooling consensus staking with protocol-risk staking without a predeclared comparability design. Turnover is retained as a proxy rather than mislabeled as spread, depth, price impact, or liquid float.

The crypto-H4-Aave-legacy-stake command reads ERC20 `totalSupply()` for the official legacy stkAAVE contract at archived daily Ethereum blocks. The 90-day series is labeled `legacy_component_only` and is prohibited from releasing H4 because current Aave Umbrella security also includes aToken and GHO stake.

The crypto-H4-BNB-stake command resolves the historical StakeHub validator set and sums `totalPooledBNB()` across every returned validator credit contract at each daily archival BSC block. Its 90-day output is a complete consensus-staking component; BNB already moved into unbonding queues is excluded.

The crypto-H4-ETH-stake command maps each UTC study date to a Beacon slot and sums `effective_balance` across all active validator statuses. It caches raw responses and redacts credential-bearing endpoint paths from provenance. A no-key public endpoint is retained only as a connectivity probe because it rejects historical validator state; an archival endpoint must be supplied locally through `ETH_BEACON_ARCHIVE_API_URL`. Validator count multiplied by 32 ETH is deliberately rejected after EIP-7251.

The review-adjudication command validates the exact crypto review grid, rejects incomplete metadata and out-of-range judgments, calculates raw agreement and Cohen's kappa only for a complete review, and emits disagreement fields. The preserved stablecoin review is reported as deferred and cannot gate the active crypto phase.

Completed reviewer worksheets are private inputs and must not be committed. Copy the generated templates to `review_inputs/crypto_h2_expansion_blind_review.csv` and `review_inputs/stablecoin_score_targeted_review.csv`, have the independent reviewer fill those copies, and rerun the command. The directory is Git-ignored, so regenerating pipeline templates cannot overwrite completed reviews.

The crypto-H2-estimator-diagnostics command audits usable observations, within-asset fee variation, two-way fixed-effect design rank, scope representation, and every leave-one-asset-out sample without estimating hypothesis coefficients. A pass establishes computational feasibility only; the two-asset application scope remains descriptive and the eleven-cluster pilot remains exploratory.

The crypto-H2-exploratory-estimates command produces guarded two-way fixed-effect point estimates for the predeclared pooled and chain-only market-cap and forward-return specifications. It reports within-fit and eleven leave-one-asset-out sensitivities; inference remains in a separate audited artifact.

The crypto-H2-small-cluster-inference command adds CR1 asset-clustered statistics and exhaustively enumerates every Rademacher wild-cluster assignment under the zero-interaction null. Pooled tests enumerate 2,048 assignments across eleven clusters and chain tests enumerate 512 across nine; overlapping forward-return results remain exploratory pending horizon-robust interpretation.

The crypto-H2-nonoverlap-sensitivity command partitions seven-day forward returns into all seven calendar offsets. Dates within each offset are spaced seven days apart, eliminating overlapping return intervals without choosing a favorable starting day. Offset results are sensitivity evidence, not independent tests, and expose sign instability hidden by the full overlapping panel.

The crypto-evidence-blockers command reconciles a machine-readable blocker manifest to the unresolved evidence grid. BNB collateral is now verified from 90 daily Venus Core Pool state reads; the remaining blocker documents the exact evidence required to resolve BNB monetary use and enforces a five-asset complete-case H8 policy while that field remains null.

The crypto-H8-evidence-plan command formalizes positive, negative, and source requirements for gas, staking, scarcity, governance, utility, and incentive classifications. Two independently validated evidence tranches verify all 36 decisions, correct BNB governance, UNI incentive, and AAVE utility classifications, reject duplicate tranche decisions, and audit agreement with the design matrix. Full H8 breadth remains unavailable for BNB until its monetary-use field is resolved.

The checkpoint-readiness command reconciles the stablecoin and crypto evidence outputs, lists every unresolved pilot decision, enforces missingness and temporal guardrails, and writes a single machine-readable checkpoint. A passing checkpoint means the methodology increment is safe to commit; it does not mean H2/H8 or H5/H6 are ready for final estimation.

The CoinPaprika command builds a no-key, rolling recent-market panel containing daily price, reported market capitalization, and 24-hour volume. CoinPaprika's free tier exposes only the latest year of daily history, so this source is a recent-period and cross-source-validation layer rather than a substitute for the full 2019–2026 market-cap panel. Identifier ambiguity is surfaced in a separate audit and never resolved by symbol alone when multiple active candidates exist.

The CryptoCompare command builds a paginated 2019–2026 daily OHLCV panel for verified non-stable crypto symbols. Its `volume_quote_usd` field is CCCAGG pair volume converted to USD, not total global spot volume and not directly interchangeable with CoinPaprika's reported 24-hour volume. Provider zero-padding before an asset's observed history is discarded.

The Binance command uses the official keyless market-data host and records venue-specific daily candles, quote volume, trade counts, and taker volume for active USDT/USDC/FDUSD spot pairs. Quote-stablecoin units are retained as such and are not silently relabeled as exact USD.

The stablecoin-panel command joins the long daily price panel to supported circulation histories and strict design scores, calculates peg-error and threshold variables, and produces a daily depeg-event table. PAXG is excluded because a gold benchmark is required. Missing calendar days censor open episodes instead of being bridged.

The stablecoin-atlas command produces asset-level peg statistics, band-robustness rates, episode rankings, monthly stress concentration, an explicit extreme-observation review queue, and a reproducible SVG summary chart. USTC remains visible as a failure control but is excluded from primary-sample rankings.

The preregistration command validates and renders the machine-readable H5-H7 draft and records checksums for its current analytical inputs. The draft contains explicit readiness gates and remains labeled `draft_not_frozen` until point-in-time design evidence, second-coder review, and remaining H7 inputs are complete.

The stablecoin-global-market command archives and normalizes DeFiLlama's free aggregate `totalCirculatingUSD.peggedUSD` history without interpolation. The stablecoin-adoption command then constructs exact-date supply growth, pilot concentration, within-pilot share, and DeFiLlama global pegged-USD share. This denominator does not represent non-USD-pegged stable-value assets.

The stablecoin-chain-distribution command extracts daily chain balances already preserved in DeFiLlama raw histories and calculates chain breadth, concentration, effective chain count, and top-chain share. These are cross-chain distribution proxies, not transaction usage or protocol-integration counts.

The stablecoin-trading-activity command joins the recent CoinPaprika volume panel to supply and peg outcomes and calculates volume-to-supply turnover. It is a recent reported trading-activity proxy, not order-book liquidity or settlement usage.

The Binance stablecoin-depth command archives keyless spot order-book snapshots and measures quoted spread, executable bid/ask depth within 10/25/50 bps, and simulated price impact for 100,000 and 1,000,000 anchor-unit trades. Quote-oriented pairs are algebraically inverted into the target stablecoin's perspective. These are venue-specific point-in-time observations; repeated snapshots are required before they can enter H7 panel estimation.

The DeFiLlama yield-integrations command archives the current free yield-pool universe and constructs conservative exact-symbol-component counts of pools, projects, and chains for each primary stablecoin. It is a cross-sectional yield-integration proxy—not an exhaustive or historical protocol-integration measure—and gross matched-pool TVL is not token-specific TVL.

The Coin Metrics stablecoin-usage command collects free daily active-address, ledger-transaction, and token-transfer metrics for explicitly supported provider assets and emits a full 14-asset coverage audit. Active addresses are not unique users, and unsupported assets remain null rather than being inferred from chain-level totals.

The stablecoin usage-panel command applies the fixed two-tier H7 design: all 14 coverage-qualified assets remain in the primary supply/share specification, while USDT, USDC, DAI, and TUSD enter a separate exploratory usage panel with exact one-day lags. The usage subsample cannot replace or determine the primary sample.

The H7-readiness command constructs the lagged recent joined panel, variable-by-asset coverage matrix, objective sample gate, and pass/fail readiness report. It does not declare H7 ready while market depth, integrations, and usage remain unsourced.

This repository is for academic research. Classifications are not legal conclusions or investment recommendations.
