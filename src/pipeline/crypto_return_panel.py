from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .crypto_h8_breadth_pilot import read_csv


def validate(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1 or spec.get("status") != "frozen_before_return_estimation":
        raise ValueError("unsupported return panel specification")
    if spec.get("minimum_asset_days", 0) < 30 or spec.get("max_gap_days", 0) < 1:
        raise ValueError("return panel needs a minimum history and a gap rule")


def beta(x: list[float], y: list[float]) -> float | None:
    if len(x) < 2:
        return None
    mx, my = statistics.fmean(x), statistics.fmean(y)
    var = sum((v - mx) ** 2 for v in x)
    if var == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / var


def build(spec: dict[str, Any], rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    validate(spec)
    start, end = date.fromisoformat(spec["start_date"]), date.fromisoformat(spec["end_date"])
    closes: dict[str, dict[date, tuple[float, float]]] = defaultdict(dict)
    for row in rows:
        if row.get("quote_asset") != spec["quote_asset"]:
            continue
        day = date.fromisoformat(row["date"])
        if not start <= day <= end:
            continue
        close, volume = float(row["close_quote"]), float(row["volume_quote"] or 0)
        if close > 0:
            closes[row["asset_id"]][day] = (close, volume)
    coverage = []
    included: dict[str, dict[date, tuple[float, float]]] = {}
    for asset in sorted(closes):
        days = sorted(closes[asset])
        record = {"asset_id": asset, "first_date": days[0].isoformat(), "last_date": days[-1].isoformat(), "close_days": len(days)}
        if len(days) >= spec["minimum_asset_days"]:
            included[asset] = closes[asset]
            record["status"] = "included"
        else:
            record["status"] = "excluded_short_history"
        coverage.append(record)
    if not included:
        raise ValueError("return panel requires at least one asset with sufficient history")
    log_returns: dict[str, dict[date, float]] = defaultdict(dict)
    max_gap = timedelta(days=spec["max_gap_days"])
    for asset, series in included.items():
        days = sorted(series)
        for previous, current in zip(days, days[1:]):
            if current - previous <= max_gap:
                log_returns[asset][current] = math.log(series[current][0] / series[previous][0])
    market: dict[date, float] = {}
    by_day: dict[date, list[float]] = defaultdict(list)
    for asset, series in log_returns.items():
        for day, value in series.items():
            by_day[day].append(value)
    for day, values in by_day.items():
        market[day] = statistics.fmean(values)
    btc = log_returns.get("crypto_btc", {})
    panel: list[dict[str, Any]] = []
    for asset in sorted(included):
        series = log_returns[asset]
        days = sorted(series)
        day_set = set(days)
        for day in days:
            def window_sum(offset_start: int, offset_end: int) -> float | None:
                total = 0.0
                for offset in range(offset_start, offset_end + 1):
                    target = day + timedelta(days=offset)
                    if target not in day_set:
                        return None
                    total += series[target]
                return total
            trailing = [series[day - timedelta(days=k)] for k in range(0, 30) if (day - timedelta(days=k)) in day_set]
            vol = statistics.pstdev(trailing) * math.sqrt(365) if len(trailing) == 30 else None
            xs, ys = [], []
            for k in range(1, 181):
                target = day - timedelta(days=k)
                if target in day_set and target in market:
                    xs.append(market[target]); ys.append(series[target])
            rolling_beta = beta(xs, ys) if len(xs) >= 120 else None
            volume = included[asset][day][1]
            panel.append({
                "asset_id": asset, "date": day.isoformat(), "close_usdt": included[asset][day][0],
                "log_return": series[day],
                "forward_log_return_7d": window_sum(1, 7), "forward_log_return_30d": window_sum(1, 30),
                "momentum_30d_skip7": window_sum(-37, -8),
                "realized_volatility_30d_annualized": vol,
                "log_dollar_volume": math.log(volume) if volume > 0 else None,
                "market_ew_log_return": market[day], "market_breadth": len(by_day[day]),
                "btc_log_return": btc.get(day), "market_beta_180d_lag1": rolling_beta,
            })
    summary = {
        "status": "return_panel_complete", "specification_version": spec["document_version"], "freeze_date": spec["freeze_date"],
        "assets_included": len(included), "assets_excluded": len(coverage) - len(included), "coverage": coverage,
        "rows": len(panel), "first_date": min(r["date"] for r in panel), "last_date": max(r["date"] for r in panel),
        "rows_with_rolling_beta": sum(r["market_beta_180d_lag1"] is not None for r in panel),
        "rows_with_forward_30d": sum(r["forward_log_return_30d"] is not None for r in panel),
        "risk_free_rate": spec["risk_free_rate"], "interpretation": spec["interpretation"],
    }
    return panel, summary


def run(repo: Path) -> dict[str, Any]:
    spec = json.loads((repo / "config/crypto_return_panel.json").read_text(encoding="utf-8"))
    panel, summary = build(spec, read_csv(repo / spec["source"]))
    out = repo / "data/processed/03_risk"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "crypto_return_panel_daily.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(panel[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows([{k: ("" if v is None else v) for k, v in row.items()} for row in panel])
    (out / "crypto_return_panel_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the frozen daily crypto return panel")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
