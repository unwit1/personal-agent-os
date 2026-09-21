# Aredhel / Renald identity resolution

Continuity: `tes.mod.vigilant`

Primary source: user-provided `Vigilant.esm`

## Question

Why does the St. Dulsa's Charnel actor appear in internal records as **Renald**, while the NPC and player-facing material call the character **Aredhel**?

## Result

The ESM strongly indicates that **Renald is a legacy development name for the later Aredhel encounter**.

There is no shipped NPC whose display name is Renald in this cluster.

The actual boss base is:

- `NPC_ 0204F0A9`
- EditorID: `zzzCHBossAredhel`
- display: **Aredhel**

The legacy Renald name survives in:
- spells;
- combat effects;
- armor EditorIDs;
- sword EditorIDs;
- death-item list;
- placed-reference EditorID;
- quest alias;
- packages;
- marker lists;
- crafting recipes.

Player-facing names were changed to Aredhel.

## Early Aredhel

The Blood Matron questline contains:

- `NPC_ 0203430D` / **Aredhel**
- internal role: `zzzBMCorruptVigilant05`
- `ACHR 0203430E` / `BMAredhelRef`
- `QUST 02038525` / **Remnants**
- location: **Enchantress' Palace**

Her death list contains **Aredhel's Note**, which identifies her as one of the surrendered Vigilants and says she willingly accepted the Blood Matron's blood.

## Later Aredhel

The Coldharbour record:

- `NPC_ 0204F0A9` / **Aredhel**

is:
- a High Elf;
- placed in **St. Dulsa's Charnel**;
- owned by `QUST 02052F4A` / **Pitier**;
- equipped with **Aredhel's Sword** and the separate **Blade of Diagna** armor set.

The quest alias is still called `Renald`, but resolves directly to this Aredhel base.

## Scene ownership proves the dialogue speaker

`SCEN 02052F4B` / `zzzCHSQ06Sc01` uses alias 0 for its dialogue actions.

Alias 0 in *Pitier* is the internal `Renald` alias resolved to **Aredhel**.

Therefore the two scene responses are structurally Aredhel's:

- recognition of the player;
- vow to destroy the “Monster of Molag Bal.”

## Gaiden supplies the renamed gear

`DIAL 02317664` asks Gaiden Shinji about Aredhel.

`INFO 02317665` says the elf Aredhel:
- was a brilliant swordsman;
- wanted revenge;
- received a sword and armor from Gaiden.

The later boss:
- is an elf;
- carries **Aredhel's Sword**;
- wears the **Blade of Diagna** armor set through `zzzCHOutfitAredhel`.

This is a strong narrative explanation for the boss's equipment after the rename.

The old internally `Renald`-named **Knight of Diagna** armor family is instead worn by **Judo of the Order of Diagna**, a named Soul-Shriven encounter. The legacy asset naming therefore spans more than one shipped character and must not be used as identity evidence by itself.

## Vigilant identity survives the rename

The later boss death list includes:

- **Fragment of the Stone: Vigilant Aredhel**

which teaches:
- **Conjure Vigilant Aredhel**.

That wording strongly bridges the later Coldharbour boss back to the earlier Vigilant character.

If “Renald” were intended as a separate person, the fragment and summon would be unexpectedly misnamed at every player-facing layer.

## Two different NPC records do not mean two different people

The early and late Aredhel forms use different NPC bases:

- Blood Matron Aredhel: `0203430D`
- Coldharbour Aredhel: `0204F0A9`

VIGILANT frequently uses multiple NPC forms for:
- memories;
- historical states;
- corrupted states;
- summons;
- Coldharbour manifestations.

So separate FormIDs do not by themselves establish separate identities.

## Key progression

Both placed Aredhel forms use the same generic pattern:

- `CHAddKeyOnDeath`

but with different keys.

### Blood Matron Aredhel
- drops **Aredhel's Key**

### Coldharbour Aredhel
- drops **St. Dulsa's Key**

This is encounter gating, not evidence that the later actor is a separate Renald.

## Development-history caution

The ESM alone cannot tell us:
- when the rename occurred;
- whether “Renald” was an earlier draft character concept;
- whether that draft had different lore;
- why some internal records were never renamed.

Lorekeeper should not reconstruct a discarded “Renald character” from EditorIDs alone.

## Current classification

- **Aredhel (Blood Matron) → Aredhel (Pitier): high-confidence same identity**
- **Renald → player-facing character identity: superseded internal/development name**
- **exact post-death/Coldharbour mechanism: unresolved**

## Lorekeeper rule

When encountering `Renald`-named records in this cluster, normalize their character target to:

**Aredhel [VIGILANT]**

while preserving the raw EditorID for provenance/debugging.

Do not create a separate Renald character entity unless future source material explicitly distinguishes one.
