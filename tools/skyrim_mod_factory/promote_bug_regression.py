#!/usr/bin/env python3
"""Create a deterministic regression-candidate packet from a validated Skyrim bug record."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
ELIGIBLE={"root-caused","fixed","validated","closed"}

def load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def schema_errors(value:dict[str,Any],name:str)->list[str]:
    schema=load(SCHEMAS/name)
    out=[]
    for err in Draft202012Validator(schema).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def promote(b:dict[str,Any])->dict[str,Any]:
    bug_errors=schema_errors(b,"skyrim-bug-regression-v1.schema.json")
    if bug_errors:
        raise ValueError("invalid bug record: "+"; ".join(bug_errors))
    if b.get("status") not in ELIGIBLE:
        raise ValueError("bug must be root-caused or later before regression promotion")
    if not b.get("root_cause"):
        raise ValueError("root_cause is required")
    if not b.get("reproduction"):
        raise ValueError("reproduction steps are required")

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
            "mutation_test":reg.get("mutation_test"),
        },
        "rule_authoring_constraints":[
            "Detection must be derived from validated root cause, not symptom similarity.",
            "Record false-positive exclusions.",
            "Auto-fix only if reversible and postconditions are independently provable.",
            "Add a mutation/bad fixture that proves the detector fails closed.",
        ],
    }
    packet_errors=schema_errors(packet,"skyrim-regression-candidate-v1.schema.json")
    if packet_errors:
        raise ValueError("regression candidate failed schema validation: "+"; ".join(packet_errors))
    return packet

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("bug",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    try:
        packet=promote(load(args.bug))
    except ValueError as exc:
        raise SystemExit(str(exc))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(packet,indent=2)+"\n",encoding="utf-8")
    print(args.output)

if __name__=="__main__":
    main()
