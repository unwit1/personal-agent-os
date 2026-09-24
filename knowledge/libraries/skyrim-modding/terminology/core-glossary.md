# Core Skyrim Modding Glossary — Pass 1

Imported: 2026-09-24
Status: sourced foundation
Scope: Skyrim/TES5, Skyrim Special Edition, Anniversary Edition, GOG where applicable, and VR where explicitly noted.

This glossary normalizes common terms so Agent OS can resolve shorthand, aliases, and closely related concepts during troubleshooting and design work. Definitions are concise summaries, not copied documentation.

## Plugin and record architecture

### Plugin / module
**Aliases:** data file, plugin file, module  
A file that contains Bethesda game records and/or overrides, commonly using `.esp`, `.esm`, or `.esl`. The extension and in-memory flags affect how the engine treats the module.  
**Tags:** plugin, records, load-order  
**Sources:** XEDIT-ESL, CK-FILE

### ESP
**Aliases:** plugin, .esp  
A Bethesda plugin file. An `.esp` can behave as a normal non-master plugin, can carry the ESM flag, and in Skyrim SE/AE can carry the ESL flag. The filename extension alone does not fully describe its runtime behavior.  
**Tags:** plugin, esp  
**Sources:** XEDIT-ESL

### ESM
**Aliases:** master, .esm  
A module treated as a master. In modern Skyrim terminology, ESM behavior is controlled by the ESM state seen by the engine; `.esm` files are force-treated as ESM in memory. ESMs are placed in the master block before non-ESM plugins.  
**Tags:** plugin, master, load-order  
**Sources:** XEDIT-ESL

### ESL
**Aliases:** light master, .esl  
A module using the light-plugin FormID space. The `.esl` extension implicitly causes the ESM and ESL behavior expected for a light master. The ESL state primarily changes FormID mapping/light-slot usage; it is not itself a simple “late-load” rule.  
**Tags:** plugin, light-plugin, formid  
**Sources:** XEDIT-ESL, XEDIT-WHATSNEW

### ESP-FE
**Aliases:** ESL-flagged ESP, light ESP  
Community shorthand for an `.esp` carrying the ESL flag. It consumes a light slot rather than a normal full plugin slot while retaining `.esp` extension semantics.  
**Tags:** plugin, light-plugin, formid  
**Sources:** XEDIT-ESL, XEDIT-WHATSNEW

### Light plugin
A plugin whose FormIDs are mapped into the FE light-plugin space because the ESL flag is active. xEdit documents up to 4096 light-module indices in that mapping scheme.  
**Tags:** plugin, light-plugin, formid  
**Sources:** XEDIT-WHATSNEW

### Full plugin
A plugin mapped into a normal full load-order slot rather than the FE light-plugin space.  
**Tags:** plugin, load-order, formid  
**Sources:** XEDIT-WHATSNEW

### Master / parent master
A plugin required by another plugin. The Creation Kit lists these as parent masters and loads them when the dependent plugin is loaded.  
**Tags:** dependency, plugin  
**Sources:** CK-FILE

### Active File
The plugin selected in the Creation Kit as the destination for edits made during the current editing session.  
**Tags:** creation-kit, plugin-authoring  
**Sources:** CK-FILE

### Record
A structured game-data object stored in a plugin, such as a weapon, NPC, quest, cell, spell, placed reference, keyword, leveled list, or worldspace entry. Records can originate in one plugin and be overridden by later plugins.  
**Tags:** records, plugin  
**Sources:** XEDIT-METHOD, CK-CELL

### Record type / signature
The category identifying the structure and purpose of a record. Examples commonly encountered in xEdit include records for statics, references, quests, cells, worldspaces, leveled lists, keywords, and many others.  
**Tags:** records, xedit  
**Sources:** XEDIT-DOCS

### FormID
The numeric identifier used to refer to a game form/record. Its loaded value incorporates plugin mapping, so the visible leading portion can depend on load order or light-plugin mapping.  
**Tags:** records, formid  
**Sources:** CK-CELL, XEDIT-WHATSNEW

### ObjectID
The plugin-local portion of a FormID used for records created in that plugin. xEdit's ESL compatibility checks are constrained by the light-plugin ObjectID space.  
**Tags:** formid, light-plugin  
**Sources:** XEDIT-WHATSNEW

### EditorID
**Aliases:** EDID  
A human-readable identifier assigned to many records for editor/tool lookup. It is distinct from the numeric FormID.  
**Tags:** records, creation-kit  
**Sources:** CK-CELL, XEDIT-WHATSNEW

### Base record / base form
The definition of an object or concept, as distinct from an individual placed instance/reference in the game world. A placed tree, door, NPC reference, container, or static may point to a base record describing what it is.  
**Tags:** records, references  
**Sources:** DYNDOLOD-TREE, CK-CELL

### Reference / placed reference
**Aliases:** ref, REFR in many xEdit contexts  
An instance of a base form placed or instantiated in a cell/worldspace. References may have position, ownership, enable state, persistence, linked-reference data, and other instance-specific information.  
**Tags:** references, worldspace, records  
**Sources:** CK-CELL

### Persistent reference
A reference marked or treated so it must remain addressable beyond ordinary cell unloading rules. Persistence is important for quests, aliases, linked logic, and scripted references.  
**Tags:** references, persistence  
**Sources:** CK-CELL

### Override
A later plugin's version of a record that already exists in an earlier master/plugin. Overrides are a normal part of Bethesda modding and are not automatically bad.  
**Tags:** conflict, records, xedit  
**Sources:** XEDIT-METHOD, XEDIT-CONFLICTS

### Conflict
A situation where multiple loaded plugins provide differing versions of the same record and those differences compete for the final effective values. Some conflicts are intentional and desirable; others require patching.  
**Tags:** conflict, xedit  
**Sources:** XEDIT-METHOD, XEDIT-CONFLICTS

### Conflict winner
The last loaded effective version of a record after all relevant overrides are considered. Its values are the ones that generally reach the game unless the record or field has special runtime merge behavior.  
**Tags:** conflict, load-order  
**Sources:** XEDIT-METHOD

### Conflict loser
An earlier version of an overridden record whose competing values are superseded by a later effective override.  
**Tags:** conflict, load-order  
**Sources:** XEDIT-METHOD

### Patch plugin
A plugin created to reconcile, forward, combine, or intentionally replace values from other plugins so the desired combination wins in the final load order.  
**Tags:** patching, compatibility  
**Sources:** XEDIT-CONFLICTS

### Merged patch
An automatically or semi-automatically generated patch concept that collects selected conflict-resolution data from multiple plugins. It is distinct from manually reasoned conflict resolution and should not be assumed to solve every incompatibility.  
**Tags:** patching, xedit  
**Sources:** XEDIT-CONFLICTS

### ITM
**Expansion:** Identical To Master  
An override record whose effective data is identical to the corresponding master version and is therefore often unnecessary. Some ITMs can be intentional, so context matters.  
**Tags:** cleaning, xedit  
**Sources:** XEDIT-WHATSNEW

### UDR
**Expansion:** Undelete and Disable Reference / undeleted-deleted reference cleanup terminology  
A cleaning concept associated with replacing problematic deleted references with a safer disabled form, used by xEdit cleaning workflows.  
**Tags:** cleaning, xedit, references  
**Sources:** XEDIT-WHATSNEW

### Quick Auto Clean / QAC
An xEdit cleaning mode that automates the filtering, ITM-removal, and undelete-and-disable workflow for a selected module. Cleaning safety can be plugin-specific; do not infer that every plugin should be cleaned merely because the tool can do it.  
**Tags:** cleaning, xedit  
**Sources:** XEDIT-WHATSNEW

### ModGroup
An xEdit mechanism for grouping expected related conflicts so known intentional relationships can be treated differently during conflict analysis.  
**Tags:** xedit, conflict-analysis  
**Sources:** XEDIT-METHOD

### Unresolved FormID
A reference from one record to a form that cannot be resolved in the current loaded plugin/master set. This can indicate a missing master, bad reference, removed record, or malformed data.  
**Tags:** error, formid, dependency  
**Sources:** DYNDOLOD-TERMS

## Load order, file order, and packaging

### Load order
The order in which plugins/modules are loaded and therefore the order in which competing plugin record overrides are resolved. This is conceptually separate from loose/archive asset overwrite priority.  
**Tags:** load-order, plugin  
**Sources:** XEDIT-ESL, XEDIT-METHOD

### Asset overwrite order
**Aliases:** mod priority, file priority, asset conflict order  
The ordering that determines which physical/virtual file wins when multiple mods provide the same path, such as a mesh, texture, script, animation, or configuration file. It is separate from plugin-record load order.  
**Tags:** assets, mod-manager, overwrite  
**Sources:** MO2-USVFS, DYNDOLOD-TERMS

### Data directory
The game's data root used by Bethesda's tools and runtime for plugins and assets. Mods may place or virtually expose plugin files, scripts, meshes, textures, sounds, animations, and archives beneath this structure.  
**Tags:** files, game-data  
**Sources:** CK-FILE

### Loose file
An asset present directly in the game's effective data directory structure rather than packed inside a Bethesda archive. Mod managers can virtualize these paths instead of physically copying them into the real Data folder.  
**Tags:** assets, files  
**Sources:** CK-FILE, MO2-USVFS

### BSA
**Expansion:** Bethesda Softworks Archive  
A Bethesda archive format used to package mod assets such as meshes, textures, scripts, and sounds. The Creation Kit includes archive-related tooling, though historical CK packaging can miss required files.  
**Tags:** archive, packaging, assets  
**Sources:** CK-FILE

### Virtual File System / VFS
A virtualization layer that presents files to selected processes as if they existed in the game directory. Mod Organizer 2's USVFS overlays multiple source directories and can hide or replace paths without requiring all files to be physically installed into Data.  
**Tags:** mod-manager, files, virtualization  
**Sources:** MO2-USVFS

### Overwrite directory
In Mod Organizer terminology, a special location used to collect files generated by tools or processes that are not assigned to a normal mod directory. Exact write behavior can vary by tool and VFS interaction, so it should be diagnosed from actual output paths.  
**Tags:** mod-organizer, files, generated-output  
**Sources:** MO2-RELEASES, MO2-USVFS

## Creation Kit and editing tools

### Creation Kit / CK
Bethesda's editor for creating and editing Skyrim game data, including plugins, worldspaces, cells, quests, dialogue, actors, objects, scripts, navmesh, and related data.  
**Tags:** tool, authoring  
**Sources:** CK-FILE, CK-CELL

### xEdit
**Skyrim executable naming:** TES5Edit for classic Skyrim; SSEEdit for Skyrim Special Edition  
A record-level Bethesda plugin editor and analysis tool used for inspection, conflict detection, patching, cleaning, and scripted processing.  
**Tags:** tool, records, compatibility  
**Sources:** XEDIT-DOCS

### SSEEdit
The Skyrim Special Edition mode/name of xEdit. In common usage, “xEdit” refers to the shared tool family and “SSEEdit” to its Skyrim SE/AE execution mode.  
**Tags:** xedit, tool  
**Sources:** XEDIT-DOCS

### Very Quick Show Conflicts
An xEdit startup mode that loads the configured plugin set and applies a conflict-focused view for faster conflict analysis.  
**Tags:** xedit, conflict-analysis  
**Sources:** XEDIT-WHATSNEW

## Papyrus scripting

### Papyrus
Skyrim's scripting language/runtime used by quests, objects, aliases, magic effects, and other game systems. Papyrus scripts compile from source into runtime script files.  
**Tags:** scripting, runtime  
**Sources:** CK-PAPYRUS, CK-COMPILER

### PSC
**Expansion:** Papyrus source file  
The editable source form of a Papyrus script. Source is compiled before the game executes the script.  
**Tags:** papyrus, files  
**Sources:** CK-COMPILER

### PEX
**Expansion:** compiled Papyrus executable/script  
The compiled runtime form of a Papyrus script placed in the scripts data path and executed by the Papyrus VM.  
**Tags:** papyrus, files  
**Sources:** CK-FILE, CK-COMPILER

### ScriptName
The declaration that names a Papyrus script and can specify the script type it extends.  
**Tags:** papyrus, language  
**Sources:** CK-PAPYRUS

### Event
A Papyrus entry point invoked in response to engine/runtime events, such as initialization, updates, activation, triggers, or save-load-related events.  
**Tags:** papyrus, language  
**Sources:** CK-PAPYRUS

### Function
A named Papyrus routine that can receive parameters, execute logic, and optionally return a value.  
**Tags:** papyrus, language  
**Sources:** CK-PAPYRUS

### Property
A Papyrus field intended to expose or store values, often bound in the Creation Kit or initialized automatically. Properties commonly connect scripts to forms, aliases, quests, globals, and other runtime objects.  
**Tags:** papyrus, language, creation-kit  
**Sources:** CK-PAPYRUS

### Auto property
A Papyrus property using automatic backing storage rather than explicitly written get/set functions.  
**Tags:** papyrus, language  
**Sources:** CK-PAPYRUS

### Script fragment
Papyrus code generated/attached for specific editor-driven fragments such as quest stages, dialogue, packages, or other CK-defined fragment contexts. Fragment naming and generated files are managed partly by the Creation Kit.  
**Tags:** papyrus, creation-kit  
**Sources:** CK-FILE

### Papyrus VM
**Aliases:** virtual machine, VM  
The runtime system responsible for executing Papyrus scripts. Native/SKSE plugin code can interact with the VM through engine interfaces.  
**Tags:** papyrus, runtime, skse  
**Sources:** CK-SKSE-PAPYRUS

### Papyrus log
A diagnostic log that can contain Papyrus warnings, errors, traces, and other script-engine activity when logging is enabled. It is useful for script diagnosis but is not a generic “crash log.”  
**Tags:** papyrus, diagnostics  
**Sources:** CK-PAPYRUS-LOG

## Quests, aliases, cells, and world data

### Quest
A game record/system that can manage stages, objectives, aliases, scripts, dialogue, scenes, and stateful logic. Quests are frequently used as general-purpose managers even when no visible player quest is involved.  
**Tags:** quest, scripting, records  
**Sources:** CK-PAPYRUS

### Quest stage
A numbered progression/state marker associated with a quest. Stage changes can drive objectives, fragments, conditions, dialogue, and scripts.  
**Tags:** quest, progression  
**Sources:** CK-PAPYRUS

### Alias
A quest-owned slot that can point to or select a reference/location and expose it to dialogue, scripting, packages, and quest logic.  
**Tags:** quest, alias  
**Sources:** CK-PAPYRUS

### Reference Alias
A quest alias that resolves to an ObjectReference/Actor-like reference and can host alias-specific Papyrus behavior.  
**Tags:** quest, alias, papyrus  
**Sources:** CK-PAPYRUS

### Condition
An engine-evaluated predicate attached to records/features such as dialogue, packages, magic effects, perks, or other systems. Conditions often determine whether a game behavior is eligible to run.  
**Tags:** conditions, game-logic  
**Sources:** CK-PAPYRUS

### Cell
A spatial unit of world data. Interior spaces are cells; exterior worldspaces are divided into coordinate-based exterior cells.  
**Tags:** worldspace, level-design  
**Sources:** CK-CELL

### Worldspace
A top-level exterior world environment divided into cells and associated with terrain, water, climate, map, and other world-level data.  
**Tags:** worldspace, level-design, lod  
**Sources:** DYNDOLOD-REFERENCE

### Navmesh
Navigation geometry used by actors for pathfinding. Navmesh data must be generated/finalized correctly and can create difficult compatibility problems when multiple mods edit the same spaces.  
**Tags:** navmesh, ai, compatibility  
**Sources:** CK-FILE

## SKSE and native plugins

### SKSE
**Expansion:** Skyrim Script Extender  
A runtime extension layer that expands Skyrim's scripting/native capabilities and provides infrastructure used by many advanced mods. SKSE builds are tied to specific game-runtime families/versions.  
**Tags:** skse, runtime, framework  
**Sources:** SKSE-OFFICIAL

### SKSE plugin
**Aliases:** native plugin, SKSE DLL  
A native-code plugin loaded through SKSE, commonly distributed as a DLL under the SKSE plugin path. Native plugins can hook or call game-engine functionality beyond ordinary Papyrus capabilities.  
**Tags:** skse, native, dll  
**Sources:** SKSE-OFFICIAL, CK-SKSE-RESOURCES

### Runtime version
The executable/game build a native plugin or SKSE build targets. Skyrim SE/AE/GOG/VR compatibility can differ by runtime, so “SE vs AE” alone may be insufficient when diagnosing native plugin compatibility.  
**Tags:** runtime, compatibility  
**Sources:** SKSE-OFFICIAL

### Address Library
A dependency used by many Skyrim SE/AE native plugins to resolve game executable addresses across supported runtime builds, reducing the need to hard-code raw addresses separately for each version.  
**Tags:** skse, native, compatibility  
**Sources:** OAR-UPSTREAM

### CommonLibSSE / CommonLibSSE-NG
A C++ reverse-engineering/helper library ecosystem used to develop Skyrim native plugins with typed game structures and SKSE integration. The NG variant is commonly used for multi-runtime SE/AE/VR-capable projects.  
**Tags:** skse, c++, native  
**Sources:** CK-SKSE-RESOURCES, OAR-UPSTREAM

## Assets and runtime files

### Mesh
A 3D asset defining geometry and related rendering/collision data used for objects, characters, architecture, landscape pieces, equipment, and other visual elements.  
**Tags:** assets, 3d  
**Sources:** DYNDOLOD-TREE, CK-RETEXTURE

### NIF
**Expansion:** NetImmerse/Gamebryo model file in Skyrim modding usage  
A principal Skyrim 3D model format containing geometry and associated model/rendering data. NIFs are commonly inspected and edited with NifSkope and related tools.  
**Tags:** mesh, nif, assets  
**Sources:** DYNDOLOD-TREE, CK-RETEXTURE

### Texture
An image asset used by meshes/materials for surface appearance and related rendering channels.  
**Tags:** assets, rendering  
**Sources:** CK-RETEXTURE

### DDS
**Expansion:** DirectDraw Surface  
The texture file format commonly used by Skyrim assets. DDS files may contain color, normal, mask, and other texture data depending on the asset/shader.  
**Tags:** texture, assets  
**Sources:** CK-RETEXTURE

### Normal map
A texture used by shaders to alter perceived surface normals and produce fine lighting detail without adding equivalent mesh geometry.  
**Tags:** texture, rendering  
**Sources:** DYNDOLOD-TREE

### Collision
Geometry/data used by the physics engine to determine physical interaction boundaries. Collision can be separate from visible geometry and often uses Havok-related structures inside NIF assets.  
**Tags:** physics, nif, assets  
**Sources:** CK-NIF-COLLISION

### HKX
A Havok-format file used in Skyrim modding for animation/behavior-related data. Animation replacement frameworks commonly operate on or redirect HKX animation assets.  
**Tags:** animation, havok, assets  
**Sources:** OAR-UPSTREAM

### FaceGen
Generated head mesh/tint assets associated with actor/NPC appearance. CK packaging documentation specifically identifies FaceGen mesh and tint paths as assets that historically required care when packaging.  
**Tags:** npc, assets, facegen  
**Sources:** CK-FILE

## LOD terminology

### LOD
**Expansion:** Level of Detail  
Distant representations used beyond the fully active nearby area. In Skyrim technical usage, terrain LOD, object LOD, and tree LOD are distinct systems.  
**Tags:** lod, worldspace  
**Sources:** DYNDOLOD-REFERENCE, DYNDOLOD-TERMS

### Object LOD
Combined distant meshes/textures representing non-animated world objects such as buildings, rocks, and landscape structures.  
**Tags:** lod, objects  
**Sources:** DYNDOLOD-OBJECT

### Tree LOD
Skyrim's dedicated distant-tree system using billboard textures and tree LOD data rather than ordinary full NIF meshes.  
**Tags:** lod, trees  
**Sources:** DYNDOLOD-TREE

### Terrain LOD
Distant terrain/ground representation for worldspaces, including terrain meshes/textures and water-LOD-related data.  
**Tags:** lod, terrain  
**Sources:** DYNDOLOD-TERRAIN

### Billboard
A simplified distant visual representation, often texture-based. Tree LOD traditionally uses billboards rather than full nearby tree geometry.  
**Tags:** lod, trees, assets  
**Sources:** DYNDOLOD-TREE

### xLODGen
A specialized xEdit-derived LOD generation mode/tool used for generating Bethesda-style LOD, especially terrain and object LOD workflows.  
**Tags:** lod, tool  
**Sources:** DYNDOLOD-REFERENCE

### DynDOLOD
A specialized Skyrim LOD generation toolset built around xEdit/xLODGen-derived technology and LODGen to create/update distant object/tree-related LOD and supporting data.  
**Tags:** lod, tool  
**Sources:** DYNDOLOD-REFERENCE

### TexGen
A DynDOLOD companion tool that generates/updates selected LOD textures and tree/grass billboard assets used by later LOD generation.  
**Tags:** lod, tool, textures  
**Sources:** DYNDOLOD-HELP

### Active exterior cells
The nearby exterior cells loaded as full game-world content around the player; distant LOD is used beyond this active area.  
**Tags:** worldspace, lod, cells  
**Sources:** DYNDOLOD-TERMS

## Animation replacement terminology

### Open Animation Replacer / OAR
An SKSE framework that replaces animations according to configurable conditions and supports in-game configuration/editor functionality.  
**Tags:** animation, skse, framework  
**Sources:** OAR-UPSTREAM

### Animation replacer
A system or mod that substitutes one animation asset/behavior for another, either globally or conditionally. Modern frameworks such as OAR can make the substitution conditional rather than requiring one unconditional file overwrite.  
**Tags:** animation, compatibility  
**Sources:** OAR-UPSTREAM

## Diagnostic distinctions

### Papyrus error vs crash
Papyrus logging describes script-engine activity and is not equivalent to a native crash dump or SKSE crash logger. A Papyrus warning near the time of a crash does not by itself prove that the script caused the crash.  
**Tags:** diagnostics, papyrus, crash-analysis  
**Sources:** CK-PAPYRUS-LOG

### Plugin conflict vs asset conflict
A plugin conflict is competing record data in load order; an asset conflict is competing files at the same virtual/physical path. They can interact but must be diagnosed separately.  
**Tags:** diagnostics, conflict, assets  
**Sources:** XEDIT-CONFLICTS, MO2-USVFS

### Missing master
A dependency failure where a plugin requires a parent master that is not available/loaded as expected. This can prevent the plugin or game from loading correctly and can produce unresolved references.  
**Tags:** dependency, plugin, error  
**Sources:** CK-FILE, DYNDOLOD-TERMS

---

# Source keys

- **CK-FILE** — Creation Kit Wiki archive/mirror, “File Menu”: https://ck.uesp.net/wiki/File_menu
- **CK-CELL** — Creation Kit Wiki archive/mirror, “Cell View Window”: https://ck.uesp.net/wiki/Cell_View_Window
- **CK-RETEXTURE** — Creation Kit Wiki archive/mirror, “Retexture Tutorial”: https://ck.uesp.net/wiki/Retexture_Tutorial
- **CK-PAPYRUS** — Creation Kit Wiki Papyrus examples/reference pages, including operator/script examples: https://ck.uesp.net/wiki/Operator_Reference
- **CK-COMPILER** — Creation Kit Wiki, Papyrus compiler setup/reference context: https://ck.uesp.net/wiki/Notepad%2B%2B_Setup
- **CK-PAPYRUS-LOG** — Creation Kit Wiki, Papyrus logging: https://ck.uesp.net/wiki/User%3ADavidJCobb/Papyrus_logging
- **CK-SKSE-RESOURCES** — Creation Kit Wiki, SKSE Plugin Development/Resources: https://ck.uesp.net/wiki/SKSE_Plugin_Development/Resources
- **CK-SKSE-PAPYRUS** — Creation Kit Wiki, SKSE Plugin Development/Calling Papyrus Functions: https://ck.uesp.net/wiki/SKSE_Plugin_Development/Calling_Papyrus_Functions
- **CK-NIF-COLLISION** — Creation Kit Wiki user technical notes on NIF/collision workflows: https://ck.uesp.net/wiki/User:DavidJCobb
- **XEDIT-DOCS** — Tome of xEdit documentation: https://tes5edit.github.io/docs/
- **XEDIT-METHOD** — Tome of xEdit, The Method: https://tes5edit.github.io/docs/6-themethod.html
- **XEDIT-CONFLICTS** — Tome of xEdit, Conflict Detection and Resolution: https://tes5edit.github.io/docs/5-conflict-detection-and-resolution.html
- **XEDIT-WHATSNEW** — xEdit documentation, ESL/cleaning and related behavior: https://tes5edit.github.io/whatsnew.html
- **XEDIT-ESL** — Tome of xEdit appendix, ESL vs ESM: https://tes5edit.github.io/docs/11-appendix.html
- **SKSE-OFFICIAL** — Official SKSE site: https://skse.silverlock.org/
- **MO2-USVFS** — Mod Organizer 2 USVFS upstream README: https://github.com/ModOrganizer2/usvfs/blob/master/README.md
- **MO2-RELEASES** — Mod Organizer 2 upstream releases: https://github.com/ModOrganizer2/modorganizer/releases
- **DYNDOLOD-REFERENCE** — DynDOLOD Reference: https://dyndolod.info/DynDOLOD-Reference
- **DYNDOLOD-TERMS** — DynDOLOD Terminology: https://dyndolod.info/Terminology
- **DYNDOLOD-TREE** — DynDOLOD Tree LOD: https://dyndolod.info/Help/Tree-LOD
- **DYNDOLOD-OBJECT** — DynDOLOD Object LOD: https://dyndolod.info/Help/Object-LOD
- **DYNDOLOD-TERRAIN** — DynDOLOD Terrain LOD and Water LOD: https://dyndolod.info/Help/Terrain-LOD-and-Water-LOD
- **DYNDOLOD-HELP** — DynDOLOD Help index: https://dyndolod.info/Help
- **OAR-UPSTREAM** — Open Animation Replacer upstream README: https://github.com/ersh1/OpenAnimationReplacer/blob/main/README.md

## Follow-up ingestion targets

This first pass deliberately prioritizes foundational vocabulary. Subsequent terminology passes should cover:

- Creation Kit record families and editor windows;
- quest/dialogue/scene/package terminology;
- navmesh and worldspace editing;
- leveled lists, keywords, FormLists, perks, spells, magic effects, conditions;
- VMAD, script attachment, fragments, latent functions, stacks, serialization;
- save-game persistence and script-instance behavior;
- SKSE messaging, trampolines, hooks, relocation, serialization, Address Library IDs;
- CommonLibSSE-NG classes and runtime abstraction;
- NIF shader/property terminology, materials, skinning, collision, morphs;
- animation graphs, behavior graphs, animation events, OAR/DAR/Nemesis/Pandora terminology;
- SPID, KID, BOS, FLM and other distributor/framework configuration terms;
- BodySlide/Outfit Studio, skeletons, weights, morphs, TRI files;
- FaceGen, tint masks, head parts, races;
- audio/voice/FUZ/LIP/XWM;
- UI/SWF/Scaleform/SkyUI/MCM;
- ENB/Community Shaders terminology;
- crash log and memory terminology;
- LOOT metadata, rules, groups, cyclic interactions;
- mod-manager concepts and deployment models;
- Wabbajack/list-building terminology;
- versioning, ESL compaction, renumbering FormIDs, persistence hazards;
- deleted navmeshes, ONAM, injected records, partial forms;
- LOD, occlusion, large references, grass cache/grass LOD;
- patching patterns and compatibility taxonomy.
