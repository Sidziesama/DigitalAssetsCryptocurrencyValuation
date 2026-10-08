from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


CODES = ("VA_MONETARY", "VA_GAS", "VA_STAKE", "VA_BURN", "VA_SCARCITY", "VA_COLLATERAL", "VA_GOV", "VA_PROTOCOL", "VA_UTILITY", "VA_INCENTIVE")
RULES = {
    "VA_MONETARY": "Material money, settlement, reserve, or store-of-value use supported by at least two behavioral tests.",
    "VA_GAS": "Token is protocol-required for ordinary transaction, computation, storage, or blockspace fees.",
    "VA_STAKE": "Token is locked, delegated, or economically at risk to secure a network or protocol service.",
    "VA_BURN": "A live rules-based mechanism irreversibly destroys tokens.",
    "VA_SCARCITY": "A credible hard cap or deterministic terminal bound exists and is exceptionally difficult to change.",
    "VA_COLLATERAL": "Collateral TVL is at least 1% of market cap or $100m for at least 90 days.",
    "VA_GOV": "Holding or delegating provides live proposal, voting, veto, treasury, or parameter control.",
    "VA_PROTOCOL": "A live mechanical route sends protocol revenue or surplus to the token or holders through distribution, buyback, burn, or an enforceable holder claim; governance over ecosystem spending alone does not qualify.",
    "VA_UTILITY": "Token is required to consume an identifiable non-generic service beyond transfer.",
    "VA_INCENTIVE": "A systematic program subsidizes liquidity, usage, development, or participation.",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(spec: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    if spec.get("schema_version") != 1:
        raise ValueError("unsupported crypto economic-design schema")
    if tuple(spec.get("value_accrual_codes", [])) != CODES:
        raise ValueError("value-accrual code order must match the formal codebook")
    registry_crypto = {a["asset_id"] for a in registry["assets"] if a["universe"] == "crypto"}
    rows = spec.get("assets")
    if not isinstance(rows, list) or not rows:
        raise ValueError("assets must be a non-empty list")
    ids = [row.get("asset_id") for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate crypto economic-design asset_id")
    if set(ids) != registry_crypto:
        missing, extra = sorted(registry_crypto - set(ids)), sorted(set(ids) - registry_crypto)
        raise ValueError(f"economic-design universe mismatch; missing={missing}, extra={extra}")
    for row in rows:
        if not isinstance(row.get("consensus"), str) or not row["consensus"]:
            raise ValueError(f"missing consensus for {row.get('asset_id')}")
        values = row.get("codes")
        if not isinstance(values, list) or len(values) != len(CODES) or any(v not in {0, 1} for v in values):
            raise ValueError(f"codes for {row.get('asset_id')} must contain ten binary values")
    return rows


def build_profiles(spec: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    assets = {a["asset_id"]: a for a in registry["assets"]}
    rows = validate(spec, registry)
    profiles = []
    for row in rows:
        flags = dict(zip(CODES, row["codes"]))
        capture = int(bool(flags["VA_BURN"] or flags["VA_PROTOCOL"]))
        profiles.append({
            "asset_id": row["asset_id"], "symbol": assets[row["asset_id"]]["symbol"],
            "selection_tier": assets[row["asset_id"]]["tier"], "valid_from": spec["as_of"],
            "consensus": row["consensus"], **{code.lower(): flags[code] for code in CODES},
            "va_breadth_count": sum(row["codes"]), "direct_capture_active": capture,
            "h2_capture_group": "active_capture" if capture else "no_active_capture",
            "classification_status": spec["status"],
        })
    return profiles


def build_review(spec: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    assets = {a["asset_id"]: a for a in registry["assets"]}
    validate(spec, registry)
    return [{
        "asset_id": row["asset_id"], "symbol": assets[row["asset_id"]]["symbol"],
        "valid_from": spec["as_of"], "consensus_context": row["consensus"], "code": code,
        "decision_0_or_1": "", "confidence_low_medium_high": "", "evidence_url": "",
        "evidence_date": "", "reviewer_note": "", "rule": RULES[code],
    } for row in spec["assets"] for code in CODES]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_completed_review(rows: list[dict[str, str]], spec: dict[str, Any]) -> dict[tuple[str, str], dict[str, str]]:
    expected = {(row["asset_id"], code) for row in spec["assets"] for code in CODES}
    indexed = {(row.get("asset_id", ""), row.get("code", "")): row for row in rows}
    if set(indexed) != expected or len(indexed) != len(rows):
        raise ValueError("targeted review must contain exactly one row per asset-function cell")
    for key, row in indexed.items():
        decision = row.get("decision_0_or_1", "")
        if decision not in {"", "0", "1"}:
            raise ValueError(f"invalid targeted-review decision: {key}")
        if decision and not all(row.get(field) for field in ("evidence_url", "evidence_date", "reviewer_note")):
            raise ValueError(f"completed targeted-review decision lacks provenance: {key}")
    return indexed


def apply_review(profiles: list[dict[str, Any]], review: list[dict[str, str]], spec: dict[str, Any]) -> list[dict[str, Any]]:
    indexed = validate_completed_review(review, spec)
    for profile in profiles:
        decisions = [indexed[(profile["asset_id"], code)]["decision_0_or_1"] for code in CODES]
        if all(value in {"0", "1"} for value in decisions):
            values = [int(value) for value in decisions]
            for code, value in zip(CODES, values):
                profile[code.lower()] = value
            profile["va_breadth_count"] = sum(values)
            profile["direct_capture_active"] = int(bool(values[CODES.index("VA_BURN")] or values[CODES.index("VA_PROTOCOL")]))
            profile["h2_capture_group"] = "active_capture" if profile["direct_capture_active"] else "no_active_capture"
            profile["classification_status"] = "complete_human_verified"
    return profiles


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def run(repo: Path) -> dict[str, Any]:
    spec = load_json(repo / "config" / "crypto_economic_design.json")
    registry = load_json(repo / "config" / "assets.json")
    profiles = build_profiles(spec, registry)
    out = repo / "data" / "processed" / "01_classification"
    review_path = out / "crypto_economic_design_targeted_review.csv"
    review = read_csv(review_path) if review_path.exists() else build_review(spec, registry)
    profiles = apply_review(profiles, review, spec)
    write_csv(out / "crypto_economic_design_profiles.csv", profiles)
    if not review_path.exists():
        write_csv(review_path, review)
    counts = Counter(p["consensus"] for p in profiles)
    summary = {
        "status": spec["status"], "assets": len(profiles), "review_decisions": len(review),
        "active_capture_assets": sum(p["direct_capture_active"] for p in profiles),
        "mean_va_breadth": sum(p["va_breadth_count"] for p in profiles) / len(profiles),
        "consensus_counts": dict(sorted(counts.items())),
        "complete_human_verified_assets": sum(p["classification_status"] == "complete_human_verified" for p in profiles),
        "next_requirement": "Use the completed human-verified matrix in separately versioned downstream analyses; do not revise rules from outcomes.",
    }
    (out / "crypto_economic_design_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate and build non-stable crypto economic-design inputs")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
