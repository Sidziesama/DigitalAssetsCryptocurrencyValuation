from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any

from .crypto_h1_activity_expansion import build_panel, estimate_sample


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle: return list(csv.DictReader(handle))


def build(spec: dict[str, Any], activity: list[dict[str, str]], market: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    analysis_spec = {"status": "frozen_before_expansion_estimation", "window": spec["window"], "primary_assets": [row["asset_id"] for row in spec["assets"]], "token_contract_sensitivity_assets": []}
    candidate = build_panel(analysis_spec, [activity], market)
    dates_by_asset = {asset: {row["date"] for row in candidate if row["asset_id"] == asset} for asset in analysis_spec["primary_assets"]}
    common = set.intersection(*dates_by_asset.values())
    panel = [row for row in candidate if row["date"] in common]
    primary = estimate_sample("one_year_native_network_robustness", panel)
    result = {"status": "h1_one_year_robustness_complete", "interpretation": spec["interpretation"], "primary": primary, "common_window_start": min(common), "common_window_end": max(common), "guardrails": ["This backward extension was specified after the 90-day result and is not independent validation.", "The nine-asset set and model are unchanged.", "Active addresses are addresses, not users; transaction definitions differ by network."]}
    return panel, result


def chart(short: dict[str, Any], history: dict[str, Any]) -> str:
    values = []
    for label, sample in (("90-day frozen expansion", short["primary"]), ("One-year retrospective robustness", history["primary"])):
        for column, metric in (("log1p_active_addresses_lag1", "Active addresses"), ("log1p_transaction_count_lag1", "Transactions")):
            values.append((f"{label}: {metric}", sample["coefficients"][column], sample["inference"][column]["wild_cluster_bootstrap_p_two_sided"]))
    width, height, zero = 980, 350, 500; scale = 330 / max(abs(value) for _, value, _ in values)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="H1 coefficient comparison across 90-day and one-year windows">','<rect width="100%" height="100%" fill="#ffffff"/>','<text x="24" y="30" font-family="Arial" font-size="20" font-weight="600" fill="#17212b">H1 changes across observation windows</text>','<text x="24" y="52" font-family="Arial" font-size="12" fill="#647383">Same nine networks and model; the one-year extension is retrospective robustness, not independent validation.</text>',f'<line x1="{zero}" y1="72" x2="{zero}" y2="310" stroke="#647383" stroke-width="1.5"/>']
    for index,(label,value,p_value) in enumerate(values):
        y=92+index*58; end=zero+value*scale; x=min(zero,end); color="#3478b8" if index<2 else "#8aa8c2"
        parts += [f'<text x="24" y="{y+15}" font-family="Arial" font-size="13" fill="#17212b">{html.escape(label)}</text>',f'<rect x="{x:.1f}" y="{y}" width="{max(abs(end-zero),1):.1f}" height="22" fill="{color}"/>',f'<text x="{end+(8 if value>=0 else -8):.1f}" y="{y+15}" text-anchor="{"start" if value>=0 else "end"}" font-family="Arial" font-size="12" fill="#17212b">{value:+.4f} · p={p_value:.3f}</text>']
    parts += ['<text x="500" y="337" text-anchor="middle" font-family="Arial" font-size="12" fill="#647383">Coefficient on lagged log(1 + activity); zero is the vertical line</text>','</svg>']
    return "\n".join(parts)+"\n"


def run(repo: Path) -> dict[str, Any]:
    spec = json.loads((repo / "config/crypto_h1_activity_history.json").read_text())
    panel, result = build(spec, read_csv(repo / "data/processed/00_foundation/crypto_h1_activity_history_coinmetrics.csv"), read_csv(repo / spec["market_input"]))
    out = repo / "data/processed/02_valuation"
    with (out / "crypto_h1_activity_history_panel.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(panel[0]), lineterminator="\n"); writer.writeheader(); writer.writerows(panel)
    (out / "crypto_h1_activity_history_analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    short = json.loads((out / "crypto_h1_activity_expansion.json").read_text())
    (repo / "research/figures/crypto-h1-activity-window-comparison.svg").write_text(chart(short, result), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate frozen one-year H1 robustness")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
