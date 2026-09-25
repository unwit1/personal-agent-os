#!/usr/bin/env python3
"""Run the pinned Mutagen semantic oracle and validate its typed output."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
PROJECT=HERE/"mutagen_semantic_oracle/MutagenSemanticOracle.csproj"
SCHEMA=REPO/"schemas/skyrim-semantic-plugin-v1.schema.json"

def schema_errors(value:dict[str,Any])->list[str]:
    schema=json.loads(SCHEMA.read_text(encoding="utf-8"))
    out=[]
    for err in Draft202012Validator(schema).iter_errors(value):
        loc=".".join(str(x) for x in err.absolute_path) or "<root>"
        out.append(f"{loc}: {err.message}")
    return out

def build_command(
    plugin:Path,
    output:Path,
    *,
    release:str="SkyrimSE",
    dotnet:str="dotnet",
)->list[str]:
    if release not in {"SkyrimSE","SkyrimLE","SkyrimVR"}:
        raise ValueError("release must be SkyrimSE, SkyrimLE, or SkyrimVR")
    return [
        dotnet,"run","--project",str(PROJECT),"--configuration","Release","--",
        str(plugin),str(output),release,
    ]

def run_oracle(
    plugin:Path,
    output:Path,
    *,
    release:str="SkyrimSE",
    dotnet:str="dotnet",
    timeout_seconds:int=900,
)->dict[str,Any]:
    if not plugin.is_file():
        raise ValueError(f"plugin not found: {plugin}")
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():
        output.unlink()
    command=build_command(plugin,output,release=release,dotnet=dotnet)
    try:
        proc=subprocess.run(
            command,
            cwd=str(REPO),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError(
            f"Mutagen semantic oracle timed out after {timeout_seconds} seconds"
        ) from exc
    if proc.returncode!=0:
        raise ValueError(
            f"Mutagen semantic oracle failed with exit code {proc.returncode}; "
            f"stderr={proc.stderr[-3000:]!r}"
        )
    if not output.exists():
        raise ValueError("Mutagen semantic oracle exited successfully without output")
    document=json.loads(output.read_text(encoding="utf-8"))
    errors=schema_errors(document)
    if errors:
        raise ValueError(
            "Mutagen semantic oracle output failed schema validation: "
            +"; ".join(errors)
        )
    return {
        "command":command,
        "exit_code":proc.returncode,
        "stdout":proc.stdout,
        "stderr":proc.stderr,
        "document":document,
    }

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("plugin",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--release",default="SkyrimSE")
    ap.add_argument("--dotnet",default="dotnet")
    ap.add_argument("--timeout-seconds",type=int,default=900)
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()
    try:
        command=build_command(
            args.plugin,args.output,release=args.release,dotnet=args.dotnet
        )
        if not args.execute:
            print(json.dumps({"dry_run":True,"command":command},indent=2))
            return
        result=run_oracle(
            args.plugin,
            args.output,
            release=args.release,
            dotnet=args.dotnet,
            timeout_seconds=args.timeout_seconds,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps({
        "output":str(args.output),
        "records":len(result["document"].get("records",[])),
        "producer":result["document"].get("provenance",{}).get("producer"),
    },indent=2))

if __name__=="__main__":
    main()
