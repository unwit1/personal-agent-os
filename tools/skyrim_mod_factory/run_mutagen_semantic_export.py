#!/usr/bin/env python3
"""Run the pinned Mutagen semantic exporter and validate its typed JSON output."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
DEFAULT_PROJECT=HERE/"mutagen_semantic_export"/"mutagen_semantic_export.csproj"
SCHEMA=REPO/"schemas"/"skyrim-semantic-plugin-v1.schema.json"

def schema_errors(value:dict[str,Any])->list[str]:
    schema=json.loads(SCHEMA.read_text(encoding="utf-8"))
    out=[]
    for err in Draft202012Validator(schema).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def build_command(
    dotnet:str,
    project:Path,
    plugin:Path,
    output:Path,
    release:str,
)->list[str]:
    return [
        dotnet,
        "run",
        "--project",str(project),
        "--configuration","Release",
        "--",
        str(plugin),
        str(output),
        release,
    ]

def run_export(
    plugin:Path,
    output:Path,
    *,
    project:Path=DEFAULT_PROJECT,
    dotnet:str="dotnet",
    release:str="SkyrimSE",
    timeout_seconds:int=900,
)->dict[str,Any]:
    if not plugin.is_file():
        raise ValueError(f"plugin not found: {plugin}")
    if not project.is_file():
        raise ValueError(f"Mutagen exporter project not found: {project}")
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():
        output.unlink()

    command=build_command(dotnet,project,plugin,output,release)
    try:
        proc=subprocess.run(
            command,
            cwd=str(project.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(
            f"Mutagen semantic export timed out after {timeout_seconds} seconds"
        ) from exc

    if proc.returncode!=0:
        raise ValueError(
            f"Mutagen semantic exporter failed with exit code {proc.returncode}: "
            f"{proc.stderr[-2000:]!r}"
        )
    if not output.is_file():
        raise ValueError(
            "Mutagen semantic exporter exited successfully but did not create output"
        )

    try:
        document=json.loads(output.read_text(encoding="utf-8"))
    except (OSError,UnicodeError,json.JSONDecodeError) as exc:
        raise ValueError(f"Mutagen semantic output is not valid UTF-8 JSON: {exc}") from exc

    errors=schema_errors(document)
    if errors:
        raise ValueError(
            "Mutagen semantic output failed schema validation: "
            +"; ".join(errors)
        )
    provenance=document.get("provenance") or {}
    if provenance.get("producer")!="mutagen-semantic-export":
        raise ValueError("Mutagen semantic output has unexpected producer provenance")
    if provenance.get("form_key_mode")!="mutagen-formkey-string":
        raise ValueError("Mutagen semantic output does not declare canonical FormKey mode")
    if provenance.get("canonical_cross_load_order_form_keys") is not True:
        raise ValueError("Mutagen semantic output does not declare canonical record identity")

    return {
        "command":command,
        "exit_code":proc.returncode,
        "stdout":proc.stdout,
        "stderr":proc.stderr,
        "output":str(output),
        "document":document,
    }

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("plugin",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--project",type=Path,default=DEFAULT_PROJECT)
    ap.add_argument("--dotnet",default="dotnet")
    ap.add_argument("--release",default="SkyrimSE")
    ap.add_argument("--timeout-seconds",type=int,default=900)
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()

    command=build_command(
        args.dotnet,args.project,args.plugin,args.output,args.release
    )
    if not args.execute:
        print(json.dumps({"dry_run":True,"command":command},indent=2))
        return

    try:
        result=run_export(
            args.plugin,
            args.output,
            project=args.project,
            dotnet=args.dotnet,
            release=args.release,
            timeout_seconds=args.timeout_seconds,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps({
        "output":result["output"],
        "record_count":len(result["document"].get("records") or []),
        "producer":result["document"].get("provenance",{}).get("producer"),
    },indent=2))

if __name__=="__main__":
    main()
