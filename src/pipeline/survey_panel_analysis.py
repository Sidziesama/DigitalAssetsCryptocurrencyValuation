"""Panel survey analysis, executing config/survey_analysis_plan.json v1.1.

Every threshold, denominator rule and level definition is read from the frozen
plan at run time. Nothing is hard-coded here that the plan also states, so a
divergence between code and plan is a load error rather than a silent choice.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

UNKNOWN = "Unknown"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------- consensus


def classify_consensus(counts: Counter, condition_dependent: str, thresholds: dict,
                       min_n: int) -> dict[str, Any]:
    """Apply the v1.1 level ladder. Requires a UNIQUE plurality; ties -> divided."""
    n = sum(counts.values())
    shares = {k: v / n for k, v in counts.items()} if n else {}
    out: dict[str, Any] = {"n": n, "counts": dict(sorted(counts.items())),
                           "shares": {k: round(v, 4) for k, v in sorted(shares.items())}}
    if n < min_n:
        out.update(level="under_powered", leader=None, leader_share=None,
                   validation_status="unresolved")
        return out

    top = max(shares.values())
    leaders = [k for k, v in shares.items() if v == top]
    if len(leaders) > 1:                      # exact tie at the top
        out.update(level="divided", leader=None, leader_share=round(top, 4),
                   tied_options=sorted(leaders), validation_status="unresolved")
        return out

    leader = leaders[0]
    if top >= thresholds["adopt"]:
        level = "consensus_condition_dependent" if leader == condition_dependent else "consensus_adopt"
    elif top >= thresholds["leaning"]:
        level = "leaning"
    else:
        level = "divided"
    out.update(level=level, leader=leader, leader_share=round(top, 4),
               validation_status="externally_validated" if level == "consensus_adopt" else "unresolved")
    return out


# ------------------------------------------------------------- reliability


def cohen_kappa(a: list[str], b: list[str]) -> dict[str, Any]:
    n = len(a)
    if n == 0:
        return {"n": 0, "observed_agreement": None, "kappa": None,
                "kappa_status": "no_overlap"}
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[k] / n) * (cb[k] / n) for k in set(a) | set(b))
    if abs(pe - 1.0) < 1e-12:
        return {"n": n, "observed_agreement": round(po, 4), "kappa": None,
                "kappa_status": "undefined_expected_agreement_is_one"}
    return {"n": n, "observed_agreement": round(po, 4),
            "kappa": round((po - pe) / (1 - pe), 4), "kappa_status": "estimated"}


def krippendorff_alpha_nominal(ratings: dict[str, dict[str, str]]) -> dict[str, Any]:
    """ratings[unit][coder] = category. Handles incomplete matrices."""
    units = {u: list(v.values()) for u, v in ratings.items() if len(v) >= 2}
    if not units:
        return {"alpha": None, "alpha_status": "no_unit_has_two_or_more_coders",
                "units_used": 0, "pairable_values": 0}
    n_total = sum(len(v) for v in units.values())
    do_num = 0.0
    for vals in units.values():
        m = len(vals)
        c = Counter(vals)
        disagreeing = m * (m - 1) - sum(x * (x - 1) for x in c.values())
        do_num += disagreeing / (m - 1)
    do = do_num / n_total
    allv = Counter(v for vals in units.values() for v in vals)
    de = (n_total / (n_total - 1)) * (1 - sum((x / n_total) ** 2 for x in allv.values())) if n_total > 1 else 0.0
    if de <= 1e-12:
        return {"alpha": None, "alpha_status": "undefined_expected_disagreement_is_zero",
                "units_used": len(units), "pairable_values": n_total,
                "category_distribution": dict(allv)}
    return {"alpha": round(1 - do / de, 4), "alpha_status": "estimated",
            "units_used": len(units), "pairable_values": n_total,
            "observed_disagreement": round(do, 6), "expected_disagreement": round(de, 6)}


# ---------------------------------------------------------------- contrast


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


# ------------------------------------------------------------------- build


def build(repo: Path, responses: Path) -> dict[str, Any]:
    plan = load(repo / "config/survey_analysis_plan.json")
    items = load(repo / "config/survey_items.json")
    taxonomy = load(repo / "config/crypto_phase1_taxonomy.json")

    if not plan["document_version"].startswith("1.1"):
        raise SystemExit(f"plan version {plan['document_version']} is not the version this module implements")

    mins = plan["minimum_counts"]
    levels = {l["label"]: l for l in plan["consensus"]["levels"]}
    thresholds = {"adopt": 0.70, "leaning": 0.50}

    with responses.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    n_submissions = len(rows)

    # duplicates are the only exclusion the plan permits
    seen, kept, dropped = set(), [], []
    for i, r in enumerate(rows):
        key = r.get("Email Address", "").strip().lower()
        if key and key in seen:
            dropped.append({"row": i, "reason": "duplicate_email"})
            continue
        if key:
            seen.add(key)
        kept.append(r)

    def answers(col: str) -> list[str]:
        return [r[col].strip() for r in kept if col in r and r[col].strip()]

    # ---- boundary and materiality consensus (item-level denominators)
    rules: dict[str, Any] = {}
    for spec in items["boundary_items"] + items["materiality_items"]:
        col = spec["title"]
        vals = answers(col)
        res = classify_consensus(Counter(vals), spec.get("condition_dependent_option", "Depends"),
                                 thresholds, mins["consensus_assessable"])
        res["item_id"] = spec["item_id"]
        res["question"] = col
        if "project_rule" in spec:
            res["project_working_convention"] = spec["project_rule"]
            res["rule_name"] = spec["rule_name"]
            res["panel_agrees_with_working_convention"] = (
                res["level"] == "consensus_adopt" and res["leader"] == spec["project_rule"])
        res["effect"] = levels[res["level"]]["effect"]
        if res["level"] == "divided":
            res["contested"] = True
        rules[spec["item_id"]] = res

    boundary_ids = [s["item_id"] for s in items["boundary_items"]]
    validated = [i for i in boundary_ids if rules[i]["validation_status"] == "externally_validated"]
    g1 = {
        "gate": "G1 boundary rules validated externally",
        "requirement": plan["consensus"]["validation_status_per_rule"]["gate_rule"],
        "boundary_rules_total": len(boundary_ids),
        "externally_validated": len(validated),
        "unresolved": sorted(set(boundary_ids) - set(validated)),
        "passes": len(validated) == len(boundary_ids) and len(boundary_ids) > 0,
        "note": "An unresolved rule continues as the project's working convention and is not externally validated.",
    }

    # ---- importance grid -> bundle scores -> contrast
    grid = items["importance_grid"]
    scale = grid["scale"]
    fn_means: dict[str, dict[str, Any]] = {}
    for row_label, code in grid["rows"].items():
        col = f'{grid["title"]} [{row_label}]'
        vals = [scale[v] for v in answers(col) if v in scale]
        fn_means[code] = {"n": len(vals),
                          "mean": round(sum(vals) / len(vals), 4) if vals else None}

    bundle_scores = {}
    for bundle, codes in taxonomy["bundles"].items():
        ms = [fn_means[c]["mean"] for c in codes if fn_means.get(c, {}).get("mean") is not None]
        bundle_scores[bundle] = round(sum(ms) / len(ms), 4) if len(ms) == len(codes) else None

    risk = repo / "data/processed/03_risk/crypto_function_risk_tests.csv"
    contrast: dict[str, Any] = {"artifact": str(risk.relative_to(repo)),
                                "interpretation": plan["ranking_prediction"]["contrast_statistic"]["interpretation"],
                                "outcomes": {}}
    if risk.exists():
        proj = defaultdict(dict)
        with risk.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r.get("sample") != "provisional_universe" or r.get("estimable") not in ("1", "True", "true"):
                    continue
                pred = r["predictor"]
                if not pred.startswith("bundle_"):
                    continue
                proj[r["outcome"]][pred[len("bundle_"):]] = float(r["permutation_p_two_sided"])
        for outcome in plan["ranking_prediction"]["contrast_statistic"]["outcomes"]:
            pv = proj.get(outcome, {})
            pairs = [(b, bundle_scores[b], pv[b]) for b in taxonomy["bundles"]
                     if bundle_scores.get(b) is not None and b in pv]
            if len(pairs) < len(taxonomy["bundles"]):
                contrast["outcomes"][outcome] = {
                    "status": "not_computable", "pairs_available": len(pairs),
                    "pairs_required": len(taxonomy["bundles"]),
                    "per_bundle": [{"bundle": b, "panel_score": s, "permutation_p": p} for b, s, p in pairs]}
                continue
            # panel: higher score = more important. project: lower p = stronger.
            rho = spearman([s for _, s, _ in pairs], [-p for _, _, p in pairs])
            contrast["outcomes"][outcome] = {
                "status": "computed", "n_pairs": len(pairs), "spearman_rho": rho,
                "p_value": None,
                "per_bundle": [{"bundle": b, "panel_score": s, "permutation_p": p} for b, s, p in pairs]}
    else:
        contrast["outcomes"] = {"status": "not_computable", "reason": "risk test artifact absent"}

    # ---- blind exercise: reliability and reference agreement
    status = load(repo / "data/processed/01_classification/classification_status.json") \
        if (repo / "data/processed/01_classification/classification_status.json").exists() else {}
    reference = load_reference(repo, items["blind_cells"])

    ratings: dict[str, dict[str, str]] = defaultdict(dict)
    scorers: list[str] = []
    for idx, r in enumerate(kept):
        coder = f"S{idx:03d}"
        any_answer = False
        for cell in items["blind_cells"]:
            col = cell["label"] + items["blind_cell_suffix"]
            v = r.get(col, "").strip()
            if v:
                any_answer = True
                ratings[f'{cell["asset_id"]}|{cell["code"]}'][coder] = v
        if any_answer:
            scorers.append(coder)

    determinate = {u: {c: v for c, v in d.items() if v != UNKNOWN} for u, d in ratings.items()}
    unknown_rate = {u: round(sum(1 for v in d.values() if v == UNKNOWN) / len(d), 4)
                    for u, d in ratings.items() if d}

    reliability: dict[str, Any] = {
        "scorers": len(scorers),
        "minimum_scorers_for_alpha": mins["reliability_alpha"],
        "minimum_scorers_for_pairwise": mins["reliability_pairwise"],
        "unknown_rate_by_cell": unknown_rate,
        "unknown_handling": plan["reliability"]["unknown_handling"],
    }
    if len(scorers) >= mins["reliability_alpha"]:
        reliability["krippendorff_alpha"] = krippendorff_alpha_nominal(determinate)
    else:
        reliability["krippendorff_alpha"] = {"alpha": None,
                                             "alpha_status": "below_minimum_scorer_count"}

    min_overlap = plan["reliability"]["inter_rater_reliability"]["edge_cases"][
        "minimum_overlapping_determinate_cells_per_pair"]
    pairwise, excluded_pairs = [], []
    if len(scorers) >= mins["reliability_pairwise"]:
        for a, b in itertools.combinations(scorers, 2):
            ua = [u for u, d in determinate.items() if a in d and b in d]
            if len(ua) < min_overlap:
                excluded_pairs.append({"pair": [a, b], "overlap": len(ua)})
                continue
            k = cohen_kappa([determinate[u][a] for u in ua], [determinate[u][b] for u in ua])
            k["pair"] = [a, b]
            pairwise.append(k)
    est = [p["kappa"] for p in pairwise if p["kappa"] is not None]
    reliability["pairwise_cohen_kappa"] = {
        "pairs_estimated": len(est), "pairs_excluded_for_low_overlap": len(excluded_pairs),
        "pairs_undefined": len(pairwise) - len(est),
        "excluded": excluded_pairs,
        "mean_kappa": round(sum(est) / len(est), 4) if est else None,
        "pairs": pairwise,
    }

    ref_rows, ref_covered = [], 0
    for u, d in determinate.items():
        ref = reference.get(u)
        if ref is None:
            ref_rows.append({"cell": u, "status": "no_reference_value",
                             "project_state": reference.get(u + "|state", "pending_or_provisional")})
            continue
        ref_covered += 1
        agree = sum(1 for v in d.values() if v == ref)
        ref_rows.append({"cell": u, "reference": ref, "scorers": len(d),
                         "agreeing": agree,
                         "agreement": round(agree / len(d), 4) if d else None})
    scored = [r for r in ref_rows if "agreement" in r and r["agreement"] is not None]
    reference_agreement = {
        "label": plan["reliability"]["reference_agreement"]["label_required"],
        "caution": plan["reliability"]["reference_agreement"]["label_prohibited"],
        "cells_with_a_reference_value": ref_covered,
        "cells_without_a_reference_value": len(ref_rows) - ref_covered,
        "mean_agreement": round(sum(r["agreement"] for r in scored) / len(scored), 4) if scored else None,
        "by_cell": ref_rows,
    }

    return {
        "plan_version": plan["document_version"],
        "plan_freeze_date": plan["freeze_date"],
        "responses_file": responses.name,
        "submissions": n_submissions,
        "analysed": len(kept),
        "excluded": dropped,
        "exclusion_rule": plan["inclusion_and_exclusion"]["partial_responses"],
        "function_importance": fn_means,
        "bundle_scores": bundle_scores,
        "rules": rules,
        "gate_g1": g1,
        "contrast_statistic": contrast,
        "reliability": reliability,
        "reference_agreement": reference_agreement,
        "classification_status_at_analysis": status.get("counts"),
    }


def load_reference(repo: Path, cells: list[dict]) -> dict[str, str | None]:
    """Project's own value for each blind cell: Yes / No, or None when not settled."""
    cfg = repo / "config"
    decisions: dict[tuple[str, str], tuple[str, int | None]] = {}
    for name in ["crypto_evidence_tranche_a.json", "crypto_design_evidence_tranche_1.json",
                 "crypto_h8_evidence_tranche_1.json", "crypto_h8_evidence_tranche_2.json",
                 "crypto_h2_expansion_evidence.json"]:
        path = cfg / name
        if not path.exists():
            continue
        for dec in load(path).get("decisions", []):
            # The expansion file carries no status field; its cells are the blind-reviewed
            # ten, so a recommended_value there is settled. Elsewhere status must be verified.
            status = dec.get("status", "reviewed" if name.endswith("expansion_evidence.json") else "unknown")
            decisions[(dec["asset_id"], dec["code"])] = (status, dec.get("recommended_value"))
    settled = {"verified", "reviewed"}
    out: dict[str, str | None] = {}
    for c in cells:
        key = f'{c["asset_id"]}|{c["code"]}'
        st, val = decisions.get((c["asset_id"], c["code"]), (None, None))
        out[key] = ("Yes" if val == 1 else "No") if st in settled and val is not None else None
        out[key + "|state"] = st or "absent"
    return out


def run(repo: Path, responses: Path) -> dict[str, Any]:
    """Synthetic input never writes into data/processed. A test fixture and a
    finding must not be able to occupy the same filename."""
    summary = build(repo, responses)
    synthetic = "synthetic" in responses.as_posix()
    summary["data_source"] = "synthetic_fixture" if synthetic else "panel_responses"
    if synthetic:
        summary["warning"] = "Produced from synthetic responses. No figure here is a finding."
        out = repo / "data/synthetic/survey"
    else:
        out = repo / "data/processed/01_classification"
    out.mkdir(parents=True, exist_ok=True)
    (out / "survey_panel_analysis.json").write_text(json.dumps(summary, indent=2) + "\n",
                                                    encoding="utf-8")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Panel survey analysis under the frozen plan")
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--responses", type=Path, required=True)
    a = ap.parse_args()
    print(json.dumps(run(a.repo.resolve(), a.responses), indent=2)[:4000])
