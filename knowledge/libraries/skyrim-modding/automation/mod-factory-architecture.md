# Skyrim Mod Factory — Automation Architecture

Created: 2026-09-24
Status: canonical design for highly automated Skyrim mod creation

## Goal

Turn a mod idea into a reproducible, testable, packageable implementation with the maximum amount of deterministic automation that is practical.

The system should answer, before implementation begins:

- what kind of mod this is;
- which Skyrim runtimes it targets;
- whether it needs ESP/ESM/ESL data, Papyrus, an SKSE DLL, assets, behavior edits, UI, runtime distribution, generated patches, or some combination;
- which tools/frameworks are appropriate;
- which parts can be generated automatically;
- which schemas must be validated;
- which conflicts and persistence hazards are likely;
- what tests prove the feature works;
- what evidence is required before release.

The Mod Factory is not a separate knowledge system. It consumes the Skyrim Modding Knowledge Repository through the Knowledge Engine and emits durable project state, reports, artifacts, and validated findings.

## Design principle

Every project is treated as a typed build graph:

idea -> requirements -> architecture -> source inputs -> generated/edited artifacts -> static validation -> integration validation -> game/CK validation -> package -> release evidence

Each node records:
- provenance;
- tool/version;
- input hashes;
- output hashes;
- warnings/errors;
- validation state;
- whether output is reproducible;
- whether a human/visual/game check remains.

## Phase 0 — Idea intake

Input can be natural language, e.g.:

> Make enemies sometimes drop enchanted broken weapon fragments that can be reforged.

Agent extracts:
- gameplay intent;
- scope;
- expected player-facing behavior;
- persistent state;
- distribution rules;
- UI requirements;
- world edits;
- animation/mesh/audio needs;
- compatibility constraints;
- likely implementation families.

Output: `skyrim-mod-project-v1` manifest candidate.

## Phase 1 — Capability decomposition

Classify each requested feature into one or more implementation layers:

1. plugin records;
2. runtime distribution/patching;
3. Papyrus;
4. native SKSE/CommonLib;
5. UI;
6. animation/behavior;
7. mesh/texture/material;
8. physics;
9. worldspace/cell/navmesh;
10. quest/dialogue/scene;
11. voice/audio;
12. LOD/grass/seasons;
13. installer/package;
14. save migration/persistence;
15. compatibility patching.

Never choose a tool before the feature layer is identified.

## Phase 2 — Implementation selection

Prefer the least invasive layer that satisfies the feature.

Examples:

### Data-only change
Prefer:
- Mutagen/xEdit-generated plugin;
- Synthesis if result depends on user's load order;
- runtime patcher only if dynamic installation compatibility is materially better.

### Distribution-only change
Consider:
- SPID for actors/perks/spells/items/outfits supported by its rules;
- KID for keyword distribution to supported item types;
- BOS for base-object swaps;
- FLM for FormList mutation;
- SkyPatcher for supported record/runtime patch domains.

### Animation replacement
Prefer OAR when behavior graph changes are unnecessary.

### Behavior graph change
Use Pandora-compatible behavior patching and validate graph output.

### Scriptable gameplay
Papyrus first when timing/performance/lifecycle needs are appropriate.

### Engine hook or performance-sensitive feature
CommonLibSSE-NG/SKSE native plugin when Papyrus/data cannot provide correct behavior.

### Mesh/morph generation
Prefer PyNifly/Nifly automation where possible; Blender/Outfit Studio only for authoring steps requiring geometry work.

### World/navmesh/dialogue authoring
Use CK/CKPE for editor-owned semantics and validate output afterward in xEdit and in game.

## Phase 3 — Question preemption

Before code generation, the planner resolves or explicitly marks unknown:

- target executable versions;
- SE/AE/GOG/VR support;
- ESL/ESP/ESM policy;
- masters;
- expected load-order behavior;
- static vs runtime mutation;
- save persistence;
- Papyrus/native dependencies;
- third-party framework availability;
- required assets;
- generated outputs;
- conflict surfaces;
- patch strategy;
- uninstall/update behavior;
- test fixtures;
- licensing/distribution constraints.

If an unknown is low-risk and inferable, choose a documented default.
If it can change save compatibility, runtime support, licensing, or architecture, create a blocking question/candidate rather than silently guessing.

## Phase 4 — Source lock

Before generation:
- pin upstream framework/tool versions;
- record target Skyrim executable;
- record SKSE and Address Library family;
- hash source plugins/assets;
- snapshot xEdit schema version;
- snapshot config grammar versions.

Generated artifacts without a source lock are non-reproducible.

## Phase 5 — Build graph generation

The planner emits ordered tasks with dependencies.

Example:

1. generate plugin records;
2. compile Papyrus;
3. run xEdit structural validation;
4. generate OAR config;
5. validate asset paths;
6. run behavior generation if needed;
7. run Synthesis compatibility patch;
8. generate LOD if world assets changed;
9. build FOMOD;
10. launch automated smoke-test profile;
11. inspect logs/crash output;
12. package candidate.

Outputs should be invalidated only when an upstream dependency changes.

## Phase 6 — Artifact generation

Supported generation families should include:

### Plugin generation
Preferred deterministic backends:
- Mutagen;
- xEdit scripting/export tooling;
- Synthesis for load-order-derived output.

CK should not be required merely to create simple deterministic records that a schema-aware writer can safely produce.

### Papyrus
- generate PSC;
- format/lint;
- compile against pinned declaration roots;
- inspect PEX metadata;
- reject unresolved dependency/native declarations;
- test registration/persistence lifecycle.

### Native plugin
- generate CommonLibSSE-NG skeleton;
- declare runtime matrix;
- compile all target presets;
- run unit tests;
- scan imports/dependencies;
- verify SKSE plugin metadata;
- verify relocations/API dependencies.

### Config frameworks
Generate and validate:
- SPID;
- KID;
- BOS;
- FLM;
- SkyPatcher;
- OAR;
- MCM/JSON/INI;
- LOOT metadata;
- FOMOD XML.

### Assets
Generate/transform/validate:
- NIF;
- TRI;
- DDS;
- HKX;
- WAV/XWM/FUZ/LIP where supported;
- FaceGen;
- BodySlide projects/output;
- LOD source/output.

## Phase 7 — Static validation gates

All projects run every applicable gate.

At minimum:
- JSON/schema validity;
- manifest completeness;
- plugin schema;
- master resolution;
- unresolved FormIDs;
- ESL/FormID range;
- accidental ITM/deletion checks;
- asset path existence;
- case/path normalization;
- BSA/package presence;
- PSC compile;
- native build;
- config grammar;
- behavior graph validation;
- NIF structural checks;
- texture format/mipmap checks;
- installer schema;
- dependency declaration;
- license/source attribution.

See `validation-gates.md`.

## Phase 8 — Cross-layer validation

The agent checks relationships that no single tool can prove:

- NPC appearance record matches FaceGen assets;
- ARMO slots match ARMA and mesh partitions;
- skeleton nodes referenced by animation/physics/display configs exist;
- INFO voice path matches plugin identity and VoiceType;
- MGEF visual assets exist;
- quest alias IDs match fragments/scenes;
- DOBJ/default-object references resolve;
- runtime distributor targets exist;
- generated plugin sees final load order;
- DynDOLOD/TexGen input matches current asset winner;
- save migration strategy matches persisted state.

## Phase 9 — Compatibility simulation

Use declared touch-set to predict conflict surfaces.

For each changed domain:
- records touched;
- fields touched;
- assets written;
- runtime mutations;
- configs injected;
- save state;
- generated outputs.

Then compare against:
- user's active modlist when available;
- known project dependencies;
- Simonrim rules where appropriate;
- popular framework overlaps;
- existing patches.

Output:
- compatible;
- requires ordering;
- requires patch;
- mutually exclusive;
- runtime conflict possible;
- unknown / needs test.

## Phase 10 — Automated test profile

A dedicated MO2 profile should support:
- target mod + minimum dependencies;
- target mod + representative conflict fixtures;
- target mod + user's real load order;
- new-game smoke save;
- established migration save where required.

MO2 can select profiles and run configured executables from the command line, which makes it suitable as the launcher boundary for automated test runs.

## Phase 11 — Runtime observation

Collect:
- SKSE logs;
- plugin logs;
- Papyrus logs only when diagnostic build enables them;
- Crash Logger;
- animation generator logs;
- OAR logs/debug state;
- framework logs;
- generated output manifests;
- screenshots or state probes when useful.

A successful launch is not sufficient.

## Phase 12 — Assertions

Where possible, build observable assertions:

Examples:
- Form exists and has expected fields;
- expected actor receives keyword/perk/spell;
- actor does not receive it when filter fails;
- item appears in expected leveled list;
- OAR condition selects expected submod;
- quest reaches expected stage;
- DLL interface reports ready;
- config parser reports N accepted / 0 rejected;
- no unresolved forms;
- no unexpected asset overwrite;
- frame budget remains under configured threshold.

## Phase 13 — Auto-debug / repair

Failures enter the repair loop:
- classify layer;
- preserve exact first error;
- map to known error catalog;
- identify smallest likely cause;
- repair only reversible/local artifacts automatically;
- rebuild downstream graph;
- rerun affected gates;
- compare before/after evidence.

See `autonomous-debug-repair-loop.md`.

## Phase 14 — Release candidate

Release is blocked until:
- all mandatory gates pass;
- known warnings are dispositioned;
- runtime matrix is accurate;
- dependencies are explicit;
- generated outputs are current;
- installer validates;
- changelog exists;
- update/uninstall notes exist when persistence is involved;
- provenance/build report is stored.

## Phase 15 — Post-release learning

Bug reports should be ingested as structured evidence:
- exact version;
- runtime;
- load order;
- logs;
- reproduction;
- root cause;
- fix;
- regression test.

Validated fixes become reusable checks so the same bug class is prevented in later projects.

## Human-required or supervised areas

Automation should be aggressive but not dishonest. Some outputs still warrant direct CK/game inspection:

- spatial aesthetics;
- navmesh traversal/finalization behavior;
- quest/scene pacing;
- dialogue timing;
- animation feel/contact quality;
- visual clipping;
- shader appearance;
- physics stability;
- VR comfort/interaction;
- performance under representative gameplay;
- subjective balance.

The agent should generate the test plan and evidence capture even when it cannot prove the result statically.

## Canonical interfaces

Suggested provider-independent interfaces:

- `skyrim.mod.plan`
- `skyrim.mod.manifest.validate`
- `skyrim.mod.tool.select`
- `skyrim.mod.build`
- `skyrim.mod.generate.plugin`
- `skyrim.mod.compile.papyrus`
- `skyrim.mod.compile.native`
- `skyrim.mod.generate.config`
- `skyrim.mod.validate.schema`
- `skyrim.mod.validate.assets`
- `skyrim.mod.validate.compatibility`
- `skyrim.mod.test.smoke`
- `skyrim.mod.test.regression`
- `skyrim.mod.debug.classify`
- `skyrim.mod.repair.propose`
- `skyrim.mod.repair.apply`
- `skyrim.mod.package`
- `skyrim.mod.release.audit`

## Success condition

The desired user experience is:

> “I have an idea for a mod that does X.”

Agent OS should be able to respond with a grounded architecture, select the lowest-risk implementation, generate most of the project, run static/tool validation, launch the right test profile, interpret failures, repair deterministic problems, and return only the genuinely human decisions or in-game observations that remain.


## AI-native execution planes

The Mod Factory should no longer assume that the agent only edits files and launches CLIs. It can use typed AI-facing tool planes where available.

### Static data plane
Preferred: houseCARL/Mutagen/Spriggit adapters.

Responsibilities:
- inspect the actual MO2 load order and VFS;
- query winners/override chains;
- perform typed dry-run record mutations;
- create isolated patch outputs;
- read output back.

### Schema oracle plane
Preferred: xEdit/xDump, with independent Mutagen/Spriggit round-trip checks.

Responsibilities:
- reject structural invalidity;
- expose definition/coverage gaps;
- provide a second implementation independent of the authoring tool.

### Runtime test plane
Preferred: devbench. Secondary: SkyLink AI; project-specific: SkyrimNet; fallback suites: AutoTest.

Responsibilities:
- drive fixture saves/scenarios;
- wait on real events;
- query live game state;
- read console/Papyrus results;
- detect stalls;
- collect runtime evidence;
- support record/replay and A/B testing where available.

Executable baseline:
- `run_mo2_runtime_session.py` owns the disposable profile, fixture, process boundary, evidence snapshots and cleanup;
- `run_devbench_runtime_observer.py` owns typed in-game actions/probes/assertions;
- `run_mo2_devbench_runtime.py` composes both rather than treating them as interchangeable adapters;
- optional `performance_capture.provider=presentmon` starts PresentMon only after fresh DevBench health identifies the launched game PID, summarizes target-PID frames into `skyrim-frame-trace-summary-v1`, and feeds G20 without overriding explicit failed performance assertions;
- missing runtime/performance evidence remains unproven rather than being silently promoted to PASS.

### 3D AI plane
Blender MCP + PyNifly/Nifly.

Responsibilities:
- let the agent inspect/edit source geometry;
- render previews;
- automate transforms/material/rig/animation work;
- export to staging.

NIF-specific independent checks remain mandatory. Cheap deterministic asset guards should run before heavier visual/runtime checks: the DDS structural validator rejects malformed/truncated or generation-incompatible texture containers, while the FaceGen coherence validator checks defining-plugin/local-FormID paths, NIF+DDS pairing and optional approved fingerprints. Neither substitutes for decoded-channel, NIF semantic, or in-game visual validation.

### Papyrus AI plane
Papyrus language tooling + pinned provider index + compiler/runtime debugger.

The model must query the provider corpus instead of inventing function signatures.

### Voice AI plane
VOSpeaker/xVASynth or another approved synthesis backend.

Dialogue identity and packaging are deterministic; voice quality and rights remain explicit gates.

## Agent planning requirement

For every feature, the planner must:

1. search the implementation-pattern registry;
2. inspect available installed adapters/capabilities;
3. inspect current project/load-order context;
4. choose the least invasive implementation;
5. list independent validators;
6. generate negative tests;
7. generate runtime assertions when static evidence is insufficient;
8. identify only the genuinely creative or product-level unknowns.

The planner should not ask the user:
- which tool writes a plugin field;
- how to name a voice path;
- whether a FormID resolves;
- which Papyrus API exists;
- what OAR/SPID/KID syntax is;
- whether an output is stale;
- which record wins;
- whether a generated NIF references a missing texture;

when an installed adapter or knowledge source can answer deterministically.

## Closed-loop build requirement

A feature is not complete until the loop has reached the strongest applicable evidence level:

**source intent -> typed generation -> independent static validation -> generated-output freshness -> runtime assertion -> human subjective check only where necessary**

When runtime testing is possible through devbench/SkyLink/etc., the default should be to execute it instead of returning an untested instruction for the user to reproduce manually.

## Schema confidence

Use the confidence levels from `schema-triangulation-and-self-checks.md`:

- A: generated + one parser;
- B: two independent parsers;
- C: two parsers + round-trip + intent diff;
- D: C + runtime assertion.

Default release target:
- structured plugin/config output: C;
- gameplay/native/save-critical behavior: D.

