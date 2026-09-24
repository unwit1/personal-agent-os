# Official Skyrim Master Data Ingestion Plan

Updated: 2026-09-24
Status: implementation-ready local ingestion path

## Goal

Use the user's legally installed Skyrim master files as the most direct evidence for actual shipped forms/settings, while keeping raw copyrighted master data local and promoting only compact technical facts into the canonical knowledge repository.

## Inputs

Typical sources:
- Skyrim.esm
- Update.esm
- Dawnguard.esm
- HearthFires.esm
- Dragonborn.esm
- current baseline Creations/Resource Pack files when installed
- optional Creation/mod masters when one project needs source-specific knowledge

## Acquisition

Use `tools/knowledge/capture_skyrim_master_records.py` with an xEdit/xDump executable pinned to a known xEdit source/release.

The wrapper initially targets high-value record families:

- GMST — Game Settings;
- DOBJ — Default Object Manager;
- AVIF — ActorValue information;
- MGEF/SPEL/PERK — magic/perk semantics;
- RACE/CSTY/CLAS — actors/AI;
- WTHR/CLMT/LGTM/IMGS — environment;
- ECZN/LCTN — encounter/location semantics;
- MUSC/SNDR/SOPM — audio.

Additional signatures can be requested explicitly.

## Storage policy

### Keep local/high-volume
- complete xDump decoded output;
- raw master copies;
- full form-by-form text;
- repeated source snapshots.

### Promote to Git
- normalized enums/tables;
- stable engine defaults;
- schema explanations;
- changed-value/version diffs;
- validated compatibility implications;
- source hashes and provenance;
- small selected factual catalogs.

This prevents Git from becoming a mirror of Bethesda game data while still making the agent knowledgeable about the engine.

## Normalization targets

### GMST catalog
For each setting:
- EditorID/name;
- type;
- shipped value by master/runtime snapshot;
- subsystem;
- known consumers;
- risk class;
- whether later masters override it.

### DOBJ snapshot
For each key:
- assigned FormID/FormKey;
- EditorID/name/type;
- master introducing/changing assignment.

### AVIF
For each ActorValue:
- enum ID;
- AVIF form;
- display/skill data;
- progression metadata.

### Magic/perks
Map:
- shipped MagicEffects -> archetype/flags;
- vanilla perks -> Entry Points/conditions;
- representative formula interactions.

### World/environment
Record:
- climate/weather relationships;
- baseline ImageSpaces/lighting templates;
- special worldspace water/default relationships.

## Diffing

For each captured master-set snapshot:
1. hash every master;
2. retain xEdit/xDump version;
3. normalize selected records;
4. diff against prior snapshot;
5. classify ADDED/REMOVED/CHANGED;
6. identify changed fields;
7. assess whether change affects mod compatibility;
8. update version-scoped canonical facts.

## Copyright boundary

Do not commit:
- full dialogue/book text;
- raw meshes/textures/audio;
- wholesale decoded master dumps.

Technical identifiers, small factual tables, schema/field relationships and derived compatibility findings should remain concise and provenance-backed.

## Long-term automation

Agent OS should detect a changed Skyrim executable/master hash and offer/run:
- current-version matrix refresh;
- xDump schema/master capture;
- record diff;
- native-runtime compatibility scan;
- downstream generator invalidation assessment.
