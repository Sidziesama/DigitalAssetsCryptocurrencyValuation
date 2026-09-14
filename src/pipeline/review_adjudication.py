from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def cohen_kappa(pairs: list[tuple[int, int]], categories: list[int]) -> float | None:
    if not pairs:
        return None
    observed = sum(left == right for left, right in pairs) / len(pairs)
    expected = sum(
        (sum(left == value for left, _ in pairs) / len(pairs))
        * (sum(right == value for _, right in pairs) / len(pairs))
        for value in categories
    )
    return 1.0 if expected == 1.0 and observed == 1.0 else (observed - expected) / (1.0 - expected)


def _validate_grid(rows: list[dict[str, str]], expected: set[tuple[str, str]], key_field: str) -> None:
    keys = [(row.get("asset_id", ""), row.get(key_field, "")) for row in rows]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError("review must preserve exactly one row per predeclared decision")


def audit_crypto(
    rows: list[dict[str, str]], evidence: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    primary = {(row["asset_id"], row["code"]): row["recommended_value"] for row in evidence["decisions"]}
    _validate_grid(rows, set(primary), "code")
    audited: list[dict[str, Any]] = []
    for row in rows:
        raw = row.get("reviewer_value", "").strip()
        complete = bool(raw)
        if complete and raw not in {"0", "1"}:
            raise ValueError("crypto reviewer_value must be blank, 0, or 1")
        if complete and (not row.get("reviewer_source_url", "").startswith("https://") or not row.get("reviewer_rationale", "").strip()):
            raise ValueError("completed crypto reviews require an HTTPS source and rationale")
        key = (row["asset_id"], row["code"])
        value = int(raw) if complete else None
        audited.append({**row, "primary_value": primary[key], "agreement": "" if value is None else int(value == primary[key])})
    return _summarize(audited, "reviewer_value", [0, 1], "primary_value", "crypto_h2_expansion")


def audit_stablecoin(
    rows: list[dict[str, str]], scorecard: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    primary = {
        (asset["asset_id"], dimension): value
        for asset in scorecard["assets"]
        for dimension, value in asset["scores"].items()
    }
    _validate_grid(rows, set(primary), "dimension")
    audited: list[dict[str, Any]] = []
    identity_fields = ["reviewer_confidence", "reviewer_rationale", "reviewer_name_or_id", "review_date"]
    for row in rows:
        raw = row.get("reviewer_score_0_to_4", "").strip()
        complete = bool(raw)
        if complete and raw not in {"0", "1", "2", "3", "4"}:
            raise ValueError("stablecoin reviewer score must be blank or an integer from 0 to 4")
        if complete and any(not row.get(field, "").strip() for field in identity_fields):
            raise ValueError("completed stablecoin reviews require confidence, rationale, reviewer ID, and date")
        key = (row["asset_id"], row["dimension"])
        value = int(raw) if complete else None
        audited.append({**row, "primary_value": primary[key], "agreement": "" if value is None else int(value == primary[key])})
    return _summarize(audited, "reviewer_score_0_to_4", list(range(5)), "primary_value", "stablecoin_h5_h6")


def _summarize(
    rows: list[dict[str, Any]], reviewer_field: str, categories: list[int], primary_field: str, review_id: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    completed = [row for row in rows if str(row.get(reviewer_field, "")).strip()]
    pairs = [(int(row[primary_field]), int(row[reviewer_field])) for row in completed]
    disagreements = [row for row in completed if row["agreement"] == 0]
    complete = len(completed) == len(rows)
    summary = {
        "review_id": review_id,
        "status": "complete_adjudication_pending" if complete and disagreements else "complete_no_disagreements" if complete else "independent_review_pending",
        "targeted_decisions": len(rows),
        "completed_decisions": len(completed),
        "pending_decisions": len(rows) - len(completed),
        "agreements": len(completed) - len(disagreements),
        "disagreements": len(disagreements),
        "raw_agreement": (len(completed) - len(disagreements)) / len(completed) if completed else None,
        "cohen_kappa": cohen_kappa(pairs, categories) if complete else None,
        "freeze_eligible": complete and not disagreements,
    }
    return rows, summary


def write_audit(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def run(repo: Path) -> dict[str, Any]:
    crypto_dir = repo / "data/processed/01_classification"
    stable_dir = repo / "data/processed/04_stablecoin_deferred"
    private_dir = repo / "review_inputs"
    crypto_evidence = json.loads((repo / "config/crypto_h2_expansion_evidence.json").read_text(encoding="utf-8"))
    scorecard = json.loads((repo / "config/stablecoin_scorecard.json").read_text(encoding="utf-8"))
    scope = json.loads((repo / "config/research_scope.json").read_text(encoding="utf-8"))
    crypto_input = private_dir / "crypto_h2_expansion_blind_review.csv"
    stable_input = private_dir / "stablecoin_score_targeted_review.csv"
    crypto_rows, crypto_summary = audit_crypto(
        read_csv(crypto_input if crypto_input.exists() else crypto_dir / "crypto_h2_expansion_blind_review.csv"), crypto_evidence
    )
    stable_rows, stable_summary = audit_stablecoin(
        read_csv(stable_input if stable_input.exists() else stable_dir / "stablecoin_score_targeted_review.csv"), scorecard
    )
    stable_summary["phase_status"] = scope["deferred_phase"]["status"]
    stable_summary["active_gate"] = False
    write_audit(crypto_dir / "crypto_h2_expansion_review_audit.csv", crypto_rows)
    write_audit(stable_dir / "stablecoin_score_review_audit.csv", stable_rows)
    result = {
        "status": "active_crypto_review_complete" if crypto_summary["freeze_eligible"] else crypto_summary["status"],
        "crypto_h2_expansion": crypto_summary,
        "stablecoin_h5_h6": stable_summary,
        "freeze_guardrail": "The active crypto specification may freeze only after its complete independent review has no unresolved disagreements; deferred stablecoin review does not gate the crypto phase.",
        "input_policy": "Completed worksheets belong in the Git-ignored review_inputs directory; generated blank templates remain reproducible pipeline outputs.",
    }
    (crypto_dir / "independent_review_summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate blind reviews and generate agreement/adjudication audits")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
