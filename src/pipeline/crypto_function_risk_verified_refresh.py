from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .crypto_function_risk_exposure import build, read_csv, write_csv


LOCKED_FIELDS = ("window", "outcomes", "predictors", "control", "model", "inference")


def merged_spec(refresh: dict[str, Any], parent: dict[str, Any]) -> dict[str, Any]:
    if refresh.get("status") != "frozen_before_verified_input_refresh":
        raise ValueError("verified risk refresh is not frozen")
    if tuple(refresh.get("locked_from_parent", [])) != LOCKED_FIELDS:
        raise ValueError("the locked parent fields changed")
    result = dict(parent)
    for field in LOCKED_FIELDS:
        if field not in parent:
            raise ValueError(f"parent risk specification is missing {field}")
    result.update({
        "document_version": refresh["document_version"],
        "freeze_date": refresh["freeze_date"],
        "experiment_id": refresh["experiment_id"],
        "verified_profiles": refresh["verified_profiles"],
        "samples": [refresh["sample"]],
        "interpretation": refresh["interpretation"]
    })
    return result


def validate_profiles(refresh: dict[str, Any], profiles: list[dict[str, str]]) -> None:
    expected = int(refresh["expected_classification_assets"])
    status = refresh["expected_classification_status"]
    if len(profiles) != expected:
        raise ValueError(f"expected {expected} classification profiles, found {len(profiles)}")
    invalid = [row.get("asset_id", "") for row in profiles if row.get("classification_status") != status]
    if invalid:
        raise ValueError(f"classification profiles are not complete: {invalid}")


def run(repo: Path) -> dict[str, Any]:
    refresh = json.loads((repo / "config/crypto_function_risk_verified_refresh.json").read_text())
    parent = json.loads((repo / refresh["parent_specification"]).read_text())
    spec = merged_spec(refresh, parent)
    profiles = read_csv(repo / refresh["verified_profiles"])
    validate_profiles(refresh, profiles)
    asset_rows, result_rows, summary = build(
        spec,
        read_csv(repo / spec["panel"]),
        profiles,
        json.loads((repo / spec["provisional_design"]).read_text()),
        json.loads((repo / spec["bundle_map"]).read_text())
    )
    summary["refresh_type"] = "classification_input_only"
    summary["parent_specification"] = refresh["parent_specification"]
    summary["classification_profiles"] = len(profiles)
    output = repo / "data/processed/03_risk"
    write_csv(output / "crypto_function_risk_verified_assets.csv", asset_rows)
    write_csv(output / "crypto_function_risk_verified_tests.csv", result_rows)
    (output / "crypto_function_risk_verified_refresh.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Refresh the frozen function-risk test using completed classifications")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
