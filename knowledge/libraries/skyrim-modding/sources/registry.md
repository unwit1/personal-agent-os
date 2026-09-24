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

## Planned source expansion

Next source-registration passes should include upstream/current references for:

- CommonLibSSE-NG and Address Library;
- SKSE source and plugin API;
- Creation Kit quest, dialogue, scene, package, navmesh, condition, worldspace, leveled-list, and Papyrus reference pages;
- NifSkope/NIF format documentation;
- BodySlide/Outfit Studio;
- RaceMenu/NetImmerse Override where relevant;
- SkyUI/MCM and Scaleform;
- Behavior/animation tooling including OAR, Nemesis, Pandora, hkxcmd-equivalent/current tools where applicable;
- SPID, KID, BOS, FLM;
- LOOT;
- Crash Logger SSE AE VR / Trainwreck and interpreting native crash logs;
- Community Shaders and ENB;
- xLODGen/DynDOLOD detailed error references;
- Wabbajack and mod-list packaging concepts.
