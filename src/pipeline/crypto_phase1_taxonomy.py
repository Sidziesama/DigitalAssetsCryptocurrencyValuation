from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from src.pipeline.crypto_economic_design import CODES, RULES


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_evidence(repo: Path) -> list[dict[str, Any]]:
    focused = load_json(repo / "config/crypto_design_evidence_tranche_1.json")["decisions"]
    extended = []
    for path in sorted((repo / "config").glob("crypto_h8_evidence_tranche_*.json")):
        extended.extend(load_json(path)["decisions"])
    return focused + extended


def validate(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1 or spec.get("phase") != "phase_1_cryptoasset_economic_function_taxonomy":
        raise ValueError("unsupported Phase 1 taxonomy configuration")
    assets = spec.get("verified_core_assets", [])
    if len(assets) != 6 or len(assets) != len(set(assets)):
        raise ValueError("Phase 1 verified core must contain six unique assets")
    bundle_codes = [code for codes in spec.get("bundles", {}).values() for code in codes]
    if len(bundle_codes) != len(set(bundle_codes)) or set(bundle_codes) != set(CODES):
        raise ValueError("Phase 1 bundles must partition the ten function codes")
    if set(spec.get("value_indicators", {})) != set(CODES) or any(not values for values in spec["value_indicators"].values()):
        raise ValueError("Phase 1 value indicators must cover all ten function codes")
    if set(spec.get("architecture_context", {})) != set(assets):
        raise ValueError("Phase 1 architecture context must cover the verified core")
    experiments = spec.get("experiments", [])
    ids = [row.get("id") for row in experiments]
    if len(ids) < 3 or len(ids) != len(set(ids)):
        raise ValueError("Phase 1 experiments must have unique identifiers")
    for row in spec.get("adjudications", []):
        if row.get("asset_id") not in assets or row.get("code") not in CODES or row.get("value") not in (0, 1):
            raise ValueError("invalid Phase 1 adjudication")
        if not str(row.get("source_url", "")).startswith("https://") or not row.get("rationale"):
            raise ValueError("Phase 1 adjudication requires source and rationale")


def build(spec: dict[str, Any], evidence: list[dict[str, Any]], symbols: dict[str, str]) -> dict[str, Any]:
    validate(spec)
    keys = [(row.get("asset_id"), row.get("code")) for row in evidence]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate Phase 1 evidence decision")
    index = {key: row for key, row in zip(keys, evidence)}
    adjudications = {(row["asset_id"], row["code"]): row for row in spec.get("adjudications", [])}
    profiles = []
    for asset_id in spec["verified_core_assets"]:
        values: dict[str, int | None] = {}
        states: dict[str, str] = {}
        for code in CODES:
            row = index.get((asset_id, code))
            if row is None or row.get("status") != "verified":
                values[code] = None; states[code] = "unresolved"
            else:
                value = row.get("recommended_value")
                if value not in (0, 1):
                    raise ValueError(f"verified decision must be binary: {asset_id} {code}")
                values[code] = int(value)
                states[code] = "verified_positive" if value == 1 else "verified_negative"
            adjudication = adjudications.get((asset_id, code))
            if adjudication:
                values[code] = int(adjudication["value"])
                states[code] = "verified_positive" if adjudication["value"] == 1 else "verified_negative"
        bundles = {}
        for name, codes in spec["bundles"].items():
            observed = [values[code] for code in codes]
            bundles[name] = None if any(value is None for value in observed) else int(any(observed))
        verified = sum(value is not None for value in values.values())
        profiles.append({
            "asset_id": asset_id, "symbol": symbols.get(asset_id, asset_id),
            "architecture_context": spec["architecture_context"][asset_id],
            **{code.lower(): values[code] for code in CODES},
            "verified_code_count": verified, "unresolved_code_count": len(CODES) - verified,
            "raw_function_breadth": sum(value == 1 for value in values.values()) if verified == len(CODES) else None,
            "active_bundle_count": sum(value == 1 for value in bundles.values()) if all(value is not None for value in bundles.values()) else None,
            **{f"bundle_{name}": value for name, value in bundles.items()},
            "classification_status": "complete_verified" if verified == len(CODES) else "partial_unresolved",
            "adjudicated_code_count": sum((asset_id, code) in adjudications for code in CODES),
        })
    prevalence = []
    for code in CODES:
        vals = [row[code.lower()] for row in profiles]
        observed = [value for value in vals if value is not None]
        prevalence.append({
            "code": code, "verified_assets": len(observed), "positive_assets": sum(observed),
            "negative_assets": len(observed) - sum(observed), "unresolved_assets": len(vals) - len(observed),
            "positive_share_of_verified": sum(observed) / len(observed) if observed else None,
        })
    return {"profiles": profiles, "prevalence": prevalence}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def run(repo: Path) -> dict[str, Any]:
    spec = load_json(repo / "config/crypto_phase1_taxonomy.json")
    registry = load_json(repo / "config/assets.json")
    symbols = {row["asset_id"]: row["symbol"] for row in registry["assets"]}
    result = build(spec, load_evidence(repo), symbols)
    profiles, prevalence = result["profiles"], result["prevalence"]
    out = repo / "data/processed/01_classification"
    write_csv(out / "crypto_phase1_taxonomy_profiles.csv", profiles)
    write_csv(out / "crypto_phase1_function_prevalence.csv", prevalence)
    codebook = [{
        "code": code,
        "bundle": next(name for name, codes in spec["bundles"].items() if code in codes),
        "classification_rule": RULES[code],
        "value_indicators": "|".join(spec["value_indicators"][code]),
    } for code in CODES]
    write_csv(out / "crypto_phase1_function_codebook.csv", codebook)
    consistency_rows = [{**row, "assets": "|".join(row["assets"])} for row in spec["consistency_cases"]]
    write_csv(out / "crypto_phase1_consistency_audit.csv", consistency_rows)
    experiments = {
        "status": "phase1_experiment_registry_frozen_before_new_tests",
        "as_of": spec["as_of"], "experiments": spec["experiments"],
        "guardrails": [
            "Raw breadth and theory-defined bundles must be reported separately.",
            "No function weights may be selected from the outcome being tested.",
            "Mechanism states must be effective-dated and cannot be backfilled.",
            "Architecture labels are controls or strata, not value-accrual outcomes.",
            "The frozen exploratory H2 result used the older broad treasury-capture rule and is not relabeled as evidence under the strict Phase 1 rule."
        ]
    }
    (out / "crypto_phase1_experiment_registry.json").write_text(json.dumps(experiments, indent=2) + "\n", encoding="utf-8")
    unresolved = [{"asset_id": row["asset_id"], "code": code.upper()}
                  for row in profiles for code, value in row.items()
                  if code.startswith("va_") and value is None]
    verified = sum(row["verified_code_count"] for row in profiles)
    target = len(profiles) * len(CODES)
    summary = {
        "status": "phase1_taxonomy_complete" if verified == target else "phase1_taxonomy_rule_consistent_completion_blocked",
        "as_of": spec["as_of"], "core_assets": len(profiles),
        "complete_verified_assets": sum(row["classification_status"] == "complete_verified" for row in profiles),
        "partial_assets": sum(row["classification_status"] == "partial_unresolved" for row in profiles),
        "verified_decisions": verified,
        "target_decisions": target, "unresolved_decisions": unresolved,
        "function_positive_counts": dict(Counter({row["code"]: row["positive_assets"] for row in prevalence})),
        "consistency_cases_open": sum(row["status"] == "adjudication_required" for row in spec["consistency_cases"]),
        "adjudicated_decisions": len(spec.get("adjudications", [])),
        "descriptive_ready": True, "confirmatory_ready": False,
        "next_gate": "Freeze the completed classification dataset and estimate only separately versioned extensions without changing rules from outcomes." if verified == target else "Resolve remaining evidence, then estimate separately versioned strict-rule experiments without changing rules from outcomes."
    }
    (out / "crypto_phase1_taxonomy_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the verified Phase 1 cryptoasset economic-function taxonomy")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
