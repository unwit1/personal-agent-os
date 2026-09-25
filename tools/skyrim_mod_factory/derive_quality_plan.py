#!/usr/bin/env python3
"""Derive a deterministic quality/test/tool plan from skyrim-mod-project-v1.

This is intentionally conservative. It does not decide creative semantics; it turns
declared implementation surfaces into required evidence and only emits questions that
can materially change architecture, save compatibility, runtime support, or release.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

BASE_GATES={"G00","G01","G23","G25","G27","G29"}

LAYER_GATES={
 "records":{"G02","G03","G05","G24"},
 "runtime-patching":{"G06","G17","G18","G19","G24","G26"},
 "papyrus":{"G07","G08","G19","G24","G26"},
 "native":{"G09","G10","G19","G20","G24","G26"},
 "ui":{"G11","G19","G26"},
 "animation":{"G11","G14","G17","G19","G26"},
 "behavior":{"G11","G14","G17","G19","G24","G26"},
 "mesh":{"G11","G12","G17","G24","G26"},
 "texture":{"G11","G13","G17","G24","G26"},
 "physics":{"G11","G12","G14","G19","G20","G26"},
 "world":{"G02","G03","G05","G11","G15","G17","G18","G24","G26"},
 "navmesh":{"G02","G03","G15","G18","G24","G26"},
 "quest-dialogue":{"G02","G03","G05","G07","G08","G11","G16","G19","G24","G26"},
 "audio":{"G11","G16","G19","G26"},
 "lod":{"G11","G17","G18","G19","G26"},
 "installer":{"G22","G23"},
 "save-persistence":{"G08","G21","G26"},
 "compatibility":{"G05","G18","G24"}
}

OUTPUT_GATES={
 "plugin":{"G02","G03","G05","G24"},
 "pex":{"G07","G24"},
 "dll":{"G09","G10","G19","G24","G26"},
 "nif":{"G11","G12","G24","G26"},
 "tri":{"G11","G12","G24","G26"},
 "dds":{"G11","G13","G24","G26"},
 "hkx":{"G11","G14","G24","G26"},
 "wav":{"G11","G16"},
 "xwm":{"G11","G16"},
 "fuz":{"G11","G16","G26"},
 "lip":{"G11","G16","G26"},
 "lod":{"G11","G17","G26"},
 "archive":{"G22","G23"},
 "xml":{"G22"}
}

LAYER_ADAPTERS={
 "records":(["housecarl","mutagen","spriggit","xdump","xedit"],["synthesis","mutagen-analyzers"]),
 "runtime-patching":(["xdump","xedit","housecarl"],["devbench","skylink-ai"]),
 "papyrus":(["pyro","papyrus-vscode","official-papyruscompiler","caprica","champollion"],["papyrus-utility","lilac","bind","devbench","skylink-ai"]),
 "native":(["commonlib-cmake-configure","commonlib-cmake-build","crash-logger"],["devbench","skylink-ai","tracy","renderdoc"]),
 "ui":(["devbench","skylink-ai"],["autotest"]),
 "animation":(["pandora","devbench"],["autotest"]),
 "behavior":(["pandora","devbench"],["skylink-ai"]),
 "mesh":(["pynifly","blender-mcp"],["ck-cmd","cathedral-assets-optimizer","autotest"]),
 "texture":(["directxtex","blender-mcp"],["cathedral-assets-optimizer","renderdoc","autotest"]),
 "physics":(["pynifly","devbench"],["blender-mcp","tracy"]),
 "world":(["ckpe","xedit"],["housecarl","devbench","autotest"]),
 "navmesh":(["ckpe","xedit"],["devbench","autotest"]),
 "quest-dialogue":(["ckpe","xedit","papyrus-vscode"],["devbench","skylink-ai","lilac","bind"]),
 "audio":(["vospeaker"],["devbench"]),
 "lod":(["xlodgen","dyndolod"],["pgpatcher","autotest"]),
 "installer":(["cathedral-assets-optimizer"],["mo2"]),
 "save-persistence":(["fallrimtools","resaver-cli","devbench"],["skylink-ai"]),
 "compatibility":(["libloot","xdump","xedit","loot","mutagen-analyzers"],["housecarl","synthesis"])
}

STATIC={
 "records":["reload output with independent plugin parsers","resolve every master/FormLink","compare declared touch-set to actual changed fields","export/dump touched record schemas through pinned xDump oracle"],
 "runtime-patching":["parse framework grammar with pinned version","resolve every target form/plugin","detect overlapping/duplicate runtime mutations"],
 "papyrus":["format/check PSC","compile all PSC with release compiler","cross-check high-risk scripts with an independent compiler","verify provider/native declarations","verify PEX freshness","verify VMAD/property bindings","inspect PEX metadata for generated scripts"],
 "native":["build every target runtime","scan imports/relocations/API versions","verify SKSE declaration and serialization version"],
 "ui":["validate exact menu/control identifiers","validate text-entry and input-focus handling"],
 "animation":["resolve HKX paths and skeleton nodes","validate OAR/animation conditions and priorities"],
 "behavior":["run Pandora and parse WARN/ERROR/FATAL","verify generated behavior output wins VFS"],
 "mesh":["parse NIF independently","validate shader slots, skinning, partitions, bounds, collision"],
 "texture":["decode DDS","validate format/mipmaps/colorspace/alpha semantics","resolve every NIF/material texture reference"],
 "physics":["validate collision layers/materials/constraints","check skeleton node dependencies"],
 "world":["validate CELL/WRLD/LAND/reference edits","check water/lighting/RoomBound/Portal forwarding"],
 "navmesh":["reject deleted NAVM","validate door links/finalization/connectivity"],
 "quest-dialogue":["validate aliases/stages/VMAD/INFO/SCEN/Story Manager links","resolve voice paths"],
 "audio":["validate audio format and exact resource path","verify VoiceType/INFO identity when dialogue"],
 "lod":["verify output input hashes/freshness","parse generator warnings/errors"],
 "installer":["validate clean staging closure","simulate supported installer option paths"],
 "save-persistence":["identify every persisted store and schema version","compare new-game and established-save state"],
 "compatibility":["analyze static field overlap, asset winners, runtime mutators and generated-output order"]
}

RUNTIME={
 "records":["load plugin in isolated test profile and read back representative touched forms"],
 "runtime-patching":["positive target receives mutation","negative target does not","duplicate-prevention","save/load reapplication"],
 "papyrus":["new-game initialization","save/load registration continuity","error-free owned Papyrus log"],
 "native":["startup/new game/load/save/revert","dependency-absent behavior","API-version mismatch behavior"],
 "ui":["keyboard/mouse/gamepad open-close","text-entry focus","resolution/UI-scale sanity"],
 "animation":["enter intended state","fallback state","event/annotation delivery"],
 "behavior":["exercise changed transition plus negative path","save/load while graph-relevant state active"],
 "mesh":["first/third-person or near/far visual inspection as applicable"],
 "texture":["representative material render under target renderer"],
 "physics":["collision/contact test","stress repeated load/unload","ragdoll/constraint stability when relevant"],
 "world":["load edited cells from multiple approaches","save/load in edited cell"],
 "navmesh":["NPC path traversal across every edited boundary/door triangle"],
 "quest-dialogue":["valid quest start","invalid-start conditions","every changed stage/alias/scene transition","mid-quest save/load"],
 "audio":["play representative line/sound in game","check subtitle/audio/lip synchronization when applicable"],
 "lod":["near/far transition inspection","worldspace reload/weather/season variant when applicable"],
 "save-persistence":["upgrade from previous release fixture","missing/old field migration","repeat save/load"],
 "compatibility":["representative conflicting-mod fixture and real-load-order smoke test"]
}

MUTATIONS={
 "records":["dangling FormLink","unexpected whole-record overwrite","invalid ESL-local FormID"],
 "runtime-patching":["malformed grammar","missing target plugin","duplicate rule"],
 "papyrus":["missing parent PSC","stale PEX","bad VMAD property","missing native provider"],
 "native":["unsupported runtime","missing Address Library/API provider","bad relocation/version gate"],
 "ui":["invalid menu identifier","hotkey collision/text-input leak"],
 "animation":["missing animation file","invalid condition/event name"],
 "behavior":["malformed graph patch","missing behavior target"],
 "mesh":["missing texture","unweighted vertex","invalid partition/bone"],
 "texture":["wrong DDS format","missing mipmaps","invalid normal-map convention"],
 "physics":["wrong collision layer/material","missing skeleton node"],
 "world":["reverted CELL subsystem field","missing persistent reference target"],
 "navmesh":["deleted navmesh","broken door link"],
 "quest-dialogue":["missing alias","bad fragment property","unreachable INFO conditions"],
 "audio":["wrong voice path","missing FUZ/LIP resource"],
 "lod":["stale generated output","missing billboard/source asset"],
 "installer":["missing payload","invalid option dependency"],
 "save-persistence":["old schema without migration","removed form still referenced by saved state"],
 "compatibility":["runtime mutator conflict hidden from xEdit"]
}

HUMAN={
 "ui":["final layout/usability"],
 "animation":["contact quality and motion feel"],
 "mesh":["final silhouette/clipping"],
 "texture":["final material/artistic appearance"],
 "physics":["feel/stability under representative play"],
 "world":["spatial composition"],
 "navmesh":["pathing quality in representative gameplay"],
 "quest-dialogue":["pacing and narrative intent"],
 "audio":["pronunciation/emotion/mix"],
 "lod":["visual transition quality"]
}

INVALIDATE={
 "records":["source plugin/master hash changes","xEdit/Mutagen/Spriggit schema version changes"],
 "runtime-patching":["framework grammar/version changes","target plugin/Form identity changes"],
 "papyrus":["PSC/provider/import-root changes","compiler version changes"],
 "native":["runtime/SKSE/Address Library/CommonLib/API provider changes"],
 "ui":["UI framework/menu asset changes"],
 "animation":["skeleton/OAR/animation source changes"],
 "behavior":["behavior source/Pandora version changes"],
 "mesh":["source NIF/skeleton/material changes"],
 "texture":["source image/material contract changes"],
 "physics":["skeleton/collision/physics-framework changes"],
 "world":["CELL/WRLD/LAND/reference source changes"],
 "navmesh":["architecture/door/navmesh source changes"],
 "quest-dialogue":["QUST/DIAL/INFO/SCEN/fragment source changes"],
 "audio":["line text/VoiceType/audio source changes"],
 "lod":["world/plugin/mesh/texture/grass/season input changes"],
 "installer":["payload/dependency/version matrix changes"],
 "save-persistence":["persisted schema or release baseline changes"],
 "compatibility":["load order, asset priority, runtime-mutator set or generated-patch set changes"]
}

RISK_WEIGHT={
 "native":4,"save-persistence":4,"navmesh":3,"quest-dialogue":3,"world":3,
 "behavior":3,"physics":3,"papyrus":2,"runtime-patching":2,"lod":2,
 "records":1,"ui":1,"animation":2,"mesh":2,"texture":1,"audio":1,
 "installer":1,"compatibility":2
}

def add_reason(reasons,key,reason):
    reasons.setdefault(key,[])
    if reason not in reasons[key]: reasons[key].append(reason)

def uniq(seq):
    seen=set(); out=[]
    for x in seq:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

def derive(manifest):
    layers=manifest.get("layers",[])
    outputs=[o.get("type") for o in manifest.get("outputs",[]) if isinstance(o,dict)]
    gates=set(BASE_GATES)
    preferred=[]; supporting=[]; static=[]; runtime=[]; mutations=[]; human=[]; invalid=[]
    reasons={}

    for layer in layers:
        for g in LAYER_GATES.get(layer,set()):
            gates.add(g); add_reason(reasons,g,f"layer:{layer}")
        pa,sa=LAYER_ADAPTERS.get(layer,([],[]))
        preferred.extend(pa); supporting.extend(sa)
        static.extend(STATIC.get(layer,[]))
        runtime.extend(RUNTIME.get(layer,[]))
        mutations.extend(MUTATIONS.get(layer,[]))
        human.extend(HUMAN.get(layer,[]))
        invalid.extend(INVALIDATE.get(layer,[]))

    for out in outputs:
        for g in OUTPUT_GATES.get(out,set()):
            gates.add(g); add_reason(reasons,g,f"output:{out}")

    pp=manifest.get("plugin_policy") or {}
    if pp.get("kind") in {"esl","esp-fe"}:
        gates.add("G04"); add_reason(reasons,"G04",f"plugin_policy:{pp.get('kind')}")
    if pp.get("localized"):
        static.append("validate STRINGS/DLSTRINGS/ILSTRINGS closure and localization keys")

    framework_ids={str(x.get("id","")).lower() for x in manifest.get("frameworks",[]) if isinstance(x,dict)}
    if framework_ids & {"papyrus-extender","po3-papyrus-extender","powerofthree-papyrus-extender"}:
        supporting.append("papyrus-extender")
        static.extend([
            "verify Papyrus Extender provider PSC/PEX generation matches the pinned API snapshot",
            "verify every used native declaration maps to an installed runtime provider"
        ])
        runtime.extend([
            "verify Papyrus Extender DLL loads and registers required natives",
            "read back at least one project-used Papyrus Extender operation on a disposable fixture"
        ])
        mutations.append("Papyrus Extender PSC present but native provider missing/incompatible")
        invalid.append("Papyrus Extender version/runtime/provider API changes")

    persistence=manifest.get("persistence") or {}
    if any(persistence.get(k) for k in ("uses_save_state","uses_skse_cosave","uses_external_state")):
        gates.update({"G21","G26"})
        add_reason(reasons,"G21","declared persistent state")
        runtime.extend(RUNTIME["save-persistence"])
        mutations.extend(MUTATIONS["save-persistence"])
        invalid.extend(INVALIDATE["save-persistence"])

    release=manifest.get("release") or {}
    if release.get("fomod"):
        gates.add("G22"); add_reason(reasons,"G22","release:fomod")
        static.extend(STATIC["installer"]); mutations.extend(MUTATIONS["installer"])

    if any(o in {"nif","tri","dds","hkx","wav","xwm","fuz","lip"} for o in outputs):
        gates.add("G28"); add_reason(reasons,"G28","generated/release asset output")

    declared=(manifest.get("validation") or {}).get("required_gates",[])
    for g in declared:
        gates.add(g); add_reason(reasons,g,"manifest-declared")

    preferred.extend((manifest.get("automation") or {}).get("preferred_adapters",[]))

    score=sum(RISK_WEIGHT.get(x,1) for x in set(layers))
    if "native" in layers and "save-persistence" in layers: risk="critical"
    elif score>=9 or any(x in layers for x in ("native","navmesh")): risk="high"
    elif score>=4: risk="medium"
    else: risk="low"

    questions=[]
    targets=manifest.get("targets",[])
    if "other" in targets:
        questions.append("What exact Skyrim executable/distribution is represented by target 'other'?")
    if "native" in layers and any(t in {"ae-steam","ae-gog","ae-1.7.x"} for t in targets):
        questions.append("What exact executable versions must the native DLL support inside the declared AE target family?")
    if any(persistence.get(k) for k in ("uses_save_state","uses_skse_cosave","uses_external_state")):
        if persistence.get("schema_version") is None:
            questions.append("What persisted-state schema version should this release use?")
        if persistence.get("supports_upgrade") is None:
            questions.append("Must this release support upgrading an existing save from a prior mod version?")
    if not release.get("license"):
        questions.append("What license/redistribution policy applies to the release and bundled/generated assets?")
    if "navmesh" in layers and "world" not in layers:
        static.append("confirm navmesh edits are intentional despite no declared world/architecture layer")

    return {
      "schema_version":"skyrim-quality-plan-v1",
      "project_id":manifest.get("project_id"),
      "risk_tier":risk,
      "gates":sorted(gates,key=lambda x:int(x[1:])),
      "adapters":{"preferred":uniq(preferred),"supporting":uniq(x for x in supporting if x not in preferred)},
      "static_checks":uniq(static),
      "runtime_scenarios":uniq(runtime),
      "mutation_tests":uniq(mutations),
      "human_checks":uniq(human + (manifest.get("validation") or {}).get("human_checks",[])),
      "invalidation_triggers":uniq(invalid),
      "blocking_questions":uniq(questions),
      "reasons":{k:v for k,v in sorted(reasons.items(),key=lambda kv:int(kv[0][1:]))}
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("schema_version")!="skyrim-mod-project-v1":
        raise SystemExit("Expected skyrim-mod-project-v1 manifest")
    result=derive(manifest)
    text=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    else:
        print(text,end="")

if __name__=="__main__":
    main()
