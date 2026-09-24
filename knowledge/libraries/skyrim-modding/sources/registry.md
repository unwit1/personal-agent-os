# Skyrim Modding Source Registry

Updated: 2026-09-24

This registry records source classes used by the Skyrim Modding Knowledge Repository. It is not a claim that every page is equally authoritative. Source quality is evaluated per claim and version.

| Source | Type | Default confidence | Best use | Important caveats |
|---|---|---:|---|---|
| Bethesda game data / Creation Kit | primary | very high | record behavior, editor workflows, shipped structures | CK bugs and undocumented engine behavior still require testing |
| Creation Kit Wiki archive/mirror at ck.uesp.net | historical documentation/community-maintained mirror | high for documented editor concepts; medium for old tutorials | CK terminology, Papyrus, editor UI, record concepts | many pages originated during LE-era development; some are incomplete, outdated, or community-authored |
| Tome of xEdit / xEdit docs | upstream specialist documentation | very high for xEdit/plugin-data behavior | conflicts, overrides, cleaning, ESL/ESM behavior, FormID interpretation | some material spans multiple Bethesda games; verify game/version scope |
| xEdit source/releases | upstream source/tool evidence | very high | exact current tool behavior | implementation can change by release |
| SKSE official site | upstream project | very high | supported runtime/build compatibility, official SKSE releases | focuses on SKSE distribution/support rather than comprehensive plugin-development documentation |
| SKSE source code | upstream source | very high | native API and runtime-extension implementation | version-specific and requires technical interpretation |
| CommonLibSSE / CommonLibSSE-NG source/docs | upstream/community reverse-engineering library | high to very high | native plugin development, engine types, relocations, cross-runtime code | names/types model reverse-engineered engine structures and can change |
| DynDOLOD documentation | maintained specialist technical documentation | very high for LOD workflows | LOD terminology, generation, diagnostics | deliberately opinionated in places; use factual technical sections as evidence |
| Mod Organizer 2 / USVFS source/docs | upstream project | very high | VFS, virtualization, MO2 output/overwrite concepts | behavior may vary by tool/process and MO2 version |
| Open Animation Replacer source/docs | upstream project | very high for OAR behavior | conditional animation replacement and OAR terminology | not a general authority for all Skyrim animation systems |
| Nexus mod pages | mod-author documentation | high for that mod, variable otherwise | requirements, configuration, compatibility statements, changelogs | author claims may be incomplete or stale; not automatically authoritative about other mods |
| GitHub mod/tool repositories | upstream source when official repo | high to very high | code, releases, schema/config behavior | forks and abandoned repos must be distinguished from canonical upstream |
| UESP | maintained reference wiki | high for game/lore/reference data | game records, mechanics, names, cross-references | not primarily a technical modding specification |
| STEP guides | curated community documentation | medium to high | installation workflows and tested modding practices | guide-specific and can lag tool/runtime updates |
| AFKTrack / Bethesda forum archives / specialist forums | community technical archive | medium | historical engine discoveries and author explanations | availability, age, and version scope vary |
| r/skyrimmods / Reddit | community evidence | low to medium until corroborated | finding leads, current user reports, niche troubleshooting | anecdotal; popularity is not validation |
| Discord conversations | community evidence | low to high depending on speaker/evidence | current tool-author guidance, niche discoveries | difficult provenance and ephemerality; preserve speaker/date/context |
| User's own controlled tests | primary local evidence | high when reproducible | project-specific behavior, regression tests, compatibility findings | scope must include runtime, tool versions, mod list, reproduction steps |
| Crash logs / tool logs | primary diagnostic evidence | high for observed state | root-cause investigation and reproduction | interpretation can be uncertain; one log rarely proves general behavior |

## Current registered sources

### CK-FILE
- URL: https://ck.uesp.net/wiki/File_menu
- Scope: data files, active file, parent masters, CK archive packaging, asset paths.
- Notes: page itself warns that parts may be incomplete/inaccurate; use cautiously for packaging edge cases.

### CK-CELL
- URL: https://ck.uesp.net/wiki/Cell_View_Window
- Scope: cells, FormID/EditorID display, placed object/reference properties.

### CK-RETEXTURE
- URL: https://ck.uesp.net/wiki/Retexture_Tutorial
- Scope: NIF/DDS/texture workflow terminology.
- Notes: historical tutorial; retain terminology, not every workflow recommendation.

### CK-PAPYRUS
- URL: https://ck.uesp.net/wiki/Operator_Reference
- Scope: Papyrus syntax/language concepts.
- Notes: pair with dedicated Papyrus pages in later passes.

### CK-COMPILER
- URL: https://ck.uesp.net/wiki/Notepad%2B%2B_Setup
- Scope: Papyrus compilation/source/output path context.
- Notes: tool setup is historical; file-role concepts remain useful.

### CK-PAPYRUS-LOG
- URL: https://ck.uesp.net/wiki/User%3ADavidJCobb/Papyrus_logging
- Scope: Papyrus logging and diagnostic interpretation.
- Notes: user-authored specialist documentation, not Bethesda-authored.

### CK-SKSE-RESOURCES
- URL: https://ck.uesp.net/wiki/SKSE_Plugin_Development/Resources
- Scope: SKSE/CommonLib development-source landscape.
- Notes: explicitly notes that no single definitive SKSE-plugin-development resource exists.

### XEDIT-DOCS
- URL: https://tes5edit.github.io/docs/
- Scope: xEdit fundamentals, conflict analysis, cleaning, patches.

### XEDIT-METHOD
- URL: https://tes5edit.github.io/docs/6-themethod.html
- Scope: master records, conflict winners/losers, ModGroups, intentional conflicts.

### XEDIT-CONFLICTS
- URL: https://tes5edit.github.io/docs/5-conflict-detection-and-resolution.html
- Scope: overrides vs conflicts, conflict filtering, patch plugins, runtime merge concepts.

### XEDIT-WHATSNEW
- URL: https://tes5edit.github.io/whatsnew.html
- Scope: ESL mapping, Quick Clean, ITM behavior and current/historical xEdit changes.

### XEDIT-ESL
- URL: https://tes5edit.github.io/docs/11-appendix.html
- Scope: distinction between ESL and ESM behavior, load-order blocks, FormID mapping.
- Notes: important correction source for common community shorthand.

### SKSE-OFFICIAL
- URL: https://skse.silverlock.org/
- Scope: SKSE release/runtime compatibility and official support status.
- Snapshot note: on 2026-09-24, the site listed AE build 2.3.1 for game runtime 1.7.104, GOG AE 2.2.6 for 1.6.1179, SE 2.0.20 for 1.5.97, and VR 2.0.12 for 1.4.15. Store this as time-sensitive version metadata, not timeless terminology.

### MO2-USVFS
- URL: https://github.com/ModOrganizer2/usvfs/blob/master/README.md
- Scope: MO2 virtual file system architecture and overlay behavior.

### MO2-RELEASES
- URL: https://github.com/ModOrganizer2/modorganizer/releases
- Scope: current/recent Mod Organizer behavior and compatibility notes.
- Notes: time-sensitive.

### DYNDOLOD-REFERENCE
- URL: https://dyndolod.info/DynDOLOD-Reference
- Scope: xLODGen, DynDOLOD, LODGen, terrain/object/tree LOD roles.

### DYNDOLOD-TERMS
- URL: https://dyndolod.info/Terminology
- Scope: specialized LOD and exterior-cell terminology.

### DYNDOLOD-TREE
- URL: https://dyndolod.info/Help/Tree-LOD
- Scope: tree LOD, billboards, tree LOD files.

### DYNDOLOD-OBJECT
- URL: https://dyndolod.info/Help/Object-LOD
- Scope: object LOD and object LOD assets.

### DYNDOLOD-TERRAIN
- URL: https://dyndolod.info/Help/Terrain-LOD-and-Water-LOD
- Scope: terrain and water LOD.

### OAR-UPSTREAM
- URL: https://github.com/ersh1/OpenAnimationReplacer/blob/main/README.md
- Scope: OAR role, conditions-based animation replacement, native-plugin requirements.


### COMMONLIB-NG
- URL: https://github.com/alandtse/CommonLibSSE-NG
- Scope: current multi-runtime CommonLibSSE-NG architecture, runtime targeting, RE/REL/SKSE abstractions, build integration, reverse-engineered engine types.
- Notes: active upstream/fork ecosystem; record exact branch/release because ABI support and APIs evolve.

### SKSE-PLUGIN-API
- URL: https://github.com/ianpatt/skse64/blob/master/skse64/PluginAPI.h
- Scope: SKSE native plugin interfaces, messaging, serialization, task/trampoline/Papyrus integration concepts.
- Notes: historical source remains useful for API lineage; current CommonLib wrappers may be the better implementation reference.

### ADDRESS-LIBRARY
- URL: https://www.nexusmods.com/skyrimspecialedition/mods/32444
- Scope: stable ID to runtime-specific address/offset mapping for native SKSE plugins.
- Notes: time-sensitive runtime coverage; exact database/version must match supported executables.

### CRASHLOGGER-SSE
- URL: https://github.com/alandtse/CrashLoggerSSE
- Scope: native crash logging, PDB/symbol usage, module/stack/register evidence.
- Notes: a stack/module mention is evidence of involvement, not automatic proof of root cause.

### LOOT-LOAD-ORDER
- URL: https://loot.github.io/docs/help/introduction-to-load-orders/
- Scope: plugin load-order concepts, override ordering, dependency constraints, LOOT metadata.
- Notes: LOOT solves ordering/metadata problems; use xEdit for semantic record conflict analysis.

### SPID-UPSTREAM
- URL: https://github.com/powerof3/Spell-Perk-Item-Distributor
- Scope: runtime distribution of spells, perks, items, shouts, packages, outfits, keywords, factions, and related NPC data.
- Notes: pair implementation/source with current user-facing Nexus documentation for config grammar.

### SPID-NEXUS
- URL: https://www.nexusmods.com/skyrimspecialedition/mods/36869
- Scope: current SPID user configuration syntax, filters, supported distributions, changelog/runtime support.
- Snapshot note: observed version 7.3.3 on 2026-09-24, updated 2026-08-26. Treat as a dated snapshot.

### KID-UPSTREAM
- URL: https://github.com/powerof3/Keyword-Item-Distributor
- Scope: runtime keyword distribution implementation and build/runtime dependencies.

### KID-NEXUS
- URL: https://www.nexusmods.com/skyrimspecialedition/mods/55728
- Scope: current KID filter grammar, target form types, traits, dynamically generated keywords, chance behavior.
- Snapshot note: observed version 4.1.0 on 2026-09-24, updated 2026-08-25. Treat as a dated snapshot.

### BOS-UPSTREAM
- URL: https://github.com/powerof3/BaseObjectSwapper
- Scope: runtime base-form swapping implementation and supported runtime families.

### BOS-NEXUS
- URL: https://www.nexusmods.com/skyrimspecialedition/mods/60805
- Scope: current BOS swap syntax, reference/form/location filters, transform overrides, chance modes, config conflicts.
- Snapshot note: current documentation observed on 2026-09-24 includes 3.5.0-era Skyrim 1.7.99+ support notes.

### FLM-UPSTREAM
- URL: https://github.com/MaskedRPGFan/FormList-Manipulator
- Scope: runtime FormList mutation, aliases, groups, collections, filters, mod-event updates, processing order.
- Notes: distinguish original framework semantics from runtime-port/build compatibility.

### FLM-NEXUS
- URL: https://www.nexusmods.com/skyrimspecialedition/mods/74037
- Scope: current user-facing FormList Manipulator configuration and compatibility documentation.

### OCF-UPSTREAM
- URL: https://github.com/GroundAura/Object-Categorization-Framework
- Scope: ecosystem example of semantic categorization using shared keywords/FormLists and runtime distributors.
- Notes: use primarily as an integration/design-pattern source, not as an engine specification.

### PANDORA-UPSTREAM
- URL: https://github.com/Monitor221hz/Pandora-Behaviour-Engine-Plus
- Scope: modern Havok behavior patching/generation, Nemesis/FNIS-compatible patch formats, graph processing.
- Notes: active project; capabilities and patch grammar can change quickly.

### NIFSKOPE-UPSTREAM
- URL: https://github.com/niftools/nifskope
- Scope: NIF block/scene-graph inspection and editing, NIF structure terminology.
- Notes: NifSkope is a format/editor authority, not by itself proof of game-runtime semantics.

### BODYSLIDE-UPSTREAM
- URL: https://github.com/ousnius/BodySlide-and-Outfit-Studio
- Scope: BodySlide/Outfit Studio project, slider, morph, weight, conversion, and generated-mesh terminology.
- Notes: pair with project wiki for authoring workflows.

### SKYUI-UPSTREAM
- URL: https://github.com/schlangster/skyui
- Scope: SkyUI and MCM architecture/history, Skyrim Scaleform/UI integration.
- Notes: repository history is valuable, but current compatibility may depend on maintained forks/builds and runtime environment.

### MCM-HELPER
- URL: https://github.com/Exit-9B/MCM-Helper
- Scope: configuration-driven MCM creation/settings persistence and current helper framework concepts.
- Notes: framework-specific persistence behavior should not be generalized to every MCM.

## Planned source expansion

Next source-registration passes should prioritize areas not yet covered deeply:

- Creation Kit navmesh, worldspace, landscape, cell, dialogue/scene/package, condition, leveled-list, and save/persistence references;
- RaceMenu/NetImmerse Override, TRI/BodyMorph, head-part and FaceGen internals;
- animation graph/behavior internals beyond tool-level documentation, including animation events and graph variables;
- Community Shaders and ENB;
- xLODGen/DynDOLOD detailed error references, large references, occlusion, grass cache/grass LOD;
- Vortex deployment model in addition to MO2/USVFS;
- Wabbajack and mod-list packaging concepts;
- save-game structure, ReSaver/FallrimTools, changeforms, orphaned script instances, and persistence diagnostics;
- audio/voice formats and dialogue generation assets such as FUZ/LIP/XWM;
- SKSE co-save structure, serialization versioning, and migration practices;
- Trainwreck and other crash-loggers as comparative diagnostic sources;
- current Creation Kit Platform Extended / CK extension tooling where relevant.
