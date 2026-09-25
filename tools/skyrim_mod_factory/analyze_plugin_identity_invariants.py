#!/usr/bin/env python3
"""Analyze canonical plugin identity/master/ESL invariants from semantic-plugin JSON."""
from __future__ import annotations

import argparse, json, re
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
SEMANTIC_SCHEMA="skyrim-semantic-plugin-v1.schema.json"
REPORT_SCHEMA="skyrim-static-invariant-report-v1.schema.json"
FORMKEY_RE=re.compile(r"^(?P<id>[0-9A-Fa-f]{6}):(?P<mod>.+\.(?:esm|esp|esl))$",re.I)

def load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def schema_errors(value:dict[str,Any],name:str)->list[str]:
    schema=load(SCHEMAS/name)
    out=[]
    for err in Draft202012Validator(schema).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def version_tuple(text:str)->tuple[int,...]:
    parts=[]
    for piece in text.split("."):
        m=re.match(r"^(\d+)",piece)
        if not m:
            break
        parts.append(int(m.group(1)))
    if not parts:
        raise ValueError(f"invalid runtime version: {text!r}")
    return tuple(parts)

def runtime_at_least(current:str,target:str)->bool:
    a=list(version_tuple(current)); b=list(version_tuple(target))
    n=max(len(a),len(b))
    return tuple(a+[0]*(n-len(a))) >= tuple(b+[0]*(n-len(b)))

def finding(rule_id:str,severity:str,message:str,*,record:str|None=None,field:str|None=None,evidence:dict[str,Any]|None=None)->dict[str,Any]:
    return {
        "rule_id":rule_id,"severity":severity,"message":message,
        "record":record,"field":field,"evidence":evidence or {},
    }

def analyze(document:dict[str,Any],*,masters:list[str],light_plugin:bool,header_version:float|None,target_runtime:str,bees_present:bool=False)->dict[str,Any]:
    errors=schema_errors(document,SEMANTIC_SCHEMA)
    if errors:
        raise ValueError("semantic plugin failed schema validation: "+"; ".join(errors))

    plugin=(document.get("plugin") or {}).get("mod_key")
    if not plugin:
        raise ValueError("semantic plugin does not declare plugin.mod_key")

    findings=[]; issues=[]; parsed=[]; seen=set()
    canonical=(document.get("provenance") or {}).get("canonical_cross_load_order_form_keys") is True
    if not canonical:
        issues.append("semantic producer does not declare canonical cross-load-order FormKeys")

    master_lookup={x.lower():x for x in masters}
    plugin_lower=plugin.lower()
    extended=runtime_at_least(target_runtime,"1.6.1130") or bees_present
    low_extended_ids=[]

    for record in document.get("records") or []:
        key=str(record.get("form_key") or "")
        signature=str(record.get("signature") or "????")
        identity=f"{signature}:{key}"
        match=FORMKEY_RE.fullmatch(key)
        if not match:
            findings.append(finding(
                "SKYRIM-PLUGIN-NONCANONICAL-FORMKEY","ERROR",
                "record identity is not a canonical six-hex-digit FormKey",
                record=identity,field="form_key",evidence={"form_key":key},
            ))
            continue

        local_id=int(match.group("id"),16)
        origin=match.group("mod")
        parsed.append((identity,local_id,origin))
        dedupe=(signature.upper(),key.lower())
        if dedupe in seen:
            findings.append(finding(
                "SKYRIM-PLUGIN-DUPLICATE-FORMKEY","BLOCKER",
                "duplicate signature/FormKey identity appears in semantic output",
                record=identity,evidence={"signature":signature,"form_key":key},
            ))
        seen.add(dedupe)

        if origin.lower()!=plugin_lower and origin.lower() not in master_lookup:
            findings.append(finding(
                "SKYRIM-PLUGIN-MISSING-MASTER","BLOCKER",
                f"record originates from {origin}, which is not declared as a master",
                record=identity,field="form_key",
                evidence={"origin_mod_key":origin,"declared_masters":masters},
            ))

        if origin.lower()!=plugin_lower:
            continue

        if light_plugin:
            if local_id>0xFFF:
                findings.append(finding(
                    "SKYRIM-PLUGIN-INVALID-ESL-RANGE","BLOCKER",
                    f"new light-plugin record local ID 0x{local_id:06X} exceeds 0xFFF",
                    record=identity,field="form_key",
                    evidence={"local_id":local_id,"maximum":0xFFF,"target_runtime":target_runtime,"bees_present":bees_present},
                ))
            elif not extended and local_id<0x800:
                findings.append(finding(
                    "SKYRIM-PLUGIN-INVALID-ESL-RANGE","BLOCKER",
                    f"new light-plugin record local ID 0x{local_id:03X} requires the extended ESL range",
                    record=identity,field="form_key",
                    evidence={"local_id":local_id,"minimum":0x800,"target_runtime":target_runtime,"bees_present":bees_present},
                ))
            elif extended and local_id<0x800:
                low_extended_ids.append(identity)
        elif local_id<0x800 and plugin_lower!="skyrim.esm":
            findings.append(finding(
                "SKYRIM-PLUGIN-LOW-REGULAR-FORMID","WARNING",
                f"new regular-plugin record local ID 0x{local_id:03X} is below the conventional 0x800 floor",
                record=identity,field="form_key",evidence={"local_id":local_id},
            ))

    if light_plugin and low_extended_ids:
        if header_version is None:
            findings.append(finding(
                "SKYRIM-PLUGIN-INVALID-ESL-RANGE","ERROR",
                "extended-range light records exist but plugin header version was not supplied",
                evidence={"records":low_extended_ids},
            ))
        elif header_version<1.71:
            findings.append(finding(
                "SKYRIM-PLUGIN-INVALID-ESL-RANGE","BLOCKER",
                "extended-range light records require a 1.71-compatible plugin header",
                field="plugin.header_version",
                evidence={"header_version":header_version,"records":low_extended_ids},
            ))

    errors_or_blockers=sum(x["severity"] in {"BLOCKER","ERROR"} for x in findings)
    warnings=sum(x["severity"]=="WARNING" for x in findings)
    status="fail" if errors_or_blockers else ("needs-review" if issues or warnings else "pass")

    report={
        "schema_version":"skyrim-static-invariant-report-v1",
        "analyzer":"plugin-identity-master-esl",
        "status":status,
        "scope":{
            "plugin":plugin,"light_plugin":light_plugin,"header_version":header_version,
            "target_runtime":target_runtime,"bees_present":bees_present,
            "extended_esl_supported":extended,
        },
        "findings":findings,
        "coverage":{
            "records_selected":len(document.get("records") or []),
            "records_with_canonical_formkey":len(parsed),
            "declared_masters":len(masters),
            "new_records":sum(origin.lower()==plugin_lower for _,_,origin in parsed),
            "override_records":sum(origin.lower()!=plugin_lower for _,_,origin in parsed),
        },
        "issues":issues,
    }
    errors=schema_errors(report,REPORT_SCHEMA)
    if errors:
        raise ValueError("static invariant report failed schema validation: "+"; ".join(errors))
    return report

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("semantic_plugin",type=Path)
    ap.add_argument("--master",action="append",default=[])
    ap.add_argument("--light-plugin",action="store_true")
    ap.add_argument("--header-version",type=float)
    ap.add_argument("--target-runtime",required=True)
    ap.add_argument("--bees-present",action="store_true")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    try:
        report=analyze(
            load(args.semantic_plugin),masters=args.master,
            light_plugin=args.light_plugin,header_version=args.header_version,
            target_runtime=args.target_runtime,bees_present=args.bees_present,
        )
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
