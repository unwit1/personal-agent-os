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
- the long `Ghost Choir 9` BOOK is verified Michael Kirkbride unofficial/developer-text reuse, originally posted to **The Elder Scrolls Forums** on **2012-02-18**.

## Completion marker

For source hash:

`455f07f3bba5de5b1b5a84c882be3309a66fd3d503866e05658b99896dfdb00e`

> **First-pass DAc0da ESM lore ingestion: COMPLETE**

Additional completion work after the earlier checkpoint:

- all 79 SCEN records indexed;
- worldspace/location layers indexed;
- character-form families indexed;
- creature/faction and custom-race morphology passes completed;
- narrative artifacts indexed;
- 66 MESG records covered by insight/system passes;
- Generic Dialogue and Citizen Dialogue normalized;
- named NPC gap pass completed;
- all 1,027 INFO records deterministically mapped to exactly one owning quest;
- no orphan, unresolved-parent, ownerless-QNAM, or multi-owner INFO records remain;
- Daggerfall and Nahd/apocryphal provenance separated;
- Ghost Choir 9 exact text and original publication metadata resolved;
- comprehensive gap audit and completeness report committed.

## Resume here — second-pass synthesis

Do not re-run broad ingestion unless the source hash changes.

### P1 — cross-Vicn direct-link reconciliation

Prioritize:

- Brain-Billies;
- Xero-Lyg;
- Radiance / Mnemo-Li / Blue Star;
- Adjacent Places / Lyg / Grabbers;
- Jhunal / Owl;
- GC9 / LYG;
- Romion / Rolls-On-Roads;
- Altano / Radiance.

For each node, distinguish:

1. same proper noun / rare vocabulary used independently by multiple Vicn plugins;
2. direct named relationship between characters/works;
3. external obscure-text vocabulary reused by multiple works;
4. thematic resemblance only.

### P2 — topic/claim promotion

Promote only evidence-backed shared claims into the parent Vicn/Lorekeeper layer. Preserve plugin-specific evidence pointers.

### P3 — targeted unresolved questions

Examples:

- Papyrus-only runtime details if scripts are later supplied;
- exact identity relationships that remain merely suggested;
- deeper cross-work reconciliation where the same rare term has different mechanics.

Do not flatten branch states, unreliable testimony, reused external sources, or one work's mechanics into another work's canon.
