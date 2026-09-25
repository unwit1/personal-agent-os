#!/usr/bin/env python3
"""Derive a regression-oriented Skyrim Mod Factory test matrix.

The matrix is intentionally broader than the feature's happy path. It adds
negative, persistence, dependency, compatibility, and recovery fixtures whenever
the implementation surfaces imply those risks.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


LAYER_DEFAULTS: dict[str, list[dict[str, Any]]] = {
    "records": [
        dict(id="records-static", category="positive", priority="blocker",
             desc="Generated plugin parses and only changes the declared record/field touch-set.",
             fixture="load-order",
             actions=["Generate the plugin from a clean source snapshot.", "Reload it through independent plugin parsers.", "Diff actual touched records/fields against declared intent."],
             assertions=["All masters and non-null FormLinks resolve.", "No undeclared records or fields changed.", "xEdit/xDump and typed parser agree on touched structure."],
             adapters=["mutagen","xdump","xedit"]),
        dict(id="records-invalid-ref", category="negative", priority="high",
             desc="Validator rejects a deliberately unresolved FormLink/missing master fixture.",
             fixture="custom",
             actions=["Inject one representative bad FormLink or remove one required fixture master.", "Run plugin validation."],
             assertions=["Validation fails with the expected issue class.", "The bad fixture cannot receive release PASS."],
             adapters=["mutagen","xdump","xedit"]),
    ],
    "runtime-patching": [
        dict(id="runtime-positive-negative", category="positive", priority="blocker",
             desc="Runtime distribution/patch applies to intended targets and not to excluded targets.",
             fixture="new-game",
             actions=["Load a positive target and a near-match negative target.", "Wait for framework application.", "Read back final runtime state."],
             assertions=["Positive target receives exactly the intended mutation.", "Negative target remains unchanged."],
             adapters=["devbench"]),
        dict(id="runtime-idempotent", category="idempotency", priority="high",
             desc="Repeated load/application does not duplicate runtime mutations.",
             fixture="save",
             actions=["Observe initial result.", "Save/reload or re-trigger framework initialization.", "Read back the same target again."],
             assertions=["No duplicate spell/perk/item/keyword/list entry appears.", "Final state is stable across repeated application."],
             adapters=["devbench"]),
    ],
    "papyrus": [
        dict(id="papyrus-compile-crosscheck", category="positive", priority="blocker",
             desc="Papyrus source compiles with the release compiler and high-risk scripts cross-check independently.",
             fixture="custom",
             actions=["Format/check source.", "Compile with official PapyrusCompiler.", "Cross-compile high-risk scripts with Caprica or Papyrus Utility.", "Inspect PEX metadata."],
             assertions=["No compile errors.", "Native/provider declarations resolve.", "PEX is newer than/derived from current PSC.", "VMAD-facing declarations match source."],
             adapters=["official-papyruscompiler","caprica","papyrus-utility","champollion"]),
        dict(id="papyrus-save-load", category="persistence", priority="high",
             desc="Papyrus registrations/state survive the intended save/load lifecycle without duplicate initialization.",
             fixture="save",
             actions=["Trigger initialization.", "Save.", "Reload.", "Trigger the relevant event again."],
             assertions=["Required registrations remain functional.", "Initialization side effects are not duplicated.", "No new owned Papyrus errors appear."],
             adapters=["devbench"]),
    ],
    "native": [
        dict(id="native-lifecycle", category="smoke", priority="blocker",
             desc="Native plugin loads and reaches every required initialization stage on each supported runtime.",
             fixture="new-game",
             actions=["Launch target runtime.", "Capture SKSE/plugin startup log.", "Start new game.", "Load a save.", "Save/revert as applicable."],
             assertions=["DLL is accepted for the runtime.", "Required hooks/APIs report ready.", "NewGame/PostLoadGame/serialization lifecycle completes without owned errors."],
             adapters=["devbench","crash-logger"]),
        dict(id="native-dependency-missing", category="dependency", priority="high",
             desc="Optional dependency absence fails closed and hard dependency absence produces explicit diagnosis.",
             fixture="dependency",
             actions=["Run fixture with one optional provider removed.", "Run fixture with one declared hard provider removed."],
             assertions=["Optional integration disables without crash.", "Hard dependency failure is explicit and actionable rather than memory corruption/undefined behavior."],
             adapters=["devbench"]),
    ],
    "ui": [
        dict(id="ui-input-focus", category="positive", priority="high",
             desc="Menu input, text entry, controller focus, and close/reopen lifecycle behave correctly.",
             fixture="new-game",
             actions=["Open the menu with each supported input mode.", "Enter text if applicable.", "Close/reopen while gameplay input is active."],
             assertions=["Gameplay hotkeys do not leak through text entry.", "Focus/cursor ownership restores after close.", "Menu remains usable at supported UI scale/resolution."],
             adapters=["devbench"]),
    ],
    "animation": [
        dict(id="animation-selection", category="positive", priority="high",
             desc="Intended animation wins in the intended condition and fallback wins outside it.",
             fixture="combat",
             actions=["Enter positive condition.", "Capture selected animation/event.", "Enter near-match negative condition."],
             assertions=["Expected animation plays in positive state.", "Fallback/other animation plays in negative state.", "No missing-file/A-pose condition occurs."],
             adapters=["pandora","devbench"]),
        dict(id="animation-perspectives", category="boundary", priority="medium",
             desc="Animation behaves across supported first-person/third-person/mount or VR perspectives.",
             fixture="custom",
             actions=["Exercise each declared camera/perspective variant."],
             assertions=["No perspective-specific missing animation or skeleton mismatch."],
             adapters=["devbench"]),
    ],
    "behavior": [
        dict(id="behavior-transition", category="positive", priority="blocker",
             desc="Every changed graph transition is reachable and has a valid negative/fallback path.",
             fixture="combat",
             actions=["Generate Pandora output.", "Enter each changed transition precondition.", "Exit through each intended transition."],
             assertions=["Pandora reports no fatal patch failure.", "Runtime reaches expected graph states/events.", "Fallback path remains functional."],
             adapters=["pandora","devbench"]),
    ],
    "mesh": [
        dict(id="mesh-structural", category="positive", priority="blocker",
             desc="NIF/TRI structure, skinning, partitions, bounds, shader references, and collision satisfy the intended contract.",
             fixture="asset",
             actions=["Parse with PyNifly.", "Load independently in NifSkope/Blender.", "Resolve all referenced textures/bones."],
             assertions=["No invalid/unweighted required vertices.", "Expected partitions/slots match records.", "All required resources resolve.", "Independent parsers agree on core structure."],
             adapters=["pynifly","nifskope"]),
        dict(id="mesh-visual", category="visual", priority="high",
             desc="Generated mesh has acceptable clipping, silhouette, and first/third-person presentation.",
             fixture="new-game",
             actions=["Render/inspect the representative item/actor in game across intended poses."],
             assertions=["No unacceptable clipping or deformation.", "No missing/purple/invisible surfaces."],
             adapters=["devbench"],
             automation="automated-with-supervised-evidence"),
    ],
    "texture": [
        dict(id="texture-format", category="positive", priority="blocker",
             desc="DDS/material resources use valid dimensions, mipmaps, compression, alpha and semantic map conventions.",
             fixture="asset",
             actions=["Decode every generated DDS.", "Validate metadata/mips.", "Resolve NIF/material references."],
             assertions=["Every texture decodes.", "Mip chain and format match usage.", "No required referenced texture is missing."],
             adapters=["directxtex"]),
    ],
    "physics": [
        dict(id="physics-stress", category="stress", priority="high",
             desc="Physics/collision remains stable across repeated load/unload and representative interactions.",
             fixture="custom",
             actions=["Exercise collision/constraint interaction repeatedly.", "Change cells or reload 3D.", "Repeat after save/load."],
             assertions=["No explosive physics, stuck constraints, disappearing collision, or crash.", "Expected material/layer contact is preserved."],
             adapters=["pynifly","devbench"]),
    ],
    "world": [
        dict(id="world-approach-reload", category="boundary", priority="high",
             desc="Edited cells render and behave from multiple approach directions and across save/load/cell attach cycles.",
             fixture="location",
             actions=["Approach edited area from multiple adjacent cells.", "Enter/leave cell.", "Save/load inside and outside edited area."],
             assertions=["No missing references, water seams, portal popping, or stale enable state attributable to the mod."],
             adapters=["xdump","xedit","devbench"]),
    ],
    "navmesh": [
        dict(id="navmesh-traversal", category="positive", priority="blocker",
             desc="NPC pathing crosses every edited navmesh boundary/door connection.",
             fixture="location",
             actions=["Spawn/use deterministic NPC path fixtures.", "Path through each edited doorway/boundary in both directions."],
             assertions=["No deleted/unfinalized NAVM.", "NPCs reach targets without collision/navmesh contradiction."],
             adapters=["ckpe","xedit","devbench"]),
    ],
    "quest-dialogue": [
        dict(id="quest-happy-negative", category="positive", priority="blocker",
             desc="Quest/dialogue can enter the intended path and rejects conditions that should not start/fire.",
             fixture="quest",
             actions=["Run valid start path.", "Run invalid/near-match start path.", "Exercise changed stages/aliases/scenes/dialogue."],
             assertions=["Valid path reaches expected stages/objectives.", "Invalid path does not start/fire.", "Alias and scene targets remain valid."],
             adapters=["xdump","xedit","devbench"]),
        dict(id="quest-midstate-save", category="persistence", priority="high",
             desc="Save/load during each important quest/scene state resumes correctly.",
             fixture="save",
             actions=["Save at representative mid-quest/mid-scene states.", "Reload and continue."],
             assertions=["No duplicated fragment/scene action.", "Aliases and objectives preserve intended state.", "Quest remains completable."],
             adapters=["devbench"]),
    ],
    "audio": [
        dict(id="audio-resource", category="positive", priority="high",
             desc="Every intended dialogue/sound asset resolves and plays with the final plugin/VoiceType identity.",
             fixture="quest",
             actions=["Resolve expected asset paths.", "Play representative lines/sounds in game."],
             assertions=["No missing FUZ/XWM/LIP/resource.", "Subtitle/voice/lip relationship is correct where applicable."],
             adapters=["devbench"]),
    ],
    "lod": [
        dict(id="lod-freshness", category="positive", priority="blocker",
             desc="LOD output is generated from the current winning plugins/assets and has no stale-input signature.",
             fixture="location",
             actions=["Compare generator input hashes/settings/load order.", "Regenerate if stale.", "Inspect near/far transitions."],
             assertions=["Generator log has no unclassified fatal/error.", "Output inputs match current state.", "No obvious near/far mismatch in representative areas."],
             adapters=["xlodgen","dyndolod"]),
    ],
    "installer": [
        dict(id="package-option-closure", category="packaging", priority="blocker",
             desc="Every supported installer option combination produces a complete valid Data tree.",
             fixture="package",
             actions=["Validate installer schema.", "Enumerate supported option combinations.", "Install each into a clean temporary tree."],
             assertions=["Every referenced payload exists.", "Required dependencies/files are present.", "No development/log/temp files leak into release."],
             adapters=["package-validator"]),
    ],
    "save-persistence": [
        dict(id="persistence-roundtrip", category="persistence", priority="blocker",
             desc="Persisted state survives repeated save/load with stable schema and no duplicate records/registrations.",
             fixture="save",
             actions=["Create representative persistent state.", "Save/load repeatedly.", "Compare state after each cycle."],
             assertions=["State round-trips without loss/duplication.", "No orphaned/corrupt save data attributable to the mod."],
             adapters=["fallrimtools","devbench"]),
    ],
    "compatibility": [
        dict(id="compat-overlap", category="compatibility", priority="high",
             desc="Representative overlapping mod fixture resolves according to declared field/asset/runtime ownership.",
             fixture="load-order",
             actions=["Build a fixture with a known overlapping mod.", "Inspect static winner, asset winner, runtime mutators, and final runtime state."],
             assertions=["Declared compatibility strategy is actually reflected in final state.", "No hidden runtime mutator silently reverses the static patch."],
             adapters=["libloot","xdump","xedit","devbench"]),
    ],
}


def uniq(seq):
    out=[]; seen=set()
    for x in seq:
        if x not in seen:
            seen.add(x); out.append(x)
    return out


def make_case(project_id: str, layer: str, row: dict[str, Any], targets: list[str]) -> dict[str, Any]:
    return {
        "test_id": f"{project_id}.{row['id']}",
        "category": row["category"],
        "priority": row["priority"],
        "description": row["desc"],
        "layers": [layer],
        "targets": targets,
        "fixture": {"kind": row["fixture"], "fresh_copy": True},
        "preconditions": [],
        "actions": row["actions"],
        "assertions": row["assertions"],
        "negative_assertions": [],
        "adapters": row["adapters"],
        "automation": row.get("automation", "fully-automated"),
        "timeout_seconds": 300,
        "cleanup": ["Discard fixture mutations or restore the fixture copy after the test."],
        "invalidates_on": [f"{layer} inputs/tool/framework version changes"],
        "acceptance_criteria": [],
        "rationale": f"Automatically required by implementation layer '{layer}'.",
        "required": True,
    }


def derive(manifest: dict[str, Any], feature: dict[str, Any] | None = None) -> dict[str, Any]:
    feature = feature or {}
    project_id = manifest.get("project_id") or "project"
    layers = uniq(manifest.get("layers") or [])
    targets = uniq(manifest.get("targets") or [])
    cases: list[dict[str, Any]] = []

    # Universal launch/build smoke.
    cases.append({
        "test_id": f"{project_id}.launch-smoke",
        "category": "smoke",
        "priority": "blocker",
        "description": "The isolated test profile launches with the candidate build and produces no new owned fatal/error diagnostics.",
        "layers": layers,
        "targets": targets,
        "fixture": {"kind": "new-game", "fresh_copy": True},
        "preconditions": ["All static blocker gates pass before launch."],
        "actions": ["Launch the dedicated test profile.", "Reach main menu.", "Start/load the representative fixture.", "Collect owned logs."],
        "assertions": ["No crash.", "No new owned ERROR/FATAL remains unclassified.", "Candidate files are the VFS winners expected by the build manifest."],
        "negative_assertions": [],
        "adapters": ["mo2","devbench","crash-logger"],
        "automation": "fully-automated",
        "timeout_seconds": 300,
        "cleanup": ["Close game and preserve only captured evidence."],
        "invalidates_on": ["any candidate build artifact, dependency, runtime, profile, or load-order change"],
        "acceptance_criteria": [],
        "rationale": "Every release candidate needs an executable smoke test.",
        "required": True,
    })

    for layer in layers:
        for row in LAYER_DEFAULTS.get(layer, []):
            cases.append(make_case(project_id, layer, row, targets))

    persistence = manifest.get("persistence") or {}
    uses_persistence = any(persistence.get(k) for k in ("uses_save_state","uses_skse_cosave","uses_external_state"))
    if uses_persistence and "save-persistence" not in layers:
        for row in LAYER_DEFAULTS["save-persistence"]:
            cases.append(make_case(project_id, "save-persistence", row, targets))

    if uses_persistence and persistence.get("supports_upgrade"):
        cases.append({
            "test_id": f"{project_id}.upgrade-prior-release",
            "category": "migration",
            "priority": "blocker",
            "description": "A save created with the prior supported release migrates to the new persisted-state schema.",
            "layers": ["save-persistence"],
            "targets": targets,
            "fixture": {"kind":"save","fresh_copy":True,"notes":"Fixture must be authored by the previous released version, not synthesized after the fact."},
            "preconditions": ["Previous release and migration baseline are pinned."],
            "actions": ["Create/load prior-release fixture.", "Upgrade candidate files.", "Load fixture.", "Exercise migrated feature.", "Save/reload again."],
            "assertions": ["Migration runs once.", "Old values map to current semantics.", "No lost/duplicate persistent state.", "Second load does not rerun destructive migration."],
            "negative_assertions": [],
            "adapters": ["fallrimtools","devbench"],
            "automation": "fully-automated",
            "timeout_seconds": 600,
            "cleanup": ["Never overwrite the canonical previous-version save fixture."],
            "invalidates_on": ["persisted schema, migration code, or prior supported release changes"],
            "acceptance_criteria": [],
            "rationale": "Upgrade support is a release promise and requires a real historical-save fixture.",
            "required": True,
        })

    if uses_persistence and persistence.get("supports_uninstall"):
        cases.append({
            "test_id": f"{project_id}.uninstall-claim",
            "category": "recovery",
            "priority": "blocker",
            "description": "The declared mid-save uninstall procedure is validated against a copy of a representative save.",
            "layers": ["save-persistence"],
            "targets": targets,
            "fixture": {"kind":"save","fresh_copy":True},
            "preconditions": ["Project explicitly claims uninstall support."],
            "actions": ["Create modded state.", "Follow documented uninstall preparation.", "Remove mod in fixture profile.", "Load/save/reload the copied save.", "Inspect residual state."],
            "assertions": ["No missing-script/native dependency failure attributable to promised uninstall path.", "Residual state matches documented expectations."],
            "negative_assertions": [],
            "adapters": ["fallrimtools","devbench"],
            "automation": "automated-with-supervised-evidence",
            "timeout_seconds": 600,
            "cleanup": ["Discard modified fixture save."],
            "invalidates_on": ["persistent-state or uninstall-procedure change"],
            "acceptance_criteria": [],
            "rationale": "Uninstall safety must never be promised without an explicit destructive-copy fixture.",
            "required": True,
        })

    # Framework dependency failure fixtures.
    required_frameworks=[f for f in (manifest.get("frameworks") or []) if isinstance(f,dict) and f.get("required",True)]
    if required_frameworks:
        cases.append({
            "test_id": f"{project_id}.required-dependency-diagnostics",
            "category": "dependency",
            "priority": "high",
            "description": "Missing/incompatible required framework produces explicit actionable diagnosis rather than undefined behavior.",
            "layers": layers,
            "targets": targets,
            "fixture": {"kind":"dependency","fresh_copy":True},
            "preconditions": [],
            "actions": ["For each required framework, run a fixture with it absent or intentionally incompatible where safe."],
            "assertions": ["Failure is explicit and names the missing/incompatible dependency.", "No save-corrupting or crash-loop behavior is introduced merely by dependency absence."],
            "negative_assertions": [],
            "adapters": ["doctor-toolchain","devbench"],
            "automation": "fully-automated",
            "timeout_seconds": 300,
            "cleanup": ["Restore dependency fixture/profile after each case."],
            "invalidates_on": ["framework dependency/version policy changes"],
            "acceptance_criteria": [],
            "rationale": "Dependency diagnostics are part of supportability and autonomous debugging.",
            "required": True,
        })

    # Map feature acceptance criteria into dedicated cases where possible.
    mapped = 0
    criteria = feature.get("acceptance_criteria") or []
    for ac in criteria:
        if not isinstance(ac, dict) or not ac.get("id") or not ac.get("statement"):
            continue
        mapped += 1
        kind=ac.get("kind","runtime")
        category={
            "negative":"negative","performance":"performance","visual":"visual",
            "persistence":"persistence","compatibility":"compatibility","packaging":"packaging"
        }.get(kind,"positive")
        automation="fully-automated" if ac.get("automatable",True) else "automated-with-supervised-evidence"
        cases.append({
            "test_id": f"{project_id}.acceptance.{ac['id']}",
            "category": category,
            "priority": "blocker" if kind in {"runtime","persistence","packaging"} else "high",
            "description": ac["statement"],
            "layers": layers,
            "targets": targets,
            "fixture": {"kind": ("custom" if ac.get("fixture_hint") else ("package" if kind=="packaging" else "custom")), "fresh_copy": True, "notes": ac.get("fixture_hint","")},
            "preconditions": [],
            "actions": ["Construct the smallest fixture that exercises this acceptance criterion.", "Trigger the behavior and capture evidence."],
            "assertions": [ac["statement"]],
            "negative_assertions": [],
            "adapters": ["devbench"] if kind not in {"static","packaging"} else ["xdump"],
            "automation": automation,
            "timeout_seconds": 300,
            "cleanup": ["Restore fixture state."],
            "invalidates_on": ["feature implementation or acceptance criterion changes"],
            "acceptance_criteria": [ac["id"]],
            "rationale": "Directly generated from feature acceptance criteria.",
            "required": True,
        })

    # De-duplicate by test ID, preserving the first canonical requirement.
    unique_cases=[]
    seen=set()
    for case in cases:
        if case["test_id"] in seen:
            continue
        seen.add(case["test_id"])
        unique_cases.append(case)

    categories=uniq(c["category"] for c in unique_cases)
    gaps=[]
    if len(criteria) != mapped:
        gaps.append("One or more malformed acceptance criteria could not be mapped.")
    if not feature and manifest.get("features"):
        gaps.append("No full skyrim-feature-intent-v1 document was provided, so feature-level acceptance criteria were not expanded.")

    return {
        "schema_version":"skyrim-test-matrix-v1",
        "project_id":project_id,
        "feature_id":feature.get("feature_id"),
        "generated_from":["skyrim-mod-project-v1"] + (["skyrim-feature-intent-v1"] if feature else []),
        "cases":unique_cases,
        "coverage":{
            "categories":categories,
            "layers":layers,
            "acceptance_criteria_total":len(criteria),
            "acceptance_criteria_mapped":mapped,
            "gaps":gaps,
        },
    }


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--feature-intent",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    feature=json.loads(args.feature_intent.read_text(encoding="utf-8")) if args.feature_intent else {}
    result=derive(manifest,feature)
    rendered=json.dumps(result,indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered,encoding="utf-8")
    else:
        print(rendered,end="")


if __name__=="__main__":
    main()
