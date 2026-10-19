# Research documentation

This directory is the human-readable layer of the project. It is deliberately tracked in Git so that the manuscript, the findings, and the open decisions can be checked against the code and data that produced them.

## Contents

| Path | What it is |
|---|---|
| `manuscript/main.tex`, `main.pdf` | The paper. Every figure in it is regenerable from the pipeline. |
| `manuscript/references.bib` | Bibliography: methodological, crypto-finance, and the protocol sources behind classifications. |
| `open_decisions.md` | Register of every decision that requires human judgment, with what changes if it flips. |
| `findings/` | Dated analysis notes and generated current-results summaries. |
| `methods/` | Data-pipeline documentation and the generated active-hypothesis test catalog. |
| `preregistration/` | Preregistration drafts and input manifests with file hashes. |

## Where to start

Start with `findings/crypto-executive-decision-summary.md`: it states what was done, the insight, and the defensible action in plain language. For a meeting, use `meeting/professor_review_checkpoint_2026-10-15.md`. Then use `findings/crypto-advisory-profiles.md` for all 23 asset profiles, `findings/crypto-market-valuation-dashboard.md` for classification-informed market and valuation context, and `findings/crypto-architecture-economic-similarity.md` for the direct test of whether architecture is an adequate economic grouping. For the exact data, equation, matrix role, inference and current result of every active hypothesis, read `methods/crypto_hypothesis_test_catalog.md`; then read the manuscript.

## How to verify a claim

Every number in the manuscript comes from a file in `data/processed/`. To check one:

```bash
python -m src.pipeline.run_stages --repo . --offline   # rebuild all processed artifacts
python -m unittest discover -s tests                   # 376 tests
git status --short                                     # should be empty
```

An empty `git status` after a rebuild means the committed artifacts are exactly what the code produces from the archived raw snapshots. The rebuild is deterministic; repeat runs are byte-identical.

Experiment specifications live in `config/`, with freeze dates recorded before estimation. Classification outputs are in `data/processed/01_classification/`, valuation outputs in `data/processed/02_valuation/`, and risk outputs in `data/processed/03_risk/`. `DATA_MAP.md` records every producer and consumer.

## What is not here

`docs/` holds the working notebook and meeting notes and is not tracked. `review_inputs/` holds completed reviewer worksheets and is not tracked, so that regenerating a blank template can never overwrite a reviewer's work. Credentials live in a local `.env` that is not tracked; `.env.example` lists the variable names.
