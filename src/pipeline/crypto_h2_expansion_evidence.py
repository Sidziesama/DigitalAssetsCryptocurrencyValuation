from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any


REVIEW_FIELDS = ["asset_id", "code", "reviewer_value", "reviewer_source_url", "reviewer_rationale"]


def audit(
    evidence: dict[str, Any], expansion: dict[str, Any], events: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, Any]]:
    if evidence.get("schema_version") != 1:
        raise ValueError("unsupported H2 expansion-evidence schema")
    assets = evidence.get("assets", [])
    codes = evidence.get("codes", [])
    if assets != expansion["expansion_assets"]:
        raise ValueError("evidence assets must equal the predeclared expansion assets in order")
    if codes != expansion["requirements"]["required_mechanism_codes"]:
        raise ValueError("evidence codes must equal the predeclared mechanism codes in order")
    if len(assets) != len(set(assets)) or len(codes) != len(set(codes)):
        raise ValueError("duplicate evidence asset or code")

    expected = {(asset_id, code) for asset_id in assets for code in codes}
    decisions = evidence.get("decisions", [])
    keys = [(row.get("asset_id"), row.get("code")) for row in decisions]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError("evidence must contain exactly one decision per expansion asset-code pair")

    window_start = date.fromisoformat(expansion["analysis_window"]["start"])
    event_index = {
        (row["asset_id"], row["code"], row["effective_from"]): row
        for row in events
        if (row.get("asset_id"), row.get("code")) in expected
    }
    audit_rows: list[dict[str, Any]] = []
    for row in decisions:
        if row.get("recommended_value") not in {0, 1}:
            raise ValueError("expansion decisions require binary recommended_value")
        if not str(row.get("source_url", "")).startswith("https://"):
            raise ValueError("expansion decisions require an HTTPS source")
        if not row.get("rationale"):
            raise ValueError("expansion decisions require rationale")
        if date.fromisoformat(row["effective_from"]) > window_start:
            raise ValueError("expansion evidence must be effective by the analysis-window start")
        event = event_index.get((row["asset_id"], row["code"], row["effective_from"]))
        event_match = bool(
            event
            and event.get("value") == row["recommended_value"]
            and event.get("source_url") == row["source_url"]
            and event.get("rationale") == row["rationale"]
        )
        audit_rows.append({**row, "event_match": int(event_match)})

    mismatches = sum(not row["event_match"] for row in audit_rows)
    review_rows = [
        {"asset_id": row["asset_id"], "code": row["code"], "reviewer_value": "",
         "reviewer_source_url": "", "reviewer_rationale": ""}
        for row in decisions
    ]
    review_complete = evidence.get("review_status") == "adjudicated_complete"
    frozen = evidence.get("preregistration_status") == "frozen_post_pilot_for_reproducibility"
    summary = {
        "status": "evidence_ready_review_complete" if mismatches == 0 and review_complete else "evidence_ready_independent_review_pending" if mismatches == 0 else "evidence_event_mismatch",
        "assets": len(assets),
        "targeted_decisions": len(audit_rows),
        "event_matches": len(audit_rows) - mismatches,
        "event_mismatches": mismatches,
        "independent_review_rows": len(review_rows),
        "independent_review_complete": review_complete,
        "preregistration_frozen": frozen,
        "adjudication_rule": evidence.get("adjudication_rule"),
    }
    return audit_rows, review_rows, summary


def run(repo: Path) -> dict[str, Any]:
    evidence = json.loads((repo / "config/crypto_h2_expansion_evidence.json").read_text(encoding="utf-8"))
    expansion = json.loads((repo / "config/crypto_h2_expansion.json").read_text(encoding="utf-8"))
    events = json.loads((repo / "config/crypto_mechanism_events.json").read_text(encoding="utf-8"))["events"]
    rows, review_rows, summary = audit(evidence, expansion, events)
    output = repo / "data/processed/01_classification"
    output.mkdir(parents=True, exist_ok=True)
    with (output / "crypto_h2_expansion_evidence_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(dict.fromkeys(key for row in rows for key in row))
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    with (output / "crypto_h2_expansion_blind_review.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS, lineterminator="\n")
        writer.writeheader(); writer.writerows(review_rows)
    (output / "crypto_h2_expansion_evidence_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit H2 expansion evidence and create a blind review sheet")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
