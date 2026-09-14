from __future__ import annotations

import argparse
import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from src.pipeline.aave_collateral_state import post_rpc
from src.pipeline.historical import request_json, write_rows
from src.pipeline.registry import load_json, sha256


def validate(spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("schema_version") != 1 or spec.get("universe_policy") != "fixed_existing_six_assets_no_expansion":
        raise ValueError("unsupported H4 staking-source configuration")
    source = spec.get("bnb_consensus_stake", {})
    expected = {"asset_id":"crypto_bnb","stake_hub_address":"0x0000000000000000000000000000000000002002",
                "get_validators_selector":"0xbff02e20","total_pooled_bnb_selector":"0x15d1f898"}
    if any(source.get(key) != value for key, value in expected.items()):
        raise ValueError("unexpected BNB StakeHub configuration")
    if not source.get("rpc_url", "").startswith("https://") or not source.get("block_lookup_base", "").startswith("https://"):
        raise ValueError("BNB staking collector requires HTTPS sources")
    return source


def encode_get_validators(selector: str, offset: int = 0, limit: int = 1000) -> str:
    return selector + f"{offset:064x}{limit:064x}"


def decode_get_validators(value: str) -> tuple[list[str], list[str], int]:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ValueError("invalid getValidators response")
    words = [value[index:index+64] for index in range(2, len(value), 64)]
    if len(words) < 3: raise ValueError("short getValidators response")
    def addresses(byte_offset: int) -> list[str]:
        start = byte_offset // 32
        length = int(words[start], 16)
        if start + length >= len(words): raise ValueError("truncated address array")
        return ["0x" + words[start + 1 + index][-40:] for index in range(length)]
    operators, credits, total = addresses(int(words[0], 16)), addresses(int(words[1], 16)), int(words[2], 16)
    if len(operators) != len(credits) or total < len(operators):
        raise ValueError("inconsistent validator arrays")
    return operators, credits, total


def decode_uint(value: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"): raise ValueError("invalid uint response")
    return int(value, 16)


def day_timestamp(day: date) -> int:
    return int(datetime.combine(day, time(12), timezone.utc).timestamp())


def collect(repo: Path, start: date, end: date, force: bool = False) -> dict[str, Any]:
    source = validate(load_json(repo / "config/crypto_h4_staking_sources.json"))
    raw_root = repo / "data/raw/crypto_h4_staking/bnb_stakehub"; rows=[]; failures=[]; day=start
    while day <= end:
        raw_path = raw_root / f"{day.isoformat()}.json"
        if raw_path.exists() and not force:
            payload = load_json(raw_path)
        else:
            block_payload = request_json(f"{source['block_lookup_base'].rstrip('/')}/{day_timestamp(day)}")
            block = int(block_payload["height"]); block_hex=hex(block)
            validator_call = {"jsonrpc":"2.0","id":"validators","method":"eth_call","params":[
                {"to":source["stake_hub_address"],"data":encode_get_validators(source["get_validators_selector"])},block_hex]}
            validator_response = post_rpc(source["rpc_url"], validator_call)
            if "result" not in validator_response:
                failures.append({"date":day.isoformat(),"stage":"validators","error":validator_response.get("error")}); day += timedelta(days=1); continue
            operators, credits, total = decode_get_validators(validator_response["result"])
            batch = [{"jsonrpc":"2.0","id":address,"method":"eth_call","params":[
                {"to":address,"data":source["total_pooled_bnb_selector"]},block_hex]} for address in credits]
            pool_responses = post_rpc(source["rpc_url"], batch)
            payload={"date":day.isoformat(),"block":block,"block_timestamp":block_payload.get("timestamp"),
                     "operators":operators,"credit_contracts":credits,"total_validator_count":total,
                     "pool_responses":pool_responses}
            raw_path.parent.mkdir(parents=True,exist_ok=True); raw_path.write_text(json.dumps(payload,separators=(",",":"))+"\n",encoding="utf-8")
            raw_path.with_suffix(".metadata.json").write_text(json.dumps({"provider":"bsc_json_rpc","measurement_role":source["measurement_role"],"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"sha256":sha256(raw_path)},indent=2)+"\n",encoding="utf-8")
        response_index={row.get("id"):row for row in payload["pool_responses"]}
        values=[]
        for address in payload["credit_contracts"]:
            response=response_index.get(address,{})
            if "result" in response: values.append(decode_uint(response["result"]))
        if len(values) != len(payload["credit_contracts"]):
            failures.append({"date":day.isoformat(),"stage":"credit_pools","observed":len(values),"expected":len(payload["credit_contracts"])})
        else:
            rows.append({"asset_id":"crypto_bnb","date":payload["date"],"bsc_block":payload["block"],
                         "validator_pools":len(values),"total_staked_native_units":sum(values)/1e18,
                         "measurement_role":source["measurement_role"],"provider":"bsc_json_rpc"})
        day += timedelta(days=1)
    expected=(end-start).days+1; out=repo/"data/processed/00_foundation"
    write_rows(out/"crypto_h4_bnb_stake_daily.csv",rows,["asset_id","date","bsc_block","validator_pools","total_staked_native_units","measurement_role","provider"])
    result={"status":"bnb_consensus_stake_window_complete" if len(rows)==expected else "bnb_consensus_stake_window_partial",
            "asset_id":"crypto_bnb","measurement_role":source["measurement_role"],"start_date":start.isoformat(),"end_date":end.isoformat(),
            "expected_days":expected,"observed_days":len(rows),"failures":failures,
            "minimum_staked_native_units":min((row["total_staked_native_units"] for row in rows),default=None),
            "maximum_staked_native_units":max((row["total_staked_native_units"] for row in rows),default=None),
            "unblocks_h4":len(rows)==expected,"limitation":source["limitation"]}
    path=repo/"data/processed/01_classification/crypto_h4_bnb_stake_summary.json"; path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Collect historical total BNB in StakeHub validator credit pools")
    parser.add_argument("--repo",type=Path,default=Path.cwd()); parser.add_argument("--start",type=date.fromisoformat,required=True); parser.add_argument("--end",type=date.fromisoformat,required=True); parser.add_argument("--force",action="store_true")
    args=parser.parse_args()
    if args.end<args.start: parser.error("--end must be on or after --start")
    print(json.dumps(collect(args.repo.resolve(),args.start,args.end,args.force),indent=2))
