# Skyrim Modding Terminology — Records, Patching, and Load-Order Semantics

Imported: 2026-09-24
Status: sourced deep-ingestion pass 2

This file expands the foundation glossary with record-level and compatibility terminology used by Creation Kit, xEdit, LOOT, and patching workflows.

## Record structure and common form types

### Form
A generic engine object/record that can be referenced by other records or scripts. Weapons, armor, quests, cells, keywords, spells, globals, FormLists, actors, and many other objects are forms.

### Form type
The engine-defined category of a form. Tools expose these using names and/or record signatures. Correct form type matters because fields, scripting APIs, keyword support, and runtime behavior differ by type.

### Record signature
The short record-type identifier used in plugin data and tools. Examples encountered in Skyrim tooling include QUST for quests and many other four-character signatures. Treat the signature as the structural type, not merely a label.

### GRUP
A plugin-format grouping structure used to organize records. xEdit presents record trees through groups and nested structures so records can be inspected in context.

### Master record
The earliest loaded defining version of a record relative to the override chain being examined. Later plugins can override that same record.

### Override chain
All loaded versions of a record from its originating/master definition through later overrides. xEdit compares this chain to determine conflict status and the final effective record.

### Winning override
The last effective version of a record in plugin load order. This is usually the version whose field values reach the game, subject to special runtime behaviors such as lists or systems that merge/add data dynamically.

### Forwarding
A patching technique in which a later plugin deliberately copies desired field values from an earlier plugin so they survive another plugin's competing override.

### Conflict resolution patch
A plugin whose purpose is to create the desired final combination of record values after comparing all relevant overrides. A good patch is based on intent and field semantics, not on mechanically copying everything from the last plugin.

### Intentional conflict
A record conflict that exists because a mod deliberately changes a value from another plugin. xEdit conflict coloring alone cannot decide whether the conflict is harmful.

### Benign conflict
A conflict where multiple records differ but the final result is acceptable and no compatibility action is needed.

### Destructive conflict
A conflict where a later override unintentionally removes or replaces data required by another mod, producing lost features, broken references, incorrect stats, missing dialogue, or other unwanted behavior.

### Leveled list
A list-like game form used to choose entries based on level and other list behavior. Skyrim has leveled-item, leveled-actor, and leveled-spell concepts. Multiple mods can add/remove entries, making these records common patching targets.

### LeveledItem
A Papyrus/game form representing a leveled-item list. Runtime and patch tools can add entries, but plugin-level edits can conflict when multiple mods alter the same list.

### LeveledActor
A leveled list that selects actor/NPC/creature forms according to the list's rules.

### LeveledSpell
A leveled list used for spells.

### FormList
A list of form references stored as a game record. Scripts and game systems can use FormLists as reusable collections. Unlike an arbitrary Papyrus array, a FormList is a form that can be referenced from records/scripts.

### Keyword
A reusable classification/tag form attached to many record types. Keywords are heavily used by conditions, crafting, equipment categorization, magic logic, animation conditions, distribution frameworks, and compatibility systems.

### GlobalVariable
A form storing a numeric global value that can be referenced by conditions, quests, Papyrus, and other systems.

### ConstructibleObject / COBJ
A crafting-recipe form. It generally identifies created output, required components, crafting station/keyword logic, and conditions.

### Container
A base object that defines inventory contents for placed or spawned container references. Container contents are distinct from runtime inventory state on one placed reference.

### Outfit
A form defining a set/list of items that can be assigned as an actor outfit. Runtime distributors such as SPID can assign outfits without editing every NPC record directly.

### Faction
A form used to group actors and represent relationships, ranks, crime/legal systems, dialogue/condition membership, and other actor logic.

### Race
A form defining race-level actor data such as body/head setup, movement/behavior relationships, spells/abilities, skeleton/model relationships, and other race-specific configuration.

### ArmorAddon / ARMA
A supporting form used by armor to define wearable model/body-slot/race-related rendering data. Armor appearance problems often require examining both the ARMO record and linked ArmorAddon data.

### Armor / ARMO
A wearable item/base record containing gameplay data and references to ArmorAddon records. The inventory item and its rendered body models are therefore not a single record.

### Weapon / WEAP
A weapon base record containing stats, models, keywords, sounds, animations/equip data references, and other weapon configuration.

### MagicEffect / MGEF
The functional building block for spells, enchantments, potions, scrolls, shouts, abilities, and related magic systems. The effect archetype supplies engine behavior while conditions/scripts can extend it.

### Spell / SPEL
A form that contains one or more effect items referencing MagicEffects plus casting/delivery/type configuration.

### Perk
A form representing perk logic. Perks can contain conditions and perk entries that alter gameplay through engine-defined entry points or other mechanisms.

### Condition
An engine-evaluated predicate used across dialogue, packages, magic effects, perks, quests, recipes, and many other record types. Conditions are evaluated by the engine rather than requiring equivalent Papyrus code.

### Condition function
A built-in engine function used inside a condition row, such as tests for actor state, faction membership, quest stage, inventory, keywords, locations, or other game state.

### Default Object
A game-wide slot pointing to a form used for a predefined engine purpose. Skyrim exposes many default objects for keywords, sounds, menu behavior, crafting categories, factions, and other systems.

### Injected record
A record whose identity is intentionally created in a way designed to use a stable FormID supplied through another module namespace rather than a normal new-record allocation. Injection is an advanced compatibility technique and should be validated carefully before use.

### Unresolved reference
A field that points to a FormID that cannot be resolved in the currently loaded master/plugin set. Common causes include missing masters, deleted/removed forms, broken patches, or incorrect FormIDs.

### Deleted reference
A placed reference override marked deleted. Deleting references can be unsafe because other game data may still refer to them; xEdit cleaning practices commonly replace unsafe deletions with a safer undelete-and-disable pattern.

### Undelete and Disable
An xEdit cleanup strategy that restores a deleted placed reference and disables/moves or otherwise neutralizes it instead of leaving a hard deletion that may be referenced elsewhere.

### Deleted navmesh
A navmesh record removed by a plugin override. Deleted navmeshes are a well-known high-risk compatibility class because navigation and connected data can reference them. Do not treat them like ordinary disposable references.

### ITM
**Expansion:** Identical To Master.  
An override that makes no effective change relative to its master version. Often accidental, but an ITM can be intentional if a mod author explicitly needs to block another override; context is required before removal.

### Cleaning
Using xEdit's supported cleaning workflow to remove known classes of accidental edits such as unnecessary ITMs and to apply safe undelete/disable handling. Cleaning is not synonymous with “make every conflict disappear.”

### Quick Auto Clean / QAC
An xEdit mode that automates supported cleaning operations for one plugin. Whether a specific plugin should be cleaned remains plugin/version-specific.

## Load-order terminology

### Plugin load order
The ordered sequence in which ESM/ESP/ESL modules are loaded. Record override chains resolve according to this ordering.

### Master block
The load-order region occupied by modules treated as ESM/master files. ESM behavior is a property/state understood by the engine; filename extension is only part of the story.

### Light-plugin space
The FE-prefixed FormID mapping space used by ESL-flagged plugins. A light plugin consumes a light index rather than a normal full plugin index.

### Plugin index
The load-order index used in loaded FormID mapping. Full and light plugins use different mapping schemes.

### ObjectID
The record-local portion of a FormID. Light-plugin compatibility requires newly created records to fit within the applicable light ObjectID range.

### Compacting FormIDs
Renumbering a plugin's newly created records into an ObjectID range suitable for ESL/light-plugin use. This can break references in dependent plugins, scripts, save data, or external configuration if done after IDs have become dependencies.

### Missing master
A required parent plugin is absent or unavailable. The dependent plugin cannot correctly resolve all forms and may fail to load or produce unresolved references.

### Cyclic dependency
A dependency/order requirement that cannot be satisfied because plugins or metadata indirectly require each other to load both before and after. LOOT metadata/rules should avoid creating cycles.

### LOOT
**Expansion:** Load Order Optimisation Tool.  
A tool that sorts supported Bethesda-game plugin load orders using plugin metadata and dependency/order constraints. It helps determine plugin ordering; it does not replace record-level conflict analysis in xEdit.

### LOOT metadata
Rules and information associated with plugins, including ordering relationships, messages, requirements, incompatibilities, dirty-plugin information, and grouping data.

### LOOT group
A metadata mechanism for placing classes of plugins into broader relative ordering regions. Grouping supplements explicit plugin dependencies/rules.

### “Load after” rule
A load-order constraint saying one plugin must come after another. It should reflect a real dependency or intended conflict outcome, not be used as a substitute for a compatibility patch when both mods' changes are needed.

### Dirty plugin
A plugin containing edits that a tool/maintainer identifies as candidates for cleaning, commonly including accidental ITMs or unsafe deleted references. “Dirty” is not a general label for all conflicts.

## Compatibility patterns

### Record patch
A conventional plugin patch that resolves competing plugin-record edits by providing a final override.

### Runtime patching
A mod/framework changes data or behavior after plugins are loaded instead of producing a static conflict-resolution plugin. SPID, KID, FLM, and BOS are examples of frameworks that move some compatibility work into runtime/config-driven processing.

### Conflict avoidance
Designing a mod so it does not edit a heavily contested vanilla/mod record in the first place, often by using runtime distribution, keywords, scripts, aliases, injected data, or framework APIs.

### Soft dependency
Optional integration where one mod can detect/use another mod when present but still functions without it.

### Hard dependency
A requirement without which the dependent mod cannot function correctly. A hard master at plugin level is one concrete form of hard dependency.

### Compatibility patch
Any additional data/config/code specifically intended to make two or more mods interact correctly. A compatibility patch may be a plugin, INI/config file, script, runtime distribution file, asset patch, or code change.

### Bashed/merged-style list synthesis
A class of automated patching that attempts to synthesize selected list-like data across plugins. Automated synthesis is useful for specific record families but should not be assumed to understand every mod author's semantic intent.

## Diagnostic rules encoded for Agent OS

1. **Do not equate an xEdit conflict with a bug.** Determine author intent and the desired final fields.
2. **Do not solve missing data with load order alone when both mods' fields are needed.** Use a patch or a compatible runtime-distribution approach.
3. **Separate plugin-record conflicts from asset-path conflicts.**
4. **Treat FormID compaction as an identity migration, not a harmless checkbox.**
5. **Treat deleted navmeshes and hard-deleted references as higher-risk than ordinary overrides.**
6. **Treat LOOT as an ordering/metadata system, not as a semantic conflict resolver.**
7. **Prefer runtime distribution/framework integration when it eliminates unnecessary shared-record edits without introducing opaque state.**

## Sources

- Tome of xEdit — Conflict Detection and Resolution: https://tes5edit.github.io/docs/5-conflict-detection-and-resolution.html
- Tome of xEdit — The Method: https://tes5edit.github.io/docs/6-themethod.html
- xEdit What's New / cleaning and ESL behavior: https://tes5edit.github.io/whatsnew.html
- Tome of xEdit appendix / ESL vs ESM: https://tes5edit.github.io/docs/11-appendix.html
- LOOT — Introduction to Load Orders: https://loot.github.io/docs/help/introduction-to-load-orders/
- Creation Kit Wiki — Magic Effect: https://ck.uesp.net/wiki/Magic_Effect
- Creation Kit Wiki — DefaultObjectManager Script: https://ck.uesp.net/wiki/DefaultObjectManager_Script
- Creation Kit Wiki — FormList examples and scripting reference material: https://ck.uesp.net/wiki/Category:Scripting
- Creation Kit Wiki — crafting categories / keywords / constructible objects: https://ck.uesp.net/wiki/Customizing_Crafting_Categories

## Provenance notes

- xEdit/LOOT are the preferred sources for load-order and override terminology.
- Creation Kit Wiki material is used primarily for game-record concepts. Many pages are historical and should be version-qualified when implementation details matter.
- Advanced terms such as injected records and deleted-navmesh handling should be revisited with additional source-code/tool evidence before automated remediation is allowed.
