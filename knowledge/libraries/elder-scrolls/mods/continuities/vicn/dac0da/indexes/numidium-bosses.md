# Numidium boss actor index

**Continuity:** `tes.mod.vicn.dac0da`  
**Primary context:** `zDcdMq04` — Numidium Tertius

This index resolves the concrete actor forms used by DAc0da's five dedicated Numidium boss quests.

## Boss 01 — Nchunak

**Quest:** `zDcdMqBoss01` — VS Nchunak  
**Quest source:** `DAc0da.esm:00B265`

Alias `Boss` points directly to:

- `DAc0da.esm:006B69`
- `zDcdBossDweGeneral01`
- FULL: **Nchunak the Evangelist**
- short name: **Nchunak**

The plugin also contains a distinct **Nchunak the Second** actor/summon form, so these should not be silently merged.

## Boss 02 — Ghost Choir 9 / O.Y.A.R.S.A.

**Quest:** `zDcdMqBoss02` — VS GC9  
**Quest source:** `DAc0da.esm:00B3A8`

Key aliases include:

- `Oyarsa` -> `DAc0da.esm:00B2CD` — **O.Y.A.R.S.A**
- `GCBase` -> `DAc0da.esm:0079C9` — **GC9**
- `GCBase2` -> `DAc0da.esm:00B446` — **GC9**

The remaining GC-name aliases are used to present the named Ghost Choir roster already indexed in `organizations/ghost-choir-9.md`.

## Boss 03 — Arcanist

**Quest:** `zDcdMqBoss03` — VS Arcanist  
**Quest source:** `DAc0da.esm:00B4F1`

Alias `Boss` points directly to:

- `DAc0da.esm:00B217`
- `zDcdBossArcanist01`
- FULL: **Arcanist**

This is the boss actor associated with the Apocryphal intrusion inside Numidium.

The actor's gear/effect namespace includes repeated **Golden Eye's Blessing** enchantments and Arcanist-specific abilities. These are mechanical/item evidence; the exact theological meaning of "Golden Eye" is not established by the boss quest itself.

## Boss 04 — Zurin Arctus

**Quest:** `zDcdMqBoss04` — VS Zurin Arctus  
**Quest source:** `DAc0da.esm:00B5EE`

Aliases:

- `Monk` -> Rolls-On-Roads
- `Boss` -> `DAc0da.esm:00AF11` — **Zurin Arctus**

The boss form is:

- `zDcdBossUnderking2nd`
- FULL: **Zurin Arctus**
- short name: **Zurin**

It carries **Wilt-Flower Greatsaber (Dual)**.

The boss quest's own dialogue has Rolls-On-Roads identify the approaching attacker as a lich after sensing decay in the hostile magic, followed by Zurin addressing **Hjalti** and questioning who Hjalti truly was.

See `characters/zurin-arctus.md`.

## Boss 05 — Dumac

**Quest:** `zDcdMqBoss05` — VS Dumac  
**Quest source:** `DAc0da.esm:00B6DC`

Alias `Boss` points directly to:

- `DAc0da.esm:00B1F8`
- `zDcdBossDweKing`
- FULL: **Dumac's Tonalframe**

The form carries **King Dumac's Greatsword**.

The explicit "Tonalframe" naming supports the main-quest explanation that the encounter is not simply the historical physical body of Dumac.

See `characters/dumac-tonalframe.md` and `analysis/dumac-records-zero-sum.md`.

## Retrieval rule

These five boss aliases establish which concrete forms the game actually uses. Dialogue/metaphysical claims about those forms still require their own evidence and should not be inferred solely from editor IDs or encounter titles.
