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

Avoid polling if an event exists.

## Prefer native CommonLib/SKSE when

- engine hook/state is unavailable to Papyrus;
- per-frame or high-volume operation requires native performance;
- custom serialization is needed;
- deep UI/render/input/physics access is required.

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
