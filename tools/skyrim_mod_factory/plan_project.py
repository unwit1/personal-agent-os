#!/usr/bin/env python3
"""Generate a deterministic first-pass Skyrim Mod Factory build plan from a project manifest."""
from __future__ import annotations
import argparse, json
from pathlib import Path

LAYER_TASKS={
"records":[("generate-plugin","Generate/patch plugin records"),("validate-plugin","Run schema/master/FormID checks")],
"runtime-patching":[("generate-runtime-configs","Generate runtime patch/distribution configs"),("validate-runtime-configs","Parse and resolve runtime configs")],
"papyrus":[("compile-papyrus","Compile Papyrus source"),("audit-papyrus","Check lifecycle/persistence/dependencies")],
"native":[("build-native","Build all native runtime targets"),("audit-native","Check plugin metadata, relocations and dependencies")],
"ui":[("validate-ui","Validate menu identifiers, paths and input behavior")],
"animation":[("validate-animation","Validate animation paths/OAR conditions/skeleton dependencies")],
"behavior":[("generate-behavior","Run behavior generator"),("validate-behavior","Parse generator log and output graph")],
"mesh":[("validate-mesh","Validate NIF/skinning/partitions/bounds/collision")],
"texture":[("validate-textures","Validate formats, paths, mipmaps and material expectations")],
"physics":[("validate-physics","Validate nodes/collision/constraints/framework dependencies")],
"world":[("validate-world","Validate CELL/WRLD/LAND/reference interactions")],
"navmesh":[("validate-navmesh","Check NAVM integrity and require CK/game traversal test")],
"quest-dialogue":[("validate-quest","Validate aliases/stages/VMAD/INFO/scenes/Story Manager")],
"audio":[("validate-audio","Validate VoiceType/voice paths/audio formats")],
"lod":[("generate-lod","Run applicable LOD generators"),("validate-lod","Parse logs and verify output freshness")],
"installer":[("build-installer","Build staging/FOMOD/archive"),("validate-installer","Validate schema and option paths")],
"save-persistence":[("test-save-migration","Test new game/save-load/upgrade persistence")],
"compatibility":[("compatibility-scan","Compare touch set against load order/runtime mutators")]
}

def add(tasks,id,description,depends=None):
    if any(t["id"]==id for t in tasks): return
    tasks.append({"id":id,"description":description,"depends_on":depends or []})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    m=json.loads(args.manifest.read_text(encoding="utf-8"))
    tasks=[]
    add(tasks,"validate-manifest","Validate project manifest")
    add(tasks,"lock-sources","Resolve/pin tools, frameworks, runtime and input hashes",["validate-manifest"])
    previous=["lock-sources"]
    for layer in m.get("layers",[]):
        for tid,desc in LAYER_TASKS.get(layer,[]):
            add(tasks,tid,desc,list(previous))
            previous=[tid]
    add(tasks,"run-gates","Evaluate required validation gates",list(previous))
    add(tasks,"smoke-test","Launch configured smoke-test profile and collect logs",["run-gates"])
    add(tasks,"build-report","Write provenance/build/gate report",["smoke-test"])
    add(tasks,"release-audit","Check release reproducibility and remaining human checks",["build-report"])

    result={
      "schema_version":"skyrim-mod-plan-v1",
      "project_id":m.get("project_id"),
      "targets":m.get("targets",[]),
      "tasks":tasks,
      "required_gates":(m.get("validation") or {}).get("required_gates",[]),
      "human_checks":(m.get("validation") or {}).get("human_checks",[])
    }
    text=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    else:
        print(text,end="")

if __name__=="__main__":
    main()
