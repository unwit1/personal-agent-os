# Skyrim Record Header and Reference Flag Semantics — xEdit 4.1.5f

Imported: 2026-09-24
Source: `TES5Edit/TES5Edit` tag `xedit-4.1.5f`
Source file: `Core/wbDefinitionsTES5.pas`
Source blob SHA: `8455d8b86440712de6e280f1e113572ffefbd11d`
Status: source-backed context-aware flag reference

## Core rule: record flags are contextual

Skyrim main records have a 32-bit Record Flags field, but **the semantic name of a bit depends on the record type and sometimes on the base object of a placed reference**.

xEdit intentionally starts from a generic 32-bit flag set and overlays per-record meanings.

Do not maintain or use one universal table that says, for example, “bit 9 always means X.”

## TES4 main-file header flags

For the `TES4` record xEdit 4.1.5f defines:

| Bit/value | Meaning |
|---|---|
| 0 / `0x00000001` | ESM |
| 1 / `0x00000002` | Altered |
| 2 / `0x00000004` | Checked |
| 3 / `0x00000008` | Active |
| 4 / `0x00000010` | Optimized File |
| 5 / `0x00000020` | Temp ID Owner |
| 7 / `0x00000080` | Localized |
| 8 / `0x00000100` | Precalc Data Only |
| 9 / `0x00000200` | ESL in SSE |

### ESM
Marks the plugin as a master in the TES4 header.

### Localized
Plugin string fields are resolved through STRINGS/DLSTRINGS/ILSTRINGS rather than stored only inline.

### ESL
For SSE, TES4 bit 9 marks the plugin light/ESL behavior. The same bit is not a universal “ESL” flag on arbitrary records.

## ACHR — placed actor reference flags

xEdit defines these named ACHR flags in the placed-NPC reference schema:

| Bit/value | Meaning |
|---|---|
| 9 / `0x00000200` | Starts Dead |
| 10 / `0x00000400` | Persistent |
| 11 / `0x00000800` | Initially Disabled |
| 25 / `0x02000000` | No AI Acquire |
| 29 / `0x20000000` | Don't Havok Settle |

### Starts Dead
The actor reference begins dead.

### Persistent
Reference resides/behaves as a persistent reference rather than an ordinary temporary cell reference. Quest alias/persistence rules can interact with this.

### Initially Disabled
The placed reference starts disabled until enabled by quest/script/enable-parent logic.

### No AI Acquire
Prevents ordinary AI acquisition behavior for that reference context.

### Don't Havok Settle
Suppresses ordinary Havok-settling behavior on load.

## REFR — generic/common placed-object flags

For the generic REFR case xEdit exposes:

| Bit/value | Meaning |
|---|---|
| 10 / `0x00000400` | Persistent |
| 11 / `0x00000800` | Initially Disabled |
| 16 / `0x00010000` | Is Full LOD |
| 26 / `0x04000000` | Filter (Collision Geometry) |
| 27 / `0x08000000` | Bounding Box (Collision Geometry) |
| 28 / `0x10000000` | Reflected By Auto Water |
| 30 / `0x40000000` | Ground |
| 31 / `0x80000000` | Multibound |

But xEdit then switches to **base-type-specific flag maps**.

## REFR with ACTI / STAT / TREE / FLOR base

| Bit | Meaning |
|---:|---|
| 9 | Hidden From Local Map |
| 10 | Persistent |
| 11 | Initially Disabled |
| 13 | Sky Marker |
| 15 | Visible when distant |
| 16 | Is Full LOD |
| 26 | Filter (Collision Geometry) |
| 27 | Bounding Box (Collision Geometry) |
| 28 | Reflected By Auto Water |
| 29 | Don't Havok Settle |
| 30 | No Respawn |
| 31 | Multibound |

## REFR with CONT base

| Bit | Meaning |
|---:|---|
| 10 | Persistent |
| 11 | Initially Disabled |
| 16 | Is Full LOD |
| 25 | No AI Acquire |
| 26 | Filter (Collision Geometry) |
| 27 | Bounding Box (Collision Geometry) |
| 28 | Reflected By Auto Water |
| 29 | Don't Havok Settle |
| 30 | Ground |
| 31 | Multibound |

## REFR with DOOR base

| Bit | Meaning |
|---:|---|
| 6 | Hidden From Local Map |
| 8 | Inaccessible |
| 10 | Persistent |
| 11 | Initially Disabled |
| 16 | Is Full LOD |
| 26 | Filter (Collision Geometry) |
| 27 | Bounding Box (Collision Geometry) |
| 28 | Reflected By Auto Water |
| 29 | Don't Havok Settle |
| 30 | No Respawn |
| 31 | Multibound |

## REFR with LIGH base

| Bit | Meaning |
|---:|---|
| 8 | Doesn't Light Water |
| 9 | Casts Shadows |
| 10 | Persistent |
| 11 | Initially Disabled |
| 16 | Never Fades |
| 17 | Doesn't Light Landscape |
| 25 | No AI Acquire |
| 28 | Reflected By Auto Water |
| 29 | Don't Havok Settle |
| 30 | No Respawn |
| 31 | Multibound |

## REFR with MSTT base

| Bit | Meaning |
|---:|---|
| 9 | Motion Blur |
| 10 | Persistent |
| 11 | Initially Disabled |
| 16 | Is Full LOD |
| 26 | Filter (Collision Geometry) |
| 27 | Bounding Box (Collision Geometry) |
| 28 | Reflected By Auto Water |
| 29 | Don't Havok Settle |
| 30 | No Respawn |
| 31 | Multibound |

## REFR with ADDN base

| Bit | Meaning |
|---:|---|
| 10 | Persistent |
| 11 | Initially Disabled |
| 16 | Is Full LOD |
| 28 | Reflected By Auto Water |
| 29 | Don't Havok Settle |
| 30 | No Respawn |
| 31 | Multibound |

## REFR with inventory-object base

For ALCH, SCRL, AMMO, ARMO, INGR, KEYM, MISC, SLGM and WEAP, xEdit uses a shared placed-reference map including:

- Persistent;
- Initially Disabled;
- Is Full LOD;
- No AI Acquire;
- Reflected By Auto Water;
- Don't Havok Settle;
- No Respawn;
- Multibound.

## STAT base-record flag examples

Static records demonstrate how the same header bits gain yet another meaning:

| Bit | STAT meaning |
|---:|---|
| 2 | Never Fades |
| 5 | Deleted |
| 6 | Has Tree LOD |
| 7 | Add-On LOD Object |
| 9 | Hidden From Local Map |
| 15 | Has Distant LOD |
| 17 | Uses HD LOD Texture |
| 19 | Has Currents |
| 23 | Is Marker |
| 25 | Obstacle |
| 26 | NavMesh Generation - Filter |
| 27 | NavMesh Generation - Bounding Box |
| 28 | Show In World Map |
| 30 | NavMesh Generation - Ground |

This is direct evidence that bit semantics are not global.

## Deleted flag

Many ordinary record schemas use bit 5 / `0x00000020` as **Deleted**, but TES4 itself uses the same bit as **Temp ID Owner**.

Therefore even apparently famous bits must be interpreted through the parent record schema.

## Compressed flag

The historical/global xEdit commentary maps bit 18 / `0x00040000` to **Compressed** for record families where compression applies. xEdit's active schema still specializes flags per record.

Treat compression as a main-record storage property, not a gameplay semantic.

## Quest Item / Persistent overlap

Historical xEdit comments show `0x00000400` can describe:
- Persistent Reference on reference records;
- Quest Item on selected item/form records;
- Displays In Main Menu on LSCR.

Again, parent record identity decides the meaning.

## Diagnostic rules

1. Always decode a flag through the **specific record schema**.
2. For REFR, base-object type can change the meaning xEdit assigns to individual bits.
3. Do not compare raw Record Flags between unrelated record signatures and assume equal bits mean equal behavior.
4. A patcher should preserve only flags whose intended semantics are understood for that parent type.
5. “Persistent” and “Initially Disabled” are reference lifecycle flags; they are not interchangeable with quest-alias persistence or current runtime enabled state.
6. “Deleted” on a normal record is not the same situation as “Initially Disabled.”
7. `ESM`, `Localized`, and `ESL` are TES4 header semantics, not global bits for all forms.
8. A future schema generator should attach flag labels to **record-signature + variant/base-type context**, not to the bit value alone.

## Related modules

- `plugin-record-signature-catalog-xedit.md`
- `object-reference-lifecycle-interactions.md`
- `xedit-plugin-format-advanced.md`
- `modern-esl-header-compatibility.md`
- `worldspace-navmesh-saves-persistence.md`
