from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .historical import write_rows
from .registry import load_json, validate_asset_config


def validate(plan: dict[str, Any], asset_config: dict[str, Any], extractions: dict[str, Any] | None = None) -> None:
    if plan.get("schema_version") != 1:
        raise ValueError("unsupported evidence-plan schema")
    configured = {asset["asset_id"] for asset in validate_asset_config(asset_config)}
    selected = plan.get("selected_assets", [])
    if len(selected) != 8 or len(set(selected)) != 8:
        raise ValueError("evidence plan must contain exactly eight unique selected assets")
    if not set(selected) <= configured:
        raise ValueError("evidence plan contains unknown assets")
    records = plan.get("assets", [])
    if {row.get("asset_id") for row in records} != set(selected):
        raise ValueError("selected_assets and asset evidence records do not match")
    required = set(plan.get("required_evidence_classes", []))
    allowed = set(plan.get("allowed_extraction_statuses", []))
    if not required or not allowed:
        raise ValueError("evidence classes and extraction statuses are required")
    for asset in records:
        if not asset.get("sources"):
            raise ValueError(f"no sources for {asset.get('asset_id')}")
        for source in asset["sources"]:
            if not str(source.get("url", "")).startswith("https://"):
                raise ValueError(f"invalid evidence URL for {asset['asset_id']}")
            if source.get("extraction_status") not in allowed:
                raise ValueError(f"invalid extraction status for {asset['asset_id']}")
            if not set(source.get("evidence_classes", [])) <= required:
                raise ValueError(f"unknown evidence class for {asset['asset_id']}")
    if extractions is None:
        return
    if extractions.get("schema_version") != 1:
        raise ValueError("unsupported evidence-extraction schema")
    source_urls = {
        asset["asset_id"]: {source["url"] for source in asset["sources"]}
        for asset in records
    }
    seen: set[tuple[str, str]] = set()
    for row in extractions.get("extractions", []):
        key = (row.get("asset_id"), row.get("evidence_class"))
        if key in seen:
            raise ValueError(f"duplicate verified extraction for {key}")
        seen.add(key)
        if key[0] not in selected or key[1] not in required:
            raise ValueError(f"unknown extraction asset or class for {key}")
        if row.get("source_url") not in source_urls[key[0]]:
            raise ValueError(f"extraction source is not registered in the evidence plan for {key}")
        required_fields = (
            "source_title", "publication_or_effective_date", "locator",
            "evidence_summary", "verified_by", "verification_date",
        )
        if row.get("verification_status") != "verified_extracted":
            raise ValueError(f"invalid verification status for {key}")
        if any(not row.get(field) for field in required_fields):
            raise ValueError(f"incomplete verified extraction for {key}")


def build_audit(plan: dict[str, Any], extractions: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    required = plan["required_evidence_classes"]
    verified_by_cell = {
        (row["asset_id"], row["evidence_class"]): row
        for row in (extractions or {}).get("extractions", [])
        if row.get("verification_status") == "verified_extracted"
        and row.get("publication_or_effective_date")
    }
    matrix: list[dict[str, Any]] = []
    summary: list[dict[str, Any]] = []
    for asset in plan["assets"]:
        sources = asset["sources"]
        for evidence_class in required:
            candidates = [source for source in sources if evidence_class in source["evidence_classes"]]
            verified = [verified_by_cell[(asset["asset_id"], evidence_class)]] if (asset["asset_id"], evidence_class) in verified_by_cell else []
            matrix.append({
                "asset_id": asset["asset_id"], "design_type": asset["design_type"],
                "evidence_class": evidence_class, "candidate_source_count": len(candidates),
                "verified_dated_source_count": len(verified),
                "candidate_coverage": int(bool(candidates)), "verified_coverage": int(bool(verified)),
                "status": "pass" if verified else ("extract" if candidates else "source_required"),
            })
        asset_rows = [row for row in matrix if row["asset_id"] == asset["asset_id"]]
        summary.append({
            "asset_id": asset["asset_id"], "design_type": asset["design_type"],
            "source_count": len(sources), "required_classes": len(required),
            "classes_with_candidates": sum(row["candidate_coverage"] for row in asset_rows),
            "classes_verified_dated": sum(row["verified_coverage"] for row in asset_rows),
            "point_in_time_score_ready": int(all(row["verified_coverage"] for row in asset_rows)),
            "status": "ready" if all(row["verified_coverage"] for row in asset_rows) else "evidence_extraction_required",
        })
    return matrix, summary


def run(repo: Path) -> dict[str, Any]:
    plan = load_json(repo / "config" / "stablecoin_evidence_plan.json")
    extraction_path = repo / "config" / "stablecoin_evidence_extractions.json"
    extractions = load_json(extraction_path) if extraction_path.exists() else {"schema_version": 1, "extractions": []}
    assets = load_json(repo / "config" / "assets.json")
    validate(plan, assets, extractions)
    matrix, asset_summary = build_audit(plan, extractions)
    out = repo / "data" / "processed" / "evidence"
    write_rows(out / "stablecoin_evidence_class_matrix.csv", matrix, ["asset_id", "design_type", "evidence_class", "candidate_source_count", "verified_dated_source_count", "candidate_coverage", "verified_coverage", "status"])
    write_rows(out / "stablecoin_evidence_asset_readiness.csv", asset_summary, ["asset_id", "design_type", "source_count", "required_classes", "classes_with_candidates", "classes_verified_dated", "point_in_time_score_ready", "status"])
    result = {
        "plan_version": plan["plan_version"], "extraction_version": extractions.get("extraction_version"),
        "selected_assets": len(asset_summary),
        "required_evidence_classes": len(plan["required_evidence_classes"]),
        "candidate_coverage_cells": sum(row["candidate_coverage"] for row in matrix),
        "total_required_cells": len(matrix),
        "verified_dated_cells": sum(row["verified_coverage"] for row in matrix),
        "point_in_time_score_ready_assets": sum(row["point_in_time_score_ready"] for row in asset_summary),
        "status": "ready" if all(row["point_in_time_score_ready"] for row in asset_summary) else "extraction_checkpoint",
    }
    (out / "stablecoin_evidence_summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    queue = "\n".join(f"- `{row['asset_id']}` — {row['classes_verified_dated']}/{row['required_classes']} evidence classes verified and dated; {row['source_count']} official source candidates." for row in asset_summary)
    findings = repo / "research" / "findings" / "stablecoin-point-in-time-evidence.md"
    findings.write_text(f"""# Stablecoin Point-in-Time Evidence Checkpoint

- Selected assets: {result['selected_assets']}.
- Required evidence classes per asset: {result['required_evidence_classes']}.
- Required asset-class cells: {result['total_required_cells']}.
- Cells with at least one official source candidate: {result['candidate_coverage_cells']}.
- Cells with a verified extraction and source date: {result['verified_dated_cells']}.
- Assets ready for point-in-time scoring: {result['point_in_time_score_ready_assets']}.
- Status: `{result['status']}`.

## Extraction queue

{queue}

Source discovery is not treated as completed evidence extraction. A score becomes point-in-time ready only after every required evidence class has a dated, verified extraction with reconstructible component rationale. The eight-asset scope is fixed before H5/H6 estimation to prevent outcome-based evidence selection.
""", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit the focused eight-asset stablecoin point-in-time evidence plan")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(run(args.repo.resolve()), indent=2))


if __name__ == "__main__":
    main()
