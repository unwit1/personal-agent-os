# Aredhel — VIGILANT continuity

- Continuity: `tes.mod.vigilant`
- Identity: Vigilant of Stendarr → corrupted Blood Matron follower → later Coldharbour boss/Stone fragment
- Early NPC: `NPC_ 0203430D` / `zzzBMCorruptVigilant05` — **Aredhel**
- Early reference: `ACHR 0203430E` / `BMAredhelRef`
- Early location: `CELL 02033B80` / **Enchantress' Palace**
- Early quest: `QUST 02038525` / **Remnants**
- Later NPC: `NPC_ 0204F0A9` / `zzzCHBossAredhel` — **Aredhel**
- Later reference: `ACHR 0205049F` / `CHBossRenaldRef`
- Later location: `CELL 0204C45B` / **St. Dulsa's Charnel**
- Later quest: `QUST 02052F4A` / **Pitier**
- Stone fragment: `BOOK 02110C85` / **Fragment of the Stone: Vigilant Aredhel**
- Summon: `NPC_ 02110C82` / **Aredhel**
- Signature weapon: `WEAP 0205049D` / **Aredhel's Sword**
- Key drops:
  - early form → `KEYM 0203430F` / **Aredhel's Key**
  - later Charnel form → `KEYM 0205186B` / **St. Dulsa's Key**

## Blood Matron phase

The first Aredhel is structurally part of the Blood Matron questline.

`NPC_ 0203430D`:
- display name **Aredhel**;
- internal identity `zzzBMCorruptVigilant05`;
- placed in **Enchantress' Palace**;
- owned by `QUST 02038525` / **Remnants**.

Her death list `LVLI 0203B10B` / `zzzBMDeathItemAredhel` includes:

- `BOOK 02038AAD` / **Aredhel's Note**

The note says:
- Jacob was killed;
- Joshua fled;
- the remaining Vigilants surrendered to the Blood Matron;
- Aredhel alone willingly accepted the Blood Matron's blood;
- she intended to persuade the others to accept it as well.

This establishes Aredhel as one of the captured Vigilants and as a willing participant in the Blood Matron's corruption.

The early placed actor also runs `CHAddKeyOnDeath` with:

- `KEYM 0203430F` / **Aredhel's Key**

## Coldharbour / St. Dulsa's Charnel phase

A separate later NPC record is:

- `NPC_ 0204F0A9`
- EditorID: `zzzCHBossAredhel`
- display name: **Aredhel**
- race: master High Elf race
- placed as `ACHR 0205049F` in **St. Dulsa's Charnel**.

The placed reference is internally named:

- `CHBossRenaldRef`

but points directly to the Aredhel boss base.

The owning quest is:

- `QUST 02052F4A` / **Pitier**

whose sole actor alias is internally named:

- `Renald`

and resolves to the Aredhel boss.

This is the main source of the Renald/Aredhel naming mismatch.

## Pitier encounter dialogue

`SCEN 02052F4B` / `zzzCHSQ06Sc01` uses alias 0 — the quest's Aredhel/`Renald` alias — for both dialogue actions.

The two responses are:

- “I knew you seemed familiar from somewhere... So it's really you...”
- “Monster of Molag Bal, this time I will end you for good.”

This makes the encounter a recognition/revenge scene rather than a random Charnel guardian.

It strongly supports continuity with an earlier character who encountered the player under Molag Bal/Blood Matron circumstances.

## Gaiden Shinji's account

Generic Coldharbour dialogue includes:

- `DIAL 02317664` — **Does the name Aredhel mean anything to you?**
- `INFO 02317665`

Gaiden Shinji answers that:
- Aredhel was an elf;
- Aredhel was a brilliant swordsman;
- Aredhel wanted revenge on someone;
- Gaiden gave Aredhel a sword and armor;
- he wonders what became of Aredhel.

This independently explains the later boss equipment. Gaiden's own VIGILANT dossier is preserved at `entities/characters/gaiden-shinji.md`.

## Renald-named development remnants

The later Aredhel's implementation contains many internal `Renald` identifiers:

- `zzzCHMgERenaldCombat`
- `zzzCHAbRenald`
- `zzzCHRenaldInvisibility`
- `zzzCHRenaldWindCutter*`
- `zzzCHArmorRenald*` — neighboring legacy asset family later used by Judo rather than Aredhel's actual boss outfit
- `zzzCHRenaldSword`
- `zzzCHDeathItemRenald`
- `CHBossRenaldRef`
- quest alias `Renald`
- `zzzCHSQ06RenaldTravelPlayer`
- `zzzCHRenaldMarkerList`

But the user-facing records consistently identify the shipped character as **Aredhel**:

- boss display name: Aredhel;
- weapon: **Aredhel's Sword**;
- summon: **Aredhel**;
- conjuration: **Conjure Vigilant Aredhel**;
- Stone fragment: **Fragment of the Stone: Vigilant Aredhel**;
- Gaiden's dialogue explicitly says **Aredhel**.

Current classification:

**Renald is a legacy/internal development identity for the later Aredhel encounter, not a separate lore character.**

## Equipment

The later Aredhel carries:

- two copies of `WEAP 0205049D` / **Aredhel's Sword**

and uses the outfit:

- `OTFT 024FC4B1` / `zzzCHOutfitAredhel`.

The outfit actually contains the separate **Blade of Diagna** set:

- `ARMO 024FC4A5` — **Blade of Diagna Boots**
- `ARMO 024FC4A6` — **Blade of Diagna Armor**
- `ARMO 024FC4A7` — **Blade of Diagna Gauntlets**
- `ARMO 024FC4A8` — **Blade of Diagna Helmet**

This matches Gaiden's statement that he supplied Aredhel with a sword and armor.

A separate legacy-Renald equipment family contains the **Knight of Diagna** set and the playable:

- `WEAP 02052F59` / **Akaviri Black Katana**

Those are used by **Judo of the Order of Diagna**, not by Aredhel's later boss outfit. See `analysis/diagna-coldharbour-cluster.md`.

## St. Dulsa's Key

The later placed actor `CHBossRenaldRef` runs:

- `CHAddKeyOnDeath`

with property:

- `MyKey = KEYM 0205186B` / **St. Dulsa's Key**

A locked door in St. Dulsa's Charnel uses that key.

This makes Aredhel the encounter gatekeeper for deeper Charnel access.

It does **not** by itself establish any historical relationship between Aredhel and Dulsa.

## Stone fragment / summon

The later boss death list:

- `LVLI 02052F5A` / `zzzCHDeathItemRenald`

includes:

- `BOOK 02110C85` / **Fragment of the Stone: Vigilant Aredhel**

That book teaches:

- `SPEL 02110C84` / **Conjure Vigilant Aredhel**

using:

- `MGEF 02110C83` / **Conjure Vigilant Aredhel**

which summons:

- `NPC_ 02110C82` / **Aredhel**

The summon templates directly from the later Aredhel boss and carries Aredhel's swords.

The phrase **Vigilant Aredhel** is particularly important because it connects the later Coldharbour boss back to Aredhel's earlier Vigilant identity.

## Identity reconstruction

The strongest sequence is:

**Vigilant Aredhel is captured in the Blood Matron incident → willingly accepts the Blood Matron's blood → is encountered/killed during Remnants → later appears in Coldharbour as the Pitier boss → Gaiden has supplied her with new sword/armor for revenge → she recognizes the player and calls them a Monster of Molag Bal → her Stone fragment preserves a summonable “Vigilant Aredhel” form.**

No single record directly says “this is the same Aredhel from Remnants.”

However, the combined evidence is unusually strong:

1. identical uncommon character name;
2. first form explicitly belongs to the Vigilants;
3. later fragment explicitly calls her **Vigilant Aredhel**;
4. later dialogue is recognition/revenge dialogue;
5. Gaiden explains the new equipment and revenge motive;
6. the later boss is part of Coldharbour, where earlier souls/identities recur.

Current classification: **high-confidence same-character identity cluster; exact metaphysical mechanism of reappearance unresolved.**

## Open questions

The ESM does not yet establish:
- exactly whom Aredhel wants revenge on in Gaiden's account, though the Pitier scene strongly points toward the player;
- how she moves from Blood Matron corruption into the later High Elf-form Coldharbour encounter;
- whether the later body is her historical body, soul, memory reconstruction, or Stone-preserved manifestation;
- why the encounter was originally developed under the name **Renald**.

## Canon boundary

Aredhel, the Blood Matron corruption, Pitier encounter, Gaiden connection, and Stone-fragment afterlife are VIGILANT-specific.
