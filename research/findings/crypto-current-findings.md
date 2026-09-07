# Current Crypto Findings

**Headline:** Fee activity has a persistent positive association with valuation when active capture exists, but the evidence is exploratory and does not predict seven-day returns.

- H2 pooled valuation interaction: 0.132; exact p-value: 0.082.
- H2 chain valuation interaction: 0.141; exact p-value: 0.125.
- All leave-one-asset-out valuation interactions positive: True.
- Non-overlapping return offsets rejecting zero at 10%: 0.

Higher fees are more strongly associated with market value when active capture exists. The result is persistent across asset exclusions and crosses the 10% exploratory reference threshold, but the post-pilot freeze and small sample prevent confirmatory interpretation; there is no robust short-horizon return signal.

Active-address and transaction-count coefficients are positive in the four-asset panel, and transaction count remains positive in every leave-one-out sample. Exact four-cluster inference does not reject zero, so H1 remains suggestive and cannot be generalized beyond BTC, ETH, UNI, and AAVE. The free circulating-supply diagnostic does not support H3: its coefficient is positive rather than the predicted negative and exact inference does not reject zero. More importantly, only BTC and ETH vary within the window, so a point-in-time unlock and issuance event panel is still required for an identification-ready test. H4 is not yet estimable. A complete 90-day BNB consensus-staking series ranges from about 25.51m to 25.78m BNB. The exact ETH active-effective-balance collector is implemented but needs an archival consensus endpoint, while the legacy stkAAVE series excludes current Umbrella aToken/GHO stake. One complete positive-staking series remains insufficient to identify liquid-float effects. The frozen five-asset breadth result was positive but unstable. In the separately frozen six-asset extension, the slope remains positive and is positive in all six leave-one-out samples, but exact permutation inference does not reject zero. Breadth is more sign-stable after adding BNB, yet there is still no statistically robust valuation-premium evidence. Stablecoin H5-H7 are deferred to a later phase.
