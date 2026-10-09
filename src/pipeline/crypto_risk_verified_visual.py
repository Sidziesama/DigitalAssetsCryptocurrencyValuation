from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any


COLORS = {"blue": "#3478b8", "gold": "#d99a2b", "gray": "#d7dde3", "text": "#17212b", "muted": "#647383", "white": "#ffffff"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def label(row: dict[str, str]) -> str:
    predictor = row["predictor"].removeprefix("bundle_").replace("_", " ").title()
    outcome = row["outcome"].replace("_", " ").title()
    return f"{predictor} — {outcome}"


def build(rows: list[dict[str, str]], top_n: int = 9) -> str:
    estimable = [row for row in rows if row.get("estimable") == "1"]
    selected = sorted(estimable, key=lambda row: float(row["permutation_p_two_sided"]))[:top_n]
    width, left, right, top, row_h = 1100, 360, 150, 105, 42
    height = top + row_h * len(selected) + 72
    plot = width - left - right
    maximum = max(0.20, max(float(row["permutation_p_two_sided"]) for row in selected) * 1.08)
    reference = left + plot * .05 / maximum
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Strongest verified economic-function and risk associations">',
        f'<rect width="100%" height="100%" fill="{COLORS["white"]}"/>',
        f'<text x="24" y="32" font-family="Arial, sans-serif" font-size="20" font-weight="600" fill="{COLORS["text"]}">Verified function–risk associations</text>',
        f'<text x="24" y="57" font-family="Arial, sans-serif" font-size="12" fill="{COLORS["muted"]}">Nine smallest permutation p-values across 27 frozen tests; none survives 10% false-discovery correction.</text>',
        f'<line x1="{reference:.2f}" y1="82" x2="{reference:.2f}" y2="{top + row_h * len(selected)}" stroke="{COLORS["gold"]}" stroke-width="2"/>',
        f'<text x="{reference + 5:.2f}" y="94" font-family="Arial, sans-serif" font-size="11" fill="{COLORS["muted"]}">nominal p = 0.05</text>'
    ]
    for index, row in enumerate(selected):
        y = top + index * row_h
        p_value, q_value = float(row["permutation_p_two_sided"]), float(row["benjamini_hochberg_q"])
        bar = plot * p_value / maximum
        parts.extend([
            f'<text x="{left - 12}" y="{y + 18}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="{COLORS["text"]}">{html.escape(label(row))}</text>',
            f'<rect x="{left}" y="{y}" width="{plot}" height="22" fill="{COLORS["gray"]}" opacity="0.38"/>',
            f'<rect x="{left}" y="{y}" width="{bar:.2f}" height="22" fill="{COLORS["blue"]}"/>',
            f'<text x="{left + bar + 8:.2f}" y="{y + 17}" font-family="Arial, sans-serif" font-size="12" font-weight="600" fill="{COLORS["text"]}">p={p_value:.3f} · q={q_value:.3f}</text>'
        ])
    parts.extend([
        f'<text x="{left + plot / 2}" y="{height - 25}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="{COLORS["muted"]}">Two-sided permutation p-value (lower is stronger evidence)</text>',
        '</svg>'
    ])
    return "\n".join(parts) + "\n"


def run(repo: Path) -> dict[str, Any]:
    summary = json.loads((repo / "data/processed/03_risk/crypto_function_risk_verified_refresh.json").read_text())
    rows = read_csv(repo / "data/processed/03_risk/crypto_function_risk_verified_tests.csv")
    figure = repo / "research/figures/crypto-risk-verified-associations.svg"
    figure.parent.mkdir(parents=True, exist_ok=True)
    figure.write_text(build(rows), encoding="utf-8")
    sample, strongest = summary["samples"][0], summary["samples"][0]["strongest_associations"][0]
    finding = repo / "research/findings/2026-10-09-verified-function-risk-refresh.md"
    finding.write_text(
        "# Verified economic-function and risk refresh\n\n"
        "The original frozen risk design has been re-estimated using the completed classification matrix. "
        "Only the classification input and obsolete sample label changed; the window, outcomes, predictors, "
        "liquidity control, permutation inference, and multiple-testing correction remain unchanged.\n\n"
        f"- Classification profiles checked: {summary['classification_profiles']}.\n"
        f"- Assets meeting the original return-history rule: {sample['assets']}.\n"
        f"- Frozen tests estimated: {sample['estimable_tests']}.\n"
        f"- Nominal p-values at or below 0.05: {sample['tests_p_at_or_below_5pct']} "
        f"({sample['expected_false_positives_at_5pct']:.2f} expected by chance).\n"
        f"- Tests surviving 10% false-discovery correction: {sample['tests_surviving_fdr_10pct']}.\n"
        f"- Strongest association: {strongest['predictor']} with {strongest['outcome']}; "
        f"coefficient {strongest['coefficient']:.4f}, permutation p={strongest['permutation_p_two_sided']:.4f}, "
        f"q={strongest['benjamini_hochberg_q']:.4f}.\n\n"
        "Interpretation: monetary/store assets have shallower drawdowns and lower beta in this sample, but the "
        "27-test family provides no false-discovery-controlled evidence that economic-function groups explain risk. "
        "This is an exploratory association, not a causal result or return forecast.\n\n"
        "![Verified function-risk associations](../figures/crypto-risk-verified-associations.svg)\n",
        encoding="utf-8"
    )
    return {"status": "crypto_risk_verified_visual_complete", "figure": str(figure.relative_to(repo)), "finding": str(finding.relative_to(repo))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
