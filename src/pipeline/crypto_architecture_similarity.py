from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from statistics import mean
from typing import Any


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def jaccard(a: tuple[int, ...], b: tuple[int, ...]) -> float:
    intersection=sum(x == 1 and y == 1 for x,y in zip(a,b))
    union=sum(x == 1 or y == 1 for x,y in zip(a,b))
    return intersection/union if union else 1.0


def difference(pairs: list[dict[str, Any]], labels: dict[str, str]) -> float:
    same=[p["similarity"] for p in pairs if labels[p["asset_id_a"]] == labels[p["asset_id_b"]]]
    cross=[p["similarity"] for p in pairs if labels[p["asset_id_a"]] != labels[p["asset_id_b"]]]
    if not same or not cross: raise ValueError("architecture comparison requires same- and cross-architecture pairs")
    return mean(same)-mean(cross)


def build(rows: list[dict[str, str]], spec: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    features=spec["features"]
    if len(rows)!=23 or any(r.get("classification_status")!="complete_human_verified" for r in rows):
        raise ValueError("architecture test requires the complete verified 23-asset matrix")
    vectors={r["asset_id"]:tuple(int(r[f]) for f in features) for r in rows}
    labels={r["asset_id"]:r["architecture_context"] for r in rows}
    symbols={r["asset_id"]:r["symbol"] for r in rows}
    ids=sorted(vectors)
    pairs=[]
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            pairs.append({"asset_id_a":a,"symbol_a":symbols[a],"architecture_a":labels[a],"asset_id_b":b,"symbol_b":symbols[b],"architecture_b":labels[b],"same_architecture":labels[a]==labels[b],"similarity":jaccard(vectors[a],vectors[b])})
    observed=difference(pairs,labels)
    rng=random.Random(spec["inference"]["seed"]); values=list(labels.values()); draws=spec["inference"]["draws"]; extreme=0
    for _ in range(draws):
        shuffled=values[:]; rng.shuffle(shuffled); perm=dict(zip(ids,shuffled)); stat=difference(pairs,perm)
        extreme += abs(stat) >= abs(observed)-1e-15
    same=[p["similarity"] for p in pairs if p["same_architecture"]]; cross=[p["similarity"] for p in pairs if not p["same_architecture"]]
    top_cross=sorted((p for p in pairs if not p["same_architecture"]),key=lambda p:(-p["similarity"],p["symbol_a"],p["symbol_b"]))[:10]
    result={
        "status":"crypto_architecture_similarity_complete", "assets":len(rows), "pairs":len(pairs),
        "same_architecture_pairs":len(same), "cross_architecture_pairs":len(cross),
        "mean_same_architecture_similarity":mean(same), "mean_cross_architecture_similarity":mean(cross),
        "difference_same_minus_cross":observed, "permutation_p_two_sided":extreme/draws,
        "permutation_draws":draws, "top_cross_architecture_pairs":[{"pair":f"{p['symbol_a']}–{p['symbol_b']}","architecture":f"{p['architecture_a']} vs {p['architecture_b']}","similarity":p["similarity"]} for p in top_cross],
        "interpretation":spec["interpretation"]
    }
    return result,pairs


def chart(result: dict[str, Any]) -> str:
    same=result["mean_same_architecture_similarity"]*100; cross=result["mean_cross_architecture_similarity"]*100
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420" viewBox="0 0 900 420" role="img" aria-label="Economic similarity within and across technical architectures">','<rect width="100%" height="100%" fill="#ffffff"/>','<text x="30" y="38" font-family="Arial" font-size="22" font-weight="700" fill="#17212b">Does architecture tell us what a token does?</text>','<text x="30" y="64" font-family="Arial" font-size="13" fill="#647383">Average overlap across ten verified economic functions; 100% means identical function profiles.</text>']
    for y,label,value,color in [(115,"Same architecture",same,"#3478b8"),(190,"Different architecture",cross,"#d99a2b")]:
        width=620*value/100
        parts += [f'<text x="185" y="{y+23}" text-anchor="end" font-family="Arial" font-size="14" fill="#17212b">{label}</text>',f'<rect x="205" y="{y}" width="620" height="34" rx="4" fill="#e8edf1"/>',f'<rect x="205" y="{y}" width="{width:.1f}" height="34" rx="4" fill="{color}"/>',f'<text x="{min(815,215+width):.1f}" y="{y+23}" font-family="Arial" font-size="14" font-weight="700" fill="#17212b">{value:.1f}%</text>']
    verdict="Architecture helps somewhat" if result["difference_same_minus_cross"]>0 else "Architecture does not improve economic similarity"
    parts += ['<line x1="30" y1="265" x2="870" y2="265" stroke="#d7dde3"/>',f'<text x="30" y="302" font-family="Arial" font-size="18" font-weight="700" fill="#17212b">{verdict}</text>',f'<text x="30" y="330" font-family="Arial" font-size="14" fill="#17212b">Difference: {result["difference_same_minus_cross"]*100:+.1f} percentage points · permutation p = {result["permutation_p_two_sided"]:.3f}</text>','<text x="30" y="365" font-family="Arial" font-size="14" font-weight="700" fill="#17212b">Action: classify economic functions directly; do not infer them from “L1”, “PoS”, “PoW”, or “DeFi”.</text>','<text x="30" y="393" font-family="Arial" font-size="12" fill="#647383">Descriptive classification test—not evidence about returns or fair value.</text>','</svg>']
    return "\n".join(parts)+"\n"


def render(result: dict[str, Any]) -> str:
    direction="higher" if result["difference_same_minus_cross"]>0 else "lower"
    lines=["# Does technical architecture identify economic function?", "", "![Architecture versus economic similarity](../figures/crypto-architecture-economic-similarity.svg)", "", f"Across {result['assets']} assets there are {result['pairs']} unique pairs. Same-architecture pairs have average economic-function similarity of {result['mean_same_architecture_similarity']:.1%}; cross-architecture pairs average {result['mean_cross_architecture_similarity']:.1%}. Same-architecture similarity is {abs(result['difference_same_minus_cross']):.1%} {direction}, with a label-permutation p-value of {result['permutation_p_two_sided']:.3f}.", "", "## Strongest cross-architecture economic peers", "", "| Pair | Architecture | Function similarity |", "|---|---|---:|"]
    lines += [f"| {p['pair']} | {p['architecture']} | {p['similarity']:.0%} |" for p in result["top_cross_architecture_pairs"]]
    lines += ["", "## Advisory meaning", "", "Architecture is useful operational context, but economic functions must be measured directly. Assets built differently may perform nearly identical economic jobs, while assets sharing an architecture may have materially different value routes. Comparable selection should therefore begin with economic-function overlap and use architecture as a secondary risk descriptor.", ""]
    return "\n".join(lines)


def run(repo: Path) -> dict[str, Any]:
    rows=read_rows(repo/"data/processed/01_classification/crypto_verified_universe_profiles.csv")
    spec=json.loads((repo/"config/crypto_architecture_similarity.json").read_text())
    result,pairs=build(rows,spec)
    out=repo/"data/processed/02_valuation"; out.mkdir(parents=True,exist_ok=True)
    (out/"crypto_architecture_similarity.json").write_text(json.dumps(result,indent=2)+"\n")
    with (out/"crypto_architecture_similarity_pairs.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(pairs[0])); w.writeheader(); w.writerows(pairs)
    (repo/"research/figures/crypto-architecture-economic-similarity.svg").write_text(chart(result))
    (repo/"research/findings/crypto-architecture-economic-similarity.md").write_text(render(result))
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--repo",type=Path,default=Path.cwd())
    print(json.dumps(run(parser.parse_args().repo.resolve()),indent=2))
