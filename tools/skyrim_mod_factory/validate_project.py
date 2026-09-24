#!/usr/bin/env python3
"""Validate a Skyrim Mod Factory project manifest using only the Python standard library.

This is a fast structural/cross-field validator. A full JSON Schema validator may be
run separately against schemas/skyrim-mod-project-v1.schema.json.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

TARGETS={"se-1.5.97","ae-steam","ae-gog","ae-1.7.x","vr-1.4.15","other"}
LAYERS={"records","runtime-patching","papyrus","native","ui","animation","behavior","mesh",
"texture","physics","world","navmesh","quest-dialogue","audio","lod","installer",
"save-persistence","compatibility"}

def err(errors,msg): errors.append(msg)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    args=ap.parse_args()
    data=json.loads(args.manifest.read_text(encoding="utf-8"))
    errors=[]; warnings=[]

    if data.get("schema_version")!="skyrim-mod-project-v1":
        err(errors,"schema_version must be skyrim-mod-project-v1")
    for k in ("project_id","name","targets","layers","outputs","validation"):
        if k not in data: err(errors,f"missing required field: {k}")

    pid=data.get("project_id","")
    if pid and not re.fullmatch(r"[a-z0-9][a-z0-9._-]*",pid):
        err(errors,"project_id contains unsupported characters")

    targets=data.get("targets",[])
    unknown=set(targets)-TARGETS
    if unknown: err(errors,"unknown targets: "+", ".join(sorted(unknown)))
    if not targets: err(errors,"at least one target is required")

    layers=data.get("layers",[])
    unknown=set(layers)-LAYERS
    if unknown: err(errors,"unknown layers: "+", ".join(sorted(unknown)))

    outputs=data.get("outputs",[])
    paths=[x.get("path") for x in outputs if isinstance(x,dict)]
    if len(paths)!=len(set(paths)): err(errors,"duplicate output paths")

    gates=(data.get("validation") or {}).get("required_gates",[])
    for g in gates:
        if not re.fullmatch(r"G\d{2}",str(g)): err(errors,f"invalid gate id: {g}")

    policy=data.get("plugin_policy") or {}
    kind=policy.get("kind")
    if kind in {"esl","esp-fe"} and policy.get("allow_formid_compaction") is None:
        warnings.append("light plugin project should explicitly state allow_formid_compaction")

    if "native" in layers:
        fw={x.get("id","").lower() for x in data.get("frameworks",[]) if isinstance(x,dict)}
        if not any("skse" in x or "commonlib" in x for x in fw):
            warnings.append("native layer declared without an explicit SKSE/CommonLib framework entry")
        if not any(g in gates for g in ("G09","G10")):
            warnings.append("native project should normally require G09 and G10")

    if "papyrus" in layers and "G07" not in gates:
        warnings.append("Papyrus project should normally require G07")
    if "save-persistence" in layers and "G21" not in gates:
        warnings.append("persistent project should normally require G21")
    if "installer" in layers and "G22" not in gates:
        warnings.append("installer project should normally require G22")
    if "navmesh" in layers and "G15" not in gates:
        warnings.append("navmesh project should normally require G15")
    if "quest-dialogue" in layers and "G16" not in gates:
        warnings.append("quest/dialogue project should normally require G16")

    print(json.dumps({"valid":not errors,"errors":errors,"warnings":warnings},indent=2))
    sys.exit(1 if errors else 0)

if __name__=="__main__":
    main()
