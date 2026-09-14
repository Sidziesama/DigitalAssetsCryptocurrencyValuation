from __future__ import annotations

import argparse
import json
import urllib.parse
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .historical import read_csv, request_json, write_rows
from .registry import load_json, sha256, validate_asset_config


BASE_URL = "https://community-api.coinmetrics.io/v4"
METRICS = ("AdrActCnt", "TxCnt", "TxTfrCnt")
FIELD_MAP = {"AdrActCnt": "active_addresses", "TxCnt": "ledger_transaction_count", "TxTfrCnt": "token_transfer_count"}


def timeseries_url(base_url: str, provider_id: str, start: date, end: date) -> str:
    query = urllib.parse.urlencode({
        "assets": provider_id, "metrics": ",".join(METRICS), "frequency": "1d",
        "start_time": start.isoformat(), "end_time": end.isoformat(), "page_size": 10000,
    })
    return f"{base_url.rstrip('/')}/timeseries/asset-metrics?{query}"


def normalize(asset_id: str, provider_id: str, payload: dict[str, Any], start: date, end: date) -> list[dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for item in payload.get("data", []):
        try:
            day = date.fromisoformat(str(item["time"])[:10])
        except (KeyError, ValueError, TypeError):
            continue
        if not start <= day <= end or item.get("asset") != provider_id:
            continue
        row: dict[str, Any] = {"asset_id": asset_id, "date": day.isoformat(), "coinmetrics_asset": provider_id, "provider": "coinmetrics_community"}
        for metric, field in FIELD_MAP.items():
            value = item.get(metric)
            try:
                row[field] = float(value) if value is not None else None
            except (TypeError, ValueError):
                row[field] = None
        output[day.isoformat()] = row
    return [output[key] for key in sorted(output)]


def coverage(asset_id: str, provider_id: str | None, rows: list[dict[str, Any]], start: date, end: date) -> dict[str, Any]:
    dates = sorted(date.fromisoformat(row["date"]) for row in rows)
    first = dates[0] if dates else None
    expected = (end - first).days + 1 if first else 0
    result: dict[str, Any] = {
        "asset_id": asset_id, "coinmetrics_asset": provider_id, "supported": int(provider_id is not None),
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "first_observed_date": first.isoformat() if first else None,
        "last_observed_date": dates[-1].isoformat() if dates else None,
        "active_window_expected_days": expected, "observed_days": len(dates),
    }
    metric_ratios = []
    for field in FIELD_MAP.values():
        count = sum(row.get(field) is not None for row in rows)
        result[f"{field}_days"] = count
        result[f"{field}_coverage_ratio"] = count / expected if expected else 0
        metric_ratios.append(result[f"{field}_coverage_ratio"])
    result["status"] = "pass" if provider_id and metric_ratios and min(metric_ratios) >= .95 else ("unsupported" if not provider_id else "review")
    return result


def collect(repo: Path, start: date, end: date, force: bool = False, base_url: str = BASE_URL) -> dict[str, Any]:
    assets = [a for a in validate_asset_config(load_json(repo / "config" / "assets.json")) if a["universe"] == "stablecoin" and a["tier"] != "failure_control" and a["asset_id"] != "stable_paxg"]
    all_rows: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    raw_root = repo / "data" / "raw" / "coinmetrics_stablecoin_usage"
    for asset in assets:
        provider_id = asset.get("coinmetrics_id")
        rows: list[dict[str, Any]] = []
        if provider_id:
            raw_path = raw_root / asset["asset_id"] / f"{start.isoformat()}_{end.isoformat()}.json"
            if raw_path.exists() and not force:
                payload = load_json(raw_path)
            else:
                payload = request_json(timeseries_url(base_url, provider_id, start, end))
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
                raw_path.with_suffix(".metadata.json").write_text(json.dumps({
                    "asset_id": asset["asset_id"], "coinmetrics_asset": provider_id,
                    "provider": "coinmetrics_community", "endpoint": "timeseries/asset-metrics",
                    "metrics": list(METRICS), "frequency": "1d", "start": start.isoformat(), "end": end.isoformat(),
                    "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "sha256": sha256(raw_path),
                    "license_note": "Coin Metrics Community Data; verify current Creative Commons terms before redistribution",
                }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            rows = normalize(asset["asset_id"], provider_id, payload, start, end)
            all_rows.extend(rows)
        audits.append(coverage(asset["asset_id"], provider_id, rows, start, end))
    out = repo / "data" / "processed" / "04_stablecoin_deferred"
    write_rows(out / "stablecoin_usage_daily_coinmetrics.csv", all_rows, ["asset_id", "date", "coinmetrics_asset", "active_addresses", "ledger_transaction_count", "token_transfer_count", "provider"])
    audit_fields = ["asset_id", "coinmetrics_asset", "supported", "start_date", "end_date", "first_observed_date", "last_observed_date", "active_window_expected_days", "observed_days", *[name for field in FIELD_MAP.values() for name in (f"{field}_days", f"{field}_coverage_ratio")], "status"]
    write_rows(out / "stablecoin_usage_coverage_coinmetrics.csv", audits, audit_fields)
    passed = [row for row in audits if row["status"] == "pass"]
    summary = {
        "eligible_assets": len(assets), "provider_supported_assets": sum(row["supported"] for row in audits),
        "coverage_pass_assets": len(passed), "daily_rows": len(all_rows),
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "readiness": "partial_asset_coverage_not_full_h7_sample_ready",
        "interpretation": "Coin Metrics asset-level active-address, ledger-transaction, and token-transfer metrics; active addresses are addresses, not identified users",
    }
    empirical = repo / "data" / "processed" / "04_stablecoin_deferred"
    empirical.mkdir(parents=True, exist_ok=True)
    (empirical / "stablecoin_usage_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    findings = repo / "research" / "findings" / "stablecoin-transaction-activity.md"
    findings.write_text(f"""# Stablecoin Transaction-Activity Coverage

- Primary stablecoins evaluated: {summary['eligible_assets']}.
- Stablecoins supported by the free Coin Metrics asset-metrics source: {summary['provider_supported_assets']}.
- Assets passing the 95% active-window metric-coverage gate: {summary['coverage_pass_assets']}.
- Daily asset observations collected: {summary['daily_rows']:,}.
- Requested window: {summary['start_date']} through {summary['end_date']}.
- Status: `{summary['readiness']}`.

The free source currently supports USDT, USDC, DAI, and TUSD for `AdrActCnt`, `TxCnt`, and `TxTfrCnt`. Active addresses are ledger addresses, not unique people or customers; one person may control many addresses and custodial addresses may represent many users. Provider asset-level definitions must not be silently interpreted as complete chain-by-chain settlement activity. The ten unsupported primary assets remain explicit, so these fields cannot yet satisfy the full-sample H7 transaction/user gate.
""", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect free Coin Metrics stablecoin transaction and active-address metrics")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    print(json.dumps(collect(args.repo.resolve(), args.start, args.end, args.force), indent=2))


if __name__ == "__main__":
    main()
