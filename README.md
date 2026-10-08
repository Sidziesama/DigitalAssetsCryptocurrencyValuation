# Digital Assets Valuation

Latest empirical checkpoint: the frozen 23-asset H8 extension finds that financial integration is the strongest single economic-function valuation indicator and modestly improves leave-one-asset-out prediction relative to raw function breadth. See `research/findings/2026-10-08-h8-verified-universe.md` for the full exploratory, non-causal result and limitations.

Visual summary: `research/findings/crypto-visual-analysis.md` shows the classification-to-hypothesis flow, group coverage, and H8 prediction comparison.

Latest H3 checkpoint: 12 material ARB monthly unlocks have been estimated descriptively, but the mean three-day abnormal return has the opposite sign from H3 and a second qualifying asset is still required before pooled inference.

**Can the economic jobs a cryptoasset performs explain what it is worth and how risky it is?**

This repository builds a reproducible way to answer that. It classifies cryptoassets by economic function rather than by technology or marketing label, proves every classification from dated primary sources, and tests whether those functions explain valuation and risk. Independent research developed at NYU Tandon (MS Financial Engineering), intended for publication.

Everything here is rebuildable. One command regenerates every processed artifact from archived raw snapshots, and 312 tests check the code that does it.

**One coder does the classification.** Independent reproducibility is untested and is stated as a limitation throughout, not worked around.

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
| H3 | Greater circulating-supply growth predicts weaker returns | Diagnostic only; insufficient within-asset variation |
| H4 | Staking reduces liquid float and affects liquidity | Source-ready; estimation blocked |
| H8 | Theory groups outperform a raw count of functions | 23-asset extension favors groups; exploratory |
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

**Classification coverage:** all 230 active-universe cells (23 assets × 10 functions) are evidence-backed with a dated source, explicit rule and researcher decision. DOGE and XMR are preserved for auditability but excluded from active-universe counts.

The full asset-by-function matrix is in [`docs/crypto_economic_classification_phase_summary.md`](docs/crypto_economic_classification_phase_summary.md); the canonical counts are regenerated into `data/processed/01_classification/classification_status.json` and nothing else is authoritative.

Of the 230, **10 carry a blind second review** (SOL, AVAX, TRX, XRP and ADA on burn and protocol capture). The other 220 were coded once. Evidence-backed and independently reviewed are different claims and the repository never merges them.

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
written rule  ->  one coder applies it to a dated primary source
      ->  decision, source URL and read date are committed
      ->  cells the evidence does not settle stay pending
      ->  verified value enters the design matrix
```

**This is a single-coder project, and that is the most serious limitation in it.** Ten cells carry a blind second review from an earlier pass; the other 220 evidence-backed cells do not. So the matrix is *auditable* — every cell names its rule, its source and the date that source was read, and anyone can check a cell against the document behind it — but it is not *shown to be reproducible*. Whether a second coder working from the same rules would produce the same matrix is untested, and no reliability coefficient is claimed for the classification.

An expert survey collects practitioner judgment on the boundary rules and includes an optional blind scoring exercise. That is external feedback on whether the rules are sensible and applicable. It is not a second coder and does not close this gap.

### Coding tranches

The remaining classification work is split by **how the evidence is obtained**, using the existing grouping:

| Tranche | Codes | Why grouped | Status |
|---|---|---|---|
| **A** | gas, stake, scarcity, burn, protocol | Fact check against protocol documentation | 68 of 70 verified, 2 pending |
| **B** | collateral, monetary | Need a 90-day quantitative window and a materiality threshold | 28 decisions outstanding |
| **C** | governance, utility, incentive | Boundary calls, the most judgment-dependent | 26 sourced, 16 pending after source review |

Tranche C was advanced while awaiting survey responses at the researcher’s request. Its September 14 snapshot applies the existing rules; it does not change historical experiment inputs. The 16 unresolved cells carry specific evidence gaps in the workbook.

The five previously untouched assets (HYPE, XMR, TON, TAO and POL) now have a first pass across all 50 cells: 28 supported values and 22 explicit gaps. See the [source-review results](research/findings/2026-09-14-five-asset-classification.md).

### The pipeline

72 modules in seven ordered stages. A test fails if any module is missing from the stage map.

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
python -m unittest discover -s tests                           # 312 tests
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

Not defensible, and stated as such: any claim that economic function predicts returns; any market-wide claim about function and risk while most of the universe is unverified; and any claim that the classification is reproducible by an independent coder, which has not been tested.

### What happens next

1. **Send the survey, with a closing date.** It collects external feedback on the six boundary rules and the materiality thresholds. The analysis plan is frozen at `config/survey_analysis_plan.json` before any response is read.
2. **Resolve the remaining source gaps**: two pending cells in tranche A, sixteen in tranche C and twenty-two across the five additional assets. If the evidence does not settle a cell, it stays pending — insufficient evidence is a result, not a failure.
3. **Summarise the responses**: agreement with each proposed rule, the function ranking, and the reasons given for disagreement. The optional blind scoring exercise is reported only if enough people complete it.
4. **Revise and document the framework**: which rules stayed, which changed, which remain uncertain. A rule the panel did not settle continues as a working convention and is labelled as one.

The thresholds the survey settles determine how tranche B is coded. Tranche C already has a source-review pass; its unresolved evidence and rule questions remain explicit.

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
- `docs/` (Git-ignored) — private working notebook and the phase summary, including the full asset matrix.

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
| [`research/survey_instrument.md`](research/survey_instrument.md) | The expert survey: external feedback on the boundary rules |

---

*Classifications are research codes, not legal conclusions. Every result is an association, not a causal or investment claim.*

## Command reference

Every module runs as `python -m src.pipeline.<module> --repo .`, and
`config/pipeline_stages.json` records the exact arguments used for the frozen snapshots — it is the
authoritative list, not this file. `python -m src.pipeline.run_stages --repo . --list` prints the
stages and their commands in order. What each module reads and writes is in
[`DATA_MAP.md`](DATA_MAP.md), which the pipeline generates, so it cannot drift from the code.

Commands that reach the network are all in the `ingestion` stage and need keys in `.env`
(copy `.env.example`). Every other stage rebuilds from archived raw snapshots and needs no
credentials.

---

This repository is for academic research. Classifications are not legal conclusions or investment
recommendations.

The [September 14 expansion input build](research/findings/2026-09-14-expansion-input-build.md) closes the four fee decisions and archives the first activity histories for tranche B. No monetary or collateral codes are assigned by that build.

The [collateral collection follow-up](research/findings/2026-09-14-collateral-collection.md) adds balance candidates for nine assets, current Venus eligibility, and separate Avalanche activity series. Historical eligibility remains unresolved; matrix counts are unchanged.
