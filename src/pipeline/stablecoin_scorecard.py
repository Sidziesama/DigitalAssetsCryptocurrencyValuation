from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from .registry import load_json


def validate(config: dict[str, Any], extractions: dict[str, Any]) -> None:
    if config.get("schema_version") != 1:
        raise ValueError("unsupported scorecard schema")
    scale = config.get("scale", {})
    low, high = scale.get("minimum"), scale.get("maximum")
    if not isinstance(low, int) or not isinstance(high, int) or low >= high:
        raise ValueError("invalid ordinal scale")
    dimensions = config.get("dimensions", {})
    if not dimensions or sum(item.get("weight", 0) for item in dimensions.values()) != 100:
        raise ValueError("dimension weights must sum to 100")
    if set(config.get("rubric", {})) != set(dimensions):
        raise ValueError("every dimension requires a rubric")
    friction = config.get("derived_scores", {}).get("redemption_friction", {})
    friction_inputs = friction.get("quality_inputs", {})
    if set(friction_inputs) != {"redemption_access_quality", "operational_resilience"} or sum(friction_inputs.values()) != 100:
        raise ValueError("redemption-friction quality inputs must contain access and resilience and sum to 100")
    expected_levels = {str(level) for level in range(low, high + 1)}
    for name, rubric in config["rubric"].items():
        if set(rubric) != expected_levels:
            raise ValueError(f"incomplete rubric for {name}")
    verified = {
        (row["asset_id"], row["evidence_class"])
        for row in extractions.get("extractions", [])
        if row.get("verification_status") == "verified_extracted"
        and row.get("publication_or_effective_date")
    }
    assets = config.get("assets", [])
    if len(assets) != 8 or len({asset.get("asset_id") for asset in assets}) != 8:
        raise ValueError("scorecard requires exactly eight unique assets")
    for asset in assets:
        if set(asset.get("scores", {})) != set(dimensions):
            raise ValueError(f"incomplete component scores for {asset.get('asset_id')}")
        if not asset.get("rationale") or asset.get("confidence") not in {"low", "medium", "high"}:
            raise ValueError(f"missing rationale or confidence for {asset.get('asset_id')}")
        if not asset.get("availability_basis"):
            raise ValueError(f"missing availability basis for {asset.get('asset_id')}")
        available = date.fromisoformat(asset["available_from_date"])
        if available > date.fromisoformat(config["as_of_date"]):
            raise ValueError(f"availability date follows scorecard date for {asset.get('asset_id')}")
        for name, score in asset["scores"].items():
            if not isinstance(score, int) or not low <= score <= high:
                raise ValueError(f"invalid {name} score for {asset['asset_id']}")
            evidence_class = dimensions[name]["evidence_class"]
            if (asset["asset_id"], evidence_class) not in verified:
                raise ValueError(f"missing verified evidence for {asset['asset_id']} {name}")


def normalized(score: int, low: int, high: int) -> float:
    return 100 * (score - low) / (high - low)


def evaluate(config: dict[str, Any], extractions: dict[str, Any]) -> list[dict[str, Any]]:
    validate(config, extractions)
    low, high = config["scale"]["minimum"], config["scale"]["maximum"]
    rows: list[dict[str, Any]] = []
    for asset in config["assets"]:
        row: dict[str, Any] = {
            "asset_id": asset["asset_id"], "as_of_date": config["as_of_date"],
            "available_from_date": asset["available_from_date"], "availability_basis": asset["availability_basis"],
            "methodology_version": config["methodology_version"], "confidence": asset["confidence"],
        }
        weighted_quality = 0.0
        for name, metadata in config["dimensions"].items():
            value = normalized(asset["scores"][name], low, high)
            row[f"{name}_ordinal"] = asset["scores"][name]
            row[f"{name}_score"] = value
            weighted_quality += value * metadata["weight"] / 100
        row["overall_design_quality_score"] = weighted_quality
        friction_inputs = config["derived_scores"]["redemption_friction"]["quality_inputs"]
        if all(f"{name}_score" in row for name in friction_inputs):
            friction_quality = sum(row[f"{name}_score"] * weight / 100 for name, weight in friction_inputs.items())
            row["redemption_friction_score"] = 100 - friction_quality
        if "operational_resilience_score" in row:
            row["operational_constraint_score"] = 100 - row["operational_resilience_score"]
        row["rationale"] = asset["rationale"]
        rows.append(row)
    return rows


def render_findings(rows: list[dict[str, Any]]) -> str:
    items = "\n".join(
        f"- `{row['asset_id']}` — design quality {row['overall_design_quality_score']:.1f}; "
        f"backing {row['backing_quality_score']:.1f}; verification {row['verification_quality_score']:.1f}; "
        f"redemption friction {row['redemption_friction_score']:.1f}; confidence `{row['confidence']}`."
        for row in rows
    )
    return f"""# Stablecoin Point-in-Time Scorecard

**Status:** Developmental input for H5--H6; not an estimated empirical result.

{items}

All components use a documented 0--4 ordinal rubric normalized to 0--100. Higher backing, verification, access, legal-protection, operational-resilience, and overall-design scores are better. Redemption-friction and operational-constraint scores reverse their corresponding quality components so higher values indicate worse conditions. Scores are accepted only when the matching evidence class has a dated verified extraction. Medium-confidence protocol scores require targeted review before preregistration is frozen.
"""


def run(repo: Path) -> dict[str, Any]:
    config = load_json(repo / "config" / "stablecoin_scorecard.json")
    extractions = load_json(repo / "config" / "stablecoin_evidence_extractions.json")
    rows = evaluate(config, extractions)
    out = repo / "data" / "processed" / "evidence" / "stablecoin_point_in_time_scorecard.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    findings = repo / "research" / "findings" / "stablecoin-point-in-time-scorecard.md"
    findings.parent.mkdir(parents=True, exist_ok=True)
    findings.write_text(render_findings(rows), encoding="utf-8")
    return {"assets_scored": len(rows), "methodology_version": config["methodology_version"], "status": "developmental_review_required"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the verified eight-asset stablecoin point-in-time scorecard")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(run(args.repo.resolve()), indent=2))


if __name__ == "__main__":
    main()
