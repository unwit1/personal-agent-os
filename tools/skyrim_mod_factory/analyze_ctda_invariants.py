#!/usr/bin/env python3
"""Validate and compare full Skyrim CTDA predicate sets."""
from __future__ import annotations

import argparse, json
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
INPUT_SCHEMA="skyrim-ctda-predicate-set-v1.schema.json"
REPORT_SCHEMA="skyrim-static-invariant-report-v1.schema.json"
VALID_OPERATOR_BITS={0x00,0x20,0x40,0x60,0x80,0xA0}

def load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def schema_errors(value:dict[str,Any],name:str)->list[str]:
    schema=load(SCHEMAS/name)
    out=[]
    for err in Draft202012Validator(schema).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def finding(message:str,*,record:str,index:int|None=None,evidence:dict[str,Any]|None=None,severity:str="ERROR")->dict[str,Any]:
    return {
        "rule_id":"SKYRIM-CTDA-SEMANTIC-LOSS",
        "severity":severity,
        "message":message,
        "record":record,
        "field":f"predicates[{index}]" if index is not None else "predicates",
        "evidence":evidence or {},
    }

def validate_predicate(predicate:dict[str,Any],*,record:str,index:int)->list[dict[str,Any]]:
    out=[]
    type_byte=predicate["type_byte"]
    operator=type_byte & 0xE0
    flags=type_byte & 0x1F
    use_aliases=bool(flags & 0x02)
    use_global=bool(flags & 0x04)
    use_packdata=bool(flags & 0x08)

    if operator not in VALID_OPERATOR_BITS:
        out.append(finding(
            f"unknown CTDA comparison-operator bits 0x{operator:02X}",
            record=record,index=index,
            evidence={"type_byte":type_byte,"operator_bits":operator},
        ))
    if use_aliases and use_packdata:
        out.append(finding(
            "CTDA cannot set both Use aliases and Use packdata",
            record=record,index=index,
            evidence={"type_byte":type_byte},
        ))

    comparison=predicate["comparison"]
    expected_kind="global" if use_global else "literal"
    if comparison["kind"]!=expected_kind:
        out.append(finding(
            f"CTDA comparison kind {comparison['kind']!r} disagrees with Type Use global flag; expected {expected_kind!r}",
            record=record,index=index,
            evidence={"type_byte":type_byte,"comparison":comparison},
        ))

    if predicate["run_on"]==2 and predicate["reference"] in (None,"",0,"000000:Null"):
        out.append(finding(
            "Run On = Reference requires an explicit CTDA reference",
            record=record,index=index,
            evidence={"run_on":predicate["run_on"],"reference":predicate["reference"]},
        ))
    return out

def normalized_predicate(predicate:dict[str,Any])->dict[str,Any]:
    # Preserve every semantically relevant field and original ordering.
    return {
        "type_byte":predicate["type_byte"],
        "comparison":predicate["comparison"],
        "function":predicate["function"],
        "parameter_1":predicate["parameter_1"],
        "parameter_2":predicate["parameter_2"],
        "run_on":predicate["run_on"],
        "reference":predicate["reference"],
        "parameter_3":predicate["parameter_3"],
    }

def analyze(source:dict[str,Any],output:dict[str,Any])->dict[str,Any]:
    for label,value in (("source",source),("output",output)):
        errors=schema_errors(value,INPUT_SCHEMA)
        if errors:
            raise ValueError(f"{label} CTDA set failed schema validation: "+"; ".join(errors))
    if source["record"]!=output["record"]:
        raise ValueError("source and output CTDA sets must refer to the same record")

    record=source["record"]
    findings=[]
    for label,value in (("source",source),("output",output)):
        for i,predicate in enumerate(value["predicates"]):
            for row in validate_predicate(predicate,record=record,index=i):
                row["evidence"]["side"]=label
                findings.append(row)

    source_norm=[normalized_predicate(x) for x in source["predicates"]]
    output_norm=[normalized_predicate(x) for x in output["predicates"]]
    intentional=bool(output.get("intentional_rewrite"))

    if source_norm!=output_norm and not intentional:
        first=None
        max_len=max(len(source_norm),len(output_norm))
        for i in range(max_len):
            a=source_norm[i] if i<len(source_norm) else None
            b=output_norm[i] if i<len(output_norm) else None
            if a!=b:
                first=i
                break
        findings.append(finding(
            "output CTDA predicate sequence does not exactly preserve source semantics",
            record=record,index=first,
            evidence={
                "source_count":len(source_norm),
                "output_count":len(output_norm),
                "first_mismatch_index":first,
                "source_predicate":source_norm[first] if first is not None and first<len(source_norm) else None,
                "output_predicate":output_norm[first] if first is not None and first<len(output_norm) else None,
            },
        ))

    errors_or_blockers=sum(x["severity"] in {"BLOCKER","ERROR"} for x in findings)
    issues=[]
    if intentional and source_norm!=output_norm:
        issues.append(
            "CTDA differs from source but output marks the change as an intentional rewrite; runtime/behavioral validation remains required"
        )
    status="fail" if errors_or_blockers else ("needs-review" if issues else "pass")

    report={
        "schema_version":"skyrim-static-invariant-report-v1",
        "analyzer":"ctda-predicate-preservation",
        "status":status,
        "scope":{"record":record,"intentional_rewrite":intentional},
        "findings":findings,
        "coverage":{
            "source_predicates":len(source_norm),
            "output_predicates":len(output_norm),
            "source_validated":len(source_norm),
            "output_validated":len(output_norm),
            "order_compared":True,
            "fields_compared":[
                "type_byte","comparison","function","parameter_1","parameter_2",
                "run_on","reference","parameter_3"
            ],
        },
        "issues":issues,
    }
    errors=schema_errors(report,REPORT_SCHEMA)
    if errors:
        raise ValueError("CTDA invariant report failed schema validation: "+"; ".join(errors))
    return report

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("source",type=Path)
    ap.add_argument("output",type=Path)
    ap.add_argument("--report",type=Path)
    args=ap.parse_args()
    try:
        report=analyze(load(args.source),load(args.output))
    except ValueError as exc:
        raise SystemExit(str(exc))
    rendered=json.dumps(report,indent=2)+"\n"
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(rendered,encoding="utf-8")
    else:
        print(rendered,end="")
    if report["status"]=="fail":
        raise SystemExit(2)
    if report["status"]=="needs-review":
        raise SystemExit(3)

if __name__=="__main__":
    main()
