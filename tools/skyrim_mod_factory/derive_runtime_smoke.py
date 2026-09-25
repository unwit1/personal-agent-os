#!/usr/bin/env python3
"""Derive the universal closed-loop Skyrim launch/health smoke test.

This test proves only the runtime harness baseline:
- the dedicated MO2 runtime reaches a live devbench instance;
- devbench can execute a registered tool in the launched process;
- instance identity fields are readable and stable (the observer enforces stability);
- G19 crash/log cleanliness is evaluated by the host worker.

It deliberately does not claim feature-semantic coverage. Projects that require G26
must also bind a feature/regression runtime test to runtime.regression.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMA=REPO/"schemas/skyrim-runtime-test-v1.schema.json"

def schema_errors(value:dict[str,Any])->list[str]:
    schema=json.loads(SCHEMA.read_text(encoding="utf-8"))
    out=[]
    for err in Draft202012Validator(schema).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def derive(manifest:dict[str,Any])->dict[str,Any]:
    project_id=manifest.get("project_id") or "project"
    test={
        "schema_version":"skyrim-runtime-test-v1",
        "test_id":f"{project_id}.launch-health",
        "project_id":project_id,
        "description":(
            "Launch the disposable MO2 test runtime and prove a fresh DevBench "
            "instance can execute/read back health state."
        ),
        "adapter":"mo2-devbench-runtime",
        "targets":list(dict.fromkeys(manifest.get("targets") or [])),
        "fixture":{
            "kind":"custom",
            "preconditions":[
                "DevBench is installed in the disposable test profile.",
                "The configured MO2 executable entry launches the target Skyrim runtime.",
            ],
            "destructive_copy_only":True,
        },
        "safety":{
            "allow_save_mutation":False,
            "allow_console_mutation":False,
            "allow_spawn_delete_fixtures":False,
            "forbidden_actions":[
                "mutating a non-disposable user profile",
                "overwriting a user save",
            ],
        },
        "steps":[{
            "id":"devbench-health-dispatch",
            "action":"Execute DevBench inspect health inside the launched runtime.",
            "driver":{
                "adapter":"devbench",
                "kind":"tool",
                "tool":"inspect",
                "arguments":{"kind":"health"},
            },
            "capture":["devbench health response"],
        }],
        "assertions":[
            {
                "id":"runtime-pid",
                "kind":"health",
                "expected":True,
                "operator":"exists",
                "severity":"BLOCKER",
                "probe":{
                    "adapter":"devbench",
                    "tool":"inspect",
                    "arguments":{"kind":"health"},
                    "json_path":"pid",
                },
            },
            {
                "id":"runtime-executable",
                "kind":"health",
                "expected":True,
                "operator":"exists",
                "severity":"BLOCKER",
                "probe":{
                    "adapter":"devbench",
                    "tool":"inspect",
                    "arguments":{"kind":"health"},
                    "json_path":"exe",
                },
            },
        ],
        "evidence":{
            "screenshots":False,
            "logs":[],
            "queries":[
                "devbench /api/health identity before/after scenario",
                "devbench inspect kind=health",
            ],
            "performance":False,
        },
        "cleanup":[
            {"action":"request clean game shutdown through DevBench"},
            {"action":"apply disposable-profile retention/deletion policy"},
        ],
        "regressions":[
            "stale DevBench process/session evidence",
            "runtime launches but DevBench tool dispatch is unavailable",
        ],
    }
    errors=schema_errors(test)
    if errors:
        raise ValueError("derived runtime smoke failed schema validation: "+"; ".join(errors))
    return test

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    try:
        test=derive(manifest)
    except ValueError as exc:
        raise SystemExit(str(exc))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(test,indent=2)+"\n",encoding="utf-8")
    print(args.output)

if __name__=="__main__":
    main()
