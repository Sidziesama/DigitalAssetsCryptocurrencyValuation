from __future__ import annotations

import argparse
import csv
import html
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .historical import read_csv, write_rows


BANDS = (10, 25, 50, 100, 500)


def numeric(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def quantile(values: Iterable[float], probability: float) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    if not 0 <= probability <= 1:
        raise ValueError("probability must be between zero and one")
    position = (len(ordered) - 1) * probability
    lower = math.floor(position); upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def asset_statistics(panel: list[dict[str, Any]], episodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_asset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    episode_by_asset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in panel: by_asset[row["asset_id"]].append(row)
    for row in episodes: episode_by_asset[row["asset_id"]].append(row)
    output = []
    for asset_id, rows in sorted(by_asset.items()):
        rows.sort(key=lambda row: row["date"])
        apes = [value for row in rows if (value := numeric(row.get("absolute_peg_error_bps"))) is not None]
        signed = [value for row in rows if (value := numeric(row.get("signed_deviation_bps"))) is not None]
        asset_episodes = episode_by_asset.get(asset_id, [])
        durations = [float(row["elapsed_days_to_recovery_or_censor"]) for row in asset_episodes]
        row_out: dict[str, Any] = {
            "asset_id": asset_id, "sample_tier": rows[0].get("sample_tier"), "failure_control": int(rows[0].get("failure_control", 0)),
            "start_date": rows[0]["date"], "end_date": rows[-1]["date"], "observations": len(rows),
            "mean_ape_bps": statistics.fmean(apes), "median_ape_bps": statistics.median(apes),
            "p95_ape_bps": quantile(apes, .95), "p99_ape_bps": quantile(apes, .99), "maximum_ape_bps": max(apes),
            "mean_signed_deviation_bps": statistics.fmean(signed), "downside_days": sum(value < 0 for value in signed),
            "episode_count_50bps": len(asset_episodes), "recovered_episode_count": sum(int(row["recovered"]) for row in asset_episodes),
            "censored_episode_count": sum(int(row["right_censored"]) for row in asset_episodes),
            "median_episode_days": statistics.median(durations) if durations else None,
            "maximum_episode_days": max(durations) if durations else None,
            "total_area_under_deviation_bps_days": sum(float(row["area_under_deviation_bps_days"]) for row in asset_episodes),
        }
        for band in BANDS:
            count = sum(int(row[f"breach_{band}bps"]) for row in rows)
            row_out[f"breach_days_{band}bps"] = count
            row_out[f"breach_rate_{band}bps"] = count / len(rows)
        output.append(row_out)
    return output


def monthly_stress(panel: list[dict[str, Any]]) -> list[dict[str, Any]]:
    months: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in panel: months[row["date"][:7]].append(row)
    output = []
    for month, rows in sorted(months.items()):
        primary = [row for row in rows if not int(row.get("failure_control", 0))]
        breach_assets = {row["asset_id"] for row in primary if int(row["breach_50bps"])}
        apes = [float(row["absolute_peg_error_bps"]) for row in primary]
        output.append({
            "month": month, "primary_assets_observed": len({row["asset_id"] for row in primary}),
            "primary_asset_days": len(primary), "breach_days_50bps": sum(int(row["breach_50bps"]) for row in primary),
            "assets_breaching_50bps": len(breach_assets), "mean_ape_bps": statistics.fmean(apes),
            "maximum_ape_bps": max(apes),
        })
    return output


def review_queue(episodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in episodes:
        if not int(row.get("data_review_flag", 0)):
            continue
        failure = int(row.get("failure_control", 0))
        status = "pending" if failure else "blocked_free_source"
        notes = "" if failure else "No Binance USDG pair in frozen exchange-info snapshot; CoinGecko public history is limited to 365 days. Requires an archival venue or provider crosscheck."
        output.append({
            "episode_id": row["episode_id"], "asset_id": row["asset_id"], "onset_date": row["onset_date"],
            "last_episode_date": row["last_episode_date"], "maximum_absolute_deviation_bps": row["maximum_absolute_deviation_bps"],
            "review_class": "expected_failure_regime_validation" if failure else "source_crosscheck_required",
            "proposed_primary_treatment": "exclude_failure_control_from_primary_models" if failure else "withhold_until_cross_source_confirmed",
            "review_status": status, "reviewer_notes": notes,
        })
    return output


def bar_svg(rows: list[dict[str, Any]], output: Path) -> None:
    ordered = sorted(rows, key=lambda row: float(row["median_ape_bps"]), reverse=True)
    width, height, left, top = 1000, 620, 170, 55
    chart_width, chart_height = 780, 500
    maximum = max(float(row["median_ape_bps"]) for row in ordered) or 1
    bar_height = chart_height / max(len(ordered), 1) * .72
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>', '<text x="30" y="32" font-family="Arial" font-size="20" font-weight="bold">Median absolute peg error by asset</text>']
    for index, row in enumerate(ordered):
        y = top + index * chart_height / len(ordered)
        value = float(row["median_ape_bps"]); bar_width = value / maximum * chart_width
        color = "#a33a3a" if int(row["failure_control"]) else "#3569a8"
        parts.extend([f'<text x="10" y="{y + bar_height * .78:.1f}" font-family="Arial" font-size="12">{html.escape(row["asset_id"])}</text>', f'<rect x="{left}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="{color}"/>', f'<text x="{left + bar_width + 5:.1f}" y="{y + bar_height * .78:.1f}" font-family="Arial" font-size="11">{value:.2f} bps</text>'])
    parts.append('</svg>')
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def run(repo: Path) -> dict[str, Any]:
    panel = read_csv(repo / "data" / "processed" / "empirical" / "stablecoin_daily.csv")
    episodes = read_csv(repo / "data" / "processed" / "empirical" / "stablecoin_depeg_episodes.csv")
    stats = asset_statistics(panel, episodes); monthly = monthly_stress(panel); reviews = review_queue(episodes)
    out = repo / "data" / "processed" / "empirical"
    stats_fields = list(stats[0]); monthly_fields = list(monthly[0]); review_fields = list(reviews[0]) if reviews else ["episode_id", "asset_id", "onset_date", "last_episode_date", "maximum_absolute_deviation_bps", "review_class", "proposed_primary_treatment", "review_status", "reviewer_notes"]
    write_rows(out / "stablecoin_asset_statistics.csv", stats, stats_fields)
    write_rows(out / "stablecoin_monthly_stress.csv", monthly, monthly_fields)
    write_rows(out / "stablecoin_episode_review_queue.csv", reviews, review_fields)
    ranked = sorted(episodes, key=lambda row: float(row["area_under_deviation_bps_days"]), reverse=True)
    write_rows(out / "stablecoin_episode_rankings.csv", ranked, list(ranked[0]))
    bar_svg(stats, repo / "outputs" / "generated" / "stablecoin_median_ape.svg")
    primary_stats = [row for row in stats if not row["failure_control"]]
    highest_median = max(primary_stats, key=lambda row: row["median_ape_bps"])
    highest_episode_count = max(primary_stats, key=lambda row: row["episode_count_50bps"])
    highest_month = max(monthly, key=lambda row: row["breach_days_50bps"])
    summary = {
        "assets": len(stats), "primary_assets": len(primary_stats), "months": len(monthly), "review_queue": len(reviews),
        "failure_control_reviews": sum(row["review_class"] == "expected_failure_regime_validation" for row in reviews),
        "source_crosschecks": sum(row["review_class"] == "source_crosscheck_required" for row in reviews),
        "highest_primary_median_ape_asset": highest_median["asset_id"],
        "highest_primary_episode_count_asset": highest_episode_count["asset_id"],
        "highest_primary_stress_month": highest_month["month"],
    }
    (out / "stablecoin_atlas_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    findings = repo / "research" / "findings" / "stablecoin-descriptive-atlas.md"
    findings.write_text(f"""# Stablecoin Descriptive Atlas

## Coverage and primary observations

- Assets summarized: {summary['assets']} ({summary['primary_assets']} primary-model assets plus USTC as a failure control).
- Calendar months summarized: {summary['months']}.
- Highest primary-sample median absolute peg error: `{summary['highest_primary_median_ape_asset']}`.
- Most 50-bps episodes in the primary sample: `{summary['highest_primary_episode_count_asset']}`.
- Month with the most primary-sample 50-bps breach days: `{summary['highest_primary_stress_month']}`.

## Review queue

- Extreme-deviation episodes: {summary['review_queue']}.
- USTC failure-regime validation items: {summary['failure_control_reviews']}.
- Non-failure-control source crosschecks: {summary['source_crosschecks']}.

The isolated USDG observation on 2025-01-30 remains withheld from source-clean headline results. The frozen Binance snapshot contains no USDG pair, and CoinGecko's public endpoint no longer exposes that date under its 365-day limit; an archival venue or provider source is required.

These are descriptive, mechanically generated results—not causal findings. USTC is preserved in the atlas but excluded from primary-model rankings. Extreme observations are not deleted: they remain in the review queue with a proposed treatment that must be confirmed before preregistration.
""", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the stablecoin descriptive atlas and review queue"); parser.add_argument("--repo", type=Path, default=Path.cwd()); args = parser.parse_args(); print(json.dumps(run(args.repo.resolve()), indent=2))


if __name__ == "__main__": main()
