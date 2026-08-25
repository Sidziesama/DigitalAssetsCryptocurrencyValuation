from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REQUIRED_ASSET_FIELDS = {
    "asset_id", "symbol", "name", "universe", "tier", "coingecko_id"
}


@dataclass(frozen=True)
class Paths:
    repo: Path
    snapshot_date: str

    @property
    def config(self) -> Path:
        return self.repo / "config" / "assets.json"

    @property
    def raw_dir(self) -> Path:
        return self.repo / "data" / "raw" / self.snapshot_date

    @property
    def processed_dir(self) -> Path:
        return self.repo / "data" / "processed" / self.snapshot_date

    @property
    def findings_dir(self) -> Path:
        return self.repo / "research" / "findings"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_asset_config(config: dict[str, Any]) -> list[dict[str, Any]]:
    if config.get("schema_version") != 1:
        raise ValueError("Unsupported asset configuration schema_version")
    assets = config.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("assets must be a non-empty list")

    seen_ids: set[str] = set()
    seen_provider_ids: set[str] = set()
    for position, asset in enumerate(assets, start=1):
        missing = REQUIRED_ASSET_FIELDS - set(asset)
        if missing:
            raise ValueError(f"asset {position} is missing fields: {sorted(missing)}")
        if asset["asset_id"] in seen_ids:
            raise ValueError(f"duplicate asset_id: {asset['asset_id']}")
        if asset["coingecko_id"] in seen_provider_ids:
            raise ValueError(f"duplicate coingecko_id: {asset['coingecko_id']}")
        if asset["universe"] not in {"crypto", "stablecoin"}:
            raise ValueError(f"invalid universe: {asset['universe']}")
        seen_ids.add(asset["asset_id"])
        seen_provider_ids.add(asset["coingecko_id"])
    return assets


def index_coingecko(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        provider_id = row.get("id")
        if provider_id:
            if provider_id in result:
                raise ValueError(f"duplicate CoinGecko id in snapshot: {provider_id}")
            result[provider_id] = row
    return result


def load_coingecko_snapshots(raw_dir: Path) -> tuple[list[dict[str, Any]], list[Path]]:
    paths = [raw_dir / "coingecko_markets.json"]
    expanded_dir = raw_dir / "expanded"
    if expanded_dir.exists():
        paths.extend(sorted(expanded_dir.glob("coingecko_*.json")))
    combined: dict[str, dict[str, Any]] = {}
    for path in paths:
        payload = load_json(path)
        if not isinstance(payload, list):
            raise ValueError(f"CoinGecko markets snapshot must be a list: {path}")
        for row in payload:
            provider_id = row.get("id")
            if provider_id:
                combined[provider_id] = row
    return list(combined.values()), paths


def index_defillama(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = payload.get("peggedAssets")
    if not isinstance(rows, list):
        raise ValueError("DeFiLlama snapshot missing peggedAssets list")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        symbol = str(row.get("symbol", "")).upper()
        if symbol and symbol not in result:
            result[symbol] = row
    return result


def numeric_present(row: dict[str, Any] | None, field: str) -> int:
    return int(row is not None and isinstance(row.get(field), (int, float)))


def build_rows(assets: list[dict[str, Any]], cg_rows: list[dict[str, Any]], llama_payload: dict[str, Any]) -> list[dict[str, Any]]:
    cg = index_coingecko(cg_rows)
    llama = index_defillama(llama_payload)
    output: list[dict[str, Any]] = []
    for asset in assets:
        cg_row = cg.get(asset["coingecko_id"])
        llama_symbol = str(asset.get("defillama_symbol", asset["symbol"])).upper()
        llama_row = llama.get(llama_symbol) if asset["universe"] == "stablecoin" else None
        circulating = (llama_row or {}).get("circulating", {}).get("peggedUSD")
        previous = (llama_row or {}).get("circulatingPrevMonth", {}).get("peggedUSD")
        month_growth = None
        if isinstance(circulating, (int, float)) and isinstance(previous, (int, float)) and previous != 0:
            month_growth = circulating / previous - 1
        required_flags = [
            numeric_present(cg_row, "market_cap"),
            numeric_present(cg_row, "total_volume"),
        ]
        if asset["universe"] == "stablecoin" and asset.get("defillama_required", True):
            required_flags.append(int(isinstance(circulating, (int, float))))
        coverage_ratio = sum(required_flags) / len(required_flags)
        output.append({
            **asset,
            "snapshot_coingecko_present": int(cg_row is not None),
            "snapshot_defillama_present": int(llama_row is not None),
            "market_cap_rank": (cg_row or {}).get("market_cap_rank"),
            "market_cap_usd": (cg_row or {}).get("market_cap"),
            "volume_24h_usd": (cg_row or {}).get("total_volume"),
            "stablecoin_supply_usd": circulating,
            "stablecoin_month_growth": month_growth,
            "required_snapshot_coverage": coverage_ratio,
            "coverage_status": "pass" if coverage_ratio == 1 else "review",
        })
    return output


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render_findings(summary: dict[str, Any]) -> str:
    review = summary["review_assets"]
    review_lines = "\n".join(f"- `{asset_id}`" for asset_id in review) or "- None"
    interpretation = (
        "The flagged observations must be resolved with an expanded provider pull or an explicitly "
        "documented alternate source. Assets must not be silently removed or replaced."
        if review else
        "All frozen-universe assets satisfy the initial cross-sectional source rule after the expanded "
        "provider lookup. This does not establish historical daily or intraday coverage."
    )
    return f"""# Snapshot Coverage Audit — {summary['snapshot_date']}

## Result

- Pilot assets: {summary['asset_count']} ({summary['crypto_count']} crypto; {summary['stablecoin_count']} stable-value).
- Initial cross-sectional coverage passes: {summary['pass_count']}.
- Review flags: {summary['review_count']}.
- Indicative combined market coverage: {summary['indicative_combined_coverage']:.2%}.

This is a source-availability audit, not a sample-exclusion decision. A review flag means at least one required field was missing from the frozen provider snapshots.

## Review queue

{review_lines}

## Interpretation

{interpretation}

## Reproducibility

The machine-readable outputs and SHA-256 hashes are stored under `data/processed/{summary['snapshot_date']}/`. Historical daily and intraday coverage remain separate validation gates.
"""


def run(repo: Path, snapshot_date: str) -> dict[str, Any]:
    paths = Paths(repo.resolve(), snapshot_date)
    config = load_json(paths.config)
    assets = validate_asset_config(config)
    cg_path = paths.raw_dir / "coingecko_markets.json"
    global_path = paths.raw_dir / "coingecko_global.json"
    llama_path = paths.raw_dir / "defillama_stablecoins.json"
    for path in (cg_path, global_path, llama_path):
        if not path.exists():
            raise FileNotFoundError(path)

    cg_rows, cg_paths = load_coingecko_snapshots(paths.raw_dir)
    global_payload = load_json(global_path)
    llama_payload = load_json(llama_path)
    total_market_cap = global_payload.get("data", {}).get("total_market_cap", {}).get("usd")
    if not isinstance(total_market_cap, (int, float)) or total_market_cap <= 0:
        raise ValueError("CoinGecko global snapshot lacks positive USD total market cap")

    rows = build_rows(assets, cg_rows, llama_payload)
    registry_fields = ["asset_id", "symbol", "name", "universe", "tier", "coingecko_id", "defillama_symbol"]
    coverage_fields = registry_fields + [
        "snapshot_coingecko_present", "snapshot_defillama_present", "market_cap_rank",
        "market_cap_usd", "volume_24h_usd", "stablecoin_supply_usd",
        "stablecoin_month_growth", "required_snapshot_coverage", "coverage_status"
    ]
    write_csv(paths.processed_dir / "identifier_registry.csv", rows, registry_fields)
    write_csv(paths.processed_dir / "snapshot_coverage.csv", rows, coverage_fields)

    selected_crypto_cap = sum((row["market_cap_usd"] or 0) for row in rows if row["universe"] == "crypto")
    selected_stable_cap = sum((row["stablecoin_supply_usd"] or 0) for row in rows if row["universe"] == "stablecoin")
    summary = {
        "schema_version": 1,
        "snapshot_date": snapshot_date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "asset_count": len(rows),
        "crypto_count": sum(row["universe"] == "crypto" for row in rows),
        "stablecoin_count": sum(row["universe"] == "stablecoin" for row in rows),
        "pass_count": sum(row["coverage_status"] == "pass" for row in rows),
        "review_count": sum(row["coverage_status"] == "review" for row in rows),
        "total_market_cap_usd": total_market_cap,
        "selected_crypto_market_cap_usd": selected_crypto_cap,
        "selected_stablecoin_supply_usd": selected_stable_cap,
        "indicative_combined_coverage": (selected_crypto_cap + selected_stable_cap) / total_market_cap,
        "raw_sha256": {
            **{str(path.relative_to(paths.raw_dir)): sha256(path) for path in cg_paths},
            global_path.name: sha256(global_path),
            llama_path.name: sha256(llama_path),
        },
        "review_assets": [row["asset_id"] for row in rows if row["coverage_status"] == "review"],
    }
    paths.processed_dir.mkdir(parents=True, exist_ok=True)
    with (paths.processed_dir / "coverage_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    paths.findings_dir.mkdir(parents=True, exist_ok=True)
    (paths.findings_dir / f"{snapshot_date}-snapshot-coverage.md").write_text(
        render_findings(summary), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build identifier registry and audit frozen snapshot coverage")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--snapshot-date", default="2026-08-22")
    args = parser.parse_args()
    print(json.dumps(run(args.repo, args.snapshot_date), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
