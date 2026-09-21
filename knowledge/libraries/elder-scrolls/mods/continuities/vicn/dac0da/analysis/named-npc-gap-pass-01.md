# DAc0da named NPC gap pass 01

**Continuity:** `tes.mod.vicn.dac0da`  
**Source class:** NPC_ / QUST / INFO / placement

This pass audits named-looking NPC forms that remained after the main character, boss, form-family, and creature-family indexes were built.

## Promoted to dedicated dossiers

### Lokir of These Parts

- `DAc0da.esm:00AA00`
- directly owned by MQ00 alias `Lokir`
- Rolls-On-Roads explicitly says the actor is a **summoned Daedra assuming a familiar form**

See `characters/lokir-of-these-parts.md`.

### Crab Spirit

- `DAc0da.esm:00492F`
- directly owned by MQ02 alias `Crab`
- speaks in the memospore sequence to an intended **Vestige** recipient before the Augur identifies it as the wrong recording

See `characters/crab-spirit.md`.

## Encounter-only named forms

The following named actors have concrete placed references and distinctive custom body plans, but no direct INFO condition assigning unique ordinary dialogue and no QUST alias ownership found in the first deterministic scan.

They remain **encounter/morphology records**, not standalone character dossiers.

### Hare's Servant

- `DAc0da.esm:00475E`
- Editor ID: `zDcdSubbossManThing`
- race: **Man-Thing**
- placed in `DcdHareMound01`

Retrieve with the Hans-the-Fox / Forelgrim / cursed-hare environmental insight material.

### Khemkel's Wooden Idol

- `DAc0da.esm:004F3A`
- Editor ID: `zDcdSubBossWoodWraith`
- race: large **Wood Wraith**
- placed in `DcdForelgrimC01`

The name is an encounter title; no first-pass evidence establishes a separately narrated biography for an individual called Khemkel.

### Eye of Orgnum

- `DAc0da.esm:004F7F`
- Editor ID: `zDcdSubbossIceSerpent`
- race: large **Ice Serpent**
- placed in `DcdFrostSeaC06`

The name is a strong Maormer/Orgnum-flavored encounter label, but the actor has no unique dialogue or quest-owned identity in the current pass.

### Blue Dugal

- `DAc0da.esm:0051A5`
- Editor ID: `zDcdSubbossDragoMan`
- race: **Drago man**

No unique dialogue or direct narrative quest alias was recovered.

### Archangel of Xrib

- `DAc0da.esm:0051F9`
- Editor ID: `zDcdSubbossXribAngel`
- race: **Xrib Angel**
- placed in `DcdFrostSeaB07`

The actor is a named subboss/body form. Its relationship to Xrib beyond the title is not explained by unique dialogue in the first pass.

## Audit conclusion

The presence of a colorful FULL name is not enough to justify a character biography.

Promote an encounter actor to a dossier when at least one of the following is present:

- unique dialogue;
- direct quest alias/role;
- written biography/history;
- meaningful script/state transitions;
- repeated cross-record identity evidence.

Otherwise keep the actor in encounter/race/location indexes.

This reduces false lore inflation while preserving every named encounter for retrieval.
