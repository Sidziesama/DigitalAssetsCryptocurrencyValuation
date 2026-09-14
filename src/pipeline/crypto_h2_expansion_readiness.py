from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from src.pipeline.historical import write_rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def build(
    config: dict[str, Any],
    market_rows: list[dict[str, str]],
    fee_rows: list[dict[str, str]],
    events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates = config["expansion_assets"]
    if len(candidates) != 5 or len(candidates) != len(set(candidates)):
        raise ValueError("H2 expansion requires five unique candidates")
    if config["requirements"].get("selection_uses_model_outcomes") is not False:
        raise ValueError("H2 expansion must prohibit outcome-based selection")
    window_start = date.fromisoformat(config["analysis_window"]["start"])
    market_index: dict[str, list[dict[str, str]]] = {}
    for row in market_rows:
        market_index.setdefault(row["asset_id"], []).append(row)
    fee_index = {row["asset_id"]: row for row in fee_rows}

    rows = []
    for asset_id in candidates:
        market_matches = [
            row for row in market_index.get(asset_id, [])
            if row["provider"] == config["requirements"]["market_provider"]
            and row["status"] == config["requirements"]["market_status"]
        ]
        market_pass = any(
            date.fromisoformat(row["start_date"]) <= window_start
            and date.fromisoformat(row["end_date"]) >= date.fromisoformat(config["analysis_window"]["end"])
            for row in market_matches
        )
        fee = fee_index.get(asset_id)
        fee_pass = bool(fee) and int(fee["fees_usd_days"]) == int(fee["expected_days"])
        mechanisms = {
            event["code"]
            for event in events
            if event["asset_id"] == asset_id
            and event["code"] in config["requirements"]["required_mechanism_codes"]
            and date.fromisoformat(event["effective_from"]) <= window_start
        }
        mechanism_pass = mechanisms == set(config["requirements"]["required_mechanism_codes"])
        rows.append(
            {
                "asset_id": asset_id,
                "market_coverage_pass": int(market_pass),
                "complete_fee_history_pass": int(fee_pass),
                "mechanism_evidence_pass": int(mechanism_pass),
                "eligible": int(market_pass and fee_pass and mechanism_pass),
            }
        )
    eligible = [row["asset_id"] for row in rows if row["eligible"]]
    return rows, {
        "status": "expansion_ready" if len(eligible) == len(candidates) else "expansion_blocked",
        "candidates": len(candidates),
        "eligible_assets": eligible,
        "selection_uses_model_outcomes": False,
    }


def run(repo: Path) -> dict[str, Any]:
    config = json.loads((repo / "config/crypto_h2_expansion.json").read_text(encoding="utf-8"))
    events = json.loads((repo / "config/crypto_mechanism_events.json").read_text(encoding="utf-8"))["events"]
    rows, summary = build(
        config,
        read_csv(repo / "data/processed/00_foundation/market_coverage_coinpaprika.csv"),
        read_csv(repo / "data/processed/00_foundation/crypto_fee_fundamentals_coverage.csv"),
        events,
    )
    output = repo / "data/processed/01_classification"
    write_rows(output / "crypto_h2_expansion_readiness.csv", rows, list(rows[0]))
    (output / "crypto_h2_expansion_readiness.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit rule-based H2 cross-section expansion readiness")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
