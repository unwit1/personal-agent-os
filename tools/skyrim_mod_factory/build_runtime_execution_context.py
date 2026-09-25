#!/usr/bin/env python3
"""Build deterministic execution-context wiring for Skyrim runtime DAG nodes.

This tool does not invent regression fixtures. It binds only runtime tests supplied
or generated elsewhere. A gate-bearing runtime node without a bound test remains
unconfigured, causing the executor to stop at needs-review rather than launching an
irrelevant scenario.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
CONTEXT_SCHEMA="skyrim-execution-context-v1.schema.json"
RUNTIME_TEST_SCHEMA="skyrim-runtime-test-v1.schema.json"
WORKER_SCHEMA="skyrim-runtime-worker-config-v1.schema.json"
COMPOSITE_ADAPTER="mo2-devbench-runtime"

def load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def schema_errors(value:dict[str,Any],name:str)->list[str]:
    schema=load(SCHEMAS/name)
    out=[]
    for err in Draft202012Validator(schema).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def validate(value:dict[str,Any],name:str,label:str)->None:
    errors=schema_errors(value,name)
    if errors:
        raise ValueError(f"{label} failed schema validation: "+"; ".join(errors))

def safe(value:str)->str:
    return re.sub(r"[^A-Za-z0-9._-]+","-",value).strip("-._") or "runtime"

def runtime_node_ids(dag:dict[str,Any])->list[str]:
    return [
        node["id"]
        for node in dag.get("nodes") or []
        if node.get("phase")=="runtime"
    ]

def bind_runtime_node(
    context:dict[str,Any],
    *,
    node_id:str,
    test_path:Path,
    worker_config_path:Path,
    run_root:Path,
    run_id:str,
)->Path:
    test=load(test_path)
    validate(test,RUNTIME_TEST_SCHEMA,f"runtime test {test_path}")
    if test.get("adapter") not in {"devbench",COMPOSITE_ADAPTER}:
        raise ValueError(
            f"runtime test {test_path} adapter must be devbench or "
            f"{COMPOSITE_ADAPTER}, got {test.get('adapter')!r}"
        )
    result_path=run_root/(safe(node_id)+"-runtime-session.json")
    node=context.setdefault("nodes",{}).setdefault(node_id,{})
    node["adapter_order"]=[COMPOSITE_ADAPTER]
    node["variables"]={
        **(node.get("variables") or {}),
        "runtime_test":str(test_path.resolve()),
        "runtime_worker_config":str(worker_config_path.resolve()),
        "runtime_run_id":run_id,
        "runtime_result":str(result_path.resolve()),
    }
    node["inputs"]=list(dict.fromkeys(
        list(node.get("inputs") or [])
        +[str(test_path.resolve()),str(worker_config_path.resolve())]
    ))
    node["outputs"]=list(dict.fromkeys(
        list(node.get("outputs") or [])+[str(result_path.resolve())]
    ))
    contracts=list(node.get("artifact_contracts") or [])
    contract={
        "path":str(result_path.resolve()),
        "validator":"json-schema",
        "schema":"skyrim-runtime-session-result-v1.schema.json",
        "required":True,
    }
    if contract not in contracts:
        contracts.append(contract)
    node["artifact_contracts"]=contracts
    return result_path

def build_context(
    *,
    project_id:str,
    dag:dict[str,Any],
    worker_config_path:Path,
    run_root:Path,
    smoke_test:Path|None=None,
    regression_test:Path|None=None,
    base_context:dict[str,Any]|None=None,
    run_nonce:str|None=None,
)->dict[str,Any]:
    worker=load(worker_config_path)
    validate(worker,WORKER_SCHEMA,f"runtime worker config {worker_config_path}")
    if dag.get("project_id")!=project_id:
        raise ValueError("build DAG project_id does not match requested project_id")

    context={
        "schema_version":"skyrim-execution-context-v1",
        "project_id":project_id,
        **(base_context or {}),
    }
    context["schema_version"]="skyrim-execution-context-v1"
    context["project_id"]=project_id
    variables=dict(context.get("variables") or {})
    variables.setdefault("python_executable",sys.executable)
    variables.setdefault("repo_root",str(REPO))
    context["variables"]=variables
    context.setdefault("nodes",{})

    run_root.mkdir(parents=True,exist_ok=True)
    nonce=safe(run_nonce or uuid.uuid4().hex[:12])
    bindings={
        "runtime.smoke":smoke_test,
        "runtime.regression":regression_test,
    }
    present=set(runtime_node_ids(dag))
    for node_id,test_path in bindings.items():
        if node_id not in present or test_path is None:
            continue
        bind_runtime_node(
            context,
            node_id=node_id,
            test_path=test_path,
            worker_config_path=worker_config_path,
            run_root=run_root,
            run_id=f"{safe(project_id)}-{safe(node_id)}-{nonce}",
        )

    validate(context,CONTEXT_SCHEMA,"runtime execution context")
    return context

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("build_dag",type=Path)
    ap.add_argument("worker_config",type=Path)
    ap.add_argument("--project-id",required=True)
    ap.add_argument("--run-root",type=Path,required=True)
    ap.add_argument("--smoke-test",type=Path)
    ap.add_argument("--regression-test",type=Path)
    ap.add_argument("--base-context",type=Path)
    ap.add_argument("--run-nonce")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    try:
        context=build_context(
            project_id=args.project_id,
            dag=load(args.build_dag),
            worker_config_path=args.worker_config,
            run_root=args.run_root,
            smoke_test=args.smoke_test,
            regression_test=args.regression_test,
            base_context=load(args.base_context) if args.base_context else None,
            run_nonce=args.run_nonce,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(context,indent=2)+"\n",encoding="utf-8")
    print(args.output)

if __name__=="__main__":
    main()
