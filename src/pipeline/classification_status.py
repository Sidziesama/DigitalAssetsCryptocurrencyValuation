from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.pipeline.crypto_design_evidence import validate_evidence

CODES = ["VA_MONETARY", "VA_GAS", "VA_STAKE", "VA_BURN", "VA_SCARCITY",
         "VA_COLLATERAL", "VA_GOV", "VA_PROTOCOL", "VA_UTILITY", "VA_INCENTIVE"]

DEFINITIONS = {
    "sourced": "A coder assigned a binary value backed by a dated primary source, audited against the design matrix. NOT independently reviewed.",
    "reviewed": "Sourced AND scored blind by a second reviewer, with agreement and Cohen's kappa computed. This is the only state that supports a reliability claim.",
    "pending": "Needs additional evidence or a rule decision. Carries no value; never defaults to zero.",
    "provisional": "Present in the design matrix only. No evidence, no source, no review.",
}
CORE_TRANCHES = ["crypto_design_evidence_tranche_1.json",
                 "crypto_h8_evidence_tranche_1.json",
                 "crypto_h8_evidence_tranche_2.json"]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build(repo: Path) -> dict[str, Any]:
    cfg, proc = repo / "config", repo / "data/processed/01_classification"
    registry = load(cfg / "assets.json")
    scope = load(cfg / "research_scope.json")
    excluded = {row["asset_id"] for row in scope.get("excluded_assets", [])}
    crypto = [a["asset_id"] for a in registry["assets"]
              if a["universe"] == "crypto" and a["asset_id"] not in excluded]

    state: dict[tuple[str, str], str] = {(a, c): "provisional" for a in crypto for c in CODES}

    # sourced: the six-asset core tranches
    core_cells: set[tuple[str, str]] = set()
    for name in CORE_TRANCHES:
        path = cfg / name
        if not path.exists():
            continue
        for dec in load(path).get("decisions", []):
            if dec.get("status") == "verified":
                key = (dec["asset_id"], dec["code"])
                state[key] = "sourced"
                core_cells.add(key)

    # sourced or pending: tranche A
    tranche_a_cells: set[tuple[str, str]] = set()
    path = cfg / "crypto_evidence_tranche_a.json"
    if path.exists():
        for dec in load(path)["decisions"]:
            key = (dec["asset_id"], dec["code"])
            state[key] = "sourced" if dec["status"] == "verified" else "pending"
            tranche_a_cells.add(key)

    for name in ("crypto_evidence_tranche_c.json", "crypto_evidence_remaining_assets.json"):
        path = cfg / name
        if path.exists():
            decisions = validate_evidence(load(path), load(cfg / "crypto_economic_design.json"), registry)
            for dec in decisions:
                key = (dec["asset_id"], dec["code"])
                if key not in state:
                    if dec["asset_id"] in excluded:
                        continue
                    raise ValueError(f"unknown classification cell: {key}")
                state[key] = "sourced" if dec["status"] == "verified" else "pending"

    # The maintained targeted-review matrix records the researcher's final
    # evidence-backed decisions. It supersedes earlier provisional/pending
    # states but is not an independent blind review.
    targeted = proc / "crypto_economic_design_targeted_review.csv"
    if targeted.exists():
        with targeted.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            key = (row.get("asset_id", ""), row.get("code", ""))
            if key in state and row.get("decision_0_or_1") in {"0", "1"}:
                if not all(row.get(field) for field in ("evidence_url", "evidence_date", "reviewer_note")):
                    raise ValueError(f"completed targeted-review decision lacks provenance: {key}")
                state[key] = "sourced"

    # reviewed: only cells covered by a COMPLETED independent blind review
    reviewed: set[tuple[str, str]] = set()
    review = load(proc / "independent_review_summary.json") if (proc / "independent_review_summary.json").exists() else {}
    crypto_review = review.get("crypto_h2_expansion", {})
    expansion = cfg / "crypto_h2_expansion_evidence.json"
    worksheet = repo / "review_inputs/crypto_h2_expansion_blind_review.csv"
    if crypto_review.get("status", "").startswith("complete") and expansion.exists() and worksheet.exists():
        for dec in load(expansion)["decisions"]:
            key = (dec["asset_id"], dec["code"])
            if key in state:
                state[key] = "reviewed"
                reviewed.add(key)

    active = set(crypto)
    state = {key: value for key, value in state.items() if key[0] in active}
    reviewed = {key for key in reviewed if key[0] in active}

    counts = {name: sum(1 for v in state.values() if v == name) for name in DEFINITIONS}
    evidence_backed = counts["sourced"] + counts["reviewed"]
    summary = {
        "status": "classification_status_complete",
        "total_cells": len(state),
        "assets": len(crypto),
        "excluded_assets": sorted(excluded),
        "codes": len(CODES),
        "counts": counts,
        "definitions": DEFINITIONS,
        "evidence_backed": evidence_backed,
        "independently_reviewed": counts["reviewed"],
        "review_coverage_of_evidence_backed": round(counts["reviewed"] / evidence_backed, 4) if evidence_backed else 0.0,
        "reviewed_scope": {
            "assets": sorted({a for a, _ in reviewed}),
            "codes": sorted({c for _, c in reviewed}),
            "cohen_kappa": crypto_review.get("cohen_kappa"),
            "note": "Cohen's kappa applies ONLY to these cells. It is not a reliability statistic for the six-asset core, which has not been independently reviewed.",
        },
        "core_cells_sourced_not_reviewed": len(core_cells - reviewed),
        "headline": (
            f"{evidence_backed} of {len(state)} cells are evidence-backed "
            f"({counts['reviewed']} of those independently reviewed); "
            f"{counts['pending']} pending, {counts['provisional']} provisional."
        ),
    }
    return summary


def run(repo: Path) -> dict[str, Any]:
    summary = build(repo)
    out = repo / "data/processed/01_classification"
    out.mkdir(parents=True, exist_ok=True)
    (out / "classification_status.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Canonical classification status counts")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
