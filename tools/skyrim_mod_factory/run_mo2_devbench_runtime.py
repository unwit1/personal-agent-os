#!/usr/bin/env python3
"""Run one closed-loop MO2 + devbench Skyrim runtime test session.

This composes the two distinct responsibilities that the DAG executor cannot treat as
alternative adapters:
- MO2 worker: disposable profile, fixture, process boundary, filesystem evidence, cleanup.
- devbench observer: in-game event-driven actions/probes and typed assertion evidence.

The run is fail-closed. It starts only with no configured conflicting process, requires
devbench health from the launched game, asks the game to quit through devbench after the
scenario, and never upgrades stale/partial evidence to PASS.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
from pathlib import Path
from typing import Any

HERE=Path(__file__).resolve().parent

def load_module(name:str,path:Path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

MO2=load_module("run_mo2_runtime_session",HERE/"run_mo2_runtime_session.py")
DB=load_module("run_devbench_runtime_observer",HERE/"run_devbench_runtime_observer.py")
MERGE=load_module("apply_runtime_observation",HERE/"apply_runtime_observation.py")

def add_file_artifact(result:dict[str,Any],path:Path,kind:str)->None:
    if path.is_file():
        result["evidence"]["artifacts"].append({
            "kind":kind,
            "path":str(path),
            "sha256":MO2.sha256_file(path),
        })

def capture_runtime_evidence(
    result:dict[str,Any],
    config:dict[str,Any],
    before:dict[str,dict[str,Any]],
    session_dir:Path,
)->None:
    after=MO2.evidence_snapshot(config)
    delta=MO2.evidence_delta(before,after)
    captured=MO2.copy_changed_evidence(delta,session_dir)
    result["evidence"]["artifacts"].extend(captured)

    evidence_cfg=config.get("evidence") or {}
    crash_roots=[str(Path(x)) for x in evidence_cfg.get("crash_paths") or []]
    frame_roots=[str(Path(x)) for x in evidence_cfg.get("frame_trace_paths") or []]
    result["evidence"]["crash_delta"]=[
        row for row in captured
        if any(row["path"].startswith(root) for root in crash_roots)
    ]
    result["evidence"]["frame_traces"]=[
        row.get("captured_path") for row in captured
        if row.get("captured_path")
        and any(row["path"].startswith(root) for root in frame_roots)
    ]
    result["evidence"]["log_delta"]=[
        row for row in captured
        if row not in result["evidence"]["crash_delta"]
    ]

    gates={row["gate"]:row for row in result["gates"]}
    gates["G19"]=MO2.evaluate_g19(
        config,
        result["evidence"]["log_delta"],
        result["evidence"]["crash_delta"],
    )
    result["gates"]=[gates[g] for g in ("G19","G20","G21","G26")]

def run_session(
    test:dict[str,Any],
    config:dict[str,Any],
    *,
    run_id:str,
    build_id:str|None=None,
    base_url:str="http://127.0.0.1:8920",
    execute:bool=False,
)->dict[str,Any]:
    result,session_dir=MO2.prepare_session(
        test,
        config,
        run_id=run_id,
        build_id=build_id,
    )
    private_template_before=result.pop("_template_before")
    if not execute:
        MO2.validate(result,MO2.RESULT_SCHEMA,"runtime session result")
        return result

    if os.name!="nt":
        result["status"]="aborted"
        result["issues"].append("MO2 + devbench runtime execution requires Windows")
        result["_template_before"]=private_template_before
        MO2.finalize_cleanup(result,config,success=False)
        MO2.validate(result,MO2.RESULT_SCHEMA,"runtime session result")
        return result

    try:
        MO2.assert_process_exclusivity(config)
    except ValueError as exc:
        result["status"]="aborted"
        result["issues"].append(str(exc))
        result["_template_before"]=private_template_before
        MO2.finalize_cleanup(result,config,success=False)
        MO2.validate(result,MO2.RESULT_SCHEMA,"runtime session result")
        return result

    before=MO2.evidence_snapshot(config)
    stdout_path=session_dir/"mo2.stdout.log"
    stderr_path=session_dir/"mo2.stderr.log"
    result["launch"]["attempted"]=True
    result["launch"]["stdout_path"]=str(stdout_path)
    result["launch"]["stderr_path"]=str(stderr_path)
    result["started_at"]=MO2.now()

    proc=None
    observation=None
    launch_error=None
    with stdout_path.open("w",encoding="utf-8") as stdout,          stderr_path.open("w",encoding="utf-8") as stderr:
        try:
            proc=subprocess.Popen(
                result["launch"]["command"],
                stdout=stdout,
                stderr=stderr,
                text=True,
            )
            observation=DB.run_observer(
                test,
                result,
                base_url=base_url,
                health_wait_seconds=config["timeouts"]["launch_seconds"],
                request_timeout_seconds=config["timeouts"]["scenario_seconds"],
                evidence_dir=session_dir/"devbench",
            )
            try:
                DB.post_tool(
                    base_url,
                    "console",
                    {"action":"exec","command":"qqq"},
                    timeout_seconds=min(10.0,config["timeouts"]["shutdown_seconds"]),
                )
            except ValueError as exc:
                result["issues"].append(
                    "devbench shutdown request failed: "+str(exc)
                )
            try:
                result["launch"]["exit_code"]=proc.wait(
                    timeout=config["timeouts"]["shutdown_seconds"]
                )
            except subprocess.TimeoutExpired:
                result["launch"]["timed_out"]=True
                result["issues"].append(
                    "MO2/game process did not exit within shutdown timeout after scenario"
                )
        except (OSError,ValueError) as exc:
            launch_error=str(exc)

    result["finished_at"]=MO2.now()
    if proc is not None and result["launch"]["exit_code"] is None and proc.poll() is not None:
        result["launch"]["exit_code"]=proc.returncode
    if launch_error:
        result["issues"].append(launch_error)
    add_file_artifact(result,stdout_path,"mo2-stdout")
    add_file_artifact(result,stderr_path,"mo2-stderr")
    capture_runtime_evidence(result,config,before,session_dir)

    if (
        observation is not None
        and not result["launch"]["timed_out"]
        and result["launch"]["exit_code"] in (0,None)
    ):
        result=MERGE.merge_observation(result,observation)
    else:
        if result["launch"]["timed_out"] or (
            result["launch"]["exit_code"] not in (0,None)
        ):
            result["status"]="failed"
        else:
            result["status"]="needs-review"
        if observation is None:
            result["issues"].append(
                "devbench did not produce a typed runtime observation"
            )

    result["_template_before"]=private_template_before
    MO2.finalize_cleanup(
        result,
        config,
        success=result["status"]=="passed",
    )
    result["status"]=MERGE.overall_status(result)
    MO2.validate(result,MO2.RESULT_SCHEMA,"runtime session result")
    return result

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("test",type=Path)
    ap.add_argument("config",type=Path)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--build-id")
    ap.add_argument("--base-url",default="http://127.0.0.1:8920")
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()
    try:
        result=run_session(
            MO2.load(args.test),
            MO2.load(args.config),
            run_id=args.run_id,
            build_id=args.build_id,
            base_url=args.base_url,
            execute=args.execute,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(args.output)
    if result["status"]=="failed":
        raise SystemExit(2)
    if result["status"] in {"needs-review","aborted"}:
        raise SystemExit(3)

if __name__=="__main__":
    main()
