from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ACTIVE = ["H1", "H2", "H3", "H4", "H8"]


def build(findings: dict[str, Any], strict: dict[str, Any], h3: dict[str, Any], h4: dict[str, Any], h8: dict[str, Any]) -> list[dict[str, Any]]:
    if findings.get("active_hypotheses") != ACTIVE:
        raise ValueError("hypothesis catalog requires the frozen active crypto scope")
    f = findings["findings"]
    strict_pooled = next(row for row in strict["results"] if row["specification"] == "pooled_market_cap")
    h3_asset_count = len(h3.get("assets", h3.get("events_by_asset", {})))
    rows = [
        {
            "hypothesis": "H1",
            "question": "Is greater network usage associated with higher network value?",
            "state": "estimated_expanded_exploratory_scope_sensitive",
            "matrix_role": "The classification matrix defines the researched asset universe but is not a regressor in H1.",
            "observation_unit": "asset-day",
            "sample": f"{f['H1']['assets']} native networks; frozen 90-day primary plus a 3,258-observation retrospective one-year robustness panel",
            "outcome": "log market capitalization",
            "predictors": ["lagged log(1 + active addresses)", "lagged log(1 + transaction count)"],
            "controls": ["asset fixed effects", "date fixed effects"],
            "formula": "log(MarketCap_it) = asset_i + date_t + beta1*log1p(ActiveAddresses_i,t-1) + beta2*log1p(Transactions_i,t-1) + error_it",
            "inference": f"Exact wild-cluster sign enumeration across {f['H1']['assets']} asset clusters, plus leave-one-asset-out sign stability.",
            "input_files": ["data/processed/00_foundation/crypto_h1_activity_history_coinmetrics.csv", "data/processed/00_foundation/market_daily_coinpaprika.csv"],
            "output_files": ["data/processed/02_valuation/crypto_h1_activity_expansion.json", "data/processed/02_valuation/crypto_h1_activity_history_analysis.json"],
            "current_result": f"Frozen 90-day transactions {f['H1']['transaction_count_coefficient']:.4f}, p={f['H1']['transaction_count_exact_p']:.4f}; retrospective one-year transactions {f['H1']['one_year_transaction_count_coefficient']:.4f}, p={f['H1']['one_year_transaction_count_exact_p']:.4f}; the latter is positive but not leave-one-out sign-stable.",
            "main_limitation": "The one-year extension is retrospective rather than independent validation; provider definitions differ, addresses are not users, and the transaction sign reverses without XLM.",
            "next_gate": "Preserve the specification and test it on a genuinely later fixed window."
        },
        {
            "hypothesis": "H2",
            "question": "Is usage more valuable when fees mechanically reach the token or holders?",
            "state": "estimated_exploratory_definition_sensitive",
            "matrix_role": "VA_PROTOCOL and VA_BURN evidence determine the effective-dated capture state; the fee-by-capture interaction is the coefficient of interest.",
            "observation_unit": "asset-day",
            "sample": "11 chain and application systems; 3,971 fee-level observations",
            "outcome": "log market capitalization; seven-day forward log return is secondary",
            "predictors": ["log(1 + fees)", "capture active", "fees x capture", "scope interactions"],
            "controls": ["asset fixed effects", "date fixed effects", "chain-versus-application scope"],
            "formula": "Y_it = asset_i + date_t + beta1*Fees_it + beta2*Capture_it + beta3*(Fees_it*Capture_it) + scope terms + error_it",
            "inference": "Exact wild-cluster sign enumeration across 11 assets (2,048 assignments), leave-one-asset-out checks, non-overlapping return sensitivity, and strict-capture sensitivity.",
            "input_files": ["data/processed/02_valuation/crypto_h2_exploratory_daily.csv", "data/processed/01_classification/crypto_mechanism_state_asof.csv"],
            "output_files": ["data/processed/02_valuation/crypto_h2_exploratory_estimates.json", "data/processed/02_valuation/crypto_h2_small_cluster_inference.json", "data/processed/02_valuation/crypto_h2_strict_capture_sensitivity.json"],
            "current_result": f"Broad fee-capture interaction {f['H2']['pooled_market_cap_interaction']:.4f}, p={f['H2']['pooled_market_cap_exact_p']:.4f}; strict interaction {strict_pooled['strict_coefficient']:.4f}, p={strict_pooled['strict_p']:.4f}.",
            "main_limitation": "The result changes materially with the capture definition and is not a causal or return-prediction result.",
            "next_gate": "Preserve both definitions and seek a later non-overlapping outcome window."
        },
        {
            "hypothesis": "H3",
            "question": "Do material supply increases weaken returns and material burns strengthen returns?",
            "state": "estimated_multiasset_low_power",
            "matrix_role": "VA_BURN and VA_SCARCITY motivate the supply mechanism, but exact event quantities and dates—not binary codes—enter the test.",
            "observation_unit": "asset-level mean of repeated supply events",
            "sample": f"{h3['events_estimated']} events: {h3['events_by_asset'].get('crypto_arb', 0)} ARB unlocks, {h3['events_by_asset'].get('crypto_bnb', 0)} BNB burns, and {h3['events_by_asset'].get('crypto_uni', 0)} UNI burn",
            "outcome": "three-trading-day cumulative abnormal log return, direction-adjusted so positive supports H3",
            "predictors": ["event direction", "gross token impact", "impact share of pre-event circulating supply"],
            "controls": ["asset return model estimated on the equal-weight crypto market over trading days -120 to -31"],
            "formula": "CAR_e[-1,+1] = sum(actual return - market-model expected return); unlock CAR is multiplied by -1 and burn CAR by +1",
            "inference": f"Exact sign-flip randomization of asset-level mean direction-adjusted CARs; {h3.get('asset_sign_flip_assignments', 2 ** h3_asset_count)} assignments for {h3_asset_count} assets.",
            "input_files": ["data/processed/02_valuation/crypto_h3_supply_event_ledger.csv", "data/processed/03_risk/crypto_return_panel_daily.csv"],
            "output_files": ["data/processed/02_valuation/crypto_h3_supply_event_estimates.csv", "data/processed/02_valuation/crypto_h3_supply_event_analysis.json"],
            "current_result": f"Mean direction-adjusted CAR {h3['mean_direction_adjusted_primary_car']:.4f}; {h3['events_matching_predicted_sign']}/{h3['events_estimated']} events match; exact asset-level p={h3['asset_sign_flip_p_two_sided']:.4f}.",
            "main_limitation": f"{h3_asset_count} independent asset units yield valid but low-powered inference; scheduled and pre-announced events may be anticipated.",
            "next_gate": "Add official exact-date events from additional assets without selecting them from returns."
        },
        {
            "hypothesis": "H4",
            "question": "Does staking reduce liquid float and affect liquidity or risk?",
            "state": "measurement_blocked",
            "matrix_role": "VA_STAKE selects positive-staking assets and structural non-staking controls; measured staked units must supply time variation.",
            "observation_unit": "asset-day once three comparable positive-staking histories are complete",
            "sample": "Fixed six-asset design: ETH, BNB, AAVE, BTC, UNI, and ARB",
            "outcome": "turnover/liquidity proxy, volatility, and drawdown",
            "predictors": ["lagged staked share", "staking entry/exit constraints"],
            "controls": ["asset effects", "date effects", "market size and common market risk as predeclared in the eventual estimation specification"],
            "formula": "LiquidityOrRisk_it = asset_i + date_t + beta*StakedShare_i,t-1 + controls_it + error_it",
            "inference": "Not run. Estimation remains prohibited until the measurement-readiness rule is met and a final model specification is frozen.",
            "input_files": ["data/processed/00_foundation/crypto_h4_bnb_stake_daily.csv", "data/processed/00_foundation/crypto_h4_aave_legacy_stake_daily.csv", "data/processed/01_classification/crypto_h4_eth_stake_daily.csv"],
            "output_files": ["data/processed/01_classification/crypto_h4_measurement_audit.json"],
            "current_result": f"Consensus assets ready={h4['consensus_assets_ready']}; separate case studies ready={h4['case_studies_ready']}; pooled estimation ready={h4['pooled_estimation_ready']}.",
            "main_limitation": "ETH has no 365-day active-effective-balance history because no archival Beacon endpoint is configured; legacy stkAAVE is not comparable consensus stake.",
            "next_gate": "Configure ETH_BEACON_ARCHIVE_API_URL and collect the exact 365-day ETH series."
        },
        {
            "hypothesis": "H8",
            "question": "Do theory-defined economic-function groups explain valuation better than a raw function count?",
            "state": "estimated_exploratory_validation_window_frozen",
            "matrix_role": "The complete 23 x 10 matrix is transformed into raw breadth and eight pre-specified group indicators; these are the regressors being compared.",
            "observation_unit": "asset cross-section",
            "sample": "23 classified assets; 22 meet the primary market-cap outcome coverage rule",
            "outcome": "mean log market capitalization over 25 August 2025 to 22 August 2026",
            "predictors": ["raw ten-function breadth", "eight theory-defined group indicators"],
            "controls": ["predeclared architecture and sample sensitivities; no causal controls in the primary single-predictor comparison"],
            "formula": "log(MarketCap_i) = alpha + beta*FunctionMeasure_i + error_i; compare leave-one-asset-out RMSE across measures",
            "inference": "Seeded 100,000-draw outcome permutations, 10% Benjamini-Hochberg FDR across eight group tests, leave-one-asset-out RMSE, and five predeclared sensitivities.",
            "input_files": ["data/processed/01_classification/crypto_verified_universe_profiles.csv", "data/processed/00_foundation/market_daily_coinpaprika.csv", "data/processed/03_risk/crypto_return_panel_daily.csv"],
            "output_files": ["data/processed/02_valuation/crypto_h8_verified_universe_results.csv", "data/processed/02_valuation/crypto_h8_verified_universe_summary.json", "data/processed/02_valuation/crypto_h8_oos_readiness.json"],
            "current_result": f"Best group {h8['best_single_group_model']}; LOAO RMSE {h8['best_single_group_loo_rmse']:.4f} versus breadth {h8['raw_breadth_loo_rmse']:.4f}.",
            "main_limitation": "The group was selected in the discovery sample; this is not independent validation or a causal valuation model.",
            "next_gate": "Wait for the fixed 23 August 2026 to 22 August 2027 validation window and do not retune the group or metric."
        }
    ]
    if [row["hypothesis"] for row in rows] != ACTIVE:
        raise ValueError("hypothesis catalog order or coverage changed")
    return rows


def render(rows: list[dict[str, Any]]) -> str:
    out = [
        "# Active cryptocurrency hypotheses and exact tests", "",
        "This file is generated from the active research scope and empirical outputs. It distinguishes how the classification matrix enters each test; the matrix is not used identically in every hypothesis.", "",
        "| ID | State | Observation unit | Matrix role |", "|---|---|---|---|"
    ]
    for row in rows:
        out.append(f"| {row['hypothesis']} | {row['state']} | {row['observation_unit']} | {row['matrix_role']} |")
    for row in rows:
        out += [
            "", f"## {row['hypothesis']} — {row['question']}", "",
            f"**Sample.** {row['sample']}", "",
            f"**Outcome.** {row['outcome']}", "",
            f"**Predictors.** {'; '.join(row['predictors'])}", "",
            f"**Controls.** {'; '.join(row['controls'])}", "",
            f"**Model.** `{row['formula']}`", "",
            f"**Inference.** {row['inference']}", "",
            "**Exact inputs.** " + ", ".join(f"`{value}`" for value in row["input_files"]), "",
            "**Exact outputs.** " + ", ".join(f"`{value}`" for value in row["output_files"]), "",
            f"**Current result.** {row['current_result']}", "",
            f"**Main limitation.** {row['main_limitation']}", "",
            f"**Next gate.** {row['next_gate']}"
        ]
    return "\n".join(out) + "\n"


def run(repo: Path) -> dict[str, Any]:
    load = lambda path: json.loads((repo / path).read_text(encoding="utf-8"))
    rows = build(
        load("data/processed/02_valuation/crypto_findings_summary.json"),
        load("data/processed/02_valuation/crypto_h2_strict_capture_sensitivity.json"),
        load("data/processed/02_valuation/crypto_h3_supply_event_analysis.json"),
        load("data/processed/01_classification/crypto_h4_measurement_audit.json"),
        load("data/processed/02_valuation/crypto_h8_verified_universe_summary.json")
    )
    output = repo / "data/processed/02_valuation/crypto_hypothesis_test_catalog.json"
    output.write_text(json.dumps({"status": "crypto_hypothesis_test_catalog_complete", "hypotheses": rows}, indent=2) + "\n")
    document = repo / "research/methods/crypto_hypothesis_test_catalog.md"
    document.parent.mkdir(parents=True, exist_ok=True)
    document.write_text(render(rows), encoding="utf-8")
    return {"status": "crypto_hypothesis_test_catalog_complete", "hypotheses": len(rows), "document": str(document.relative_to(repo))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
