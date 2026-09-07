# Stablecoin Market-Depth Snapshot

- Eligible primary assets: 14.
- Assets with an active Binance pair against USDT, USDC, or FDUSD: 9.
- Snapshot rows added: 9.
- Status: `snapshot_only_not_historical_panel_ready`.

The collector preserves the raw top 1,000 order-book levels and calculates quoted spread, executable bid and ask depth within 10/25/50 bps, and simulated 100,000 and 1,000,000 anchor-unit market-order price impact. Impact is null when the archived book cannot fully execute the hypothetical trade. Metrics are venue-specific and point-in-time. They cannot enter the H7 daily panel until repeated snapshots meet a preregistered time-coverage threshold. Unsupported assets remain explicit in `stablecoin_market_depth_pair_audit.csv`; no pair is inferred from symbol alone.
