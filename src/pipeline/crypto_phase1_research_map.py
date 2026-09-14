from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from .crypto_h8_breadth_pilot import read_csv

CODES = ["VA_MONETARY", "VA_GAS", "VA_STAKE", "VA_BURN", "VA_SCARCITY",
         "VA_COLLATERAL", "VA_GOV", "VA_PROTOCOL", "VA_UTILITY", "VA_INCENTIVE"]
STATES = {"observed_series", "partial_series", "documentary_only", "not_collected"}


def validate(spec: dict[str, Any], codebook: list[dict[str, str]], registry: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1 or set(spec.get("observability_states", [])) != STATES:
        raise ValueError("unsupported Phase 1 research map specification")
    observability = spec.get("indicator_observability", {})
    codebook_codes = {row["code"] for row in codebook}
    if codebook_codes != set(CODES):
        raise ValueError("Phase 1 codebook must cover exactly the ten function codes")
    for row in codebook:
        for indicator in row["value_indicators"].split("|"):
            entry = observability.get(indicator)
            if entry is None:
                raise ValueError(f"indicator {indicator} has no observability entry")
            if entry.get("state") not in STATES:
                raise ValueError(f"indicator {indicator} has an invalid observability state")
            if entry["state"] in {"observed_series", "partial_series"} and not (entry.get("dataset") and entry.get("measure")):
                raise ValueError(f"indicator {indicator} claims a series without a dataset and measure")
            if entry["state"] == "not_collected" and entry.get("dataset"):
                raise ValueError(f"indicator {indicator} is not collected but names a dataset")
    experiment_ids = {experiment["id"] for experiment in registry.get("experiments", [])}
    for code in CODES:
        uses = spec.get("experiment_use", {}).get(code)
        if not uses or not set(uses) <= experiment_ids:
            raise ValueError(f"{code} must map to registered Phase 1 experiments")
    if set(spec.get("experiment_status", {})) != experiment_ids:
        raise ValueError("every registered experiment needs exactly one status entry")


def series_coverage(repo: Path, entry: dict[str, Any]) -> dict[str, Any]:
    if entry["state"] not in {"observed_series", "partial_series"}:
        return {"assets_observed": None, "rows_observed": None, "dataset_present": bool(entry.get("dataset")) and (repo / entry["dataset"]).exists()}
    path = repo / entry["dataset"]
    if not path.exists():
        return {"assets_observed": 0, "rows_observed": 0, "dataset_present": False}
    rows = read_csv(path)
    measure = entry["measure"]
    if rows and measure not in rows[0]:
        raise ValueError(f"dataset {entry['dataset']} lacks measure column {measure}")
    populated = [row for row in rows if row.get(measure) not in (None, "")]
    return {"assets_observed": len({row["asset_id"] for row in populated}), "rows_observed": len(populated), "dataset_present": True}


def build(repo: Path, spec: dict[str, Any], codebook: list[dict[str, str]], prevalence: list[dict[str, str]],
          profiles: list[dict[str, str]], registry: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    validate(spec, codebook, registry)
    prevalence_index = {row["code"]: row for row in prevalence}
    observability = spec["indicator_observability"]
    indicator_rows: list[dict[str, Any]] = []
    code_rows: list[dict[str, Any]] = []
    for row in sorted(codebook, key=lambda item: CODES.index(item["code"])):
        code = row["code"]
        indicators = row["value_indicators"].split("|")
        states = []
        for indicator in indicators:
            entry = observability[indicator]
            coverage = series_coverage(repo, entry)
            states.append(entry["state"])
            indicator_rows.append({"code": code, "bundle": row["bundle"], "indicator": indicator, "state": entry["state"],
                                   "dataset": entry.get("dataset") or "", "measure": entry.get("measure") or "",
                                   **coverage, "note": entry.get("note", "")})
        positive_assets = sorted(profile["asset_id"] for profile in profiles if profile[code.lower()] == "1")
        prevalence_row = prevalence_index[code]
        code_rows.append({
            "code": code, "bundle": row["bundle"], "classification_rule": row["classification_rule"],
            "verified_assets": int(prevalence_row["verified_assets"]), "positive_assets": int(prevalence_row["positive_assets"]),
            "positive_asset_ids": "|".join(positive_assets), "indicators": len(indicators),
            "observed_series_indicators": states.count("observed_series"), "partial_series_indicators": states.count("partial_series"),
            "documentary_only_indicators": states.count("documentary_only"), "not_collected_indicators": states.count("not_collected"),
            "measurement_readiness": "measured" if states.count("observed_series") else ("proxied" if states.count("partial_series") else "documentary"),
            "experiments": "|".join(spec["experiment_use"][code]),
        })
    summary = {
        "status": "phase1_research_map_complete", "as_of": spec["as_of"], "codes": len(code_rows),
        "indicators": len(indicator_rows),
        "indicator_states": {state: sum(row["state"] == state for row in indicator_rows) for state in sorted(STATES)},
        "measured_codes": [row["code"] for row in code_rows if row["measurement_readiness"] == "measured"],
        "proxied_codes": [row["code"] for row in code_rows if row["measurement_readiness"] == "proxied"],
        "documentary_codes": [row["code"] for row in code_rows if row["measurement_readiness"] == "documentary"],
        "experiment_status": spec["experiment_status"],
        "guardrail": "Documentary indicators support classification only; valuation tests may use measured or proxied series and must label proxies as proxies.",
    }
    return code_rows, indicator_rows, summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(repo: Path) -> dict[str, Any]:
    spec = json.loads((repo / "config/crypto_phase1_research_map.json").read_text(encoding="utf-8"))
    evidence = repo / "data/processed/01_classification"
    registry = json.loads((evidence / "crypto_phase1_experiment_registry.json").read_text(encoding="utf-8"))
    code_rows, indicator_rows, summary = build(repo, spec, read_csv(evidence / "crypto_phase1_function_codebook.csv"),
                                               read_csv(evidence / "crypto_phase1_function_prevalence.csv"),
                                               read_csv(evidence / "crypto_phase1_taxonomy_profiles.csv"), registry)
    write_csv(evidence / "crypto_phase1_research_map.csv", code_rows)
    write_csv(evidence / "crypto_phase1_indicator_observability.csv", indicator_rows)
    (evidence / "crypto_phase1_research_map.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Join the Phase 1 taxonomy to observable indicators and registered experiments")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
