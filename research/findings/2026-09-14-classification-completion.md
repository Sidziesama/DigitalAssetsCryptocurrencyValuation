# Classification completion — 14 September 2026

178 of 250 cells are evidence-backed, 44 pending, and 28 provisional. The first pass closed five documentation gaps; the governance, utility and incentive pass added another 24 supported decisions. A subsequent five-asset pass added 28 more supported decisions. The documentation follow-up resolved SOL governance and, with researcher approval, ZEC governance. No independent review was added.

| Asset | Function | Decision | Source |
|---|---|---|---|
| DOGE | Burn | No | [Official mining documentation](https://dogecoin.com/dogepedia/articles/what-is-a-miner/) |
| DOGE | Revenue capture | No | Fees compensate miners for service, under the same source. |
| LTC | Burn | No | [Official fee FAQ](https://litecoin.com/what-is-litecoin) |
| HBAR | Burn | No | [Schedule A fee and payment rules](https://hedera.com/terms/) |
| OP | Burn | No | [Buybacks retain tokens in treasury; burning is a future possibility](https://optimism.io/blog/op-token-buybacks) |

OP revenue capture remains pending. [Execution reports](https://gov.optimism.io/t/buyback-communication-thread/10588) confirm three completed buybacks. They do not establish continued operation at the September 7 classification date. The earlier claim that execution was unconfirmed has been corrected.

## Governance, utility and incentives

All 42 cells across the fourteen expansion assets were inspected. 24 received supported values; 18 remain null with specific evidence needs. The pending total increased because previously unexamined assumptions now have recorded gaps. This is a source-review pass, not external validation.

| Asset | Governance | Utility | Incentives |
|---|---|---|---|
| ADA | Yes | Yes | ? |
| AVAX | No | Yes | ? |
| BCH | No | ? | ? |
| DOGE | No | No | ? |
| HBAR | No | Yes | ? |
| LINK | ? | Yes | Yes |
| LTC | No | No | ? |
| OP | Yes | No | ? |
| SOL | No | Yes | ? |
| SUI | ? | Yes | ? |
| TRX | Yes | Yes | ? |
| XLM | No | Yes | ? |
| XRP | No | Yes | ? |
| ZEC | Yes | No | ? |

Every decision and its reasoning are in [tranche C](../../config/crypto_evidence_tranche_c.json). These are dated September 14, with retrieval dates recorded as retrieval dates, not historical effective dates. The existing definitions are unchanged.

## Working matrix

Y/N = supported yes/no; ? = pending; P = provisional assumption awaiting evidence.

| Asset | Money | Fees | Stake | Burn | Cap | Collateral | Governance | Capture | Utility | Incentives |
|---|---|---|---|---|---|---|---|---|---|---|
| BTC | Y | N | N | N | Y | Y | N | N | N | N |
| ETH | Y | Y | Y | Y | N | Y | N | Y | Y | N |
| BNB | Y | Y | Y | Y | N | Y | Y | Y | Y | Y |
| XRP | P | Y | N | Y | Y | P | N | Y | Y | ? |
| SOL | P | Y | Y | Y | N | P | N | Y | Y | ? |
| TRX | P | Y | Y | Y | N | P | Y | Y | Y | ? |
| HYPE | ? | Y | Y | Y | Y | ? | Y | Y | Y | ? |
| DOGE | P | ? | N | N | N | P | N | N | N | ? |
| ZEC | P | ? | N | N | Y | P | Y | N | N | ? |
| LINK | P | N | Y | N | Y | P | ? | ? | Y | Y |
| ADA | P | Y | Y | N | Y | P | Y | N | Y | ? |
| XMR | ? | ? | N | N | N | ? | N | N | N | N |
| XLM | P | Y | N | N | Y | P | N | N | Y | ? |
| BCH | P | ? | N | N | Y | P | N | N | ? | ? |
| LTC | P | ? | N | N | Y | P | N | N | N | ? |
| HBAR | P | Y | Y | N | Y | P | N | N | Y | ? |
| SUI | P | Y | Y | N | Y | P | ? | N | Y | ? |
| AVAX | P | Y | Y | Y | Y | P | N | Y | Y | ? |
| TON | ? | Y | Y | Y | N | ? | Y | Y | Y | ? |
| TAO | ? | Y | ? | ? | Y | ? | ? | ? | Y | ? |
| UNI | N | N | N | Y | N | N | Y | Y | N | N |
| AAVE | N | N | Y | N | N | Y | Y | N | N | Y |
| ARB | N | N | N | N | N | N | Y | N | N | Y |
| OP | P | N | N | N | N | P | Y | ? | N | ? |
| POL | ? | Y | Y | ? | N | ? | ? | ? | Y | ? |

## Remaining evidence

| Asset | Function | What is needed | Source inspected |
|---|---|---|---|
| ADA | INCENTIVE | Confirm ongoing Fund15 rewards or a subsequent active round with ADA payout rules and dates. | [Primary source](https://docs.projectcatalyst.io/current-fund/fund-basics/fund-parameters) |
| AVAX | INCENTIVE | Establish whether a separate active AVAX distribution programme has qualifying allocation rules; do not infer absence from discretionary grants. | [Primary source](https://retro-9000.avax.network/) |
| BCH | UTILITY | Trace CashTokens or contract-service consumption to BCH requirements and apply the existing utility rule consistently with the unresolved fee boundary. | [Primary source](https://github.com/bitjson/bch-p2s/blob/master/stakeholders.md) |
| BCH | INCENTIVE | Find current programme documentation sufficient to distinguish qualifying BCH rewards from mining and discretionary grants. | [Primary source](https://bitcoincash.org/) |
| DOGE | INCENTIVE | Confirm current fund operation and qualifying release payouts; do not code zero merely because native issuance goes to miners. | [Primary source](https://foundation.dogecoin.com/announcements/2022-12-31-corefund/) |
| HBAR | INCENTIVE | Confirm outstanding qualifying distributions or another active HBAR programme; exclude historical competitions and consensus rewards. | [Primary source](https://ai-bounties.hedera.com/) |
| LINK | GOV | Locate current administration and upgrade authority documentation to establish whether holders have binding governance rights. | [Primary source](https://docs.chain.link/resources/link-token-contracts) |
| LTC | INCENTIVE | Complete the current non-mining programme check before assigning a negative value. | [Primary source](https://litecoin.com/learningcenter) |
| OP | INCENTIVE | Identify an active September OP programme and its distribution rules and schedule. | [Primary source](https://gov.optimism.io/t/governance-update-12/10697) |
| SOL | INCENTIVE | Check current non-consensus SOL programme rules and operating dates. | [Primary source](https://solana.com/staking) |
| SUI | GOV | Find operative voting, execution and delegation rules or establish that the advertised mechanism is not deployed. | [Primary source](https://docs.sui.io/develop/sui-architecture/tokenomics-overview) |
| SUI | INCENTIVE | Verify an active SUI-denominated programme, distinguishing other-token rewards, discretionary grants, storage refunds and consensus issuance. | [Primary source](https://www.sui.io/programs-funding) |
| TRX | INCENTIVE | Check current non-consensus TRX distribution programmes and allocation rules. | [Primary source](https://developers.tron.network/docs/reward-calculation) |
| XLM | INCENTIVE | Check current XLM-denominated programmes; distinguish discretionary community grants, historical rewards and rewards in other tokens. | [Primary source](https://developers.stellar.org/docs/learn/fundamentals/lumens) |
| XRP | INCENTIVE | Establish current qualifying XRP programme rules or documented exclusions; do not infer absence from uncompensated validation. | [Primary source](https://xrpl.org/about/faq) |
| ZEC | INCENTIVE | Trace current ZEC recipient allocation rules and active distributions; distinguish funding a grants body from rewarding participation under a standing rule. | [Primary source](https://z.cash/upgrade/nu6-1/) |

Also outstanding: the six tranche A cells (BCH, DOGE, LTC and ZEC fee requirement; LINK and OP capture), 28 monetary/collateral cells, and 22 pending cells for HYPE, XMR, TON, TAO and POL. Their [five-asset report](2026-09-14-five-asset-classification.md) records the remaining evidence needs.

The earlier five documentation decisions retain September 7 as their classification date, with September 14 retrieval recorded and the historical-availability caveat retained. This new tranche is dated September 14. No effective-dated ledger, survey prediction or frozen experiment input was updated.

The working workbook and canonical status output are regenerated by their existing pipeline commands. This report is a dated snapshot.

Primary-source archive: `data/raw/classification_sources/2026-09-14/tranche_c/manifest.json` records URLs, retrieval times and hashes for 37 downloaded pages. Two Zcash pages blocked direct downloads; their records explicitly identify that limitation. Both were inspected through web retrieval.

Current follow-up: [documentation corrections and researcher review](2026-09-14-documentation-followup.md). The first-pass counts above describe that earlier pass; the full working matrix reflects the follow-up.
