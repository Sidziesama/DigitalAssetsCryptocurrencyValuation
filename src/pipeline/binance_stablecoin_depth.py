from __future__ import annotations

import argparse
import json
import math
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .binance_klines import BASE_URL, request_json
from .historical import merge_rows, read_csv, write_rows
from .registry import load_json, sha256, validate_asset_config


BANDS_BPS = (10, 25, 50)
TRADE_SIZES = (100_000, 1_000_000)
ANCHORS = ("USDT", "USDC", "FDUSD")


def select_pairs(assets: list[dict[str, Any]], exchange_info: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    active = [row for row in exchange_info.get("symbols", []) if row.get("status") == "TRADING"]
    resolved: dict[str, dict[str, Any]] = {}
    unresolved: dict[str, str] = {}
    for asset in assets:
        target = asset["symbol"].upper()
        candidates = []
        for row in active:
            base, quote = row.get("baseAsset"), row.get("quoteAsset")
            if base == target and quote in ANCHORS and quote != target:
                candidates.append((0, ANCHORS.index(quote), row, True, quote))
            elif quote == target and base in ANCHORS and base != target:
                candidates.append((1, ANCHORS.index(base), row, False, base))
        candidates.sort(key=lambda item: (item[0], item[1], item[2]["symbol"]))
        if candidates:
            _, _, row, target_is_base, anchor = candidates[0]
            resolved[asset["asset_id"]] = {"pair": row["symbol"], "target_is_base": target_is_base, "anchor_asset": anchor}
        else:
            unresolved[asset["asset_id"]] = "no_active_binance_pair_against_usdt_usdc_or_fdusd"
    return resolved, unresolved


def depth_url(base_url: str, symbol: str, limit: int = 1000) -> str:
    return f"{base_url.rstrip('/')}/depth?{urllib.parse.urlencode({'symbol': symbol, 'limit': limit})}"


def transform_book(payload: dict[str, Any], target_is_base: bool) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    def levels(name: str) -> list[tuple[float, float]]:
        output = []
        for item in payload.get(name, []):
            try:
                price, quantity = float(item[0]), float(item[1])
            except (TypeError, ValueError, IndexError):
                continue
            if price > 0 and quantity > 0:
                output.append((price, quantity))
        return output

    bids, asks = levels("bids"), levels("asks")
    if target_is_base:
        return sorted(bids, reverse=True), sorted(asks)
    # Invert a BASE/TARGET book into TARGET/BASE. Original asks become target bids.
    target_bids = [(1 / price, price * quantity) for price, quantity in asks]
    target_asks = [(1 / price, price * quantity) for price, quantity in bids]
    return sorted(target_bids, reverse=True), sorted(target_asks)


def execution(levels: list[tuple[float, float]], target_quantity: float) -> tuple[float | None, float]:
    remaining, anchor_value = target_quantity, 0.0
    for price, available in levels:
        filled = min(remaining, available)
        anchor_value += filled * price
        remaining -= filled
        if remaining <= 1e-12:
            return anchor_value / target_quantity, 1.0
    filled_total = target_quantity - remaining
    return (anchor_value / filled_total if filled_total > 0 else None), (filled_total / target_quantity if target_quantity > 0 else 0)


def analyze(payload: dict[str, Any], target_is_base: bool) -> dict[str, Any]:
    bids, asks = transform_book(payload, target_is_base)
    if not bids or not asks:
        raise ValueError("order book has no valid two-sided levels")
    best_bid, best_ask = bids[0][0], asks[0][0]
    mid = (best_bid + best_ask) / 2
    result: dict[str, Any] = {
        "best_bid_anchor_per_target": best_bid, "best_ask_anchor_per_target": best_ask,
        "mid_anchor_per_target": mid, "quoted_spread_bps": 10_000 * (best_ask - best_bid) / mid,
    }
    for band in BANDS_BPS:
        bid_floor = mid * (1 - band / 10_000)
        ask_ceiling = mid * (1 + band / 10_000)
        result[f"bid_depth_{band}bps_anchor"] = sum(price * quantity for price, quantity in bids if price >= bid_floor)
        result[f"ask_depth_{band}bps_anchor"] = sum(price * quantity for price, quantity in asks if price <= ask_ceiling)
    for notional in TRADE_SIZES:
        quantity = notional / mid
        buy_vwap, buy_fill = execution(asks, quantity)
        sell_vwap, sell_fill = execution(bids, quantity)
        suffix = f"{notional // 1000}k"
        result[f"buy_impact_{suffix}_bps"] = 10_000 * (buy_vwap / mid - 1) if buy_vwap is not None and buy_fill == 1 else None
        result[f"sell_impact_{suffix}_bps"] = 10_000 * (1 - sell_vwap / mid) if sell_vwap is not None and sell_fill == 1 else None
        result[f"buy_fill_{suffix}"] = buy_fill
        result[f"sell_fill_{suffix}"] = sell_fill
    return result


def collect(repo: Path, force_exchange_info: bool = False, base_url: str = BASE_URL) -> dict[str, Any]:
    assets = [a for a in validate_asset_config(load_json(repo / "config" / "assets.json")) if a["universe"] == "stablecoin" and a["tier"] != "failure_control" and a["asset_id"] != "stable_paxg"]
    raw_root = repo / "data" / "raw" / "binance_stablecoin_depth"
    info_path = raw_root / "exchange_info.json"
    if info_path.exists() and not force_exchange_info:
        info = load_json(info_path)
    else:
        info = request_json(f"{base_url.rstrip('/')}/exchangeInfo")
        raw_root.mkdir(parents=True, exist_ok=True)
        info_path.write_text(json.dumps(info, separators=(",", ":")) + "\n", encoding="utf-8")
    resolved, unresolved = select_pairs(assets, info)
    rows = []
    for asset in assets:
        pair = resolved.get(asset["asset_id"])
        if not pair:
            continue
        retrieved = datetime.now(timezone.utc)
        stamp = retrieved.strftime("%Y%m%dT%H%M%S.%fZ")
        raw_path = raw_root / asset["asset_id"] / f"{stamp}.json"
        payload = request_json(depth_url(base_url, pair["pair"]))
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
        raw_path.with_suffix(".metadata.json").write_text(json.dumps({
            "asset_id": asset["asset_id"], **pair, "provider": "binance_spot",
            "endpoint": "/api/v3/depth", "limit": 1000,
            "retrieved_at_utc": retrieved.isoformat(), "sha256": sha256(raw_path),
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        rows.append({"asset_id": asset["asset_id"], "timestamp_utc": retrieved.isoformat(), **pair, **analyze(payload, pair["target_is_base"]), "provider": "binance_spot"})
    fields = ["asset_id", "timestamp_utc", "pair", "target_is_base", "anchor_asset", "best_bid_anchor_per_target", "best_ask_anchor_per_target", "mid_anchor_per_target", "quoted_spread_bps", *[f"{side}_depth_{band}bps_anchor" for band in BANDS_BPS for side in ("bid", "ask")], *[f"{metric}_{size // 1000}k{unit}" for size in TRADE_SIZES for metric, unit in (("buy_impact", "_bps"), ("sell_impact", "_bps"), ("buy_fill", ""), ("sell_fill", ""))], "provider"]
    out = repo / "data" / "processed" / "04_stablecoin_deferred"
    path = out / "stablecoin_market_depth_snapshots.csv"
    merged = merge_rows(read_csv(path), rows, ("asset_id", "timestamp_utc"))
    write_rows(path, merged, fields)
    audit = [{"asset_id": a["asset_id"], **resolved.get(a["asset_id"], {}), "status": "resolved" if a["asset_id"] in resolved else unresolved[a["asset_id"]]} for a in assets]
    write_rows(out / "stablecoin_market_depth_pair_audit.csv", audit, ["asset_id", "pair", "target_is_base", "anchor_asset", "status"])
    summary = {"eligible_assets": len(assets), "resolved_assets": len(resolved), "snapshot_rows_added": len(rows), "total_snapshot_rows": len(merged), "unresolved": unresolved, "readiness": "snapshot_only_not_historical_panel_ready"}
    (out / "stablecoin_market_depth_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    findings = repo / "research" / "findings" / "stablecoin-market-depth.md"
    findings.write_text(f"""# Stablecoin Market-Depth Snapshot

- Eligible primary assets: {summary['eligible_assets']}.
- Assets with an active Binance pair against USDT, USDC, or FDUSD: {summary['resolved_assets']}.
- Snapshot rows added: {summary['snapshot_rows_added']}.
- Status: `{summary['readiness']}`.

The collector preserves the raw top 1,000 order-book levels and calculates quoted spread, executable bid and ask depth within 10/25/50 bps, and simulated 100,000 and 1,000,000 anchor-unit market-order price impact. Impact is null when the archived book cannot fully execute the hypothetical trade. Metrics are venue-specific and point-in-time. They cannot enter the H7 daily panel until repeated snapshots meet a preregistered time-coverage threshold. Unsupported assets remain explicit in `stablecoin_market_depth_pair_audit.csv`; no pair is inferred from symbol alone.
""", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect keyless Binance stablecoin order-book snapshots")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--force-exchange-info", action="store_true")
    args = parser.parse_args()
    print(json.dumps(collect(args.repo.resolve(), args.force_exchange_info), indent=2))


if __name__ == "__main__":
    main()
