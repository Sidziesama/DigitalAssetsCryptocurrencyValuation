from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build(findings: dict[str, Any]) -> dict[str, Any]:
    h = findings["findings"]
    improvement = 1 - h["H8"]["verified_universe_best_group_loo_rmse"] / h["H8"]["verified_universe_raw_breadth_loo_rmse"]
    return {
        "status": "crypto_executive_summary_complete",
        "headline": "Economic function is useful as a due-diligence framework; it is not yet a standalone pricing or trading model.",
        "rows": [
            {
                "topic": "Classify the asset",
                "done": "Verified 230 function decisions across 23 cryptoassets using ten consistent economic-function rules.",
                "insight": "Assets cannot be understood by one label. What a token does matters more than whether it is called an L1, governance token, or utility token.",
                "action": "Use the matrix as the first advisory screen: identify monetary use, network demand, supply effects, financial integration, control rights, and holder capture.",
                "strength": "usable_now"
            },
            {
                "topic": "Explain valuation differences",
                "done": f"Compared raw function count with theory-defined groups across 23 classified assets; 22 had sufficient market-cap data.",
                "insight": f"Financial integration produced {improvement:.1%} lower leave-one-asset-out error than simply counting functions. The improvement is modest and exploratory.",
                "action": "Describe which functions an asset has, not how many. Treat collateral and financial integration as a research lead, not a price target.",
                "strength": "promising_not_proven"
            },
            {
                "topic": "Test activity and value capture",
                "done": "Tested network activity across nine chains and fee/capture interaction across eleven assets.",
                "insight": "Activity alone is unstable. Fee activity looks more informative when value reaches the token or holder, but the result disappears under the strict capture definition.",
                "action": "Ask where economic value actually ends. Do not count governance, treasury spending, or validator compensation as holder capture without a direct route.",
                "strength": "promising_not_proven"
            },
            {
                "topic": "Test supply-event trading stories",
                "done": f"Measured {h['H3']['supply_events_estimated']} unlock or burn events across {len(h['H3']['supply_event_assets'])} assets.",
                "insight": f"Only {h['H3']['supply_events_matching_predicted_sign']} of {h['H3']['supply_events_estimated']} events moved in the predicted direction, and every asset-level average opposed the hypothesis.",
                "action": "Do not use an unlock or burn announcement by itself as a trading signal. Add valuation, anticipation, liquidity, and market conditions.",
                "strength": "not_supported"
            },
            {
                "topic": "Test staking and liquidity",
                "done": "Built the BNB stake history, market controls, and an ETH collector; froze the analysis before estimation.",
                "insight": "There is no H4 finding yet because the required historical ETH stake series is missing.",
                "action": "Do not present a staking/liquidity conclusion. Obtain the ETH archive series first, then run the locked test.",
                "strength": "not_tested"
            }
        ],
        "advisory_use_now": [
            "Explain a token's economic jobs consistently.",
            "Separate usage from value capture.",
            "Compare assets with similar functions rather than similar marketing labels.",
            "Flag unsupported narratives and missing evidence."
        ],
        "not_ready": ["price targets", "causal claims", "automatic buy/sell signals", "portfolio weights"],
    }


def render(result: dict[str, Any]) -> str:
    lines = ["# Cryptocurrency economic-function research — decision summary", "", f"**Bottom line:** {result['headline']}", "", "## What we have done → what it means → what to do", "", "| What we did | Insight | Action | Evidence status |", "|---|---|---|---|"]
    labels = {"usable_now": "Usable framework", "promising_not_proven": "Exploratory", "not_supported": "Not supported", "not_tested": "Not tested"}
    for row in result["rows"]:
        lines.append(f"| **{row['topic']}** — {row['done']} | {row['insight']} | {row['action']} | {labels[row['strength']]} |")
    lines += ["", "## What an advisor can use today", ""] + [f"- {item}" for item in result["advisory_use_now"]]
    lines += ["", "## What this research cannot support yet", ""] + [f"- {item.capitalize()}" for item in result["not_ready"]]
    lines += ["", "The classification matrix is the product available today. The empirical tests are quality checks on whether parts of that matrix also contain valuation information. They remain exploratory until they work in a genuinely later sample.", ""]
    return "\n".join(lines)


def run(repo: Path) -> dict[str, Any]:
    findings = json.loads((repo / "data/processed/02_valuation/crypto_findings_summary.json").read_text(encoding="utf-8"))
    result = build(findings)
    out = repo / "data/processed/02_valuation/crypto_executive_summary.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    report = repo / "research/findings/crypto-executive-decision-summary.md"
    report.write_text(render(result), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate the plain-language crypto research decision summary")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
