# H4 execution checkpoint: pipeline complete, empirical result awaits ETH history

25 October 2026

H4 asks whether a larger staked share is associated with trading turnover, volatility and drawdown. The primary sample remains ETH and BNB with BTC, UNI and ARB structural controls. Legacy stkAAVE remains a separate case study.

## What is ready

- The 12 October sample/window design is preserved. Detailed outcome, lag, control and inference rules were committed on 25 October before any empirical H4 estimate.
- The gated estimator, `src/pipeline/crypto_h4_estimation.py`, assembles a balanced panel and estimates the three outcomes only after complete staking histories pass the gate.
- Market denominators and archived USD price lookbacks support 361 common days, above the 350-day requirement. The first study day is excluded because its preceding-day market denominator is not observed.
- BNB staking has all 362 required study dates.
- ETH staking has zero of the 362 dates, and `ETH_BEACON_ARCHIVE_API_URL` is not configured locally.
- Synthetic tests exercise the complete estimator and confirm that missing or partial ETH data cannot generate a research result. No synthetic figures appear in empirical outputs.

## Public-source checks

Small requests were made for validator 0 at slot 12,441,598, corresponding to the specified 25 August 2025 daily snapshot. The explorer probe used epoch 388,799.

| Source | Response | What can be concluded |
|---|---|---|
| PublicNode Beacon `/eth/v1/beacon/states/12441598/validators?id=0` | HTTP 403 | This request was denied. It does not establish whether a differently authorized service retains the state. |
| ChainSafe checkpoint host, same validator path | HTTP 404 | That host did not serve the requested route/state. A checkpoint host is not evidence of full archival support. |
| Beaconcha.in `/api/v1/epoch/388799` | HTTP 401, API key required | Access was unavailable without credentials. An epoch summary would also need its measurement and snapshot timing verified before substituting for the exact slot series. |

These failures document unavailable access, not zero staking. No provider account was created and no paid source was purchased.

The [Ethereum Beacon API specification](https://github.com/ethereum/beacon-APIs) defines state-validator access. The [Ethereum client checkpoint directory](https://eth-clients.github.io/checkpoint-sync-endpoints/) identifies checkpoint services, which should not be confused with historical state archives. Execution-layer archive RPC access alone is also insufficient for the required consensus state.

## Exact measurement and practical collection

The ETH series sums `effective_balance` for `active_ongoing`, `active_exiting` and `active_slashed` validators at each configured 12:00 UTC slot. Validator counts multiplied by 32 ETH, deposit-contract balances, actual validator balances and daily/epoch averages do not satisfy this definition.

Add the provider URL only to the local `.env` file:

```dotenv
ETH_BEACON_ARCHIVE_API_URL=https://your-consensus-archive-endpoint
```

Then run the small historical access check:

```bash
python -m src.pipeline.crypto_h4_eth_stake --repo . --check-history
```

It checks the study start, midpoint and end using a single validator per request. Output reports only the hostname, dates and sanitized errors. A passing check proves limited historical access, not a complete dataset or an affordable bulk download.

Full validator snapshots can be large. Confirm provider limits, response sizes, storage needs and any charges before requesting all 362 dates. Only after that operational review should the full collector run:

```bash
python -m src.pipeline.crypto_h4_eth_stake --repo . --start 2025-08-25 --end 2026-08-21
python -m src.pipeline.crypto_h4_analysis_readiness --repo .
python -m src.pipeline.crypto_h4_estimation --repo .
```

An exact historical export could be considered instead, but source definitions, timestamps, validator-status coverage and provenance must be reconciled before adding an import adapter. We have not approved a weaker measure or a changed window.

## Analysis limits established before estimation

The BTC-return control is common across all assets on a given date and is absorbed by date fixed effects. The estimator therefore fits lagged staked share and log market capitalization after asset/date demeaning; it does not assign a separate coefficient to the absorbed return control.

Five asset clusters yield 32 Rademacher sign assignments, with a two-sided p-value resolution of 0.0625 in nondegenerate cases. Only two assets contribute positive stake. Exhaustive enumeration does not guarantee valid finite-sample inference. Three outcome tests receive Benjamini–Hochberg correction and must be interpreted together.

Trading volume divided by capitalization is a turnover proxy, not executable liquidity. ETH effective consensus weight and BNB validator-pool stake are chain-specific measurements, and neither captures all economically unavailable supply. Liquid-staking instruments can also leave staked exposure tradeable. H4 will remain an exploratory association test even when its input is complete.

Staked share and turnover both depend on capitalization-based denominators, albeit with a lag for the predictor. This can contribute to an observed association and is another reason a coefficient cannot establish a causal effect on liquidity.

## Decision needed

Provide a working consensus archive endpoint or a provenance-backed exact export. If access requires purchasing a plan, the researcher must choose and authorize that source. The estimator is implemented; the empirical hypothesis remains unestimated until this input is resolved.

Current machine-readable status: [H4 estimation readiness and result](../../data/processed/02_valuation/crypto_h4_estimation.json). Current generated explanation: [H4 estimation note](crypto-h4-estimation.md).
