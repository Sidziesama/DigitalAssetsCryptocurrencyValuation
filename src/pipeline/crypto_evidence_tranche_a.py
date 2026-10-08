from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from .crypto_design_evidence import validate_evidence
from .crypto_economic_design import CODES, load_json


def validate_tranche(evidence: dict[str, Any]) -> None:
    if evidence.get("tranche") != "A" or not evidence.get("tranche_order_rule"):
        raise ValueError("tranche A evidence requires a tranche label and a fixed tranche-order rule")
    if not evidence.get("adjudication_rule") or evidence.get("review_status") not in {"awaiting_independent_blind_review", "single_coder_with_documented_limitations"}:
        raise ValueError("tranche A evidence must record its adjudication rule and review status")
    for case in evidence.get("consistency_cases", []):
        if case.get("status") != "open_requires_adjudication" or not case.get("precedent") or not case.get("question"):
            raise ValueError(f"consistency case {case.get('case_id')} needs a precedent, a question, and open status")
        pending = {(d["asset_id"], d["code"]) for d in evidence["decisions"] if d["status"] != "verified"}
        for asset in case["assets"]:
            if (asset, case["code"]) not in pending:
                raise ValueError(f"consistency case {case['case_id']} names {asset} but that cell is not pending")


def audit(evidence: dict[str, Any], design: dict[str, Any], registry: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    validate_tranche(evidence)
    decisions = validate_evidence(evidence, design, registry)
    design_index = {row["asset_id"]: dict(zip(CODES, row["codes"])) for row in design["assets"]}
    rows: list[dict[str, Any]] = []
    for decision in decisions:
        provisional = design_index[decision["asset_id"]][decision["code"]]
        recommended = decision["recommended_value"]
        rows.append({**decision, "provisional_value": provisional,
                     "verified_matches_provisional": "" if recommended is None else int(provisional == recommended)})
    verified = [row for row in rows if row["status"] == "verified"]
    pending = [row for row in rows if row["status"] != "verified"]
    mismatches = [row for row in verified if row["verified_matches_provisional"] == 0]
    worksheet = [{"asset_id": row["asset_id"], "code": row["code"], "reviewer_value": "", "reviewer_source_url": "",
                  "reviewer_rationale": "", "review_note": "Score independently. Do not consult the coder's value, source, or rationale."}
                 for row in rows]
    summary = {
        "status": "tranche_a_single_coder_evidence" if evidence["review_status"] == "single_coder_with_documented_limitations" else "tranche_a_drafted_awaiting_review",
        "specification_version": evidence["document_version"], "as_of": evidence["as_of"],
        "assets": len(evidence["assets"]), "codes": len(evidence["codes"]), "decisions": len(rows),
        "verified_decisions": len(verified), "pending_decisions": len(pending),
        "coverage_ratio": len(verified) / len(rows),
        "provisional_matrix_mismatches": len(mismatches),
        "mismatch_detail": [{k: row[k] for k in ("asset_id", "code", "provisional_value", "recommended_value")} for row in mismatches],
        "pending_detail": [{k: row[k] for k in ("asset_id", "code", "rationale")} for row in pending],
        "open_consistency_cases": [{k: case[k] for k in ("case_id", "assets", "code", "recommendation")}
                                    for case in evidence.get("consistency_cases", [])],
        "independent_replication": evidence.get("independent_replication"),
        "url_confirmed_decisions": sum(row.get("verification", "").startswith("url_confirmed") for row in rows),
        "tranche_order_rule": evidence["tranche_order_rule"],
        "next_requirement": "Resolve the remaining evidence gaps and apply the same rules consistently. This is a single-coder project; no further blind reviewer is required. Pending cells stay null until adjudicated and never default to zero.",
    }
    return rows, worksheet, summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({key for row in rows for key in row}, key=lambda key: (key not in ("asset_id", "code"), key))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", restval="")
        writer.writeheader()
        writer.writerows(rows)


def run(repo: Path) -> dict[str, Any]:
    evidence = load_json(repo / "config" / "crypto_evidence_tranche_a.json")
    rows, worksheet, summary = audit(evidence, load_json(repo / "config" / "crypto_economic_design.json"),
                                     load_json(repo / "config" / "assets.json"))
    out = repo / "data/processed/01_classification"
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "crypto_evidence_tranche_a.csv", rows)
    write_csv(out / "crypto_evidence_tranche_a_blind_review.csv", worksheet)
    (out / "crypto_evidence_tranche_a_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit the tranche A rule-mechanical evidence draft and emit its blind review worksheet")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
