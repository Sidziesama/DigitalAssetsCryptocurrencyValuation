from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from .crypto_economic_design import CODES


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build(registry: dict[str, Any], scope: dict[str, Any], design: dict[str, Any],
          taxonomy: dict[str, Any], review: list[dict[str, str]]) -> dict[str, Any]:
    excluded = {row["asset_id"] for row in scope.get("excluded_assets", [])}
    assets = [row for row in registry["assets"]
              if row["universe"] == "crypto" and row["asset_id"] not in excluded]
    asset_ids = {row["asset_id"] for row in assets}
    architecture = {row["asset_id"]: row["consensus"] for row in design["assets"]}
    indexed = {(row["asset_id"], row["code"]): row for row in review
               if row["asset_id"] in asset_ids}
    expected = {(asset_id, code) for asset_id in asset_ids for code in CODES}
    if set(indexed) != expected:
        missing = sorted(expected - set(indexed))
        extra = sorted(set(indexed) - expected)
        raise ValueError(f"verified universe grid mismatch; missing={missing}, extra={extra}")
    if any(row.get("decision_0_or_1") not in {"0", "1"} for row in indexed.values()):
        raise ValueError("verified universe contains an unresolved decision")

    bundles = taxonomy["bundles"]
    profiles: list[dict[str, Any]] = []
    memberships: list[dict[str, Any]] = []
    for asset in assets:
        values = {code: int(indexed[(asset["asset_id"], code)]["decision_0_or_1"]) for code in CODES}
        bundle_values = {name: int(any(values[code] for code in codes)) for name, codes in bundles.items()}
        active_groups = [name for name, value in bundle_values.items() if value]
        profiles.append({
            "asset_id": asset["asset_id"], "symbol": asset["symbol"],
            "selection_tier": asset["tier"], "architecture_context": architecture[asset["asset_id"]],
            **{code.lower(): values[code] for code in CODES},
            "raw_function_breadth": sum(values.values()),
            "active_bundle_count": sum(bundle_values.values()),
            **{f"bundle_{name}": value for name, value in bundle_values.items()},
            "active_groups": "|".join(active_groups),
            "classification_status": "complete_human_verified",
        })
        for name in active_groups:
            memberships.append({
                "group_id": name, "asset_id": asset["asset_id"], "symbol": asset["symbol"],
                "architecture_context": architecture[asset["asset_id"]],
                "group_definition": "|".join(bundles[name]),
            })

    counts = {name: sum(row[f"bundle_{name}"] for row in profiles) for name in bundles}
    return {"profiles": profiles, "memberships": memberships, "group_counts": counts,
            "assets": len(profiles), "cells": len(profiles) * len(CODES), "excluded_assets": sorted(excluded)}


def run(repo: Path) -> dict[str, Any]:
    cfg = repo / "config"
    out = repo / "data/processed/01_classification"
    result = build(
        load_json(cfg / "assets.json"), load_json(cfg / "research_scope.json"),
        load_json(cfg / "crypto_economic_design.json"), load_json(cfg / "crypto_phase1_taxonomy.json"),
        read_csv(out / "crypto_economic_design_targeted_review.csv"),
    )
    write_csv(out / "crypto_verified_universe_profiles.csv", result["profiles"])
    write_csv(out / "crypto_verified_function_groups.csv", result["memberships"])
    summary = {
        "status": "verified_groups_ready_for_preregistered_hypothesis_extensions",
        "assets": result["assets"], "classification_cells": result["cells"],
        "excluded_assets": result["excluded_assets"], "group_counts": result["group_counts"],
        "grouping_rule": "A bundle is active when any pre-specified member function equals one; assets may belong to multiple groups.",
        "testing_guardrail": "Use only separately versioned specifications. Do not alter group definitions after inspecting outcomes.",
    }
    (out / "crypto_verified_universe_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the complete verified crypto function groups")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
