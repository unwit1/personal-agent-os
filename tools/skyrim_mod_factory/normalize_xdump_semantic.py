#!/usr/bin/env python3
"""Normalize xEdit/xDump record text into skyrim-semantic-plugin-v1.

Without a load-order map, displayed FormIDs remain explicitly noncanonical.
With a validated load-order map, displayed full/light FormIDs are converted to
Mutagen-compatible six-hex-digit FormKeys (e.g. 012ABC:Skyrim.esm).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMAS=REPO/"schemas"
SEMANTIC_SCHEMA="skyrim-semantic-plugin-v1.schema.json"
LOAD_MAP_SCHEMA="skyrim-load-order-formid-map-v1.schema.json"
PRODUCER_VERSION="1.1"

RECORD_RE=re.compile(
    r"\[(?P<signature>[A-Z0-9_]{4}):(?P<form>[0-9A-Fa-f]{8})\]"
)
ASSET_RE=re.compile(
    r"(?P<path>[^\s\"'<>|]+\.(?:nif|dds|tga|png|wav|xwm|fuz|lip|swf|gfx|"
    r"pex|psc|hkx|tri|bsa))\b",
    re.I,
)
EDID_RE=re.compile(r"(?:^|\\|\s)EDID(?:\s*-\s*Editor ID)?\b",re.I)

def sha256_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def canonical_json_sha256(value:Any)->str:
    payload=json.dumps(
        value,sort_keys=True,separators=(",",":"),ensure_ascii=False
    ).encode("utf-8")
    return sha256_bytes(payload)

def load_schema(name:str)->dict[str,Any]:
    return json.loads((SCHEMAS/name).read_text(encoding="utf-8"))

def schema_errors(value:dict[str,Any],name:str=SEMANTIC_SCHEMA)->list[str]:
    out=[]
    for err in Draft202012Validator(load_schema(name)).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def normalize_load_order_map(value:dict[str,Any])->dict[str,Any]:
    errors=schema_errors(value,LOAD_MAP_SCHEMA)
    if errors:
        raise ValueError("invalid load-order FormID map: "+"; ".join(errors))
    return {
        "schema_version":"skyrim-load-order-formid-map-v1",
        "full":{k.upper():v for k,v in value["full"].items()},
        "light":{k.upper():v for k,v in value["light"].items()},
    }

def displayed_formid_to_formkey(
    form_id:str,
    load_order_map:dict[str,Any],
)->str:
    form=form_id.upper()
    if not re.fullmatch(r"[0-9A-F]{8}",form):
        raise ValueError(f"invalid displayed FormID: {form_id!r}")
    mapping=normalize_load_order_map(load_order_map)
    if form.startswith("FF"):
        raise ValueError(
            f"dynamic FormID {form} cannot be converted to a persisted plugin FormKey"
        )
    if form.startswith("FE"):
        index=form[2:5]
        mod_key=mapping["light"].get(index)
        if not mod_key:
            raise ValueError(
                f"light load-order index {index} for FormID {form} is absent from map"
            )
        local_id=form[5:8].rjust(6,"0")
    else:
        index=form[:2]
        mod_key=mapping["full"].get(index)
        if not mod_key:
            raise ValueError(
                f"full load-order index {index} for FormID {form} is absent from map"
            )
        local_id=form[2:8]
    return f"{local_id}:{mod_key}"

def indentation(raw:str)->int:
    expanded=raw.expandtabs(4)
    return len(expanded)-len(expanded.lstrip(" "))

def split_field(text:str)->tuple[str,str|None]:
    if ": " in text:
        name,value=text.split(": ",1)
        return name.strip(),value.strip()
    return text.strip(),None

def stable_path(
    stack:list[tuple[int,str]],
    indent:int,
    name:str,
)->tuple[list[tuple[int,str]],str]:
    while stack and stack[-1][0]>=indent:
        stack.pop()
    parts=[x[1] for x in stack]+[name]
    stack.append((indent,name))
    return stack," \\ ".join(x for x in parts if x)

def extract_asset_paths(text:str)->list[str]:
    seen=[]
    for match in ASSET_RE.finditer(text):
        path=match.group("path").replace("/","\\")
        if path not in seen:
            seen.append(path)
    return seen

def parse_xdump(
    text:str,
    *,
    plugin:str,
    game_release:str="skyrim-se-ae",
    producer_version:str=PRODUCER_VERSION,
    source_plugin_sha256:str|None=None,
    load_order_sha256:str|None=None,
    load_order_map:dict[str,Any]|None=None,
    created_at:str|None=None,
)->dict[str,Any]:
    normalized_map=(
        normalize_load_order_map(load_order_map)
        if load_order_map is not None else None
    )
    map_sha=canonical_json_sha256(normalized_map) if normalized_map else None
    lines=text.splitlines()
    records=[]
    current=None
    stack:list[tuple[int,str]]=[]
    field_lines=0
    unassigned_nonempty=0
    seen_keys=set()

    def flush()->None:
        nonlocal current
        if current is None:
            return
        key=f'{current["signature"]}:{current["form_key"]}'
        if key in seen_keys:
            current.setdefault("fields",{}).setdefault("_producer_warnings",[]).append(
                "duplicate record identity appeared in xDump text"
            )
        seen_keys.add(key)
        records.append(current)
        current=None

    for line_number,raw in enumerate(lines,1):
        if not raw.strip():
            continue
        body=raw.strip()
        rec=RECORD_RE.search(body)
        if rec:
            flush()
            form=rec.group("form").upper()
            signature=rec.group("signature")
            form_key=(
                displayed_formid_to_formkey(form,normalized_map)
                if normalized_map is not None
                else f"{plugin}|{form}"
            )
            current={
                "form_key":form_key,
                "signature":signature,
                "editor_id":None,
                "fields":{
                    "_xdump":{
                        "record_header":body,
                        "displayed_form_id":form,
                        "ordered_fields":[],
                    }
                },
                "asset_paths":[],
            }
            stack=[]
            continue

        if current is None:
            unassigned_nonempty+=1
            continue

        indent=indentation(raw)
        name,value=split_field(body)
        stack,path=stable_path(stack,indent,name)
        row={
            "line":line_number,
            "indent":indent,
            "path":path,
            "name":name,
            "value":value,
            "raw":body,
        }
        current["fields"]["_xdump"]["ordered_fields"].append(row)
        field_lines+=1

        if EDID_RE.search(name) and value:
            current["editor_id"]=value

        for asset in extract_asset_paths(value or body):
            if asset not in current["asset_paths"]:
                current["asset_paths"].append(asset)

        if "VMAD" in path.upper():
            current.setdefault("vmad",{"xdump_lines":[]})
            current["vmad"]["xdump_lines"].append(row)

    flush()
    if not records:
        raise ValueError(
            "no xEdit-style [SIGNATURE:FORMID] record headers were found in xDump text"
        )

    canonical=normalized_map is not None
    omissions=[
        "record flags are not inferred unless a later typed producer decodes them",
        "localized-string identity is preserved only as displayed text",
        "unknown serialization bytes not printed by xDump are unavailable",
    ]
    if not canonical:
        omissions.insert(
            1,
            "master-relative FormKeys are not reconstructed without a load-order map",
        )
    provenance={
        "producer":"xedit-xdump-text-normalizer",
        "producer_version":producer_version,
        "schema_source":"xEdit/xDump human-readable record tree",
        "created_at":created_at or dt.datetime.now(dt.timezone.utc).isoformat(),
        "form_key_mode":(
            "mutagen-formkey-string"
            if canonical else "target-plugin-plus-load-order-formid"
        ),
        "canonical_cross_load_order_form_keys":canonical,
        "coverage":{
            "input_lines":len(lines),
            "records_emitted":len(records),
            "field_lines_preserved":field_lines,
            "unassigned_nonempty_lines":unassigned_nonempty,
            "semantic_fields":["editor_id","asset_paths"],
            "omissions":omissions,
        },
        "raw_xdump_sha256":sha256_bytes(text.encode("utf-8")),
    }
    if source_plugin_sha256:
        provenance["source_plugin_sha256"]=source_plugin_sha256
    if canonical:
        provenance["load_order_map_sha256"]=map_sha
        provenance["load_order_sha256"]=load_order_sha256 or map_sha
    elif load_order_sha256:
        provenance["load_order_sha256"]=load_order_sha256

    document={
        "schema_version":"skyrim-semantic-plugin-v1",
        "plugin":{
            "mod_key":plugin,
            "game_release":game_release,
        },
        "records":records,
        "provenance":provenance,
    }
    errors=schema_errors(document)
    if errors:
        raise ValueError(
            "normalized xDump semantic document failed schema validation: "
            +"; ".join(errors)
        )
    return document

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("xdump_text",type=Path)
    ap.add_argument("--plugin",required=True)
    ap.add_argument("--game-release",default="skyrim-se-ae")
    ap.add_argument("--producer-version",default=PRODUCER_VERSION)
    ap.add_argument("--source-plugin-sha256")
    ap.add_argument("--load-order-sha256")
    ap.add_argument("--load-order-map",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()

    load_map=(
        json.loads(args.load_order_map.read_text(encoding="utf-8"))
        if args.load_order_map else None
    )
    try:
        document=parse_xdump(
            args.xdump_text.read_text(encoding="utf-8",errors="replace"),
            plugin=args.plugin,
            game_release=args.game_release,
            producer_version=args.producer_version,
            source_plugin_sha256=args.source_plugin_sha256,
            load_order_sha256=args.load_order_sha256,
            load_order_map=load_map,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))

    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(document,indent=2)+"\n",encoding="utf-8")
    print(args.output)

if __name__=="__main__":
    main()
