# DAc0da ingestion checkpoint 01

Continuity: `tes.mod.vicn.dac0da`

## Source

- `DAc0da.esm`
- SHA-256: `455f07f3bba5de5b1b5a84c882be3309a66fd3d503866e05658b99896dfdb00e`
- Stable provenance format: `DAc0da.esm:<load-order-independent local FormID>`

Do not restart the structural inventory unless the source hash changes.

## Completed

### Structural

- First-pass ESM inventory: 51,137 resolved records.
- All 43 QUST records indexed.
- DIAL -> INFO/NAM1 dialogue extraction established.
- Selected quest aliases resolved to concrete NPC forms.
- All 90 BOOK records inventoried and split into narrative/provenance versus spell/item material.

### Numbered main quest

Reconstructed at first lore depth:

- `zDcdMq00` — **The Call of Landfall**
- `zDcdMq01` — **The Sea of Causality**
- `zDcdMq02` — **Negative Legacy**
- `zDcdMq03` — **Patchwork**
- `zDcdMq04` — **Numidium Tertius**
- `zDcdMq05` — **Censored Fate**

### Major side quests / endings

Processed:

- `zDcdSqYngol` — **Drowned Nighthawk**
- `zDcdSqHalfElf` — **The End of All Wishes**
- `zDcdSqAbnur` — **Abnur Tharn**
- `zDcdSqWorm` — **Echoes of Mnemolichite**
- `zDcdSqWormSub01` — Option: Dreugh
- `zDcdSqWormSub02` — Group Battle: The Sload City
- `zDcdSqWormSub03` — Group Battle: The Revenant
- `zDcdSqWormSub04` — **The Sea of Radiance**
- `zDcdSqAugur` / `zDcdGenAugur` — Augur of the Obscure material
- `zDcdSqSheogorath` — **Cheese Party**
- `zDcdSqSloadRadio` — **Sload Radio**
- `zDcdMqCheeseEnd` — **Rella Mozzarella**
- `zDcdMqArgoEnd` — **Pan-Argonia**
- Abnur Tharn epilogue/will
- Akashiya-Samon epilogue/follow-up

### Structural seed awaiting non-dialogue analysis

- `zDcdSqPrisoner` — **In Grabbers' Hands**
  - direct objective: retrieve Kye and **restore your name**
  - aliases: Player, Boss, Kye
  - no directly owned DIAL topics, so scene/script/form analysis is required

### Major dossiers/concepts

- Rolls-On-Roads
- Akashiya-Samon
- Yngol
- Beynhaal
- Vanus Galerion
- Templar of Hahd Yu'qbar
- Vigilant Athanasius
- Augur of the Obscure
- Ghost Choir 9
- Republic of Hahd
- Prisoner / Many Paths
- mnemolichite
- Adjacent Places / Grabbers
- time breaches / mirror logic / zero-sum
- Hist / Jills / Akulakhan / Fifth-Era anomaly

## Strong cross-Vicn bridges now indexed

### GLENMORIL

**Rolls-On-Roads -> Romion** is a direct named relationship. DAc0da describes Romion as Rolls-On-Roads' Altmer Dwemer-scholar friend/former colleague; GLENMORIL independently defines Romion as a major Dwemer-study/Yelem-School character.

### VIGILANT

BOOK `DAc0da.esm:006133`, **Letter to a Friend**, sends a seeker of Radiance to nightmare-plagued Dawnstar to find a Vigilant named **Altano**, learn compassion, and undergo suffering. VIGILANT independently has Altano as a central character.

### UNSLAAD

DAc0da and UNSLAAD independently use the rare exact vocabulary **Adjacent Place** and **Grabbers**. UNSLAAD connects an adjacent place to Lyg and fate-changing mirrors; DAc0da's Augur says he comes from an Adjacent Place and warns about Grabbers.

### Mnemo-Li

DAc0da, GLENMORIL, and UNSLAAD independently cluster **Mnemo-Li** with memory, possibility/multiple states, dream/reality instability, and unusual identity transformations. Source-specific mechanics remain separate.

## Written-lore pass 01

The BOOK inventory is:

- 66 spell/summon/item books;
- 13 letters/notes;
- 11 Nahd-fiction/apocryphal texts.

High-value written findings include:

- Snow-Elf orders to attack Jylkurfyk under a claimed contract with Lord Dagon;
- a separate letter explicitly describing an anti-elven/mixed-blood purge at Jylkurfyk;
- direct Radiance -> Altano/VIGILANT link;
- Abnur's time-displacement note;
- Sload orders to N'Danda;
- Abnur will variants;
- three alternate-reality Temporal Tomes.

Known/reused source material is being provenance-separated:

- six Daggerfall/Totem correspondence records are source-reuse candidates;
- `ANON/ANU/ANUI-EL` already matches the apocryphal library;
- `A Type of Zero Still to Be Discovered` already has verified developer-obscure-text provenance in the library;
- remaining `NahdFiction_*_MK` texts still need exact source reconciliation.

## Resume here

### P1 — non-dialogue identity/name pass

Start with:

**`DAc0da.esm:00CEFE` — `zDcdSqPrisoner` — In Grabbers' Hands**

Resolve:

1. Kye's form and identity.
2. Boss form/identity.
3. target location.
4. attached scripts, scenes, activators, messages, items, effects, and conditions.
5. what the game mechanically means by **"restore your name."**
6. whether the mechanic directly links Grabbers to stolen name/identity data.

Do not infer mechanism from the title/objective alone.

### P2 — remaining support/epilogue records

Then process:

- `zDcdEpiQYngol` — Yngol epilogue via scenes/scripts;
- `zDcdMqDragon` — Golden Dragon Flight;
- `zDcdMqAgent` — Agent Event;
- Numidium shortcut/manager material where it adds lore.

### P3 — provenance / indexing

- exact text comparison for six Daggerfall/Totem letters;
- exact source resolution for unresolved `NahdFiction_*_MK` texts;
- scene-speaker coverage;
- remaining NPC/location/artifact/creature indexing.

Preserve conditional branches, speaker reliability, alternate realities, and source provenance. Do not silently promote DAc0da/Vicn claims into official Elder Scrolls canon.
