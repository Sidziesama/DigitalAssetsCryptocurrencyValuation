# Open decisions register

7 September 2026. Every decision in this project that requires human judgment rather than code. Each entry states what is at stake, what would change if the decision went the other way, and who can settle it. Items marked **BLOCKING** prevent a specific result from being reported.

Decisions are grouped by the kind of judgment they need, because that determines who should be asked. Classification-rule decisions suit a panel of researchers and practitioners. Research-design decisions suit an advisor. Resource decisions need the principal investigator.

---

## A. Classification rules

These define the measuring instrument. They should be settled by people who know both the protocols and the valuation literature, and settled *once*, so the rule generalises to assets not yet classified.

### A1. Relay policy versus consensus rule for VA_GAS — **BLOCKING, 4 cells**
On UTXO proof-of-work chains a zero-fee transaction is consensus-valid; fee minimums are node relay policy. The verified Bitcoin decision therefore scores `VA_GAS = 0`. Bitcoin Cash, Litecoin, Dogecoin and Zcash share that property.

*Options.* (i) Apply the precedent, all five score 0. (ii) Revise the rule to admit economically required fees, in which case all five score 1 and the Bitcoin decision must be re-reviewed.

*What changes.* Four of the twenty assets in the risk test move on the transaction-service-demand bundle, which is one of the two bundles that produced sub-0.05 associations. Option (ii) also changes the verified core.

*Do not split them.* Scoring the forks differently from Bitcoin is the one outcome that is indefensible.

### A2. Governed-treasury capture boundary — settled, seeking external validation
Adjudicated: governance authority over a treasury is not value capture unless value mechanically terminates at the token through burn, buyback, distribution, or an enforceable claim. Applied to ARB, ADA and Zcash's development fund.

*What changes.* This is the single most consequential rule in the project. Under the broad definition the headline H2 interaction is 0.132 with $p = 0.082$; under the strict definition it is 0.061 with $p = 0.478$. External agreement on the rule is worth more than any additional estimate.

### A3. Chainlink Reserve and Smart Value Recapture — **BLOCKING, 1 cell**
Staking rewards are currently emissions-funded, which is service compensation and does not qualify. The official economics page also describes a Reserve and a mechanism called Smart Value Recapture whose disposition could not be established from primary sources.

*Needed.* Primary documentation of where Reserve value goes. If it terminates at LINK, `VA_PROTOCOL = 1`.

### A4. Optimism buyback status — **BLOCKING, 2 cells**
Governance approved routing a share of Superchain revenue to OP buybacks and execution was observed for at least two months, but the official thread does not confirm the mechanism is currently live. A paused mechanism scores zero only after review, never by default.

### A5. What counts as material monetary use — **BLOCKING for the risk test**
The rule requires two behavioral tests plus dated primary evidence of monetary or payment design. The provisional matrix codes fourteen of twenty assets as monetary, including LTC, BCH, XLM, ZEC and DOGE. That generosity is the main reason the twenty-asset risk result cannot be treated as evidence.

*Needed.* A defensible materiality threshold. The monetary-store bundle is the strongest single predictor in every cross-sectional test, so this rule effectively determines that result.

### A6. Collateral materiality threshold
Currently: collateral balances of at least one percent of market capitalization, or one hundred million dollars, sustained for ninety days. Both numbers are defensible and arbitrary.

*What changes.* Financial integration is the third-strongest bundle in the risk sorts.

### A7. Sequestration versus destruction — settled, low controversy
Stellar's fees enter a locked account and are "not given to or used by anyone". Scored as not a burn, because supply is not reduced. Worth confirming as a general rule for any chain that escrows rather than destroys.

### A8. Issuance-funded rewards are service compensation — settled
Staking and mining rewards paid from new issuance do not constitute value capture. This is what distinguishes Cardano from Ethereum in the classification and it follows from the same logic as A2.

### A9. The bundle map
Eight bundles were defined from theory before estimation. Seven contain a single function, so bundle count and raw breadth correlate at 0.956 and the bundle-versus-breadth test cannot discriminate.

*Options.* (i) Keep the map and report that the test is uninformative at this granularity. (ii) Regroup on theoretical grounds into fewer, larger bundles, freeze the new map, and re-run. Any regrouping must be justified before seeing outcomes.

---

## B. Research design

### B1. Should the strict capture rule become the primary H2 specification?
Currently the frozen pilot uses the broad definition and the strict rule is reported as a sensitivity. If A2 is externally validated, the strict result arguably becomes the headline and the broad one the sensitivity.

*Constraint.* Whichever is primary must be declared before the next estimation, not after comparing them.

### B2. Publication framing
The strongest paper available now is a methods and measurement contribution with pre-registered nulls. The alternative is to wait for the full classification and attempt a results paper.

*Trade-off.* The methods paper is publishable now and the instrument is the novel contribution. The results paper needs at least the twenty-asset classification finished and may still produce nulls.

### B3. Valuation multiple denominator
The bundle comparison uses market capitalization over daily fees. Market capitalization over activity was withheld because free activity data covers only four of six core assets. Adding a paid activity source would enable it.

### B4. Universe extension
Twenty-five assets, of which twenty meet the common-window coverage rule. Extending would improve power but requires the same evidence standard per asset, at roughly ten decisions each.

### B5. Second coder identity and blinding protocol
The reported kappa of 1.00 rests on ten decisions reviewed inside the project. An external reviewer scoring a substantial blind sample converts the review protocol from a described method into a reported reliability statistic. This is the cheapest available upgrade to the paper's methods section.

---

## C. Resources

### C1. Archival Ethereum consensus endpoint — **BLOCKING, all of H4**
The exact effective-balance collector is implemented and correctly rejects the post-EIP-7251 validator-count shortcut, but public beacon endpoints reject historical validator state. An archive-tier provider is required. Small recurring cost; only the principal investigator can approve it.

### C2. Aave staking boundary — **RESOLVED**
Legacy stkAAVE now has a complete 365-day series and remains a separate protocol-risk-stake case study. Umbrella stakes aTokens and GHO rather than AAVE, so it is correctly excluded from the AAVE-token staking series and cannot substitute for consensus stake.

### C3. Point-in-time unlock and issuance events — **PARTIALLY RESOLVED, still blocking pooled H3**
Twelve exact-date material ARB unlocks are estimated descriptively. A second qualifying asset is still required before pooled inference.

### C4. Independent reproducibility
All 230 active-universe cells are evidence-backed, but only 10 have an independent blind review. This is reported as a limitation rather than an unfinished coverage task.

---

## Summary of what is blocked on what

| Blocked result | Blocking decisions |
|---|---|
| Re-estimating P1_H6 on verified codes | **Resolved 2026-10-09**; verified-input refresh complete |
| Reporting a confirmatory market-wide function-and-risk claim | A genuinely later, non-overlapping outcome window; C4 remains a classification limitation |
| H4 pooled estimation | C1 |
| H3 identification | C3 |
| Classification coverage | **Resolved**; 230/230 active-universe cells evidence-backed |
| Choosing the primary H2 specification | A2, then B1 |
