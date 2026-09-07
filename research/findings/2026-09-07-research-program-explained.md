# What this research is, in plain language

7 September 2026. A complete account of the project for someone who has not seen the code: the questions, the method, the machinery, what we found, and what could be published today.

---

## 1. The problem, stated simply

If you want to value a company, you know what to look at. Revenue, costs, growth, the cash it returns to shareholders. Different companies get different treatment, but the categories are agreed, and a bank and a software firm are understood to be different kinds of thing.

Cryptoassets have no such agreement. They get sorted by the technology underneath them, so people say "Layer 1", "Layer 2", "DeFi token", or by marketing labels the projects choose for themselves. Neither tells you how the thing is supposed to make anyone money. Bitcoin and Ethereum are both called Layer 1s, but Bitcoin has a fixed supply and no fee burn, and Ethereum has no supply cap and destroys fees as they are paid. Those are opposite monetary designs sharing a label. Meanwhile Uniswap and Aave are both "DeFi tokens" and share almost nothing.

So the question underneath this project is simple to state and hard to answer.

**Do the economic jobs a token actually performs explain what it is worth and how risky it is?**

Not the technology. Not the label. The jobs. Is it used as money. Do you have to spend it to use the network. Is it locked up to keep the network safe. Does using the network destroy some of it. Is there a hard limit on how many exist. Is it accepted as collateral. Does holding it give you a vote. Does protocol revenue actually reach the token. Is it needed to buy some service. Is it being given away to bootstrap usage.

Ten jobs. Every asset gets a yes or no on each, and the yes has to be proven from the protocol's own documentation, on a date.

---

## 2. Why "prove it on a date" is the whole idea

The single most important design choice in this project sounds like bookkeeping and is actually the intellectual core.

A token's economics change. Uniswap did not route fees to a burn until December 2025. Aave started buying back its own token in April 2025 and paused it in April 2026. If you look up "does Uniswap burn fees" today and answer yes, then apply that yes to price data from 2024, you have quietly used tomorrow's newspaper to explain yesterday's market. Every answer you get afterwards is contaminated.

So every classification in this project is stamped with the date it became true, and the pipeline resolves what was true on each day of data separately. A mechanism that was announced but not live counts as no. A mechanism that was paused counts as no from the pause date. An answer nobody can evidence stays blank, and a blank never quietly becomes a zero.

That rule cost us a headline result, which is the best evidence that it is working. More on that below.

---

## 3. The classification architecture

Four layers, each doing one job.

**Layer 1, technical context.** Proof of work, proof of stake, application token, rollup governance token. Recorded, then deliberately kept out of the economics. Architecture is a control variable, never an answer.

**Layer 2, ten economic functions.** Each has a written rule, a list of the evidence that would satisfy it, and three possible verdicts: yes with evidence, no with evidence, or unresolved.

| Code | The job it names |
|---|---|
| MONETARY | Used as money, settlement, or a store of value |
| GAS | Required to pay for using the network |
| STAKE | Locked or at risk to keep something secure |
| BURN | Usage permanently destroys some of it |
| SCARCITY | A hard cap that is very hard to change |
| COLLATERAL | Accepted as material collateral elsewhere |
| GOV | Holding it gives real control |
| PROTOCOL | Revenue mechanically reaches the token or its holders |
| UTILITY | Required to buy an identifiable service |
| INCENTIVE | A programme subsidises usage or participation |

**Layer 3, eight bundles.** The ten functions group into eight economically distinct families, decided from theory before any estimation, so that the grouping cannot be tuned to a result.

**Layer 4, measurement readiness.** For each of the 34 pieces of evidence the rules call for, the pipeline records whether we have it as a real time series, as a proxy, as a document only, or not at all. Three functions are measured (monetary, gas, collateral), three are proxied (stake, burn, protocol), four are documents only (scarcity, governance, utility, incentive). This is stated plainly because a function you can only document cannot enter a valuation model as a variable, and pretending otherwise is how bad papers get written.

### The sharpest rule we wrote

The hardest boundary turned out to be between **governance** and **value capture**, and getting it right changed a result.

Arbitrum's DAO receives network revenue and ARB holders vote on the treasury. Cardano is similar. It is tempting to call that value capture, because tokenholders control the money. But the money is spent on grants, infrastructure and development. It never mechanically reaches the token or its holders. Compare that with Ethereum, where every transaction burns ETH, or Aave's buyback, where protocol revenue is used to buy the token itself. In those cases value terminates at the token by rule, not by vote.

So the rule reads: **governance authority over a treasury is not value capture unless value mechanically terminates at the token, through a burn, a buyback, a distribution, or an enforceable claim.** Voting on how to spend money is a right, not a cash flow.

---

## 4. The research questions and the hypotheses

Five questions drive the work.

1. Which economic functions is each asset actually performing, on each date, and does that carry information beyond what the technology already tells you?
2. Does network usage explain what an asset is worth, over and above the market as a whole?
3. Does usage matter *more* when there is a live mechanism sending value back to the token?
4. Do assets doing several economic jobs at once command a premium over single-purpose assets?
5. Does economic function explain how *risky* an asset is, even where it fails to explain returns?

These become six registered experiments. Each one has a specification file written and frozen before the estimation runs, so that nobody, including us, can quietly change the test after seeing the answer.

| ID | Hypothesis | Status |
|---|---|---|
| P1_H1 | Usage is associated with higher market value | Estimated, suggestive, not significant |
| P1_H2 | Usage matters more when value capture is live | **Estimated, definition-dependent** |
| P1_H3 | Theory bundles beat a raw count of functions | Estimated, bundles do not beat the count |
| P1_H4 | Staking reduces free float and affects liquidity | Blocked on a data source |
| P1_H5 | Turning a capture mechanism on or off moves value | Estimated, no effect detected |
| P1_H6 | Function predicts risk exposure, not return | **Estimated, not supported after correction** |

---

## 5. The data and the machinery

**What we have.** Daily prices, volumes and trade counts for 24 assets from 2019 to August 2026, about 52,000 asset-days, from archived exchange data. One year of daily network fees, protocol revenue and holder revenue for 11 economic systems. Network activity for the assets where a free provider offers it. Ninety days of on-chain staking readings taken block by block for BNB and for Aave's legacy contract. Collateral balances read directly from lending protocols. And the classification evidence itself: dated links to protocol documentation for every yes and every no.

**How it is organised.** Raw snapshots are downloaded once and never edited, with a checksum. Everything downstream is rebuilt from them by code, so any number in any document can be regenerated from scratch. There are 66 modules arranged in seven stages that run in a fixed order, and a test that fails if any module is missing from that order. There are 238 unit tests. Nothing is done by hand in a spreadsheet.

```
raw snapshots  ->  normalised series  ->  classification evidence  ->  frozen experiment  ->  result
   (immutable)        (rebuilt)            (dated, reviewed)          (spec written first)   (reproducible)
```

**The review protocol.** Classifications are drafted by one coder with sources, then a second reviewer scores the same decisions blind, without seeing the first set. A script compares them and computes the agreement statistic. Disagreements are adjudicated with a written rule, and the rule is recorded so it applies to every future case. This is standard practice in empirical social science and almost absent from crypto research.

---

## 6. What we actually found

### Finding 1: technology does not predict economics

Two proof-of-stake base layers, Ethereum and BNB, differ on two of the ten functions. Two application tokens, Uniswap and Aave, share only one. Collateral use and governance are the most common functions in the verified core; a genuine hard cap is the rarest, held by Bitcoin alone among the six. The classification carries information that the architecture label does not.

### Finding 2: value capture matters, but only if you define it loosely

The central test, P1_H2, asks whether fee activity is more strongly related to market value when a capture mechanism is live. Across eleven assets over a year, the interaction is positive and holds up when any single asset is removed. Under the original broad definition, which counted a tokenholder-governed treasury as capture, the estimate is 0.132 with an exact p-value of 0.082, just inside the 10 percent exploratory threshold.

Then we applied the strict rule from Section 3, which says a governed treasury is not capture. The estimate roughly halves to 0.061 and the p-value rises to 0.478. **The finding does not survive its own definition.**

That is reported as the result, not buried. It is also the most useful thing in the paper, because it says precisely where the disagreement lives. Whether "value capture" includes governed treasuries is not a modelling detail. It is the difference between a result and no result.

### Finding 3: counting functions tells you nothing

Assets performing more economic jobs are not reliably worth more. The slope is positive but the exact permutation test does not come close to significance. Grouping the functions into theory bundles does not help either, because on a six-asset core the bundle count and the raw count are almost the same variable. The one predictor that improves out-of-sample accuracy is the monetary bundle alone, and even that is partly a size effect, since the monetary assets in the core are also the largest.

### Finding 4: turning mechanisms on and off does not visibly move prices

Three events had enough clean data: Aave's buyback launch, Uniswap's fee-to-burn activation, and Aave's buyback pause. One of the three moves in the predicted direction. None is distinguishable from placebo events on random dates or on control assets. On a one-year view the Aave pause looked like a 13 percent effect; on the seven-year panel with 22 control assets it disappears entirely. A result that vanishes under a better test was never a result.

### Finding 5: the market factor eats almost everything

Across 24 assets, a single common market factor explains a median 60 percent of daily variation. Bitcoin is the low-beta asset at 0.67, the rollups are the high-beta tail at 1.27 and 1.40 with badly negative alpha. Momentum is flat, volatility is not priced, and higher-beta assets actually earn *less*, the same "betting against beta" pattern seen in equities. Anything the classification claims to explain must clear that bar first.

### Finding 6: function looks related to risk, and does not survive correction

This is the most recent test, P1_H6, and it was frozen before it was run. Measuring all assets on one common window with a size control, we asked whether function predicts market beta, volatility, and worst drawdown.

The direction is consistent. Assets classified as money average a beta of 0.93 and a worst drawdown of −1.44, against 1.19 and −2.37 for the rest. Assets you must spend to use the network look the same way. Governance-heavy tokens are the reverse. The gaps are economically large.

But we ran 27 tests, and with 27 tests you expect roughly one or two to look significant by pure chance. Three did. After the standard correction for multiple testing, none survives. **The honest report is that the hypothesis is not supported yet**, with a consistent signal that is worth pursuing on more assets.

Note what does *not* show up: holder capture, the mechanism at the heart of P1_H2, predicts none of the three risk measures. Nor does the raw count of functions.

---

## 7. Where the evidence stands, and its limits

Verified today: six assets fully classified across all ten functions, sixty of sixty decisions, zero unresolved, reconciled with a blind reviewer at perfect agreement after one adjudication. Fourteen more assets have just been drafted across the five most mechanical codes, 59 verified and 11 held open.

The binding constraint is honest and simple. **Six fully verified assets cannot support a claim about the market.** Cross-sectional tests on six assets cannot separate a function from size, because the three monetary assets are also the three largest. The provisional classifications used for the twenty-asset test have not been through evidence review, and the tranche A work just exposed exactly why that matters: the provisional matrix says Stellar burns fees, and the protocol documentation says fees go into a locked account and are never destroyed. Sequestration is not destruction. Five such disagreements turned up in 59 decisions.

Two boundary questions are open and recorded rather than resolved quietly. On Bitcoin-style chains a zero-fee transaction is technically valid and fee minimums are node policy, so the verified Bitcoin decision scores "required to pay fees" as no; Bitcoin Cash, Litecoin, Dogecoin and Zcash have the same property, and scoring them differently would contradict the precedent. And Chainlink's rewards are currently funded by emissions, which is service payment, but the project describes a Reserve whose treatment under the strict capture rule has not been established from primary sources.

---

## 8. How this scales into a valuation model

The path from here is not "add more machine learning". It is to finish the measurement and let the model be simple enough to defend.

**Step one, finish the classification.** Twenty-five assets fully verified across ten functions, in three tranches ordered by difficulty. That turns a case study into a dataset and is the only thing standing between the current results and a real cross-sectional test.

**Step two, turn documents into series.** Four of the ten functions currently exist only as documents. Governance can become delegated supply over time. Incentives can become programme emissions. Once a function is a number that moves, it can enter a panel rather than sit as a fixed label.

**Step three, the model that the evidence actually supports.** Not a price forecast. The credible model is one that explains an asset's *risk profile and valuation multiple* from its functions: what beta should this asset have, what drawdown should you expect, what multiple of fees should it trade at, given what it does. That is the analogue of a sector model in equities, and the early signs point that way while the return-prediction results point nowhere.

**Step four, mechanisms as events.** Every time a protocol turns a burn on, or pauses a buyback, the effective-dated ledger records it. As those accumulate the event study stops being three observations and starts being a real test of whether the market prices these mechanisms at all.

The honest expectation, stated up front: daily crypto returns are close to unpredictable, and this project should not promise otherwise. What a functional taxonomy can plausibly deliver is a defensible account of *what kind of asset this is* and *what risk that implies*, which is what an advisor or an allocator actually needs.

---

## 9. What could be published today

**The strongest paper available right now is a methods and measurement paper, not a results paper**, and that is not a consolation prize. The contributions stand on their own.

1. **A reproducible economic-function taxonomy for cryptoassets**, with written rules, dated primary-source evidence, blind review, a reported agreement statistic, and adjudication rules that generalise. Nothing comparable exists in the literature.
2. **The governed-treasury capture boundary.** A conceptual contribution with a demonstrated empirical consequence: define capture loosely and you get a result at the 10 percent level; define it strictly and the result disappears. That is a finding about the literature, not just about our data.
3. **A set of well-powered negative results.** Function breadth does not command a premium. Mechanism activations are not visibly priced. Function does not predict risk once you correct for multiple testing. Each is pre-registered, each is reported, and the field currently has very few honest nulls.
4. **The infrastructure itself**, releasable as a reproducibility artifact: immutable snapshots, frozen specifications, seven ordered stages, 238 tests, and every number in the manuscript regenerable from one command.

What cannot be published yet is any claim that economic function explains cross-sectional value or risk market-wide. That needs the remaining classification work, and the schedule for it is written down.

---

## 10. Principles we work by

These are enforced by code, not by good intentions.

- **Freeze before you look.** Every experiment's specification exists in the repository, with a freeze date, before its estimate is produced.
- **Never backfill.** What we know today cannot be applied to yesterday's prices. Mechanisms carry the date they became true.
- **Unknown is not zero.** Missing evidence stays null. Eleven of seventy tranche A decisions are open right now for exactly this reason.
- **Correct for looking many times.** Twenty-seven tests get twenty-seven-test treatment.
- **Report the weaker version.** Where two defensible specifications disagree, both are published side by side. That is why the halved P1_H2 estimate and the vanished Aave event effect both appear here.
- **Do not choose what to measure based on what showed a result.** Classification tranches are ordered by evidence difficulty, decided in advance, precisely so the next round of work cannot be steered toward the bundles that looked promising.
- **A rule adjudicated once applies everywhere.** The treasury boundary settled Arbitrum and Cardano together, and now settles Zcash's development fund the same way.

The last one is worth stating plainly, because it is unusual. On two separate occasions this project produced a number that looked like a finding, and on both occasions applying its own rules honestly made the number go away. That is what the rules are for.
