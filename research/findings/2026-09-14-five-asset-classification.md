# Five-asset classification pass — 14 September 2026

HYPE, XMR, TON, TAO and POL now have a documented first pass across all 50 cells. 28 are supported by primary sources; 22 remain null with specific evidence needs. Overall the working matrix has **176 supported, 46 pending and 28 provisional cells**. No independent review was added.

## Decisions

Y/N = supported yes/no; ? = pending. Monetary use and collateral require measured use, not merely a product description.

| Asset | Money | Fees | Stake | Burn | Cap | Collateral | Governance | Capture | Utility | Incentives |
|---|---|---|---|---|---|---|---|---|---|---|
| HYPE | ? | Y | Y | Y | Y | ? | Y | Y | Y | ? |
| XMR | ? | ? | N | N | N | ? | N | N | N | N |
| TON | ? | Y | Y | Y | N | ? | Y | Y | Y | ? |
| TAO | ? | Y | ? | ? | Y | ? | ? | ? | Y | ? |
| POL | ? | Y | Y | ? | N | ? | ? | ? | Y | ? |

## Reading the decisions

HYPE has a documented fee-funded buyback and burn route and a separate execution-fee burn. Its governance value refers specifically to binding market-rule decisions by HYPE-weighted validators, not a general claim of holder control. [Hyperliquid fees](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees).

XMR has uncapped tail issuance. Its native mining rewards and discretionary crowdfunding do not qualify as a separate rules-based incentive programme. [Tail emission](https://www.getmonero.org/resources/moneropedia/tail-emission.html), [crowdfunding rules](https://ccs.getmonero.org/what-is-ccs/).

TON documentation describes native fee burning and binding stake-weighted configuration votes. Current technical pages call the native currency Gram; this pass retains the existing registry identifier, crypto_ton. No historical reclassification is inferred from terminology. [Configuration rules](https://docs.ton.org/foundations/config).

TAO recycling permits later re-emission, and alpha is a separate asset. Permanent TAO burns, security exposure and incentive denomination need further resolution. [Bittensor emissions](https://www.bittensor.com/docs/concepts/emissions).

POL has continuing issuance. New fee-routing and gas-subsidy proposals mean the historical MATIC burn description alone is insufficient to settle current capture or incentives. [POL issuance](https://docs.polygon.technology/pos/concepts/tokens/pol), [gas programme](https://forum.polygon.technology/t/pip-82-agentic-commerce-gas-program/21721).

## Evidence still needed

| Asset | Function | Next evidence | Source inspected |
|---|---|---|---|
| HYPE | MONETARY | Measure the agreed monetary-use indicators over the required window, applying the settled materiality rule. | [Source](https://hyperliquid.gitbook.io/hyperliquid-docs/about-hyperliquid/hyperliquid-101-for-non-crypto-audiences) |
| HYPE | COLLATERAL | Collect the 90-day collateral series and assess coverage and materiality; retain the documented eligibility as supporting evidence. | [Source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/portfolio-margin) |
| HYPE | INCENTIVE | Confirm a live non-consensus HYPE programme, its payout currency and rules; do not treat fee discounts or historical airdrops as token distributions. | [Source](https://hyperliquid.gitbook.io/hyperliquid-docs/referrals/proposal-staking-referral-program) |
| XMR | MONETARY | Assemble usage evidence and document what privacy prevents observing; apply the same monetary threshold as other assets. | [Source](https://www.getmonero.org/get-started/what-is-monero/) |
| XMR | GAS | Check executable zero-fee transaction validity and apply the same boundary as BTC and the four held UTXO assets. | [Source](https://www.getmonero.org/get-started/mining/) |
| XMR | COLLATERAL | Identify qualifying collateral venues and gather the required observation window; do not infer zero from privacy or lack of an EVM token. | [Source](https://www.getmonero.org/get-started/what-is-monero/) |
| TON | MONETARY | Collect monetary-use observations over the required window and apply the settled threshold. | [Source](https://docs.ton.org/applications/payments/gram) |
| TON | COLLATERAL | Identify eligible TON or qualifying wrapped exposures and gather 90-day collateral observations. | [Source](https://docs.ton.org/nodes/staking/overview) |
| TON | INCENTIVE | Find current TON-denominated programme terms and operating dates; distinguish ecosystem jetton rewards and historical campaigns. | [Source](https://docs.ton.org/nodes/staking/overview) |
| TAO | MONETARY | Collect monetary-use indicators and apply the settled threshold without substituting subnet trading volume. | [Source](https://www.bittensor.com/docs/concepts/money) |
| TAO | STAKE | Trace present TAO security responsibilities and protocol-defined consequences; distinguish alpha market exposure from TAO security capital. | [Source](https://www.bittensor.com/docs/concepts/staking-pools) |
| TAO | BURN | Establish a live permanent TAO destruction mechanism or settle whether all relevant native mechanisms are recycling; do not count alpha burns as TAO. | [Source](https://www.bittensor.com/docs/concepts/emissions) |
| TAO | COLLATERAL | Identify qualifying TAO collateral markets and gather the required 90-day balances. | [Source](https://www.bittensor.com/docs/concepts/staking-pools) |
| TAO | GOV | Verify current governance authority and implementation; distinguish stake-based reward allocation from binding protocol or treasury decisions. | [Source](https://www.bittensor.com/docs/concepts/transactions) |
| TAO | PROTOCOL | Trace external revenue or surplus to TAO holders or an enforceable TAO sink under the strict rule. | [Source](https://www.bittensor.com/docs/concepts/emissions) |
| TAO | INCENTIVE | Determine whether an active TAO distribution is separable from native consensus/security issuance under the existing rule, and verify payout denomination. | [Source](https://www.bittensor.com/docs/concepts/emissions) |
| POL | MONETARY | Measure POL-specific monetary use over the required observation window. | [Source](https://docs.polygon.technology/pos/concepts/tokens/pol) |
| POL | BURN | Verify current implementation and actual non-recycled burn execution at the classification date; do not carry forward the old MATIC burn description untested. | [Source](https://forum.polygon.technology/t/pip-82-agentic-commerce-gas-program/21721) |
| POL | COLLATERAL | Identify native/wrapped POL lending reserves and gather 90-day collateral balances; distinguish POL from liquid-staking receipt tokens. | [Source](https://polygon.technology/spol-terms-of-use-risk-disclosures) |
| POL | GOV | Resolve operative binding holder or delegated rights across these mechanisms; do not treat signaling or a council label as sufficient. | [Source](https://forum.polygon.technology/t/pip-50-staked-tokenholder-signalling/19974) |
| POL | PROTOCOL | Confirm current fee-flow contracts, distributions and final burn destination under the strict capture rule. | [Source](https://forum.polygon.technology/t/pip-82-agentic-commerce-gas-program/21721) |
| POL | INCENTIVE | Confirm activation and current remaining budget or payouts before classifying the programme as active. | [Source](https://forum.polygon.technology/t/pip-82-agentic-commerce-gas-program/21721) |

The full decision record is [crypto_evidence_remaining_assets.json](../../config/crypto_evidence_remaining_assets.json), including primary and supporting URLs, retrieval dates and short rationales. The workbook uses these values and leaves pending cells blank. These are current documentation judgments dated September 14, not a claim of historical availability. The survey, prediction, historical ledger and frozen estimates were not changed.

The dated source archive contains 30 of 31 downloaded primary pages, with retrieval times and hashes in `data/raw/classification_sources/2026-09-14/remaining_assets/manifest.json`. The unsuccessful direct download is recorded explicitly: https://www.ton.org/en/whitepaper.pdf. That source was inspected through web retrieval.
