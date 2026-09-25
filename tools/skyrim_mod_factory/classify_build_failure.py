#!/usr/bin/env python3
"""Classify the first causal-looking Skyrim Mod Factory build failure into a bug record.

This bridge is intentionally conservative:
- it selects the first failed build step in recorded DAG order;
- it preserves normalized issue codes, analyzer rule IDs and log evidence;
- a matched analyzer rule raises classification confidence but does not by itself
  claim a root cause;
- unknown failures remain reported bugs for hypothesis-driven repair planning.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
DEFAULT_RULE_PACK=REPO/"knowledge/libraries/skyrim-modding/automation/analyzer-rule-pack-core.json"

def load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def schema_errors(value:dict[str,Any],schema_name:str)->list[str]:
    schema=load(SCHEMAS/schema_name)
    return [
        (".".join(str(x) for x in e.absolute_path) or "<root>")+": "+e.message
        for e in Draft202012Validator(schema).iter_errors(value)
    ]

def rules_by_id(pack:dict[str,Any])->dict[str,dict[str,Any]]:
    return {
        r["rule_id"]:r for r in pack.get("rules",[])
        if isinstance(r,dict) and r.get("rule_id")
    }

def changed_output_paths(step:dict[str,Any])->list[str]:
    before={x.get("path"):x for x in step.get("outputs_before") or [] if x.get("path")}
    changed=[]
    for after in step.get("outputs_after") or []:
        path=after.get("path")
        if not path:
            continue
        if before.get(path)!=after:
            changed.append(path)
    return changed

def infer_layer(step:dict[str,Any],matched:list[dict[str,Any]])->str:
    scopes=[]
    for rule in matched:
        scopes.extend(rule.get("scope") or [])
    if scopes:
        return scopes[0]
    sid=str(step.get("id") or "")
    known={
        "records":"records","runtime-patching":"runtime-patching","papyrus":"papyrus",
        "native":"native","ui":"ui","animation":"animation","behavior":"behavior",
        "mesh":"mesh","texture":"texture","physics":"physics","world":"world",
        "navmesh":"navmesh","quest-dialogue":"dialogue","audio":"voice",
        "lod":"generated-output","installer":"packaging","save-persistence":"save",
        "compatibility":"integration",
    }
    for token,layer in known.items():
        if token in sid:
            return layer
    return "unknown"

def classify(report:dict[str,Any],rule_pack:dict[str,Any])->dict[str,Any]:
    failed=[x for x in report.get("steps",[]) if x.get("status")=="failed"]
    if not failed:
        raise ValueError("build report has no failed step")
    step=failed[0]
    rule_ids=list(dict.fromkeys(step.get("analyzer_rule_ids") or []))
    index=rules_by_id(rule_pack)
    matched=[index[rid] for rid in rule_ids if rid in index]
    unknown=[rid for rid in rule_ids if rid not in index]

    issues=list(step.get("issues") or [])
    issue_codes=list(step.get("issue_codes") or [])
    evidence=[]
    evidence.extend(rule_ids)
    evidence.extend(f"ISSUE:{x}" for x in issue_codes)
    for key in ("stdout_path","stderr_path"):
        if step.get(key):
            evidence.append(f"{key}:{step[key]}")
    if unknown:
        evidence.append("UNKNOWN_ANALYZER_RULES:"+",".join(unknown))

    symptom=issues[0] if issues else f"Build step {step.get('id')} failed"
    record={
        "schema_version":"skyrim-bug-regression-v1",
        "bug_id":re.sub(
            r"[^A-Za-z0-9._-]+",
            "-",
            f"{report.get('build_id','build')}-{step.get('id','failed')}",
        ).strip("-") or "build-failure",
        "project_id":report.get("project_id","unknown"),
        "build_id":report.get("build_id"),
        "status":"reported",
        "symptom":symptom,
        "environment":{
            "runtime_context":report.get("runtime_context") or {},
            "build_status":report.get("status"),
        },
        "evidence":evidence,
        "first_causal_error":symptom,
        "layer":infer_layer(step,matched),
        "failing_task":step.get("id",""),
        "adapter":step.get("adapter_id",""),
        "exit_code":step.get("exit_code"),
        "changed_files":changed_output_paths(step),
        "regression":{},
    }
    if len(matched)==1:
        record["regression"]["analyzer_rule_id"]=matched[0]["rule_id"]
    if not record["build_id"]:
        record.pop("build_id",None)
    if record["exit_code"] is None:
        # null is permitted and useful for timeout/launch failures.
        pass

    errs=schema_errors(record,"skyrim-bug-regression-v1.schema.json")
    if errs:
        raise ValueError("classified bug record failed schema validation: "+"; ".join(errs))
    return record

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("build_report",type=Path)
    ap.add_argument("--rule-pack",type=Path,default=DEFAULT_RULE_PACK)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    try:
        record=classify(load(args.build_report),load(args.rule_pack))
    except ValueError as exc:
        raise SystemExit(str(exc))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "bug_id":record["bug_id"],
        "failing_task":record["failing_task"],
        "analyzer_rule_id":record.get("regression",{}).get("analyzer_rule_id"),
        "output":str(args.output),
    },indent=2))

if __name__=="__main__":
    main()
