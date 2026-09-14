from __future__ import annotations

import argparse
import csv
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .registry import load_json
from .stablecoin_scorecard import normalized


def score_row(asset: dict[str, Any], dimensions: dict[str, Any], low: int, high: int, methodology: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "asset_id": asset["asset_id"], "effective_from": asset["effective_from"],
        "effective_to": asset.get("effective_to", ""), "methodology_version": methodology,
        "confidence": asset["confidence"],
    }
    overall = 0.0
    for name, metadata in dimensions.items():
        value = normalized(asset["scores"][name], low, high)
        row[f"{name}_score"] = value
        overall += value * metadata["weight"] / 100
    row["overall_design_quality_score"] = overall
    access_quality = row["redemption_access_quality_score"] * .60 + row["operational_resilience_score"] * .40
    row["redemption_friction_score"] = 100 - access_quality
    row["operational_constraint_score"] = 100 - row["operational_resilience_score"]
    row["source_urls"] = " | ".join(source["url"] for source in asset["sources"])
    row["rationale"] = asset["rationale"]
    return row


def validate_and_build(scorecard: dict[str, Any], history: dict[str, Any]) -> list[dict[str, Any]]:
    if history.get("schema_version") != 1:
        raise ValueError("unsupported historical-score schema")
    dimensions = scorecard["dimensions"]
    low, high = scorecard["scale"]["minimum"], scorecard["scale"]["maximum"]
    intervals: list[dict[str, Any]] = []
    historical_assets = {row["asset_id"] for row in history["intervals"]}
    current_by_asset = {asset["asset_id"]: asset for asset in scorecard["assets"]}
    for item in history["intervals"]:
        if item["asset_id"] not in current_by_asset or set(item["scores"]) != set(dimensions):
            raise ValueError(f"invalid historical interval for {item.get('asset_id')}")
        start, end = date.fromisoformat(item["effective_from"]), date.fromisoformat(item["effective_to"])
        if end < start or not item.get("sources") or any(not source["url"].startswith("https://") for source in item["sources"]):
            raise ValueError(f"invalid dates or sources for {item['asset_id']}")
        if any(date.fromisoformat(source["available_from_date"]) > start for source in item["sources"]):
            raise ValueError(f"interval predates source availability for {item['asset_id']}")
        intervals.append(score_row(item, dimensions, low, high, history["methodology_version"]))
    for current in scorecard["assets"]:
        item = {
            **current, "effective_from": current["available_from_date"], "effective_to": "",
            "sources": [{"url": "config/stablecoin_evidence_extractions.json"}],
        }
        intervals.append(score_row(item, dimensions, low, high, scorecard["methodology_version"]))
    intervals.sort(key=lambda row: (row["asset_id"], row["effective_from"]))
    previous: dict[str, dict[str, Any]] = {}
    for row in intervals:
        prior = previous.get(row["asset_id"])
        if prior:
            if not prior["effective_to"] or date.fromisoformat(prior["effective_to"]) >= date.fromisoformat(row["effective_from"]):
                raise ValueError(f"overlapping score intervals for {row['asset_id']}")
            if date.fromisoformat(prior["effective_to"]) + timedelta(days=1) != date.fromisoformat(row["effective_from"]):
                raise ValueError(f"gap between declared consecutive score intervals for {row['asset_id']}")
        previous[row["asset_id"]] = row
    return intervals


def run(repo: Path) -> dict[str, Any]:
    scorecard = load_json(repo / "config" / "stablecoin_scorecard.json")
    history = load_json(repo / "config" / "stablecoin_historical_score_intervals.json")
    rows = validate_and_build(scorecard, history)
    out = repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_score_intervals.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    return {"intervals": len(rows), "assets": len({row['asset_id'] for row in rows}), "historical_intervals": len(history["intervals"]), "status": "historical_pilot_ready"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build non-overlapping effective-dated stablecoin score intervals")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args(); print(json.dumps(run(args.repo.resolve()), indent=2))


if __name__ == "__main__":
    main()
