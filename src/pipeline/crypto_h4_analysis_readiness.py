from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from src.pipeline.registry import load_json


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1 or spec.get("hypothesis") != "H4":
        raise ValueError("unsupported H4 analysis specification")
    primary = spec.get("primary_sample", {})
    if primary.get("consensus_staking_assets") != ["crypto_eth", "crypto_bnb"]:
        raise ValueError("H4 primary positive-staking sample must remain ETH and BNB")
    if primary.get("structural_nonstaking_controls") != ["crypto_btc", "crypto_uni", "crypto_arb"]:
        raise ValueError("H4 structural controls changed after design freeze")
    if spec.get("separate_case_study") != ["crypto_aave"]:
        raise ValueError("legacy stkAAVE must remain a separate case study")
    if spec.get("predictor") != "lagged_staked_share_of_circulating_supply":
        raise ValueError("unexpected H4 predictor")


def coverage(rows: list[dict[str, str]], asset_id: str, start: date, end: date) -> dict[str, Any]:
    dates = sorted({date.fromisoformat(row["date"]) for row in rows if row.get("asset_id") == asset_id and start <= date.fromisoformat(row["date"]) <= end})
    expected = (end - start).days + 1
    return {
        "asset_id": asset_id,
        "observed_days": len(dates),
        "expected_days": expected,
        "first_date": dates[0].isoformat() if dates else None,
        "last_date": dates[-1].isoformat() if dates else None,
        "complete": len(dates) == expected,
    }


def build(repo: Path) -> dict[str, Any]:
    spec = load_json(repo / "config/crypto_h4_analysis.json")
    validate(spec)
    start, end = date.fromisoformat(spec["study_start"]), date.fromisoformat(spec["study_end"])
    market = read_rows(repo / "data/processed/00_foundation/market_daily_coinpaprika.csv")
    eth = read_rows(repo / "data/processed/01_classification/crypto_h4_eth_stake_daily.csv")
    bnb = read_rows(repo / "data/processed/00_foundation/crypto_h4_bnb_stake_daily.csv")
    aave = read_rows(repo / "data/processed/00_foundation/crypto_h4_aave_legacy_stake_daily.csv")

    primary_assets = spec["primary_sample"]["consensus_staking_assets"] + spec["primary_sample"]["structural_nonstaking_controls"]
    market_coverage = [coverage(market, asset, start, end) for asset in primary_assets + spec["separate_case_study"]]
    stake_coverage = [coverage(eth, "crypto_eth", start, end), coverage(bnb, "crypto_bnb", start, end)]
    case_coverage = coverage(aave, "crypto_aave", start, end)
    market_ready = all(row["observed_days"] >= spec["minimum_common_days"] for row in market_coverage)
    stake_ready = all(row["complete"] for row in stake_coverage)
    result = {
        "status": "h4_analysis_ready" if market_ready and stake_ready else "h4_analysis_blocked_on_eth_history",
        "design_frozen_on": spec["design_frozen_on"],
        "study_window": {"start": spec["study_start"], "end": spec["study_end"], "calendar_days": (end-start).days+1},
        "primary_assets": primary_assets,
        "consensus_staking_assets_required": 2,
        "consensus_staking_assets_ready": sum(row["complete"] for row in stake_coverage),
        "market_coverage": market_coverage,
        "stake_coverage": stake_coverage,
        "aave_case_study_coverage": case_coverage,
        "market_ready": market_ready,
        "staking_measurement_ready": stake_ready,
        "estimation_allowed": market_ready and stake_ready,
        "resolved_design_issue": "The earlier three-comparable-positive-series gate was impossible in the fixed universe. The frozen primary design uses the two comparable consensus-staking assets, ETH and BNB, plus BTC, UNI, and ARB structural controls. Legacy stkAAVE remains separate.",
        "next_required": "Collect ETH active effective balance for every day in the frozen common window; do not estimate or retune the model before that gate passes.",
    }
    return result


def chart(result: dict[str, Any]) -> str:
    labels = {"crypto_eth": "ETH stake", "crypto_bnb": "BNB stake", "crypto_btc": "BTC market", "crypto_uni": "UNI market", "crypto_arb": "ARB market"}
    stake = {row["asset_id"]: row for row in result["stake_coverage"]}
    market = {row["asset_id"]: row for row in result["market_coverage"]}
    assets = result["primary_assets"]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="940" height="390" viewBox="0 0 940 390" role="img" aria-label="Frozen H4 primary design and data readiness">', '<rect width="100%" height="100%" fill="#ffffff"/>', '<text x="30" y="38" font-family="Arial" font-size="22" font-weight="700" fill="#17212b">H4 primary design: one input remains</text>', '<text x="30" y="63" font-family="Arial" font-size="13" fill="#647383">362-day common window · green = complete · red = missing · legacy stkAAVE remains separate</text>']
    for index, asset in enumerate(assets):
        x = 30 + index * 180
        if asset in stake:
            ready = stake[asset]["complete"]
            days = stake[asset]["observed_days"]
        else:
            ready = market[asset]["complete"]
            days = market[asset]["observed_days"]
        color = "#287a52" if ready else "#b6534c"
        parts += [f'<rect x="{x}" y="105" width="150" height="105" rx="9" fill="{color}"/>', f'<text x="{x+75}" y="138" text-anchor="middle" font-family="Arial" font-size="16" font-weight="700" fill="#ffffff">{labels[asset]}</text>', f'<text x="{x+75}" y="170" text-anchor="middle" font-family="Arial" font-size="24" font-weight="700" fill="#ffffff">{days}/362</text>', f'<text x="{x+75}" y="194" text-anchor="middle" font-family="Arial" font-size="12" fill="#ffffff">{"READY" if ready else "MISSING"}</text>']
    parts += ['<line x1="105" y1="235" x2="825" y2="235" stroke="#9aa7b2" stroke-width="2"/>', '<rect x="235" y="275" width="470" height="72" rx="9" fill="#eef2f5" stroke="#9aa7b2"/>', '<text x="470" y="303" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700" fill="#17212b">ESTIMATION LOCKED</text>', '<text x="470" y="329" text-anchor="middle" font-family="Arial" font-size="13" fill="#647383">Unlock only after ETH active effective balance reaches 362/362</text>', '</svg>']
    return "\n".join(parts) + "\n"


def run(repo: Path) -> dict[str, Any]:
    result = build(repo)
    path = repo / "data/processed/02_valuation/crypto_h4_analysis_readiness.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    figure = repo / "research/figures/crypto-h4-analysis-readiness.svg"
    figure.parent.mkdir(parents=True, exist_ok=True)
    figure.write_text(chart(result), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit the frozen H4 analysis design and input coverage")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
