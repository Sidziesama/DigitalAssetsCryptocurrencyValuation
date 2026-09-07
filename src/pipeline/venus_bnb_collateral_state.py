from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from src.pipeline.aave_collateral_state import encode_call, post_rpc
from src.pipeline.historical import request_json, write_rows
from src.pipeline.registry import load_json, sha256


def validate(spec: dict[str, Any]) -> None:
    expected = {"schema_version":1,"chain":"bsc","asset_id":"crypto_bnb","method":"markets(address)","selector":"0x8e8f294b"}
    if any(spec.get(key) != value for key, value in expected.items()):
        raise ValueError("unsupported Venus BNB collateral-state configuration")
    for field in ("rpc_url", "block_lookup_base", "official_deployment_source", "official_method_source"):
        if not str(spec.get(field, "")).startswith("https://"):
            raise ValueError(f"invalid {field}")
    for field in ("comptroller_address", "vtoken_address"):
        if len(str(spec.get(field, ""))) != 42 or not str(spec[field]).startswith("0x"):
            raise ValueError(f"invalid {field}")


def decode_market(value: str) -> dict[str, Any]:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ValueError("invalid Venus markets response")
    words = [value[index:index + 64] for index in range(2, len(value), 64)]
    if len(words) < 2 or any(len(word) != 64 for word in words):
        raise ValueError("short Venus markets response")
    listed = int(words[0], 16)
    if listed not in (0, 1):
        raise ValueError("invalid Venus listed flag")
    factor = int(words[1], 16)
    return {"listed": listed, "collateral_factor_mantissa": factor,
            "collateral_factor": factor / 1e18,
            "collateral_enabled": int(listed == 1 and factor > 0)}


def day_timestamp(day: date) -> int:
    return int(datetime.combine(day, time(12), timezone.utc).timestamp())


def materiality_days(repo: Path, start: date, end: date) -> dict[str, int]:
    path = repo / "data/processed/evidence/crypto_collateral_daily_proxy.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row["asset_id"] == "crypto_bnb" and start.isoformat() <= row["date"] <= end.isoformat()]
    return {row["date"]: int(row["material_proxy"]) for row in rows}


def collect(repo: Path, start: date, end: date, force: bool = False) -> dict[str, Any]:
    spec = load_json(repo / "config/venus_bnb_collateral_state.json"); validate(spec)
    materiality = materiality_days(repo, start, end)
    raw_root = repo / "data/raw/venus_bnb_collateral_state" / spec["snapshot_namespace"]
    rows = []; failures = []; day = start
    while day <= end:
        raw_path = raw_root / f"{day.isoformat()}.json"
        try:
            if raw_path.exists() and not force:
                payload = load_json(raw_path)
            else:
                block_payload = request_json(f"{spec['block_lookup_base'].rstrip('/')}/{day_timestamp(day)}")
                block = int(block_payload["height"])
                rpc = {"jsonrpc":"2.0","id":"crypto_bnb","method":"eth_call","params":[{
                    "to":spec["comptroller_address"],"data":encode_call(spec["selector"],spec["vtoken_address"])},hex(block)]}
                response = post_rpc(spec["rpc_url"], rpc)
                payload = {"date":day.isoformat(),"block":block,"block_timestamp":block_payload.get("timestamp"),"response":response}
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
                raw_path.with_suffix(".metadata.json").write_text(json.dumps({
                    "provider":"bsc_json_rpc","official_deployment_source":spec["official_deployment_source"],
                    "official_method_source":spec["official_method_source"],"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),
                    "sha256":sha256(raw_path)}, indent=2) + "\n", encoding="utf-8")
            if "result" not in payload["response"]:
                raise ValueError(str(payload["response"].get("error", "missing RPC result")))
            decoded = decode_market(payload["response"]["result"])
            rows.append({"asset_id":"crypto_bnb","date":day.isoformat(),"bsc_block":payload["block"],**decoded,
                         "materiality_pass":materiality.get(day.isoformat()),
                         "classification_day_pass":int(decoded["collateral_enabled"] and materiality.get(day.isoformat()) == 1)})
        except Exception as exc:
            failures.append({"date":day.isoformat(),"error":str(exc)})
        day += timedelta(days=1)
    expected = (end - start).days + 1
    complete = len(rows) == expected and not failures and len(materiality) == expected
    pass_days = sum(row["classification_day_pass"] for row in rows)
    out = repo / "data/processed/evidence"
    write_rows(out / "venus_bnb_collateral_state_daily.csv", rows, list(rows[0]) if rows else ["asset_id"])
    result = {"status":"venus_bnb_collateral_verified_positive" if complete and pass_days == expected else "venus_bnb_collateral_incomplete",
              "asset_id":"crypto_bnb","start_date":start.isoformat(),"end_date":end.isoformat(),"expected_days":expected,
              "observed_state_days":len(rows),"materiality_days":len(materiality),"classification_pass_days":pass_days,
              "minimum_collateral_factor":min((row["collateral_factor"] for row in rows),default=None),
              "maximum_collateral_factor":max((row["collateral_factor"] for row in rows),default=None),
              "failures":failures,"recommended_va_collateral":1 if complete and pass_days == expected else None,
              "rule":spec["eligibility_rule"]}
    (out / "venus_bnb_collateral_state_summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Verify historical Venus vBNB collateral eligibility")
    parser.add_argument("--repo",type=Path,default=Path.cwd()); parser.add_argument("--start",type=date.fromisoformat,required=True)
    parser.add_argument("--end",type=date.fromisoformat,required=True); parser.add_argument("--force",action="store_true"); args=parser.parse_args()
    if args.end < args.start: parser.error("--end must be on or after --start")
    print(json.dumps(collect(args.repo.resolve(),args.start,args.end,args.force),indent=2))
