# Playbook — Skyrim Mod Author Testing, Regression, and Release Validation

Updated: 2026-09-24
Status: operational authoring playbook

This is the default validation workflow Agent OS should recommend/use when helping create or modify a Skyrim mod.

## Build a reproducible test matrix

Record:
- Skyrim runtime(s);
- SKSE version(s);
- Address Library version;
- Creation Kit/xEdit/tool versions;
- mod manager;
- dependency versions;
- test profile/load order;
- generated-output versions;
- test save identity.

For native plugins, explicitly test every claimed runtime family rather than inferring SE/AE/VR support from compilation.

## Test scopes

### Structural test
- xEdit Check for Errors;
- unresolved FormIDs;
- correct masters;
- no accidental wild edits;
- expected ESL/ESM flags;
- expected FormIDs preserved;
- assets exist at referenced paths.

### Clean-install test
Install packaged release into a fresh empty test profile rather than the author's development workspace. This detects missing loose files, FaceGen, scripts, voice, configs and archive packaging mistakes.

### New-game test
Validate initialization with no previous save state.

### Existing-save upgrade test
Start from a save made with prior release, apply update and verify migrations.

### Dependency-missing test
When dependency is optional, verify graceful behavior when absent.

### Conflict test
Install representative popular mods/frameworks that edit the same subsystem and verify intended compatibility/patched behavior.

### Generated-output test
Regenerate Synthesis/BodySlide/Pandora/TexGen/DynDOLOD outputs from documented instructions and compare with expected behavior.

## Test categories

### Plugin records
Verify record changes in xEdit and in-game effects.

### Papyrus
Enable appropriate logging in test environment; verify errors, migrations, events, registrations and save/reload.

### Native SKSE
Inspect SKSE/plugin log, lifecycle initialization and serialization across save/load.

### Assets
Inspect effective file winners and validate NIF/DDS/HKX/SWF formats.

### Worldspace
Test COC/direct entry, normal travel, fast travel, save/reload, cell reset where relevant, NPC pathing, navmesh doors/borders and LOD transitions.

### NPC appearance
Test final NPC override and FaceGen on clean profile, with conflicting gameplay mod/patch.

### UI
Open/close menu repeatedly, new game/load game, controller/keyboard, different resolutions/UI scales if relevant.

### Animation/physics
Test behavior generation, OAR conditions, skeleton variants, equipment changes, save/load, actor unload/reload and high-load scenes.

### Performance
Measure frame time/memory/log spam rather than subjective smoothness only.

## Regression tests

A regression test should reproduce a previously fixed bug with:
- minimal setup;
- exact trigger;
- expected failure before fix;
- expected behavior after fix.

Store regression cases with the project, especially for:
- FormID migration;
- save updates;
- optional dependency detection;
- runtime-specific hooks;
- conflict patches;
- NPC FaceGen;
- navmesh/pathing;
- animation condition priorities;
- generated patch outputs.

## Change isolation

Change one causal variable per test. Avoid simultaneously:
- resorting plugins;
- changing asset priority;
- updating SKSE;
- rebuilding BodySlide;
- regenerating LOD;
- editing save state.
Otherwise the result cannot identify which change mattered.

## Packaging validation

Inspect final archive/package, not source directory:
- FOMOD choices;
- Data/root layout;
- DLL runtime variants;
- PEX and source policy;
- FaceGen;
- voice/FUZ;
- translations;
- MCM configs;
- INIs/JSON;
- BSA contents;
- licenses/readme;
- version metadata.

## Release versioning

### Semantic version
Use meaningful version changes where practical and document breaking migrations.

### Runtime support matrix
List exact supported Skyrim executable versions for native DLLs.

### Dependency floor
State minimum required framework versions.

### Changelog
Describe user-visible changes, fixes, compatibility changes and migration requirements.

### Upgrade instructions
State whether existing saves are supported and required steps.

### Rollback safety
Document whether reverting mod versions on an already-updated save is supported.

## Automated validation opportunities

Agent OS can automate:
- plugin master/error scan;
- FormID diff;
- record diff;
- package file manifest;
- missing referenced assets;
- duplicate/conflicting file paths;
- Papyrus compile;
- C++ build/tests;
- config grammar validation;
- generated output hash/diff;
- source/release manifest;
- reproducible test checklist.

Do not auto-approve gameplay semantics merely because structural tests pass.

## Release evidence bundle

For every significant release keep:
- source commit;
- built artifact hash;
- plugin hash;
- dependency/runtime matrix;
- xEdit validation report;
- automated test output;
- manual test checklist;
- known issues;
- migration notes;
- generated-output provenance.

This lets Agent OS reproduce and debug old versions instead of relying on memory.

## Sources
- Tome of xEdit: https://tes5edit.github.io/docs/
- SKSE: https://skse.silverlock.org/
- CommonLibSSE-NG: https://github.com/alandtse/CommonLibSSE-NG
- Mod Organizer 2: https://github.com/ModOrganizer2/modorganizer
- Wabbajack: https://github.com/wabbajack-tools/wabbajack
