from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .historical import coverage_record, merge_rows, read_csv, write_rows
from .registry import load_json, sha256, validate_asset_config


BASE_URL = "https://api.coinpaprika.com/v1"


def request_json(url: str, retries: int = 4) -> Any:
    headers = {"Accept": "application/json", "User-Agent": "digital-assets-valuation-research/0.1"}
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def historical_url(base_url: str, provider_id: str, start: date, end: date) -> str:
    query = urllib.parse.urlencode({"start": start.isoformat(), "end": end.isoformat(), "interval": "1d", "quote": "usd"})
    return f"{base_url.rstrip('/')}/tickers/{urllib.parse.quote(provider_id)}/historical?{query}"


def normalize_daily(payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for item in payload:
        timestamp = item.get("timestamp")
        if not isinstance(timestamp, str):
            continue
        day = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(timezone.utc).date().isoformat()
        rows[day] = {
            "date": day,
            "price_usd": item.get("price"),
            "market_cap_usd": item.get("market_cap"),
            "volume_24h_usd": item.get("volume_24h"),
        }
    return [rows[day] for day in sorted(rows)]


def resolve_provider_ids(assets: list[dict[str, Any]], coins: list[dict[str, Any]]) -> tuple[dict[str, str], dict[str, str]]:
    active = [coin for coin in coins if coin.get("is_active", True)]
    resolved: dict[str, str] = {}
    unresolved: dict[str, str] = {}
    for asset in assets:
        explicit = asset.get("coinpaprika_id")
        if explicit:
            resolved[asset["asset_id"]] = explicit
            continue
        symbol = asset["symbol"].upper()
        candidates = [coin for coin in active if str(coin.get("symbol", "")).upper() == symbol]
        exact_name = [coin for coin in candidates if str(coin.get("name", "")).casefold() == asset["name"].casefold()]
        selected = exact_name if exact_name else candidates
        if len(selected) == 1 and selected[0].get("id"):
            resolved[asset["asset_id"]] = selected[0]["id"]
        else:
            unresolved[asset["asset_id"]] = "ambiguous" if selected else "not_found"
    return resolved, unresolved


def collect(repo: Path, start: date, end: date, asset_ids: set[str] | None = None, force: bool = False, base_url: str = BASE_URL) -> dict[str, Any]:
    assets = validate_asset_config(load_json(repo / "config" / "assets.json"))
    if asset_ids:
        unknown = asset_ids - {asset["asset_id"] for asset in assets}
        if unknown:
            raise ValueError(f"unknown asset ids: {sorted(unknown)}")
        assets = [asset for asset in assets if asset["asset_id"] in asset_ids]

    raw_root = repo / "data" / "raw" / "coinpaprika"
    coins_path = raw_root / "coins.json"
    if coins_path.exists() and not force:
        coins = load_json(coins_path)
    else:
        coins = request_json(f"{base_url.rstrip('/')}/coins")
        raw_root.mkdir(parents=True, exist_ok=True)
        coins_path.write_text(json.dumps(coins, separators=(",", ":")) + "\n", encoding="utf-8")

    resolved, unresolved = resolve_provider_ids(assets, coins)
    all_rows: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    provider_errors: dict[str, str] = {}
    for asset in assets:
        provider_id = resolved.get(asset["asset_id"])
        if not provider_id:
            continue
        raw_path = raw_root / asset["asset_id"] / f"{start.isoformat()}_{end.isoformat()}.json"
        if raw_path.exists() and not force:
            payload = load_json(raw_path)
        else:
            try:
                payload = request_json(historical_url(base_url, provider_id, start, end))
            except urllib.error.HTTPError as exc:
                provider_errors[asset["asset_id"]] = f"http_{exc.code}"
                continue
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
            metadata = {
                "asset_id": asset["asset_id"], "provider": "coinpaprika", "provider_id": provider_id,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "start": start.isoformat(),
                "end": end.isoformat(), "sha256": sha256(raw_path),
            }
            raw_path.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            time.sleep(0.25)
        rows = normalize_daily(payload)
        all_rows.extend({"asset_id": asset["asset_id"], **row} for row in rows)
        record = coverage_record(asset["asset_id"], rows, start, end)
        record.update({
            "provider": "coinpaprika", "provider_id": provider_id,
            "market_cap_days": sum(isinstance(row.get("market_cap_usd"), (int, float)) for row in rows),
            "volume_days": sum(isinstance(row.get("volume_24h_usd"), (int, float)) for row in rows),
        })
        coverage.append(record)

    out = repo / "data" / "processed" / "historical"
    daily_path = out / "market_daily_coinpaprika.csv"
    coverage_path = out / "market_coverage_coinpaprika.csv"
    all_rows = merge_rows(read_csv(daily_path), all_rows, ("asset_id", "date"))
    coverage = merge_rows(read_csv(coverage_path), coverage, ("asset_id", "start_date", "end_date"))
    write_rows(daily_path, all_rows, ["asset_id", "date", "price_usd", "market_cap_usd", "volume_24h_usd"])
    write_rows(coverage_path, coverage, ["asset_id", "provider", "provider_id", "start_date", "end_date", "expected_days", "observed_days", "price_days", "market_cap_days", "volume_days", "coverage_ratio", "price_coverage_ratio", "longest_missing_run_days", "status"])
    mapping_path = out / "coinpaprika_identifier_audit.csv"
    with mapping_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["asset_id", "coinpaprika_id", "status"])
        writer.writeheader()
        for asset in assets:
            asset_id = asset["asset_id"]
            writer.writerow({"asset_id": asset_id, "coinpaprika_id": resolved.get(asset_id, ""), "status": "resolved" if asset_id in resolved else unresolved[asset_id]})
    observed_days = sum(int(row["observed_days"]) for row in coverage)
    market_cap_days = sum(int(row["market_cap_days"]) for row in coverage)
    volume_days = sum(int(row["volume_days"]) for row in coverage)
    findings = repo / "research" / "findings" / "free-market-data-coverage.md"
    findings.parent.mkdir(parents=True, exist_ok=True)
    findings.write_text(
        f"""# Free Market-Data Coverage — CoinPaprika

- Requested window: {start.isoformat()} through {end.isoformat()}.
- Universe: {len(assets)} assets; {len(resolved)} provider IDs resolved.
- Daily observations: {observed_days:,}.
- Non-null reported market-cap observations: {market_cap_days:,}.
- Non-null 24-hour-volume observations: {volume_days:,}.
- Unresolved identifiers: {', '.join(sorted(unresolved)) or 'None'}.

CoinPaprika's no-key plan is a rolling one-year source. This panel supports recent-period estimation and cross-source checks, but it does not satisfy the full 2019–2026 window. Provider-reported market cap is retained as reported and is not reconstructed from price.
""",
        encoding="utf-8",
    )
    return {
        "requested_assets": len(assets), "resolved_assets": len(resolved), "unresolved": unresolved,
        "provider_errors": provider_errors, "coverage_records": len(coverage),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect the free rolling CoinPaprika daily market panel")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--asset-id", action="append", dest="asset_ids")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    print(json.dumps(collect(args.repo.resolve(), args.start, args.end, set(args.asset_ids or []), args.force), indent=2))


if __name__ == "__main__":
    main()
