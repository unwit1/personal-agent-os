#!/usr/bin/env python3
"""Resolve a Skyrim implementation pattern into a deterministic tool/test plan.

The LLM/agent chooses or proposes a semantic pattern ID. This script does not guess
creative intent; it verifies that the chosen pattern exists and resolves preferred
adapters from the capability registry.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
LIB=ROOT/"knowledge/libraries/skyrim-modding/automation"
PATTERNS=LIB/"implementation-patterns-core.json"
REGISTRY=LIB/"tool-capability-registry.json"

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("pattern_id")
    ap.add_argument("--available",help="Comma-separated installed adapter IDs. Omit to plan against registry.")
    ap.add_argument("--json",action="store_true")
    args=ap.parse_args()

    patterns=load(PATTERNS)["patterns"]
    pattern=next((p for p in patterns if p["pattern_id"]==args.pattern_id),None)
    if not pattern:
        known=", ".join(sorted(p["pattern_id"] for p in patterns))
        raise SystemExit(f"Unknown pattern {args.pattern_id!r}. Known: {known}")

    registry={x["adapter_id"]:x for x in load(REGISTRY)["adapters"]}
    available=set(x.strip() for x in args.available.split(",") if x.strip()) if args.available else set(registry)

    def classify(ids):
        resolved=[]; unavailable=[]; unknown=[]
        for aid in ids:
            if aid not in registry:
                unknown.append(aid)
            elif aid in available:
                resolved.append(registry[aid])
            else:
                unavailable.append(registry[aid])
        return resolved,unavailable,unknown

    preferred,preferred_missing,preferred_unknown=classify(pattern["selection"]["preferred"])
    alternatives,alternative_missing,alternative_unknown=classify(pattern["selection"].get("alternatives",[]))

    plan={
        "pattern_id":pattern["pattern_id"],
        "intent":pattern["intent"],
        "preferred_layers":pattern["preferred_layers"],
        "selected_preferred_adapters":[x["adapter_id"] for x in preferred],
        "missing_preferred_adapters":[x["adapter_id"] for x in preferred_missing],
        "available_alternatives":[x["adapter_id"] for x in alternatives],
        "missing_alternatives":[x["adapter_id"] for x in alternative_missing],
        "unregistered_adapter_references":preferred_unknown+alternative_unknown,
        "conditions":pattern["selection"].get("conditions",[]),
        "avoid_by_default":pattern["selection"].get("avoid_by_default",[]),
        "artifacts":pattern.get("artifacts",[]),
        "preemptive_questions":pattern.get("preemptive_questions",[]),
        "required_gates":pattern["validation"]["gates"],
        "runtime_tests":pattern["validation"].get("runtime_tests",[]),
        "negative_tests":pattern["validation"].get("negative_tests",[]),
        "human_checks":pattern["validation"].get("human_checks",[]),
        "compatibility_surfaces":pattern.get("compatibility_surfaces",[]),
        "notes":pattern.get("notes",""),
        "status":"ready" if preferred else ("fallback-only" if alternatives else "missing-tools"),
    }

    if args.json:
        print(json.dumps(plan,indent=2))
    else:
        print(f"Pattern: {plan['pattern_id']} ({plan['status']})")
        print("Preferred available:", ", ".join(plan["selected_preferred_adapters"]) or "none")
        if plan["missing_preferred_adapters"]:
            print("Preferred missing:", ", ".join(plan["missing_preferred_adapters"]))
        if plan["available_alternatives"]:
            print("Alternatives:", ", ".join(plan["available_alternatives"]))
        print("Gates:", ", ".join(plan["required_gates"]))
        for label,key in [
            ("Runtime tests","runtime_tests"),
            ("Negative tests","negative_tests"),
            ("Human checks","human_checks"),
        ]:
            if plan[key]:
                print(label+":")
                for value in plan[key]:
                    print(" -",value)

if __name__=="__main__":
    main()
