# Digital Assets Valuation

**Current checkpoint (9 October 2026).** The classification instrument is complete for the active universe: 23 assets x 10 functions = 230 evidence-backed decisions, with no pending or provisional cells. DOGE and XMR are retained in the audit trail but excluded from estimation. H1, H2, H3 and H8 have exploratory estimates. H3 now includes ARB unlocks and BNB burns; H4 has complete 365-day BNB consensus-stake and legacy stkAAVE histories, but pooled estimation still requires archival ETH consensus data.

The clearest result so far is H8: theory-defined function groups contain more valuation information than a raw count of functions in this sample. Financial integration is the strongest single group and modestly lowers leave-one-asset-out prediction error. This is exploratory and non-causal, not an investment rule. See [`research/findings/crypto-current-findings.md`](research/findings/crypto-current-findings.md) and the [visual analysis](research/findings/crypto-visual-analysis.md).

**Can the economic jobs a cryptoasset performs explain what it is worth and how risky it is?**

This repository builds a reproducible way to answer that. It classifies cryptoassets by economic function rather than by technology or marketing label, proves every classification from dated primary sources, and tests whether those functions explain valuation and risk. Independent research developed at NYU Tandon (MS Financial Engineering), intended for publication.

Everything here is rebuildable. One command regenerates every processed artifact from archived raw snapshots, and 352 tests check the code that does it.

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

These become five active hypotheses. Each empirical design is frozen before its estimate is produced, so the test cannot be changed after seeing the answer.

| ID | Hypothesis | Status |
|---|---|---|
| H1 | Usage is associated with higher network value | Estimated; positive, not significant (p = 0.250) |
| H2 | Usage matters more when value capture is live | Estimated; **definition-dependent** (broad p = 0.082; strict p = 0.478) |
| H3 | Greater circulating-supply growth predicts weaker returns | 16 events across ARB and BNB; not supported, very low power |
| H4 | Staking reduces liquid float and affects liquidity or risk | BNB and legacy stkAAVE histories complete; ETH archive blocks pooled test |
| H8 | Theory groups outperform a raw count of functions | 23-asset extension favors groups; exploratory |

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

23 active non-stable cryptoassets, selected on market capitalisation, volume, economic relevance and reproducible free-data access. DOGE and XMR are excluded from the active analysis. Stablecoin work is preserved for a later phase.

| Dataset | Coverage | Used for |
|---|---|---|
| Daily OHLCV | 24 assets, 2019-01-02 to 2026-08-22, 52,116 asset-days | Return panel, factor baseline, risk measures |
| Chain and protocol fees | 11 economic systems, 362 days | The usage variable in H2 |
| Network activity | 4–5 assets on free provider tiers | H1, H3 |
| Collateral balances | Daily protocol state reads, 90-day windows | `VA_COLLATERAL` evidence |
| Staking series | BNB consensus stake and legacy stkAAVE, 365 days each; ETH 0/365 | H4 measurement audit |
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

### Classification completion and review boundary

The source-review tranches are complete. The canonical status is **220 sourced cells + 10 sourced and independently blind-reviewed cells = 230 evidence-backed cells**. No cell is pending or provisional. The earlier blind review covers only burn and protocol-capture decisions for ADA, AVAX, SOL, TRX and XRP; its kappa of 1.00 must not be generalized to the whole matrix.

The remaining classification limitation is external reproducibility, not coverage. An expert survey may test whether practitioners accept the boundary rules and materiality conventions, but downstream exploratory work does not silently treat that survey as completed.

### The pipeline

83 commands in seven ordered stages. A test fails if any pipeline module is missing from the stage map.

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
python -m unittest discover -s tests                           # 352 tests
git status --short                                             # should be empty after a rebuild
```

An empty `git status` after a rebuild means the committed artifacts are exactly what the code produces. The rebuild is deterministic; repeat runs are byte-identical.

### Statistical approach

With six to twenty assets, large-sample approximations do not apply. So the design stops approximating and starts counting. Instead of trusting a t-distribution, we enumerate the possibilities: all 2,048 Rademacher sign assignments for the eleven-cluster wild bootstrap, all 720 permutations for a six-asset cross-section. The p-values are exact and reproducible to the digit. The cost is honest — with six assets and a 3-3 binary split, the smallest attainable p-value is 0.10, so that sample cannot reject at 5% however strong the effect.

Full walkthrough in [`research/findings/2026-09-07-the-math-explained.md`](research/findings/2026-09-07-the-math-explained.md).

## 6. Where the project stands

**The classification instrument is complete; the empirical evidence is exploratory and mixed.**

- **Architecture does not predict economics.** Two PoS base layers in the verified core differ on two of ten functions; two application tokens share one.
- **The central capture result is definition-dependent.** Fee activity is more strongly associated with market value when a capture route is live: pooled interaction 0.132, exact p = 0.082, positive in all eleven leave-one-out samples. Apply the strict holder-capture rule and it halves to 0.061 with p = 0.478. **Whether a governed treasury counts as capture is the difference between a result and no result.**
- **Which functions are present is more informative than how many.** In the verified 23-asset H8 extension, raw breadth has leave-one-asset-out RMSE 1.8109; the best single group, financial integration, improves it modestly to 1.7594. Monetary/store, supply absorption and financial integration survive 10% false-discovery control in this sample.
- **The H3 event evidence does not support the predicted supply-shock direction.** Across 12 material ARB unlocks and four BNB burns, both asset-level mean direction-adjusted returns oppose H3. Eight of 16 events match their predicted sign; the exact asset-level sign-flip p-value is 0.50. With only two independent assets, this is valid but extremely low-powered evidence.
- **H4 measurement is partly complete.** BNB has 365/365 days of native consensus stake; legacy stkAAVE has 365/365 days as a separate case study. ETH has 0/365 because a historical consensus endpoint is not configured, so pooled estimation is blocked.
- **Mechanism activations are not visibly priced.** Three events, 22 controls, ~280 calendar placebos each. One carries its expected sign; none rejects at 10%.
- **A single market factor dominates.** Median beta 1.03, median R² 0.60 across 24 assets. Lagged beta is negatively priced (t = −2.12).
- **Verified function and risk associations do not survive correction.** Re-estimating the unchanged frozen design with the completed matrix leaves 19 assets meeting the original history rule. Monetary/store membership has the strongest drawdown association (coefficient 1.071, permutation p = 0.0128), but only one of 27 tests reaches p ≤ 0.05 against 1.35 expected by chance, and none survives a 10% false-discovery rate.

Not defensible, and stated as such: any claim that economic function causes valuation or predicts returns out of sample; any confirmatory interpretation of H8 before its fixed validation window closes; and any claim that the classification is reproducible by an independent coder, which has not been tested.

### What happens next

1. **Unblock H4 measurement.** Configure `ETH_BEACON_ARCHIVE_API_URL` with a provider that serves historical beacon states, then collect 365 days of active effective balance and run the frozen H4 analysis.
2. **Broaden H3 without outcome selection.** The two-asset gate is now passed with ARB and BNB. Add independently sourced assets to improve power while preserving the current definitions, materiality rule, event window, and asset-level randomization.
3. **Accumulate the frozen H8 validation window.** The design is now fixed at 23 August 2026–22 August 2027, with financial integration compared against raw breadth using the same leave-one-asset-out RMSE. The readiness audit prevents estimation before the window closes and requires at least 292 daily observations per asset.
4. **Treat the verified risk refresh as exploratory.** The classification-only refresh is complete; preserve its null false-discovery-controlled result and seek a genuinely later risk window before calling it validation.
5. **Collect external rule feedback.** Use the frozen survey analysis plan to document agreement and disagreement with the classification boundaries. This strengthens interpretation but is not represented as independent recoding.

Every decision that needs human judgment is registered in [`research/open_decisions.md`](research/open_decisions.md), with what changes if it flips and which result it blocks.

## 7. Repository layout

The project runs in phases. **Phase 1 classification is complete for the active universe; Phase 2 hypothesis testing is now the active build.** See [`PROJECT_PLAN.md`](PROJECT_PLAN.md) for the phase breakdown and gates.

Processed data is grouped by the phase that owns it, so you can tell from the path which question a file belongs to:

```
data/
  raw/                              immutable dated snapshots, by source, never edited
  processed/
    00_foundation/                  shared market, price and activity series
    01_classification/              Phase 1 evidence, mechanism states, taxonomy
    02_valuation/        ← active   H1 H2 H3 H8 and the event studies
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
| [`research/findings/2026-10-09-verified-function-risk-refresh.md`](research/findings/2026-10-09-verified-function-risk-refresh.md) | Verified classification-to-risk refresh |
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
