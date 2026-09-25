#!/usr/bin/env python3
"""Evaluate Skyrim Mod Factory validation gates from build evidence.

The evaluator never equates process success with semantic proof automatically for
runtime, human, quorum, mutation-test, or mixed-evidence gates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
DEFAULT_REGISTRY=REPO/"knowledge/libraries/skyrim-modding/automation/validation-gate-registry.json"

PHASES=["preflight","source","generate","validate","integrate","runtime","package","release"]
PHASE_INDEX={x:i for i,x in enumerate(PHASES)}

def load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def registry_map(data:dict[str,Any])->dict[str,dict[str,Any]]:
    return {
        x["gate"]:x for x in data.get("gates",[])
        if isinstance(x,dict) and x.get("gate")
    }

def required_gates(quality:dict[str,Any],dag:dict[str,Any])->list[str]:
    out=[]
    for gate in quality.get("gates",[]):
        if gate not in out:
            out.append(gate)
    for node in dag.get("nodes",[]):
        for gate in node.get("gates",[]):
            if gate not in out:
                out.append(gate)
    return sorted(out,key=lambda x:int(x[1:]))

def explicit_evidence(report:dict[str,Any])->dict[str,dict[str,Any]]:
    return {
        x["gate"]:x for x in report.get("gates",[])
        if isinstance(x,dict) and x.get("gate")
    }

def gate_nodes(gate:str,dag:dict[str,Any])->list[dict[str,Any]]:
    # Gate-evaluator aggregation nodes declare the gates they evaluate but are not
    # evidence for those gates themselves.
    return [
        x for x in dag.get("nodes",[])
        if gate in (x.get("gates") or [])
        and x.get("id") not in {"integrate.gates"}
    ]

def status_by_step(report:dict[str,Any])->dict[str,str]:
    return {
        x.get("id"):x.get("status") for x in report.get("steps",[])
        if isinstance(x,dict) and x.get("id")
    }

def normalize_explicit(row:dict[str,Any],policy:dict[str,Any])->dict[str,Any]:
    out={
        "gate":policy["gate"],
        "status":row.get("status","warning"),
        "severity":row.get("severity") or policy["severity"],
        "tool":row.get("tool"),
        "evidence":list(row.get("evidence") or []),
        "issues":list(row.get("issues") or []),
    }
    if row.get("waiver"):
        out["waiver"]=row["waiver"]
    if out.get("tool") is None:
        out.pop("tool",None)
    return out

def automatic_result(
    policy:dict[str,Any],
    nodes:list[dict[str,Any]],
    step_status:dict[str,str],
)->dict[str,Any]:
    statuses=[step_status.get(n["id"]) for n in nodes if n.get("id") in step_status]
    issues=[]
    if not nodes:
        issues.append("no DAG node is assigned to this required gate")
        return {"status":"warning","issues":issues}
    failed=[n["id"] for n in nodes if step_status.get(n["id"])=="failed"]
    review=[n["id"] for n in nodes if step_status.get(n["id"])=="needs-review"]
    missing=[n["id"] for n in nodes if n["id"] not in step_status]
    skipped=[n["id"] for n in nodes if step_status.get(n["id"])=="skipped"]
    if failed:
        return {"status":"fail","issues":["failed evidence nodes: "+", ".join(failed)]}
    if review:
        return {"status":"warning","issues":["evidence nodes need review: "+", ".join(review)]}
    if missing:
        return {"status":"warning","issues":["evidence nodes have no step result: "+", ".join(missing)]}
    if skipped:
        return {"status":"warning","issues":["evidence nodes were skipped: "+", ".join(skipped)]}
    if statuses and all(x=="passed" for x in statuses):
        return {"status":"pass","issues":[]}
    return {"status":"warning","issues":["gate evidence is incomplete"]}

def evaluate(
    registry:dict[str,Any],
    quality:dict[str,Any],
    dag:dict[str,Any],
    report:dict[str,Any],
    *,
    through_phase:str="release",
)->dict[str,Any]:
    if through_phase not in PHASE_INDEX:
        raise ValueError(f"unknown phase: {through_phase}")
    policies=registry_map(registry)
    explicit=explicit_evidence(report)
    steps=status_by_step(report)
    rows=[]
    blockers=[]
    warnings=[]

    for gate in required_gates(quality,dag):
        policy=policies.get(gate)
        if not policy:
            row={
                "gate":gate,
                "status":"warning",
                "severity":"BLOCKER",
                "issues":["gate is required but absent from validation-gate registry"],
                "evidence":[],
            }
            rows.append(row)
            blockers.append(f"{gate}: unregistered gate")
            continue

        if gate in explicit:
            row=normalize_explicit(explicit[gate],policy)
        else:
            due=PHASE_INDEX[through_phase]>=PHASE_INDEX[policy["final_phase"]]
            started=PHASE_INDEX[through_phase]>=PHASE_INDEX[policy["earliest_phase"]]
            nodes=[
                n for n in gate_nodes(gate,dag)
                if PHASE_INDEX.get(n.get("phase","release"),999)<=PHASE_INDEX[through_phase]
            ]
            auto=automatic_result(policy,nodes,steps) if started else {"status":"not-applicable","issues":[]}

            if auto["status"]=="fail":
                status="fail"
                issues=auto["issues"]
            elif not due:
                status="not-applicable"
                issues=[f"gate is not final until phase {policy['final_phase']}"]
                if auto["status"]=="warning":
                    issues+=auto["issues"]
            elif policy["evidence_mode"] in {"automatic","adapter-evidence","provenance"}:
                status=auto["status"]
                issues=auto["issues"]
            else:
                # Process/node evidence can expose failures, but cannot prove these gate classes.
                if auto["status"]=="fail":
                    status="fail"
                    issues=auto["issues"]
                else:
                    status="warning"
                    issues=auto["issues"]+[f"{policy['evidence_mode']} evidence is required"]

            row={
                "gate":gate,
                "status":status,
                "severity":policy["severity"],
                "evidence":[],
                "issues":issues,
            }

        rows.append(row)
        if row["status"]=="fail":
            blockers.append(f"{gate}: "+("; ".join(row.get("issues") or ["failed"])))
        elif row["status"]=="warning":
            if policy.get("blocking",True):
                blockers.append(f"{gate}: authoritative evidence is incomplete")
            else:
                warnings.append(f"{gate}: warning")
        elif row["status"]=="waived" and policy.get("blocking",True):
            warnings.append(f"{gate}: waived")

    status="failed" if any(x["status"]=="fail" for x in rows) else (
        "needs-review" if blockers else "passed"
    )
    return {
        "schema_version":"skyrim-gate-evaluation-v1",
        "through_phase":through_phase,
        "status":status,
        "gates":rows,
        "blockers":blockers,
        "warnings":warnings,
        "summary":{
            "required":len(rows),
            "passed":sum(x["status"]=="pass" for x in rows),
            "failed":sum(x["status"]=="fail" for x in rows),
            "warnings":sum(x["status"]=="warning" for x in rows),
            "waived":sum(x["status"]=="waived" for x in rows),
            "not_applicable":sum(x["status"]=="not-applicable" for x in rows),
        },
    }

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("quality_plan",type=Path)
    ap.add_argument("build_dag",type=Path)
    ap.add_argument("build_report",type=Path)
    ap.add_argument("--registry",type=Path,default=DEFAULT_REGISTRY)
    ap.add_argument("--through-phase",choices=PHASES,default="release")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()

    result=evaluate(
        load(args.registry),
        load(args.quality_plan),
        load(args.build_dag),
        load(args.build_report),
        through_phase=args.through_phase,
    )
    rendered=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered,encoding="utf-8")
    else:
        print(rendered,end="")

    if result["status"]=="failed":
        raise SystemExit(2)
    if result["status"]=="needs-review":
        raise SystemExit(3)

if __name__=="__main__":
    main()
