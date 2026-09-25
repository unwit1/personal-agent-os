#!/usr/bin/env python3
"""Validate composition of typed SPID/KID/BOS runtime patch intents."""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
INTENT_SCHEMA=SCHEMAS/"skyrim-runtime-patch-intent-v1.schema.json"
REPORT_SCHEMA=SCHEMAS/"skyrim-runtime-patch-bundle-report-v1.schema.json"

def load_module(name:str):
    path=HERE/f"{name}.py"
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

SPID=load_module("render_spid")
KID=load_module("render_kid")
BOS=load_module("render_bos")

def load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def schema_errors(value:dict[str,Any],schema_path:Path)->list[str]:
    schema=load(schema_path)
    out=[]
    for err in Draft202012Validator(schema).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def finding(
    severity:str,code:str,message:str,
    *,intent_id:str|None=None,entry_index:int|None=None,
)->dict[str,Any]:
    return {
        "severity":severity,"code":code,"message":message,
        "intent_id":intent_id,"entry_index":entry_index,
    }

def form_ref(value:dict[str,Any])->str:
    if value.get("editor_id"):
        return "edid:"+value["editor_id"].casefold()
    if value.get("form_id") and value.get("plugin"):
        return (
            "form:"+value["plugin"].casefold()+":"
            +value["form_id"].lower().removeprefix("0x").lstrip("0")
        )
    if value.get("dynamic_keyword"):
        return "dynamic:"+value["dynamic_keyword"].casefold()
    return "invalid:"+json.dumps(value,sort_keys=True)

def default_output(intent:dict[str,Any])->str|None:
    if intent.get("output_file"):
        return str(intent["output_file"])
    iid=intent.get("intent_id")
    framework=intent.get("framework")
    if not iid:
        return None
    suffix={
        "spid":"_DISTR.ini",
        "kid":"_KID.ini",
        "bos":"_SWAP.ini",
    }.get(framework)
    return iid+suffix if suffix else None

def detect_cycle(edges:dict[str,str])->list[str]|None:
    visited=set()
    for start in sorted(edges):
        if start in visited:
            continue
        order=[]
        position={}
        node=start
        while node in edges:
            if node in position:
                return order[position[node]:]+[node]
            if node in visited:
                break
            position[node]=len(order)
            order.append(node)
            node=edges[node]
        visited.update(order)
    return None

def validate_bundle(intents:list[dict[str,Any]])->dict[str,Any]:
    findings=[]
    rows=[]
    seen_ids={}
    seen_outputs={}
    counts={"spid":0,"kid":0,"bos":0}
    rendered_seen=defaultdict(dict)
    bos_targets=defaultdict(dict)
    bos_edges={}

    for intent_index,intent in enumerate(intents):
        errors=schema_errors(intent,INTENT_SCHEMA)
        iid=str(intent.get("intent_id") or f"<intent-{intent_index}>")
        framework=str(intent.get("framework") or "")
        if errors:
            for message in errors:
                findings.append(finding(
                    "ERROR","RUNTIME-INTENT-SCHEMA",message,intent_id=iid
                ))
            rows.append({
                "intent_id":iid,"framework":framework,
                "output_file":default_output(intent),
                "entry_count":len(intent.get("entries") or []),
                "schema_valid":False,
            })
            continue

        key=iid.casefold()
        if key in seen_ids:
            findings.append(finding(
                "ERROR","RUNTIME-DUPLICATE-INTENT-ID",
                f"intent_id {iid!r} duplicates {seen_ids[key]!r}",
                intent_id=iid,
            ))
        else:
            seen_ids[key]=iid

        output=default_output(intent)
        if output:
            okey=output.replace("\\","/").casefold()
            if okey in seen_outputs:
                findings.append(finding(
                    "ERROR","RUNTIME-OUTPUT-COLLISION",
                    f"output {output!r} collides with intent {seen_outputs[okey]!r}",
                    intent_id=iid,
                ))
            else:
                seen_outputs[okey]=iid

        rows.append({
            "intent_id":iid,"framework":framework,
            "output_file":output,
            "entry_count":len(intent["entries"]),
            "schema_valid":True,
        })

        if framework not in {"spid","kid","bos"}:
            findings.append(finding(
                "WARNING","RUNTIME-FRAMEWORK-NOT-COMPOSED",
                f"bundle composition validator has no specialized checks for {framework!r}",
                intent_id=iid,
            ))
            continue

        for index,entry in enumerate(intent["entries"]):
            counts[framework]+=1
            try:
                if framework=="spid":
                    rendered=SPID.render(entry)
                elif framework=="kid":
                    rendered=KID.render(entry)
                else:
                    rendered=f"[{BOS.section(entry)}] "+BOS.render_line(entry)
            except Exception as exc:
                findings.append(finding(
                    "ERROR","RUNTIME-RENDER-INVALID",
                    str(exc),intent_id=iid,entry_index=index,
                ))
                continue

            rkey=rendered.casefold()
            prior=rendered_seen[framework].get(rkey)
            if prior is not None:
                findings.append(finding(
                    "WARNING","RUNTIME-DUPLICATE-RULE",
                    f"exact duplicate {framework.upper()} rule also appears at {prior}",
                    intent_id=iid,entry_index=index,
                ))
            else:
                rendered_seen[framework][rkey]=f"{iid}[{index}]"

            if framework=="bos":
                section=tuple(entry.get("conditions") or [])
                swaps=tuple(form_ref(x) for x in entry["swap"])
                for base in entry["base"]:
                    bkey=form_ref(base)
                    skey=(bkey,section)
                    prior_swaps=bos_targets["map"].get(skey)
                    if prior_swaps is not None and prior_swaps!=swaps:
                        findings.append(finding(
                            "ERROR","BOS-AMBIGUOUS-BASE-SWAP",
                            f"BOS base {bkey} under conditions {list(section)!r} "
                            f"maps to both {list(prior_swaps)!r} and {list(swaps)!r}",
                            intent_id=iid,entry_index=index,
                        ))
                    else:
                        bos_targets["map"][skey]=swaps

                if (
                    not entry.get("conditions")
                    and not entry.get("properties_raw")
                    and not entry.get("chance_raw")
                    and len(entry["base"])==1
                    and len(entry["swap"])==1
                ):
                    source=form_ref(entry["base"][0])
                    target=form_ref(entry["swap"][0])
                    existing=bos_edges.get(source)
                    if existing is not None and existing!=target:
                        findings.append(finding(
                            "ERROR","BOS-AMBIGUOUS-UNCONDITIONAL-SWAP",
                            f"unconditional BOS base {source} maps to both "
                            f"{existing} and {target}",
                            intent_id=iid,entry_index=index,
                        ))
                    else:
                        bos_edges[source]=target

    cycle=detect_cycle(bos_edges)
    if cycle:
        findings.append(finding(
            "ERROR","BOS-SWAP-CYCLE",
            "unconditional one-to-one BOS swap cycle: "+" -> ".join(cycle),
        ))

    errors=sum(x["severity"]=="ERROR" for x in findings)
    warnings=sum(x["severity"]=="WARNING" for x in findings)
    status="fail" if errors else ("needs-review" if warnings else "pass")
    report={
        "schema_version":"skyrim-runtime-patch-bundle-report-v1",
        "status":status,
        "intents":rows,
        "findings":findings,
        "coverage":{
            "intents":len(intents),
            "spid_entries":counts["spid"],
            "kid_entries":counts["kid"],
            "bos_entries":counts["bos"],
        },
    }
    errors=schema_errors(report,REPORT_SCHEMA)
    if errors:
        raise ValueError(
            "runtime bundle report failed schema validation: "+"; ".join(errors)
        )
    return report

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("intent",type=Path,nargs="+")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    try:
        report=validate_bundle([load(x) for x in args.intent])
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
