"""Synthetic Google Forms exports for testing the panel analysis.

These files exist so the analysis code can be exercised and its edge cases
checked BEFORE any real response is read. No synthetic figure is ever reported
as a finding; every artifact is written under a synthetic/ directory and its
header row records the scenario and seed that produced it.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any

SCENARIOS = ["consensus", "leaning", "tie", "divided", "depends", "sparse", "degenerate"]


def load(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def columns(items: dict) -> list[str]:
    cols = ["Timestamp", "Email Address"]
    cols += list(items["screening"].values())
    g = items["importance_grid"]
    cols += [f'{g["title"]} [{row}]' for row in g["rows"]]
    cols += [s["title"] for s in items["boundary_items"]]
    cols += [s["title"] for s in items["materiality_items"]]
    cols += [c["label"] + items["blind_cell_suffix"] for c in items["blind_cells"]]
    return cols


def boundary_answers(spec: dict, scenario: str, n: int, rng: random.Random) -> list[str]:
    opts = spec["options"]
    keep, other, depends = spec["project_rule"], [o for o in opts if o != spec["project_rule"]][0], opts[-1]
    if scenario == "consensus":
        pattern = [keep] * round(n * 0.8) + [other] * (n - round(n * 0.8))
    elif scenario == "leaning":
        pattern = [keep] * round(n * 0.6) + [other] * (n - round(n * 0.6))
    elif scenario == "tie":
        half = n // 2
        pattern = [keep] * half + [other] * (n - half)
    elif scenario == "depends":
        pattern = [depends] * round(n * 0.8) + [keep] * (n - round(n * 0.8))
    elif scenario == "degenerate":
        pattern = [keep] * n
    else:                                        # divided
        pattern = [opts[i % len(opts)] for i in range(n)]
    rng.shuffle(pattern)
    return pattern


def build(repo: Path, scenario: str, n: int, seed: int) -> tuple[list[str], list[dict]]:
    items = load(repo / "config/survey_items.json")
    rng = random.Random(seed)
    cols = columns(items)
    grid = items["importance_grid"]
    scale_labels = list(grid["scale"].keys())

    per_item = {s["item_id"]: boundary_answers(s, scenario, n, rng)
                for s in items["boundary_items"]}

    rows = []
    for i in range(n):
        r = {c: "" for c in cols}
        r["Timestamp"] = f"2026/09/{15 + i % 10} 10:{i % 60:02d}:00"
        r["Email Address"] = f"p{i:03d}@example.invalid"
        r[items["screening"]["role"]] = rng.choice(
            ["Asset or wealth management", "Financial advisory", "Research or analytics"])
        r[items["screening"]["years"]] = rng.choice(["Under 2", "2 to 5", "5 to 8", "Over 8"])
        r[items["screening"]["familiarity"]] = str(rng.randint(1, 5))
        r[items["screening"]["allocator"]] = rng.choice(["Yes", "No"])

        for row_label in grid["rows"]:
            if scenario == "sparse" and rng.random() < 0.5:
                continue
            r[f'{grid["title"]} [{row_label}]'] = rng.choice(scale_labels)

        for s in items["boundary_items"]:
            r[s["title"]] = per_item[s["item_id"]][i]
        for s in items["materiality_items"]:
            r[s["title"]] = rng.choice(["Any observable use", "Above USD 100m outstanding",
                                        "Above 1 percent of supply", "Depends"])

        if scenario != "sparse" or i % 2 == 0:
            for c in items["blind_cells"]:
                if scenario == "degenerate":
                    v = "Yes"
                elif scenario == "sparse":
                    v = rng.choice(items["blind_options"] + [""])
                else:
                    v = rng.choices(items["blind_options"], weights=[5, 4, 2])[0]
                r[c["label"] + items["blind_cell_suffix"]] = v
        rows.append(r)

    if scenario == "consensus" and n >= 3:                     # one duplicate to exercise the rule
        dup = dict(rows[0]); dup["Timestamp"] = "2026/09/25 09:00:00"
        rows.append(dup)
    return cols, rows


def run(repo: Path, scenario: str, n: int, seed: int) -> Path:
    cols, rows = build(repo, scenario, n, seed)
    out = repo / "data/synthetic/survey"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"synthetic_responses_{scenario}_n{n}_seed{seed}.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate synthetic survey responses for testing")
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--scenario", choices=SCENARIOS, default="consensus")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=20260914)
    a = ap.parse_args()
    print(run(a.repo.resolve(), a.scenario, a.n, a.seed))
