"""Panel survey analysis, executing config/survey_analysis_plan.json v1.2.

Thresholds, denominators, level definitions and scoring rules are read from the
plan at run time. Nothing the plan states is restated here, so plan and code
cannot drift apart silently.

Two rules this module enforces rather than assumes:
  - Output scope is declared by the caller. It is never inferred from a path.
  - A panel-scope run requires a recruitment record and archives a hashed
    snapshot of the reference values it used.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

UNKNOWN = "Unknown"
INVALID = "__invalid__"
TIMESTAMP_FORMATS = ["%Y/%m/%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ ingestion


class ExportError(RuntimeError):
    """Raised when the export cannot be read as the frozen plan requires."""


def _index_map(header: list[str], items: dict) -> tuple[dict[str, int], dict[str, int], list[str]]:
    """Resolve every expected column to an index.

    Six scenario items share the free-text title 'Why? One line.', so free-text
    columns are bound by POSITION: the one immediately after each scenario item.
    Reading by header name would collapse them onto a single column.
    """
    positions: dict[str, list[int]] = defaultdict(list)
    for i, h in enumerate(header):
        positions[h.strip()].append(i)

    cols: dict[str, int] = {}
    missing: list[str] = []

    def take(title: str, key: str) -> None:
        if positions.get(title):
            cols[key] = positions[title][0]
        else:
            missing.append(title)

    take("Timestamp", "timestamp")
    if positions.get("Email Address"):
        cols["email"] = positions["Email Address"][0]

    for key, title in items["screening"].items():
        take(title, f"screen:{key}")
    g = items["importance_grid"]
    for row_label, code in g["rows"].items():
        take(f'{g["title"]} [{row_label}]', f"grid:{code}")

    why: dict[str, int] = {}
    for s in items["boundary_items"]:
        take(s["title"], f'item:{s["item_id"]}')
        idx = cols.get(f'item:{s["item_id"]}')
        if idx is not None and idx + 1 < len(header) and header[idx + 1].strip() == items["boundary_free_text_title"]:
            why[s["item_id"]] = idx + 1
    for group in ("materiality_items", "checkbox_items", "single_choice_items", "free_text_items"):
        for s in items.get(group, []):
            take(s["title"], f'item:{s["item_id"]}')
    for c in items["blind_cells"]:
        take(c["label"] + items["blind_cell_suffix"], f'blind:{c["asset_id"]}|{c["code"]}')

    if missing:
        raise ExportError("export is missing expected columns, so it cannot be analysed under the "
                          "frozen plan:\n  - " + "\n  - ".join(missing))
    return cols, why, [h for h in header if h.strip() not in _expected_titles(items)]


def _expected_titles(items: dict) -> set[str]:
    g = items["importance_grid"]
    titles = {"Timestamp", "Email Address", items["boundary_free_text_title"]}
    titles |= set(items["screening"].values())
    titles |= {f'{g["title"]} [{r}]' for r in g["rows"]}
    for group in ("boundary_items", "materiality_items", "checkbox_items",
                  "single_choice_items", "free_text_items"):
        titles |= {s["title"] for s in items.get(group, [])}
    titles |= {c["label"] + items["blind_cell_suffix"] for c in items["blind_cells"]}
    return titles


def _parse_timestamp(raw: str) -> datetime | None:
    raw = raw.strip()
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def read_export(path: Path, items: dict) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        raw = list(csv.reader(fh))
    if not raw:
        raise ExportError(f"{path} is empty")
    header, body = raw[0], raw[1:]
    cols, why, unexpected = _index_map(header, items)

    records = []
    for n, row in enumerate(body):
        row = row + [""] * (len(header) - len(row))
        rec: dict[str, Any] = {"row": n, "answers": {}, "why": {}, "blind": {}, "grid": {}}
        rec["timestamp_raw"] = row[cols["timestamp"]].strip()
        rec["timestamp"] = _parse_timestamp(rec["timestamp_raw"])
        rec["email"] = row[cols["email"]].strip().lower() if "email" in cols else ""
        for key, idx in cols.items():
            if key.startswith("item:") or key.startswith("screen:"):
                v = row[idx].strip()
                if v:
                    rec["answers"][key.split(":", 1)[1]] = v
            elif key.startswith("grid:"):
                rec["grid"][key.split(":", 1)[1]] = row[idx].strip()
            elif key.startswith("blind:"):
                v = row[idx].strip()
                if v:
                    rec["blind"][key.split(":", 1)[1]] = v
        for item_id, idx in why.items():
            v = row[idx].strip()
            if v:
                rec["why"][item_id] = v
        records.append(rec)

    return {"records": records, "unexpected_columns": sorted(set(unexpected)),
            "free_text_columns_bound_by_position": len(why),
            "rows": len(records)}


def deduplicate(records: list[dict], rule: str) -> tuple[list[dict], list[dict]]:
    """Keep the LATER submission per respondent identity, as the plan requires."""
    by_email: dict[str, list[dict]] = defaultdict(list)
    anonymous = [r for r in records if not r["email"]]
    for r in records:
        if r["email"]:
            by_email[r["email"]].append(r)

    kept, dropped = list(anonymous), []
    for email, group in by_email.items():
        if len(group) == 1:
            kept.append(group[0])
            continue
        parsed = [r for r in group if r["timestamp"] is not None]
        ambiguous = len(parsed) != len(group)
        if parsed and not ambiguous:
            latest = max(group, key=lambda r: r["timestamp"])
            if sum(1 for r in group if r["timestamp"] == latest["timestamp"]) > 1:
                ambiguous = True
                latest = group[-1]
        else:
            latest = group[-1]
        kept.append(latest)
        for r in group:
            if r is latest:
                continue
            dropped.append({"row": r["row"], "reason": "duplicate_submission_superseded",
                            "timestamp": r["timestamp_raw"], "kept_timestamp": latest["timestamp_raw"],
                            "resolved_by": "row order" if ambiguous else "timestamp",
                            "ambiguous": ambiguous})
    kept.sort(key=lambda r: r["row"])
    return kept, dropped


# ------------------------------------------------------------------ consensus


def classify_consensus(counts: Counter, condition_dependent: str | None,
                       thresholds: dict, min_n: int) -> dict[str, Any]:
    n = sum(counts.values())
    shares = {k: v / n for k, v in counts.items()} if n else {}
    out: dict[str, Any] = {"n": n, "counts": dict(sorted(counts.items())),
                           "shares": {k: round(v, 4) for k, v in sorted(shares.items())}}
    if n < min_n:
        out.update(level="under_powered", leader=None, leader_share=None,
                   validation_status="unresolved")
        return out
    top = max(shares.values())
    leaders = sorted(k for k, v in shares.items() if v == top)
    if len(leaders) > 1:
        out.update(level="divided", leader=None, leader_share=round(top, 4),
                   tied_options=leaders, validation_status="unresolved")
        return out
    leader = leaders[0]
    if top >= thresholds["adopt"]:
        level = ("consensus_condition_dependent" if condition_dependent and leader == condition_dependent
                 else "consensus_adopt")
    elif top >= thresholds["leaning"]:
        level = "leaning"
    else:
        level = "divided"
    out.update(level=level, leader=leader, leader_share=round(top, 4),
               validation_status="externally_validated" if level == "consensus_adopt" else "unresolved")
    return out


# ---------------------------------------------------------------- statistics


def cohen_kappa(a: list[str], b: list[str]) -> dict[str, Any]:
    n = len(a)
    if n == 0:
        return {"n": 0, "observed_agreement": None, "kappa": None, "kappa_status": "no_overlap"}
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[k] / n) * (cb[k] / n) for k in set(a) | set(b))
    if abs(pe - 1.0) < 1e-12:
        return {"n": n, "observed_agreement": round(po, 4), "kappa": None,
                "kappa_status": "undefined_expected_agreement_is_one"}
    return {"n": n, "observed_agreement": round(po, 4),
            "kappa": round((po - pe) / (1 - pe), 4), "kappa_status": "estimated"}


def krippendorff_alpha_nominal(ratings: dict[str, dict[str, str]]) -> dict[str, Any]:
    units = {u: list(v.values()) for u, v in ratings.items() if len(v) >= 2}
    if not units:
        return {"alpha": None, "alpha_status": "no_unit_has_two_or_more_coders",
                "units_used": 0, "pairable_values": 0}
    n_total = sum(len(v) for v in units.values())
    do_num = 0.0
    for vals in units.values():
        m, c = len(vals), Counter(vals)
        do_num += (m * (m - 1) - sum(x * (x - 1) for x in c.values())) / (m - 1)
    do = do_num / n_total
    allv = Counter(v for vals in units.values() for v in vals)
    de = ((n_total / (n_total - 1)) * (1 - sum((x / n_total) ** 2 for x in allv.values()))
          if n_total > 1 else 0.0)
    if de <= 1e-12:
        return {"alpha": None, "alpha_status": "undefined_expected_disagreement_is_zero",
                "units_used": len(units), "pairable_values": n_total,
                "category_distribution": dict(allv)}
    return {"alpha": round(1 - do / de, 4), "alpha_status": "estimated",
            "units_used": len(units), "pairable_values": n_total,
            "observed_disagreement": round(do, 6), "expected_disagreement": round(de, 6)}


def average_ranks(scores: dict[str, float]) -> dict[str, float]:
    """Descending ranks, ties sharing the average of the ranks they span."""
    ordered = sorted(scores.items(), key=lambda kv: -kv[1])
    ranks: dict[str, float] = {}
    i = 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and ordered[j + 1][1] == ordered[i][1]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[ordered[k][0]] = avg
        i = j + 1
    return ranks


def spearman(x: list[float], y: list[float]) -> float | None:
    n = len(x)
    if n < 3:
        return None

    def rank(v: list[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = rank(x), rank(y)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return round(num / (dx * dy), 4) if dx and dy else None


def score_prediction(fn_means: dict[str, Any], spec: dict, min_n: int) -> dict[str, Any]:
    """The prediction frozen at ff15698, scored condition by condition."""
    usable = {c: v["mean"] for c, v in fn_means.items()
              if v["mean"] is not None and v["n"] >= min_n}
    out: dict[str, Any] = {"source": spec["source"], "statement": spec["statement"],
                           "functions_scorable": len(usable), "functions_total": len(fn_means)}
    if len(usable) != len(fn_means):
        out.update(verdict="not_scorable",
                   reason="Every function needs a mean over at least the reportable minimum for a "
                          "complete ranking. Conditions are not scored on a partial ranking.",
                   under_powered=[c for c in fn_means if c not in usable])
        return out

    ranks = average_ranks(usable)
    band, total = spec["band_size"], len(usable)
    conditions = []
    for code in spec["top_three"]:
        conditions.append(_band_condition(code, ranks, "top", band, total))
    for code in spec["bottom_three"]:
        conditions.append(_band_condition(code, ranks, "bottom", band, total))
    out.update(
        ranking=[{"code": c, "mean": usable[c], "rank": ranks[c]}
                 for c in sorted(usable, key=lambda c: (ranks[c], c))],
        conditions=conditions,
        conditions_met=sum(1 for c in conditions if c["satisfied"]),
        conditions_total=len(conditions),
        verdict="supported" if all(c["satisfied"] for c in conditions) else "not_supported",
        note="All four conditions must hold. Partial satisfaction is reported condition by "
             "condition and is never summarised as a hit.")
    return out


def _band_condition(code: str, ranks: dict[str, float], side: str, band: int, total: int) -> dict[str, Any]:
    rank = ranks[code]
    group = sorted(c for c, r in ranks.items() if r == rank)
    # An averaged rank hides the positions the tie group actually occupies. A group of
    # m tied at average rank r spans positions r-(m-1)/2 .. r+(m-1)/2, and the plan
    # requires that whole span to sit inside the band.
    half = (len(group) - 1) / 2
    first, last = rank - half, rank + half
    if side == "top":
        satisfied, target = last <= band, f"top {band}"
    else:
        floor = total - band + 1
        satisfied, target = first >= floor, f"bottom {band}"
    return {"code": code, "required": target, "rank": rank, "tie_group": group,
            "tie_group_size": len(group), "tie_group_positions": [first, last],
            "satisfied": bool(satisfied),
            "tie_rule": "A tied function counts only if the whole span of positions its tie "
                        "group occupies falls inside the band."}


# --------------------------------------------------------------------- build


def build(repo: Path, responses: Path, scope: str) -> dict[str, Any]:
    plan = load(repo / "config/survey_analysis_plan.json")
    items = load(repo / "config/survey_items.json")
    taxonomy = load(repo / "config/crypto_phase1_taxonomy.json")
    if not plan["document_version"].startswith("1.2"):
        raise ExportError(f"plan version {plan['document_version']} is not the version this module implements")
    if scope not in plan["output_scope"]["values"]:
        raise ExportError(f"unknown output scope {scope!r}")

    mins = plan["minimum_counts"]
    thresholds = plan["consensus"]["thresholds"]
    levels = {l["label"]: l for l in plan["consensus"]["levels"]}

    recruitment = None
    if scope == "panel":
        rec_path = repo / "config/survey_recruitment.json"
        if not rec_path.exists():
            raise ExportError("panel scope requires config/survey_recruitment.json; "
                              + plan["recruitment_record"]["gate"])
        recruitment = load(rec_path)
        blank = [f for f in plan["recruitment_record"]["fields"] if not recruitment.get(f)]
        if blank:
            raise ExportError("recruitment record is incomplete: " + ", ".join(blank))
        if "synthetic" in responses.as_posix():
            raise ExportError("refusing to analyse a file under data/synthetic/ at panel scope")

    ingest = read_export(responses, items)
    kept, dropped = deduplicate(ingest["records"], plan["inclusion_and_exclusion"]["duplicates"])
    invalid: list[dict] = []

    # ---- importance grid
    grid, scale = items["importance_grid"], items["importance_grid"]["scale"]
    fn_means: dict[str, Any] = {}
    for code in grid["rows"].values():
        vals = []
        for r in kept:
            v = r["grid"].get(code, "")
            if not v:
                continue
            if v in scale:
                vals.append(scale[v])
            else:
                invalid.append({"row": r["row"], "field": f"grid:{code}", "value": v})
        fn_means[code] = {"n": len(vals),
                          "mean": round(sum(vals) / len(vals), 4) if vals else None,
                          "reportable": len(vals) >= mins["item_reportable"]}

    prediction = score_prediction(fn_means, items["frozen_prediction"], mins["item_reportable"])

    # ---- single-choice consensus items
    rules: dict[str, Any] = {}
    for spec in items["boundary_items"] + items["materiality_items"] + items["single_choice_items"]:
        vals, others = [], []
        for r in kept:
            v = r["answers"].get(spec["item_id"], "")
            if not v:
                continue
            if v in spec["options"]:
                vals.append(v)
            elif spec.get("other_option_allowed"):
                vals.append(v)
                others.append({"row": r["row"], "value": v})
            else:
                invalid.append({"row": r["row"], "field": spec["item_id"], "value": v})
        res = classify_consensus(Counter(vals), spec.get("condition_dependent_option"),
                                 thresholds, mins["consensus_assessable"])
        res.update(item_id=spec["item_id"], question=spec["title"],
                   other_answers=others, effect=levels[res["level"]]["effect"])
        if others:
            res["other_note"] = plan["consensus"]["other_option_handling"]
        if "project_rule" in spec:
            res["project_working_convention"] = spec["project_rule"]
            res["rule_name"] = spec["rule_name"]
            res["panel_agrees_with_working_convention"] = (
                res["level"] == "consensus_adopt" and res["leader"] == spec["project_rule"])
        if res["level"] == "divided":
            res["contested"] = True
        rules[spec["item_id"]] = res

    boundary_ids = [s["item_id"] for s in items["boundary_items"]]
    validated = [i for i in boundary_ids if rules[i]["validation_status"] == "externally_validated"]
    g1 = {"gate": "G1 boundary rules validated externally",
          "requirement": plan["consensus"]["validation_status_per_rule"]["gate_rule"],
          "boundary_rules_total": len(boundary_ids), "externally_validated": len(validated),
          "unresolved": sorted(set(boundary_ids) - set(validated)),
          "passes": len(validated) == len(boundary_ids) and len(boundary_ids) > 0,
          "note": "An unresolved rule continues as the project's working convention and is not "
                  "externally validated."}

    # ---- checkbox items
    checkboxes = {}
    for spec in items["checkbox_items"]:
        answered, counts, unparsed = 0, Counter(), []
        pairs: Counter = Counter()
        for r in kept:
            raw = r["answers"].get(spec["item_id"], "")
            if not raw:
                continue
            answered += 1
            picked = [o for o in spec["options"] if o in raw]
            residue = raw
            for o in picked:
                residue = residue.replace(o, "")
            residue = residue.strip(" ,")
            if residue:
                unparsed.append({"row": r["row"], "residue": residue})
                counts["__other_or_unparsed__"] += 1
            for o in picked:
                counts[o] += 1
            for a, b in itertools.combinations(sorted(picked), 2):
                pairs[f"{a} + {b}"] += 1
        checkboxes[spec["item_id"]] = {
            "question": spec["title"], "answered": answered,
            "selection_rate": {o: round(counts[o] / answered, 4) for o in counts} if answered else {},
            "selection_count": dict(counts),
            "top_co_selections": [{"pair": k, "count": v} for k, v in pairs.most_common(5)],
            "unparsed": unparsed,
            "rule": plan["checkbox_items_rule"],
        }

    # ---- free text: counts and a coding worksheet only
    free_rows = []
    for r in kept:
        for item_id, v in r["why"].items():
            free_rows.append({"response_id": f"R{r['row']:03d}", "item_id": item_id,
                              "kind": "scenario_reasoning", "text": v, "argument_group": ""})
        for spec in items["free_text_items"]:
            v = r["answers"].get(spec["item_id"], "")
            if v:
                free_rows.append({"response_id": f"R{r['row']:03d}", "item_id": spec["item_id"],
                                  "kind": "open_question", "text": v, "argument_group": ""})
    free_text = {"answers": len(free_rows),
                 "by_item": dict(Counter(r["item_id"] for r in free_rows)),
                 "rule": plan["free_text"]["rule"],
                 "worksheet": "survey_free_text_coding.csv"}

    # ---- blind exercise
    ratings: dict[str, dict[str, str]] = defaultdict(dict)
    scorers: list[str] = []
    for r in kept:
        coder = f"R{r['row']:03d}"
        answered = False
        for c in items["blind_cells"]:
            key = f'{c["asset_id"]}|{c["code"]}'
            v = r["blind"].get(key, "")
            if not v:
                continue
            if v not in items["blind_options"]:
                invalid.append({"row": r["row"], "field": f"blind:{key}", "value": v})
                continue
            ratings[key][coder] = v
            answered = True
        if answered:
            scorers.append(coder)

    determinate = {u: {c: v for c, v in d.items() if v != UNKNOWN} for u, d in ratings.items()}
    coverage = {
        "per_cell": {u: round(len(determinate[u]) / len(d), 4) for u, d in ratings.items() if d},
        "per_scorer": {s: round(
            sum(1 for u in ratings if determinate.get(u, {}).get(s))
            / max(1, sum(1 for u in ratings if s in ratings[u])), 4) for s in scorers},
        "rule": plan["coverage_reporting"]["rule"],
    }

    reliability: dict[str, Any] = {
        "scorers": len(scorers), "coverage": coverage,
        "unknown_handling": plan["reliability"]["unknown_handling"],
        "krippendorff_alpha": (krippendorff_alpha_nominal(determinate)
                               if len(scorers) >= mins["reliability_alpha"]
                               else {"alpha": None, "alpha_status": "below_minimum_scorer_count"}),
    }
    min_overlap = plan["reliability"]["inter_rater_reliability"]["edge_cases"][
        "minimum_overlapping_determinate_cells_per_pair"]
    pairwise, excluded_pairs = [], []
    if len(scorers) >= mins["reliability_pairwise"]:
        for a, b in itertools.combinations(scorers, 2):
            shared = [u for u, d in determinate.items() if a in d and b in d]
            if len(shared) < min_overlap:
                excluded_pairs.append({"pair": [a, b], "overlap": len(shared)})
                continue
            k = cohen_kappa([determinate[u][a] for u in shared], [determinate[u][b] for u in shared])
            k["pair"] = [a, b]
            pairwise.append(k)
    est = [p["kappa"] for p in pairwise if p["kappa"] is not None]
    reliability["pairwise_cohen_kappa"] = {
        "pairs_estimated": len(est), "pairs_excluded_for_low_overlap": len(excluded_pairs),
        "pairs_undefined": len(pairwise) - len(est), "excluded": excluded_pairs,
        "mean_kappa": round(sum(est) / len(est), 4) if est else None, "pairs": pairwise}

    # ---- reference agreement: per respondent, plus a per-cell distribution
    reference, ref_state = load_reference(repo, items["blind_cells"])
    per_respondent = []
    for s in scorers:
        obs, proj = [], []
        for u, d in determinate.items():
            if s in d and reference.get(u) is not None:
                obs.append(d[s])
                proj.append(reference[u])
        if not obs:
            per_respondent.append({"respondent": s, "comparable_cells": 0,
                                   "agreement": None, "kappa": None,
                                   "kappa_status": "no_comparable_cells"})
            continue
        k = cohen_kappa(obs, proj)
        per_respondent.append({"respondent": s, "comparable_cells": len(obs),
                               "agreement": round(sum(o == p for o, p in zip(obs, proj)) / len(obs), 4),
                               "kappa": k["kappa"], "kappa_status": k["kappa_status"]})
    scored = [r for r in per_respondent if r["agreement"] is not None]
    kappas = [r["kappa"] for r in per_respondent if r["kappa"] is not None]
    reference_agreement = {
        "label": plan["reliability"]["reference_agreement"]["label_required"],
        "definition": plan["reliability"]["reference_agreement"]["description"],
        "caution": plan["reliability"]["reference_agreement"]["label_prohibited"],
        "respondents_scored": len(scored),
        "mean_agreement_across_respondents": (round(sum(r["agreement"] for r in scored) / len(scored), 4)
                                              if scored else None),
        "mean_kappa_across_respondents": round(sum(kappas) / len(kappas), 4) if kappas else None,
        "respondents_with_undefined_kappa": len(per_respondent) - len(kappas),
        "by_respondent": per_respondent,
    }

    status = repo / "data/processed/01_classification/classification_status.json"
    cell_output = []
    for c in items["blind_cells"]:
        u = f'{c["asset_id"]}|{c["code"]}'
        dist = Counter(ratings.get(u, {}).values())
        cell_output.append({"cell": u, "label": c["label"],
                            "distribution": {o: dist.get(o, 0) for o in items["blind_options"]},
                            "project_value": reference.get(u),
                            "project_state": ref_state.get(u, "absent"),
                            "coverage": coverage["per_cell"].get(u)})

    # ---- contrast (secondary)
    contrast = _contrast(repo, plan, taxonomy, fn_means)

    summary = {
        "plan_version": plan["document_version"],
        "plan_freeze_date": plan["freeze_date"],
        "output_scope": scope,
        "data_source": "synthetic_fixture" if scope == "synthetic" else "panel_responses",
        "responses_file": responses.name,
        "recruitment": recruitment,
        "ingestion": {"rows": ingest["rows"], "analysed": len(kept),
                      "unexpected_columns": ingest["unexpected_columns"],
                      "free_text_columns_bound_by_position": ingest["free_text_columns_bound_by_position"],
                      "invalid_values": invalid,
                      "invalid_value_count": len(invalid),
                      "rule": plan["input_validation"]["unrecognised_values"]},
        "excluded": dropped,
        "exclusion_rule": plan["inclusion_and_exclusion"]["duplicates"],
        "denominator_rule": plan["inclusion_and_exclusion"]["partial_responses"],
        "function_importance": fn_means,
        "frozen_prediction": prediction,
        "rules": rules,
        "gate_g1": g1,
        "checkbox_items": checkboxes,
        "free_text": free_text,
        "contrast_statistic": contrast,
        "reliability": reliability,
        "reference_agreement": reference_agreement,
        "blind_cell_detail": cell_output,
        "classification_status_at_analysis": (load(status)["counts"] if status.exists() else None),
    }
    if scope == "synthetic":
        summary["warning"] = "Produced from synthetic responses. No figure here is a finding."
    return summary, free_rows, reference


def _contrast(repo: Path, plan: dict, taxonomy: dict, fn_means: dict) -> dict[str, Any]:
    cs = plan["ranking_prediction"]["contrast_statistic"]
    out: dict[str, Any] = {"status": cs["status"],
                           "what_it_actually_compares": cs["what_it_actually_compares"],
                           "prohibited_claims": cs["prohibited_claims"],
                           "interpretation": cs["interpretation"],
                           "artifact": cs["project_side"]["artifact"], "outcomes": {}}
    bundle_scores = {}
    for bundle, codes in taxonomy["bundles"].items():
        ms = [fn_means[c]["mean"] for c in codes if fn_means.get(c, {}).get("mean") is not None]
        bundle_scores[bundle] = round(sum(ms) / len(ms), 4) if len(ms) == len(codes) else None
    out["panel_bundle_scores"] = bundle_scores

    risk = repo / cs["project_side"]["artifact"]
    if not risk.exists():
        out["outcomes"] = {"status": "not_computable", "reason": "risk test artifact absent"}
        return out
    proj: dict[str, dict[str, float]] = defaultdict(dict)
    with risk.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("sample") != "provisional_universe" or r.get("estimable") not in ("1", "True", "true"):
                continue
            if not r["predictor"].startswith("bundle_"):
                continue
            proj[r["outcome"]][r["predictor"][len("bundle_"):]] = float(r[cs["project_side"]["field"]])
    for outcome in cs["outcomes"]:
        pv = proj.get(outcome, {})
        pairs = [(b, bundle_scores[b], pv[b]) for b in taxonomy["bundles"]
                 if bundle_scores.get(b) is not None and b in pv]
        detail = [{"bundle": b, "panel_score": s, "permutation_p": p} for b, s, p in pairs]
        if len(pairs) < len(taxonomy["bundles"]):
            out["outcomes"][outcome] = {"status": "not_computable", "pairs_available": len(pairs),
                                        "pairs_required": len(taxonomy["bundles"]), "per_bundle": detail}
            continue
        out["outcomes"][outcome] = {
            "status": "computed", "n_pairs": len(pairs),
            "spearman_rho": spearman([s for _, s, _ in pairs], [-p for _, _, p in pairs]),
            "p_value": None, "per_bundle": detail}
    return out


def load_reference(repo: Path, cells: list[dict]) -> tuple[dict[str, str | None], dict[str, str]]:
    cfg = repo / "config"
    decisions: dict[tuple[str, str], tuple[str, int | None]] = {}
    for name in ["crypto_evidence_tranche_a.json", "crypto_design_evidence_tranche_1.json",
                 "crypto_h8_evidence_tranche_1.json", "crypto_h8_evidence_tranche_2.json",
                 "crypto_h2_expansion_evidence.json"]:
        path = cfg / name
        if not path.exists():
            continue
        for dec in load(path).get("decisions", []):
            status = dec.get("status", "reviewed" if name.endswith("expansion_evidence.json") else "unknown")
            decisions[(dec["asset_id"], dec["code"])] = (status, dec.get("recommended_value"))
    settled = {"verified", "reviewed"}
    values: dict[str, str | None] = {}
    states: dict[str, str] = {}
    for c in cells:
        key = f'{c["asset_id"]}|{c["code"]}'
        st, val = decisions.get((c["asset_id"], c["code"]), (None, None))
        values[key] = ("Yes" if val == 1 else "No") if st in settled and val is not None else None
        states[key] = st or "absent"
    return values, states


def reference_snapshot(values: dict[str, str | None], states: dict[str, str] | None = None) -> dict[str, Any]:
    payload = json.dumps(sorted(values.items()), separators=(",", ":"))
    return {"values": dict(sorted(values.items())),
            "sha256": hashlib.sha256(payload.encode()).hexdigest(),
            "note": "The reference values this run used. A later correction is documented as its own "
                    "entry and never applied retroactively to a published agreement figure."}


def run(repo: Path, responses: Path, scope: str) -> dict[str, Any]:
    summary, free_rows, reference = build(repo, responses, scope)
    out = (repo / "data/synthetic/survey" if scope == "synthetic"
           else repo / "data/processed/01_classification")
    out.mkdir(parents=True, exist_ok=True)
    (out / "survey_panel_analysis.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with (out / "survey_free_text_coding.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["response_id", "item_id", "kind", "text", "argument_group"])
        w.writeheader()
        w.writerows(free_rows)
    if scope == "panel":
        (out / "survey_reference_snapshot.json").write_text(
            json.dumps(reference_snapshot(reference), indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Panel survey analysis under the frozen plan")
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--responses", type=Path, required=True)
    ap.add_argument("--scope", required=True, choices=["synthetic", "panel"],
                    help="Declared explicitly. Never inferred from the file path.")
    a = ap.parse_args()
    s = run(a.repo.resolve(), a.responses, a.scope)
    print(json.dumps({k: s[k] for k in ["plan_version", "output_scope", "data_source", "ingestion"]}, indent=2))
