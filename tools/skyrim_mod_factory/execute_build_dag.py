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
DEFAULT_REPAIR_RULE_PACK=REPO/"knowledge/libraries/skyrim-modding/automation/analyzer-rule-pack-core.json"
DEFAULT_REPAIR_HANDLERS=REPO/"knowledge/libraries/skyrim-modding/automation/repair-handler-registry.json"
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

def canonical_json_sha256(value:Any)->str:
    payload=json.dumps(
        value,
        sort_keys=True,
        separators=(",",":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def path_fingerprint(path_text:str)->dict[str,Any]:
    """Return a deterministic content fingerprint for a file, directory, or missing path."""
    path=Path(path_text)
    base={"path":str(path),"exists":path.exists()}
    if not path.exists():
        return {**base,"kind":"missing"}

    if path.is_file():
        stat=path.stat()
        return {
            **base,
            "kind":"file",
            "size":stat.st_size,
            "sha256":sha256(path),
        }

    if path.is_dir():
        rows=[]
        total_size=0
        file_count=0
        for child in sorted(path.rglob("*"),key=lambda p:p.relative_to(path).as_posix()):
            rel=child.relative_to(path).as_posix()
            if child.is_dir():
                rows.append({"path":rel,"kind":"directory"})
                continue
            if child.is_file():
                stat=child.stat()
                digest=sha256(child)
                total_size+=stat.st_size
                file_count+=1
                rows.append({
                    "path":rel,
                    "kind":"file",
                    "size":stat.st_size,
                    "sha256":digest,
                })
        return {
            **base,
            "kind":"directory",
            "file_count":file_count,
            "size":total_size,
            "sha256":canonical_json_sha256(rows),
        }

    return {**base,"kind":"missing","exists":False}

def atomic_write_json(path:Path,value:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    tmp.write_text(json.dumps(value,indent=2)+"\n",encoding="utf-8")
    tmp.replace(path)

def new_execution_state(project_id:str,build_id:str|None=None)->dict[str,Any]:
    return {
        "schema_version":"skyrim-execution-state-v1",
        "project_id":project_id,
        "build_id":build_id or str(uuid.uuid4()),
        "updated_at":now(),
        "nodes":{},
    }

def load_execution_state(path:Path,project_id:str)->dict[str,Any]:
    if not path.exists():
        return new_execution_state(project_id)
    state=load_json(path)
    errs=schema_errors(state,"skyrim-execution-state-v1.schema.json")
    if errs:
        raise ValueError("invalid execution state: "+"; ".join(errs))
    if state.get("project_id")!=project_id:
        raise ValueError(
            f"execution state project_id {state.get('project_id')!r} does not match {project_id!r}"
        )
    return state

def save_execution_state(path:Path,state:dict[str,Any])->None:
    state=copy.deepcopy(state)
    state["updated_at"]=now()
    errs=schema_errors(state,"skyrim-execution-state-v1.schema.json")
    if errs:
        raise ValueError("execution state failed schema validation: "+"; ".join(errs))
    atomic_write_json(path,state)

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

def validate_artifact_contracts(
    node:dict[str,Any],
    context:dict[str,Any],
)->list[dict[str,Any]]:
    """Validate declared intermediate artifacts after a successful node."""
    ncfg=(context.get("nodes") or {}).get(node["id"],{}) or {}
    rows=[]
    for contract in ncfg.get("artifact_contracts") or []:
        path=Path(str(contract["path"]))
        required=contract.get("required",True)
        row={
            "artifact":str(path),
            "validator":contract["validator"],
            "status":"pass",
            "issues":[],
        }
        if not path.exists():
            row["status"]="fail" if required else "not-applicable"
            if required:
                row["issues"].append("required artifact does not exist")
            rows.append(row)
            continue
        if contract["validator"]=="json-schema":
            schema_name=contract.get("schema")
            schema_path=SCHEMAS/str(schema_name)
            if not schema_name or not schema_path.is_file():
                row["status"]="fail"
                row["issues"].append(f"schema is unavailable: {schema_name}")
                rows.append(row)
                continue
            try:
                value=json.loads(path.read_text(encoding="utf-8"))
            except (OSError,UnicodeError,json.JSONDecodeError) as exc:
                row["status"]="fail"
                row["issues"].append(f"artifact is not valid UTF-8 JSON: {exc}")
                rows.append(row)
                continue
            row["issues"].extend(schema_errors(value,str(schema_name)))
            if row["issues"]:
                row["status"]="fail"
        rows.append(row)
    return rows

def enforce_artifact_contracts(
    step:dict[str,Any],
    node:dict[str,Any],
    context:dict[str,Any],
)->dict[str,Any]:
    if step.get("status")!="passed":
        return step
    checks=validate_artifact_contracts(node,context)
    if not checks:
        return step
    step=copy.deepcopy(step)
    step.setdefault("evidence",{})["artifact_contracts"]=checks
    failures=[x for x in checks if x["status"]=="fail"]
    if failures:
        step["status"]="failed"
        issues=step.setdefault("issues",[])
        for row in failures:
            detail="; ".join(row.get("issues") or ["validation failed"])
            issues.append(
                f"artifact contract failed for {row['artifact']} via {row['validator']}: {detail}"
            )
    return step

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

def node_external_facts(
    node:dict[str,Any],
    *,
    manifest:dict[str,Any],
    quality:dict[str,Any],
    lock:dict[str,Any],
    context:dict[str,Any],
    capability_map:dict[str,dict[str,Any]],
    adapter_dir:Path,
    gate_registry:dict[str,Any],
)->dict[str,Any]:
    """Return only external/config facts that can change this node's result."""
    facts:dict[str,Any]={}
    nid=node["id"]

    if nid=="preflight.manifest":
        facts["manifest"]=manifest
    if nid=="preflight.quality":
        facts["quality"]=quality
    if nid=="preflight.toolchain":
        facts["toolchain_lock"]=lock
    if nid=="integrate.gates":
        facts["gate_registry"]=gate_registry
        facts["quality"]=quality

    if nid=="preflight.dependencies" and manifest.get("dependency_lock"):
        p=Path(str(manifest["dependency_lock"]))
        if not p.is_absolute():
            p=(Path(context.get("manifest_dir") or ".")/p).resolve()
        facts["dependency_lock"]=path_fingerprint(str(p))

    if nid=="source.lock":
        facts["source_paths"]=[
            path_fingerprint(str(x)) for x in context.get("source_paths") or []
        ]

    ncfg=(context.get("nodes") or {}).get(nid,{}) or {}
    facts["node_context"]=ncfg

    input_paths=[]
    input_paths.extend(str(x) for x in ncfg.get("inputs") or [])
    locks=lock_map(lock)
    adapter_facts={}
    for aid in adapter_candidates(node,context):
        acfg=((context.get("adapters") or {}).get(aid,{}) or {})
        input_paths.extend(str(x) for x in acfg.get("inputs") or [])
        manifest_data,source=load_adapter_manifest(aid,capability_map,adapter_dir)
        lock_entry=locks.get(aid)
        afact:dict[str,Any]={
            "context":acfg,
            "lock":lock_entry,
            "manifest_source":source or None,
        }
        if source:
            afact["manifest_file"]=path_fingerprint(source)
        executable=(lock_entry or {}).get("executable")
        if executable:
            afact["executable"]=path_fingerprint(str(executable))
        adapter_facts[aid]=afact
    if adapter_facts:
        facts["adapters"]=adapter_facts

    if input_paths:
        facts["inputs"]=[
            path_fingerprint(x) for x in sorted(set(input_paths))
        ]
    return facts

def compute_node_fingerprint(
    node:dict[str,Any],
    *,
    manifest:dict[str,Any],
    quality:dict[str,Any],
    lock:dict[str,Any],
    context:dict[str,Any],
    capability_map:dict[str,dict[str,Any]],
    adapter_dir:Path,
    gate_registry:dict[str,Any],
    dependency_fingerprints:dict[str,str],
)->str:
    payload={
        "node":node,
        "dependencies":{
            dep:dependency_fingerprints.get(dep)
            for dep in node.get("depends_on",[])
        },
        "external":node_external_facts(
            node,
            manifest=manifest,
            quality=quality,
            lock=lock,
            context=context,
            capability_map=capability_map,
            adapter_dir=adapter_dir,
            gate_registry=gate_registry,
        ),
    }
    return canonical_json_sha256(payload)

def current_output_fingerprints(
    node:dict[str,Any],
    context:dict[str,Any],
    adapter_id:str|None=None,
)->list[dict[str,Any]]:
    _,outputs,_=node_io(node,context,adapter_id)
    return [path_fingerprint(str(x)) for x in outputs]

def output_fingerprints_match(saved:list[dict[str,Any]])->bool:
    for expected in saved:
        path=expected.get("path")
        if not path:
            return False
        if path_fingerprint(str(path))!=expected:
            return False
    return True

def reusable_prior_step(
    node:dict[str,Any],
    fingerprint:str,
    state:dict[str,Any],
)->dict[str,Any]|None:
    prior=(state.get("nodes") or {}).get(node["id"])
    if not prior or prior.get("status")!="passed":
        return None
    if prior.get("fingerprint")!=fingerprint:
        return None
    if not output_fingerprints_match(prior.get("output_fingerprints") or []):
        return None

    step=copy.deepcopy(prior.get("step_record") or {})
    if not step:
        return None
    step["id"]=node["id"]
    step["status"]="passed"
    step.setdefault("evidence",{})
    step["evidence"]["resumed_from_state"]=True
    step["evidence"]["resume_fingerprint"]=fingerprint
    step["evidence"]["resumed_at"]=now()
    return step

def checkpoint_node(
    state:dict[str,Any],
    *,
    node:dict[str,Any],
    fingerprint:str,
    step:dict[str,Any],
    context:dict[str,Any],
)->None:
    outputs=current_output_fingerprints(node,context,step.get("adapter_id"))
    entry={
        "fingerprint":fingerprint,
        "status":step.get("status","skipped"),
        "updated_at":now(),
        "step_record":copy.deepcopy(step),
        "output_fingerprints":outputs,
    }
    if step.get("adapter_id"):
        entry["adapter_id"]=step["adapter_id"]
    state.setdefault("nodes",{})[node["id"]]=entry

def write_retry_checkpoint(
    *,
    node_id:str,
    adapter_id:str,
    attempt:int,
    record:dict[str,Any],
    decision:str,
    log_dir:Path,
)->str:
    before=list(record.get("outputs_before") or [])
    after=list(record.get("outputs_after") or [])
    checkpoint={
        "schema_version":"skyrim-retry-checkpoint-v1",
        "node_id":node_id,
        "adapter_id":adapter_id,
        "attempt":attempt,
        "created_at":now(),
        "status":record.get("status","failed"),
        "outputs_before":before,
        "outputs_after":after,
        "output_mutated":before!=after,
        "decision":decision,
    }
    errs=schema_errors(checkpoint,"skyrim-retry-checkpoint-v1.schema.json")
    if errs:
        raise ValueError("retry checkpoint failed schema validation: "+"; ".join(errs))
    safe_node=re.sub(r"[^A-Za-z0-9_.-]+","_",node_id)
    safe_adapter=re.sub(r"[^A-Za-z0-9_.-]+","_",adapter_id)
    path=log_dir.parent/"retry-checkpoints"/(
        f"{safe_node}--{safe_adapter}--attempt-{attempt:02d}.json"
    )
    atomic_write_json(path,checkpoint)
    return str(path)

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
            output_mutated=(
                list(record.get("outputs_before") or [])
                != list(record.get("outputs_after") or [])
            )
            if record.get("status")!="failed":
                decision="return"
            elif attempt>=max_attempts:
                decision="return"
            elif output_mutated:
                decision="stop-for-rollback"
            else:
                decision="retry"
            checkpoint_path=write_retry_checkpoint(
                node_id=node["id"],
                adapter_id=aid,
                attempt=attempt,
                record=record,
                decision=decision,
                log_dir=log_dir,
            )
            attempts.append({
                "attempt":attempt,
                "status":record.get("status"),
                "stdout_path":record.get("stdout_path"),
                "stderr_path":record.get("stderr_path"),
                "exit_code":record.get("exit_code"),
                "output_mutated":output_mutated,
                "decision":decision,
                "checkpoint":checkpoint_path,
            })
            if record.get("status")!="failed":
                record.setdefault("evidence",{})
                record["evidence"]["adapter_manifest"]=source
                record["evidence"]["attempts"]=attempts
                return record
            if decision=="stop-for-rollback":
                record.setdefault("issues",[]).append(
                    "automatic retry stopped because the failed attempt mutated outputs; "
                    "restore from a repair/rollback checkpoint before another attempt"
                )
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

RUNTIME_RESULT_SCHEMA="skyrim-runtime-session-result-v1.schema.json"

def runtime_session_summary(path:Path)->dict[str,Any]:
    try:
        session=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,UnicodeError,json.JSONDecodeError) as exc:
        raise ValueError(f"could not read runtime session result {path}: {exc}") from exc
    errors=schema_errors(session,RUNTIME_RESULT_SCHEMA)
    if errors:
        raise ValueError(
            f"runtime session result {path} failed schema validation: "
            +"; ".join(errors)
        )
    assertions=list(session.get("assertions") or [])
    status_map={
        "passed":"pass",
        "failed":"fail",
        "needs-review":"warning",
        "aborted":"warning",
        "prepared":"warning",
    }
    evidence=[
        str(path),
        f"session-token:{session.get('session_token')}",
    ]
    evidence.extend(
        str(x.get("path"))
        for x in (session.get("evidence") or {}).get("artifacts") or []
        if isinstance(x,dict) and x.get("path")
    )
    return {
        "path":str(path),
        "test_id":session["test_id"],
        "adapter":"mo2-devbench-runtime",
        "status":status_map[session["status"]],
        "assertions_total":len(assertions),
        "assertions_passed":sum(x.get("status")=="pass" for x in assertions),
        "assertions_failed":sum(x.get("status")=="fail" for x in assertions),
        "evidence":list(dict.fromkeys(evidence)),
        "gates":copy.deepcopy(session.get("gates") or []),
    }

def attach_runtime_session_evidence(
    step:dict[str,Any],
    node:dict[str,Any],
)->dict[str,Any]:
    if node.get("phase")!="runtime":
        return step
    candidates=[
        Path(str(x["path"]))
        for x in step.get("outputs_after") or []
        if isinstance(x,dict) and x.get("exists") and x.get("kind")=="file" and x.get("path")
    ]
    summaries=[]
    issues=[]
    for path in candidates:
        if path.suffix.lower()!=".json":
            continue
        try:
            value=json.loads(path.read_text(encoding="utf-8"))
        except (OSError,UnicodeError,json.JSONDecodeError):
            continue
        if value.get("schema_version")!="skyrim-runtime-session-result-v1":
            continue
        try:
            summaries.append(runtime_session_summary(path))
        except ValueError as exc:
            issues.append(str(exc))
    if not summaries and not issues:
        return step
    step=copy.deepcopy(step)
    if summaries:
        step.setdefault("evidence",{})["runtime_sessions"]=summaries
    if issues:
        step.setdefault("issues",[]).extend(issues)
        step["status"]="failed"
    return step

def combine_runtime_gate_rows(
    summaries_by_step:dict[str,list[dict[str,Any]]],
    gate_registry:dict[str,Any],
    dag:dict[str,Any],
)->list[dict[str,Any]]:
    policies={
        row["gate"]:row
        for row in gate_registry.get("gates") or []
        if isinstance(row,dict) and row.get("gate")
    }
    runtime_nodes=[
        node for node in dag.get("nodes") or []
        if isinstance(node,dict) and node.get("phase")=="runtime"
    ]
    required={
        gate:[
            node["id"] for node in runtime_nodes
            if gate in (node.get("gates") or [])
        ]
        for gate in sorted({
            gate
            for node in runtime_nodes
            for gate in (node.get("gates") or [])
        },key=lambda x:int(x[1:]))
    }
    result=[]
    for gate,node_ids in required.items():
        policy=policies.get(gate) or {"severity":"BLOCKER"}
        rows=[]
        for node_id in node_ids:
            summaries=summaries_by_step.get(node_id) or []
            if not summaries:
                rows.append({
                    "status":"needs-review",
                    "evidence":[],
                    "issues":[
                        f"required runtime node {node_id} produced no typed runtime session evidence"
                    ],
                    "_test_id":node_id,
                    "_path":None,
                })
                continue
            for summary in summaries:
                matches=[
                    row for row in summary.get("gates") or []
                    if isinstance(row,dict) and row.get("gate")==gate
                ]
                if not matches:
                    rows.append({
                        "status":"needs-review",
                        "evidence":[],
                        "issues":[
                            f"runtime session omitted required gate {gate}"
                        ],
                        "_test_id":summary.get("test_id"),
                        "_path":summary.get("path"),
                    })
                    continue
                for row in matches:
                    copied=copy.deepcopy(row)
                    copied["_test_id"]=summary.get("test_id")
                    copied["_path"]=summary.get("path")
                    if copied.get("status")=="not-applicable":
                        copied["status"]="needs-review"
                        copied.setdefault("issues",[]).append(
                            f"{gate} is assigned to runtime node {node_id}; "
                            "not-applicable evidence cannot discharge that required gate"
                        )
                    rows.append(copied)

        statuses=[row.get("status") for row in rows]
        if "fail" in statuses:
            status="fail"
        elif any(x in {"warning","needs-review"} for x in statuses):
            status="warning"
        elif rows and all(x=="pass" for x in statuses):
            status="pass"
        else:
            status="warning"

        evidence=[]
        issues=[]
        for row in rows:
            prefix=f"{row.get('_test_id')}: "
            evidence.extend(prefix+str(x) for x in row.get("evidence") or [])
            if row.get("_path"):
                evidence.append(prefix+f"runtime-session:{row.get('_path')}")
            issues.extend(prefix+str(x) for x in row.get("issues") or [])
        result.append({
            "gate":gate,
            "status":status,
            "severity":policy.get("severity","BLOCKER"),
            "tool":"mo2-devbench-runtime",
            "evidence":list(dict.fromkeys(evidence)),
            "issues":list(dict.fromkeys(issues)),
        })
    return result

def collect_runtime_report_evidence(
    steps:list[dict[str,Any]],
    gate_registry:dict[str,Any],
    dag:dict[str,Any],
)->tuple[list[dict[str,Any]],list[dict[str,Any]]]:
    summaries_by_step={
        step.get("id"):list(
            (step.get("evidence") or {}).get("runtime_sessions") or []
        )
        for step in steps
        if step.get("id")
    }
    summaries=[
        summary
        for rows in summaries_by_step.values()
        for summary in rows
    ]
    runtime_tests=[
        {
            k:copy.deepcopy(summary[k])
            for k in (
                "test_id","adapter","status","assertions_total",
                "assertions_passed","assertions_failed","evidence"
            )
        }
        for summary in summaries
    ]
    gates=combine_runtime_gate_rows(
        summaries_by_step,
        gate_registry,
        dag,
    )
    return runtime_tests,gates


def run_automatic_repair(
    args:argparse.Namespace,
    *,
    report_path:Path,
    state_path:Path,
)->dict[str,Any]:
    loop=load_module("run_repair_loop",HERE/"run_repair_loop.py")
    loop_args=argparse.Namespace(
        failed_report=report_path,
        manifest=args.manifest,
        quality_plan=args.quality_plan,
        build_dag=args.build_dag,
        run_dir=args.run_dir,
        work_dir=args.repair_work_dir,
        state=state_path,
        toolchain_lock=args.toolchain_lock,
        context=args.context,
        capabilities=args.capabilities,
        adapter_dir=args.adapter_dir,
        gate_registry=args.gate_registry,
        rule_pack=args.repair_rule_pack,
        handler_registry=args.repair_handler_registry,
        allowed_output_root=list(args.allowed_output_root or []),
        git_commit=args.git_commit,
        execute=True,
        output=None,
    )
    try:
        return loop.run_cycle(loop_args)
    except ValueError as exc:
        return {
            "schema_version":"skyrim-repair-loop-result-v1",
            "result_status":"escalated",
            "executed":False,
            "reason":str(exc),
        }

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
    ap.add_argument("--state",type=Path)
    ap.add_argument("--no-resume",action="store_true")
    ap.add_argument("--git-commit")
    ap.add_argument("--auto-repair",action="store_true")
    ap.add_argument("--repair-work-dir",type=Path)
    ap.add_argument("--repair-rule-pack",type=Path,default=DEFAULT_REPAIR_RULE_PACK)
    ap.add_argument("--repair-handler-registry",type=Path,default=DEFAULT_REPAIR_HANDLERS)
    ap.add_argument("--allowed-output-root",type=Path,action="append",default=[])
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
    state_path=args.state or (args.run_dir/"execution-state.json")
    if args.no_resume:
        execution_state=new_execution_state(manifest.get("project_id"))
    else:
        execution_state=load_execution_state(state_path,manifest.get("project_id"))
    if not execution_state.get("build_id"):
        execution_state["build_id"]=str(uuid.uuid4())
    save_execution_state(state_path,execution_state)

    capability_map=load_capability_map(args.capabilities)
    gate_registry=load_json(args.gate_registry)
    ordered=topological_order(dag)
    policy=context.get("policy") or {}
    stop_on_failure=policy.get("stop_on_failure",True)
    continue_review=policy.get("continue_on_needs_review",False)

    started=now()
    steps_by_id={}
    node_fingerprints={}
    agent_actions=[]
    hard_stop=False

    for node in ordered:
        fingerprint=compute_node_fingerprint(
            node,
            manifest=manifest,
            quality=quality,
            lock=lock,
            context=context,
            capability_map=capability_map,
            adapter_dir=args.adapter_dir,
            gate_registry=gate_registry,
            dependency_fingerprints=node_fingerprints,
        )
        node_fingerprints[node["id"]]=fingerprint
        reused=None if args.no_resume else reusable_prior_step(
            node,fingerprint,execution_state
        )

        if reused is not None:
            step=reused
        elif hard_stop:
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
            step=enforce_artifact_contracts(step,node,context)
            step=attach_runtime_session_evidence(step,node)
            if step.get("status")=="failed" and stop_on_failure:
                hard_stop=True

        steps_by_id[node["id"]]=step
        checkpoint_node(
            execution_state,
            node=node,
            fingerprint=fingerprint,
            step=step,
            context=context,
        )
        save_execution_state(state_path,execution_state)
        safe=re.sub(r"[^A-Za-z0-9_.-]+","_",node["id"])
        atomic_write_json(step_dir/f"{safe}.json",step)
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

    runtime_tests,runtime_gates=collect_runtime_report_evidence(
        steps,gate_registry,dag
    )

    report={
        "schema_version":"skyrim-mod-build-report-v1",
        "project_id":manifest.get("project_id"),
        "build_id":execution_state["build_id"],
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
        "gates":runtime_gates,
        "runtime_tests":runtime_tests,
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
        "resumed":sum(
            bool((x.get("evidence") or {}).get("resumed_from_state"))
            for x in steps
        ),
        "execution_state":str(state_path),
        "report":str(report_path),
    },indent=2))

    if final=="failed" and args.execute and args.auto_repair:
        repair_result=run_automatic_repair(
            args,
            report_path=report_path,
            state_path=state_path,
        )
        print(json.dumps({"auto_repair":repair_result},indent=2))
        if repair_result.get("result_status")=="repaired":
            return
        if repair_result.get("result_status") in {"escalated","decision-required"}:
            raise SystemExit(3)
    if final=="failed":
        raise SystemExit(2)
    if final=="needs-review":
        raise SystemExit(3)

if __name__=="__main__":
    main()
