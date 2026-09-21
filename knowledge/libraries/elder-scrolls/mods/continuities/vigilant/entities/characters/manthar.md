# Manthar

- Continuity: `tes.mod.vigilant`
- Historical role: sorcerer and architect of the Alessian Order
- Boss form: `NPC_ 021146D9` / `zzzCHBossBoneLord` — **Sorcerer Manthar**
- Summon form: `NPC_ 0213B503` / `zzzCHSummonBoneLord` — **Sorcerer Manthar**
- Placed boss reference: `ACHR 021146DA`
- Encounter location: **Funeral Temple** (`CELL 021114AF`)

## Saint tradition

`BOOK 020CB0DF` / *The Eight Saints of Cyrod* describes Manthar as a sorcerer and architect of the Alessian Order.

It says he:
- worked with **Nenyond**;
- helped construct hundreds of priories funded by Nenyond;
- participated in the construction of Nenyond's underground priory;
- disappeared together with Nenyond while exploring Dawn Era ruins uncovered during the work.

The book later says **Silorn** entered the sealed ruins searching for Nenyond and Manthar and never returned intact.

## VIGILANT implementation

The ESM gives Manthar a concrete post-historical identity:

- `021146D9` — **Sorcerer Manthar**, implemented as the `zzzCHBossBoneLord` NPC;
- `0213B503` — a summon version of Sorcerer Manthar;
- `MGEF 0213B504` — **Conjure Sorcerer Manthar**;
- `ACHR 021146DA` — the boss form is physically placed in **Funeral Temple**.

The Funeral Temple is directly linked by the Coldharbour door graph to **Nenyond's Underground Priory**, making Manthar's boss placement spatially consistent with the disappearance story preserved in *The Eight Saints of Cyrod*.

## Evidence limits

No INFO records currently resolve uniquely to Manthar. His surviving role is therefore reconstructed from:

1. the saint biography;
2. NPC identity/name;
3. placed boss form;
4. summon/magic-effect implementation;
5. the Nenyond/Funeral Temple geography.

The ESM strongly supports that VIGILANT intends **Sorcerer Manthar** to be the same historical identity cluster described in the saint text, but it does not yet explain how the missing architect became the Bone Lord boss form.

## Canon boundary

Manthar's Alessian biography, disappearance with Nenyond, and later Bone Lord manifestation belong to `tes.mod.vigilant` unless separately corroborated by licensed Elder Scrolls sources.
