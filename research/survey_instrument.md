# Expert panel instrument

Draft, 7 September 2026. For a panel of digital-advisory and digital-asset professionals. Purpose is to settle assumptions the project currently carries on its own authority, and to convert the classification review protocol into a reported reliability statistic.

This is an **expert panel**, not a representative survey. Ten to fifteen considered responses is the target. Report it as a panel and never as a population estimate.

---

## What this audience can and cannot settle

Match the question to the expertise or the answers are worthless.

**They are the right people for:** whether classifying by economic function is useful at all; whether the ten functions are complete; what "material" means for collateral and monetary use, since setting materiality thresholds is practitioner work; whether binary or graded coding is right; which functions they believe drive value, which is a prior worth capturing; and what output would actually be usable.

**They are the wrong people for:** protocol facts. Whether Solana burns half its base fee is settled by reading Solana's documentation, not by polling. Do not put factual questions in a survey — it launders a documentation gap into an opinion.

**Only a subset can do Section 5.** Blind classification needs protocol-level knowledge and about twenty minutes. Screen for it with Q0.3 rather than sending it to everyone.

---

## Fielding rules

1. **Field and close this before re-estimating anything.** Several answers change classifications that determine the project's strongest association. Collecting them after seeing which answer helps would invalidate the result.
2. **Anonymise the assets in Section 2.** Naming Arbitrum invites a view about Arbitrum instead of a view about the rule.
3. **Do not reveal the project's own answers, or which way the data points**, until after the response is submitted. Offer to send findings afterwards as the incentive.
4. **Q2.2 is a calibration item** with a near-unanimous expected answer. A respondent who misses it is answering randomly; note it, do not silently drop them.
5. **Two rounds if you can.** Round two shows the anonymised distribution and the reasons given, then re-asks only the items where the panel split. Convergence is itself reportable.
6. Target completion time is twelve minutes for Sections 0 to 4, plus twenty for Section 5.

---

## Section 0. Respondent profile

**0.1** Which best describes your role?
Asset or wealth management · Financial advisory · Research or analytics · Protocol or foundation · Exchange, custody or market infrastructure · Academic · Other

**0.2** Years working with digital assets professionally.
Under 2 · 2 to 5 · 5 to 8 · Over 8

**0.3** How would you rate your familiarity with protocol-level mechanics such as fee burns, staking design and issuance schedules?
1 Not familiar · 2 · 3 · 4 · 5 I read protocol documentation regularly

*Routing: send Section 5 only to respondents selecting 4 or 5.*

**0.4** Do you make or advise on allocation decisions in digital assets? Yes · No

---

## Section 1. Is economic function the right axis?

*Tests the project's foundational assumption, which currently has no external support.*

**1.1** When you assess a cryptoasset, how useful is each frame for organising your thinking? Rate 1 (not useful) to 5 (essential).

| Frame | 1–5 |
|---|---|
| Technical architecture (Layer 1, Layer 2, rollup) | |
| Sector label (DeFi, infrastructure, gaming, payments) | |
| Economic function (what the token is used for and what accrues to it) | |
| Market capitalisation tier | |
| Regulatory or legal status | |

**1.2** Below are ten economic functions. For each, rate how much you think it *should* matter to what a token is worth. 1 (irrelevant) to 5 (decisive).

| Function | Plain description | 1–5 |
|---|---|---|
| Monetary use | Used as money, settlement or a store of value | |
| Fee requirement | You must spend it to use the network | |
| Staking | Locked or at risk to secure something | |
| Burn | Usage permanently destroys supply | |
| Hard cap | A terminal supply limit that is very hard to change | |
| Collateral | Accepted as material collateral elsewhere | |
| Governance | Holding it gives real control | |
| Revenue capture | Protocol revenue mechanically reaches the token | |
| Service utility | Required to buy an identifiable service | |
| Incentives | A programme subsidises usage or participation | |

**1.3** Is anything missing from that list, or is anything on it redundant? Free text.

**1.4** Should technical architecture be treated as part of a token's economic profile, or kept separate as context?
Part of it · Kept separate · Depends, explain

---

## Section 2. Boundary rules

*Scenarios only. No asset names. Each item is a forced choice plus one line of reasoning.*

**2.1 Governed treasury.**
A protocol earns real revenue from usage. The revenue accumulates in a treasury. Token holders vote on how the treasury is spent. The evidenced spending funds ecosystem grants, infrastructure and developer salaries. There is no burn, no buyback and no distribution to holders.

Does the token capture value from that revenue?
Yes, capture · No, this is a governance right only · Depends
*Why, in one line.*

**2.2 Fee destruction.** *(calibration)*
Every transaction on a network permanently destroys a portion of the native token by protocol rule. Nobody receives the destroyed tokens. Supply falls.

Does the token capture value from usage?
Yes · No · Depends
*Why, in one line.*

**2.3 A paused mechanism.**
A protocol funded buybacks of its own token for twelve months. Governance paused the programme three months ago. The mechanism still exists in the code and could be restarted by a vote.

For classification as of today, is the mechanism active?
Active · Not active · Partially, explain
*Why, in one line.*

**2.4 Fees by convention rather than by rule.**
On a particular chain, a transaction paying zero fee is valid under the consensus rules. Block producers simply choose not to include such transactions, so in practice everyone pays a fee.

Is the native token *required* in order to transact?
Yes, required in substance · No, only by convention · Depends
*Why, in one line.*

**2.5 Rewards paid from new issuance.**
Stakers receive newly issued tokens for securing a network. The tokens are created rather than transferred from fee revenue.

Is that value accruing to the token, or payment for a service rendered?
Value accrual · Payment for a service · Depends
*Why, in one line.*

**2.6 Escrowed rather than destroyed.**
Fees collected by a network are moved into an account that no one controls and from which nothing can be spent. Supply is unchanged, but the tokens are permanently immobilised.

Is that economically equivalent to destroying them?
Equivalent · Not equivalent · Depends
*Why, in one line.*

---

## Section 3. Materiality thresholds

*Practitioner judgment. This is the section this audience is best qualified for.*

**3.1** At what point would you say an asset is *materially* used as collateral?
Any observable use · Above 100m dollars outstanding · Above 1% of its own market cap · Above 5% of its own market cap · Both a dollar floor and a percentage floor · Other

**3.2** What evidence would convince you a cryptoasset is genuinely used as money rather than merely traded? Select all that apply.
Merchant or payment acceptance at scale · On-chain transfer value large relative to market cap · Held as a reserve asset by institutions or treasuries · Used as a unit of account for pricing · Material remittance or cross-border corridor volume · Sustained non-speculative transaction counts · None of these are sufficient on their own

**3.3** How long must a mechanism be live before you would count it in a classification?
No minimum, count it from activation · 30 days · 90 days · 180 days · A full year

**3.4** Should these functions be recorded as yes or no, or on a scale?
Binary yes/no · Three levels: none, partial, material · Continuous intensity score · It depends by function, explain which

**3.5** If evidence for a function is unavailable or ambiguous, what should the classification record?
Record it as absent · Record it as unknown and exclude the asset from tests using it · Record a best estimate with a confidence flag · Other

---

## Section 4. What output would be useful

**4.1** Which would be most useful in your work?
A model estimating fair value from a token's functions · A model estimating risk profile, meaning market sensitivity, drawdown and volatility, from its functions · The classification itself, applied by me · A screening tool that flags mismatches between price and function · None of these

**4.2** Suppose a classification told you an asset is monetary, collateral-eligible and supply-capped, with no revenue capture. What, if anything, would you do differently with that information? Free text.

**4.3** What would make you trust a classification produced by researchers rather than a data vendor? Select all that apply.
Published rules · Primary sources cited per decision · A second independent reviewer and a published agreement statistic · Open code that regenerates every number · Named authors and institution · Track record of predictions · Nothing would, I would use a vendor

**4.4** Anything you would want this research to answer that it currently does not? Free text.

---

## Section 5. Blind classification exercise

*Only for respondents rating 4 or 5 on Q0.3. Roughly twenty minutes.*

Instructions to the respondent: score each cell using only the rule text and your own knowledge. Do not consult the project's classifications. If you do not know, mark unknown rather than guessing, because a guess is worse than a gap here.

Present 12 to 15 asset-and-function cells as a table with three columns: asset, function with its full rule text, and a response of Yes, No or Unknown, plus an optional source.

Sample construction rules, fixed before fielding:

- Draw cells from assets already verified in the project **and** from the pending tranche, so agreement can be measured against both a settled answer and an open one.
- Include at least three cells the project itself holds pending, so the panel is genuinely contributing rather than only replicating.
- Do not select cells by whether they favour a result.
- Keep the same sample for every respondent so kappa is computed on a common grid.

Reporting: raw agreement and Cohen's kappa against the project's verified values, computed only over cells where both sides gave a determinate answer, with unknowns reported separately as a coverage figure. The existing `review_adjudication` command consumes exactly this grid.

---

## What each section settles

| Section | Assumption it addresses | What changes if the panel disagrees with us |
|---|---|---|
| 1.1, 1.4 | Economic function is the right organising axis, and architecture belongs outside it | The framing of the paper's contribution |
| 1.2 | Which functions practitioners believe drive value | Nothing mechanical, but the contrast with the data is itself a finding |
| 1.3 | The ten functions are complete and non-redundant | A missing function means the taxonomy needs an eleventh code and a new tranche |
| 2.1, 2.5 | The strict holder-capture rule | Directly flips the project's headline result between significant and not |
| 2.2 | Calibration | Detects inattentive responses |
| 2.3 | A paused mechanism scores zero | Two pending cells, and the Aave event study's interpretation |
| 2.4 | Relay policy is not a protocol requirement | Four pending cells, and re-opens the verified Bitcoin decision |
| 2.6 | Escrow is not destruction | One verified cell, currently scored on our own reading |
| 3.1 | The collateral threshold of 1% or 100m dollars over 90 days | Recodes collateral across the universe |
| 3.2 | What material monetary use requires | Recodes the single strongest predictor in every cross-sectional test |
| 3.3 | The 90-day persistence window | Recodes any recently activated mechanism |
| 3.4 | Binary coding | A graded scheme would require re-coding everything and rebuilding the bundles |
| 3.5 | Unknown stays null and never becomes zero | A core reproducibility rule |
| 4.1 | Risk exposure rather than fair value is the useful output | The direction of the next phase |
| 4.3 | The review protocol is what earns trust | What to emphasise in the methods section |
| 5 | The classification is reproducible by someone outside the project | Produces the external reliability statistic the paper currently lacks |

---

## The question that turns an input into a finding

Q1.2 asks practitioners which functions *should* drive value. The project's own data says monetary use and transaction demand track risk, while revenue capture predicts nothing.

If the panel ranks revenue capture at or near the top, the paper gains a second contribution at the cost of a single question: **the mechanism practitioners believe matters most is the one with the least empirical support in this sample.** Report the panel ranking beside the estimated associations and let the gap speak.

Prediction to record before fielding, so this is a test rather than a story told afterwards: capture and monetary use will rank in the top three, incentives and governance in the bottom three.
