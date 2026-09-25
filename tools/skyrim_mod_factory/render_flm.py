#!/usr/bin/env python3
"""Render typed FormList Manipulator intent into a *_FLM.ini file.

Grammar source:
MaskedRPGFan/FormList-Manipulator README, snapshot 82a694e5d33194ae223f23846b1f180ee394cdee.

The renderer deliberately emits no INI section header: FLM's documented grammar is
a flat sequence of Keyword = fields records. Definitions are emitted before
operations so generated output does not depend on source-intent ordering.
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
SCHEMA=REPO/"schemas"/"skyrim-runtime-patch-intent-v1.schema.json"

DEFINITION_ORDER={
    "FLMFilter":0,
    "FLMCollection":1,
    "FLMAlias":2,
    "FLMGroup":3,
}
KEYS={
    "FLMFilter":"Filter",
    "FLMCollection":"Collection",
    "FLMAlias":"Alias",
    "FLMGroup":"Group",
    "FLMFormList":"FormList",
    "FLMModEvent":"ModEvent",
    "FLMPlant":"Plant",
    "FLMBToys":"BToys",
    "FLMGToys":"GToys",
    "FLMHairColors":"HairColors",
    "FLMAtronachForge":"AtronachForge",
    "FLMAtronachForgeSigil":"AtronachForgeSigil",
    "FLMDragonbornSpiderCrafting":"DragonbornSpiderCrafting",
}

def schema_errors(value:dict[str,Any])->list[str]:
    schema=json.loads(SCHEMA.read_text(encoding="utf-8"))
    out=[]
    for err in Draft202012Validator(schema).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def form_ref(value:dict[str,Any])->str:
    if value.get("editor_id"):
        return str(value["editor_id"])
    if value.get("form_id") and value.get("plugin"):
        return f'{value["form_id"]}~{value["plugin"]}'
    raise ValueError("FLM form reference requires editor_id or form_id + plugin")

def member_ref(value:dict[str,Any])->str:
    source=value.get("source")
    if source=="form":
        return form_ref(value["form"])
    if source=="formlist_contents":
        return "*"+form_ref(value["form"])
    if source in {"group","collection"}:
        return "#"+str(value["name"])
    raise ValueError(f"unsupported FLM member source: {source!r}")

def target_ref(value:dict[str,Any])->str:
    source=value.get("source")
    if source=="formlist":
        return form_ref(value["form"])
    if source=="alias":
        return "#"+str(value["name"])
    raise ValueError(f"unsupported FLM list target source: {source!r}")

def filter_ref(value:dict[str,Any]|None)->str:
    if not value:
        return ""
    has_name=bool(value.get("name"))
    conditions=value.get("conditions") or []
    if has_name==bool(conditions):
        raise ValueError("FLM filter must contain exactly one of name or conditions")
    if has_name:
        return "#"+str(value["name"])
    return ",".join(str(x) for x in conditions)

def render_entry(entry:dict[str,Any])->str:
    kind=entry.get("kind")
    key=KEYS.get(kind)
    if not key:
        raise ValueError(f"unsupported FLM entry kind: {kind!r}")

    if kind=="FLMFilter":
        fields=[entry["name"],",".join(entry["conditions"])]
    elif kind=="FLMCollection":
        keywords=[
            ("-" if item.get("exclude") else "")+form_ref(item["form"])
            for item in entry["keywords"]
        ]
        fields=[
            entry["name"],
            entry["form_type"],
            ",".join(keywords),
            filter_ref(entry.get("filter")),
        ]
    elif kind=="FLMAlias":
        fields=[entry["name"],",".join(form_ref(x) for x in entry["formlists"])]
    elif kind=="FLMGroup":
        fields=[entry["name"],",".join(member_ref(x) for x in entry["members"])]
    elif kind=="FLMFormList":
        fields=[
            target_ref(entry["target"]),
            ",".join(member_ref(x) for x in entry["members"]),
            filter_ref(entry.get("filter")),
        ]
    elif kind=="FLMModEvent":
        fields=[
            entry["event_name"],
            target_ref(entry["target"]),
            ",".join(member_ref(x) for x in entry["members"]),
        ]
    elif kind in {
        "FLMPlant","FLMAtronachForge","FLMAtronachForgeSigil",
        "FLMDragonbornSpiderCrafting",
    }:
        fields=[
            form_ref(entry["first"]),
            form_ref(entry["second"]),
            filter_ref(entry.get("filter")),
        ]
    elif kind in {"FLMBToys","FLMGToys","FLMHairColors"}:
        fields=[
            ",".join(member_ref(x) for x in entry["members"]),
            filter_ref(entry.get("filter")),
        ]
    else:
        raise ValueError(f"unsupported FLM entry kind: {kind!r}")

    while fields and fields[-1]=="":
        fields.pop()
    return f"{key} = "+"|".join(fields)

def ordered_entries(entries:list[dict[str,Any]])->list[dict[str,Any]]:
    indexed=list(enumerate(entries))
    return [
        entry
        for _,entry in sorted(
            indexed,
            key=lambda pair:(
                0 if pair[1].get("kind") in DEFINITION_ORDER else 1,
                DEFINITION_ORDER.get(pair[1].get("kind"),0),
                pair[0],
            ),
        )
    ]

def render_document(data:dict[str,Any])->str:
    errors=schema_errors(data)
    if errors:
        raise ValueError("intent failed schema validation: "+"; ".join(errors))
    if data.get("framework")!="flm":
        raise ValueError("render_flm.py only accepts framework=flm")

    lines=[
        "; Generated by Skyrim Mod Factory. Edit semantic intent, not this file.",
        f'; intent_id={data.get("intent_id","")}',
        f'; grammar_snapshot={data.get("grammar_source",{}).get("snapshot","")}',
        "",
    ]
    for entry in ordered_entries(data["entries"]):
        comment=entry.get("comment")
        if comment:
            lines.append("; "+str(comment).replace("\n"," "))
        lines.append(render_entry(entry))
    return "\n".join(lines).rstrip()+"\n"

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("intent",type=Path)
    ap.add_argument("--output",type=Path)
    ap.add_argument("--validate-only",action="store_true")
    args=ap.parse_args()

    data=json.loads(args.intent.read_text(encoding="utf-8"))
    try:
        output=render_document(data)
    except ValueError as exc:
        print(str(exc),file=sys.stderr)
        raise SystemExit(1)

    if args.validate_only:
        print(output,end="")
        return
    out=args.output or (Path(data["output_file"]) if data.get("output_file") else None)
    if out is None:
        raise SystemExit("Specify --output or output_file")
    if not out.name.lower().endswith("_flm.ini"):
        raise SystemExit("FLM output filename must end with _FLM.ini")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(output,encoding="utf-8")
    print(out)

if __name__=="__main__":
    main()
