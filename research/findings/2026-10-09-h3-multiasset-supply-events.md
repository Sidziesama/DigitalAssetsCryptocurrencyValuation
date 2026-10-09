# H3 multiasset supply-event checkpoint

The frozen H3 event design now includes two independently sourced mechanisms: twelve material ARB monthly unlocks and four material BNB quarterly burns. BNB was selected because official BNB Foundation records provide exact completion dates, quantities, and transaction links—not because of observed returns.

## Result

- Eligible events: 16.
- Assets: ARB and BNB.
- Events matching their predicted sign: 8 of 16.
- ARB mean direction-adjusted three-day abnormal log return: -0.0155.
- BNB mean direction-adjusted three-day abnormal log return: -0.0017.
- Pooled mean direction-adjusted three-day abnormal log return: -0.0120.
- Exact two-sided asset-level sign-flip p-value: 0.50 from four assignments.

Positive direction-adjusted returns would support H3: unlock returns are multiplied by -1 because their predicted sign is negative, while burn returns retain their sign because their predicted sign is positive. Both asset-level averages are negative, so both mechanisms move opposite the hypothesis on average.

## Interpretation

H3 is not supported in this sample. The randomization unit is the asset rather than the event, preventing twelve observations from one token from being treated as twelve independent experiments. That choice is statistically conservative and leaves only two independent units, so the test is valid but extremely low-powered. Additional assets should be added only when official exact-date evidence satisfies the unchanged 0.5% materiality rule.
