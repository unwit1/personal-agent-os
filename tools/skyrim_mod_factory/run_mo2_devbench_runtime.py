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
PM=load_module("run_presentmon_capture",HERE/"run_presentmon_capture.py")

def add_file_artifact(result:dict[str,Any],path:Path,kind:str)->None:
    if path.is_file():
        result["evidence"]["artifacts"].append({
            "kind":kind,
            "path":str(path),
            "sha256":MO2.sha256_file(path),
        })

def performance_requested(test:dict[str,Any])->bool:
    return bool(
        (test.get("evidence") or {}).get("performance")
        or any(x.get("kind")=="performance" for x in test.get("assertions") or [])
    )

def apply_presentmon_gate(
    result:dict[str,Any],
    test:dict[str,Any],
    summary:dict[str,Any]|None,
)->None:
    if not performance_requested(test):
        return
    gates={row["gate"]:row for row in result["gates"]}
    gate=gates["G20"]
    explicit=any(
        x.get("kind")=="performance" or "G20" in (x.get("gates") or [])
        for x in test.get("assertions") or []
    )
    if summary is None:
        if gate["status"]!="fail":
            gate["status"]="needs-review"
        gate["issues"].append("PresentMon performance evidence was requested but unavailable")
    else:
        pm_status=summary["status"]
        gate["evidence"].append(
            f'PresentMon frames={summary["frame_count"]} status={pm_status}'
        )
        if pm_status=="fail":
            gate["status"]="fail"
        elif pm_status=="needs-review" and gate["status"]!="fail":
            gate["status"]="needs-review"
        elif not explicit and pm_status=="pass":
            gate["status"]="pass"
            gate["issues"]=[
                x for x in gate["issues"]
                if x!="performance evidence has not been supplied"
            ]
    result["gates"]=[gates[g] for g in ("G19","G20","G21","G26")]

def validate_session_health_for_termination(
    health:dict[str,Any],
    config:dict[str,Any],
)->tuple[int,str]:
    policy=config.get("process_policy") or {}
    if not policy.get("allow_force_kill_session_game",False):
        raise ValueError("force-kill policy is disabled")
    raw_pid=health.get("pid")
    if not isinstance(raw_pid,int) or raw_pid<=0:
        raise ValueError("DevBench health did not provide a valid positive session pid")
    exe=Path(str(health.get("exe") or "")).name
    expected=[
        Path(str(x)).name.lower()
        for x in policy.get("session_game_executables") or []
        if str(x).strip()
    ]
    if not expected:
        raise ValueError(
            "force-kill requires process_policy.session_game_executables"
        )
    if exe.lower() not in expected:
        raise ValueError(
            f"DevBench session executable {exe!r} is not in allowed session game executables"
        )
    return raw_pid,exe

def force_kill_session_game(
    health:dict[str,Any],
    config:dict[str,Any],
)->dict[str,Any]:
    if os.name!="nt":
        raise ValueError("session game termination requires Windows")
    pid,exe=validate_session_health_for_termination(health,config)
    proc=subprocess.run(
        ["taskkill","/PID",str(pid),"/T","/F"],
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "pid":pid,
        "exe":exe,
        "exit_code":proc.returncode,
        "stdout":proc.stdout,
        "stderr":proc.stderr,
        "killed":proc.returncode==0,
    }

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
    crash_sources=list(evidence_cfg.get("crash_paths") or [])
    frame_sources=list(evidence_cfg.get("frame_trace_paths") or [])
    result["evidence"]["crash_delta"]=[
        row for row in captured
        if any(
            MO2.path_matches_source(row["path"],source)
            for source in crash_sources
        )
    ]
    result["evidence"]["frame_traces"]=[
        row.get("captured_path") for row in captured
        if row.get("captured_path")
        and any(
            MO2.path_matches_source(row["path"],source)
            for source in frame_sources
        )
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
    session_health=None
    launch_error=None
    force_kill_result=None
    performance_summary=None
    pm_proc=None
    pm_stdout_handle=None
    pm_stderr_handle=None
    pm_trace_path=session_dir/"presentmon.csv"
    pm_summary_path=session_dir/"presentmon-summary.json"
    pm_stdout_path=session_dir/"presentmon.stdout.log"
    pm_stderr_path=session_dir/"presentmon.stderr.log"
    with stdout_path.open("w",encoding="utf-8") as stdout, \
         stderr_path.open("w",encoding="utf-8") as stderr:
        try:
            proc=subprocess.Popen(
                result["launch"]["command"],
                stdout=stdout,
                stderr=stderr,
                text=True,
            )
            session_health=DB.wait_for_health(
                base_url,
                wait_seconds=config["timeouts"]["launch_seconds"],
                request_timeout_seconds=min(
                    5.0,
                    float(config["timeouts"]["launch_seconds"]),
                ),
            )
            health_path=session_dir/"devbench-session-health.json"
            health_path.write_text(
                json.dumps(session_health,indent=2)+"\n",
                encoding="utf-8",
            )
            add_file_artifact(result,health_path,"devbench-session-health")
            if performance_requested(test):
                perf_cfg=config.get("performance_capture")
                if perf_cfg:
                    try:
                        pm_trace_path.unlink(missing_ok=True)
                        pm_summary_path.unlink(missing_ok=True)
                        pm_stdout_handle=pm_stdout_path.open("w",encoding="utf-8")
                        pm_stderr_handle=pm_stderr_path.open("w",encoding="utf-8")
                        pm_proc=subprocess.Popen(
                            PM.build_command(
                                Path(perf_cfg["executable"]),
                                process_id=int(session_health["pid"]),
                                output_csv=pm_trace_path,
                                timed_seconds=perf_cfg.get("timed_seconds"),
                            ),
                            stdout=pm_stdout_handle,
                            stderr=pm_stderr_handle,
                            text=True,
                        )
                    except (OSError,ValueError) as exc:
                        result["issues"].append(
                            "PresentMon capture did not start: "+str(exc)
                        )
                else:
                    result["issues"].append(
                        "performance evidence requested but performance_capture is not configured"
                    )
            observation=DB.run_observer(
                test,
                result,
                base_url=base_url,
                health_wait_seconds=config["timeouts"]["launch_seconds"],
                request_timeout_seconds=config["timeouts"]["scenario_seconds"],
                evidence_dir=session_dir/"devbench",
                initial_health=session_health,
            )
        except (OSError,ValueError) as exc:
            launch_error=str(exc)
        finally:
            if session_health is not None:
                try:
                    DB.post_tool(
                        base_url,
                        "console",
                        {"action":"exec","command":"qqq"},
                        timeout_seconds=min(
                            10.0,
                            config["timeouts"]["shutdown_seconds"],
                        ),
                    )
                except ValueError as exc:
                    result["issues"].append(
                        "devbench shutdown request failed: "+str(exc)
                    )
            if proc is not None:
                try:
                    result["launch"]["exit_code"]=proc.wait(
                        timeout=config["timeouts"]["shutdown_seconds"]
                    )
                except subprocess.TimeoutExpired:
                    result["launch"]["timed_out"]=True
                    result["issues"].append(
                        "MO2/game process did not exit within shutdown timeout"
                    )
                    if (
                        session_health is not None
                        and (config.get("process_policy") or {}).get(
                            "allow_force_kill_session_game",False
                        )
                    ):
                        try:
                            force_kill_result=force_kill_session_game(
                                session_health,
                                config,
                            )
                            result["evidence"]["artifacts"].append({
                                "kind":"runtime-force-kill",
                                "pid":force_kill_result["pid"],
                                "exe":force_kill_result["exe"],
                                "exit_code":force_kill_result["exit_code"],
                                "killed":force_kill_result["killed"],
                            })
                            if force_kill_result["killed"]:
                                result["issues"].append(
                                    "session game required scoped forced termination "
                                    "after clean shutdown timeout"
                                )
                                try:
                                    result["launch"]["exit_code"]=proc.wait(timeout=5)
                                except subprocess.TimeoutExpired:
                                    pass
                            else:
                                result["issues"].append(
                                    "scoped session game force-kill command failed"
                                )
                        except ValueError as exc:
                            result["issues"].append(
                                "scoped runtime force-kill refused: "+str(exc)
                            )

    if pm_proc is not None:
        try:
            pm_exit=pm_proc.wait(timeout=config["timeouts"]["shutdown_seconds"])
        except subprocess.TimeoutExpired:
            result["issues"].append(
                "PresentMon did not exit within shutdown timeout; terminating capture process"
            )
            pm_proc.terminate()
            try:
                pm_exit=pm_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pm_proc.kill()
                pm_exit=pm_proc.wait(timeout=5)
        if pm_exit!=0:
            result["issues"].append(f"PresentMon exited with code {pm_exit}")
    if pm_stdout_handle is not None:
        pm_stdout_handle.close()
        add_file_artifact(result,pm_stdout_path,"presentmon-stdout")
    if pm_stderr_handle is not None:
        pm_stderr_handle.close()
        add_file_artifact(result,pm_stderr_path,"presentmon-stderr")
    if (
        performance_requested(test)
        and session_health is not None
        and (pm_proc is not None or pm_trace_path.is_file())
    ):
        performance_summary=PM.summarize_csv(
            pm_trace_path,
            int(session_health["pid"]),
        )
        pm_summary_path.write_text(
            json.dumps(performance_summary,indent=2)+"\n",
            encoding="utf-8",
        )
        add_file_artifact(result,pm_trace_path,"presentmon-csv")
        add_file_artifact(result,pm_summary_path,"presentmon-summary")

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

    apply_presentmon_gate(result,test,performance_summary)
    result["status"]=MERGE.overall_status(result)

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
