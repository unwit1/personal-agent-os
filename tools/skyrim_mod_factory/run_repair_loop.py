#!/usr/bin/env python3
"""Run one bounded automatic Skyrim Mod Factory repair cycle.

The loop is intentionally narrow:
failed report -> classify -> plan -> checkpoint/invalidate -> minimal DAG rerun ->
postcondition assessment -> rollback on regression -> optional regression candidate.

Unknown, proposal-only, manual, or forbidden repairs never mutate automatically.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]

def load_module(name:str,path:Path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

CLASSIFY=load_module("classify_build_failure",HERE/"classify_build_failure.py")
PLAN=load_module("plan_repair",HERE/"plan_repair.py")
REPAIR=load_module("execute_repair",HERE/"execute_repair.py")
EXEC=load_module("execute_build_dag",HERE/"execute_build_dag.py")

def load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def write(path:Path,value:dict[str,Any])->None:
    EXEC.atomic_write_json(path,value)

def executor_command(args:argparse.Namespace)->list[str]:
    cmd=[
        sys.executable,
        str(HERE/"execute_build_dag.py"),
        str(args.manifest),
        str(args.quality_plan),
        str(args.build_dag),
        "--run-dir",str(args.run_dir),
        "--execute",
    ]
    for flag,value in (
        ("--toolchain-lock",args.toolchain_lock),
        ("--context",args.context),
        ("--capabilities",args.capabilities),
        ("--adapter-dir",args.adapter_dir),
        ("--gate-registry",args.gate_registry),
        ("--state",args.state),
    ):
        if value is not None:
            cmd.extend([flag,str(value)])
    if args.git_commit:
        cmd.extend(["--git-commit",args.git_commit])
    return cmd

def persist_initial_artifacts(
    *,
    failed_report:dict[str,Any],
    bug:dict[str,Any],
    plan:dict[str,Any],
    work_dir:Path,
)->tuple[Path,Path,Path]:
    work_dir.mkdir(parents=True,exist_ok=True)
    report_path=work_dir/"original-build-report.json"
    bug_path=work_dir/"bug.json"
    plan_path=work_dir/"repair-plan.json"
    write(report_path,failed_report)
    write(bug_path,bug)
    write(plan_path,plan)
    return report_path,bug_path,plan_path

def run_cycle(args:argparse.Namespace)->dict[str,Any]:
    failed_report=load(args.failed_report)
    if failed_report.get("status")!="failed":
        raise ValueError(
            f"repair loop requires a failed build report, got {failed_report.get('status')!r}"
        )
    rule_pack=load(args.rule_pack)
    handler_registry=load(args.handler_registry)
    bug=CLASSIFY.classify(failed_report,rule_pack)
    plan=PLAN.plan(bug,rule_pack,handler_registry=handler_registry)

    work_dir=args.work_dir or (args.run_dir/"repair")
    original_path,bug_path,plan_path=persist_initial_artifacts(
        failed_report=failed_report,
        bug=bug,
        plan=plan,
        work_dir=work_dir,
    )

    summary={
        "schema_version":"skyrim-repair-loop-result-v1",
        "project_id":plan["project_id"],
        "bug_id":bug["bug_id"],
        "repair_id":plan["repair_id"],
        "policy_mode":plan["policy"]["mode"],
        "executed":False,
        "rerun_exit_code":None,
        "result_status":plan.get("result",{}).get("status","planned"),
        "original_report":str(original_path),
        "bug":str(bug_path),
        "repair_plan":str(plan_path),
    }

    if plan["policy"]["mode"]!="automatic":
        plan.setdefault("result",{})["status"]="escalated"
        plan["result"].setdefault("evidence",[]).append(
            "automatic repair loop stopped because policy mode is "
            +plan["policy"]["mode"]
        )
        write(plan_path,plan)
        summary["result_status"]="escalated"
        return summary

    state_path=args.state or (args.run_dir/"execution-state.json")
    if not state_path.exists():
        raise ValueError(f"execution state not found: {state_path}")

    state=load(state_path)
    dag=load(args.build_dag)
    active,checkpoint=REPAIR.execute(
        plan,
        dag,
        state,
        handler_registry,
        state_path=state_path,
        checkpoint_dir=work_dir/"checkpoints",
        execute_mutation=args.execute,
        allowed_output_roots=list(args.allowed_output_root or []),
    )
    write(plan_path,active)

    if not args.execute:
        summary["result_status"]=active["result"]["status"]
        return summary

    if checkpoint is None:
        raise ValueError("automatic repair execution did not create a checkpoint")

    summary["executed"]=True
    cmd=executor_command(args)
    rerun=subprocess.run(cmd,check=False)
    summary["rerun_exit_code"]=rerun.returncode

    report_path=args.run_dir/"build-report.json"
    if not report_path.exists():
        REPAIR.restore_checkpoint(
            checkpoint,
            state_path=state_path,
            allowed_output_roots=list(args.allowed_output_root or []),
        )
        active["result"]["status"]="rolled-back"
        active["result"].setdefault("evidence",[]).append(
            "executor rerun did not produce build-report.json; checkpoint restored"
        )
        write(plan_path,active)
        summary["result_status"]="rolled-back"
        return summary

    rerun_report=load(report_path)
    post_path=work_dir/"post-repair-build-report.json"
    write(post_path,rerun_report)
    summary["post_repair_report"]=str(post_path)

    finalized=REPAIR.finalize_repair(
        active,
        rerun_report,
        checkpoint=checkpoint,
        state_path=state_path,
        allowed_output_roots=list(args.allowed_output_root or []),
        execute_rollback=True,
        bug=bug,
        regression_output=work_dir/"regression-candidate.json",
    )
    write(plan_path,finalized)
    candidate=work_dir/"regression-candidate.json"
    if candidate.exists():
        summary["regression_candidate"]=str(candidate)
    summary["result_status"]=finalized["result"]["status"]
    return summary

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("failed_report",type=Path)
    ap.add_argument("manifest",type=Path)
    ap.add_argument("quality_plan",type=Path)
    ap.add_argument("build_dag",type=Path)
    ap.add_argument("--run-dir",type=Path,required=True)
    ap.add_argument("--work-dir",type=Path)
    ap.add_argument("--state",type=Path)
    ap.add_argument("--toolchain-lock",type=Path)
    ap.add_argument("--context",type=Path)
    ap.add_argument("--capabilities",type=Path)
    ap.add_argument("--adapter-dir",type=Path)
    ap.add_argument("--gate-registry",type=Path)
    ap.add_argument("--rule-pack",type=Path,default=CLASSIFY.DEFAULT_RULE_PACK)
    ap.add_argument("--handler-registry",type=Path,default=REPAIR.DEFAULT_HANDLERS)
    ap.add_argument("--allowed-output-root",type=Path,action="append",default=[])
    ap.add_argument("--git-commit")
    ap.add_argument("--execute",action="store_true")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()

    try:
        result=run_cycle(args)
    except ValueError as exc:
        raise SystemExit(str(exc))
    rendered=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered,encoding="utf-8")
    else:
        print(rendered,end="")

    if result["result_status"]=="rolled-back":
        raise SystemExit(2)
    if result["result_status"] in {"escalated","decision-required"}:
        raise SystemExit(3)

if __name__=="__main__":
    main()
