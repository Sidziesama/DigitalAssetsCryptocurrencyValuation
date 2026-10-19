from __future__ import annotations

import argparse
import csv
import html
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


GROUP_LABELS = {
    "monetary_store": "monetary adoption and scarcity",
    "transaction_service_demand": "network fees and service demand",
    "security_commitment": "real staking yield, dilution and security budget",
    "supply_absorption": "burns, sequestration and net supply growth",
    "financial_integration": "collateral demand and financial integration",
    "control_rights": "governance scope and controlled treasury",
    "holder_capture": "holder revenue or token-level capture",
    "subsidized_participation": "organic activity after incentive emissions",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def active_groups(row: dict[str, str]) -> list[str]:
    return [key.removeprefix("bundle_") for key, value in row.items() if key.startswith("bundle_") and value == "1"]


def trailing_return(rows: list[dict[str, str]], days: int) -> float | None:
    usable = [row for row in rows if number(row.get("close_usdt")) not in (None, 0)]
    if len(usable) <= days:
        return None
    latest, earlier = number(usable[-1]["close_usdt"]), number(usable[-days - 1]["close_usdt"])
    return latest / earlier - 1 if latest is not None and earlier not in (None, 0) else None


def latest_nonmissing(rows: list[dict[str, str]], field: str) -> float | None:
    for row in reversed(rows):
        value = number(row.get(field))
        if value is not None:
            return value
    return None


def average_positive(rows: list[dict[str, str]], field: str, count: int) -> float | None:
    values = [value for row in rows if (value := number(row.get(field))) is not None and value >= 0]
    return statistics.fmean(values[-count:]) if values else None


def state(applicable: bool, value: float | None, unit: str) -> dict[str, Any]:
    if not applicable:
        return {"state": "not_applicable", "value": None, "unit": unit}
    if value is None:
        return {"state": "data_unavailable", "value": None, "unit": unit}
    return {"state": "measured", "value": value, "unit": unit}


def build(
    spec: dict[str, Any],
    profiles: list[dict[str, str]],
    return_rows: list[dict[str, str]],
    risk_rows: list[dict[str, str]],
    valuation_rows: list[dict[str, str]],
    advisory_profiles: dict[str, Any],
) -> dict[str, Any]:
    if spec.get("schema_version") != 1 or spec.get("status") != "frozen_before_dashboard_estimation":
        raise ValueError("dashboard specification must be frozen before estimation")
    if len(profiles) != 23 or any(row.get("classification_status") != "complete_human_verified" for row in profiles):
        raise ValueError("dashboard requires the complete verified 23-asset matrix")
    return_by_asset: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in return_rows:
        return_by_asset[row["asset_id"]].append(row)
    for rows in return_by_asset.values():
        rows.sort(key=lambda row: row["date"])
    valuation_by_asset: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in valuation_rows:
        valuation_by_asset[row["asset_id"]].append(row)
    for rows in valuation_by_asset.values():
        rows.sort(key=lambda row: row["date"])
    risk_by_asset = {row["asset_id"]: row for row in risk_rows}
    advice_by_asset = {row["asset_id"]: row for row in advisory_profiles["profiles"]}
    assets = []
    for profile in profiles:
        asset_id, symbol = profile["asset_id"], profile["symbol"]
        groups = active_groups(profile)
        market = return_by_asset.get(asset_id, [])
        risk = risk_by_asset.get(asset_id, {})
        valuation = valuation_by_asset.get(asset_id, [])
        latest_market_cap = latest_nonmissing(valuation, "market_cap_usd")
        avg_fees = average_positive(valuation, "fees_usd_lag1", spec["valuation_average_days"])
        avg_holder_revenue = average_positive(valuation, "holders_revenue_usd_lag1", spec["valuation_average_days"])
        fee_multiple = latest_market_cap / (avg_fees * spec["annualization_days"]) if latest_market_cap and avg_fees and avg_fees > 0 else None
        holder_multiple = latest_market_cap / (avg_holder_revenue * spec["annualization_days"]) if latest_market_cap and avg_holder_revenue and avg_holder_revenue > 0 else None
        technical = {
            "as_of_date": market[-1]["date"] if market else None,
            "price_usdt": state(bool(market), number(market[-1].get("close_usdt")) if market else None, "USDT"),
            "return_30d": state(bool(market), trailing_return(market, 30), "decimal_return"),
            "return_90d": state(bool(market), trailing_return(market, 90), "decimal_return"),
            "realized_volatility_30d_annualized": state(bool(market), latest_nonmissing(market, "realized_volatility_30d_annualized"), "decimal_volatility"),
            "market_beta": state(bool(risk), number(risk.get("market_beta")), "beta"),
            "max_drawdown": state(bool(risk), (math.exp(number(risk["max_drawdown_log"])) - 1) if number(risk.get("max_drawdown_log")) is not None else None, "decimal_return"),
            "mean_daily_dollar_volume": state(bool(risk), math.exp(number(risk["mean_log_dollar_volume"])) if number(risk.get("mean_log_dollar_volume")) is not None else None, "USD"),
        }
        fee_applicable = "transaction_service_demand" in groups or "holder_capture" in groups
        holder_applicable = "holder_capture" in groups
        metric_states = {
            "market_cap": state(True, latest_market_cap, "USD"),
            "market_cap_to_annualized_fees": state(fee_applicable, fee_multiple, "multiple"),
            "market_cap_to_annualized_holder_revenue": state(holder_applicable, holder_multiple, "multiple"),
        }
        trend = technical["return_90d"]["value"]
        trend_text = "90-day market direction is unavailable." if trend is None else f"The asset's 90-day return is {'positive' if trend >= 0 else 'negative'} ({trend:.1%})."
        measured = [name for name, item in metric_states.items() if item["state"] == "measured"]
        missing = [name for name, item in metric_states.items() if item["state"] == "data_unavailable"]
        valuation_text = f"Measured valuation fields: {', '.join(measured)}." if measured else "No function-relevant valuation multiple is currently measurable."
        if missing:
            valuation_text += f" Required but unavailable: {', '.join(missing)}."
        assets.append({
            "asset_id": asset_id,
            "symbol": symbol,
            "architecture_context": profile["architecture_context"],
            "economic_groups": groups,
            "selected_valuation_lenses": [GROUP_LABELS[group] for group in groups],
            "technical_market_state": technical,
            "valuation_metrics": metric_states,
            "closest_economic_comparables": advice_by_asset[asset_id]["closest_economic_comparables"],
            "plain_finding": f"{trend_text} {valuation_text}",
            "advisory_action": "Compare market state and valuation only with economic peers; investigate divergence between price, usage, and capture before forming an advisory view.",
            "investment_score": None,
        })
    return {
        "status": "classification_informed_market_valuation_dashboard_complete",
        "specification_version": spec["document_version"],
        "freeze_date": spec["freeze_date"],
        "market_data_end_date": spec["market_data_end_date"],
        "assets": len(assets),
        "technical_coverage": sum(bool(return_by_asset.get(row["asset_id"])) for row in profiles),
        "risk_coverage": sum(row["asset_id"] in risk_by_asset for row in profiles),
        "market_cap_coverage": sum(asset["valuation_metrics"]["market_cap"]["state"] == "measured" for asset in assets),
        "holder_multiple_coverage": sum(asset["valuation_metrics"]["market_cap_to_annualized_holder_revenue"]["state"] == "measured" for asset in assets),
        "guardrails": spec["guardrails"],
        "asset_results": assets,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Classification-informed market and valuation dashboard",
        "",
        f"Frozen {result['freeze_date']}; market data end {result['market_data_end_date']}. This dashboard describes market state and selects valuation metrics using the verified economic-function matrix. It does not issue recommendations, price targets, rankings, or investment scores.",
        "",
        "## Coverage",
        "",
        f"- Economic classifications: {result['assets']} assets.",
        f"- Technical market history: {result['technical_coverage']} assets.",
        f"- Common-window risk measures: {result['risk_coverage']} assets.",
        f"- Market-cap observations in the valuation panel: {result['market_cap_coverage']} assets.",
        f"- Measurable holder-revenue multiples: {result['holder_multiple_coverage']} assets.",
        "",
        "![Risk map](../figures/crypto-market-risk-map.svg)",
        "",
        "## Asset dashboard",
        "",
        "| Asset | Economic lens | 30d | 90d | Volatility | Beta | Drawdown | Valuation status |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    def pct(item: dict[str, Any]) -> str:
        return "—" if item["state"] != "measured" else f"{item['value']:.1%}"
    def dec(item: dict[str, Any]) -> str:
        return "—" if item["state"] != "measured" else f"{item['value']:.2f}"
    for asset in result["asset_results"]:
        tech, values = asset["technical_market_state"], asset["valuation_metrics"]
        valuation_state = ", ".join(name.replace("market_cap_to_annualized_", "") for name, value in values.items() if value["state"] == "measured") or "unavailable"
        lens = ", ".join(asset["economic_groups"]) or "none"
        lines.append(f"| {asset['symbol']} | {lens} | {pct(tech['return_30d'])} | {pct(tech['return_90d'])} | {pct(tech['realized_volatility_30d_annualized'])} | {dec(tech['market_beta'])} | {pct(tech['max_drawdown'])} | {valuation_state} |")
    lines += ["", "## How to use it", "", "1. Select peers from shared economic functions, not architecture alone.", "2. Read momentum, volatility, beta and drawdown as market-state and risk context—not intrinsic value.", "3. Use only function-relevant valuation denominators. A fee multiple is not evidence of holder value capture.", "4. Treat `data_unavailable` as a research gap and `not_applicable` as an economic judgment; neither means zero.", "5. Investigate price–fundamental divergence, then complete custody, liquidity, legal, concentration and suitability review separately.", ""]
    return "\n".join(lines)


def render_svg(result: dict[str, Any]) -> str:
    points = []
    for asset in result["asset_results"]:
        tech = asset["technical_market_state"]
        vol, draw = tech["realized_volatility_30d_annualized"]["value"], tech["max_drawdown"]["value"]
        if vol is not None and draw is not None:
            points.append((asset, vol * 100, abs(draw) * 100))
    width, height, left, right, top, bottom = 1100, 690, 90, 40, 95, 75
    pw, ph = width - left - right, height - top - bottom
    xmax = max(vol for _, vol, _ in points) * 1.08
    ymax = max(draw for _, _, draw in points) * 1.08
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Cryptoasset volatility and maximum drawdown risk map">', '<rect width="100%" height="100%" fill="#ffffff"/>', '<text x="24" y="34" font-family="Arial, sans-serif" font-size="22" font-weight="700" fill="#17212b">Market risk map by verified economic classification</text>', '<text x="24" y="60" font-family="Arial, sans-serif" font-size="13" fill="#647383">Further right = higher recent annualized volatility; further up = deeper common-window drawdown. Gold indicates verified holder capture.</text>']
    for i in range(6):
        x = left + pw * i / 5
        y = top + ph * i / 5
        parts += [f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+ph}" stroke="#e6ebef"/>', f'<text x="{x:.1f}" y="{top+ph+24}" text-anchor="middle" font-family="Arial" font-size="11" fill="#647383">{xmax*i/5:.0f}%</text>', f'<line x1="{left}" y1="{top+ph-ph*i/5:.1f}" x2="{left+pw}" y2="{top+ph-ph*i/5:.1f}" stroke="#e6ebef"/>', f'<text x="{left-12}" y="{top+ph-ph*i/5+4:.1f}" text-anchor="end" font-family="Arial" font-size="11" fill="#647383">{ymax*i/5:.0f}%</text>']
    for asset, vol, draw in points:
        x, y = left + pw * vol / xmax, top + ph - ph * draw / ymax
        color = "#d99a2b" if "holder_capture" in asset["economic_groups"] else "#3478b8"
        parts += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{color}" opacity="0.88"/>', f'<text x="{x+8:.1f}" y="{y-7:.1f}" font-family="Arial" font-size="11" fill="#17212b">{html.escape(asset["symbol"])}</text>']
    parts += [f'<text x="{left+pw/2}" y="{height-20}" text-anchor="middle" font-family="Arial" font-size="13" fill="#17212b">30-day realized volatility, annualized</text>', f'<text x="20" y="{top+ph/2}" transform="rotate(-90 20 {top+ph/2})" text-anchor="middle" font-family="Arial" font-size="13" fill="#17212b">Maximum drawdown depth</text>', '</svg>']
    return "\n".join(parts) + "\n"


def run(repo: Path) -> dict[str, Any]:
    spec = json.loads((repo / "config/crypto_market_valuation_dashboard.json").read_text(encoding="utf-8"))
    result = build(
        spec,
        read_csv(repo / "data/processed/01_classification/crypto_verified_universe_profiles.csv"),
        read_csv(repo / "data/processed/03_risk/crypto_return_panel_daily.csv"),
        read_csv(repo / "data/processed/03_risk/crypto_function_risk_verified_assets.csv"),
        read_csv(repo / "data/processed/02_valuation/crypto_h2_exploratory_daily.csv"),
        json.loads((repo / "data/processed/02_valuation/crypto_advisory_profiles.json").read_text(encoding="utf-8")),
    )
    out = repo / "data/processed/02_valuation"
    out.mkdir(parents=True, exist_ok=True)
    (out / "crypto_market_valuation_dashboard.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    findings = repo / "research/findings/crypto-market-valuation-dashboard.md"
    findings.write_text(render_markdown(result), encoding="utf-8")
    figure = repo / "research/figures/crypto-market-risk-map.svg"
    figure.write_text(render_svg(result), encoding="utf-8")
    return {key: result[key] for key in ("status", "assets", "technical_coverage", "risk_coverage", "market_cap_coverage", "holder_multiple_coverage")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the classification-informed market and valuation dashboard")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
