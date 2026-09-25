#!/usr/bin/env python3
"""Preflight a Skyrim Mod Factory toolchain lock before generation begins."""
from __future__ import annotations
import argparse, hashlib, json, os
from pathlib import Path

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def issue(items, severity, code, message, **extra):
    row={"severity":severity,"code":code,"message":message}
    row.update(extra); items.append(row)

def audit(lock, quality=None, manifest=None, check_files=True):
    items=[]
    if lock.get("schema_version")!="skyrim-toolchain-lock-v1":
        issue(items,"error","LOCK_SCHEMA","Expected skyrim-toolchain-lock-v1")
    adapters=lock.get("adapters") or []
    seen=set()
    for a in adapters:
        aid=a.get("adapter_id")
        if not aid:
            issue(items,"error","ADAPTER_ID_MISSING","Adapter entry has no adapter_id")
            continue
        if aid in seen:
            issue(items,"error","ADAPTER_DUPLICATE",f"Duplicate adapter lock: {aid}",adapter_id=aid)
        seen.add(aid)
        exe=a.get("executable")
        if check_files and exe:
            p=Path(os.path.expandvars(os.path.expanduser(exe)))
            if not p.exists():
                issue(items,"error" if a.get("required") else "warning","EXECUTABLE_MISSING",f"{aid}: executable not found: {p}",adapter_id=aid)
            elif not p.is_file():
                issue(items,"error","EXECUTABLE_NOT_FILE",f"{aid}: executable path is not a file: {p}",adapter_id=aid)
            elif a.get("sha256"):
                actual=sha256(p)
                if actual.lower()!=a["sha256"].lower():
                    issue(items,"error","EXECUTABLE_HASH_MISMATCH",f"{aid}: SHA-256 does not match lock",adapter_id=aid,expected=a["sha256"],actual=actual)
        if a.get("required") and not (a.get("version") or a.get("source_ref")):
            issue(items,"warning","UNPINNED_REQUIRED_ADAPTER",f"{aid}: required adapter has neither version nor source_ref",adapter_id=aid)

    if quality:
        for aid in quality.get("adapters",{}).get("preferred",[]):
            if aid not in seen:
                issue(items,"warning","PREFERRED_ADAPTER_UNLOCKED",f"Preferred adapter is not in toolchain lock: {aid}",adapter_id=aid)

    if manifest:
        explicit=(manifest.get("automation") or {}).get("preferred_adapters",[])
        for aid in explicit:
            if aid not in seen:
                issue(items,"error","EXPLICIT_ADAPTER_UNLOCKED",f"Manifest explicitly requests adapter not present in lock: {aid}",adapter_id=aid)
        layers=set(manifest.get("layers") or [])
        rt=lock.get("runtime") or {}
        if "native" in layers:
            for key in ("game_runtime","skse_version","address_library_version"):
                if not rt.get(key):
                    issue(items,"error","NATIVE_RUNTIME_UNPINNED",f"Native layer requires runtime.{key} to be pinned",field=key)
        if "world" in layers or "navmesh" in layers or "quest-dialogue" in layers:
            if not rt.get("creation_kit_version"):
                issue(items,"warning","CK_VERSION_UNPINNED","Editor-owned content is declared but Creation Kit version is not pinned")
        targets=manifest.get("targets") or []
        if "other" in targets and not rt.get("game_runtime"):
            issue(items,"error","OTHER_RUNTIME_UNRESOLVED","Target 'other' requires an exact runtime in the toolchain lock")

    roots=[Path(os.path.expandvars(os.path.expanduser(x))) for x in lock.get("generated_output_roots") or []]
    normalized=[str(x).replace("\\","/").rstrip("/").lower() for x in roots]
    if len(normalized)!=len(set(normalized)):
        issue(items,"error","OUTPUT_ROOT_DUPLICATE","Generated output roots contain duplicates")
    for raw,norm in zip(lock.get("generated_output_roots") or [],normalized):
        if norm.endswith("/data") or norm.endswith("skyrim special edition"):
            issue(items,"error","UNSAFE_OUTPUT_ROOT",f"Generated output root points at game/Data root: {raw}")
        if norm.endswith("/mods") or norm.endswith("/overwrite"):
            issue(items,"warning","BROAD_OUTPUT_ROOT",f"Generated output root is a broad mod-manager root; prefer a dedicated child folder: {raw}")

    errors=sum(1 for x in items if x["severity"]=="error")
    warnings=sum(1 for x in items if x["severity"]=="warning")
    return {
      "schema_version":"skyrim-toolchain-doctor-report-v1",
      "project_id":lock.get("project_id"),
      "status":"fail" if errors else ("warn" if warnings else "pass"),
      "errors":errors,"warnings":warnings,
      "locked_adapters":sorted(seen),
      "issues":items
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("lock",type=Path)
    ap.add_argument("--quality-plan",type=Path)
    ap.add_argument("--manifest",type=Path)
    ap.add_argument("--no-file-check",action="store_true")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    lock=json.loads(args.lock.read_text(encoding="utf-8"))
    quality=json.loads(args.quality_plan.read_text(encoding="utf-8")) if args.quality_plan else None
    manifest=json.loads(args.manifest.read_text(encoding="utf-8")) if args.manifest else None
    report=audit(lock,quality,manifest,not args.no_file_check)
    text=json.dumps(report,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    else:
        print(text,end="")
    if report["status"]=="fail":
        raise SystemExit(2)

if __name__=="__main__":
    main()
