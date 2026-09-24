# Skyrim Plugin Record Schema — Actors and AI

Imported: 2026-09-24
Status: field-level schema deepening

## NPC_ — ActorBase

Key fields:
- EDID: EditorID.
- FULL: display name.
- ACBS: flags, level/min/max, speed multiplier, disposition/template-related base data.
- SNAM: factions and ranks.
- SPLO: spells/abilities.
- PRKR: perks and ranks.
- ITEMS/CNTO: base inventory.
- AIDT: AI aggression/confidence/assistance/morality and related data.
- PKID: AI packages.
- CNAM: Class.
- DNAM: player-skill/stat/template-related actor data.
- RNAM: Race.
- COCT/CNAM-like container count/data structures depending schema generation.
- DOFT/SOFT: default/sleep outfits.
- DPLT: default package list where used.
- HCLF: hair color.
- ZNAM: combat style.
- NAM5/NAM6/NAM7 etc.: appearance/height/weight and face-related data according to xEdit schema.
- Head Parts: PNAM references to HDPT.
- Face morph/tint structures.
- VMAD: attached Papyrus scripts.

Patch semantics:
- Appearance fields must remain coherent with FaceGen.
- Race/weight can affect both gameplay and visual output.
- Factions/perks/packages/inventory are usually gameplay-forwarding candidates.
- ACBS flags such as Essential/Protected/Unique must be intentionally reconciled.
- Do not replace whole NPC_ merely to preserve one appearance field.

## ACHR — Placed Actor Reference

Key concerns:
- NAME: base NPC_.
- DATA: position/rotation.
- XESP: enable parent.
- ownership/lock/linked-ref ExtraData.
- persistent/initially-disabled/reference flags.
- location ref types.
- encounter-zone/reference data.
- VMAD/reference script.

Patch semantics:
- Base NPC_ conflict and ACHR placement conflict are separate.
- Moving a persistent ACHR can create save-side transform ChangeForms.
- Quest aliases can make an actor persistent regardless of intuitive placement expectations.

## RACE

Key concerns:
- playable/child/behavior flags;
- male/female skeleton/model paths;
- body/head data;
- default spells;
- keywords;
- skill/stat modifiers;
- movement types;
- equip-slot/body relationships;
- behavior graph/animation data.

Patch semantics:
- Race overhaul conflicts can affect every NPC using the race.
- Skeleton/model/behavior edits are high-impact.
- Custom-race vampire/werewolf mappings require separate compatibility.

## CLAS — Class

Fields influence:
- favored skills;
- skill weights;
- attribute/health-magicka-stamina progression inputs;
- service/training-related behavior in some contexts.

Patch semantics:
- Class change can alter leveled/scaled NPC stats even when NPC_ record itself is unchanged.

## CSTY — Combat Style

Fields commonly govern:
- offensive/defensive weights;
- melee/ranged/magic preferences;
- bash/block/power-attack behavior;
- movement/spacing;
- stamina thresholds.

Patch semantics:
- Combat overhauls often compete here.
- Last whole-record winner is rarely correct if two mods intentionally tune different subgroups.

## FACT — Faction

Fields:
- name;
- ranks and rank names;
- reactions to other factions;
- crime data;
- vendor/service flags;
- ownership/crime relationships;
- conditions where supported.

Patch semantics:
- Faction conflict can alter crime, dialogue, hostility and merchant behavior simultaneously.

## RELA — Relationship

Fields:
- parent actor;
- child actor;
- relationship rank;
- AssociationType.

Patch semantics:
- RELA is distinct from runtime SetRelationshipRank changes baked into save.

## OTFT — Outfit

Fields:
- ordered/listed item forms.

Patch semantics:
- NPC outfit mods can conflict independently of NPC inventory.
- Runtime outfit managers may override static outfit choices.

## PACK — Package

Fields:
- package template/procedure tree;
- schedule;
- package conditions;
- target/location/data inputs;
- flags;
- package fragments/VMAD.

Patch semantics:
- Preserve both procedure and bound data.
- Alias package overrides can supersede base NPC packages at runtime.

## IDLE

Fields:
- animation event/file relationships;
- conditions;
- parent/child idle links;
- animation groups.

Patch semantics:
- OAR can replace clips without editing IDLE.
- AnimObject references/behavior events can still require static/runtime compatibility.

## LVLN — Leveled Actor

Fields:
- entries (level + ActorBase/LVLN);
- chance none;
- flags;
- global/chance controls.

Patch semantics:
- merge additions/removals according to overhaul intent.
- EncounterZone context changes which entry is selected but is not stored inside LVLN itself.

## High-risk actor patch checklist

When patching one NPC:
1. compare origin + every override;
2. identify appearance source;
3. identify gameplay source;
4. preserve race/weight coherence;
5. preserve desired factions/perks/packages/outfits;
6. verify FaceGen;
7. inspect runtime distributors;
8. test on new game and affected established save when runtime state matters.

## Sources

- xEdit/TES5Edit schemas and scripts
- Creation Kit actor/package documentation
- Bethesda plugin-format references
