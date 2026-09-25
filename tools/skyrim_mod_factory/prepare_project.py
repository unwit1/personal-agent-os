#!/usr/bin/env python3
"""Prepare a Skyrim Mod Factory project in one deterministic pass.

Pipeline:
manifest -> pattern/provider resolution -> quality plan -> optional toolchain preflight
-> incremental build DAG -> readiness report.
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

def load_providers(path: Path):
    if not path.exists(): return {}
    data=json.loads(path.read_text(encoding="utf-8"))
    return {p["provider_id"]:p for p in data.get("providers",[])}

def load_adapter_ids(path: Path):
    if not path.exists(): return set()
    data=json.loads(path.read_text(encoding="utf-8"))
    return {p["adapter_id"] for p in data.get("adapters",[])}

def resolve_provider(token, providers, adapter_ids, seen=None):
    """Return (kind, resolved adapter or None, provider record or None).

    Direct adapter IDs always win. Aliases may point to an adapter or another
    provider. Cycles are reported as unknown.
    """
    if token in adapter_ids:
        return "adapter", token, None
    seen=set(seen or ())
    if token in seen:
        return "unknown", None, None
    seen.add(token)
    p=providers.get(token)
    if not p:
        return "unknown", None, None
    kind=p.get("kind")
    if kind=="alias":
        if p.get("adapter_id"):
            aid=p["adapter_id"]
            return ("adapter",aid,p) if aid in adapter_ids else ("unknown",None,p)
        if p.get("resolves_to"):
            k,a,_=resolve_provider(p["resolves_to"],providers,adapter_ids,seen)
            return k,a,p
    return kind, p.get("adapter_id"), p

def enrich_quality(manifest, quality, patterns, providers=None, adapter_ids=None):
    providers=providers or {}
    adapter_ids=set(adapter_ids or ())
    selected=[]
    pattern_issues=[]
    provider_issues=[]
    implementation_providers=[]
    frameworks=[]
    strategies=[]
    references=[]
    unadapted_preferred=[]
    reasons=quality.setdefault("reasons",{})
    quality.setdefault("adapters",{}).setdefault("preferred",[])
    quality["adapters"].setdefault("supporting",[])
    features=manifest.get("features") or []

    def apply_provider(token, preference):
        kind,adapter,meta=resolve_provider(token,providers,adapter_ids)
        row={"provider_id":token,"kind":kind,"preference":preference}
        if adapter: row["resolved_adapter"]=adapter
        implementation_providers.append(row)
        validations=(meta or {}).get("validation_adapters",[])
        if preference=="preferred":
            if kind=="adapter" and adapter:
                quality["adapters"]["preferred"]=uniq(quality["adapters"]["preferred"]+[adapter])
            elif kind=="framework":
                frameworks.append(token)
            elif kind=="strategy":
                strategies.append(token)
            elif kind=="reference":
                references.append(token)
            elif kind=="unadapted-tool":
                unadapted_preferred.append(token)
            elif kind=="pattern":
                # This records architectural fallback/composition; it is not
                # recursively selected unless the project feature itself names it.
                strategies.append(f"pattern:{(meta or {}).get('pattern_id',token)}")
            else:
                provider_issues.append(f"preferred:{token}:unclassified provider")
        else:
            if kind=="adapter" and adapter and adapter not in quality["adapters"]["preferred"]:
                quality["adapters"]["supporting"]=uniq(quality["adapters"]["supporting"]+[adapter])
            elif kind=="unknown":
                provider_issues.append(f"alternative:{token}:unclassified provider")
        for aid in validations:
            if aid in adapter_ids and aid not in quality["adapters"]["preferred"]:
                quality["adapters"]["supporting"]=uniq(quality["adapters"]["supporting"]+[aid])

    for feature in features:
        pid=feature.get("pattern_id")
        if not pid: continue
        pat=patterns.get(pid)
        if not pat:
            pattern_issues.append(f"Unknown implementation pattern '{pid}' for feature '{feature.get('feature_id')}'.")
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
        for token in sel.get("preferred",[]): apply_provider(token,"preferred")
        for token in sel.get("alternatives",[]): apply_provider(token,"alternative")

    quality["gates"]=sorted(set(quality["gates"]),key=lambda x:int(x[1:]))
    quality["adapters"]["preferred"]=uniq(quality["adapters"]["preferred"])
    quality["adapters"]["supporting"]=uniq(
        x for x in quality["adapters"]["supporting"] if x not in quality["adapters"]["preferred"]
    )
    quality["selected_patterns"]=uniq(selected)
    quality["pattern_issues"]=uniq(pattern_issues)
    quality["implementation_providers"]=implementation_providers
    quality["framework_dependencies"]=uniq(frameworks)
    quality["strategy_dependencies"]=uniq(strategies)
    quality["reference_dependencies"]=uniq(references)
    quality["unadapted_providers"]=uniq(unadapted_preferred)
    quality["provider_issues"]=uniq(provider_issues)
    return quality

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--workspace",type=Path,required=True,
                    help="Directory that will receive generated planning/preflight artifacts")
    ap.add_argument("--patterns",type=Path,
        default=REPO/"knowledge/libraries/skyrim-modding/automation/implementation-patterns-core.json")
    ap.add_argument("--providers",type=Path,
        default=REPO/"knowledge/libraries/skyrim-modding/automation/implementation-provider-registry.json")
    ap.add_argument("--capabilities",type=Path,
        default=REPO/"knowledge/libraries/skyrim-modding/automation/tool-capability-registry.json")
    ap.add_argument("--toolchain-lock",type=Path)
    ap.add_argument("--no-file-check",action="store_true")
    args=ap.parse_args()

    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("schema_version")!="skyrim-mod-project-v1":
        raise SystemExit("Expected skyrim-mod-project-v1 manifest")

    args.workspace.mkdir(parents=True,exist_ok=True)
    patterns=load_patterns(args.patterns)
    providers=load_providers(args.providers)
    adapter_ids=load_adapter_ids(args.capabilities)
    quality=QUALITY.derive(manifest)
    quality=enrich_quality(manifest,quality,patterns,providers,adapter_ids)
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

    blocking_provider_issues=[x for x in quality.get("provider_issues",[]) if x.startswith("preferred:")]
    environment_ok=(doctor is None or doctor.get("status")!="fail")
    design_ok=not quality.get("blocking_questions") and not quality.get("pattern_issues") and not blocking_provider_issues
    supervised_ready=design_ok and environment_ok
    autonomous_ready=supervised_ready and not quality.get("unadapted_providers")

    report={
      "schema_version":"skyrim-project-preparation-report-v1",
      "project_id":manifest.get("project_id"),
      "risk_tier":quality["risk_tier"],
      "selected_patterns":quality.get("selected_patterns",[]),
      "framework_dependencies":quality.get("framework_dependencies",[]),
      "unadapted_preferred_providers":quality.get("unadapted_providers",[]),
      "pattern_issues":quality.get("pattern_issues",[]),
      "provider_issues":quality.get("provider_issues",[]),
      "blocking_questions":quality.get("blocking_questions",[]),
      "gate_count":len(quality["gates"]),
      "dag_nodes":len(dag["nodes"]),
      "toolchain":doctor,
      "ready_for_execution":supervised_ready,
      "ready_for_autonomous_execution":autonomous_ready,
      "requires_supervised_provider":supervised_ready and not autonomous_ready,
      "artifacts":{"quality_plan":str(qpath),"build_dag":str(dpath)}
    }
    rpath.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    if doctor and doctor.get("status")=="fail":
        raise SystemExit(2)

if __name__=="__main__":
    main()
