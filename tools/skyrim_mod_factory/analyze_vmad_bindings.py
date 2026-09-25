#!/usr/bin/env python3
"""Validate VMAD script/property bindings against a pinned Papyrus symbol inventory."""
from __future__ import annotations

import argparse, json
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
INVENTORY_SCHEMA="skyrim-papyrus-symbol-inventory-v1.schema.json"
BINDING_SCHEMA="skyrim-vmad-binding-set-v1.schema.json"
REPORT_SCHEMA="skyrim-static-invariant-report-v1.schema.json"
RULE_ID="SKYRIM-VMAD-PROPERTY-MISMATCH"

def load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def schema_errors(value:dict[str,Any],name:str)->list[str]:
    schema=load(SCHEMAS/name)
    out=[]
    for err in Draft202012Validator(schema).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def finding(message:str,*,record:str,field:str|None=None,evidence:dict[str,Any]|None=None,severity:str="ERROR")->dict[str,Any]:
    return {
        "rule_id":RULE_ID,
        "severity":severity,
        "message":message,
        "record":record,
        "field":field,
        "evidence":evidence or {},
    }

def normalize_type(value:str)->str:
    return "".join(value.split()).lower()

def is_none_value(value:Any)->bool:
    return value is None or value=="" or value=="None" or value=="Null"

def build_script_index(inventory:dict[str,Any])->tuple[dict[str,dict[str,Any]],list[str]]:
    scripts={}
    issues=[]
    for script in inventory["scripts"]:
        key=script["name"].lower()
        if key in scripts:
            issues.append(f"duplicate Papyrus script declaration: {script['name']}")
        scripts[key]=script
        seen_props=set()
        for prop in script["properties"]:
            pkey=prop["name"].lower()
            if pkey in seen_props:
                issues.append(
                    f"duplicate property declaration {script['name']}.{prop['name']}"
                )
            seen_props.add(pkey)
    return scripts,issues

def resolved_properties(
    script_name:str,
    scripts:dict[str,dict[str,Any]],
)->tuple[dict[str,dict[str,Any]],list[str]]:
    result={}
    issues=[]
    chain=[]
    current=script_name.lower()
    visited=set()

    while current:
        if current in visited:
            issues.append(
                "Papyrus inheritance cycle: "
                +" -> ".join(chain+[scripts.get(current,{"name":current})["name"]])
            )
            break
        visited.add(current)
        script=scripts.get(current)
        if script is None:
            issues.append(f"missing Papyrus parent/script declaration: {current}")
            break
        chain.append(script["name"])
        # Child declarations win; we're walking child -> parent.
        for prop in script["properties"]:
            result.setdefault(prop["name"].lower(),prop)
        parent=script.get("parent")
        current=parent.lower() if isinstance(parent,str) and parent else ""
    return result,issues

def analyze(inventory:dict[str,Any],bindings:dict[str,Any])->dict[str,Any]:
    for label,value,schema in (
        ("inventory",inventory,INVENTORY_SCHEMA),
        ("bindings",bindings,BINDING_SCHEMA),
    ):
        errors=schema_errors(value,schema)
        if errors:
            raise ValueError(f"{label} failed schema validation: "+"; ".join(errors))

    record=bindings["record"]
    scripts,index_issues=build_script_index(inventory)
    findings=[]
    issues=list(index_issues)
    seen_script_bindings=set()
    checked_properties=0
    required_properties=0

    for bound_script in bindings["scripts"]:
        script_name=bound_script["name"]
        skey=script_name.lower()
        if skey in seen_script_bindings:
            findings.append(finding(
                f"duplicate VMAD script attachment: {script_name}",
                record=record,field=f"scripts.{script_name}",
            ))
        seen_script_bindings.add(skey)

        if skey not in scripts:
            findings.append(finding(
                f"VMAD references script {script_name!r} that is absent from the pinned Papyrus inventory",
                record=record,field=f"scripts.{script_name}",
                evidence={"script":script_name},
            ))
            continue

        props,resolve_issues=resolved_properties(script_name,scripts)
        issues.extend(resolve_issues)
        if resolve_issues:
            continue

        bound={}
        for prop in bound_script["properties"]:
            pkey=prop["name"].lower()
            if pkey in bound:
                findings.append(finding(
                    f"duplicate VMAD property binding: {script_name}.{prop['name']}",
                    record=record,
                    field=f"scripts.{script_name}.{prop['name']}",
                ))
            bound[pkey]=prop
            checked_properties+=1

            declared=props.get(pkey)
            if declared is None:
                findings.append(finding(
                    f"VMAD property {script_name}.{prop['name']} is not declared by the script or its inheritance chain",
                    record=record,
                    field=f"scripts.{script_name}.{prop['name']}",
                    evidence={"vmad_type":prop["type"]},
                ))
                continue

            if normalize_type(prop["type"])!=normalize_type(declared["type"]):
                findings.append(finding(
                    f"VMAD property type mismatch for {script_name}.{prop['name']}",
                    record=record,
                    field=f"scripts.{script_name}.{prop['name']}",
                    evidence={
                        "vmad_type":prop["type"],
                        "declared_type":declared["type"],
                    },
                ))

        for pkey,declared in props.items():
            if not declared["required"]:
                continue
            required_properties+=1
            actual=bound.get(pkey)
            if actual is None:
                findings.append(finding(
                    f"required Papyrus property is not bound: {script_name}.{declared['name']}",
                    record=record,
                    field=f"scripts.{script_name}.{declared['name']}",
                    evidence={"declared_type":declared["type"]},
                ))
            elif is_none_value(actual["value"]):
                findings.append(finding(
                    f"required Papyrus property is bound to None: {script_name}.{declared['name']}",
                    record=record,
                    field=f"scripts.{script_name}.{declared['name']}",
                    evidence={"declared_type":declared["type"]},
                ))

    errors_or_blockers=sum(x["severity"] in {"BLOCKER","ERROR"} for x in findings)
    status="fail" if errors_or_blockers else ("needs-review" if issues else "pass")
    report={
        "schema_version":"skyrim-static-invariant-report-v1",
        "analyzer":"vmad-papyrus-binding",
        "status":status,
        "scope":{"record":record},
        "findings":findings,
        "coverage":{
            "inventory_scripts":len(inventory["scripts"]),
            "attached_scripts":len(bindings["scripts"]),
            "bound_properties_checked":checked_properties,
            "required_properties_checked":required_properties,
        },
        "issues":issues,
    }
    errors=schema_errors(report,REPORT_SCHEMA)
    if errors:
        raise ValueError("VMAD invariant report failed schema validation: "+"; ".join(errors))
    return report

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("inventory",type=Path)
    ap.add_argument("bindings",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    try:
        report=analyze(load(args.inventory),load(args.bindings))
    except ValueError as exc:
        raise SystemExit(str(exc))
    rendered=json.dumps(report,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered,encoding="utf-8")
    else:
        print(rendered,end="")
    if report["status"]=="fail":
        raise SystemExit(2)
    if report["status"]=="needs-review":
        raise SystemExit(3)

if __name__=="__main__":
    main()
