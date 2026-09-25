#!/usr/bin/env python3
"""Create a deterministic regression-candidate packet from a validated Skyrim bug record."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ELIGIBLE={"root-caused","fixed","validated","closed"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("bug",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    b=json.loads(args.bug.read_text(encoding="utf-8"))
    if b.get("schema_version")!="skyrim-bug-regression-v1":
        raise SystemExit("Wrong schema_version")
    if b.get("status") not in ELIGIBLE:
        raise SystemExit("Bug must be root-caused or later before regression promotion")
    if not b.get("root_cause"):
        raise SystemExit("root_cause is required")
    if not b.get("reproduction"):
        raise SystemExit("reproduction steps are required")

    reg=b.get("regression") or {}
    packet={
      "schema_version":"skyrim-regression-candidate-v1",
      "bug_id":b["bug_id"],
      "project_id":b["project_id"],
      "symptom":b["symptom"],
      "expected":b.get("expected"),
      "layer":b.get("layer"),
      "root_cause":b["root_cause"],
      "first_causal_error":b.get("first_causal_error"),
      "reproduction":b["reproduction"],
      "validated_fix":b.get("fixed_by",[]),
      "validation_evidence":b.get("validation",[]),
      "evidence":b.get("evidence",[]),
      "requested_outputs":{
        "fixture_id":reg.get("fixture_id"),
        "test_id":reg.get("test_id"),
        "analyzer_rule_id":reg.get("analyzer_rule_id"),
        "mutation_test":reg.get("mutation_test")
      },
      "rule_authoring_constraints":[
        "Detection must be derived from validated root cause, not symptom similarity.",
        "Record false-positive exclusions.",
        "Auto-fix only if reversible and postconditions are independently provable.",
        "Add a mutation/bad fixture that proves the detector fails closed."
      ]
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(packet,indent=2)+"\n",encoding="utf-8")
    print(args.output)

if __name__=="__main__":
    main()
