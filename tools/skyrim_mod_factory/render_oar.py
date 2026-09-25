#!/usr/bin/env python3
"""Render typed Open Animation Replacer author configs.

Pinned parser evidence:
ersh1/OpenAnimationReplacer src/Parsing.cpp and src/ReplacerMods.cpp,
snapshot f4e7688b065175aff70aa523073857911e15aca3.

This baseline writes only author-owned config.json files. It never generates
user.json, copies HKX files, or invents condition-specific argument schemas.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SCHEMA=REPO/"schemas"/"skyrim-runtime-patch-intent-v1.schema.json"

def schema_errors(value:dict[str,Any])->list[str]:
    schema=json.loads(SCHEMA.read_text(encoding="utf-8"))
    out=[]
    for err in Draft202012Validator(schema).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def safe_relative_directory(raw:str)->Path:
    normalized=raw.replace("\\","/")
    pure=PurePosixPath(normalized)
    if pure.is_absolute() or not pure.parts or any(x in {"",".."} for x in pure.parts):
        raise ValueError(f"unsafe OAR submod directory: {raw!r}")
    if any(":" in x for x in pure.parts):
        raise ValueError(f"OAR submod directory must be relative: {raw!r}")
    return Path(*pure.parts)

def root_config(data:dict[str,Any])->dict[str,Any]:
    meta=data.get("oar")
    if not isinstance(meta,dict) or not meta.get("name"):
        raise ValueError("framework=oar requires root oar.name metadata")
    out={"name":meta["name"]}
    if meta.get("author") is not None:
        out["author"]=meta["author"]
    if meta.get("description") is not None:
        out["description"]=meta["description"]
    return out

def submod_config(entry:dict[str,Any])->dict[str,Any]:
    if entry.get("kind")!="OARSubmod":
        raise ValueError("OAR entries must use kind=OARSubmod")
    out={
        "name":entry["name"],
        "priority":entry["priority"],
        "conditions":entry["conditions"],
    }
    mapping=[
        ("description","description"),
        ("disabled","disabled"),
        ("override_animations_folder","overrideAnimationsFolder"),
        ("required_behavior_project_name","requiredBehaviorProjectName"),
        ("interruptible","interruptible"),
        ("replace_on_loop","replaceOnLoop"),
        ("replace_on_echo","replaceOnEcho"),
        ("paired_conditions","pairedConditions"),
    ]
    for source,target in mapping:
        if source in entry:
            out[target]=entry[source]
    return out

def render_files(data:dict[str,Any])->dict[str,dict[str,Any]]:
    errors=schema_errors(data)
    if errors:
        raise ValueError("intent failed schema validation: "+"; ".join(errors))
    if data.get("framework")!="oar":
        raise ValueError("render_oar.py only accepts framework=oar")

    files={"config.json":root_config(data)}
    seen=set()
    for entry in data["entries"]:
        rel=safe_relative_directory(entry["directory"])
        key=(rel/"config.json").as_posix()
        folded=key.casefold()
        if folded in seen:
            raise ValueError(f"duplicate OAR submod config path: {key}")
        seen.add(folded)
        files[key]=submod_config(entry)
    return files

def serialize(value:dict[str,Any])->str:
    return json.dumps(value,indent=2,ensure_ascii=False)+"\n"

def write_files(files:dict[str,dict[str,Any]],output_dir:Path)->list[Path]:
    written=[]
    for rel,value in sorted(files.items(),key=lambda x:x[0].casefold()):
        target=output_dir/Path(rel)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(serialize(value),encoding="utf-8")
        written.append(target)
    return written

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("intent",type=Path)
    ap.add_argument("--output-dir",type=Path)
    ap.add_argument("--validate-only",action="store_true")
    args=ap.parse_args()

    data=json.loads(args.intent.read_text(encoding="utf-8"))
    try:
        files=render_files(data)
    except ValueError as exc:
        print(str(exc),file=sys.stderr)
        raise SystemExit(1)

    if args.validate_only:
        print(json.dumps(files,indent=2,ensure_ascii=False))
        return
    if args.output_dir is None:
        raise SystemExit("Specify --output-dir for OAR author config tree")
    written=write_files(files,args.output_dir)
    for path in written:
        print(path)

if __name__=="__main__":
    main()
