# Skyrim ChangeForm Flag Catalog — CommonLibSSE-NG

Imported: 2026-09-24
Status: reverse-engineered source-derived save-overlay catalog

## Purpose

A Skyrim save does not simply reload current plugin records. It stores **ChangeForms** whose bit flags declare which categories of one form/reference have diverged from plugin defaults.

The same bit position can mean different things for different FormTypes. Always decode a ChangeFlag in the context of its parent form type.

## Sources

- `TESForm.h` blob `6ea87f98951bed95c2fe9e8d9a79591fcd5562d0`
- `TESObjectREFR.h` blob `584212939055d1a100e85d54dea433dcc28c1b03`
- `Actor.h` blob `83dae032ca85bd3bfe1cd53ac00e4e98c1de8e65`
- `TESNPC.h` blob `7b8d1830a3e3450be8a3c123bdbbecc8b210e3a8`
- `TESObjectCELL.h` blob `fa8a60c3986f907480c975155fc2cf1d6652b397`
- `BGSListForm.h` blob `6dd9165d92b568683577763e8da4e21adfe53bfc`
- `TESQuest.h` blob `00297a304022c9d4b4b1a6666f026b7715e97d5c`
- `TESFaction.h` blob `619fad4d15b1fbc2bff6ae49416787d65b2b54dd`
- `BGSRelationship.h` blob `c75028ab4dafc2f08147b85fc79f1ed40f631959`

Upstream: https://github.com/alandtse/CommonLibSSE-NG

## Base TESForm

| Bit | Change category |
|---|---|
| 0 | Flags |

`Created = 0` is represented as the created-form state rather than an ordinary bit flag.

## TESObjectREFR / placed reference

| Bit | Change category |
|---:|---|
| 1 | Moved |
| 2 | Havok Moved |
| 3 | Cell Changed |
| 4 | Scale |
| 5 | Inventory |
| 6 | Ownership Extra |
| 7 | Base Object |
| 10 | Item ExtraData |
| 11 | Ammo Extra |
| 12 | Lock Extra |
| 17 | Teleport Extra |
| 21 | Empty |
| 22 | Open Default State |
| 23 | Open State |
| 25 | Promoted |
| 26 | Activating Children |
| 27 | Leveled Inventory |
| 28 | Animation |
| 29 | Encounter Zone Extra |
| 30 | Created-Only Extra |
| 31 | Game-Only Extra |

### Why REFR is high risk

A placed reference can therefore preserve:
- position/rotation movement;
- Havok movement;
- a new parent cell;
- scale;
- inventory and instance ExtraData;
- ownership;
- a changed base object;
- lock/teleport state;
- open/closed state;
- animation/runtime data.

This explains why changing a plugin REFR can appear to have no effect on an established save.

## Actor / ACHR runtime state

| Bit | Change category |
|---:|---|
| 10 | Life State |
| 11 | Package ExtraData |
| 12 | Merchant Container |
| 17 | Dismembered Limbs |
| 18 | Leveled Actor |
| 19 | Display Modifiers |
| 20 | Temporary Modifiers |
| 21 | Damage Modifiers |
| 22 | Override Modifiers |
| 23 | Permanent Modifiers |

The modifier flags map directly onto runtime ActorValue state layers. A base NPC or spell/perk patch does not automatically erase these saved actor modifiers.

## NPC_ / ActorBase mutable state

| Bit | Change category |
|---:|---|
| 1 | Base Data |
| 2 | Attributes |
| 3 | AI Data |
| 4 | Spell List |
| 5 | Full Name |
| 6 | Factions |
| 9 | NPC Skills |
| 10 | Class |
| 11 | Face |
| 12 | Default Outfit |
| 13 | Sleep Outfit |
| 24 | Gender |
| 25 | Race |

### NPC appearance implication

Face, gender, race and outfits can all participate in saved NPC ChangeForms. This is one reason appearance/base-data updates need new-game vs established-save testing and why tools such as Save Unbaker exist for selected baked fields.

## CELL

| Bit | Change category |
|---:|---|
| 1 | Flags |
| 2 | Full Name |
| 3 | Ownership |
| 28 | Exterior Short |
| 29 | Exterior Char |
| 30 | Detach Time |
| 31 | Seen Data |

Cell discovery/seen state and ownership can therefore live in save state independently of current CELL plugin defaults.

## FLST / FormList

| Bit | Change category |
|---:|---|
| 31 | Added Form |

Runtime `FormList.AddForm` behavior can persist as a ChangeForm addition. Static xEdit content is only the initial list.

## QUST

| Bit | Change category |
|---:|---|
| 1 | Quest Flags |
| 2 | Quest Script Delay |
| 26 | Quest Already Run |
| 27 | Quest Instance Data |
| 28 | Quest Runtime Data |
| 29 | Quest Objectives |
| 30 | Quest Script |
| 31 | Quest Stages |

This is direct structural evidence that quest lifecycle, objective and stage state are save-persistent overlays.

## FACT

| Bit | Change category |
|---:|---|
| 1 | Faction Flags |
| 2 | Faction Reactions |
| 31 | Faction Crime Counts |

Static faction flags/reactions can therefore be superseded by established-save state.

## RELA

| Bit | Change category |
|---:|---|
| 1 | Relationship Data |

A saved relationship change can outlive a later static RELA patch.

## TESGlobal note

Current `TESGlobal.h` in the inspected CommonLib snapshot does **not** define a form-specific `ChangeFlags` block. Global values still participate in save/runtime state, but should not be forced into the same per-form ChangeFlag table without evidence from the save parser/runtime source.

## Cross-type bit collision

Bit 31 means different things depending on form type:

- REFR: Game-Only Extra;
- FLST: Added Form;
- QUST: Quest Stages;
- FACT: Faction Crime Counts.

Similarly, bit 1 means:
- base TESForm Flags;
- NPC Base Data;
- CELL Flags;
- QUST Quest Flags;
- FACT Faction Flags;
- RELA Relationship Data.

**Never decode a ChangeForm bitmask without the FormType.**

## Troubleshooting workflow

When a plugin edit appears ignored on an existing save:

1. identify the affected form/reference;
2. identify its FormType;
3. inspect the corresponding ChangeFlags;
4. determine whether the changed field is represented in the save;
5. compare fresh game vs affected save;
6. prefer a mod-provided migration/unbake/reset;
7. only perform ReSaver surgery when the exact stale ChangeForm category is known;
8. retain backup and validate save/load cycles afterward.

## Patch and migration rules

1. Static conflict resolution and save migration are separate tasks.
2. A perfect xEdit patch cannot override every saved ChangeForm field.
3. New-game testing proves static data, not mid-save migration.
4. Scripts/native plugins should version migration logic for any persistent state they own.
5. Do not clear whole ChangeForms merely to replace one stale field.
6. Record which ChangeFlag was intentionally reset/unbaked during a repair.

## Related modules

- `ess-changeforms-savegame-internals.md`
- `papyrus-persistence-advanced.md`
- `inventory-instance-extradata-stack-model-commonlib.md`
- `native-form-actor-flag-catalog-commonlib.md`
- `plugin-record-schema-quests-dialogue.md`
