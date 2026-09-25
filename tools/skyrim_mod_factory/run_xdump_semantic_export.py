#!/usr/bin/env python3
"""Run xDump on one plugin and normalize the fresh decoded text into semantic JSON."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any

HERE=Path(__file__).resolve().parent

def load_module(name:str,path:Path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

NORMALIZE=load_module("normalize_xdump_semantic",HERE/"normalize_xdump_semantic.py")

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def build_command(
    xdump:Path,
    plugin:Path,
    *,
    game_mode:str="SSE",
    data_path:Path|None=None,
    record_filter:list[str]|None=None,
)->list[str]:
    cmd=[str(xdump),"-Dump",f"-{game_mode.upper()}"]
    if data_path is not None:
        cmd.append(f"-d:{data_path}")
    if record_filter:
        cleaned=[]
        for value in record_filter:
            sig=value.strip().upper()
            if len(sig)!=4 or not sig.replace("_","A").isalnum():
                raise ValueError(f"invalid xDump record signature: {value!r}")
            cleaned.append(sig)
        cmd.append("-dr:"+",".join(cleaned))
    cmd.append(str(plugin))
    return cmd

def run_export(
    xdump:Path,
    plugin:Path,
    raw_output:Path,
    semantic_output:Path,
    *,
    game_mode:str="SSE",
    game_release:str="skyrim-se-ae",
    data_path:Path|None=None,
    record_filter:list[str]|None=None,
    load_order_map:dict[str,Any]|None=None,
    load_order_sha256:str|None=None,
    timeout_seconds:int=900,
)->dict[str,Any]:
    if not xdump.is_file():
        raise ValueError(f"xDump executable not found: {xdump}")
    if not plugin.is_file():
        raise ValueError(f"plugin not found: {plugin}")
    raw_output.parent.mkdir(parents=True,exist_ok=True)
    semantic_output.parent.mkdir(parents=True,exist_ok=True)
    for path in (raw_output,semantic_output):
        if path.exists():
            path.unlink()

    command=build_command(
        xdump,plugin,game_mode=game_mode,data_path=data_path,
        record_filter=record_filter,
    )
    try:
        proc=subprocess.run(
            command,
            cwd=str(xdump.parent),
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
            f"xDump semantic export timed out after {timeout_seconds} seconds"
        ) from exc

    raw_output.write_text(proc.stdout,encoding="utf-8")
    if proc.returncode!=0:
        raise ValueError(
            f"xDump failed with exit code {proc.returncode}: {proc.stderr[-2000:]!r}"
        )
    if not proc.stdout.strip():
        raise ValueError("xDump completed without decoded stdout")

    document=NORMALIZE.parse_xdump(
        proc.stdout,
        plugin=plugin.name,
        game_release=game_release,
        source_plugin_sha256=sha256(plugin),
        load_order_sha256=load_order_sha256,
        load_order_map=load_order_map,
    )
    semantic_output.write_text(
        json.dumps(document,indent=2)+"\n",
        encoding="utf-8",
    )
    return {
        "command":command,
        "exit_code":proc.returncode,
        "stdout_path":str(raw_output),
        "semantic_output":str(semantic_output),
        "stderr":proc.stderr,
        "document":document,
    }

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("xdump",type=Path)
    ap.add_argument("plugin",type=Path)
    ap.add_argument("--raw-output",type=Path,required=True)
    ap.add_argument("--semantic-output",type=Path,required=True)
    ap.add_argument("--game-mode",default="SSE")
    ap.add_argument("--game-release",default="skyrim-se-ae")
    ap.add_argument("--data-path",type=Path)
    ap.add_argument("--record",action="append",default=[])
    ap.add_argument("--load-order-map",type=Path)
    ap.add_argument("--load-order-sha256")
    ap.add_argument("--timeout-seconds",type=int,default=900)
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()

    load_map=(
        json.loads(args.load_order_map.read_text(encoding="utf-8"))
        if args.load_order_map else None
    )
    command=build_command(
        args.xdump,args.plugin,game_mode=args.game_mode,
        data_path=args.data_path,record_filter=args.record,
    )
    if not args.execute:
        print(json.dumps({"dry_run":True,"command":command},indent=2))
        return

    try:
        result=run_export(
            args.xdump,args.plugin,args.raw_output,args.semantic_output,
            game_mode=args.game_mode,game_release=args.game_release,
            data_path=args.data_path,record_filter=args.record,
            load_order_map=load_map,load_order_sha256=args.load_order_sha256,
            timeout_seconds=args.timeout_seconds,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps({
        "semantic_output":result["semantic_output"],
        "record_count":len(result["document"].get("records") or []),
        "canonical_formkeys":result["document"].get("provenance",{}).get(
            "canonical_cross_load_order_form_keys"
        ),
    },indent=2))

if __name__=="__main__":
    main()
