# Open decisions register

15 October 2026. This register contains only decisions that remain open. Historical classification questions that have already been adjudicated remain in dated findings and evidence records.

## D1. Ethereum archival consensus source — blocks H4

**25 October update:** The primary estimator and small historical-access checker are implemented and tested. Market/price inputs support 361 common analysis dates; BNB stake is complete at 362/362, ETH remains 0/362 and no local archive endpoint is configured. PublicNode returned 403, a ChainSafe checkpoint route returned 404, and Beaconcha.in requested an API key. None supplies the required dataset under current access. See `findings/2026-10-25-h4-access-and-execution-checkpoint.md`. Verify endpoint history and download limits before full collection.

**Need:** An endpoint that serves historical Beacon validator states over the frozen common window.

**Why:** H4 measures active effective balance. Validator count multiplied by 32 ETH is rejected because post-Pectra validators may have larger effective balances.

**Current state:** BNB consensus stake and all market controls are complete. Legacy stkAAVE is complete as a separate non-consensus case study. ETH is 0/362 in the common analysis window.

**Who decides:** Principal researcher, because an archive-capable provider may require payment or account setup.

**Constraint:** Do not estimate H4 and do not substitute a weaker measure before this is resolved.

## D2. External rule-validation sample — required for survey fielding

**Need:** Select professor and industry-professional recipients for the frozen survey.

**Why:** The matrix is complete but 220 of 230 cells are single-coded. External feedback can test whether experts accept the boundary rules and materiality conventions.

**What the survey can establish:** Agreement or disagreement with rules for monetary use, collateral materiality, gas, incentives, and holder capture.

**What it cannot establish:** Full-matrix inter-rater reliability, unless external reviewers independently code a representative blind sample.

**Who decides:** Principal researcher.

## D3. Fourth H3 event asset — approval after evidence review

**Need:** A candidate from the existing universe with an official exact-date supply increase or burn that meets the unchanged 0.5% materiality rule.

**Why:** H3 currently has 17 events but only three independent asset units, giving low-powered asset-level inference.

**Evidence-only screen completed 15 October 2026:** OP failed the unchanged 0.5% materiality threshold; SUI lacked an official exact event date and amount; AVAX uses a continuous burn rather than a discrete event. No return or price outcome was examined. No candidate was added.

**Selection rule:** Establish event eligibility without examining its return. Record the candidate, source, date, direction, and materiality before adding market outcomes.

**Who decides:** Principal researcher or advisor after the evidence-only candidate note is complete.

## D4. Publication emphasis — advisor discussion

Three defensible contributions now exist:

1. the ten-function classification instrument and asset profiles;
2. the result that architecture is informative but incomplete;
3. the governed-treasury versus holder-capture boundary and its empirical consequence.

**Need:** Decide which contribution leads the paper after professor feedback. The underlying results and specifications do not change with the framing.

## Resolved boundaries that remain binding

- Governance over ecosystem spending is not holder capture unless value mechanically reaches the token or holder.
- Issuance-funded staking rewards are security compensation, not protocol capture.
- Sequestration is not token destruction.
- Legacy stkAAVE is a separate protocol-risk-stake case and is not pooled with consensus staking.
- DOGE and XMR remain outside the active estimation universe, with their audit trail preserved.

## Summary

| Open decision | Blocks |
|---|---|
| D1 ETH archive provider | H4 estimation |
| D2 survey recipients | External rule validation |
| D3 future fourth H3 asset | Higher-powered H3 inference; current OP/SUI/AVAX screen found no qualifier |
| D4 publication emphasis | Manuscript positioning, not empirical work |

No classification cell is pending or provisional.
