# Synthetic data

Nothing here is evidence. Every file is generated from a fixed seed by
`src/pipeline/survey_synthetic_responses.py`, so the panel analysis can be
exercised and its edge cases checked **before any real response is read**.

Scope is declared by the caller, never inferred from a path or filename:

```bash
python -m src.pipeline.survey_panel_analysis --responses <file> --scope synthetic
```

`--scope panel` writes into `data/processed/01_classification/`, requires a
complete `config/survey_recruitment.json`, refuses any file under
`data/synthetic/`, and archives a hashed snapshot of the reference values it
used. `--scope synthetic` writes only here and stamps
`data_source: synthetic_fixture`.

The fixtures reproduce two awkward properties of the real export: six columns
share the header `Why? One line.`, and several items allow a free-text *Other*.

| Scenario | What it exercises |
|---|---|
| `consensus` | a rule adopted at 70 percent or more |
| `leaning` | a unique plurality between 50 and 70 percent — unresolved, not validated |
| `tie` | an exact 50/50 split — divided, never leaning |
| `divided` | no option at 50 percent |
| `depends` | the condition-dependent option winning — adopts no value, cannot satisfy G1 |
| `sparse` | item-level denominators, scorer pairs below minimum overlap, an unscorable prediction |
| `degenerate` | every scorer answering identically — both coefficients undefined, never imputed |
| `duplicates` | the later submission kept by timestamp, and an ambiguous equal-timestamp pair |
| `dirty` | out-of-scale grid values, undeclared blind answers, *Other* answers with commas |
| `prediction_hit` | the frozen prediction satisfied on all four conditions, with tie groups |

Regenerate:

```bash
python -m src.pipeline.survey_synthetic_responses --scenario dirty --n 12
```
