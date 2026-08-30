# Digital Assets Valuation

Research and development repository for an NYU Financial Engineering master's project on the economic design, valuation, adoption, and risk of digital assets.

## Research objective

Build a reproducible economic taxonomy of stablecoins and cryptocurrencies, translate token design into measurable variables, and test whether usage, value-accrual mechanisms, supply, liquidity, security, reserve quality, and redemption design explain valuation and risk.

## Repository layout

- `docs/` — living research notebook and methodology documents.
- `data/raw/` — immutable dated source snapshots. Never edit these files in place.
- `data/reference/` — editable classification workbooks and research codebooks.
- `research/findings/` — dated findings, selection decisions, and analytical notes.
- `research/manuscript/` — Overleaf-ready publication manuscript and BibTeX references.
- `src/artifacts/` — reproducible builders for document and workbook artifacts.
- `src/pipeline/` — data acquisition, normalization, quality-control, and panel-building code.
- `tests/` — tests for identifiers, classifications, transformations, and empirical inputs.
- `outputs/` — generated analytical tables and figures; large/reproducible outputs may be ignored by Git.

## Current pilot universe

The Phase 2 pilot contains 25 non-stable cryptoassets and 16 stable-value assets. The dated 2026-08-22 snapshot provides approximately 95.5% indicative total-market coverage using CoinGecko and DeFiLlama inputs. It also includes a limited growth sleeve and historical UST as a failure control.

## Reproducibility rules

1. Raw data is stored in dated, immutable folders with source and retrieval metadata.
2. Symbols are not primary keys; use stable internal IDs and chain-qualified contract addresses.
3. Design classifications are effective-dated and retain evidence URLs, coder, reviewer, and confidence.
4. Unknown values remain null. A zero means the field was reviewed and the criterion was not met.
5. Every analytical table must be reproducible from frozen raw inputs and version-controlled transformations.
6. Market snapshots, issuer terms, protocol designs, and legal rights are treated as time-varying.

## Current checkpoint and immediate workstream

The project has reached an **expanded point-in-time design-evidence and exploratory-estimation pilot**. The stablecoin scorecard has temporally valid post-score outcomes for eight assets. The first non-stable crypto tranche covers six assets and four prioritized value-accrual codes: 22 of 24 decisions are verified, leaving only BNB monetary and collateral status unresolved. The six-code H8 extension verifies all 36 gas, staking, scarcity, governance, utility, and incentive decisions with no verified conflicts against the corrected design matrix. H2's burn/protocol-capture fields are complete, its fee-scope sensitivities are predeclared, and its estimator diagnostics pass with small-sample limits. Guarded H2 point estimates, leave-one-asset-out sensitivities, and exhaustive wild-cluster tests are reproducible. The fee-capture interaction is positive in every predeclared specification, but no wild-cluster result rejects zero at 10%; the pooled market-cap result is closest at $p=0.156$. Full ten-code H8 breadth is available for five assets; BNB is withheld under a machine-readable blocker policy. This remains an exploratory methodology checkpoint, not a confirmatory hypothesis result.

1. Approve or revise the documented policy that retains BNB as null and excludes it from five-asset complete-case H8 estimation.
2. Freeze the H2/H8 pilot specification before adding uncertainty estimates or testing additional variants.
3. Complete the targeted stablecoin component review required for H5/H6 estimation.
4. Extend the candidate panels beyond the current 89-day market window using reproducible free sources.
5. Add horizon-robust and small-cluster inference, then run the preregistered sensitivity checks.

## Run the current pipeline

From the repository root:

```bash
python -m unittest discover -s tests -v
python -m src.pipeline.registry --repo . --snapshot-date 2026-08-22
python -m src.pipeline.historical --repo . --start 2026-07-24 --end 2026-08-22 --asset-id crypto_btc
python -m src.pipeline.llama_history --repo . --start 2019-01-01 --end 2026-08-22
python -m src.pipeline.stablecoin_supply --repo . --start 2019-01-01 --end 2026-08-22
python -m src.pipeline.stablecoin_global_market --repo . --start 2019-01-01 --end 2026-08-22
python -m src.pipeline.source_availability --repo .
python -m src.pipeline.stablecoin_risk --repo .
python -m src.pipeline.stablecoin_evidence --repo .
python -m src.pipeline.stablecoin_scorecard --repo .
python -m src.pipeline.stablecoin_score_intervals --repo .
python -m src.pipeline.h5_h6_readiness --repo .
python -m src.pipeline.crypto_economic_design --repo .
python -m src.pipeline.crypto_design_evidence --repo .
python -m src.pipeline.crypto_fundamentals --repo . --start 2026-07-24 --end 2026-08-22
python -m src.pipeline.crypto_collateral --repo . --start 2026-05-25 --end 2026-08-22
python -m src.pipeline.aave_collateral_state --repo . --start 2026-05-25 --end 2026-08-22
python -m src.pipeline.crypto_monetary --repo .
python -m src.pipeline.crypto_mechanism_state --repo .
python -m src.pipeline.crypto_h2_h8_readiness --repo .
python -m src.pipeline.crypto_fee_fundamentals --repo . --start 2026-05-25 --end 2026-08-21
python -m src.pipeline.crypto_h2_pilot_panel --repo .
python -m src.pipeline.crypto_h2_estimator_diagnostics --repo .
python -m src.pipeline.crypto_h2_exploratory_estimates --repo .
python -m src.pipeline.crypto_h2_small_cluster_inference --repo .
python -m src.pipeline.crypto_evidence_blockers --repo .
python -m src.pipeline.crypto_h8_evidence_plan --repo .
python -m src.pipeline.checkpoint_readiness --repo .
python -m src.pipeline.coinpaprika_market --repo . --start 2025-08-25 --end 2026-08-22
python -m src.pipeline.cryptocompare_volume --repo . --start 2019-01-01 --end 2026-08-22
python -m src.pipeline.binance_klines --repo . --start 2019-01-01 --end 2026-08-22
python -m src.pipeline.stablecoin_panel --repo . --breach-bps 50 --recovery-bps 25
python -m src.pipeline.stablecoin_atlas --repo .
python -m src.pipeline.preregistration --repo .
python -m src.pipeline.stablecoin_adoption --repo .
python -m src.pipeline.stablecoin_chain_distribution --repo .
python -m src.pipeline.stablecoin_trading_activity --repo .
python -m src.pipeline.binance_stablecoin_depth --repo .
python -m src.pipeline.defillama_yield_integrations --repo .
python -m src.pipeline.coinmetrics_stablecoin_usage --repo . --start 2019-01-01 --end 2026-08-24
python -m src.pipeline.stablecoin_usage_panel --repo .
python -m src.pipeline.h7_readiness --repo .
```

The registry command validates the asset configuration and frozen raw snapshots, records SHA-256 hashes, and writes the identifier registry and cross-sectional coverage audit to `data/processed/2026-08-22/`. It also writes a readable audit note to `research/findings/`.

The historical command performs a bounded example pull. The collector chunks long requests, caches immutable raw responses and retrieval metadata, normalizes data to UTC dates, merges incremental runs without discarding earlier assets, and writes daily data plus a missingness report to `data/processed/historical/`. Set `COINGECKO_API_KEY` when the selected CoinGecko plan requires authenticated historical access.

For local authenticated APIs, copy `.env.example` to `.env` and add keys there. The CoinGecko historical collector loads the repository `.env` automatically; existing shell environment variables take precedence. `.env` is excluded from Git and must never contain credentials intended for sharing.

The DeFiLlama fallback command builds the long daily-price history when early CoinGecko access is unavailable. It uses one asset per provider request, yearly cache partitions, nearest-UTC-day normalization, and active-window coverage diagnostics. It supplies price only; historical market capitalization, volume, and circulating supply remain separate data workstreams.

The stablecoin-supply command collects DeFiLlama `circulating.peggedUSD` histories for supported assets. The source-availability command produces the explicit metric-by-asset matrix showing which histories are implemented or still blocked.

The stablecoin-risk command validates evidence-linked component inputs and calculates strict reserve-quality, transparency, and redemption-friction scores. Strict composites are withheld when any required component is unknown.

The stablecoin-evidence command enforces the focused eight-asset H5/H6 evidence plan and separates source discovery from verified point-in-time extraction. Verified, dated summaries and reconstructible locators live in `config/stablecoin_evidence_extractions.json`; the command audits five required evidence classes per asset and prohibits treating an undated or merely discovered source as score-ready evidence.

The stablecoin-scorecard command applies a versioned 0--4 ordinal rubric to the five verified evidence classes and produces an eight-asset point-in-time scorecard. It validates that every component has matching dated evidence, reports confidence, and keeps developmental design scores distinct from estimated H5/H6 results.

The stablecoin-score-intervals command combines current scores with independently evidenced historical intervals, validates source availability and non-overlap, and prohibits gaps between explicitly consecutive regimes for the same asset.

The H5-H6 readiness command generates a blind, 40-row targeted component-review worksheet and audits temporal overlap between score dates and peg outcomes. It explicitly blocks retrospective use of later design scores, preventing look-ahead bias before model estimation.

The crypto-economic-design command validates the provisional ten-code value-accrual matrix against the frozen 25-asset non-stable universe. It creates an asset-level H2/H8 profile and a blind 250-decision review worksheet; provisional classifications cannot be treated as frozen research inputs until evidence-backed review is complete.

The crypto-design-evidence command audits the first prioritized H2/H8 evidence tranche. It requires a complete asset-code grid, dated HTTPS sources, binary values only for verified decisions, and explicit nulls for unresolved quantitative or mechanism tests.

The crypto-fundamentals command collects the Coin Metrics Community fields confirmed to be free: daily addresses, transactions, transfer count, market capitalization, and supply for the first evidence tranche. Coverage is audited per metric; activity supplies at most one `VA_MONETARY` behavioral test and never substitutes for separate acceptance or holding evidence. Adjusted transfer value, fees, and issuance are explicitly reported as unavailable on this free tier.

The crypto-collateral command screens exact token balances across a named eight-protocol, chain-relevant lending sample against the preregistered 1%-of-market-cap or $100m-for-90-days rule. Every selected protocol must cover the full window before a below-threshold result can support zero. DeFiLlama supplied-token TVL remains a screening proxy: a passing asset still requires effective-dated proof that the balance was collateral-enabled before `VA_COLLATERAL=1` can be frozen.

The Aave collateral-state command resolves daily Ethereum blocks and performs historical read-only `Pool.getConfiguration` calls for WBTC and WETH. Eligibility passes only when LTV is positive, the reserve is active, and it is not paused on every day of the 90-day materiality window; raw RPC responses and hashes are archived.

The crypto-monetary command implements the two-test `VA_MONETARY` rule: 90 days of material address/transaction activity plus independent, dated primary evidence of monetary or payment design. Missing provider data and failure of this pilot screen remain unresolved rather than being converted into negative classifications.

The crypto-mechanism-state command resolves burn and protocol-capture classifications from effective-dated activation, pause, and deactivation events. The latest event known by the observation date must match the design matrix; promised, paused, or inactive mechanisms remain zero.

The crypto-H2/H8-readiness command creates a six-asset pilot design panel without filling unevidenced fields from the provisional matrix. H2 capture is released only when burn and protocol capture are verified; H8 breadth stays null until all ten value-accrual codes are verified.

The crypto-fee-fundamentals command archives DeFiLlama's free daily fees, protocol revenue, and holder revenue for six associated economic systems. Coverage is chain-level for BTC, ETH, BNB, and ARB but application-level for UNI and AAVE; these scopes are retained explicitly, and the three accounting concepts are never treated as interchangeable.

The crypto-H2-pilot-panel command joins six-asset CoinPaprika market outcomes, four-asset Coin Metrics activity, free fee/revenue histories, and effective-dated capture events without backfilling later classifications. Exact one-day explanatory lags and exact seven-day forward returns preserve gaps. The candidate H2 panel now carries an application-scope indicator and predeclared pooled, chain-only, application-only, and leave-one-asset-out sensitivities. Pilot inference remains exploratory because six asset clusters are too few for conventional clustered asymptotics.

The crypto-H2-estimator-diagnostics command audits usable observations, within-asset fee variation, two-way fixed-effect design rank, scope representation, and every leave-one-asset-out sample without estimating hypothesis coefficients. A pass establishes computational feasibility only; the two-asset application scope remains descriptive and the six-cluster pilot remains exploratory.

The crypto-H2-exploratory-estimates command produces guarded two-way fixed-effect point estimates for the predeclared pooled and chain-only market-cap and forward-return specifications. It reports within-fit and leave-one-asset-out sensitivity but intentionally omits standard errors and p-values at the six-cluster pilot stage.

The crypto-H2-small-cluster-inference command adds CR1 asset-clustered statistics and exhaustively enumerates every Rademacher wild-cluster assignment under the zero-interaction null. Six-cluster tests have 64 assignments and four-cluster tests only 16, so attainable p-values are coarse; overlapping forward-return results remain exploratory pending horizon-robust inference.

The crypto-evidence-blockers command reconciles a machine-readable blocker manifest to the unresolved evidence grid. It documents the exact evidence required to resolve BNB monetary and collateral classifications and enforces a five-asset complete-case H8 policy while those fields remain null.

The crypto-H8-evidence-plan command formalizes positive, negative, and source requirements for gas, staking, scarcity, governance, utility, and incentive classifications. Two independently validated evidence tranches verify all 36 decisions, correct BNB governance, UNI incentive, and AAVE utility classifications, reject duplicate tranche decisions, and audit agreement with the design matrix. Full H8 breadth remains unavailable for BNB until its monetary and collateral fields in the focused four-code tranche are resolved.

The checkpoint-readiness command reconciles the stablecoin and crypto evidence outputs, lists every unresolved pilot decision, enforces missingness and temporal guardrails, and writes a single machine-readable checkpoint. A passing checkpoint means the methodology increment is safe to commit; it does not mean H2/H8 or H5/H6 are ready for final estimation.

The CoinPaprika command builds a no-key, rolling recent-market panel containing daily price, reported market capitalization, and 24-hour volume. CoinPaprika's free tier exposes only the latest year of daily history, so this source is a recent-period and cross-source-validation layer rather than a substitute for the full 2019–2026 market-cap panel. Identifier ambiguity is surfaced in a separate audit and never resolved by symbol alone when multiple active candidates exist.

The CryptoCompare command builds a paginated 2019–2026 daily OHLCV panel for verified non-stable crypto symbols. Its `volume_quote_usd` field is CCCAGG pair volume converted to USD, not total global spot volume and not directly interchangeable with CoinPaprika's reported 24-hour volume. Provider zero-padding before an asset's observed history is discarded.

The Binance command uses the official keyless market-data host and records venue-specific daily candles, quote volume, trade counts, and taker volume for active USDT/USDC/FDUSD spot pairs. Quote-stablecoin units are retained as such and are not silently relabeled as exact USD.

The stablecoin-panel command joins the long daily price panel to supported circulation histories and strict design scores, calculates peg-error and threshold variables, and produces a daily depeg-event table. PAXG is excluded because a gold benchmark is required. Missing calendar days censor open episodes instead of being bridged.

The stablecoin-atlas command produces asset-level peg statistics, band-robustness rates, episode rankings, monthly stress concentration, an explicit extreme-observation review queue, and a reproducible SVG summary chart. USTC remains visible as a failure control but is excluded from primary-sample rankings.

The preregistration command validates and renders the machine-readable H5-H7 draft and records checksums for its current analytical inputs. The draft contains explicit readiness gates and remains labeled `draft_not_frozen` until point-in-time design evidence, second-coder review, and remaining H7 inputs are complete.

The stablecoin-global-market command archives and normalizes DeFiLlama's free aggregate `totalCirculatingUSD.peggedUSD` history without interpolation. The stablecoin-adoption command then constructs exact-date supply growth, pilot concentration, within-pilot share, and DeFiLlama global pegged-USD share. This denominator does not represent non-USD-pegged stable-value assets.

The stablecoin-chain-distribution command extracts daily chain balances already preserved in DeFiLlama raw histories and calculates chain breadth, concentration, effective chain count, and top-chain share. These are cross-chain distribution proxies, not transaction usage or protocol-integration counts.

The stablecoin-trading-activity command joins the recent CoinPaprika volume panel to supply and peg outcomes and calculates volume-to-supply turnover. It is a recent reported trading-activity proxy, not order-book liquidity or settlement usage.

The Binance stablecoin-depth command archives keyless spot order-book snapshots and measures quoted spread, executable bid/ask depth within 10/25/50 bps, and simulated price impact for 100,000 and 1,000,000 anchor-unit trades. Quote-oriented pairs are algebraically inverted into the target stablecoin's perspective. These are venue-specific point-in-time observations; repeated snapshots are required before they can enter H7 panel estimation.

The DeFiLlama yield-integrations command archives the current free yield-pool universe and constructs conservative exact-symbol-component counts of pools, projects, and chains for each primary stablecoin. It is a cross-sectional yield-integration proxy—not an exhaustive or historical protocol-integration measure—and gross matched-pool TVL is not token-specific TVL.

The Coin Metrics stablecoin-usage command collects free daily active-address, ledger-transaction, and token-transfer metrics for explicitly supported provider assets and emits a full 14-asset coverage audit. Active addresses are not unique users, and unsupported assets remain null rather than being inferred from chain-level totals.

The stablecoin usage-panel command applies the fixed two-tier H7 design: all 14 coverage-qualified assets remain in the primary supply/share specification, while USDT, USDC, DAI, and TUSD enter a separate exploratory usage panel with exact one-day lags. The usage subsample cannot replace or determine the primary sample.

The H7-readiness command constructs the lagged recent joined panel, variable-by-asset coverage matrix, objective sample gate, and pass/fail readiness report. It does not declare H7 ready while market depth, integrations, and usage remain unsourced.

This repository is for academic research. Classifications are not legal conclusions or investment recommendations.
