# H5-H7 Preregistration — Draft 0.1-draft

**Status:** `draft_not_frozen`. This document is not yet a frozen preregistration and must not be described as one.

## Scope and sample

The analysis uses USD-target stablecoins in the frozen pilot universe from 2019-01-01 through 2026-08-22. PAXG is excluded because its reference asset is gold. USTC is excluded from primary models and retained as a failure-control robustness case. The unresolved USDG observation on 2025-01-30 is withheld unless independently confirmed before freezing.

## Primary peg definitions

- Continuous outcome: `log1p(absolute_peg_error_bps)`.
- Breach outcome: strictly outside ±50 bps.
- Recovery: at or inside ±25 bps.
- Robustness bands: 10, 25, 100, 500 bps.
- Calendar gaps right-censor open episodes.

## Temporal integrity

Design scores and explanatory variables may only be used when their evidence/effective date is known. Current 2026 design scores are not backfilled into earlier history. Partial risk scores are diagnostic only and prohibited from headline models.

## Model families

- H5: reserve quality versus peg error, breaches, severity, and recovery.
- H6: redemption friction versus the same outcomes, including stress interactions.
- H7: supply, market share, liquidity, integrations, and usage.

Two exact-date shares are implemented: `pilot_observed_supply_share` and `global_peggedusd_supply_share`. The latter uses DeFiLlama's source-audited `totalCirculatingUSD.peggedUSD` denominator. It may be described only as DeFiLlama global pegged-USD supply share, not as a share of every stable-value asset. Current order-book and yield-integration snapshots remain developmental proxies until their historical and identifier-validation gates pass. Coin Metrics usage histories cover four assets only, and active addresses must not be labeled unique users.

## Current readiness

- **H5:** `temporal_overlap_ready_8_assets_targeted_review_and_additional_historical_score_dates_pending`
- **H6:** `temporal_overlap_ready_8_assets_targeted_review_pending`
- **H7:** `primary_14_asset_supply_share_ready_exploratory_4_asset_usage_ready_historical_depth_and_validated_integrations_pending`

## Gates required before estimation

- **H5:** point-in-time reserve scores for at least 8 primary assets; second-coder review complete; at least two score dates per asset where time variation is claimed
- **H6:** strict redemption-friction scores for at least 8 primary assets; point-in-time evidence; second-coder review complete
- **H7:** daily supply coverage gate passed; pilot-share denominator constructed; DeFiLlama global pegged-USD denominator source-audited; market-depth and integration variables source-audited; four-asset usage subsample fixed before estimation and labeled exploratory

## Inference and robustness

Primary panel models include asset and calendar-time fixed effects where identified. Standard errors are clustered by asset and date where supported. Hypothesis-family p-values receive Benjamini-Hochberg adjustment. Verified peg outcomes are not winsorized in primary analysis; unverified provider anomalies may only be withheld through a documented pre-estimation review rule.
