from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

CODES = ["VA_MONETARY", "VA_GAS", "VA_STAKE", "VA_BURN", "VA_SCARCITY",
         "VA_COLLATERAL", "VA_GOV", "VA_PROTOCOL", "VA_UTILITY", "VA_INCENTIVE"]
FONT = "Arial"
INK, GOLD, CLAY, SLATE = "132238", "E0A33E", "C25A46", "40566E"
# classification status -> (fill, meaning)
STATUS = {
    "verified":    ("C8E6C9", "Evidence plus independent blind review complete"),
    "drafted":     ("FFF0C2", "Sourced by the coder, awaiting blind review"),
    "pending":     ("F8D7CF", "Held for adjudication; never defaults to zero"),
    "provisional": ("ECEFF3", "From the design matrix only, no evidence yet"),
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def collect(repo: Path) -> dict[str, Any]:
    cfg, proc = repo / "config", repo / "data/processed/01_classification"
    registry = load_json(cfg / "assets.json")
    design = load_json(cfg / "crypto_economic_design.json")
    profiles = read_csv(proc / "crypto_phase1_taxonomy_profiles.csv")
    tranche_a = load_json(cfg / "crypto_evidence_tranche_a.json")
    taxonomy = load_json(cfg / "crypto_phase1_taxonomy.json")
    codebook = read_csv(proc / "crypto_phase1_function_codebook.csv")

    # cell state: (value, status, source_url, source_date)
    cells: dict[tuple[str, str], tuple[Any, str, str, str]] = {}
    order = design["value_accrual_codes"]
    for asset in design["assets"]:
        for code, value in zip(order, asset["codes"]):
            cells[(asset["asset_id"], code)] = (value, "provisional", "", "")
    for row in profiles:
        if row.get("classification_status") != "complete_verified":
            continue
        for code in CODES:
            cells[(row["asset_id"], code)] = (int(row[code.lower()]), "verified", "", "")
    for dec in tranche_a["decisions"]:
        key = (dec["asset_id"], dec["code"])
        if key in cells and cells[key][1] == "verified":
            continue
        status = "drafted" if dec["status"] == "verified" else "pending"
        cells[key] = (dec["recommended_value"], status, dec.get("source_url", ""), dec.get("source_date", ""))

    # evidence sources for the verified core
    sources: list[dict[str, str]] = []
    for name in ["crypto_design_evidence_tranche_1.json", "crypto_h8_evidence_tranche_1.json",
                 "crypto_h8_evidence_tranche_2.json", "crypto_h2_expansion_evidence.json"]:
        path = cfg / name
        if not path.exists():
            continue
        for dec in load_json(path).get("decisions", []):
            sources.append({"asset_id": dec["asset_id"], "code": dec["code"],
                            "value": dec.get("recommended_value"), "source_url": dec.get("source_url", ""),
                            "source_date": dec.get("source_date", ""), "tranche": name.replace(".json", "")})
    for dec in tranche_a["decisions"]:
        sources.append({"asset_id": dec["asset_id"], "code": dec["code"], "value": dec.get("recommended_value"),
                        "source_url": dec.get("source_url", ""), "source_date": dec.get("source_date", ""),
                        "tranche": "crypto_evidence_tranche_a"})
    return {"registry": registry, "cells": cells, "codebook": codebook, "taxonomy": taxonomy,
            "tranche_a": tranche_a, "sources": sources,
            "design_as_of": design.get("as_of"), "profiles": profiles}


def style_title(ws, title: str, subtitle: str) -> None:
    ws["A1"] = title
    ws["A1"].font = Font(name=FONT, size=14, bold=True, color=INK)
    ws["A2"] = subtitle
    ws["A2"].font = Font(name=FONT, size=9, italic=True, color=SLATE)


def header_row(ws, row: int, values: list[str]) -> None:
    for index, value in enumerate(values, start=1):
        cell = ws.cell(row=row, column=index, value=value)
        cell.font = Font(name=FONT, size=9, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=INK)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.freeze_panes = ws.cell(row=row + 1, column=1)


def autosize(ws, widths: dict[int, int]) -> None:
    for column, width in widths.items():
        ws.column_dimensions[get_column_letter(column)].width = width


def build(repo: Path) -> tuple[Workbook, dict[str, Any]]:
    data = collect(repo)
    cells = data["cells"]
    crypto = [a for a in data["registry"]["assets"] if a["universe"] == "crypto"]
    counts: dict[str, int] = {s: 0 for s in STATUS}
    for asset in crypto:
        for code in CODES:
            counts[cells.get((asset["asset_id"], code), (None, "provisional", "", ""))[1]] += 1

    old_path = repo / "data/reference/digital_asset_research_universe.xlsx"
    old = load_workbook(old_path) if old_path.exists() else None
    wb = Workbook()

    # ---------------------------------------------------------------- README
    ws = wb.active
    ws.title = "README"
    style_title(ws, "Digital Asset Research Universe",
                f"Generated from the repository by src/pipeline/research_universe_workbook.py on {date.today().isoformat()}. Do not edit by hand.")
    rows = [
        ("Active phase", "Phase 1 — Economic classification. Phases 2 and 3 are on hold behind its gates; Phase 4 is deferred."),
        ("What this workbook is", "The human-readable view of the asset universe and its classification state. The machine-readable source is config/ and data/processed/01_classification/."),
        ("Crypto assets in registry", len(crypto)),
        ("Stable-value assets (deferred)", sum(a["universe"] == "stablecoin" for a in data["registry"]["assets"])),
        ("Classification cells", f"{len(crypto) * len(CODES)} total"),
        ("  verified", f"{counts['verified']} — evidence plus independent blind review"),
        ("  drafted", f"{counts['drafted']} — sourced, awaiting blind review"),
        ("  pending", f"{counts['pending']} — held for adjudication"),
        ("  provisional", f"{counts['provisional']} — design matrix only, no evidence"),
        ("Design matrix as of", data["design_as_of"]),
        ("Selection logic", "Market dominance first; liquidity and reproducible data access second; a limited growth sleeve third."),
        ("Reading the colours", "Green verified · amber drafted · red pending · grey provisional. A pending cell never defaults to zero."),
        ("Important", "Selection and design codes are research classifications, not investment recommendations or legal conclusions."),
        ("Maintenance", "Regenerate with: python -m src.pipeline.research_universe_workbook --repo ."),
    ]
    header_row(ws, 4, ["Field", "Value"])
    for index, (field, value) in enumerate(rows, start=5):
        ws.cell(row=index, column=1, value=field).font = Font(name=FONT, size=10, bold=not field.startswith("  "))
        ws.cell(row=index, column=2, value=value).font = Font(name=FONT, size=10)
        ws.cell(row=index, column=2).alignment = Alignment(wrap_text=True, vertical="top")
    autosize(ws, {1: 30, 2: 95})

    # ---------------------------------------------------------------- Universe
    ws = wb.create_sheet("Universe")
    style_title(ws, "Universe Selection",
                "Frozen market snapshot with selection rationale, plus live classification progress per asset.")
    head = ["asset_id", "symbol", "name", "universe", "market_cap_rank", "market_cap_usd", "volume_24h_usd",
            "volume_to_mcap", "selection_tier", "inclusion_rationale", "codes_verified", "codes_drafted",
            "codes_pending", "codes_provisional", "classification_state"]
    header_row(ws, 4, head)
    carried = {}
    if old and "Universe" in old.sheetnames:
        oldws = old["Universe"]
        oldhead = [c for c in next(oldws.iter_rows(min_row=4, max_row=4, values_only=True))]
        for row in oldws.iter_rows(min_row=5, values_only=True):
            record = dict(zip(oldhead, row))
            if record.get("asset_id"):
                carried[record["asset_id"]] = record
    line = 5
    for asset in data["registry"]["assets"]:
        prior = carried.get(asset["asset_id"], {})
        per = [cells.get((asset["asset_id"], c), (None, "provisional", "", ""))[1] for c in CODES] \
            if asset["universe"] == "crypto" else []
        tally = {s: per.count(s) for s in STATUS}
        state = ("deferred phase" if asset["universe"] != "crypto" else
                 "complete verified" if tally["verified"] == len(CODES) else
                 "in tranche review" if tally["drafted"] or tally["pending"] else "provisional only")
        values = [asset["asset_id"], asset["symbol"], asset["name"], asset["universe"],
                  prior.get("market_cap_rank"), prior.get("market_cap_usd"), prior.get("volume_24h_usd"),
                  f"=IFERROR(G{line}/F{line},0)", prior.get("selection_tier") or asset.get("tier"),
                  prior.get("inclusion_rationale"),
                  tally["verified"] or None, tally["drafted"] or None, tally["pending"] or None,
                  tally["provisional"] or None, state]
        for column, value in enumerate(values, start=1):
            cell = ws.cell(row=line, column=column, value=value)
            cell.font = Font(name=FONT, size=9)
            if column in (6, 7):
                cell.number_format = '$#,##0;($#,##0);-'
            if column == 8:
                cell.number_format = '0.000'
            if column == 15 and asset["universe"] == "crypto":
                key = {"complete verified": "verified", "in tranche review": "drafted",
                       "provisional only": "provisional"}[state]
                cell.fill = PatternFill("solid", fgColor=STATUS[key][0])
        line += 1
    autosize(ws, {1: 18, 2: 9, 3: 24, 4: 12, 5: 9, 6: 18, 7: 18, 8: 12, 9: 20, 10: 52, 11: 10, 12: 10, 13: 10, 14: 12, 15: 20})

    # ---------------------------------------------------------- economic_design
    ws = wb.create_sheet("economic_design")
    style_title(ws, "Economic design — ten functions by asset",
                "1 means the function is performed. Colour shows how well evidenced that cell is, which matters as much as the value.")
    header_row(ws, 4, ["asset_id", "symbol", "architecture"] + [c.replace("VA_", "") for c in CODES] + ["functions", "state"])
    arch = {row["asset_id"]: row.get("architecture_context", "") for row in data["profiles"]}
    line = 5
    for asset in crypto:
        states = [cells.get((asset["asset_id"], c), (None, "provisional", "", "")) for c in CODES]
        ws.cell(row=line, column=1, value=asset["asset_id"]).font = Font(name=FONT, size=9)
        ws.cell(row=line, column=2, value=asset["symbol"]).font = Font(name=FONT, size=9, bold=True)
        ws.cell(row=line, column=3, value=arch.get(asset["asset_id"], "")).font = Font(name=FONT, size=8, color=SLATE)
        for offset, (value, status, _, _) in enumerate(states):
            cell = ws.cell(row=line, column=4 + offset, value=value)
            cell.font = Font(name=FONT, size=9, bold=bool(value))
            cell.alignment = Alignment(horizontal="center")
            cell.fill = PatternFill("solid", fgColor=STATUS[status][0])
        known = [v for v, s, _, _ in states if v is not None]
        ws.cell(row=line, column=14, value=sum(known) if known else None).font = Font(name=FONT, size=9, bold=True)
        ws.cell(row=line, column=14).alignment = Alignment(horizontal="center")
        pending = sum(1 for _, s, _, _ in states if s == "pending")
        ws.cell(row=line, column=15,
                value="complete verified" if all(s == "verified" for _, s, _, _ in states)
                else f"{pending} pending" if pending else "provisional/drafted").font = Font(name=FONT, size=9)
        line += 1
    legend = line + 1
    ws.cell(row=legend, column=1, value="Legend").font = Font(name=FONT, size=10, bold=True)
    for offset, (status, (fill, meaning)) in enumerate(STATUS.items(), start=1):
        ws.cell(row=legend + offset, column=1, value=status).fill = PatternFill("solid", fgColor=fill)
        ws.cell(row=legend + offset, column=1).font = Font(name=FONT, size=9, bold=True)
        ws.cell(row=legend + offset, column=2, value=meaning).font = Font(name=FONT, size=9)
    autosize(ws, {1: 18, 2: 9, 3: 30, **{i: 10 for i in range(4, 14)}, 14: 10, 15: 20})

    # ---------------------------------------------------------------- Codebook
    ws = wb.create_sheet("Codebook")
    style_title(ws, "Classification codebook",
                "The live rules, generated from the pipeline. VA_PROTOCOL carries the adjudicated strict wording.")
    header_row(ws, 4, ["code", "bundle", "classification_rule", "value_indicators"])
    for index, row in enumerate(data["codebook"], start=5):
        for column, key in enumerate(["code", "bundle", "classification_rule", "value_indicators"], start=1):
            cell = ws.cell(row=index, column=column, value=row.get(key, "").replace("|", ", "))
            cell.font = Font(name=FONT, size=9, bold=(column == 1))
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    autosize(ws, {1: 18, 2: 26, 3: 78, 4: 52})

    # ----------------------------------------------------------- Adjudications
    ws = wb.create_sheet("Adjudications")
    style_title(ws, "Adjudicated rules and open consistency cases",
                "A rule adjudicated once binds every future case. Open cases block the cells they name.")
    header_row(ws, 4, ["case_id", "assets", "code", "status", "question or reason", "recommendation"])
    line = 5
    for case in data["taxonomy"].get("consistency_cases", []):
        values = [case.get("case_id"), "|".join(case.get("assets", [])), case.get("code"),
                  case.get("status"), case.get("reason") or case.get("question"), case.get("recommendation", "")]
        for column, value in enumerate(values, start=1):
            cell = ws.cell(row=line, column=column, value=value)
            cell.font = Font(name=FONT, size=9)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        line += 1
    for case in data["tranche_a"].get("consistency_cases", []):
        values = [case.get("case_id"), "|".join(case.get("assets", [])), case.get("code"),
                  case.get("status"), case.get("question"), case.get("recommendation", "")]
        for column, value in enumerate(values, start=1):
            cell = ws.cell(row=line, column=column, value=value)
            cell.font = Font(name=FONT, size=9)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            if column == 4:
                cell.fill = PatternFill("solid", fgColor=STATUS["pending"][0])
        line += 1
    autosize(ws, {1: 34, 2: 26, 3: 14, 4: 26, 5: 80, 6: 60})

    # --------------------------------------------------------- Evidence sources
    ws = wb.create_sheet("Evidence_sources")
    style_title(ws, "Evidence sources",
                "Every classification decision with a dated primary source. This is the audit trail.")
    header_row(ws, 4, ["asset_id", "code", "value", "source_date", "tranche", "source_url"])
    for index, row in enumerate(sorted(data["sources"], key=lambda r: (r["asset_id"], r["code"])), start=5):
        for column, key in enumerate(["asset_id", "code", "value", "source_date", "tranche", "source_url"], start=1):
            cell = ws.cell(row=index, column=column, value=row.get(key))
            cell.font = Font(name=FONT, size=8)
    autosize(ws, {1: 18, 2: 16, 3: 8, 4: 12, 5: 32, 6: 100})

    # -------------------------------------------------- stablecoin (carried)
    if old and "stablecoin_design" in old.sheetnames:
        ws = wb.create_sheet("stablecoin_design_deferred")
        style_title(ws, "Stablecoin design (Phase 4 — deferred)",
                    "Carried forward unchanged. Not an active gate; not maintained until Phases 1 to 3 close.")
        oldws = old["stablecoin_design"]
        for r, row in enumerate(oldws.iter_rows(min_row=4, values_only=True), start=4):
            for c, value in enumerate(row, start=1):
                cell = ws.cell(row=r, column=c, value=value)
                cell.font = Font(name=FONT, size=8, color=SLATE)
                if r == 4:
                    cell.font = Font(name=FONT, size=8, bold=True, color="FFFFFF")
                    cell.fill = PatternFill("solid", fgColor=SLATE)
        autosize(ws, {i: 16 for i in range(1, 23)})

    summary = {"status": "research_universe_workbook_complete", "generated": date.today().isoformat(),
               "crypto_assets": len(crypto), "cells": len(crypto) * len(CODES), "cell_status": counts,
               "sheets": wb.sheetnames}
    return wb, summary


def run(repo: Path) -> dict[str, Any]:
    wb, summary = build(repo)
    out = repo / "data/reference"
    out.mkdir(parents=True, exist_ok=True)
    wb.save(out / "digital_asset_research_universe.xlsx")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regenerate the research universe reference workbook")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()), indent=2))
