# Skyrim Mod Factory — Validation Gates

Created: 2026-09-24
Status: canonical gate registry

A build is not "done" because files were generated. It advances only when every applicable gate passes or has an explicit reviewed waiver.

## Gate severity

- **BLOCKER** — release/build cannot continue.
- **ERROR** — feature likely incorrect; must fix or waive with evidence.
- **WARNING** — potentially valid but requires disposition.
- **INFO** — evidence/provenance note.

## G00 — Manifest validity

Check:
- project id/name;
- target runtime(s);
- output types;
- masters/dependencies;
- implementation layers;
- build/test commands;
- persistence policy;
- package policy.

Auto-fix:
- formatting/default fields only.

## G01 — Source/provenance lock

Check:
- tool versions;
- framework versions;
- source plugin/asset hashes;
- game runtime;
- SKSE/Address Library;
- schema snapshot.

Fail if an output cannot be reproduced from identified inputs.

## G02 — Plugin binary/schema validity

Use:
- xEdit/xDump definitions;
- Mutagen reload;
- xEdit error scan.

Check:
- valid record/subrecord layout;
- FormVersion/header;
- field type;
- array/count consistency;
- record flags context.

Auto-fix only when transformation is schema-preserving and unambiguous.

## G03 — Master/FormID integrity

Check:
- all masters exist;
- master order;
- all FormIDs resolve;
- no stale compacted IDs;
- plugin references intended source.

Block on unresolved FormID.

## G04 — ESL/light-plugin integrity

Check:
- header flag;
- local FormID range for target header/runtime;
- compaction provenance;
- persistent external references;
- config/FormID references that would break after renumbering.

Never auto-compact an established released plugin without a migration decision.

## G05 — Record conflict intent

Check generated override against:
- origin;
- every upstream override;
- declared field ownership;
- compatibility rules.

Detect:
- accidental whole-record copy;
- reverted unrelated field;
- unintentional ITM;
- accidental deletion.

Auto-fix by forwarding fields only when the project manifest identifies authoritative sources.

## G06 — Runtime patch/config validity

Applies to SPID/KID/BOS/FLM/SkyPatcher/OAR/etc.

Check:
- grammar;
- form resolution;
- duplicate/overlapping rules;
- priority/order;
- impossible filters;
- framework version.

Prefer framework's own parser/log as final grammar oracle.

## G07 — Papyrus compile and dependency validity

Check:
- all PSC compile;
- declaration roots pinned;
- no missing parent/type;
- no unresolved native declarations in release environment;
- no duplicate ScriptName provider ambiguity;
- fragment scripts match plugin VMAD.

Cross-compile with official compiler/Caprica where project risk warrants.

## G08 — Papyrus lifecycle/persistence

Static checks:
- registration cleanup;
- update loops;
- OnInit assumptions;
- latent calls;
- property migration;
- alias/reference lifetime;
- serialization/external state.

Runtime tests:
- new game;
- save/load;
- upgrade;
- uninstall only if promised.

## G09 — Native plugin build matrix

Check every declared target:
- compiler/build success;
- warnings policy;
- SKSE metadata;
- Address Library/relocation coverage;
- API version checks;
- dependency imports;
- runtime guards;
- serialization version.

A single successful AE build does not prove SE/GOG/VR compatibility.

## G10 — Native safety/static analysis

Check:
- null/handle lifetime;
- threading;
- event unregistration;
- trampoline/hook assumptions;
- relocation IDs;
- ABI-gated structures;
- serialization bounds/versioning.

Run unit tests and sanitizers where feasible outside game process.

## G11 — Asset path closure

Build a referenced-asset graph from:
- plugin paths;
- NIF texture/controller paths;
- configs;
- scripts;
- UI;
- voice paths.

Fail on missing required files.

Warn on unused/orphaned files.

## G12 — NIF/mesh/morph validity

Check:
- game target;
- block types;
- shader properties/texture slots;
- skin/bones;
- unweighted vertices;
- partitions/biped consistency;
- bounds;
- collision;
- TRI vertex/topology compatibility;
- _0/_1 compatibility.

Round-trip test via Nifly/PyNifly where practical.

## G13 — Texture/material validity

Check:
- dimensions;
- compression/format;
- mipmaps;
- normal-map conventions;
- alpha mode;
- cubemap/environment masks;
- parallax/PBR requirements;
- referenced paths.

Visual check remains required for final material appearance.

## G14 — Animation/behavior validity

Check:
- referenced skeleton nodes;
- HKX target/version;
- OAR config parse;
- priorities;
- event/annotation names;
- Pandora patch generation;
- graph/node validation;
- output winner.

Run representative animation states in game.

## G15 — World/cell/navmesh validity

Check:
- deleted navmesh;
- door triangles/links;
- cell/world ownership;
- persistent refs;
- Room Bounds/Portals;
- water/flow data;
- landscape conflicts;
- location/ref types.

CK/game validation required for pathing and visibility.

## G16 — Quest/dialogue/scene validity

Check:
- alias IDs;
- fill strategy;
- stages/objectives;
- VMAD fragments;
- scene action alias references;
- INFO conditions;
- Story Manager entry path;
- voice asset resolution.

Runtime scenario tests required.

## G17 — Generated-output freshness

Generated artifacts declare input hashes.

Invalidate/rebuild when source changes:
- BodySlide;
- behavior output;
- Synthesis/Bashed patches;
- ParallaxGen;
- grass cache;
- TexGen/xLODGen/DynDOLOD;
- installer archive.

## G18 — Load-order and compatibility

Check:
- masters;
- LOOT metadata;
- explicit incompatibilities;
- runtime mutator overlap;
- asset overwrite winner;
- generated patch position.

LOOT success is necessary evidence, not proof of semantic compatibility.

## G19 — Crash/log cleanliness

Smoke-test run must produce:
- no crash;
- no new ERROR/FATAL in owned tool/framework logs;
- no unresolved native/Papyrus dependency;
- no generator failure.

Warnings must be classified, not ignored wholesale.

## G20 — Performance budget

Feature-specific budget:
- Papyrus update frequency;
- native hook cost;
- allocations;
- render pass GPU cost;
- script stack growth;
- actor iteration;
- load-time generation.

Capture baseline and changed result when feature can affect performance.

## G21 — Save migration

If mod persists state:
- identify persisted schema;
- assign save-data version;
- test upgrade from previous released version;
- verify missing-old-field defaults;
- verify removed fields do not corrupt load.

Never promise uninstall safety without a test.

## G22 — Packaging/FOMOD

Check:
- clean staging root;
- expected Data paths;
- installer schema;
- every option combination needed by support matrix;
- dependencies;
- version;
- README/changelog/license;
- no accidental development files.

## G23 — Release reproducibility

A release candidate must record:
- Git commit;
- manifest hash;
- tool/framework lock;
- build commands;
- input hashes;
- generated outputs;
- validation report;
- known waivers;
- tested runtimes.

## Auto-fix policy

### Safe automatic fixes
Examples:
- normalize slashes/case where semantics are known;
- rebuild stale generated output;
- regenerate an index;
- add missing derived count field;
- recompile source;
- remove a build-temp file from staging;
- forward a field when manifest has explicit source authority.

### Proposal-only fixes
Examples:
- choosing one mod's gameplay semantics over another;
- compacting FormIDs;
- changing masters;
- altering navmesh;
- changing quest stages/aliases;
- removing persistent script data;
- changing native hook location;
- destructive mesh optimization.

### Never infer silently
- target runtime;
- save-breaking migration;
- license compatibility;
- whether a visual/subjective result is acceptable.

## Gate result schema

Each result should record:
- gate id;
- status;
- severity;
- tool;
- tool version;
- command;
- inputs/hashes;
- evidence/log excerpt location;
- issue code;
- auto-fix applied;
- output hashes;
- waiver and rationale.
