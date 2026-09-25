#!/usr/bin/env python3
"""Execute a compiled Skyrim Mod Factory DAG conservatively and reproducibly.

This is the first orchestration layer above run_adapter.py. It:
- topologically executes DAG nodes;
- validates core preflight artifacts;
- resolves adapter manifests from the capability registry;
- injects pinned executables from the toolchain lock;
- merges typed global/adapter/node execution variables;
- retries only when an adapter explicitly marks retry safe;
- blocks downstream work on failures;
- never treats GUI/library/unconfigured adapters as successful;
- emits a schema-valid skyrim-mod-build-report-v1 report.

Safety:
- dry-run by default;
- --execute is required to launch external tools;
- output cleanup is never performed unless a later implementation explicitly
  proves scope and the execution context opts in.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import re
import uuid
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
DEFAULT_CAPABILITIES=REPO/"knowledge/libraries/skyrim-modding/automation/tool-capability-registry.json"
DEFAULT_ADAPTER_DIR=REPO/"knowledge/libraries/skyrim-modding/automation/adapters"
DEFAULT_GATE_REGISTRY=REPO/"knowledge/libraries/skyrim-modding/automation/validation-gate-registry.json"
SCHEMAS=REPO/"schemas"

def load_module(name:str, path:Path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

RUN=load_module("run_adapter",HERE/"run_adapter.py")
DOCTOR=load_module("doctor_toolchain",HERE/"doctor_toolchain.py")
GATES=load_module("evaluate_gates",HERE/"evaluate_gates.py")

def now()->str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def load_json(path:Path|None)->dict[str,Any]:
    return {} if path is None else json.loads(path.read_text(encoding="utf-8"))

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def schema_errors(instance:dict[str,Any], schema_name:str)->list[str]:
    schema=load_json(SCHEMAS/schema_name)
    validator=Draft202012Validator(schema)
    out=[]
    for err in sorted(validator.iter_errors(instance),key=lambda e:list(e.absolute_path)):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def topological_order(dag:dict[str,Any])->list[dict[str,Any]]:
    nodes={n["id"]:n for n in dag.get("nodes",[])}
    indegree={nid:0 for nid in nodes}
    children={nid:[] for nid in nodes}
    for nid,node in nodes.items():
        for dep in node.get("depends_on",[]):
            if dep not in nodes:
                raise ValueError(f"{nid} depends on missing node {dep}")
            indegree[nid]+=1
            children[dep].append(nid)
    ready=[nid for nid,v in indegree.items() if v==0]
    order=[]
    while ready:
        ready.sort()
        nid=ready.pop(0)
        order.append(nodes[nid])
        for child in sorted(children[nid]):
            indegree[child]-=1
            if indegree[child]==0:
                ready.append(child)
    if len(order)!=len(nodes):
        raise ValueError("build DAG contains a cycle")
    return order

def load_capability_map(path:Path)->dict[str,dict[str,Any]]:
    data=load_json(path)
    return {
        x["adapter_id"]:x for x in data.get("adapters",[])
        if isinstance(x,dict) and x.get("adapter_id")
    }

def load_adapter_manifest(
    adapter_id:str,
    capability_map:dict[str,dict[str,Any]],
    adapter_dir:Path,
)->tuple[dict[str,Any]|None,str]:
    entry=capability_map.get(adapter_id) or {}
    rel=entry.get("adapter_manifest")
    candidates=[]
    if rel:
        p=Path(rel)
        candidates.append(p if p.is_absolute() else REPO/p)
    candidates.append(adapter_dir/f"{adapter_id}.json")
    for path in candidates:
        if not path.exists():
            continue
        data=load_json(path)
        if data.get("adapter_id")==adapter_id:
            return data,str(path)
    return None,""

def lock_map(lock:dict[str,Any])->dict[str,dict[str,Any]]:
    return {
        x["adapter_id"]:x for x in lock.get("adapters",[])
        if isinstance(x,dict) and x.get("adapter_id")
    }

def hydrate_adapter(adapter:dict[str,Any], lock_entry:dict[str,Any]|None)->dict[str,Any]:
    out=copy.deepcopy(adapter)
    if not lock_entry:
        return out
    if lock_entry.get("version") and not out.get("tool_version"):
        out["tool_version"]=lock_entry["version"]
    inv=out.setdefault("invocation",{})
    if lock_entry.get("executable"):
        inv["executable"]=lock_entry["executable"]
    if lock_entry.get("endpoint"):
        inv.setdefault("endpoint",lock_entry["endpoint"])
    return out

def base_variables(lock:dict[str,Any], context:dict[str,Any])->dict[str,str]:
    out={}
    runtime=lock.get("runtime") or {}
    for k,v in runtime.items():
        if isinstance(v,(str,int,float,bool)):
            out[k]=str(v)
    host=lock.get("host") or {}
    for k,v in host.items():
        if isinstance(v,(str,int,float,bool)):
            out.setdefault(k,str(v))
    for k,v in (context.get("variables") or {}).items():
        out[k]=str(v)
    aliases={
        "data":"data_root",
        "data_dir":"data_root",
        "game_path":"game_root",
        "instance":"mo2_instance",
        "profile":"mo2_profile",
    }
    for alias,source in aliases.items():
        if source in out and alias not in out:
            out[alias]=out[source]
    return out

def node_io(
    node:dict[str,Any],
    context:dict[str,Any],
    adapter_id:str|None=None,
)->tuple[list[str],list[str],dict[str,str]]:
    ncfg=(context.get("nodes") or {}).get(node["id"],{}) or {}
    acfg=((context.get("adapters") or {}).get(adapter_id,{}) or {}) if adapter_id else {}
    inputs=list(ncfg.get("inputs") or acfg.get("inputs") or [])
    outputs=list(ncfg.get("outputs") or acfg.get("outputs") or node.get("outputs") or [])
    variables={}
    variables.update({k:str(v) for k,v in (acfg.get("variables") or {}).items()})
    variables.update({k:str(v) for k,v in (ncfg.get("variables") or {}).items()})
    if outputs:
        variables.setdefault("output",outputs[0])
        variables.setdefault("output_path",outputs[0])
    return inputs,outputs,variables

def simple_step(node:dict[str,Any],status:str,issues:list[str]|None=None,**extra)->dict[str,Any]:
    row={
        "id":node["id"],
        "status":status,
        "started_at":now(),
        "finished_at":now(),
        "issues":issues or [],
    }
    row.update(extra)
    return row

def preflight_step(
    node:dict[str,Any],
    *,
    manifest:dict[str,Any],
    quality:dict[str,Any],
    lock:dict[str,Any],
    context:dict[str,Any],
)->dict[str,Any]|None:
    nid=node["id"]
    if nid=="preflight.manifest":
        errs=schema_errors(manifest,"skyrim-mod-project-v1.schema.json")
        return simple_step(node,"failed" if errs else "passed",errs)
    if nid=="preflight.quality":
        errs=schema_errors(quality,"skyrim-quality-plan-v1.schema.json")
        return simple_step(node,"failed" if errs else "passed",errs)
    if nid=="preflight.dependencies":
        dep_path=manifest.get("dependency_lock")
        if not dep_path:
            return simple_step(node,"passed",[])
        p=Path(dep_path)
        if not p.is_absolute():
            base=Path(context.get("manifest_dir") or ".")
            p=(base/p).resolve()
        if not p.exists():
            return simple_step(node,"failed",[f"dependency lock not found: {p}"])
        return simple_step(
            node,"passed",[],
            inputs=[RUN.file_fact(str(p))]
        )
    if nid=="preflight.toolchain":
        if not lock:
            return simple_step(node,"needs-review",["toolchain lock was not supplied"])
        result=DOCTOR.audit(lock,quality,manifest,check_files=True)
        status="failed" if result.get("status")=="fail" else "passed"
        issues=[f"{x.get('code')}: {x.get('message')}" for x in result.get("issues",[])]
        return simple_step(node,status,issues,evidence={"toolchain_doctor":result})
    if nid=="source.lock":
        paths=[str(x) for x in context.get("source_paths") or []]
        facts=[RUN.file_fact(x) for x in paths]
        missing=[x["path"] for x in facts if not x.get("exists")]
        return simple_step(
            node,
            "failed" if missing else "passed",
            [f"source path missing: {x}" for x in missing],
            inputs=facts,
            evidence={"source_count":len(facts)}
        )
    return None

def adapter_candidates(node:dict[str,Any],context:dict[str,Any])->list[str]:
    override=((context.get("nodes") or {}).get(node["id"],{}) or {}).get("adapter_order")
    return list(override or node.get("adapters") or [])

def execute_adapter_node(
    node:dict[str,Any],
    *,
    capability_map:dict[str,dict[str,Any]],
    adapter_dir:Path,
    lock:dict[str,Any],
    context:dict[str,Any],
    log_dir:Path,
    execute:bool,
)->dict[str,Any]:
    locks=lock_map(lock)
    base=base_variables(lock,context)
    reasons=[]
    policy=context.get("policy") or {}
    allow_retry=policy.get("allow_safe_retry",True)
    cap=int(policy.get("max_attempts_cap",3))

    for aid in adapter_candidates(node,context):
        acfg=((context.get("adapters") or {}).get(aid,{}) or {})
        if acfg.get("enabled") is False:
            reasons.append(f"{aid}: disabled by execution context")
            continue
        manifest,source=load_adapter_manifest(aid,capability_map,adapter_dir)
        if not manifest:
            reasons.append(f"{aid}: no executable adapter manifest")
            continue
        manifest=hydrate_adapter(manifest,locks.get(aid))
        inputs,outputs,specific=node_io(node,context,aid)
        variables=dict(base)
        variables.update(specific)
        try:
            RUN.build_invocation(manifest,variables)
        except ValueError as ex:
            reasons.append(f"{aid}: {ex}")
            continue

        retry=manifest.get("retry") or {}
        max_attempts=max(1,min(int(retry.get("max_attempts",1)),cap))
        if not allow_retry or not retry.get("safe",False):
            max_attempts=1
        if retry.get("cleanup_outputs_first",False) and not policy.get("allow_cleanup_outputs",False):
            max_attempts=1

        attempts=[]
        for attempt in range(1,max_attempts+1):
            record=RUN.run_adapter(
                manifest,
                adapter_id=aid,
                variables=variables,
                inputs=inputs,
                outputs=outputs,
                log_dir=log_dir,
                execute=execute,
                record_id=node["id"],
            )
            attempts.append({
                "attempt":attempt,
                "status":record.get("status"),
                "stdout_path":record.get("stdout_path"),
                "stderr_path":record.get("stderr_path"),
                "exit_code":record.get("exit_code"),
            })
            if record.get("status")!="failed":
                record.setdefault("evidence",{})
                record["evidence"]["adapter_manifest"]=source
                record["evidence"]["attempts"]=attempts
                return record
        record.setdefault("evidence",{})
        record["evidence"]["adapter_manifest"]=source
        record["evidence"]["attempts"]=attempts
        return record

    return simple_step(
        node,
        "needs-review",
        reasons or ["node declares no executable adapter"],
    )

def gate_evaluation_step(
    node:dict[str,Any],
    *,
    gate_registry:dict[str,Any],
    quality:dict[str,Any],
    dag:dict[str,Any],
    completed_steps:list[dict[str,Any]],
)->dict[str,Any]:
    partial_report={
        "schema_version":"skyrim-mod-build-report-v1",
        "project_id":dag.get("project_id"),
        "build_id":"partial",
        "started_at":now(),
        "status":"running",
        "steps":completed_steps,
        "gates":[],
    }
    result=GATES.evaluate(
        gate_registry,quality,dag,partial_report,through_phase="integrate"
    )
    status={
        "passed":"passed",
        "failed":"failed",
        "needs-review":"needs-review",
    }[result["status"]]
    return simple_step(
        node,status,
        list(result.get("blockers") or []),
        evidence={"gate_evaluation":result},
    )

def blocked_by_dependencies(node:dict[str,Any],steps:dict[str,dict[str,Any]],continue_review:bool)->list[str]:
    blocked=[]
    for dep in node.get("depends_on",[]):
        status=(steps.get(dep) or {}).get("status")
        if status=="failed":
            blocked.append(f"{dep}=failed")
        elif status=="needs-review" and not continue_review:
            blocked.append(f"{dep}=needs-review")
    return blocked

def validate_report(report:dict[str,Any])->list[str]:
    return schema_errors(report,"skyrim-mod-build-report-v1.schema.json")

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("quality_plan",type=Path)
    ap.add_argument("build_dag",type=Path)
    ap.add_argument("--toolchain-lock",type=Path)
    ap.add_argument("--context",type=Path)
    ap.add_argument("--capabilities",type=Path,default=DEFAULT_CAPABILITIES)
    ap.add_argument("--adapter-dir",type=Path,default=DEFAULT_ADAPTER_DIR)
    ap.add_argument("--gate-registry",type=Path,default=DEFAULT_GATE_REGISTRY)
    ap.add_argument("--run-dir",type=Path,required=True)
    ap.add_argument("--report",type=Path)
    ap.add_argument("--git-commit")
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()

    manifest=load_json(args.manifest)
    quality=load_json(args.quality_plan)
    dag=load_json(args.build_dag)
    lock=load_json(args.toolchain_lock)
    context=load_json(args.context)
    context.setdefault("manifest_dir",str(args.manifest.parent.resolve()))

    if context and context.get("schema_version"):
        errs=schema_errors(context,"skyrim-execution-context-v1.schema.json")
        if errs:
            raise SystemExit("Invalid execution context:\n- "+"\n- ".join(errs))

    if dag.get("schema_version")!="skyrim-build-dag-v1":
        raise SystemExit("Expected skyrim-build-dag-v1")
    if dag.get("project_id")!=manifest.get("project_id"):
        raise SystemExit("DAG project_id does not match manifest")
    if context.get("project_id") and context.get("project_id")!=manifest.get("project_id"):
        raise SystemExit("Execution context project_id does not match manifest")

    args.run_dir.mkdir(parents=True,exist_ok=True)
    step_dir=args.run_dir/"steps"
    log_dir=args.run_dir/"logs"
    step_dir.mkdir(parents=True,exist_ok=True)
    log_dir.mkdir(parents=True,exist_ok=True)
    report_path=args.report or (args.run_dir/"build-report.json")

    capability_map=load_capability_map(args.capabilities)\n    gate_registry=load_json(args.gate_registry)
    ordered=topological_order(dag)
    policy=context.get("policy") or {}
    stop_on_failure=policy.get("stop_on_failure",True)
    continue_review=policy.get("continue_on_needs_review",False)

    started=now()
    steps_by_id={}
    agent_actions=[]
    hard_stop=False

    for node in ordered:
        if hard_stop:
            step=simple_step(node,"skipped",["execution stopped after prior failure"])
        else:
            blocked=blocked_by_dependencies(node,steps_by_id,continue_review)
            if blocked:
                step=simple_step(node,"skipped",["blocked by dependency: "+", ".join(blocked)])
            else:
                step=preflight_step(
                    node,manifest=manifest,quality=quality,lock=lock,context=context
                )
                if step is None:
                    if node.get("id")=="integrate.gates":
                        step=gate_evaluation_step(
                            node,
                            gate_registry=gate_registry,
                            quality=quality,
                            dag=dag,
                            completed_steps=[steps_by_id[n["id"]] for n in ordered if n["id"] in steps_by_id],
                        )
                    elif node.get("adapters"):
                        step=execute_adapter_node(
                            node,
                            capability_map=capability_map,
                            adapter_dir=args.adapter_dir,
                            lock=lock,
                            context=context,
                            log_dir=log_dir,
                            execute=args.execute,
                        )
                    else:
                        step=simple_step(
                            node,
                            "needs-review",
                            ["no built-in handler or executable adapter is defined for this node"],
                        )
            if step.get("status")=="failed" and stop_on_failure:
                hard_stop=True

        steps_by_id[node["id"]]=step
        safe=re.sub(r"[^A-Za-z0-9_.-]+","_",node["id"])
        (step_dir/f"{safe}.json").write_text(json.dumps(step,indent=2)+"\n",encoding="utf-8")
        if step.get("adapter_id"):
            agent_actions.append({
                "adapter_id":step["adapter_id"],
                "action":node.get("action",""),
                "dry_run":bool(step.get("dry_run",not args.execute)),
                "mutated":bool(args.execute and node.get("phase") in {"generate","integrate","package"}),
                "readback_verified":bool(step.get("status")=="passed" and step.get("outputs_after") is not None),
                "evidence":[x for x in [step.get("stdout_path"),step.get("stderr_path")] if x],
            })

    steps=[steps_by_id[n["id"]] for n in ordered]
    statuses=[s.get("status") for s in steps]

    report={
        "schema_version":"skyrim-mod-build-report-v1",
        "project_id":manifest.get("project_id"),
        "build_id":str(uuid.uuid4()),
        "git_commit":args.git_commit,
        "manifest_sha256":sha256(args.manifest),
        "started_at":started,
        "finished_at":now(),
        "status":"running",
        "runtime_context":{
            k:v for k,v in (lock.get("runtime") or {}).items()
            if isinstance(v,(str,int,float,bool)) or v is None
        },
        "steps":steps,
        "gates":[],
        "artifacts":[],
        "known_issues":[
            issue for step in steps for issue in step.get("issues",[])
            if step.get("status") in {"failed","needs-review"}
        ],
        "human_checks_remaining":list(quality.get("human_checks") or []),
        "agent_actions":agent_actions,
    }
    # Evaluate the final authoritative gate state after all available phases.
    gate_result=GATES.evaluate(
        gate_registry,quality,dag,report,through_phase="release"
    )
    report["gates"]=gate_result["gates"]
    if "failed" in statuses or gate_result["status"]=="failed":
        final="failed"
    elif "needs-review" in statuses or not args.execute or gate_result["status"]=="needs-review":
        final="needs-review"
    else:
        final="passed"
    report["status"]=final

    # Remove optional null forbidden-by-schema fields.
    if report.get("git_commit") is None:
        report.pop("git_commit",None)

    errors=validate_report(report)
    if errors:
        failure={
            "schema_version":"skyrim-executor-schema-failure-v1",
            "errors":errors,
            "report":report,
        }
        (args.run_dir/"invalid-build-report.json").write_text(
            json.dumps(failure,indent=2)+"\n",encoding="utf-8"
        )
        raise SystemExit("Generated build report failed schema validation:\n- "+"\n- ".join(errors))

    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "project_id":report["project_id"],
        "build_id":report["build_id"],
        "status":report["status"],
        "steps_total":len(steps),
        "passed":sum(x=="passed" for x in statuses),
        "failed":sum(x=="failed" for x in statuses),
        "needs_review":sum(x=="needs-review" for x in statuses),
        "skipped":sum(x=="skipped" for x in statuses),
        "report":str(report_path),
    },indent=2))

    if final=="failed":
        raise SystemExit(2)
    if final=="needs-review":
        raise SystemExit(3)

if __name__=="__main__":
    main()
