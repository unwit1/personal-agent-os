# Skyrim Mod Factory — Implementation Selection Rules

Created: 2026-09-24

These rules make tool choice predictable.

## Prefer static plugin generation when

- the change is stable game data;
- users should see it in xEdit;
- no per-load-order discovery is required;
- a runtime framework would add unnecessary dependency/state.

Backend priority:
1. Mutagen for typed deterministic generation;
2. xEdit scripting/native export when xEdit-specific semantics are needed;
3. CK when the record/editor workflow owns semantics not safely generated elsewhere.

## Prefer Synthesis when

- output depends on the user's actual load order;
- many upstream mods must be reconciled;
- patch logic is deterministic and codeable;
- users should regenerate after load-order changes.

Examples:
- leveled-list synthesis;
- NPC field merging;
- keyword/stat normalization;
- cross-mod record forwarding.

## Prefer runtime distribution when

- static overrides would create broad compatibility churn;
- target selection is naturally expressed as filters;
- framework supports the target data safely;
- changes can be applied at startup/runtime without save hazards.

Choose the narrowest framework:
- KID for keywords;
- SPID for supported actor distribution;
- BOS for base swaps;
- FLM for FormLists;
- SkyPatcher for supported record/runtime patches.

## Prefer Papyrus when

- feature is quest/event/gameplay-state driven;
- engine exposes needed events/functions;
- timing is not frame-critical;
- persistence can be managed safely.

Before writing a custom native DLL:
1. search vanilla/SKSE Papyrus APIs;
2. search the pinned powerofthree Papyrus Extender catalog for an existing function or event;
3. prefer an event over polling;
4. verify whether the call mutates a base form, one reference, one inventory instance, or loaded 3D;
5. escalate to native code only if the required engine surface/timing still is not available.

For repeatable project builds, prefer Pyro as the build orchestrator around the pinned release compiler, then independently inspect/cross-check PEX output.

## Prefer native CommonLib/SKSE when

- engine hook/state is unavailable through records, runtime patchers, vanilla/SKSE Papyrus, and existing Papyrus Extender APIs;
- per-frame or high-volume operation requires native performance;
- custom serialization is needed;
- deep UI/render/input/physics access is required.

Build policy:
- configure through the pinned CommonLib/CMake toolchain;
- build every declared target;
- preserve DLL/PDB hashes;
- scan imports/plugin metadata;
- verify load **and feature initialization** on the exact runtime;
- fail closed on unsupported runtimes/APIs.

Native code raises runtime, ABI and licensing obligations; do not use it merely because it is powerful.

## Prefer OAR when

- goal is conditional animation replacement;
- graph state machine does not need structural change.

## Prefer Pandora behavior patching when

- behavior nodes/transitions/projects must be modified;
- new behavior graph semantics are needed.

## Prefer PyNifly scripting when

- NIF transformation can be expressed programmatically;
- batch validation/repair is desired;
- Blender geometry authoring is not actually required.

## Require Blender/Outfit Studio supervision when

- topology/UV/weights require artistic editing;
- clipping must be judged;
- complex morph/cloth authoring is needed.

## Require CK/CKPE supervision when

- navmesh authoring/finalization;
- complex scenes/dialogue editor relationships;
- spatial world placement;
- FaceGen/editor-generated outputs;
- editor-specific quest/package authoring;
- visual cell/portal work.

Still post-validate CK output with xEdit and automated asset checks.

## Generated outputs are downstream artifacts

Never hand-edit generated output when source/config can be fixed instead.

Examples:
- Pandora output;
- BodySlide output;
- Synthesis patch;
- TexGen/DynDOLOD;
- grass cache;
- generated FOMOD archive.

Fix source -> regenerate -> validate.

## Prefer text/source interchange for Git-owned plugin authoring when

- a plugin is maintained as code/reviewable source;
- record changes need ordinary Git diffs/reviews;
- a supported Spriggit translation package covers the records involved.

Policy:
binary -> Spriggit source -> regenerated binary is accepted only after Mutagen/xEdit reload, semantic round-trip comparison, and touch-set validation. Spriggit source is not allowed to become a single-validator trust boundary.

## Runtime-test adapter selection

Prefer a runtime adapter that can prove the actual requested postcondition.

- **DevBench / dedicated Agent OS bridge** — preferred general typed runtime query/action/event surface when available.
- **SkyLink AI** — useful current runtime bridge where its supported runtime and operations fit.
- **SkyrimNet** — preferred when the project itself already depends on SkyrimNet.
- **Skytest** — experimental Linux/gamescope isolated A/B/replay harness. Use only after local self-tests prove session freshness, profile restoration, probe isolation, and known input limitations.
- **AutoTest** — specialized fallback for its supported screenshot/cell/NPC workflows.

A transport success is never a gameplay assertion. Always use read -> act -> wait -> read plus fresh-session evidence.
