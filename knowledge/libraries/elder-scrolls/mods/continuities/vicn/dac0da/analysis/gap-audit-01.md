# DAc0da gap audit 01

**Continuity:** `tes.mod.vicn.dac0da`  
**Source:** `DAc0da.esm`  
**Source SHA-256:** `455f07f3bba5de5b1b5a84c882be3309a66fd3d503866e05658b99896dfdb00e`

This audit asks a narrower question than “has every record been copied into a file?”:

> **Does each lore-bearing record class have enough deterministic coverage that future work can target real gaps instead of re-reading already-normalized material?**

## QUST — 43 records

### Covered at narrative or structural depth

- all 6 numbered main quests;
- all major side quests;
- Worm/Mnemolichite subquests;
- Ghost Choir scene quest;
- Cheese/Argonian alternate endings;
- Cheese Party;
- Sload Radio;
- In Grabbers' Hands;
- all four epilogues;
- Golden Dragon Flight;
- Agent Event;
- Augur generic dialogue;
- Generic Dialogue;
- all five Numidium boss quests at structural/boss-index level.

### Manager/support quests that are intentionally low-lore

- `zDcdQManagerNumidium`
- `zDcdQInit`
- `zDcdSafetyQuest`
- `zDcdJsonManager`
- `zDcdQManagerPortalGun`
- `zDcdQManagerSkyshard`
- `zDcdSqNumShotcut`

`Numidium Shortcut` contains script properties such as `ShortCut01`–`06` and lift portals; it is route infrastructure, not a missing story quest.

### Remaining QUST gap

No major unprocessed narrative quest is currently apparent.

## DIAL / INFO

### Covered

- all numbered-main-quest dialogue;
- major side quests;
- Worm arc;
- epilogues;
- scene-bound INFO speaker resolution;
- Augur generic dialogue;
- `zDcdGen` Generic Dialogue unique-speaker pass.

### Newly resolved generic-dialogue actors

- **Crabbimarco**
- **Mecha-Kanra**

Voice-type-only barks are now treated as culture/faction evidence rather than unique-speaker biography.

### Deterministic orphan-dialogue audit — complete

A raw-group linkage audit now establishes:

- **737 / 737 DIAL** records contain a direct `QNAM` quest owner;
- **1,027 / 1,027 INFO** records are contained under a valid DIAL group;
- **0** DIAL records lack QNAM ownership;
- **0** INFO records are orphaned from the DIAL group structure;
- **0** text-bearing no-QNAM DIAL blocks exist.

Therefore there is no hidden unowned dialogue corpus remaining in the ESM.

Any future dialogue work is refinement of already-owned quest/generic/scene material rather than discovery of an orphan conversation block.

## SCEN — 79 records

### Covered

- **79 / 79** owning quests resolved.
- **73** dialogue-bearing scenes mapped to aliases/speakers.
- **6** non-dialogue choreography/control scenes separated.
- complete `indexes/scene-speaker-index.md`.

### Remaining SCEN gap

Only line-by-line comparison for scene dialogue that may add minor details to existing dossiers. No scene is currently ownerless.

## BOOK — 90 records

### Covered

- full 90-record inventory;
- 66 low-prose spell/summon/item books separated;
- 13 letters/notes indexed;
- 11 Nahd-fiction/apocryphal records indexed;
- Daggerfall Totem-letter reuse verified;
- major Michael Kirkbride/community-apocrypha provenance separated;
- DAc0da-specific letters normalized;
- Temporal Tomes normalized.

### Remaining BOOK gap

No major first-pass provenance gap remains.

The long **Ghost Choir 9** BOOK is now verified as Michael Kirkbride unofficial/developer text originally posted to **The Elder Scrolls Forums** on **2012-02-18**.

Lower-priority future work:

- exact source comparison for the two Snow-Elf letters if an external precursor is suspected;
- item-level indexing of all 66 spell/summon BOOKs where they expose a unique creature/object name.

## MESG — 66 records

### Covered

- full message-insight pass;
- environmental activator mapping;
- Kagrenac records;
- Dumac ZERO SUM N0 route;
- Hist/Jill Milk Tree diagnostic;
- Atmoran/Jhunal/Owl material;
- Pan-Argonia bad-ending summary;
- Mnemolichite / Mnemolic Sign / blueshift system;
- ordinary UI-only messages identified as mechanics.

### Remaining MESG gap

No major high-value unprocessed message group is currently apparent.

## NPC_ — 554 records

### Covered at high-value depth

Dedicated dossiers/indexes now cover:

- Rolls-On-Roads
- Samon
- Yngol
- Hgelhelm
- Haalj
- Sindwen
- Beynhaal
- Vanus
- Yu'qbar
- Athanasius
- Augur
- Abnur
- N'Danda
- Crabbimarco
- Mecha-Kanra
- Yaghra Agent forms
- Ghost Choir 9
- major Numidium bosses
- ordinary/boss/ghost/summon/memospore/alternate form families
- creature/encounter families.

### Named-NPC completeness — complete

A deterministic named-NPC ledger now classifies all **146 unique display names** found among the 554 NPC_ records:

- 36 major/story identities;
- 32 named forms/subbosses/summons/special encounters;
- 78 generic encounter/cultural/leveled roles;
- **0 unclassified high-value names**.

See `indexes/named-npc-coverage.md`.

Low-priority leveled/corpse/treasure/summon duplicates intentionally remain represented by family indexes rather than individual biographies.

## RACE — custom races

### Covered

- custom morphology index created;
- major Yaghra/Sload/Dwemer/Goldborn/Apocryphal/flesh/Atmoran transformations separated;
- Weredrake / Mecha-Kanra / Crabbimarco custom race states indexed.

### Remaining RACE gap

Only morphology-to-lore joins where dialogue/books explain a race's origin.

## FACT — 24 records

### Covered

- all custom factions inventoried;
- lore-relevant Blackworm/Psijic/Atmoran/Snow-Elf/Apocrypha/Numidium factions separated from implementation scaffolding.

### Remaining FACT gap

Only membership joins for important named actors where faction membership materially changes interpretation.

## WRLD / CELL / locations

### Covered

- all five WRLD records identified;
- custom worlds:
  - Sea of Causality
  - Dwemereth
  - Mozarella Spacetime
- major named CELL clusters indexed;
- important interior Numidium cells indexed;
- direct actor-to-cell anchors added.

### Remaining location gap

Potential future refinement:

- exact route ordering through the Sea of Causality;
- LCTN record joins for every cell cluster;
- maps of parent/child transitions and doors.

This is navigation enrichment, not a major lore hole.

## ACTI / environmental insights

### Covered

- high-value lore activators mapped to MESG and placed cells;
- Y.E.L.E.M. dream circuits;
- Kagrenac records;
- Dumac ZERO SUM route;
- Hist/Jill and Atmoran insights.

### Remaining ACTI gap

Audit non-message activators only if they have custom scripts or names suggesting unindexed lore.

## Artifacts/items

### Covered

- Book of the Prisoner / nymic object
- seven Numidium/Cheese Totems
- Ahzidal bracelet
- Yngol Forgehammer
- Varen's shield
- Underking/Zurin weapons
- Dumac gear
- Kagrenac equipment
- Tsaesci dragon-hunting weapons
- Snow-Drake/Auri-El halberds
- Tsa-the-Dozing-Rat idols

### Remaining artifact gap

Prioritize only items that:

- are unique quest rewards;
- occur in named actor inventories;
- encode repeated identity symbols;
- have scripts or descriptions with actual lore.

## Cross-Vicn coverage

Strong direct or rare-vocabulary bridges currently include:

- Rolls-On-Roads <-> Romion / GLENMORIL
- Altano / VIGILANT
- Adjacent Place + Grabbers / UNSLAAD
- Mnemo-Li across DAc0da/GLENMORIL/UNSLAAD
- Blue Star / Radiance
- Hist-Jillian / Wheelian rip
- Jhunal / Owl
- Brain-Billies / GLENMORIL
- Xero-Lyg / GLENMORIL
- GC9 / LYG
- Atmora/Saarthal comparison network

## First-pass closure

The previously identified P1/P2/P3 gaps are now closed:

- named-NPC coverage ledger: complete;
- orphan INFO/DIAL audit: complete;
- Ghost Choir 9 original-source provenance: resolved.

## Current assessment

> **DAc0da first-pass ESM lore ingestion is COMPLETE for the source hash above.**

No significant lore-bearing record class remains broadly unprocessed.

Remaining work is optional refinement or second-pass synthesis:

- Papyrus-only runtime internals if loose scripts/PEX become available;
- exhaustive door/navigation graphing;
- item-by-item treatment of low-prose spell/summon BOOK records;
- external precursor checks for DAc0da-specific letters if a concrete source candidate appears;
- cross-Vicn reconciliation and promotion into shared Lorekeeper claim/entity structures.

Future continuation should **not** restart broad DAc0da ingestion unless the source hash/version changes.
