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

### Non-dialogue/support passes completed

- `zDcdSqPrisoner` — **In Grabbers' Hands**
  - radiant clearable-dungeon target with selected Boss alias
  - Boss script: `DcdNymicStealerAliasScript`
  - Kye = **Book of the Prisoner**
  - quest nymic object = `Bendu Olo Olo`
  - strong mechanical Grabber <-> stolen-name/nymic relationship; exact compiled rename logic still unavailable
- `zDcdEpiQYngol` — branch-dependent dead-dragon/reward-chest aftermath
- `zDcdMqDragon` — Golden Dragon Flight stage/package choreography
- `zDcdMqAgent` — scripted Yaghra-Agent manifestation
  - dedicated Agent ash pile contains the six Daggerfall Totem correspondence letters

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

Known/reused source material is now substantially provenance-separated:

- six Daggerfall/Totem correspondence records are **verified official Daggerfall text reuse**, with DAc0da-specific static placeholder substitutions;
- `Djaf: Arena of Lyg` is verified community apocrypha by **mojonation1487**;
- `ANON/ANU/ANUI-EL / KINMUNE`, `The Tsaesci Creation Myth`, `Dominion Prism Textract`, `et'Ada, Eight Aedra, Eat the Dreamer`, `Lament for Pelinal`, and `A Type of Zero Still to Be Discovered` are verified reused Michael Kirkbride developer/obscure material;
- the exact original standalone publication/authorship trail for the long `Ghost Choir 9` BOOK remains unresolved.

## Resume here

### P1 — SCEN coverage

Build a deterministic index over all **79 SCEN records**.

For each scene:

1. capture local FormID and EditorID;
2. resolve the owning quest where possible;
3. decode scene actor/alias references;
4. map aliases back to QUST alias names and concrete NPCs;
5. identify dialogue/actions that are only recoverable through scene structure;
6. flag scenes that materially change an existing character, quest, or chronology dossier.

Prioritize scene-only lore over pure choreography.

### P2 — entity/location coverage

After the first scene pass:

- expand unresolved NPC/form families;
- index important CELL/WRLD/location layers;
- index artifacts/items/creatures where placement, inventory, or scripts carry lore.

### P3 — remaining provenance

Recover the exact standalone source for the long **Ghost Choir 9** text if possible.

Preserve conditional branches, speaker reliability, alternate realities, source provenance, and mechanical-vs-narrative evidence boundaries. Do not silently promote DAc0da/Vicn claims into official Elder Scrolls canon.
