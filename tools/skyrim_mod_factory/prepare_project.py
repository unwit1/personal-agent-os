#!/usr/bin/env python3
"""Prepare a Skyrim Mod Factory project in one deterministic pass.

Pipeline:
manifest -> structural validation -> pattern enrichment -> quality plan ->
optional dependency/toolchain preflight -> build DAG -> preparation report.
"""
from __future__ import annotations
import argparse, importlib.util, json
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]

def load_module(name, filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

QUALITY=load_module("quality","derive_quality_plan.py")
DAG=load_module("dag","compile_build_dag.py")
DOCTOR=load_module("doctor","doctor_toolchain.py")

def uniq(xs):
    out=[]; seen=set()
    for x in xs:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

def load_patterns(path: Path):
    if not path.exists(): return {}
    data=json.loads(path.read_text(encoding="utf-8"))
    return {p["pattern_id"]:p for p in data.get("patterns",[])}

def enrich_quality(manifest, quality, patterns):
    selected=[]
    unresolved=[]
    reasons=quality.setdefault("reasons",{})
    features=manifest.get("features") or []
    for feature in features:
        pid=feature.get("pattern_id")
        if not pid: continue
        pat=patterns.get(pid)
        if not pat:
            unresolved.append(f"Unknown implementation pattern '{pid}' for feature '{feature.get('feature_id')}'.")
            continue
        selected.append(pid)
        val=pat.get("validation") or {}
        for gate in val.get("gates",[]):
            if gate not in quality["gates"]: quality["gates"].append(gate)
            reasons.setdefault(gate,[])
            marker=f"pattern:{pid}"
            if marker not in reasons[gate]: reasons[gate].append(marker)
        quality["runtime_scenarios"]=uniq(quality.get("runtime_scenarios",[])+val.get("runtime_tests",[]))
        quality["mutation_tests"]=uniq(quality.get("mutation_tests",[])+val.get("negative_tests",[]))
        quality["human_checks"]=uniq(quality.get("human_checks",[])+val.get("human_checks",[]))
        sel=pat.get("selection") or {}
        quality["adapters"]["preferred"]=uniq(quality["adapters"].get("preferred",[])+sel.get("preferred",[]))
        quality["adapters"]["supporting"]=uniq(
            x for x in quality["adapters"].get("supporting",[])+sel.get("alternatives",[])
            if x not in quality["adapters"]["preferred"]
        )
    quality["gates"]=sorted(set(quality["gates"]),key=lambda x:int(x[1:]))
    quality["selected_patterns"]=uniq(selected)
    quality["pattern_issues"]=unresolved
    return quality

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--workspace",type=Path,required=True,
                    help="Directory that will receive generated planning/preflight artifacts")
    ap.add_argument("--patterns",type=Path,default=REPO/"knowledge/libraries/skyrim-modding/automation/implementation-patterns-core.json")
    ap.add_argument("--toolchain-lock",type=Path)
    ap.add_argument("--no-file-check",action="store_true")
    args=ap.parse_args()

    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("schema_version")!="skyrim-mod-project-v1":
        raise SystemExit("Expected skyrim-mod-project-v1 manifest")

    args.workspace.mkdir(parents=True,exist_ok=True)
    patterns=load_patterns(args.patterns)
    quality=QUALITY.derive(manifest)
    quality=enrich_quality(manifest,quality,patterns)
    dag=DAG.compile_dag(manifest,quality)

    doctor=None
    if args.toolchain_lock:
        lock=json.loads(args.toolchain_lock.read_text(encoding="utf-8"))
        doctor=DOCTOR.audit(lock,quality,manifest,not args.no_file_check)

    qpath=args.workspace/"quality-plan.json"
    dpath=args.workspace/"build-dag.json"
    rpath=args.workspace/"preparation-report.json"
    qpath.write_text(json.dumps(quality,indent=2)+"\n",encoding="utf-8")
    dpath.write_text(json.dumps(dag,indent=2)+"\n",encoding="utf-8")

    report={
      "schema_version":"skyrim-project-preparation-report-v1",
      "project_id":manifest.get("project_id"),
      "risk_tier":quality["risk_tier"],
      "selected_patterns":quality.get("selected_patterns",[]),
      "pattern_issues":quality.get("pattern_issues",[]),
      "blocking_questions":quality.get("blocking_questions",[]),
      "gate_count":len(quality["gates"]),
      "dag_nodes":len(dag["nodes"]),
      "toolchain":doctor,
      "ready_for_execution":(
          not quality.get("blocking_questions")
          and not quality.get("pattern_issues")
          and (doctor is None or doctor.get("status")!="fail")
      ),
      "artifacts":{
        "quality_plan":str(qpath),
        "build_dag":str(dpath)
      }
    }
    rpath.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    if doctor and doctor.get("status")=="fail":
        raise SystemExit(2)

if __name__=="__main__":
    main()
