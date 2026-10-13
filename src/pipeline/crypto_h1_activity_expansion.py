from __future__ import annotations

import argparse
import csv
import html
import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .crypto_h2_exploratory_estimates import estimate
from .crypto_h2_small_cluster_inference import wild_cluster_test


COLUMNS = ("log1p_active_addresses_lag1", "log1p_transaction_count_lag1")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build_panel(
    spec: dict[str, Any], activity_sources: list[list[dict[str, str]]], market: list[dict[str, str]]
) -> list[dict[str, Any]]:
    if spec.get("status") != "frozen_before_expansion_estimation":
        raise ValueError("H1 expansion design must be frozen before estimation")
    permitted = set(spec["primary_assets"] + spec["token_contract_sensitivity_assets"])
    activity: dict[tuple[str, str], tuple[float, float]] = {}
    for source in activity_sources:
        for row in source:
            asset, day = row.get("asset_id"), row.get("date")
            if asset not in permitted or not day:
                continue
            try:
                addresses, transactions = float(row["active_addresses"]), float(row["transaction_count"])
            except (KeyError, TypeError, ValueError):
                continue
            if min(addresses, transactions) < 0 or not all(map(math.isfinite, (addresses, transactions))):
                raise ValueError("activity values must be finite and non-negative")
            key = (asset, day)
            if key in activity and activity[key] != (addresses, transactions):
                raise ValueError(f"conflicting activity row for {asset} {day}")
            activity[key] = (addresses, transactions)
    start, end = spec["window"]["start"], spec["window"]["end"]
    rows = []
    for row in market:
        asset, day_text = row.get("asset_id"), row.get("date")
        if asset not in permitted or not day_text or not start <= day_text <= end:
            continue
        try:
            cap = float(row["market_cap_usd"])
        except (KeyError, TypeError, ValueError):
            continue
        if cap <= 0 or not math.isfinite(cap):
            continue
        lag_day = (date.fromisoformat(day_text) - timedelta(days=1)).isoformat()
        lag = activity.get((asset, lag_day))
        if lag is None:
            continue
        scope = "native_network" if asset in spec["primary_assets"] else "token_contract"
        rows.append({
            "asset_id": asset, "date": day_text, "measurement_scope": scope,
            "market_cap_usd": cap, "log_market_cap_usd": math.log(cap),
            "active_addresses_lag1": lag[0], "transaction_count_lag1": lag[1],
            "log1p_active_addresses_lag1": math.log1p(lag[0]),
            "log1p_transaction_count_lag1": math.log1p(lag[1]),
        })
    return sorted(rows, key=lambda row: (row["asset_id"], row["date"]))


def estimate_sample(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    assets = sorted({row["asset_id"] for row in rows})
    dates = sorted({row["date"] for row in rows})
    if len(assets) < 4 or not dates:
        raise ValueError(f"{name} requires at least four assets and observed dates")
    if len(rows) != len(assets) * len(dates):
        raise ValueError(f"{name} must be a balanced asset-date panel")
    point = estimate(name, rows, "log_market_cap_usd", COLUMNS)
    inference = {column: wild_cluster_test(rows, "log_market_cap_usd", COLUMNS, target=column) for column in COLUMNS}
    leave_one_out = []
    for asset in assets:
        subset = [row for row in rows if row["asset_id"] != asset]
        result = estimate(f"{name}_without_{asset}", subset, "log_market_cap_usd", COLUMNS)
        leave_one_out.append({"excluded_asset": asset, **result["coefficients"]})
    return {
        "sample": name, "rows": len(rows), "assets": assets, "dates": len(dates),
        "coefficients": point["coefficients"], "within_r_squared": point["within_r_squared"],
        "inference": inference, "leave_one_asset_out": leave_one_out,
    }


def build(spec: dict[str, Any], activity_sources: list[list[dict[str, str]]], market: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    panel = build_panel(spec, activity_sources, market)
    primary = [row for row in panel if row["measurement_scope"] == "native_network"]
    pooled = panel
    primary_result = estimate_sample("native_network_primary", primary)
    pooled_result = estimate_sample("network_plus_token_sensitivity", pooled)
    result = {
        "status": "h1_activity_expansion_complete_exploratory",
        "design_frozen_before_estimation": True,
        "primary": primary_result,
        "sensitivity": pooled_result,
        "excluded_by_rule": {"crypto_doge": "prior active-universe exclusion", "crypto_xmr": "active-address metric unavailable"},
        "interpretation_guardrails": spec["reporting"],
    }
    return panel, result


def chart(result: dict[str, Any]) -> str:
    entries = []
    for sample_key, sample_label in (("primary", "Native networks"), ("sensitivity", "Networks + tokens")):
        sample = result[sample_key]
        for column, metric in ((COLUMNS[0], "Active addresses"), (COLUMNS[1], "Transactions")):
            entries.append((f"{sample_label}: {metric}", sample["coefficients"][column], sample["inference"][column]["wild_cluster_bootstrap_p_two_sided"]))
    width, height, zero = 920, 350, 455
    scale = 320 / max(abs(value) for _, value, _ in entries)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="H1 activity coefficients by measurement scope">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="30" font-family="Arial" font-size="20" font-weight="600" fill="#17212b">H1 activity coefficients depend on measurement scope</text>',
        '<text x="24" y="52" font-family="Arial" font-size="12" fill="#647383">Asset and date fixed effects; exact asset-cluster p-values shown. Neither primary coefficient is confirmed.</text>',
        f'<line x1="{zero}" y1="72" x2="{zero}" y2="310" stroke="#647383" stroke-width="1.5"/>',
    ]
    for index, (label, value, p_value) in enumerate(entries):
        y = 92 + index * 58
        end = zero + value * scale
        x = min(zero, end); bar_width = max(abs(end - zero), 1)
        color = "#3478b8" if index < 2 else "#8aa8c2"
        parts += [
            f'<text x="24" y="{y+15}" font-family="Arial" font-size="13" fill="#17212b">{html.escape(label)}</text>',
            f'<rect x="{x:.1f}" y="{y}" width="{bar_width:.1f}" height="22" fill="{color}"/>',
            f'<text x="{end + (8 if value >= 0 else -8):.1f}" y="{y+15}" text-anchor="{"start" if value >= 0 else "end"}" font-family="Arial" font-size="12" fill="#17212b">{value:+.4f} · p={p_value:.3f}</text>',
        ]
    parts += [
        '<text x="455" y="337" text-anchor="middle" font-family="Arial" font-size="12" fill="#647383">Coefficient on lagged log(1 + activity); zero is the vertical line</text>',
        '</svg>',
    ]
    return "\n".join(parts) + "\n"


def run(repo: Path) -> dict[str, Any]:
    spec = json.loads((repo / "config/crypto_h1_activity_expansion.json").read_text())
    activity = [read_csv(repo / path) for path in spec["activity_inputs"]]
    market = read_csv(repo / spec["market_input"])
    panel, result = build(spec, activity, market)
    out = repo / "data/processed/02_valuation"
    fields = list(panel[0])
    with (out / "crypto_h1_activity_expansion_panel.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(panel)
    (out / "crypto_h1_activity_expansion.json").write_text(json.dumps(result, indent=2) + "\n")
    (repo / "research/figures/crypto-h1-activity-expansion.svg").write_text(chart(result), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate the frozen H1 activity expansion")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
