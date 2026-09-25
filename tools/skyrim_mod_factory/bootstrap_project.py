#!/usr/bin/env python3
"""Bootstrap a Skyrim Mod Factory project workspace."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

DEFAULT_GATES=["G00","G01","G02","G03","G05","G11","G18","G19","G23"]

def slugify(value:str)->str:
    s=re.sub(r"[^a-z0-9._-]+","-",value.lower()).strip("-")
    if not s:
        raise SystemExit("Could not derive project id")
    return s

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root",type=Path)
    ap.add_argument("--name",required=True)
    ap.add_argument("--project-id")
    ap.add_argument("--target",action="append",default=["ae-steam"])
    ap.add_argument("--layer",action="append",default=["records"])
    ap.add_argument("--plugin-kind",default="esp",choices=["none","esp","esm","esl","esp-fe","generated"])
    args=ap.parse_args()

    root=args.root.resolve()
    root.mkdir(parents=True,exist_ok=True)
    pid=args.project_id or slugify(args.name)

    dirs=[
      "src/plugin","src/papyrus","src/native","src/tools",
      "configs","assets/source","assets/generated",
      "tests/fixtures","tests/reports","generated","dist","docs"
    ]
    for d in dirs:
        (root/d).mkdir(parents=True,exist_ok=True)

    gates=list(DEFAULT_GATES)
    layer_gates={
      "papyrus":["G07","G08"],
      "native":["G09","G10"],
      "mesh":["G12"],
      "texture":["G13"],
      "animation":["G14"],
      "behavior":["G14"],
      "world":["G15"],
      "navmesh":["G15"],
      "quest-dialogue":["G16"],
      "lod":["G17"],
      "save-persistence":["G21"],
      "installer":["G22"]
    }
    for layer in args.layer:
        for g in layer_gates.get(layer,[]):
            if g not in gates: gates.append(g)

    outputs=[]
    if args.plugin_kind!="none":
        ext={"esm":".esm","esl":".esl","esp":".esp","esp-fe":".esp","generated":".esp"}[args.plugin_kind]
        outputs.append({"path":f"generated/{pid}{ext}","type":"plugin","generated":True,"generator":"TBD"})
    if "papyrus" in args.layer:
        outputs.append({"path":"generated/Scripts","type":"pex","generated":True,"generator":"Papyrus compiler"})
    if "native" in args.layer:
        outputs.append({"path":f"generated/SKSE/Plugins/{pid}.dll","type":"dll","generated":True,"generator":"CMake/CommonLib"})

    manifest={
      "schema_version":"skyrim-mod-project-v1",
      "project_id":pid,
      "name":args.name,
      "summary":"",
      "targets":list(dict.fromkeys(args.target)),
      "plugin_policy":{
        "kind":args.plugin_kind,
        "masters":["Skyrim.esm","Update.esm"],
        "allow_formid_compaction":False,
        "localized":False
      },
      "layers":list(dict.fromkeys(args.layer)),
      "frameworks":[],
      "dependency_lock":"dependencies.lock.json",
      "inputs":[],
      "outputs":outputs or [{"path":"dist/.keep","type":"other","generated":True,"generator":"project"}],
      "persistence":{
        "uses_save_state":"save-persistence" in args.layer,
        "uses_skse_cosave":False,
        "uses_external_state":False,
        "supports_upgrade":False,
        "supports_uninstall":False
      },
      "compatibility":{
        "records_touched":[],
        "assets_touched":[],
        "runtime_mutators":[],
        "known_conflicts":[],
        "patch_strategy":""
      },
      "validation":{
        "required_gates":gates,
        "warnings_as_errors":False,
        "runtime_tests":["new-game smoke test"],
        "human_checks":[]
      },
      "release":{
        "license":"",
        "fomod":"installer" in args.layer,
        "source_release":True,
        "debug_symbols":"native" in args.layer
      }
    }
    (root/"mod.project.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")

    dependency_lock={
      "schema_version":"skyrim-dependency-lock-v1",
      "project_id":pid,
      "generated_at":"UNRESOLVED",
      "dependencies":[]
    }
    (root/"dependencies.lock.json").write_text(json.dumps(dependency_lock,indent=2)+"\n",encoding="utf-8")

    gitignore="""# generated/build output
generated/
dist/
build/
tests/reports/

# local tools/game paths
.local/
*.log
*.tmp

# keep source assets/configs tracked
"""
    (root/".gitignore").write_text(gitignore,encoding="utf-8")

    readme=f"""# {args.name}

Project ID: `{pid}`

This project was bootstrapped for the Skyrim Mod Factory.

## Source vs generated

- `src/` — authored source.
- `configs/` — authored runtime/tool configuration.
- `assets/source/` — canonical editable assets.
- `assets/generated/` — derived assets if intentionally tracked.
- `generated/` — rebuildable output; not source of truth.
- `tests/fixtures/` — regression fixtures/metadata.
- `dist/` — release staging.

## First commands

Validate:
`python <agent-os>/tools/skyrim_mod_factory/validate_project.py mod.project.json`

Plan:
`python <agent-os>/tools/skyrim_mod_factory/plan_project.py mod.project.json`

Fill in the project manifest and `dependencies.lock.json` before implementation.
"""
    (root/"README.md").write_text(readme,encoding="utf-8")
    print(f"Bootstrapped {args.name} at {root}")

if __name__=="__main__":
    main()
