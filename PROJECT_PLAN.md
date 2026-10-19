# Project plan

Current research state and next gates. Updated 19 October 2026.

## Objective

Build a reproducible economic classification of cryptocurrencies for advisory and valuation, then test whether those functions contain information about value, usage, supply events, staking, and risk.

The product available today is an economic due-diligence framework. It is not yet a price-target model, portfolio allocator, or trading system.

## Current checkpoint

| Workstream | Current state | What it means |
|---|---|---|
| Classification | Complete: 23 assets × 10 functions = 230 evidence-backed decisions | The matrix is ready for research and advisory comparison |
| Independent review | 10 cells reviewed; 220 cells single-coded | The full matrix is auditable but independent reproducibility is untested |
| Architecture test | Complete: 253 asset pairs | Architecture is informative but does not replace economic classification |
| H1 usage | One-year retrospective robustness complete | Positive and suggestive, but XLM-sensitive and not independent validation |
| H2 fee and capture | Estimated | Broad result is suggestive; strict holder-capture result is not supported |
| H3 supply events | 17 events across ARB, BNB, and UNI | Predicted direction is not supported; power remains low |
| H4 staking | Design frozen; BNB and controls ready | Estimation remains blocked by missing historical ETH active stake |
| H8 valuation groups | Verified-universe extension complete | Financial integration modestly outpredicts raw function breadth; later validation is required |
| Risk test | Verified-input refresh complete | No function-risk result survives false-discovery correction |
| Market and valuation dashboard | First reproducible version complete | Technical state covers 22 assets, common-window risk covers 19, and function-relevant valuation coverage is explicitly reported |
| Stablecoins | Preserved and deferred | Not part of the active cryptocurrency phase |

## Findings that can be stated plainly

1. **Architecture helps, but is incomplete.** Same-architecture pairs share 51.7% of their functions on average, versus 33.1% across architectures. Some differently built assets remain near-identical economically.
2. **Which functions an asset performs is more useful than how many it performs.** Financial integration lowers leave-one-asset-out valuation error by 2.8% relative to raw function count. This is exploratory.
3. **Usage is not value capture.** The fee-and-capture result depends on whether treasury control counts as capture. Under the stricter holder-directed rule, the relationship is not supported.
4. **Supply events are not standalone signals.** Eight of 17 events move in the predicted direction and every asset-level average opposes H3.
5. **The classification is usable before the valuation model is complete.** It can structure due diligence, economic-peer selection, and narrative review without producing an investment recommendation.

## Phase status

### Phase 0 — Data foundation: complete

Raw source responses are archived with metadata and checksums. Processed outputs rebuild from those snapshots. Network collectors and offline transformations are separated.

### Phase 1 — Economic classification: complete, with external-validation limitation

All 230 active-universe cells are resolved from dated evidence. DOGE and XMR remain in the audit trail but are excluded from estimation. Ten cells have an earlier blind review; the remaining 220 are single-coded.

The unresolved issue is not coverage. It is whether outside experts accept and can consistently apply the boundary rules, especially:

- material monetary use;
- collateral materiality;
- protocol-required gas versus economically normal fees;
- governance versus holder capture;
- issuance-funded rewards versus value capture.

The expert survey tests those rules. It does not retroactively become an independent second coding of the matrix.

### Phase 2 — Valuation and mechanism tests: active

- H1, H2, H3, and H8 have exploratory estimates.
- H4 has a frozen design but cannot be estimated without ETH archive history.
- No model may be retuned because a result is weak.
- H8 temporal validation remains fixed at 23 August 2026–22 August 2027 and cannot be estimated early.

### Phase 3 — Risk and market structure: frozen for later validation

The verified-input refresh finds no result surviving 10% false-discovery control. The next valid step is a genuinely later, non-overlapping outcome window using the unchanged design.

### Phase 4 — Stablecoin research: deferred

Existing stablecoin work is preserved but does not gate the active cryptocurrency paper.

## Immediate work programme

### Checkpoint A — communication and external review

- Keep the README, project plan, manuscript, hypothesis catalog, and executive summary consistent.
- Use the professor/team review package to present the work in plain language.
- Field the frozen expert survey and record rule-level agreement, disagreement, and comments.
- Report survey feedback as external rule validation, not as full-matrix inter-rater reliability.

### Checkpoint A2 — dashboard: secondary output, further implementation deferred

- Maintain common market-risk measures for every asset with adequate data.
- Select valuation metrics from verified economic functions instead of applying one universal multiple.
- Compare assets with economic peers rather than architecture labels alone.
- Report measured, data-unavailable, and not-applicable fields separately.
- Use technical indicators as market-state context, never as intrinsic value or automatic trading signals.
- Produce no composite investment score, price target, ranking, or recommendation.

### Checkpoint V1 — relative valuation models: active, first build complete

- RV1 specification was committed before estimation; historical outcomes were previously examined, so this is an exploratory modelling extension.
- Compare all-group ridge regression with mean-only and raw-count benchmarks on the same 22-asset sample.
- Compare fees, volume and scope with and without holder capture on the same 11-asset sample.
- Hold every target asset out of its fit and scaler; calculate empirical error bands using only the remaining assets.
- Report model drivers, asset residuals, failures and scope-matched peer multiples. Static classifications are retrospective descriptors.
- Current findings: groups reduce error by 19.1% versus raw count; the capture addition worsens fundamentals error by 7.8%; BTC's identity-model residual exposes substantial unexplained asset-specific value.
- Next: review asset-level failures and improve fundamental measurement under a separately frozen extension. Preserve all current model comparisons.

### Checkpoint CA1 — benchmark comparison and advisory synthesis: first build complete

- Archived free adjusted-price histories for GLD, SPY and IWM with retrieval metadata and checksums.
- Fixed crypto basket has 21 eligible assets; HYPE lacks history and TON fails 90% calendar coverage. Report every exclusion.
- Primary weekly-return correlations use 52 matched periods, paired four-week block-bootstrap intervals and chronological-half checks.
- Daily, shifted-close, BTC/ETH, ex-BTC/ETH, function-group, rolling and equity-down views expose sensitivity. No price-level correlations or artificial holiday returns.
- One editable report and self-contained HTML combine classification, hypothesis tests, RV1, market context and benchmark results.
- Presentation limitations: only one year, asynchronous closes, USDT/USD basis, retrospective membership and no independent second-vendor price verification. A Goldman Sachs advisory presentation is the intended discussion audience, not an endorsement or quality certification.

### Checkpoint B — improve existing empirical tests without outcome selection

- Preserve the three-asset H3 sample after the evidence-only OP/SUI/AVAX screen found no qualifying fourth asset; add one only if an official source establishes an exact event date and the unchanged 0.5% materiality rule is met.
- Preserve the current null H3 result even if the additional asset changes it.
- Preserve the nine-network H1 model for a genuinely later validation window.

### Checkpoint C — unblock H4

- Configure an archive-capable Ethereum consensus endpoint.
- Collect active effective balance over the frozen common window.
- Run the locked ETH/BNB plus BTC/UNI/ARB panel only after the readiness gate passes.
- Keep legacy stkAAVE separate from consensus staking.

### Checkpoint D — later validation

- Run H8 only after its fixed validation window ends on 22 August 2027 and coverage passes the predeclared threshold.
- Repeat the risk model on a later non-overlapping window.
- Do not change selected functions, groups, outcomes, or thresholds in response to discovery-sample results.

## Decisions that require the researcher

| Decision | Why it matters | Needed now? |
|---|---|---|
| Approve or obtain an archive-capable ETH consensus provider | Required for H4 | Yes, only if H4 should proceed now |
| Choose professor/industry survey recipients | Required for external rule feedback | Yes, before fielding |
| Approve any future fourth H3 asset after source review | Protects against outcome-selected event inclusion; the OP/SUI/AVAX screen produced no qualifier | After a qualifying candidate is documented |

No other classification decision is currently open.

## Canonical outputs

| Need | File |
|---|---|
| Plain-language conclusion | `research/findings/crypto-executive-decision-summary.md` |
| Asset-level advisory profiles | `research/findings/crypto-advisory-profiles.md` |
| Market and valuation dashboard | `research/findings/crypto-market-valuation-dashboard.md` |
| Active relative valuation models and findings | `research/findings/crypto-relative-valuation.md` |
| Consolidated advisory report | `research/findings/crypto-advisory-report.md` and `.html` |
| Architecture result | `research/findings/crypto-architecture-economic-similarity.md` |
| Exact hypothesis designs and status | `research/methods/crypto_hypothesis_test_catalog.md` |
| Human decisions and blockers | `research/open_decisions.md` |
| Manuscript | `research/manuscript/main.tex` |
| Processed-data inventory | `DATA_MAP.md` |

## Rebuild and verify

```bash
python -m src.pipeline.run_stages --repo . --list
python -m src.pipeline.run_stages --repo . --offline
python -m unittest discover -s tests                 # 388 tests
git status --short                                   # empty after a committed rebuild
```

The pipeline contains 97 registered commands in seven ordered stages. A test fails when a pipeline module is not registered.
