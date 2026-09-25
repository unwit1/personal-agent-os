#!/usr/bin/env python3
"""Compile a parallelizable incremental Skyrim Mod Factory build DAG."""
from __future__ import annotations
import argparse, json
from pathlib import Path

GENERATE={
 "records":("generate.records","Generate/patch typed plugin data",["housecarl","mutagen","spriggit"]),
 "runtime-patching":("generate.runtime-patching","Render runtime patch/distribution configs",[]),
 "papyrus":("generate.papyrus","Build Papyrus project and compile sources",["pyro","official-papyruscompiler","caprica"]),
 "native":("generate.native","Build native SKSE targets",["commonlib-cmake-build"]),
 "ui":("generate.ui","Build/generate UI artifacts",[]),
 "animation":("generate.animation","Stage animation/OAR assets",[]),
 "behavior":("generate.behavior","Generate behavior graph output",["pandora"]),
 "mesh":("generate.mesh","Build/transform NIF/TRI assets",["pynifly","blender-mcp"]),
 "texture":("generate.texture","Build/convert DDS/material inputs",["directxtex"]),
 "physics":("generate.physics","Build physics/collision configuration",["pynifly"]),
 "world":("generate.world","Author/generate world/cell records",["ckpe"]),
 "navmesh":("generate.navmesh","Author/finalize navmesh changes",["ckpe"]),
 "quest-dialogue":("generate.quest-dialogue","Author/generate quests/dialogue/scenes",["ckpe","papyrus-vscode"]),
 "audio":("generate.audio","Generate/convert audio/voice assets",["vospeaker"]),
 "lod":("generate.lod","Generate terrain/object/tree/grass LOD",["xlodgen","dyndolod"]),
 "installer":("generate.installer","Build release staging/installer/archive",[]),
 "save-persistence":("generate.persistence","Build/migrate persistent-state schema",[]),
 "compatibility":("generate.compatibility","Generate compatibility patch/config if required",["synthesis"])
}

VALIDATE={
 "records":("validate.records",["xedit","mutagen","spriggit"]),
 "runtime-patching":("validate.runtime-patching",["xedit"]),
 "papyrus":("validate.papyrus",["caprica","champollion"]),
 "native":("validate.native",["crash-logger"]),
 "ui":("validate.ui",[]),
 "animation":("validate.animation",["pandora"]),
 "behavior":("validate.behavior",["pandora"]),
 "mesh":("validate.mesh",["pynifly"]),
 "texture":("validate.texture",["directxtex"]),
 "physics":("validate.physics",["pynifly"]),
 "world":("validate.world",["xedit"]),
 "navmesh":("validate.navmesh",["xedit","ckpe"]),
 "quest-dialogue":("validate.quest-dialogue",["xedit","papyrus-vscode"]),
 "audio":("validate.audio",[]),
 "lod":("validate.lod",["xlodgen","dyndolod"]),
 "installer":("validate.installer",[]),
 "save-persistence":("validate.persistence",["fallrimtools","resaver-cli"]),
 "compatibility":("validate.compatibility",["xedit","loot","mutagen-analyzers"])
}

def uniq(xs):
    out=[]; seen=set()
    for x in xs:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

def add(nodes, node):
    if any(n["id"]==node["id"] for n in nodes): return
    node["depends_on"]=uniq(node.get("depends_on",[]))
    node["adapters"]=uniq(node.get("adapters",[]))
    node["gates"]=uniq(node.get("gates",[]))
    node["invalidated_by"]=uniq(node.get("invalidated_by",[]))
    node["layers"]=uniq(node.get("layers",[]))
    node["outputs"]=uniq(node.get("outputs",[]))
    nodes.append(node)

def layer_gates(quality, layer):
    reasons=quality.get("reasons",{})
    return [g for g,rs in reasons.items() if any(r==f"layer:{layer}" for r in rs)]

def compile_dag(manifest, quality):
    nodes=[]
    pid=manifest.get("project_id")
    add(nodes,{"id":"preflight.manifest","phase":"preflight","action":"Validate project manifest",
      "depends_on":[],"adapters":[],"gates":["G00"],"invalidated_by":["project manifest"],"layers":[],"outputs":[]})
    add(nodes,{"id":"preflight.quality","phase":"preflight","action":"Derive/validate automatic quality plan",
      "depends_on":["preflight.manifest"],"adapters":[],"gates":["G27"],"invalidated_by":["project manifest","quality planner"],"layers":[],"outputs":[]})
    if manifest.get("dependency_lock"):
        add(nodes,{"id":"preflight.dependencies","phase":"preflight","action":"Validate dependency lock, license and runtime compatibility",
          "depends_on":["preflight.manifest"],"adapters":[],"gates":["G01"],"invalidated_by":["dependency lock"],"layers":[],"outputs":[]})
        tool_deps=["preflight.quality","preflight.dependencies"]
    else:
        tool_deps=["preflight.quality"]
    add(nodes,{"id":"preflight.toolchain","phase":"preflight","action":"Run toolchain doctor and verify pinned environment",
      "depends_on":tool_deps,"adapters":[],"gates":["G01","G25"],"invalidated_by":["toolchain lock","runtime/tool version"],"layers":[],"outputs":[]})
    add(nodes,{"id":"source.lock","phase":"source","action":"Hash and lock source plugins/assets/framework versions",
      "depends_on":["preflight.toolchain"],"adapters":[],"gates":["G01"],"invalidated_by":["source input","tool/framework version"],"layers":[],"outputs":[]})

    validators=[]
    layers=manifest.get("layers",[])
    output_by_layer={l:[] for l in layers}
    for o in manifest.get("outputs",[]):
        gen=o.get("generator","")
        typ=o.get("type")
        for l in layers:
            if l in gen.lower() or (
              (l=="records" and typ=="plugin") or (l=="papyrus" and typ in {"psc","pex"}) or
              (l=="native" and typ=="dll") or (l=="mesh" and typ in {"nif","tri"}) or
              (l=="texture" and typ=="dds") or (l in {"animation","behavior"} and typ=="hkx") or
              (l=="audio" and typ in {"wav","xwm","fuz","lip"}) or (l=="lod" and typ=="lod")
            ):
                output_by_layer[l].append(o.get("path",""))

    for layer in layers:
        if layer not in GENERATE: continue
        gid,action,defaults=GENERATE[layer]
        invalid=quality.get("invalidation_triggers",[])
        preferred=quality.get("adapters",{}).get("preferred",[])
        gadapters=[x for x in defaults if x in preferred] or defaults
        gen_deps=["source.lock"]
        if layer=="native":
            preferred_set=set(preferred)
            cfg=["commonlib-cmake-configure"] if ("commonlib-cmake-configure" in preferred_set or not preferred_set) else ["commonlib-cmake-configure"]
            add(nodes,{"id":"generate.native-configure","phase":"generate","action":"Configure native SKSE/CommonLib build tree","layers":[layer],
              "depends_on":["source.lock"],"adapters":cfg,"gates":[],"invalidated_by":invalid,
              "outputs":[],"parallel_group":"layer-generate"})
            gen_deps=["generate.native-configure"]
        add(nodes,{"id":gid,"phase":"generate","action":action,"layers":[layer],
          "depends_on":gen_deps,"adapters":gadapters,"gates":[],"invalidated_by":invalid,
          "outputs":output_by_layer.get(layer,[]),"parallel_group":"layer-generate"})
        vid,vdefaults=VALIDATE[layer]
        vadapters=[x for x in vdefaults if x in preferred or x in quality.get("adapters",{}).get("supporting",[])] or vdefaults
        add(nodes,{"id":vid,"phase":"validate","action":f"Validate {layer} outputs","layers":[layer],
          "depends_on":[gid],"adapters":vadapters,"gates":layer_gates(quality,layer),
          "invalidated_by":invalid,"outputs":[],"parallel_group":"layer-validate"})
        validators.append(vid)

    if not validators: validators=["source.lock"]
    add(nodes,{"id":"integrate.cross-layer","phase":"integrate","action":"Run asset closure, touch-set, static/runtime disagreement and schema triangulation checks",
      "depends_on":validators,"adapters":["xedit"],"gates":["G11","G18","G24"],"invalidated_by":["any validated layer output","load order","asset priority"],"layers":layers,"outputs":[]})
    add(nodes,{"id":"integrate.gates","phase":"integrate","action":"Evaluate all required quality gates and mutation-test validators",
      "depends_on":["integrate.cross-layer"],"adapters":[],"gates":quality.get("gates",[]),"invalidated_by":["quality plan","validation evidence"],"layers":layers,"outputs":[]})
    runtime_capable={
      "mo2-devbench-runtime","devbench","skytest","skylink-ai","skyrimnet","autotest"
    }
    declared_runtime=[
      x
      for x in (
        quality.get("adapters",{}).get("preferred",[])
        +quality.get("adapters",{}).get("supporting",[])
      )
      if x in runtime_capable
    ]
    # devbench is the in-game observer. For normal DAG execution, wrap it in the
    # composite MO2 harness so profile/process isolation and evidence cleanup are
    # part of the same executable node rather than an assumed external precondition.
    chosen_runtime=uniq([
      "mo2-devbench-runtime" if x=="devbench" else x
      for x in declared_runtime
    ])
    smoke_adapters=chosen_runtime or ["mo2-devbench-runtime"]
    regression_adapters=chosen_runtime or ["mo2-devbench-runtime"]
    quality_gates=set(quality.get("gates") or [])
    smoke_gates=[g for g in ("G19","G26") if g in quality_gates]
    regression_gates=[g for g in ("G20","G21","G26") if g in quality_gates]
    runtime_tail="integrate.gates"
    if smoke_gates:
        add(nodes,{"id":"runtime.smoke","phase":"runtime","action":"Run isolated smoke scenarios with log/state readback",
          "depends_on":[runtime_tail],"adapters":smoke_adapters,"gates":smoke_gates,"invalidated_by":["runtime-affecting output","test fixture"],"layers":layers,"outputs":[]})
        runtime_tail="runtime.smoke"
    if regression_gates:
        add(nodes,{"id":"runtime.regression","phase":"runtime","action":"Run layer-derived regression, negative and migration scenarios",
          "depends_on":[runtime_tail],"adapters":regression_adapters,"gates":regression_gates,"invalidated_by":["runtime-affecting output","regression corpus"],"layers":layers,"outputs":[]})
        runtime_tail="runtime.regression"

    package_dep=runtime_tail
    if "installer" in layers:
        package_dep="validate.installer" if any(n["id"]=="validate.installer" for n in nodes) else package_dep
        # Installer must be rebuilt after the last required runtime stage is accepted.
        for n in nodes:
            if n["id"]=="generate.installer": n["depends_on"]=[runtime_tail]
            if n["id"]=="validate.installer": n["depends_on"]=["generate.installer"]
        package_dep="validate.installer"
    else:
        add(nodes,{"id":"package.staging","phase":"package","action":"Assemble clean release staging tree",
          "depends_on":[runtime_tail],"adapters":[],"gates":["G22"],"invalidated_by":["release payload"],"layers":[],"outputs":[]})
        package_dep="package.staging"

    add(nodes,{"id":"release.audit","phase":"release","action":"Verify reproducibility, provenance, waivers, licenses and final artifact hashes",
      "depends_on":[package_dep],"adapters":[],"gates":["G23","G28","G29"],"invalidated_by":["release payload","dependency/license metadata","source commit"],"layers":[],"outputs":[]})

    # Validate graph.
    ids={n["id"] for n in nodes}
    for n in nodes:
        missing=[d for d in n["depends_on"] if d not in ids]
        if missing: raise ValueError(f"{n['id']} depends on missing nodes: {missing}")
    visiting=set(); done=set()
    graph={n["id"]:n["depends_on"] for n in nodes}
    def visit(x):
        if x in visiting: raise ValueError(f"cycle detected at {x}")
        if x in done: return
        visiting.add(x)
        for d in graph[x]: visit(d)
        visiting.remove(x); done.add(x)
    for x in ids: visit(x)

    return {"schema_version":"skyrim-build-dag-v1","project_id":pid,"nodes":nodes}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("quality_plan",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    quality=json.loads(args.quality_plan.read_text(encoding="utf-8"))
    result=compile_dag(manifest,quality)
    txt=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(txt,encoding="utf-8")
    else: print(txt,end="")

if __name__=="__main__":
    main()
