#!/usr/bin/env python3
"""Validate Skyrim Mod Factory adapter manifests without external dependencies."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

MODES={"cli","library","gui-supervised","hybrid","service","mcp","mcp-stdio","mcp-http","rest","named-pipe","in-process-api"}
ID_RE=re.compile(r"^[a-z0-9][a-z0-9._-]*$")

def validate_manifest(path:Path,data:dict)->list[str]:
    errors=[]
    if data.get("schema_version")!="skyrim-tool-adapter-v1":
        errors.append("schema_version must be skyrim-tool-adapter-v1")
    aid=data.get("adapter_id")
    if not isinstance(aid,str) or not ID_RE.fullmatch(aid):
        errors.append("adapter_id missing or invalid")
    if not isinstance(data.get("tool"),str) or not data.get("tool"):
        errors.append("tool missing")
    caps=data.get("capabilities")
    if not isinstance(caps,list) or not caps or len(caps)!=len(set(caps)):
        errors.append("capabilities must be a non-empty unique list")
    inv=data.get("invocation")
    if not isinstance(inv,dict) or inv.get("mode") not in MODES:
        errors.append("invocation.mode missing/invalid")
    elif inv.get("mode")=="cli" and not inv.get("executable"):
        # Individual descriptive manifests may describe a CLI without a local executable
        # only when transport documents discovery; otherwise adapter is not executable.
        if not inv.get("transport"):
            errors.append("cli adapter needs executable or transport description")
    ev=data.get("evidence")
    if not isinstance(ev,dict) or not ev.get("source_url") or not ev.get("verified_date"):
        errors.append("evidence.source_url and verified_date are required")
    return errors

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("path",type=Path)
    args=ap.parse_args()
    paths=sorted(args.path.glob("*.json")) if args.path.is_dir() else [args.path]
    errors=[]; ids={}
    validated=0; registries=0
    for path in paths:
        data=json.loads(path.read_text(encoding="utf-8"))
        # Aggregate execution registry: validate runnable entry basics too.
        if isinstance(data,dict) and isinstance(data.get("adapters"),list):
            registries+=1
            seen=set()
            for idx,entry in enumerate(data.get("adapters",[])):
                label=f"{path}: adapters[{idx}]"
                if not isinstance(entry,dict):
                    errors.append(f"{label}: entry must be object"); continue
                aid=entry.get("adapter_id")
                if not isinstance(aid,str) or not ID_RE.fullmatch(aid):
                    errors.append(f"{label}: adapter_id missing or invalid")
                elif aid in seen:
                    errors.append(f"{label}: duplicate adapter_id {aid}")
                else:
                    seen.add(aid)
                if not entry.get("tool"):
                    errors.append(f"{label}: tool missing")
                caps=entry.get("capabilities")
                if not isinstance(caps,list) or not caps or len(caps)!=len(set(caps)):
                    errors.append(f"{label}: capabilities must be a non-empty unique list")
                inv=entry.get("invocation")
                if not isinstance(inv,dict) or inv.get("mode") not in {"cli","hybrid"} or not inv.get("executable"):
                    errors.append(f"{label}: runnable invocation needs cli/hybrid mode and executable")
                ev=entry.get("evidence")
                if not isinstance(ev,dict) or not ev.get("source_url") or not ev.get("verified_date"):
                    errors.append(f"{label}: evidence.source_url and verified_date are required")
            continue
        validated+=1
        for e in validate_manifest(path,data):
            errors.append(f"{path}: {e}")
        aid=data.get("adapter_id")
        if aid:
            if aid in ids: errors.append(f"duplicate adapter_id {aid}: {ids[aid]} and {path}")
            ids[aid]=path
    result={"valid":not errors,"manifests":validated,"aggregate_registries":registries,"errors":errors}
    print(json.dumps(result,indent=2))
    sys.exit(1 if errors else 0)

if __name__=="__main__":
    main()
