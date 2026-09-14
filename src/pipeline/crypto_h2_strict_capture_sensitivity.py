from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from src.pipeline.crypto_h2_estimator_diagnostics import CHAIN_COLUMNS, POOLED_COLUMNS, eligible, read_rows
from src.pipeline.crypto_h2_small_cluster_inference import wild_cluster_test

SPECIFICATIONS = {
    "pooled_market_cap": ("log_market_cap_usd", None, POOLED_COLUMNS),
    "chain_market_cap": ("log_market_cap_usd", "chain", CHAIN_COLUMNS),
}
COLUMN = {"VA_BURN": "va_burn_effective", "VA_PROTOCOL": "va_protocol_effective"}


def validate(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1 or spec.get("status") != "frozen_before_sensitivity_estimation":
        raise ValueError("unsupported strict capture sensitivity specification")
    if not spec.get("overrides") or not spec.get("selection_rule") or not spec.get("interpretation"):
        raise ValueError("strict capture sensitivity requires overrides and guardrails")
    if not spec.get("specifications") or any(name not in SPECIFICATIONS for name in spec["specifications"]):
        raise ValueError("unknown H2 specification requested")
    for override in spec["overrides"]:
        if override.get("code") not in COLUMN or override.get("value") not in (0, 1) or not override.get("applies_from"):
            raise ValueError("overrides need a burn or protocol code, a binary value, and an application date")


def relabel(rows: list[dict[str, str]], overrides: list[dict[str, Any]]) -> tuple[list[dict[str, str]], int]:
    changed = 0
    output = []
    for row in rows:
        new = dict(row)
        touched = False
        for override in overrides:
            if new["asset_id"] == override["asset_id"] and new["date"] >= override["applies_from"]:
                column = COLUMN[override["code"]]
                if new.get(column) not in ("", None) and int(float(new[column])) != override["value"]:
                    new[column] = str(override["value"])
                    touched = True
        if touched:
            burn, protocol = new.get("va_burn_effective"), new.get("va_protocol_effective")
            if burn not in ("", None) and protocol not in ("", None):
                capture = int(bool(int(float(burn)) or int(float(protocol))))
                new["h2_active_capture"] = str(capture)
                fees = new.get("log1p_fees_usd_lag1")
                new["fees_x_capture"] = str(float(fees) * capture) if fees not in ("", None) else ""
            changed += 1
        output.append(new)
    return output, changed


def build(spec: dict[str, Any], rows: list[dict[str, str]], baseline: dict[str, Any]) -> dict[str, Any]:
    validate(spec)
    relabeled, changed = relabel(rows, spec["overrides"])
    if changed == 0:
        raise ValueError("strict capture overrides changed no panel rows")
    baseline_index = {result["specification"]: result for result in baseline.get("results", [])}
    results = []
    for name in spec["specifications"]:
        outcome, scope, columns = SPECIFICATIONS[name]
        strict = wild_cluster_test(eligible(relabeled, outcome, scope), outcome, columns)
        base = baseline_index.get(name)
        if base is None:
            raise ValueError(f"baseline inference lacks specification {name}")
        results.append({
            "specification": name, "outcome": outcome,
            "frozen_coefficient": base["coefficient"], "frozen_p": base["wild_cluster_bootstrap_p_two_sided"],
            "strict_coefficient": strict["coefficient"], "strict_p": strict["wild_cluster_bootstrap_p_two_sided"],
            "strict_cluster_robust_standard_error_cr1": strict["cluster_robust_standard_error_cr1"],
            "coefficient_ratio_strict_to_frozen": strict["coefficient"] / base["coefficient"] if base["coefficient"] else None,
            "clusters": strict["clusters"], "bootstrap_assignments": strict["bootstrap_assignments"],
            "frozen_rejects_at_10pct": base["wild_cluster_bootstrap_p_two_sided"] <= 0.10,
            "strict_rejects_at_10pct": strict["wild_cluster_bootstrap_p_two_sided"] <= 0.10,
        })
    return {
        "status": "exploratory_strict_capture_sensitivity_complete",
        "specification_version": spec["document_version"], "freeze_date": spec["freeze_date"],
        "overrides": [{k: o[k] for k in ("asset_id", "code", "value", "applies_from")} for o in spec["overrides"]],
        "relabeled_rows": changed, "results": results,
        "headline_survives_strict_rule": all(r["strict_rejects_at_10pct"] for r in results if r["frozen_rejects_at_10pct"]) and any(r["frozen_rejects_at_10pct"] for r in results),
        "selection_rule": spec["selection_rule"], "interpretation": spec["interpretation"],
    }


def run(repo: Path) -> dict[str, Any]:
    spec = json.loads((repo / "config/crypto_h2_strict_capture_sensitivity.json").read_text(encoding="utf-8"))
    baseline = json.loads((repo / spec["baseline"]).read_text(encoding="utf-8"))
    summary = build(spec, read_rows(repo / spec["panel"]), baseline)
    output = repo / "data/processed/02_valuation/crypto_h2_strict_capture_sensitivity.json"
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Re-estimate frozen H2 valuation specifications under the strict holder-capture rule")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
