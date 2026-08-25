# H7 Coverage and Readiness Checkpoint

- Status: `partial_not_analysis_ready`.
- Recent common window: 2025-08-25 through 2026-08-21.
- Assets evaluated: 14.
- Proposed recent sample at 80% complete-row coverage: 14 assets.
- Complete joined rows: 5,005 of 5,068.

## Gates

- **pilot_supply_and_share:** `pass`
- **chain_distribution_proxy:** `pass`
- **recent_trading_activity_proxy:** `pass_recent_window_only`
- **global_peggedusd_market_share:** `pass`
- **market_depth_spread_price_impact:** `fail_snapshot_only_insufficient_time_coverage`
- **protocol_integration_count:** `fail_cross_sectional_yield_proxy_only`
- **transaction_volume_and_users:** `pass_exploratory_four_asset_subsample_only`

The 14-asset joined panel is suitable for primary supply/share specification development. Coin Metrics usage histories are preregistered separately as an exploratory USDT/USDC/DAI/TUSD subsample and do not shrink or determine the primary sample. H7 is not headline-analysis ready because depth and integration snapshots lack historical coverage and yield matches require contract validation. Active addresses are not unique users. Chain predictors and trading activity are lagged by one exact calendar day; missing lag dates remain null.
