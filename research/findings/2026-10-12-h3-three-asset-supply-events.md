# H3 three-asset supply-event checkpoint

The frozen H3 event design now includes three independently evidenced mechanisms: twelve material ARB monthly unlocks, four material BNB quarterly burns, and Uniswap's completed 100 million UNI burn on 27 December 2025. UNI was added because an existing official record supplies both the completed date and quantity, and the event exceeds the unchanged 0.5% materiality threshold. It was not selected from its return.

## Result

- Eligible and estimated events: 17.
- Independent assets: ARB, BNB, and UNI.
- Events matching their predicted sign: 8 of 17.
- ARB mean direction-adjusted three-day abnormal log return: -0.0155.
- BNB mean direction-adjusted three-day abnormal log return: -0.0017.
- UNI direction-adjusted three-day abnormal log return: -0.0001.
- Pooled mean direction-adjusted three-day abnormal log return: -0.0113.
- Exact two-sided asset-level sign-flip p-value: 0.25 from eight assignments.

Positive direction-adjusted returns would support H3: unlock returns are multiplied by -1 because their predicted sign is negative, while burn returns retain their sign because their predicted sign is positive. All three asset-level averages are negative. The expanded evidence therefore still does not support H3.

## Interpretation and limitation

The randomization unit remains the asset rather than the event, so twelve ARB unlocks are not treated as twelve independent experiments. Three assets permit eight exact sign assignments—better resolution than the earlier four, but still low power. The UNI burn was preceded by a public proposal and vote; an execution-date event window can miss a price response that occurred earlier. This anticipation limitation is reported rather than addressed by moving the event date after inspecting returns.

## Next gate

Add a fourth asset only if a primary source establishes an exact effective date and quantity, the event exceeds 0.5% of pre-event circulating supply, and the event was not selected from observed returns. SUI remains excluded because its official circulation series provides month-end totals rather than an exact intra-month effective date.
