# Research documentation

This directory is the human-readable layer of the project. It is deliberately tracked in Git so that the manuscript, the findings, and the open decisions can be checked against the code and data that produced them.

## Contents

| Path | What it is |
|---|---|
| `manuscript/main.tex`, `main.pdf` | The paper. Every figure in it is regenerable from the pipeline. |
| `manuscript/references.bib` | Bibliography: methodological, crypto-finance, and the protocol sources behind classifications. |
| `open_decisions.md` | Register of every decision that requires human judgment, with what changes if it flips. |
| `findings/` | Dated analysis notes. The three from 2026-09-07 are the current entry points. |
| `methods/` | Data pipeline documentation. |
| `preregistration/` | Preregistration drafts and input manifests with file hashes. |

## Where to start

For the research programme in plain language, read `findings/2026-09-07-research-program-explained.md`. For the statistics and why each technique was chosen over its obvious alternative, read `findings/2026-09-07-the-math-explained.md`. For the most recent results, read `findings/2026-09-07-checkpoint-function-and-risk.md`. Then the manuscript.

## How to verify a claim

Every number in the manuscript comes from a file in `data/processed/`. To check one:

```bash
python -m src.pipeline.run_stages --repo . --offline   # rebuild all processed artifacts
python -m unittest discover -s tests                   # 238 tests
git status --short                                     # should be empty
```

An empty `git status` after a rebuild means the committed artifacts are exactly what the code produces from the archived raw snapshots. The rebuild is deterministic; repeat runs are byte-identical.

Experiment specifications live in `config/`, one JSON per experiment, each with a `freeze_date` recorded before its estimate was produced. Classification outputs are in `data/processed/evidence/` and estimation outputs in `data/processed/empirical/`.

## What is not here

`docs/` holds the working notebook and meeting notes and is not tracked. `review_inputs/` holds completed reviewer worksheets and is not tracked, so that regenerating a blank template can never overwrite a reviewer's work. Credentials live in a local `.env` that is not tracked; `.env.example` lists the variable names.
