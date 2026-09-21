# VIGILANT Act 4 quest orchestration

Continuity: `tes.mod.vigilant`

This page records quest-manager, FormList, VMAD-property, quest-fragment, alias, and marker evidence from `Vigilant.esm`. It deliberately does not invent the contents of external Papyrus `.pex` fragment bodies.

## Dedicated dream ordering

`FLST 0251D63F` / `zzzCHDreamQuestList` contains all thirteen numbered memory quests in exact order:

1. `0212C4F4` — *The Grand Inquisitor*
2. `0213712B` — *The Mad King*
3. `0213965A` — *Knight of Hounds*
4. `02140225` — *Johan the Fool*
5. `0205AE03` — *Adabal*
6. `0206A23B` — *Remains of the Miracle*
7. `0206F53C` — *Temptation of Marukh*
8. `02080E91` — *The Nameless Bard*
9. `022CAE30` — *Beyond the Shores of Madness*
10. `022A532E` — *Pelinal the Bloody*
11. `022B9BAB` — *After the Storm*
12. `022BC395` — *The Final Night*
13. `0251C038` — *Paravania the Man-Bull*

This is the strongest record-level evidence for the intended order of the memory sequence.

## Quest Manager

`QUST 0251EABC` / `zzzCHQuestManager` runs `zzzCHQuestManagerQuestScript` and has two object properties:

- `DreamList` → `zzzCHDreamQuestList`
- `Act4StarterList` → `zzzCHAct4QuestStarterList`

The ESM does not contain that script's compiled body, so list membership does not by itself tell us the exact runtime call made for every entry.

### Act 4 starter list

`FLST 0251EABB` contains 21 quests:

- `zzzCHSubQuest01` — *More Skooma*
- `zzzCHSubQuest02` — *Archer of Kyne*
- `zzzCHSubQuest03` — *The Black Worm*
- `zzzCHSubQuest04` — *Funeral*
- `zzzCHSubQuest05` — *Madness*
- `zzzCHSubQuest06` — *Pitier*
- `zzzCHSubQuest07` — *Knight of Julianos*
- `zzzCHSubQuest08` — *Knight of Zenithar*
- `zzzCHSubQuest09` — *Paladin Melus*
- `zzzCHSubQuest10` — *Knight of Arkay*
- `zzzCHSubQuest11` — *Kyne's Dragon*
- `zzzCHSubQuest12` — *Knight of Kynareth*
- `zzzCHSubQuest13` — *Broken Horns*
- `zzzCHSubQuest14` — *Bald Man-Ape*
- `zzzChSubQuest15` — *The Saint's Corpse*
- memory quest 01 — *The Grand Inquisitor*
- memory quest 03 — *Knight of Hounds*
- memory quest 10 — *Pelinal the Bloody*
- `zzzCHMQ01` — *Aetherius*
- `zzzCHBossQuestMentana` — *VS Menta-Na*
- `zzzCHBossQuestRitho` — *VS Ritho*

The broader starter list is therefore not equivalent to the memory list. It coordinates side quests, selected memory quests, the Aetherius main quest, and boss quests.

## Memory Guide

`QUST 0242E0B1` / **Memory Guide** contains stages 0, 10, 20, ... 120 plus completion stage 999. Every one of those stages has an attached quest-fragment entry in `QF_zzzCHMemoryGuide_0242E0B1`.

Its fragment script stores object properties `Dream01` through `Dream13`. `Dream01`–`Dream12` point directly to the matching numbered memory quests.

### Dream13 is special

`Dream13` does **not** point directly to `zzzCHMemoryQuest13`. It points to:

- `0251ADBF` / `zzzCHSubQuest13` — **Broken Horns**

Broken Horns then stores:

- `MemQ13` → `0251C038` / *Paravania the Man-Bull*
- `Sq11` → *Kyne's Dragon*
- `BqMorihaus` → *VS Morihaus*
- `AoMSq03` → *Legacy of Belharza*
- `qGenBLH` → Belharza generic-dialogue quest
- `gBelharzaRelease` → the Act 4 Belharza-release global
- multiple Belharza/Morihaus/dragon aliases and time-portal/shortcut/barrier references

`zzzCHMemoryQuest13` in turn stores `Sq13` → **Broken Horns**.

This two-way structural relationship establishes that the final Man-Bull memory is embedded in a larger Belharza/Morihaus side-quest handoff rather than being launched by the Memory Guide in exactly the same way as memories 1–12.

## Main Coldharbour quest link

`zzzCHMQ00` / *Coldharbour* has a VMAD property `QM` pointing directly to `zzzCHQuestManager`. It also references `zzzCHGreymarchQuest`, Act 4/current-act globals, area/travel aliases, Order markers, Menta-Na's boss quest, the Horn of Stendarr, and the Eye of Marukh.

This is direct implementation evidence that the Coldharbour main quest owns or invokes the Act 4 orchestration layer, though the exact Papyrus statements remain external.

## Aetherius branch markers

`zzzCHMQ01` / *Aetherius* has explicit aliases/properties for:

- `BadEndMarker` → `REFR 021369CA`, physically placed in `CELL 02136194` / `zzzCHAetheriusBad`
- `MolagWarpMarker` → `REFR 021369D5`, also in `zzzCHAetheriusBad`
- `GateBreakMarker` → `REFR 0213C06C`, in **Sancremor Angasel**
- `Anchor` → `REFR 02134E2A`, also in **Sancremor Angasel**
- `AfterEp4Marker` → `REFR 0213C070`, in **Mathmalatu Priory**
- `ReturnMarker` → `REFR 021369B8`, placed under a master-game cell (`00000D74`; name not recoverable from VIGILANT alone)

The separately named `CELL 021353E4` / `zzzCHAetheriusGood` contains:

- `CHMeq08EndMarkerRef`, the end marker associated with *The Nameless Bard*
- `CHGuideMolagBalRef`
- two Molag Bal statue/activator references

This is strong branch-location evidence, but not enough to state the exact karma/radiance/piety threshold selecting Good versus Bad Aetherius. The `Aetherius` quest does carry properties for `zzzCHKarma`, Pious, Radiance, current cycle, current act, and a dedicated bad-end scene.

## Papyrus limitation

The ESM records **which** quest stages have fragments, the fragment filenames, and the Papyrus object properties those scripts receive. The executable statements inside those fragments and `zzzCHQuestManagerQuestScript` reside in external compiled `.pex` files. Therefore:

- stage/fragment existence is structural fact;
- object-property references are structural fact;
- exact calls such as `Start()`, `SetStage()`, `Enable()`, or threshold comparisons cannot be asserted from the ESM unless independently encoded by conditions/records.

If the VIGILANT scripts/BSA are ingested later, this page can be upgraded into a full runtime transition graph.
