from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from .historical import read_csv, write_rows
from .registry import load_json


def build_blind_review(config: dict[str, Any], extractions: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = {(row["asset_id"], row["evidence_class"]): row for row in extractions["extractions"]}
    rows: list[dict[str, Any]] = []
    for asset in config["assets"]:
        for dimension, metadata in config["dimensions"].items():
            item = evidence[(asset["asset_id"], metadata["evidence_class"])]
            rows.append({
                "asset_id": asset["asset_id"], "dimension": dimension,
                "evidence_class": metadata["evidence_class"],
                "source_title": item["source_title"], "source_url": item["source_url"],
                "publication_or_effective_date": item["publication_or_effective_date"],
                "locator": item["locator"], "evidence_summary": item["evidence_summary"],
                "limitations": item.get("limitations", ""),
                "rubric_0": config["rubric"][dimension]["0"],
                "rubric_1": config["rubric"][dimension]["1"],
                "rubric_2": config["rubric"][dimension]["2"],
                "rubric_3": config["rubric"][dimension]["3"],
                "rubric_4": config["rubric"][dimension]["4"],
                "reviewer_score_0_to_4": "", "reviewer_confidence": "",
                "reviewer_rationale": "", "reviewer_name_or_id": "", "review_date": "",
            })
    return rows


def temporal_readiness(score_rows: list[dict[str, Any]], outcome_rows: list[dict[str, Any]]) -> dict[str, Any]:
    scored_assets = {row["asset_id"] for row in score_rows}
    starts = [date.fromisoformat(row.get("effective_from") or row.get("available_from_date") or row["as_of_date"]) for row in score_rows]
    outcome_dates = [date.fromisoformat(row["date"]) for row in outcome_rows]
    eligible_by_asset: Counter[str] = Counter()
    pre_score_by_asset: Counter[str] = Counter()
    for row in outcome_rows:
        asset_id = row["asset_id"]
        if asset_id not in scored_assets:
            continue
        if any(interval_matches(score, row["date"]) for score in score_rows if score["asset_id"] == asset_id):
            eligible_by_asset[asset_id] += 1
        else:
            pre_score_by_asset[asset_id] += 1
    eligible_assets = sorted(asset for asset, count in eligible_by_asset.items() if count)
    return {
        "status": "temporal_overlap_ready" if len(eligible_assets) == len(scored_assets) else "blocked_temporal_overlap",
        "scored_assets": len(scored_assets), "assets_with_post_score_outcomes": len(eligible_assets),
        "post_score_outcome_rows": sum(eligible_by_asset.values()),
        "pre_score_rows_prohibited_from_backfill": sum(pre_score_by_asset.values()),
        "earliest_score_date": min(starts).isoformat() if starts else None,
        "outcome_start_date": min(outcome_dates).isoformat() if outcome_dates else None,
        "outcome_end_date": max(outcome_dates).isoformat() if outcome_dates else None,
        "eligible_assets": eligible_assets,
        "rule": "A design score may join only to observations on or after its evidence/as-of date; later scores are never backfilled.",
        "next_requirement": "Complete the targeted component review before H5/H6 estimation; add further independently evidenced historical score dates before claiming time-varying H5 effects.",
    }


def interval_matches(score: dict[str, Any], day: str) -> bool:
    start = score.get("effective_from") or score.get("available_from_date") or score["as_of_date"]
    end = score.get("effective_to") or "9999-12-31"
    return start <= day <= end


def join_temporally_valid(score_rows: list[dict[str, Any]], outcome_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    score_index: dict[str, list[dict[str, Any]]] = {}
    for row in score_rows:
        score_index.setdefault(row["asset_id"], []).append(row)
    score_fields = [
        "effective_from", "effective_to", "available_from_date", "methodology_version", "confidence", "backing_quality_score",
        "verification_quality_score", "redemption_access_quality_score",
        "legal_protection_quality_score", "operational_resilience_score",
        "overall_design_quality_score", "redemption_friction_score", "operational_constraint_score",
    ]
    outcome_fields = [
        "sample_tier", "failure_control", "price_usd", "absolute_peg_error_bps",
        "breach_50bps", "circulating_peg_usd", "price_provider", "supply_provider",
    ]
    output: list[dict[str, Any]] = []
    for outcome in outcome_rows:
        matches = [score for score in score_index.get(outcome["asset_id"], []) if interval_matches(score, outcome["date"])]
        if not matches:
            continue
        if len(matches) != 1:
            raise ValueError(f"multiple score intervals match {outcome['asset_id']} {outcome['date']}")
        score = matches[0]
        output.append({
            "asset_id": outcome["asset_id"], "date": outcome["date"],
            **{field: outcome.get(field, "") for field in outcome_fields},
            **{field: score.get(field, "") for field in score_fields},
        })
    output.sort(key=lambda row: (row["asset_id"], row["date"]))
    return output


def run(repo: Path) -> dict[str, Any]:
    config = load_json(repo / "config" / "stablecoin_scorecard.json")
    extractions = load_json(repo / "config" / "stablecoin_evidence_extractions.json")
    interval_path = repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_score_intervals.csv"
    scores = read_csv(interval_path) if interval_path.exists() else read_csv(repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_point_in_time_scorecard.csv")
    outcomes = read_csv(repo / "data" / "processed" / "04_stablecoin_deferred" / "stablecoin_daily.csv")
    review = build_blind_review(config, extractions)
    summary = temporal_readiness(scores, outcomes)
    joined = join_temporally_valid(scores, outcomes)
    out = repo / "data" / "processed" / "04_stablecoin_deferred"
    review_fields = list(review[0])
    write_rows(out / "stablecoin_score_targeted_review.csv", review, review_fields)
    write_rows(out / "stablecoin_h5_h6_temporally_valid_panel.csv", joined, list(joined[0]) if joined else ["asset_id", "date"])
    (out / "stablecoin_h5_h6_temporal_readiness.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    findings = repo / "research" / "findings" / "stablecoin-h5-h6-temporal-readiness.md"
    findings.parent.mkdir(parents=True, exist_ok=True)
    findings.write_text(f"""# H5--H6 Temporal Readiness

- Status: `{summary['status']}`.
- Scored assets: {summary['scored_assets']}.
- Assets with post-score outcomes: {summary['assets_with_post_score_outcomes']}.
- Eligible post-score outcome rows: {summary['post_score_outcome_rows']}.
- Historical rows prohibited from score backfill: {summary['pre_score_rows_prohibited_from_backfill']}.
- Earliest score date: {summary['earliest_score_date']}.
- Available outcome window: {summary['outcome_start_date']} through {summary['outcome_end_date']}.

The targeted review worksheet contains {len(review)} blind asset-component decisions. It omits the primary researcher's scores and exposes only the evidence, limitations, and complete rubric. H5--H6 estimation remains blocked until review is complete and design scores have valid temporal overlap with outcomes. Current scores cannot be applied retrospectively to earlier depeg observations.
""", encoding="utf-8")
    return {**summary, "targeted_review_rows": len(review), "temporally_valid_panel_rows": len(joined)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the targeted H5-H6 score review and temporal readiness audit")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(run(args.repo.resolve()), indent=2))


if __name__ == "__main__":
    main()
