from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.pipeline.crypto_economic_design import CODES


H2_CODES = ("VA_BURN", "VA_PROTOCOL")


def build(rows: list[dict[str, Any]], assets: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    index = {(row["asset_id"], row["code"]): row for row in rows}
    panel = []
    for asset_id in assets:
        verified = {
            code: index[(asset_id, code)]["recommended_value"]
            for code in CODES
            if (asset_id, code) in index and index[(asset_id, code)]["status"] == "verified"
        }
        h2_ready = all(code in verified for code in H2_CODES)
        h8_ready = all(code in verified for code in CODES)
        panel.append({
            "asset_id": asset_id,
            "verified_code_count": len(verified),
            "h2_active_capture": int(any(int(verified[code]) for code in H2_CODES)) if h2_ready else None,
            "h2_design_ready": int(h2_ready),
            "h8_value_accrual_breadth": sum(int(verified[code]) for code in CODES) if h8_ready else None,
            "h8_design_ready": int(h8_ready),
        })
    summary = {
        "assets": len(assets),
        "h2_design_ready_assets": sum(row["h2_design_ready"] for row in panel),
        "h8_design_ready_assets": sum(row["h8_design_ready"] for row in panel),
        "status": "h2_pilot_design_ready_h8_requires_full_code_evidence",
        "interpretation": "H2 requires verified burn and protocol-capture fields. H8 breadth is withheld until all ten value-accrual codes are evidence-backed for an asset.",
    }
    return panel, summary


def run(repo: Path) -> dict[str, Any]:
    config = json.loads((repo / "config/crypto_design_evidence_tranche_1.json").read_text())
    panel, summary = build(config["decisions"], config["assets"])
    out = repo / "data/processed/evidence"; out.mkdir(parents=True, exist_ok=True)
    with (out / "crypto_h2_h8_pilot_readiness.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(panel[0]), lineterminator="\n"); writer.writeheader(); writer.writerows(panel)
    (out / "crypto_h2_h8_pilot_readiness.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build conservative H2/H8 pilot design readiness")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
