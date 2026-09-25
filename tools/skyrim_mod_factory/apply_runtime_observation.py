#!/usr/bin/env python3
"""Merge a typed runtime observer report into a prepared MO2 session result.

Security/reliability rules:
- run_id + session_token must match the current session;
- observation timestamp cannot predate session start;
- unknown step/assertion IDs are rejected;
- observers cannot set G26 directly; it is derived from typed assertion results;
- a failed/timed-out launch or failed cleanup cannot be upgraded to PASS;
- missing observer coverage remains needs-review.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
SESSION_SCHEMA="skyrim-runtime-session-result-v1.schema.json"
OBS_SCHEMA="skyrim-runtime-observation-v1.schema.json"

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

def parse_time(value:str)->dt.datetime:
    parsed=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp must include timezone offset: {value}")
    return parsed.astimezone(dt.timezone.utc)

def index_unique(rows:list[dict[str,Any]],label:str)->dict[str,dict[str,Any]]:
    out={}
    for row in rows:
        key=row["id"]
        if key in out:
            raise ValueError(f"duplicate {label} id in observation: {key}")
        out[key]=row
    return out

def gate_index(rows:list[dict[str,Any]])->dict[str,dict[str,Any]]:
    return {row["gate"]:row for row in rows}

def assertion_gate(assertions:list[dict[str,Any]])->dict[str,Any]:
    evidence=[
        f'{row["id"]}: {row["status"]}'
        for row in assertions
    ]
    hard_fail=[
        row for row in assertions
        if row["status"]=="fail" and row.get("severity") in {"BLOCKER","ERROR"}
    ]
    soft_fail=[
        row for row in assertions
        if row["status"]=="fail" and row.get("severity") in {"WARNING","INFO"}
    ]
    pending=[row for row in assertions if row["status"]=="needs-review"]
    if hard_fail:
        status="fail"
        issues=[
            f'runtime assertion failed: {row["id"]}'
            for row in hard_fail
        ]
    elif soft_fail:
        status="warning"
        issues=[
            f'non-blocking runtime assertion failed: {row["id"]}'
            for row in soft_fail
        ]
    elif pending:
        status="needs-review"
        issues=[
            f'runtime assertion lacks decisive evidence: {row["id"]}'
            for row in pending
        ]
    else:
        status="pass"
        issues=[]
    return {
        "gate":"G26",
        "status":status,
        "evidence":evidence,
        "issues":issues,
    }

def overall_status(session:dict[str,Any])->str:
    launch=session["launch"]
    if launch.get("timed_out"):
        return "failed"
    if launch.get("attempted") and launch.get("exit_code") not in (0,None):
        return "failed"
    if session["cleanup"]["status"]=="failed":
        return "failed"
    if any(row["status"]=="failed" for row in session["steps"]):
        return "failed"
    if any(
        row["status"]=="fail" and row.get("severity") in {"BLOCKER","ERROR"}
        for row in session["assertions"]
    ):
        return "failed"
    if any(row["status"]=="fail" for row in session["gates"]):
        return "failed"
    if any(row["status"]=="needs-review" for row in session["steps"]):
        return "needs-review"
    if any(row["status"]=="needs-review" for row in session["assertions"]):
        return "needs-review"
    if any(row["status"] in {"warning","needs-review"} for row in session["gates"]):
        return "needs-review"
    if any(
        row["status"]=="fail" and row.get("severity") in {"WARNING","INFO"}
        for row in session["assertions"]
    ):
        return "needs-review"
    if not launch.get("attempted"):
        return "prepared"
    return "passed"

def merge_observation(
    session:dict[str,Any],
    observation:dict[str,Any],
)->dict[str,Any]:
    validate(session,SESSION_SCHEMA,"runtime session")
    validate(observation,OBS_SCHEMA,"runtime observation")

    if observation["run_id"]!=session["run_id"]:
        raise ValueError("runtime observation run_id does not match session")
    if observation["session_token"]!=session["session_token"]:
        raise ValueError(
            "runtime observation session_token does not match current session; "
            "stale/cross-session evidence is rejected"
        )
    if not session["launch"]["attempted"] or not session.get("started_at"):
        raise ValueError("runtime observation cannot be applied before session launch")
    if parse_time(observation["captured_at"])<parse_time(session["started_at"]):
        raise ValueError(
            "runtime observation predates session start; stale evidence is rejected"
        )

    merged=copy.deepcopy(session)
    session_steps={row["id"]:row for row in merged["steps"]}
    observed_steps=index_unique(observation["steps"],"step")
    unknown_steps=sorted(set(observed_steps)-set(session_steps))
    if unknown_steps:
        raise ValueError(
            "runtime observation contains unknown step ids: "
            +", ".join(unknown_steps)
        )
    for sid,row in observed_steps.items():
        target=session_steps[sid]
        target["status"]=row["status"]
        target["issues"]=list(row.get("issues") or [])
        if row.get("evidence"):
            target["evidence"]=list(row["evidence"])

    session_assertions={row["id"]:row for row in merged["assertions"]}
    observed_assertions=index_unique(observation["assertions"],"assertion")
    unknown_assertions=sorted(set(observed_assertions)-set(session_assertions))
    if unknown_assertions:
        raise ValueError(
            "runtime observation contains unknown assertion ids: "
            +", ".join(unknown_assertions)
        )
    for aid,row in observed_assertions.items():
        target=session_assertions[aid]
        target["status"]=row["status"]
        target["observed"]=row.get("observed")
        target["issues"]=list(row.get("issues") or [])
        if row.get("evidence"):
            target["evidence"]=list(row["evidence"])

    gates=gate_index(merged["gates"])
    seen_gate=set()
    for row in observation["gates"]:
        gate=row["gate"]
        if gate in seen_gate:
            raise ValueError(f"duplicate gate evidence in observation: {gate}")
        seen_gate.add(gate)
        gates[gate]=copy.deepcopy(row)
    gates["G26"]=assertion_gate(merged["assertions"])
    merged["gates"]=[gates[g] for g in ("G19","G20","G21","G26")]

    observation_artifacts=copy.deepcopy(observation.get("artifacts") or [])
    merged["evidence"]["artifacts"].extend(observation_artifacts)
    screenshot_paths=[
        str(row["path"])
        for row in observation_artifacts
        if isinstance(row,dict)
        and row.get("kind")=="screenshot"
        and row.get("path")
    ]
    for path in screenshot_paths:
        if path not in merged["evidence"]["screenshots"]:
            merged["evidence"]["screenshots"].append(path)
    frame_paths=[
        str(row["path"])
        for row in observation_artifacts
        if isinstance(row,dict)
        and row.get("kind") in {"frame-trace","performance-trace"}
        and row.get("path")
    ]
    for path in frame_paths:
        if path not in merged["evidence"]["frame_traces"]:
            merged["evidence"]["frame_traces"].append(path)
    merged["evidence"]["artifacts"].append({
        "kind":"runtime-observation",
        "observer_id":observation["observer_id"],
        "observer_version":observation.get("observer_version"),
        "transport":observation.get("transport"),
        "captured_at":observation["captured_at"],
        "run_id":observation["run_id"],
        "session_token":observation["session_token"],
    })
    for issue in observation.get("issues") or []:
        if issue not in merged.setdefault("issues",[]):
            merged["issues"].append(issue)

    merged["status"]=overall_status(merged)
    validate(merged,SESSION_SCHEMA,"merged runtime session")
    return merged

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("session",type=Path)
    ap.add_argument("observation",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    try:
        merged=merge_observation(load(args.session),load(args.observation))
    except ValueError as exc:
        raise SystemExit(str(exc))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(merged,indent=2)+"\n",encoding="utf-8")
    print(args.output)
    if merged["status"]=="failed":
        raise SystemExit(2)
    if merged["status"]=="needs-review":
        raise SystemExit(3)

if __name__=="__main__":
    main()
