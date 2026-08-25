# Stablecoin Transaction-Activity Coverage

- Primary stablecoins evaluated: 14.
- Stablecoins supported by the free Coin Metrics asset-metrics source: 4.
- Assets passing the 95% active-window metric-coverage gate: 4.
- Daily asset observations collected: 10,856.
- Requested window: 2019-01-01 through 2026-08-24.
- Status: `partial_asset_coverage_not_full_h7_sample_ready`.

The free source currently supports USDT, USDC, DAI, and TUSD for `AdrActCnt`, `TxCnt`, and `TxTfrCnt`. Active addresses are ledger addresses, not unique people or customers; one person may control many addresses and custodial addresses may represent many users. Provider asset-level definitions must not be silently interpreted as complete chain-by-chain settlement activity. The ten unsupported primary assets remain explicit, so these fields cannot yet satisfy the full-sample H7 transaction/user gate.
