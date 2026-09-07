from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

EXCLUDED_MODULES = {"__init__", "run_stages"}


def load(repo: Path) -> dict[str, Any]:
    return json.loads((repo / "config/pipeline_stages.json").read_text(encoding="utf-8"))


def validate(spec: dict[str, Any], repo: Path) -> None:
    if spec.get("schema_version") != 1 or not spec.get("stages"):
        raise ValueError("unsupported pipeline stage specification")
    seen: dict[str, str] = {}
    ids = [stage["id"] for stage in spec["stages"]]
    if len(ids) != len(set(ids)):
        raise ValueError("stage identifiers must be unique")
    for stage in spec["stages"]:
        if "network" not in stage or not stage.get("commands"):
            raise ValueError(f"stage {stage['id']} needs a network flag and commands")
        for command in stage["commands"]:
            module = command["module"]
            if module in seen:
                raise ValueError(f"module {module} appears in both {seen[module]} and {stage['id']}")
            seen[module] = stage["id"]
            if not (repo / "src/pipeline" / f"{module}.py").exists():
                raise ValueError(f"stage {stage['id']} references missing module {module}")
    present = {path.stem for path in (repo / "src/pipeline").glob("*.py")} - EXCLUDED_MODULES
    unmapped = sorted(present - set(seen))
    if unmapped:
        raise ValueError(f"pipeline modules missing from the stage map: {unmapped}")


def plan(spec: dict[str, Any], stage_ids: list[str], repo: Path) -> list[dict[str, Any]]:
    wanted = {stage["id"]: stage for stage in spec["stages"]}
    unknown = [s for s in stage_ids if s not in wanted]
    if unknown:
        raise ValueError(f"unknown stages {unknown}; available: {list(wanted)}")
    steps = []
    for stage_id in stage_ids:
        for command in wanted[stage_id]["commands"]:
            missing = [name for name in command.get("requires_env", []) if not os.environ.get(name)]
            steps.append({"stage": stage_id, "module": command["module"],
                          "argv": [sys.executable, "-m", f"src.pipeline.{command['module']}", "--repo", str(repo), *command["args"]],
                          "skip_reason": f"missing environment {missing}" if missing else None})
    return steps


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pipeline stages in their frozen order")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--stage", action="append", help="stage id; repeatable")
    parser.add_argument("--offline", action="store_true", help="run every stage that needs no network, in order")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    spec = load(repo)
    validate(spec, repo)
    if args.list:
        for stage in spec["stages"]:
            print(f"{stage['id']:24s} network={str(stage['network']).lower():5s} {len(stage['commands']):3d} commands  {stage['title']}")
        return
    stage_ids = args.stage or ([s["id"] for s in spec["stages"] if not s["network"]] if args.offline else [])
    if not stage_ids:
        parser.error("choose --stage, --offline, or --list")
    for step in plan(spec, stage_ids, repo):
        label = f"[{step['stage']}] {step['module']}"
        if step["skip_reason"]:
            print(f"SKIP {label}: {step['skip_reason']}")
            continue
        print(f"RUN  {label}")
        if args.dry_run:
            continue
        result = subprocess.run(step["argv"], cwd=repo, stdout=subprocess.DEVNULL)
        if result.returncode != 0:
            raise SystemExit(f"stage {step['stage']} failed at {step['module']} (exit {result.returncode})")


if __name__ == "__main__":
    main()
