# Skyrim Creation Kit Tooling and Authoring Workflow

Imported: 2026-09-24
Status: sourced authoring knowledge

## Creation Kit

### Creation Kit / CK
Bethesda editor for plugin records, cells, worldspaces, actors, quests, dialogue, navmesh, Papyrus, landscape, lighting and asset references.

### Active file
Plugin receiving newly authored edits.

### Parent masters
Loaded dependencies used as source data for the active plugin.

### Render Window
3D editor view for placed references, landscape, lighting and navmesh.

### Object Window
Record browser/editor grouped by object/form type.

### Cell View
Cell/worldspace selector plus placed-reference list.

### Reference
Placed object instance in a cell/worldspace.

### Gizmo
Editor transform control for translate/rotate/scale operations.

### Havok simulation in CK
Editor preview support for physics-enabled references. Preview behavior is not a substitute for in-game runtime testing.

### CK autosave
Editor autosave mechanism. Keep external version control/backups because autosave does not guarantee recovery from plugin corruption.

## Creation Kit Platform Extended

### CKPE
Creation Kit Platform Extended: open-source collection of fixes, enhancements and reverse-engineered resources for Bethesda Creation Kit versions, successor to prior SSE CK fixes projects.

### CK runtime/version matching
CKPE builds target particular Creation Kit versions/CPU capabilities; editor extensions should be version-matched like game native plugins.

### no-AVX2 build
Compatibility build for CPUs lacking AVX2.

### Editor patch
Runtime/binary patch to the Creation Kit executable, distinct from a game mod.

### Unicode/editor enhancement
CKPE lineage includes fixes enhancing editor behavior such as Unicode support and stability/performance improvements.

## Plugin authoring workflow

1. Define scope and masters.
2. Create dedicated working plugin/branch.
3. Make small edits.
4. Save and inspect in xEdit.
5. Check accidental overrides/ITMs.
6. Test in a controlled profile.
7. Generate external assets as required.
8. Validate packaging.
9. Re-test on new game and relevant existing-save migration scenario.
10. Commit/tag known-good states.

### xEdit post-save inspection
Open the plugin after CK edits to verify only intended records changed.

### Accidental edit
Record touched unintentionally by CK/render-window operations.

### Dirty edit
Unwanted override introduced during authoring. Not every override is dirty.

### External asset
File not fully represented in plugin data, such as scripts, FaceGen, meshes, textures, voice, behavior, SKSE DLL/config, JSON/INI.

### Packaging audit
Explicit comparison of required external files against final archive. CK packaging historically misses FaceGen, sound/voice and some scripts.

### Dependency audit
Verify every master/API/framework dependency is actually required and documented.

### Runtime test matrix
Test across exact supported Skyrim runtimes when distributing native SKSE functionality.

## Papyrus authoring

### Papyrus compiler
Compiles PSC source into PEX bytecode.

### Import path
Compiler source directories searched for parent scripts/types.

### Flags file
Compiler configuration defining special flags/annotations.

### Compile-time error
Papyrus source fails type/syntax/identifier checks.

### Runtime error
Compiled script executes but encounters invalid state such as None access, missing form, invalid cast, bad lifecycle assumption.

### Fragment
CK-generated Papyrus source associated with quest/dialogue/package/scene editor contexts.

### Generated fragment class
Compiler-generated script class name; source/output files should be treated as CK-owned artifacts where applicable.

### Source control
Keep PSC source even when shipping only PEX, and version source alongside plugin changes.

## Data-generation tools

### xEdit script
Automation written for xEdit's scripting API, commonly Pascal-style, to inspect/modify large record sets.

### Automation patcher
Script/program generating deterministic plugin changes from input load order.

### Mutagen patcher
.NET code using Mutagen typed records.

### Synthesis pipeline
Orchestrated execution of one or more patchers against current load order.

### Generated plugin provenance
Record generator name/version/commit/settings and input load order so output can be reproduced.

## Quality gates

- Plugin loads with all masters.
- xEdit reports no unexpected unresolved references.
- Intentional conflict decisions documented.
- Scripts compile from source.
- External assets present.
- FaceGen generated where NPC faces changed.
- Voice assets present where dialogue expects them.
- Navmesh finalized and path tested.
- LOD regenerated where required.
- Native runtime matrix tested if applicable.
- Logs free of new known errors in target scenarios.
- Clean profile/new game smoke test passes.
- Upgrade/migration test passes if mod supports existing saves.

## Sources

- Creation Kit Wiki File Menu: https://ck.uesp.net/wiki/File_menu
- Creation Kit Wiki Cell View: https://ck.uesp.net/wiki/Cell_View_Window
- Creation Kit Wiki Papyrus compiler/Notepad++ setup: https://ck.uesp.net/wiki/Notepad%2B%2B_Setup
- Creation Kit Platform Extended: https://github.com/Perchik71/Creation-Kit-Platform-Extended
- Tome of xEdit: https://tes5edit.github.io/docs/
- Synthesis docs: https://mutagen-modding.github.io/Synthesis/
