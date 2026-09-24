# RaceMenu / SKEE Appearance-State Persistence Model

Imported: 2026-09-24
Pinned source commit: `9ebcb733e17be695f994cd2e9cc383043446bc02`
Status: source-backed runtime/save-state model

## SKEE serialization owner

SKEE registers SKSE serialization unique ID:

`SKEE`

and installs:
- Revert callback;
- Save callback;
- Load callback.

## Save order / state families

Current source saves these major subsystems:

1. String table
2. Face morph/sculpt interface
3. NiTransform interface
4. Overlay interface
5. Override interface
6. BodyMorph interface
7. ItemData interface

## Serialized record chunks

The current loader recognizes:

| Chunk | Meaning / owner |
|---|---|
| `STTB` | SKEE string table |
| `MRST` | face morph data |
| `SCDT` | face sculpt data |
| `AOVL` | actor overlays |
| `ACEN` | armor/addon overrides |
| `NDEN` | node overrides |
| `WPEN` | weapon overrides |
| `SKNR` | skin overrides |
| `MRPH` | body morph data |
| `ITEE` | item data |
| `ACTM` | actor/node transform data |

## Revert behavior

SKEE clears/reverts:
- actor update manager;
- overlays;
- overrides;
- body morphs;
- item data;
- dye map;
- transforms;
- face morph interface;
- attachment interface;
- string table.

This is direct evidence that these systems maintain runtime state beyond static ESP/ESM records.

## BodyMorph

### Identity

BodyMorph state is keyed by:
- actor/reference;
- morph name;
- morph key/provider;
- float value.

This permits multiple mods/providers to contribute to one named body morph without necessarily overwriting each other's key.

### Key semantics

`morphName` identifies the shape/morph channel.
`morphKey` identifies one contributor/namespace.

Clearing one key is different from clearing the entire morph name or every morph on the actor.

### Application

Serialized morph values and rendered geometry are separate layers:
- serialized state records desired morph contributions;
- model/3D updates apply those contributions to loaded meshes/TRI morph data.

A correct saved morph can therefore appear visually absent if:
- actor 3D is not updated;
- generated body/outfit lacks the required morph;
- TRI/topology mismatch exists;
- skeleton/mesh winner differs;
- deferred update fails.

## NiTransform

Node transform state can vary by:
- actor/reference;
- first-person vs third-person;
- sex;
- node name;
- named transform key/provider.

Transform components include:
- position;
- rotation;
- scale;
- scale mode.

This is another layered contribution model: named transform keys allow multiple systems to own transformations on the same node.

## Overrides

SKEE stores multiple override families separately:

### Armor/addon override
Targets actor + sex + ARMO + ARMA + node + property key/index.

### Node override
Targets actor + sex + node + property key/index.

### Weapon override
Targets actor/equipment/weapon/node semantics.

### Skin override
Targets actor + sex + first-person + biped slot + property key/index.

Override values can be typed:
- Int;
- Float;
- String;
- Bool;
- TextureSet.

Therefore “the NIF looks right” does not prove the live shader/property state equals the file's defaults.

## Overlays

Overlay state controls actor overlay nodes for:
- body;
- hands;
- feet;
- face;
- normal vs spell overlays.

Overlay count/config and serialized actor overlay state are distinct:
- INI/config decides capacity/behavior;
- save state decides which actor overlays exist;
- generated/runtime nodes implement them on 3D.

## ItemData

SKEE can attach data to unique inventory instances using identifiers that incorporate ExtraUniqueID/owner information.

This explains why:
- two copies of the same ARMO can have different dyes/data;
- dropping/recreating an item may lose or change instance-specific state;
- base ARMO/ARMA record comparison is insufficient for dye/instance bugs.

## Face morph and sculpt

Face morph/sculpt data has dedicated serialization chunks separate from ordinary NPC_ face fields and FaceGen files.

For the player and supported actors, apparent face state may be a composition of:
- NPC_ base appearance;
- FaceGen NIF/DDS;
- RaceMenu morph values;
- sculpt deltas;
- headpart selection;
- overlays/tints;
- external head/preset state.

## Presets are not saves

RaceMenu preset files and SKSE co-save appearance state are different persistence channels.

A preset is an explicit import/export artifact. Loading a preset can apply selected categories (face, overrides, body morphs, transforms, skin overrides) but does not mean every prior save-side SKEE state is automatically absent.

## Troubleshooting matrix

| Symptom | Inspect first |
|---|---|
| Body differs only on old save | `MRPH` body morph state + generated meshes/TRI |
| Node scale returns after reinstall | `ACTM` serialized transform state |
| Armor shader differs for one actor | `ACEN`/skin/node override state |
| One weapon/item has unique color | `ITEE` instance data + ExtraUniqueID |
| Overlay returns on save load | `AOVL` state |
| Face differs despite correct FaceGen | `MRST` / `SCDT` + head/tint/overlay state |
| New game fixes appearance | save-side SKEE state strongly implicated |
| Body correct naked but outfit wrong | outfit mesh/TRI/BodySlide, not necessarily MRPH |
| First-person node differs only | NiTransform first-person branch |
| Clearing one mod's morph breaks others | morph keys/providers were not isolated correctly |

## Reset hierarchy

Before destructive save editing, determine which layer owns the visible result:

1. static NPC_/ARMO/ARMA/plugin data;
2. loose/BSA mesh/texture/TRI;
3. BodySlide/generated output;
4. RaceMenu/SKEE serialized morph/override/transform/item data;
5. currently loaded actor 3D;
6. external preset/config;
7. another runtime framework applying changes after SKEE.

## Safety rule

Do not delete all SKEE co-save state merely to solve one actor/body issue unless the user deliberately accepts losing every mod's SKEE-owned appearance data. Prefer provider-key or actor-specific cleanup where APIs permit.
