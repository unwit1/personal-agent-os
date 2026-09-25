#!/usr/bin/env python3
"""Compute Skyrim Mod Factory schema-confidence quorum.

Confidence is earned from independent implementations and evidence, not from the
number of tools invoked. A disagreement or unclassified coverage gap blocks PASS.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

LEVELS={"none":0,"A":1,"B":2,"C":3,"D":4}


def coverage_issue(check: dict[str, Any]) -> str | None:
    cov=check.get("coverage") or {}
    discovered=int(cov.get("discovered",0))
    processed=int(cov.get("processed",0))
    skipped=int(cov.get("skipped",0))
    unclassified=int(cov.get("unclassified",0))
    if processed+skipped+unclassified != discovered:
        return f"{check.get('validator')}: coverage arithmetic mismatch ({processed}+{skipped}+{unclassified}!={discovered})"
    if unclassified:
        return f"{check.get('validator')}: {unclassified} discovered inputs are unclassified"
    if skipped and len(cov.get("skip_reasons") or []) == 0:
        return f"{check.get('validator')}: skipped inputs have no classified reason"
    return None


def evaluate(doc: dict[str, Any]) -> dict[str, Any]:
    checks=doc.get("checks") or []
    blockers=[]
    warnings=[]
    passed=[]

    for check in checks:
        issue=coverage_issue(check)
        if issue:
            blockers.append(issue)
        status=check.get("status")
        if status=="fail":
            blockers.append(f"{check.get('validator')}: validator failed")
        elif status in {"warning","unsupported","skipped"}:
            warnings.append(f"{check.get('validator')}: {status}")
        elif status=="pass":
            passed.append(check)

    # Independence is based on implementation family, not adapter name.
    families=[]
    for check in passed:
        if not check.get("independent",False):
            continue
        family=check.get("implementation_family")
        if family and family not in families:
            families.append(family)

    # If validators emit semantic fingerprints, independent disagreement blocks.
    fingerprints={}
    for check in passed:
        fp=check.get("semantic_fingerprint")
        if not fp or not check.get("independent",False):
            continue
        fingerprints.setdefault(fp,[]).append(check.get("validator"))
    if len(fingerprints)>1:
        blockers.append("Independent validators disagree on semantic fingerprint: "+
                        "; ".join(f"{fp}={','.join(vs)}" for fp,vs in fingerprints.items()))

    level="none"
    if passed and not blockers:
        level="A"
    if len(families)>=2 and not blockers:
        level="B"

    rt=doc.get("round_trip") or {}
    intent=doc.get("intent_diff") or {}
    round_ok=(rt.get("status")=="pass" and rt.get("semantic_equivalence") is True)
    intent_ok=(intent.get("status")=="pass" and not (intent.get("unexplained_changes") or []))
    if level=="B" and round_ok and intent_ok and not blockers:
        level="C"

    runtime=doc.get("runtime_assertion") or {}
    runtime_ok=(
        runtime.get("status")=="pass"
        and int(runtime.get("assertions_total",0))>0
        and int(runtime.get("assertions_passed",0))==int(runtime.get("assertions_total",0))
    )
    if level=="C" and runtime_ok and not blockers:
        level="D"

    required=doc.get("required_level") or "A"
    meets=not blockers and LEVELS[level]>=LEVELS[required]

    if rt.get("status")=="fail":
        blockers.append("Round-trip validation failed")
    if intent.get("status")=="fail" or (intent.get("unexplained_changes") or []):
        blockers.append("Intent diff contains unexplained changes")
    if runtime.get("status")=="fail":
        blockers.append("Runtime assertion failed")

    # Recompute after late blockers.
    meets=not blockers and LEVELS[level]>=LEVELS[required]
    status="pass" if meets else "blocked" if blockers else "insufficient-evidence"

    return {
      "schema_version":"skyrim-validation-quorum-result-v1",
      "artifact":doc.get("artifact"),
      "artifact_type":doc.get("artifact_type"),
      "required_level":required,
      "achieved_level":level,
      "status":status,
      "meets_required_level":meets,
      "independent_families":families,
      "passed_validators":[c.get("validator") for c in passed],
      "blockers":blockers,
      "warnings":warnings,
      "evidence_summary":{
        "validators_total":len(checks),
        "validators_passed":len(passed),
        "independent_families":len(families),
        "round_trip":rt.get("status","not-run"),
        "intent_diff":intent.get("status","not-run"),
        "runtime_assertion":runtime.get("status","not-run"),
      }
    }


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("input",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    result=evaluate(json.loads(args.input.read_text(encoding="utf-8")))
    rendered=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered,encoding="utf-8")
    else:
        print(rendered,end="")


if __name__=="__main__":
    main()
