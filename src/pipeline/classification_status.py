from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

CODES = ["VA_MONETARY", "VA_GAS", "VA_STAKE", "VA_BURN", "VA_SCARCITY",
         "VA_COLLATERAL", "VA_GOV", "VA_PROTOCOL", "VA_UTILITY", "VA_INCENTIVE"]

DEFINITIONS = {
    "sourced": "A coder assigned a binary value backed by a dated primary source, audited against the design matrix. NOT independently reviewed.",
    "reviewed": "Sourced AND scored blind by a second reviewer, with agreement and Cohen's kappa computed. This is the only state that supports a reliability claim.",
    "pending": "Held for adjudication. Carries no value; never defaults to zero.",
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
    crypto = [a["asset_id"] for a in registry["assets"] if a["universe"] == "crypto"]

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

    counts = {name: sum(1 for v in state.values() if v == name) for name in DEFINITIONS}
    evidence_backed = counts["sourced"] + counts["reviewed"]
    summary = {
        "status": "classification_status_complete",
        "total_cells": len(state),
        "assets": len(crypto),
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
