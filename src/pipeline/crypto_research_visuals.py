from __future__ import annotations

import argparse, csv, html, json
from pathlib import Path
from typing import Any


COLORS={"navy":"#17324d","blue":"#3478b8","gold":"#d99a2b","green":"#3b8c6e","gray":"#d7dde3","text":"#17212b","muted":"#647383","red":"#b6534c","white":"#ffffff"}


def read_csv(path: Path) -> list[dict[str,str]]:
    with path.open(newline="",encoding="utf-8") as handle: return list(csv.DictReader(handle))


def svg_text(x: float,y: float,text: Any,anchor: str="start",size: int=13,weight: int=400,fill: str|None=None) -> str:
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{weight}" fill="{fill or COLORS["text"]}">{html.escape(str(text))}</text>'


def horizontal_bars(title: str, subtitle: str, items: list[tuple[str,float,str]], value_format, width: int=900) -> str:
    left,right,top,row_h=260,90,92,42; height=top+row_h*len(items)+58; maximum=max(v for _,v,_ in items)*1.08
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">',f'<rect width="100%" height="100%" fill="{COLORS["white"]}"/>',svg_text(24,32,title,size=20,weight=600),svg_text(24,57,subtitle,size=12,fill=COLORS["muted"])]
    plot=width-left-right
    for i,(label,value,color) in enumerate(items):
        y=top+i*row_h; bar=plot*value/maximum
        parts += [svg_text(left-12,y+18,label,anchor="end"),f'<rect x="{left}" y="{y}" width="{plot}" height="22" rx="3" fill="{COLORS["gray"]}" opacity="0.38"/>',f'<rect x="{left}" y="{y}" width="{bar:.2f}" height="22" rx="3" fill="{color}"/>',svg_text(left+bar+8,y+17,value_format(value),size=12,weight=600)]
    parts.append('</svg>'); return "\n".join(parts)+"\n"


def hypothesis_flow(rows: list[dict[str,str]]) -> str:
    width,height=1000,360; xs=[55,245,435,625,815]; colors={"H1":COLORS["gold"],"H2":COLORS["gold"],"H3":COLORS["red"],"H4":COLORS["gray"],"H8":COLORS["green"]}
    answers={"H1":"Suggestive","H2":"Definition-sensitive","H3":"Not identified","H4":"Data-blocked","H8":"Groups favored"}
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Research flow from classification to five hypothesis results">',f'<rect width="100%" height="100%" fill="{COLORS["white"]}"/>',svg_text(24,32,"From classification to empirical evidence",size=20,weight=600),svg_text(24,57,"One verified matrix feeds five distinct tests; evidence strength differs by question.",size=12,fill=COLORS["muted"]),f'<rect x="350" y="82" width="300" height="54" rx="8" fill="{COLORS["navy"]}"/>',svg_text(500,105,"23 assets × 10 economic functions",anchor="middle",size=15,weight=600,fill=COLORS["white"]),svg_text(500,125,"230 human-verified decisions",anchor="middle",size=12,fill=COLORS["white"])]
    for x,row in zip(xs,rows):
        parts += [f'<line x1="500" y1="136" x2="{x+65}" y2="198" stroke="{COLORS["muted"]}" stroke-width="1.5"/>',f'<rect x="{x}" y="198" width="130" height="94" rx="8" fill="{colors[row["hypothesis"]]}" opacity="0.9"/>',svg_text(x+65,224,row["hypothesis"],anchor="middle",size=16,weight=600,fill=COLORS["white"] if row["hypothesis"]!="H4" else COLORS["text"]),svg_text(x+65,249,answers[row["hypothesis"]],anchor="middle",size=12,weight=600,fill=COLORS["white"] if row["hypothesis"]!="H4" else COLORS["text"]),svg_text(x+65,273,row["sample"],anchor="middle",size=11,fill=COLORS["white"] if row["hypothesis"]!="H4" else COLORS["text"])]
    parts += [svg_text(500,330,"Exploratory association ≠ causation or investment recommendation",anchor="middle",size=12,fill=COLORS["muted"]),'</svg>']; return "\n".join(parts)+"\n"


def build(group_summary: dict[str,Any], h8_rows: list[dict[str,str]], register_rows: list[dict[str,str]]) -> dict[str,str]:
    groups=sorted(group_summary["group_counts"].items(),key=lambda item:item[1],reverse=True)
    group_svg=horizontal_bars("Economic-function groups in the verified universe","Assets may belong to several groups; n = 23.",[(name.replace("_"," ").title(),float(count),COLORS["blue"]) for name,count in groups],lambda v:f"{int(v)} assets")
    primary=[r for r in h8_rows if r["outcome"]=="mean_log_market_cap_usd"]
    benchmark=next(r for r in primary if r["model_id"]=="raw_function_breadth"); selected=[r for r in primary if r["model_id"].startswith("bundle_") and r["model_id"] not in {"bundle_count"}]
    selected.sort(key=lambda r:float(r["loo_rmse"])); items=[]
    for row in selected:
        significant=row.get("fdr_10pct_reject")=="1"; items.append((row["model_id"].removeprefix("bundle_").replace("_"," ").title(),float(row["loo_rmse"]),COLORS["green"] if significant else COLORS["blue"]))
    items.append(("Raw function breadth",float(benchmark["loo_rmse"]),COLORS["gold"]))
    rmse_svg=horizontal_bars("H8 out-of-sample valuation error","Lower LOAO RMSE is better. Green groups survive 10% FDR; gold is the breadth benchmark.",items,lambda v:f"{v:.3f}")
    return {"crypto-function-group-coverage.svg":group_svg,"crypto-h8-prediction-error.svg":rmse_svg,"crypto-hypothesis-flow.svg":hypothesis_flow(register_rows)}


def run(repo: Path) -> dict[str,Any]:
    groups=json.loads((repo/"data/processed/01_classification/crypto_verified_universe_summary.json").read_text())
    visuals=build(groups,read_csv(repo/"data/processed/02_valuation/crypto_h8_verified_universe_results.csv"),read_csv(repo/"data/processed/02_valuation/crypto_hypothesis_evidence_register.csv"))
    out=repo/"research/figures"; out.mkdir(parents=True,exist_ok=True)
    for name,content in visuals.items(): (out/name).write_text(content,encoding="utf-8")
    report=repo/"research/findings/crypto-visual-analysis.md"
    report.write_text("# Crypto economic-function analysis — visual summary\n\n![Research flow](../figures/crypto-hypothesis-flow.svg)\n\n![Function-group coverage](../figures/crypto-function-group-coverage.svg)\n\n![H8 prediction error](../figures/crypto-h8-prediction-error.svg)\n\nGreen H8 bars identify groups that survive the pre-specified 10% false-discovery threshold. Lower prediction error is better. These are exploratory cross-sectional associations, not causal estimates.\n",encoding="utf-8")
    return {"status":"crypto_research_visuals_complete","figures":sorted(visuals),"report":str(report.relative_to(repo))}


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--repo",type=Path,default=Path.cwd()); print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
