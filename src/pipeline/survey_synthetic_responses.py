"""Synthetic Google Forms exports for testing the panel analysis.

These files exist so the analysis can be exercised and its edge cases checked
BEFORE any real response is read. No synthetic figure is ever reported as a
finding; every output lives under data/synthetic/ and the analysis refuses to
write a synthetic result into data/processed/.

The export deliberately reproduces two awkward properties of the real one: six
columns share the header 'Why? One line.', and several items allow a free-text
'Other'.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any

SCENARIOS = ["consensus", "leaning", "tie", "divided", "depends", "sparse",
             "degenerate", "duplicates", "dirty", "prediction_hit"]


def load(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def columns(items: dict) -> list[tuple[str, str]]:
    """(header, key) pairs. Headers repeat; keys do not."""
    g = items["importance_grid"]
    cols: list[tuple[str, str]] = [("Timestamp", "Timestamp"), ("Email Address", "Email Address")]
    cols += [(t, t) for t in items["screening"].values()]
    cols += [(f'{g["title"]} [{r}]', f'grid::{c}') for r, c in g["rows"].items()]
    for s in items["boundary_items"]:
        cols.append((s["title"], f'item::{s["item_id"]}'))
        cols.append((items["boundary_free_text_title"], f'why::{s["item_id"]}'))
    cols.append((items["free_text_items"][0]["title"], "item::F1_missing_functions"))
    cols.append((items["single_choice_items"][0]["title"], "item::S1_architecture_placement"))
    for s in items["materiality_items"]:
        cols.append((s["title"], f'item::{s["item_id"]}'))
    cols.append((items["checkbox_items"][0]["title"], "item::C1_money_evidence"))
    cols.append((items["single_choice_items"][1]["title"], "item::S2_most_useful"))
    cols.append((items["free_text_items"][1]["title"], "item::F2_what_would_change"))
    cols.append((items["checkbox_items"][1]["title"], "item::C2_trust"))
    cols.append((items["free_text_items"][2]["title"], "item::F3_unanswered"))
    cols += [(c["label"] + items["blind_cell_suffix"], f'blind::{c["asset_id"]}|{c["code"]}')
             for c in items["blind_cells"]]
    cols.append((items["free_text_items"][3]["title"], "item::F4_blind_exercise_problems"))
    return cols


def pattern_for(spec: dict, scenario: str, n: int, rng: random.Random) -> list[str]:
    opts = spec["options"]
    keep = spec.get("project_rule", opts[0])
    other = next(o for o in opts if o != keep)
    dep = spec.get("condition_dependent_option", opts[-1])
    if scenario in ("consensus", "duplicates", "prediction_hit", "dirty"):
        p = [keep] * round(n * 0.8) + [other] * (n - round(n * 0.8))
    elif scenario == "leaning":
        p = [keep] * round(n * 0.6) + [other] * (n - round(n * 0.6))
    elif scenario == "tie":
        h = n // 2
        p = [keep] * h + [other] * (n - h)
    elif scenario == "depends":
        p = [dep] * round(n * 0.8) + [keep] * (n - round(n * 0.8))
    elif scenario == "degenerate":
        p = [keep] * n
    else:
        p = [opts[i % len(opts)] for i in range(n)]
    rng.shuffle(p)
    return p


def build(repo: Path, scenario: str, n: int, seed: int) -> tuple[list[str], list[list[str]]]:
    items = load(repo / "config/survey_items.json")
    rng = random.Random(seed)
    cols = columns(items)
    grid = items["importance_grid"]
    labels = list(grid["scale"].keys())
    # the frozen prediction: capture and monetary high, incentives and governance low
    favoured = {"VA_PROTOCOL": "5 Decisive", "VA_MONETARY": "5 Decisive", "VA_SCARCITY": "4"}
    disfavoured = {"VA_INCENTIVE": "1 Irrelevant", "VA_GOV": "1 Irrelevant"}

    per_item = {s["item_id"]: pattern_for(s, scenario, n, rng) for s in items["boundary_items"]}
    rows: list[dict[str, str]] = []
    for i in range(n):
        r = {k: "" for _, k in cols}
        r["Timestamp"] = f"2026/09/{15 + i % 10:02d} 10:{i % 60:02d}:00"
        r["Email Address"] = f"p{i:03d}@example.invalid"
        for t in items["screening"].values():
            r[t] = ""
        sc = items["screening"]
        r[sc["role"]] = rng.choice(["Asset or wealth management", "Financial advisory", "Research or analytics"])
        r[sc["years"]] = rng.choice(["Under 2", "2 to 5", "5 to 8", "Over 8"])
        r[sc["familiarity"]] = str(rng.randint(1, 5))
        r[sc["allocator"]] = rng.choice(["Yes", "No"])

        for code in grid["rows"].values():
            if scenario == "sparse" and rng.random() < 0.5:
                continue
            if scenario == "dirty" and rng.random() < 0.15:
                r[f"grid::{code}"] = "6 Beyond decisive"      # outside the declared scale
                continue
            if scenario == "prediction_hit":
                r[f"grid::{code}"] = favoured.get(code, disfavoured.get(code, "3"))
            else:
                r[f"grid::{code}"] = rng.choice(labels)

        for s in items["boundary_items"]:
            r[f'item::{s["item_id"]}'] = per_item[s["item_id"]][i]
            if rng.random() < 0.7:
                r[f'why::{s["item_id"]}'] = f"Reasoning from respondent {i} on {s['item_id']}."
        for s in items["materiality_items"]:
            if scenario == "dirty" and s.get("other_option_allowed") and rng.random() < 0.3:
                r[f'item::{s["item_id"]}'] = f"Other: a bespoke threshold from respondent {i}"
            else:
                r[f'item::{s["item_id"]}'] = rng.choice(s["options"])
        for s in items["single_choice_items"]:
            r[f'item::{s["item_id"]}'] = rng.choice(s["options"])
        for s in items["checkbox_items"]:
            picks = rng.sample(s["options"], rng.randint(1, 3))
            if scenario == "dirty" and rng.random() < 0.3:
                picks.append("a bespoke answer, with a comma in it")
            r[f'item::{s["item_id"]}'] = ", ".join(picks)
        for s in items["free_text_items"][:3]:
            if rng.random() < 0.5:
                r[f'item::{s["item_id"]}'] = f"Open answer {i} for {s['item_id']}."

        if scenario != "sparse" or i % 2 == 0:
            for c in items["blind_cells"]:
                key = f'blind::{c["asset_id"]}|{c["code"]}'
                if scenario == "degenerate":
                    r[key] = "Yes"
                elif scenario == "dirty" and rng.random() < 0.12:
                    r[key] = "Probably"                        # not a declared option
                elif scenario == "sparse":
                    r[key] = rng.choice(items["blind_options"] + [""])
                else:
                    r[key] = rng.choices(items["blind_options"], weights=[5, 4, 2])[0]
            r["item::F4_blind_exercise_problems"] = f"Cell note from respondent {i}."
        rows.append(r)

    if scenario == "duplicates" and n >= 2:
        early = dict(rows[0]); early["Timestamp"] = "2026/09/01 08:00:00"
        early["item::B1_governed_treasury"] = "Yes, this is value capture"
        rows.insert(0, early)                                   # superseded by the later one
        tie_a = dict(rows[-1]); tie_a["Email Address"] = "tied@example.invalid"
        tie_b = dict(tie_a)
        rows += [tie_a, tie_b]                                  # identical timestamps
    return [h for h, _ in cols], [[r[k] for _, k in cols] for r in rows]


def run(repo: Path, scenario: str, n: int, seed: int) -> Path:
    header, rows = build(repo, scenario, n, seed)
    out = repo / "data/synthetic/survey"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"synthetic_responses_{scenario}_n{n}_seed{seed}.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
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
