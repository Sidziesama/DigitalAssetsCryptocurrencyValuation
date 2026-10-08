from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import date
from pathlib import Path
from typing import Any


def read_dates(path: Path) -> dict[str, set[str]]:
    dates: dict[str, set[str]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            asset_id, day = row.get("asset_id", ""), row.get("date", "")
            if asset_id and day:
                dates.setdefault(asset_id, set()).add(day)
    return dates


def validate(spec: dict[str, Any], discovery: dict[str, Any]) -> None:
    if spec.get("status") != "frozen_before_validation_outcomes":
        raise ValueError("H8 temporal validation design is not frozen")
    if spec.get("expected_assets") != discovery.get("expected_assets"):
        raise ValueError("validation universe differs from discovery universe")
    discovery_end = date.fromisoformat(discovery["measurement_window"]["end"])
    validation_start = date.fromisoformat(spec["validation_window"]["start"])
    if (validation_start - discovery_end).days != 1:
        raise ValueError("validation window must begin immediately after discovery window")
    if spec.get("candidate_model", {}).get("id") != "bundle_financial_integration":
        raise ValueError("the discovery-selected candidate model changed")
    if spec.get("benchmark_model", {}).get("id") != "raw_function_breadth":
        raise ValueError("the raw-breadth benchmark changed")
    if spec.get("primary_metric") != "leave_one_asset_out_root_mean_squared_prediction_error":
        raise ValueError("the frozen comparison metric changed")


def build(spec: dict[str, Any], discovery: dict[str, Any], observed: dict[str, set[str]]) -> dict[str, Any]:
    validate(spec, discovery)
    window = spec["validation_window"]
    start, end = date.fromisoformat(window["start"]), date.fromisoformat(window["end"])
    expected_days = (end - start).days + 1
    minimum_days = math.ceil(expected_days * float(window["minimum_coverage_share"]))
    coverage = []
    for asset_id in sorted(observed):
        days = sum(window["start"] <= day <= window["end"] for day in observed[asset_id])
        coverage.append({"asset_id": asset_id, "observed_days": days, "minimum_days": minimum_days, "ready": days >= minimum_days})
    assets_ready = sum(row["ready"] for row in coverage)
    window_closed = date.today() >= end
    return {
        "status": "ready_for_estimation" if window_closed and assets_ready == spec["expected_assets"] else "waiting_for_fixed_validation_window",
        "specification_version": spec["document_version"],
        "validation_window": window,
        "expected_calendar_days": expected_days,
        "minimum_days_per_asset": minimum_days,
        "window_closed": window_closed,
        "assets_expected": spec["expected_assets"],
        "assets_ready": assets_ready,
        "candidate_model": spec["candidate_model"]["id"],
        "benchmark_model": spec["benchmark_model"]["id"],
        "decision_rule": spec["decision_rule"],
        "coverage": coverage,
        "next_required": "Collect the fixed 2026-08-23 to 2027-08-22 outcome window without changing the model, universe, dates, or metric."
    }


def run(repo: Path) -> dict[str, Any]:
    spec = json.loads((repo / "config/crypto_h8_out_of_sample_validation.json").read_text())
    discovery = json.loads((repo / spec["discovery_specification"]).read_text())
    result = build(spec, discovery, read_dates(repo / spec["market_input"]))
    output = repo / "data/processed/02_valuation/crypto_h8_oos_readiness.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
