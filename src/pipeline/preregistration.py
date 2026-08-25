from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .registry import load_json, sha256


REQUIRED_TOP_LEVEL = {"schema_version", "document_version", "status", "scope", "analysis_window", "sample", "peg_measurement", "hypotheses", "outcomes", "covariates", "models", "missing_data", "readiness_gates", "current_readiness"}


def validate(spec: dict[str, Any]) -> None:
    missing = REQUIRED_TOP_LEVEL - set(spec)
    if missing: raise ValueError(f"missing preregistration sections: {sorted(missing)}")
    if spec["schema_version"] != 1: raise ValueError("unsupported schema version")
    if spec["status"] not in {"draft_not_frozen", "frozen"}: raise ValueError("invalid status")
    peg = spec["peg_measurement"]
    if peg["primary_recovery_bps"] >= peg["primary_breach_bps"]: raise ValueError("recovery band must be narrower than breach band")
    if set(spec["hypotheses"]) != {"H5", "H6", "H7"}: raise ValueError("scope must define H5-H7")
    if not spec["missing_data"].get("no_silent_imputation"): raise ValueError("no-silent-imputation rule is required")
    if "stable_ustc" not in spec["sample"]["failure_controls_excluded_primary"]: raise ValueError("USTC primary treatment must be explicit")
    if "stable_paxg" not in spec["sample"]["exclude_reference_assets"]: raise ValueError("PAXG reference treatment must be explicit")
    expected_usage = {"stable_usdt", "stable_usdc", "stable_dai", "stable_tusd"}
    if set(spec["sample"].get("h7_exploratory_usage_assets", [])) != expected_usage: raise ValueError("H7 exploratory usage subsample must be fixed to the four source-supported assets")
    if "exploratory" not in spec["sample"].get("h7_usage_scope_rule", ""): raise ValueError("H7 usage scope must remain explicitly exploratory")
    if "evidence/effective date" not in spec["covariates"]["design_effective_date_rule"]: raise ValueError("point-in-time design rule is required")


def build_manifest(repo: Path, spec: dict[str, Any]) -> dict[str, Any]:
    inputs = [
        repo / "config" / "assets.json", repo / "config" / "stablecoin_risk_inputs.json",
        repo / "config" / "stablecoin_evidence_plan.json",
        repo / "config" / "stablecoin_evidence_extractions.json",
        repo / "config" / "preregistration_h5_h7.json",
        repo / "data" / "processed" / "empirical" / "stablecoin_daily.csv",
        repo / "data" / "processed" / "empirical" / "stablecoin_depeg_episodes.csv",
        repo / "data" / "processed" / "empirical" / "stablecoin_episode_review_queue.csv",
        repo / "data" / "processed" / "historical" / "stablecoin_global_market_daily.csv",
        repo / "data" / "processed" / "empirical" / "stablecoin_adoption_daily.csv",
        repo / "data" / "processed" / "empirical" / "stablecoin_chain_distribution_daily.csv",
        repo / "data" / "processed" / "empirical" / "stablecoin_trading_activity_daily.csv",
        repo / "data" / "processed" / "empirical" / "stablecoin_market_depth_snapshots.csv",
        repo / "data" / "processed" / "empirical" / "stablecoin_yield_integration_snapshot.csv",
        repo / "data" / "processed" / "historical" / "stablecoin_usage_daily_coinmetrics.csv",
        repo / "data" / "processed" / "empirical" / "stablecoin_h7_usage_exploratory_daily.csv",
        repo / "data" / "processed" / "empirical" / "stablecoin_h7_readiness.json",
        repo / "data" / "processed" / "evidence" / "stablecoin_evidence_summary.json",
    ]
    return {"document_version": spec["document_version"], "status": spec["status"], "inputs": {str(path.relative_to(repo)): sha256(path) for path in inputs}}


def render(spec: dict[str, Any]) -> str:
    readiness = "\n".join(f"- **{key}:** `{value}`" for key, value in spec["current_readiness"].items())
    gates = "\n".join(f"- **{key}:** " + "; ".join(values) for key, values in spec["readiness_gates"].items())
    return f"""# H5-H7 Preregistration — Draft {spec['document_version']}

**Status:** `{spec['status']}`. This document is not yet a frozen preregistration and must not be described as one.

## Scope and sample

The analysis uses USD-target stablecoins in the frozen pilot universe from {spec['analysis_window']['start']} through {spec['analysis_window']['end']}. PAXG is excluded because its reference asset is gold. USTC is excluded from primary models and retained as a failure-control robustness case. The unresolved USDG observation on 2025-01-30 is withheld unless independently confirmed before freezing.

## Primary peg definitions

- Continuous outcome: `{spec['outcomes']['continuous_primary']}`.
- Breach outcome: strictly outside ±{spec['peg_measurement']['primary_breach_bps']} bps.
- Recovery: at or inside ±{spec['peg_measurement']['primary_recovery_bps']} bps.
- Robustness bands: {', '.join(str(value) for value in spec['peg_measurement']['robustness_bands_bps'])} bps.
- Calendar gaps right-censor open episodes.

## Temporal integrity

Design scores and explanatory variables may only be used when their evidence/effective date is known. Current 2026 design scores are not backfilled into earlier history. Partial risk scores are diagnostic only and prohibited from headline models.

## Model families

- H5: reserve quality versus peg error, breaches, severity, and recovery.
- H6: redemption friction versus the same outcomes, including stress interactions.
- H7: supply, market share, liquidity, integrations, and usage.

Two exact-date shares are implemented: `pilot_observed_supply_share` and `global_peggedusd_supply_share`. The latter uses DeFiLlama's source-audited `totalCirculatingUSD.peggedUSD` denominator. It may be described only as DeFiLlama global pegged-USD supply share, not as a share of every stable-value asset. Current order-book and yield-integration snapshots remain developmental proxies until their historical and identifier-validation gates pass. Coin Metrics usage histories cover four assets only, and active addresses must not be labeled unique users.

## Current readiness

{readiness}

## Gates required before estimation

{gates}

## Inference and robustness

Primary panel models include asset and calendar-time fixed effects where identified. Standard errors are clustered by asset and date where supported. Hypothesis-family p-values receive Benjamini-Hochberg adjustment. Verified peg outcomes are not winsorized in primary analysis; unverified provider anomalies may only be withheld through a documented pre-estimation review rule.
"""


def run(repo: Path) -> dict[str, Any]:
    spec = load_json(repo / "config" / "preregistration_h5_h7.json"); validate(spec)
    manifest = build_manifest(repo, spec)
    out = repo / "research" / "preregistration"; out.mkdir(parents=True, exist_ok=True)
    (out / "H5-H7-draft.md").write_text(render(spec), encoding="utf-8")
    (out / "H5-H7-input-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"status": spec["status"], "document_version": spec["document_version"], "manifest_inputs": len(manifest["inputs"]), "current_readiness": spec["current_readiness"]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and render the H5-H7 preregistration draft"); parser.add_argument("--repo", type=Path, default=Path.cwd()); args = parser.parse_args(); print(json.dumps(run(args.repo.resolve()), indent=2))


if __name__ == "__main__": main()
