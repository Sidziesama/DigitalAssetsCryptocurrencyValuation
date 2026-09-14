# Working context

Read this before changing anything. It is the operating manual: what the project is for, the rules that must not be broken, how to extend it, and the traps that have already cost us once.

For *what the project is*, read [`README.md`](README.md). For *where it is going*, read [`PROJECT_PLAN.md`](PROJECT_PLAN.md). This file is about *how to work on it*.

---

## 1. The goal

Cryptoassets are sorted by technology or by marketing label, and neither tells you how the asset is supposed to accrue value. This project builds a reproducible classification of cryptoassets by **economic function** — what job the token actually performs, proved from dated primary sources — and tests whether that classification explains valuation and risk.

Two things are being produced. **An instrument**: a classification anyone can reproduce and check, with a published reliability statistic. **A set of honest tests** of whether economic function explains anything, reported whether or not they work.

The intended output is a publishable paper. The instrument is the contribution; the empirical results so far are mostly null, and that is reported as the finding rather than buried.

**Active phase: Phase 1, economic classification.** Phases 2 and 3 have exploratory results but are on hold behind Phase 1's gates. Phase 4 (stablecoins) is deferred.

---

## 2. The rules that must not be broken

These are the project's credibility. Code enforces most of them; you enforce the rest.

1. **Freeze before you look.** Every experiment has a specification file in `config/` with a `freeze_date`, committed *before* its estimate exists. Never write a spec after seeing the result it describes.
2. **Never backfill.** What we know today cannot explain yesterday's prices. Classifications are effective-dated and the panel resolves the state prevailing on each observation day.
3. **Unknown is not zero.** Missing evidence stays null. A zero means someone reviewed it and the criterion was not met. Pending cells render blank in every output for this reason.
4. **Correct for looking many times.** 27 tests get 27-test treatment. Multiple-testing correction is declared in the spec, not decided after seeing p-values.
5. **Report the weaker version.** Where two defensible specifications disagree, publish both side by side. The H2 strict-rule sensitivity exists because of this rule.
6. **Never choose what to measure based on what showed a result.** Coding tranches are ordered by evidence difficulty, fixed in advance. If someone suggests verifying the monetary codes first *because that is where the signal is*, decline and say why.
7. **A rule adjudicated once binds every future case.** The governed-treasury boundary settled ARB and ADA together, and now settles Zcash's development fund the same way.
8. **Survey before re-estimation.** The expert panel must be fielded and closed before any re-estimate. Several answers change classifications that determine the strongest association; collecting them afterwards would invalidate the result.

---

## 3. How the repository is laid out

```
config/                    frozen specs — one JSON per experiment, plus the registry,
                           codebook, evidence tranches and the effective-dated ledger
data/raw/                  immutable dated snapshots, by source. NEVER edit in place.
data/processed/
  00_foundation/           shared market, price and activity series
  01_classification/  ←    Phase 1 evidence, mechanism states, taxonomy
  02_valuation/            H1 H2 H3 H8 and the event studies
  03_risk/                 return panel, factor baseline, P1_H6
  04_stablecoin_deferred/  parked
data/reference/            the generated universe workbook
src/pipeline/              one module per command; run_stages.py runs them in order
tests/                     one test file per module, plus structural tests
research/                  manuscript, findings, open decisions, survey
```

Every processed file is catalogued in [`DATA_MAP.md`](DATA_MAP.md) with its producer and consumers. That file is generated — do not edit it.

---

## 4. The working loop

```bash
source .venv/bin/activate
python -m src.pipeline.run_stages --repo . --list          # the seven stages
python -m src.pipeline.run_stages --repo . --offline       # rebuild everything
python -m unittest discover -s tests                       # 248 tests
git status --short                                         # MUST be empty after a rebuild
```

**An empty `git status` after a rebuild is the contract.** It means the committed artifacts are exactly what the code produces from archived raw data. If a rebuild dirties the tree, something is nondeterministic or stale — fix it before committing.

Two stages are slow: `crypto_h2` runs exhaustive bootstraps (~2 min), and `crypto_returns` builds a 52,000-row panel. Run them individually rather than fighting a timeout.

---

## 5. Adding things

**A new pipeline module.** Write `src/pipeline/<name>.py` exposing `run(repo) -> dict`. Register it in `config/pipeline_stages.json` under the right stage — a test fails if any module is missing from the stage map. Write `tests/test_<name>.py`. Outputs go in the phase folder that owns them.

**A new experiment.** Write `config/<name>.json` first, with `status`, `freeze_date`, the outcomes, predictors, sample, inference method and multiple-testing treatment. Commit it. Then write the estimator. The spec must name everything before the first number exists. Register it in the experiment registry so it appears in the research map.

**A new classification decision.** It needs a dated HTTPS primary source, a rationale, and a status of `verified` or `pending`. Never `verified` with a guessed value. If it touches a boundary that another asset has already faced, apply the existing adjudication rather than deciding afresh.

**Paths.** Always `repo / "data/processed/<phase>/<file>"`. Four different spellings used to coexist here and that inconsistency was most of why the data layer felt unfollowable. Use one.

---

## 6. Traps that have already bitten

**Correcting a classification is not the same as a mechanism changing.** If a protocol genuinely turns a burn on, add a *new* effective-dated event. If we simply scored something wrong and the underlying mechanism never changed, correct the *existing* event in place and keep its original date. Getting this backwards once produced a "fix" dated outside the panel window that silently did nothing — the panel kept resolving the old event, and the numbers were unchanged in a way that looked like the fix had failed to matter.

**The frozen H2 pilot is not to be relabelled.** It was estimated under the older broad treasury definition. The strict rule is applied as a separately versioned sensitivity, on a copy of the panel. Do not edit the frozen spec, its evidence files or its ledger to make the headline move.

**A generated file with no producer is stale.** The data map test fails on orphans. Two such files sat in the repo for weeks before that test existed.

**`cmd | tail` hides the exit code.** A failing pipeline stage looks like a passing one. Check exit status explicitly.

**Artifacts can drift from code.** The stablecoin outputs in git predated later edits to their writers, so a rebuild produced an 18-file diff — the first thing any reviewer would have hit. Rebuild and commit together.

---

## 7. What good work looks like here

Every number in the manuscript is regenerable by one command. Every classification cites a dated source. Every experiment's specification predates its result. Nulls are reported as findings. Where a definition changes a conclusion, both versions are published.

If a result improves because a rule was loosened, that is a finding about the rule, not a result. Say so.

---

## 8. Where to look

| You want | File |
|---|---|
| What the project is | [`README.md`](README.md) |
| Phases, gates, flowcharts | [`PROJECT_PLAN.md`](PROJECT_PLAN.md) |
| Every data file and who writes it | [`DATA_MAP.md`](DATA_MAP.md) *(generated)* |
| The research in plain language | [`research/findings/2026-09-07-research-program-explained.md`](research/findings/2026-09-07-research-program-explained.md) |
| The statistics and why each method | [`research/findings/2026-09-07-the-math-explained.md`](research/findings/2026-09-07-the-math-explained.md) |
| What needs human judgment | [`research/open_decisions.md`](research/open_decisions.md) |
| The survey that unblocks Phase 1 | [`research/survey/README.md`](research/survey/README.md) |
| The paper | [`research/manuscript/main.tex`](research/manuscript/main.tex) |

---

## 9. Current state

As of 14 September 2026: 70 pipeline modules, 248 tests, 151 processed files, 21 commits.

Classification: 250 cells total — **60 verified**, 59 drafted awaiting blind review, 11 held pending adjudication, 120 still provisional.

Phase 1 has four gates and **none passes yet**: rules validated externally, full coverage, an external reliability statistic, and zero open consistency cases. The immediate next step is fielding the expert panel, because its answers set the materiality thresholds that tranche B needs.

Headline results, all exploratory and on hold: the H2 fee-and-capture interaction is 0.132 with exact p = 0.082 under the loose capture definition and 0.061 with p = 0.478 under the strict one; function breadth commands no premium; mechanism activations are not visibly priced; and function-versus-risk gives three of 27 tests at p ≤ 0.05 against 1.35 expected by chance, with none surviving a 10 percent false-discovery rate.

Regenerate this section's numbers with `python -m src.pipeline.run_stages --repo . --stage reporting`.
