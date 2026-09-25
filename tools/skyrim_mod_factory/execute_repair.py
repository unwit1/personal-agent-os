#!/usr/bin/env python3
"""Execute only registered automatic Skyrim Mod Factory repair handlers.

Initial supported handler:
  generated-output.invalidate-and-regenerate

It never edits source artifacts. It checkpoints execution state, invalidates the
owning generator node and its downstream cached nodes, then relies on the normal
DAG executor to regenerate and revalidate those nodes.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import importlib.util
import json
import re
import shutil
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
DEFAULT_HANDLERS=REPO/"knowledge/libraries/skyrim-modding/automation/repair-handler-registry.json"

def load_module(name:str,path:Path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

EXEC=load_module("execute_build_dag",HERE/"execute_build_dag.py")
PROMOTE=load_module("promote_bug_regression",HERE/"promote_bug_regression.py")

def now()->str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def schema_errors(value:dict[str,Any],name:str)->list[str]:
    schema=load(SCHEMAS/name)
    validator=Draft202012Validator(schema)
    out=[]
    for err in sorted(validator.iter_errors(value),key=lambda e:list(e.absolute_path)):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def handler_map(registry:dict[str,Any])->dict[str,dict[str,Any]]:
    return {
        h["handler_id"]:h for h in registry.get("handlers",[])
        if isinstance(h,dict) and h.get("handler_id")
    }

def node_map(dag:dict[str,Any])->dict[str,dict[str,Any]]:
    return {n["id"]:n for n in dag.get("nodes",[])}

def downstream_closure(dag:dict[str,Any],root_id:str)->list[str]:
    nodes=node_map(dag)
    if root_id not in nodes:
        raise ValueError(f"repair target is not a DAG node: {root_id}")
    children={nid:[] for nid in nodes}
    for nid,node in nodes.items():
        for dep in node.get("depends_on",[]):
            if dep in children:
                children[dep].append(nid)
    seen=set()
    queue=[root_id]
    while queue:
        nid=queue.pop(0)
        if nid in seen:
            continue
        seen.add(nid)
        queue.extend(sorted(children.get(nid,[])))
    return [n["id"] for n in EXEC.topological_order(dag) if n["id"] in seen]

def validate_automatic_plan(
    plan:dict[str,Any],
    registry:dict[str,Any],
)->list[dict[str,Any]]:
    errors=schema_errors(plan,"skyrim-repair-plan-v1.schema.json")
    if errors:
        raise ValueError("invalid repair plan: "+"; ".join(errors))
    policy=plan.get("policy") or {}
    if policy.get("mode")!="automatic":
        raise ValueError(f"repair policy is {policy.get('mode')!r}, not automatic")
    if policy.get("reversible") is not True:
        raise ValueError("automatic repair must be reversible")
    if policy.get("postconditions_provable") is not True:
        raise ValueError("automatic repair must have provable postconditions")
    if (plan.get("rollback") or {}).get("checkpoint_required") is not True:
        raise ValueError("automatic repair must require a rollback checkpoint")

    handlers=handler_map(registry)
    resolved=[]
    actions=(plan.get("repair") or {}).get("actions") or []
    if not actions:
        raise ValueError("automatic repair plan has no actions")
    for action in actions:
        hid=action.get("handler_id")
        if not hid:
            raise ValueError(f"automatic repair action {action.get('id')} has no handler_id")
        handler=handlers.get(hid)
        if not handler:
            raise ValueError(f"repair handler is not registered: {hid}")
        if handler.get("automatic") is not True:
            raise ValueError(f"repair handler is not authorized for automatic use: {hid}")
        if handler.get("reversible") is not True or handler.get("checkpoint_required") is not True:
            raise ValueError(f"repair handler is not reversible/checkpointed: {hid}")
        resolved.append(handler)
    return resolved

def is_within(path:Path,roots:list[Path])->bool:
    resolved=path.resolve(strict=False)
    for root in roots:
        r=root.resolve(strict=False)
        if resolved==r or r in resolved.parents:
            return True
    return False

def affected_output_paths(state:dict[str,Any],invalidated:list[str])->list[Path]:
    out=[]
    seen=set()
    for nid in invalidated:
        entry=(state.get("nodes") or {}).get(nid) or {}
        for fact in entry.get("output_fingerprints") or []:
            raw=fact.get("path")
            if not raw:
                continue
            p=Path(str(raw))
            key=str(p.resolve(strict=False))
            if key not in seen:
                seen.add(key)
                out.append(p)
    return out

def backup_outputs(
    state:dict[str,Any],
    invalidated:list[str],
    *,
    backup_dir:Path,
    allowed_output_roots:list[Path],
)->list[dict[str,Any]]:
    paths=affected_output_paths(state,invalidated)
    if paths and not allowed_output_roots:
        raise ValueError(
            "automatic generated-output repair requires at least one allowed output root"
        )
    for path in paths:
        if not is_within(path,allowed_output_roots):
            raise ValueError(
                f"refusing to back up/mutate output outside allowed roots: {path}"
            )

    backups=[]
    backup_dir.mkdir(parents=True,exist_ok=True)
    for idx,path in enumerate(paths,1):
        if not path.exists():
            continue
        safe=re.sub(r"[^A-Za-z0-9_.-]+","_",path.name or f"output-{idx}")
        dest=backup_dir/f"{idx:03d}-{safe}"
        fact=EXEC.path_fingerprint(str(path))
        if path.is_file():
            shutil.copy2(path,dest)
            kind="file"
        elif path.is_dir():
            shutil.copytree(path,dest,symlinks=True)
            kind="directory"
        else:
            raise ValueError(f"unsupported generated output type: {path}")
        backups.append({
            "path":str(path),
            "backup_path":str(dest),
            "kind":kind,
            **({"sha256":fact["sha256"]} if fact.get("sha256") else {}),
            **({"size":fact["size"]} if fact.get("size") is not None else {}),
        })
    return backups

def make_checkpoint(
    plan:dict[str,Any],
    state_path:Path,
    state:dict[str,Any],
    invalidated:list[str],
    output_backups:list[dict[str,Any]]|None=None,
)->dict[str,Any]:
    return {
        "schema_version":"skyrim-repair-checkpoint-v1",
        "repair_id":plan["repair_id"],
        "project_id":plan["project_id"],
        "build_id":state.get("build_id"),
        "created_at":now(),
        "execution_state_path":str(state_path),
        "invalidated_nodes":invalidated,
        "prior_nodes":{
            nid:copy.deepcopy(state.get("nodes",{}).get(nid))
            for nid in invalidated
            if nid in state.get("nodes",{})
        },
        "output_backups":list(output_backups or []),
    }

def apply_invalidate_and_regenerate(
    plan:dict[str,Any],
    dag:dict[str,Any],
    state:dict[str,Any],
)->list[str]:
    target=(plan.get("failure") or {}).get("failing_task")
    if not target:
        raise ValueError("repair plan does not identify failure.failing_task")
    nodes=node_map(dag)
    node=nodes.get(target)
    if not node:
        raise ValueError(f"repair target is not a DAG node: {target}")
    if node.get("phase")!="generate":
        raise ValueError(
            f"generated-output repair target must be a generate-phase node, got "
            f"{target} phase={node.get('phase')!r}"
        )
    invalidated=downstream_closure(dag,target)
    for nid in invalidated:
        state.setdefault("nodes",{}).pop(nid,None)
    return invalidated

def checkpoint_expected_outputs(checkpoint:dict[str,Any])->dict[str,dict[str,Any]]:
    expected={}
    for entry in (checkpoint.get("prior_nodes") or {}).values():
        if not isinstance(entry,dict):
            continue
        for fact in entry.get("output_fingerprints") or []:
            if isinstance(fact,dict) and fact.get("path"):
                expected[str(fact["path"])]=copy.deepcopy(fact)
    return expected

def remove_output_path(path:Path)->None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)

def restore_checkpoint(
    checkpoint:dict[str,Any],
    *,
    state_path:Path,
    allowed_output_roots:list[Path]|None=None,
)->dict[str,Any]:
    errors=schema_errors(checkpoint,"skyrim-repair-checkpoint-v1.schema.json")
    if errors:
        raise ValueError("invalid repair checkpoint: "+"; ".join(errors))
    allowed=list(allowed_output_roots or [])
    expected=checkpoint_expected_outputs(checkpoint)
    backups={
        str(x["path"]):x for x in checkpoint.get("output_backups") or []
        if isinstance(x,dict) and x.get("path")
    }
    if expected and not allowed:
        raise ValueError("rollback requires at least one allowed output root")

    restored_outputs=[]
    for raw,fact in expected.items():
        path=Path(raw)
        if not is_within(path,allowed):
            raise ValueError(f"refusing to restore output outside allowed roots: {path}")
        existed=bool(fact.get("exists"))
        backup=backups.get(raw)
        if existed and not backup:
            raise ValueError(f"checkpoint has no backup for previously existing output: {path}")
        remove_output_path(path)
        if existed:
            source=Path(str(backup["backup_path"]))
            if not source.exists():
                raise ValueError(f"repair backup is missing: {source}")
            path.parent.mkdir(parents=True,exist_ok=True)
            if backup.get("kind")=="file":
                shutil.copy2(source,path)
            elif backup.get("kind")=="directory":
                shutil.copytree(source,path,symlinks=True)
            else:
                raise ValueError(f"unsupported backup kind for {path}: {backup.get('kind')}")
            restored=EXEC.path_fingerprint(str(path))
            if restored!=fact:
                raise ValueError(f"restored output fingerprint does not match checkpoint: {path}")
            restored_outputs.append({"path":str(path),"action":"restored"})
        else:
            restored_outputs.append({"path":str(path),"action":"removed"})

    state=load(state_path)
    if state.get("project_id")!=checkpoint.get("project_id"):
        raise ValueError("rollback checkpoint project_id does not match execution state")
    if checkpoint.get("build_id") and state.get("build_id")!=checkpoint.get("build_id"):
        raise ValueError("rollback checkpoint build_id does not match execution state")

    for nid in checkpoint.get("invalidated_nodes") or []:
        state.setdefault("nodes",{}).pop(nid,None)
    for nid,entry in (checkpoint.get("prior_nodes") or {}).items():
        state.setdefault("nodes",{})[nid]=copy.deepcopy(entry)
    EXEC.save_execution_state(state_path,state)
    return {
        "schema_version":"skyrim-repair-rollback-result-v1",
        "repair_id":checkpoint["repair_id"],
        "project_id":checkpoint["project_id"],
        "build_id":checkpoint.get("build_id"),
        "restored_at":now(),
        "restored_nodes":list(checkpoint.get("prior_nodes") or {}),
        "restored_outputs":restored_outputs,
    }

def assess_repair_postconditions(
    plan:dict[str,Any],
    report:dict[str,Any],
)->dict[str,Any]:
    target=(plan.get("failure") or {}).get("failing_task")
    steps={
        x.get("id"):x for x in report.get("steps") or []
        if isinstance(x,dict) and x.get("id")
    }
    target_step=steps.get(target)
    original_codes=set((plan.get("failure") or {}).get("issue_codes") or [])
    current_codes={
        code
        for step in steps.values()
        for code in (step.get("issue_codes") or [])
    }
    new_codes=sorted(current_codes-original_codes)
    reasons=[]

    if not target_step:
        reasons.append(f"rerun report does not contain repaired task: {target}")
    elif target_step.get("status")!="passed":
        reasons.append(
            f"repaired task did not pass: {target}={target_step.get('status')}"
        )

    if report.get("status")=="failed":
        reasons.append("rerun build report is failed")
    failed_gates=[
        x.get("gate") for x in report.get("gates") or []
        if isinstance(x,dict) and x.get("status")=="fail"
    ]
    if failed_gates:
        reasons.append("rerun has failed gates: "+", ".join(x for x in failed_gates if x))
    if new_codes:
        reasons.append("rerun introduced new issue codes: "+", ".join(new_codes))

    warnings=[
        x.get("gate") for x in report.get("gates") or []
        if isinstance(x,dict) and x.get("status")=="warning"
    ]
    if reasons:
        status="failed"
    elif report.get("status")!="passed" or warnings:
        status="unproven"
        if report.get("status")!="passed":
            reasons.append(f"rerun build report is {report.get('status')}")
        if warnings:
            reasons.append("rerun has warning gates: "+", ".join(x for x in warnings if x))
    else:
        status="repaired"

    return {
        "status":status,
        "target":target,
        "target_status":target_step.get("status") if target_step else None,
        "new_issue_codes":new_codes,
        "reasons":reasons,
    }

def finalize_repair(
    plan:dict[str,Any],
    report:dict[str,Any],
    *,
    checkpoint:dict[str,Any]|None=None,
    state_path:Path|None=None,
    allowed_output_roots:list[Path]|None=None,
    execute_rollback:bool=True,
    bug:dict[str,Any]|None=None,
    regression_output:Path|None=None,
)->dict[str,Any]:
    result=copy.deepcopy(plan)
    assessment=assess_repair_postconditions(result,report)
    out=result.setdefault("result",{})
    out.setdefault("evidence",[])
    out["new_issue_codes"]=assessment["new_issue_codes"]
    out["evidence"].append(
        "post-repair assessment: "+assessment["status"]
        + ("; "+"; ".join(assessment["reasons"]) if assessment["reasons"] else "")
    )

    if assessment["status"]=="repaired":
        out["status"]="repaired"
        if bug is not None:
            eligible=bool(bug.get("root_cause") and bug.get("reproduction"))
            if eligible:
                validated_bug=copy.deepcopy(bug)
                validated_bug["status"]="validated"
                fixed_by=list(validated_bug.get("fixed_by") or [])
                for action in (result.get("repair") or {}).get("actions") or []:
                    label=action.get("handler_id") or action.get("action")
                    if label and label not in fixed_by:
                        fixed_by.append(label)
                validated_bug["fixed_by"]=fixed_by
                validation=list(validated_bug.get("validation") or [])
                validation.append(
                    f"repair {result['repair_id']} rerun passed target "
                    f"{assessment.get('target')}"
                )
                validated_bug["validation"]=validation
                packet=PROMOTE.promote(validated_bug)
                destination=regression_output
                if destination is None and state_path is not None:
                    destination=(
                        state_path.parent/"regression-candidates"/
                        f"{validated_bug['bug_id']}.json"
                    )
                if destination is not None:
                    EXEC.atomic_write_json(destination,packet)
                    out["regression_promoted"]=True
                    out["evidence"].append(f"regression candidate: {destination}")
            else:
                out["evidence"].append(
                    "regression candidate not promoted: bug lacks explicit root cause "
                    "or reproduction evidence"
                )
    elif assessment["status"]=="unproven":
        out["status"]="escalated"
    elif (
        execute_rollback
        and checkpoint is not None
        and state_path is not None
        and (result.get("rollback") or {}).get("bad_fix_rollback_automatic",False)
    ):
        rollback_result=restore_checkpoint(
            checkpoint,
            state_path=state_path,
            allowed_output_roots=allowed_output_roots,
        )
        out["status"]="rolled-back"
        out["evidence"].append(
            "automatic rollback restored checkpoint for "
            +str(len(rollback_result.get("restored_nodes") or []))
            +" nodes"
        )
    else:
        out["status"]="failed"

    errors=schema_errors(result,"skyrim-repair-plan-v1.schema.json")
    if errors:
        raise ValueError("finalized repair plan failed schema validation: "+"; ".join(errors))
    return result

def execute(
    plan:dict[str,Any],
    dag:dict[str,Any],
    state:dict[str,Any],
    registry:dict[str,Any],
    *,
    state_path:Path,
    checkpoint_dir:Path,
    execute_mutation:bool,
    allowed_output_roots:list[Path]|None=None,
)->tuple[dict[str,Any],dict[str,Any]|None]:
    handlers=validate_automatic_plan(plan,registry)
    entrypoints={h["implementation"]["entrypoint"] for h in handlers}
    if entrypoints!={"invalidate_and_regenerate_generated_node"}:
        raise ValueError(
            "this executor version only supports invalidate_and_regenerate_generated_node; got "
            + ", ".join(sorted(entrypoints))
        )

    preview=copy.deepcopy(state)
    invalidated=apply_invalidate_and_regenerate(plan,dag,preview)
    result=copy.deepcopy(plan)
    result.setdefault("result",{})
    result["result"]["attempts"]=int(result["result"].get("attempts",0))+1
    result["result"].setdefault("evidence",[])
    result["result"].setdefault("new_issue_codes",[])
    result["result"].setdefault("regression_promoted",False)

    checkpoint=None
    if not execute_mutation:
        result["result"]["status"]="planned"
        result["result"]["evidence"].append(
            "dry-run: would invalidate cached nodes: "+", ".join(invalidated)
        )
        return result,None

    checkpoint_dir.mkdir(parents=True,exist_ok=True)
    safe=re.sub(r"[^A-Za-z0-9_.-]+","_",plan["repair_id"])
    stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    checkpoint_path=checkpoint_dir/f"{stamp}-{safe}.json"
    backup_dir=checkpoint_dir/f"{stamp}-{safe}.assets"
    backups=backup_outputs(
        state,
        invalidated,
        backup_dir=backup_dir,
        allowed_output_roots=list(allowed_output_roots or []),
    )
    checkpoint=make_checkpoint(
        plan,state_path,state,invalidated,output_backups=backups
    )
    cp_errors=schema_errors(checkpoint,"skyrim-repair-checkpoint-v1.schema.json")
    if cp_errors:
        raise ValueError("repair checkpoint failed schema validation: "+"; ".join(cp_errors))
    EXEC.atomic_write_json(checkpoint_path,checkpoint)

    state.clear()
    state.update(preview)
    EXEC.save_execution_state(state_path,state)

    result.setdefault("rollback",{})["checkpoint"]=str(checkpoint_path)
    result["result"]["status"]="testing"
    result["result"]["evidence"].extend([
        f"repair checkpoint: {checkpoint_path}",
        "invalidated cached nodes: "+", ".join(invalidated),
        "next action: rerun the normal DAG executor and prove repair postconditions",
    ])
    out_errors=schema_errors(result,"skyrim-repair-plan-v1.schema.json")
    if out_errors:
        raise ValueError("updated repair plan failed schema validation: "+"; ".join(out_errors))
    return result,checkpoint

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("repair_plan",type=Path)
    ap.add_argument("build_dag",type=Path)
    ap.add_argument("execution_state",type=Path)
    ap.add_argument("--handler-registry",type=Path,default=DEFAULT_HANDLERS)
    ap.add_argument("--checkpoint-dir",type=Path)
    ap.add_argument("--allowed-output-root",type=Path,action="append",default=[])
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()

    plan=load(args.repair_plan)
    dag=load(args.build_dag)
    state=load(args.execution_state)
    state_errors=schema_errors(state,"skyrim-execution-state-v1.schema.json")
    if state_errors:
        raise SystemExit("Invalid execution state:\n- "+"\n- ".join(state_errors))
    if dag.get("schema_version")!="skyrim-build-dag-v1":
        raise SystemExit("Expected skyrim-build-dag-v1")
    if dag.get("project_id")!=plan.get("project_id") or state.get("project_id")!=plan.get("project_id"):
        raise SystemExit("repair plan, DAG and execution state project_id values do not match")

    checkpoint_dir=args.checkpoint_dir or (args.execution_state.parent/"repair-checkpoints")
    try:
        updated,_=execute(
            plan,
            dag,
            state,
            load(args.handler_registry),
            state_path=args.execution_state,
            checkpoint_dir=checkpoint_dir,
            execute_mutation=args.execute,
            allowed_output_roots=args.allowed_output_root,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))

    EXEC.atomic_write_json(args.output,updated)
    print(json.dumps({
        "repair_id":updated["repair_id"],
        "status":updated.get("result",{}).get("status"),
        "checkpoint":updated.get("rollback",{}).get("checkpoint") or None,
        "output":str(args.output),
        "executed":args.execute,
    },indent=2))

if __name__=="__main__":
    main()
