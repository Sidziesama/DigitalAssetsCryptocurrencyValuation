from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from src.pipeline.crypto_economic_design import CODES, load_json, validate as validate_design


def validate_evidence(evidence: dict[str, Any], design: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    if evidence.get("schema_version") != 1:
        raise ValueError("unsupported crypto design-evidence schema")
    validate_design(design, registry)
    assets, codes = evidence.get("assets", []), evidence.get("codes", [])
    expected = {(asset, code) for asset in assets for code in codes}
    if len(assets) != len(set(assets)) or len(codes) != len(set(codes)):
        raise ValueError("duplicate tranche asset or code")
    if not set(codes) <= set(CODES):
        raise ValueError("unknown value-accrual code in evidence tranche")
    decisions = evidence.get("decisions", [])
    keys = [(row.get("asset_id"), row.get("code")) for row in decisions]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError("evidence tranche must contain exactly one decision per asset-code pair")
    as_of = date.fromisoformat(evidence["as_of"])
    for row in decisions:
        if row.get("status") == "verified" and row.get("recommended_value") not in {0, 1}:
            raise ValueError("verified decisions require a binary recommended_value")
        if row.get("status") != "verified" and row.get("recommended_value") is not None:
            raise ValueError("pending decisions must not recommend a value")
        if not str(row.get("source_url", "")).startswith("https://"):
            raise ValueError("every evidence decision requires an HTTPS source")
        if date.fromisoformat(row["source_date"]) > as_of:
            raise ValueError("source_date cannot be later than tranche as_of")
        if row.get("date_basis") not in {"published", "created", "report_as_of", "effective", "retrieved_as_of"}:
            raise ValueError("every evidence decision requires a valid date_basis")
        if not row.get("rationale"):
            raise ValueError("every evidence decision requires rationale")
    return decisions


def audit(evidence: dict[str, Any], design: dict[str, Any], registry: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    decisions = validate_evidence(evidence, design, registry)
    design_index = {row["asset_id"]: dict(zip(CODES, row["codes"])) for row in design["assets"]}
    rows = []
    for row in decisions:
        provisional = design_index[row["asset_id"]][row["code"]]
        recommended = row["recommended_value"]
        rows.append({**row, "provisional_value": provisional,
                     "verified_matches_design": "" if recommended is None else int(provisional == recommended)})
    verified = [r for r in rows if r["status"] == "verified"]
    summary = {
        "status": "tranche_complete_pending_remaining_evidence",
        "assets": len(evidence["assets"]), "targeted_decisions": len(rows),
        "verified_decisions": len(verified), "pending_decisions": len(rows) - len(verified),
        "verified_mismatches": sum(r["verified_matches_design"] == 0 for r in verified),
        "coverage_ratio": len(verified) / len(rows),
        "next_requirement": "Resolve the remaining monetary and positive collateral-eligibility tests; then extend the same evidence schema to the remaining 19 assets."
    }
    return rows, summary


def run(repo: Path) -> dict[str, Any]:
    evidence = load_json(repo / "config" / "crypto_design_evidence_tranche_1.json")
    design = load_json(repo / "config" / "crypto_economic_design.json")
    registry = load_json(repo / "config" / "assets.json")
    rows, summary = audit(evidence, design, registry)
    out = repo / "data" / "processed" / "evidence"; out.mkdir(parents=True, exist_ok=True)
    with (out / "crypto_design_evidence_tranche_1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    pending = [{"asset_id": row["asset_id"], "code": row["code"], "reviewer_value": "", "reviewer_source_url": "", "reviewer_rationale": ""} for row in rows if row["status"] != "verified"]
    with (out / "crypto_design_evidence_focused_review.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["asset_id", "code", "reviewer_value", "reviewer_source_url", "reviewer_rationale"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(pending)
    (out / "crypto_design_evidence_tranche_1_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit the first non-stable crypto design-evidence tranche")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
