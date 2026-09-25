#!/usr/bin/env python3
"""Compare two typed Skyrim semantic-plugin documents conservatively.

Array order remains significant. Record identity compatibility is checked before
record-level diffing so incompatible producer identity schemes cannot masquerade
as a giant semantic change.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
INPUT_SCHEMA="skyrim-semantic-plugin-v1.schema.json"
OUTPUT_SCHEMA="skyrim-semantic-plugin-diff-v1.schema.json"
MISSING=object()

def load_schema(name:str)->dict[str,Any]:
    return json.loads((SCHEMAS/name).read_text(encoding="utf-8"))

def schema_errors(value:dict[str,Any],name:str)->list[str]:
    out=[]
    for err in Draft202012Validator(load_schema(name)).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def record_key(r:dict)->str:
    return f'{r.get("signature","????")}:{r.get("form_key","?")}'

def diff_values(a:Any,b:Any,path:str,out:list[dict]):
    if type(a) is not type(b):
        out.append({"path":path,"kind":"type-changed","before":a,"after":b})
        return
    if isinstance(a,dict):
        keys=sorted(set(a)|set(b))
        for k in keys:
            av=a.get(k,MISSING)
            bv=b.get(k,MISSING)
            p=f"{path}.{k}" if path else k
            if av is MISSING:
                out.append({"path":p,"kind":"added","after":bv})
            elif bv is MISSING:
                out.append({"path":p,"kind":"removed","before":av})
            else:
                diff_values(av,bv,p,out)
    elif isinstance(a,list):
        if a!=b:
            out.append({"path":path,"kind":"list-changed","before":a,"after":b})
    elif a!=b:
        out.append({"path":path,"kind":"changed","before":a,"after":b})

def strip_producer_private(value:Any)->Any:
    if isinstance(value,dict):
        return {
            k:strip_producer_private(v)
            for k,v in value.items()
            if not str(k).startswith("_")
        }
    if isinstance(value,list):
        return [strip_producer_private(x) for x in value]
    return value

def declared_semantic_fields(doc:dict[str,Any])->list[str]|None:
    coverage=((doc.get("provenance") or {}).get("coverage") or {})
    fields=coverage.get("semantic_fields")
    if not isinstance(fields,list) or not all(isinstance(x,str) for x in fields):
        return None
    return sorted(set(fields))

def get_path(value:dict[str,Any],path:str)->Any:
    current:Any=value
    for part in path.split("."):
        if not isinstance(current,dict) or part not in current:
            return MISSING
        current=current[part]
    return current

def set_path(target:dict[str,Any],path:str,value:Any)->None:
    parts=path.split(".")
    current=target
    for part in parts[:-1]:
        current=current.setdefault(part,{})
    current[parts[-1]]=strip_producer_private(value)

def semantic_coverage(
    before:dict[str,Any],
    after:dict[str,Any],
)->tuple[dict[str,Any],list[str]|None]:
    a=declared_semantic_fields(before)
    b=declared_semantic_fields(after)
    if a is None or b is None:
        return {
            "mode":"legacy-full-record",
            "compared_fields":[],
            "before_only_fields":[],
            "after_only_fields":[],
        },None
    aset=set(a)
    bset=set(b)
    common=sorted(aset & bset)
    return {
        "mode":"declared-intersection",
        "compared_fields":common,
        "before_only_fields":sorted(aset-bset),
        "after_only_fields":sorted(bset-aset),
    },common

def project_record(record:dict[str,Any],fields:list[str]|None)->dict[str,Any]:
    if fields is None:
        return strip_producer_private(record)
    projected={}
    for path in fields:
        value=get_path(record,path)
        if value is not MISSING:
            set_path(projected,path,value)
    return projected

def identity_facts(doc:dict[str,Any])->dict[str,Any]:
    provenance=doc.get("provenance") or {}
    canonical=provenance.get("canonical_cross_load_order_form_keys")
    mode=provenance.get("form_key_mode")
    if mode is None and canonical is True:
        mode="canonical-formkey"
    return {
        "mode":mode,
        "canonical":canonical if isinstance(canonical,bool) else None,
        "load_order_sha256":provenance.get("load_order_sha256"),
        "producer":provenance.get("producer"),
    }

def identity_comparability(
    before:dict[str,Any],
    after:dict[str,Any],
)->tuple[bool,list[str],dict[str,Any]]:
    a=identity_facts(before)
    b=identity_facts(after)
    reasons=[]

    if a["canonical"] is True and b["canonical"] is True:
        comparable=True
    elif a["mode"] and b["mode"] and a["mode"]==b["mode"]:
        if a["load_order_sha256"] and b["load_order_sha256"]:
            comparable=a["load_order_sha256"]==b["load_order_sha256"]
            if not comparable:
                reasons.append(
                    "noncanonical record identities were emitted under different load-order snapshots"
                )
        elif a["canonical"] is False or b["canonical"] is False:
            comparable=False
            reasons.append(
                "noncanonical record identities require matching load_order_sha256 provenance"
            )
        else:
            comparable=True
            reasons.append(
                "identity mode matches but canonical/load-order provenance is unspecified"
            )
    else:
        comparable=False
        reasons.append(
            "semantic producers use different or unspecified record-identity modes"
        )

    identity={
        "before_mode":a["mode"],
        "after_mode":b["mode"],
        "before_load_order_sha256":a["load_order_sha256"],
        "after_load_order_sha256":b["load_order_sha256"],
        "before_canonical":a["canonical"],
        "after_canonical":b["canonical"],
    }
    return comparable,reasons,identity

def compare(
    before:dict[str,Any],
    after:dict[str,Any],
    *,
    before_name:str="<before>",
    after_name:str="<after>",
)->dict[str,Any]:
    for label,value in (("before",before),("after",after)):
        errors=schema_errors(value,INPUT_SCHEMA)
        if errors:
            raise ValueError(
                f"{label} semantic plugin failed schema validation: "
                +"; ".join(errors)
            )

    comparable,reasons,identity=identity_comparability(before,after)
    coverage,semantic_fields=semantic_coverage(before,after)
    ar={record_key(x):x for x in before.get("records",[])}
    br={record_key(x):x for x in after.get("records",[])}

    plugin_changes=[]
    diff_values(
        before.get("plugin",{}),
        after.get("plugin",{}),
        "plugin",
        plugin_changes,
    )

    if comparable:
        added=sorted(set(br)-set(ar))
        removed=sorted(set(ar)-set(br))
        changed=[]
        for key in sorted(set(ar)&set(br)):
            diffs=[]
            diff_values(
                project_record(ar[key],semantic_fields),
                project_record(br[key],semantic_fields),
                "",
                diffs,
            )
            if diffs:
                changed.append({"record":key,"changes":diffs})
    else:
        added=[]
        removed=[]
        changed=[]

    has_diff=bool(added or removed or changed or plugin_changes)
    verdict="not-comparable" if not comparable else (
        "different" if has_diff else "equivalent"
    )
    result={
        "schema_version":"skyrim-semantic-plugin-diff-v1",
        "before":before_name,
        "after":after_name,
        "verdict":verdict,
        "comparable":comparable,
        "comparability_reasons":reasons,
        "identity":identity,
        "coverage":coverage,
        "summary":{
            "records_before":len(ar),
            "records_after":len(br),
            "added":len(added),
            "removed":len(removed),
            "changed":len(changed),
            "plugin_header_changes":len(plugin_changes),
        },
        "plugin_changes":plugin_changes,
        "records_added":added,
        "records_removed":removed,
        "records_changed":changed,
    }
    errors=schema_errors(result,OUTPUT_SCHEMA)
    if errors:
        raise ValueError(
            "semantic plugin diff failed schema validation: "
            +"; ".join(errors)
        )
    return result

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("before",type=Path)
    ap.add_argument("after",type=Path)
    ap.add_argument("--output",type=Path)
    ap.add_argument("--fail-on-diff",action="store_true")
    ap.add_argument("--require-comparable",action="store_true")
    args=ap.parse_args()

    try:
        result=compare(
            json.loads(args.before.read_text(encoding="utf-8")),
            json.loads(args.after.read_text(encoding="utf-8")),
            before_name=str(args.before),
            after_name=str(args.after),
        )
    except ValueError as exc:
        raise SystemExit(str(exc))

    text=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    else:
        print(text,end="")

    if args.require_comparable and not result["comparable"]:
        raise SystemExit(3)
    if args.fail_on_diff and result["verdict"]=="different":
        raise SystemExit(2)

if __name__=="__main__":
    main()
