# UNSLAAD continuity

**Continuity ID:** tes.mod.vicn.unslaad  
**Parent continuity:** tes.mod.vicn  
**Primary source:** user-provided translated Unslaad.esm (UNSLAAD 3.0.6)  
**Source SHA-256:** 1dabd2782ad6f4af565ace37fbe198c497d18f7a9ae0d2f36d892d743454b05b  
**Source size:** 10,432,096 bytes

UNSLAAD is stored under the shared **Vicn continuity** with **VIGILANT**, **GLENMORIL**, and **DAc0da**. Source-level claims remain attributable to UNSLAAD unless another Vicn work independently supports them. Nothing in this layer is silently promoted into official Elder Scrolls canon.

## Direct ESM inventory

The deterministic parser pass found **44,103 records**, including:

- 833 INFO records with **1,015 embedded response strings**
- 661 DIAL records
- 52 QUST records
- 517 NPC_ records
- 50 BOOK records
- 98 MESG records
- 59 SCEN records
- 1,740 CELL records
- 7 WRLD records

The translated ESM is not localized, so its English dialogue and book text can be extracted directly without external string tables.

## Current coverage

### Numbered main quest

The lore-bearing dialogue/scene pass is complete for all ten numbered main quests, from **Falling Cat** through **Under the Elder Tree**.

### Side quests and shared dialogue

High-value side/generic material is now ingested, including:
- Fluffy's Secret
- Dragon Souls
- Arkved
- Snow Guardian
- Liturgy of I
- Watcher from the Third Era
- Boss Rush
- Sermon of Khev
- VS Dreugh King
- radiant/repeatable dialogue families

The shared **zzzCrbGeneric** audit resolved:
- **217 INFO rows**
- **120 DIAL topics**
- **28 named speaker labels**

using GetIsID speaker conditions.

### Epilogue

The Epilogue quest's **106 INFO responses** have been analyzed for Ulliss/Lizz, Lizz/Fluffy-Ja'cobee, and Lizz/Aisha relationship evidence.

### Scene reconciliation

All **59 SCEN records** are accounted for:
- **53** contain DIAL-backed dialogue actions, all mapped to already-ingested dialogue families;
- **6** contain no DIAL actions and are retained as technical/orchestration scenes.

There is therefore no hidden SCEN dialogue backlog in this ESM version.

### Books

The source corpus preserves **50 / 50 BOOK records** as individual FormID-keyed files under books/source/.

This includes:
- all seven Loveletter fragments;
- the full Loveletter From the Fifth Era;
- Sermon 37;
- Sermon 0;
- Vivec and Molag Bal;
- Ysmir the Forefather, Volume IV;
- Harakk Warrior's Final Note;
- Note from Fluffy;
- all gameplay/spell/summon books.

Reused/apocryphal texts remain provenance-distinct from UNSLAAD-authored material.

### Messages, item text, and structural lore

All **98 MESG records** are now classified:
- 33 dedicated Insight messages;
- 65 non-Insight messages, with lore-bearing research/inspection clusters promoted separately.

Embedded item-description coverage is also audited:
- 5 ARMO DESC records;
- 55 WEAP DESC records.

The strongest new item lore is the post-Mq07 Gray-Owl craft trio:
- **Gray OWL** — "second CHICK," Atmoran mage, sought the "dragon";
- **Gray EGG** — crushed by a Chick Trader of Anequina, "future" lost;
- **Shadow of the Gray OWL** — Saarthal secret / higher planes.

### Placed-reference and VMAD coverage

A first placed-reference pass now maps major lore objects into cells/worldspaces, including Dragon's Cradle, Dragon's Peak, Old City of Chains, Frozen Tomb, Ysgrim's Seal, World-Eater's-Waking, End of Radiance, and Oracle Iridescent's Workshop.

A first VMAD metadata pass confirms direct implementation links including:
- Lyg door + ice-mirror markers in The Final Journey;
- Mural/Cradle/Owl/soul-fire wiring in The Owl Flies at Dusk;
- Loveletter quest state wired to the frozen-time access gate;
- GC9 object wired to its LYG memory-erasure message.

### Artifact ownership / death-loot / factions

A first deterministic ownership graph now covers named NPC/container inventories, custom death-item lists, reward-container provenance, craftable forms, enchantment links, and custom race/faction membership.

Promoted dossiers include Austella's Hoarfrost equipment, Jhunal/Gray-Owl equipment, Khev/Molag/Muatra/Coldfire, Atmoran trial relics, Dov-Ah-Kiin relics, KINMUNE/Ayrenn/Oracle-Iridescent staging, Owl/Lyg-Crab/World-Eater/Blades/Companion/core factions, Sinak/Woodland-Man/Owl relationships, and Jill trial/cross-VICN material.

### Named forms / race taxonomy

The lore-facing actor layer is now indexed structurally:
- **243 named NPC forms** out of 517 NPC_ records;
- **174 unique display names**;
- **41 duplicate-name/form families**;
- **57 custom races used by named actors**.

Named forms are split across four alphabetic indexes, with a separate duplicate-family summary and custom-race catalog. Unnamed/template/leveled NPC records are retained as implementation forms rather than promoted as characters.

This provides canonical form-state lookup for cases such as Ulliss, Aisha, Jhunal the Gray, Khev, Sinak summons, Jills, Dragon Pus forms, and training proxies.

### Summons, magic, recipes, and identity-state coverage

The structural combat/magic layer now includes:

- complete deterministic **32-book summon-chain** mapping: BOOK -> SPEL -> MGEF -> summoned NPC;
- hostile/natural versus summoned-form differentiation for Sinak, Draco-Nord, Hor/Dreugh, Watcher, Hoarfrost, Atmoran beasts, and Rackety-Nix;
- selected artifact ENCH/MGEF mapping, including Dragon-Soul-scaled Dragonslayer gear;
- custom weapon-art mapping for Bormahu/Jill/World-Eater staves, Woodland-Man weapons, and Yngol;
- custom SHOU/Voice ownership for Ulliss dragons, Ysgrim/Ysgramor, Dregs of Alduin, Manque, Rackety-Nix, Eamal, and Pelinaalilargus;
- recipe-condition mapping for major post-encounter artifact reconstructions;
- mask/outfit identity mapping, including Gray Owl's Mask on multiple Jhunal-the-Gray forms and the Void-Jill set on Elja;
- a reusable multi-form identity graph for Ulliss, Aisha, Jhunal/Gray Owl, Elja/Jills, Ysgrim/Ysgramor, Khev, and Ja'cobee/Fluffy.

### Relic and placement coverage

Additional named-relic dossiers now cover:
- GHARTOK weapons;
- Wolf King / Earthbones;
- Hor Ritual;
- Khemkel's Carving Knife;
- Spear of the Fox;
- Saarthal's Sorrow;
- Elder Wood equipment;
- Princess Ayrenn equipment;
- Dragon Fangs;
- Dragonbone Smashers;
- Ysgramor's Fork;
- Jill equipment;
- Hermit's Tower Vivec/Muatra source cluster.

### No-dialogue boss/trial quests

Named boss/trial families have a structural index even when they contain no ordinary INFO dialogue, including Trial of the Gods, Idol of Magnar, Last Giant of Jhunal, Jill trials, Ysgramor trial, Priest of Jhunal, and Woodland Man hunt.

## Major established VICN links

- **Ja'cobee / Ulliss / Aisha / EGG:** direct named and conceptual overlap with GLENMORIL; UNSLAAD now independently contains Ja'cobee/EGG statements.
- **Jhunal / Owls / Saarthal / Night of Tears / Magnus-fire:** independently recurring in UNSLAAD, VIGILANT, and GLENMORIL.
- **Jhunal / Laza / dragon experimentation:** UNSLAAD Gray Owl names Laza among failed experiments; VIGILANT Jhunal independently links Laza to dragon harvesting.
- **Arkved / Oneiromancer:** direct explicit link in both UNSLAAD and GLENMORIL.
- **Orlando / Blue Star / Owl / Elder Wood:** direct Orlando recurrence plus Owl/Atmora material.
- **Mnemo-Li / Blue Orphan / dream without a dreamer:** distinctive vocabulary shared with GLENMORIL.
- **Loveletter / Nu-Mantia:** reused apocryphal substrate actively interpreted by UNSLAAD through Liturgy of I and Khev.
- **Hjalti / Alcaire:** multiple internally consistent UNSLAAD references, retained as a comparison thread rather than a forced Talos identity.
- **Chick Trader / Anequina / Gray Owl:** UNSLAAD Gray EGG directly names a Chick Trader of Anequina; GLENMORIL independently traces original Chick Traders to the prince of Anequina and royal guards. "Second CHICK" identity remains unresolved.
- **GC9 / LYG:** UNSLAAD's implementation-tagged GC9 message describes LYG-sector memory evaporation/timeline disposal; DAc0da independently has Ghost Choir 9, LYG mass-erasure, and a memory project.
- **Radiance / Mnemo-Li:** UNSLAAD and DAc0da independently connect Radiance/Mnemo-Li to unstable memory, identity, paths, or world reconstruction, while preserving conflicting definitions.

## Provenance policy

- Quest structure, aliases, GetIsID/GetIsAliasRef conditions, scene bindings, record placements, and exact actor forms are implementation evidence.
- Character explanations remain attributed testimony unless separately corroborated.
- Reused official/apocryphal texts are not attributed to Vicn merely because copies exist in Unslaad.esm.
- Colored Owl/Jhunal/Orlando forms remain densely linked but are not globally merged into one body/person.
- Translation wording is preserved when terminology is uncertain.
- Contradictory or unstable identity evidence is retained rather than normalized away.

## Second-pass synthesis additions

New parent-level synthesis now includes:
- **Jhunal identity matrix** — separates original/deific Jhunal, Gray/Black/White Owl mappings, VIGILANT Jhunal the Owl, Orlando incarnation claims, and body/state uncertainty.
- **Atmora / Saarthal / Night of Tears** — reconciles repeated named history across all four VICN works while preserving DAc0da's contradictory Atmoran testimony and the distinct Magnus/Owl layers.

These should be used before attempting new local identity merges.

## Ingestion completion status

**Status: complete for the supplied translated UNSLAAD 3.0.6 ESM.**

The current Lorekeeper corpus now accounts for:
- all numbered main-quest dialogue families;
- high-value side, generic, radiant, boss, and epilogue dialogue;
- all 59 SCEN records at the dialogue/orchestration classification layer;
- all 50 BOOK records with source/provenance handling;
- all 98 MESG records;
- all direct ARMO/WEAP description records;
- named NPC/form families and custom races;
- major factions, inventories, death items, recipes, enchantments, Shouts, summon chains, masks/outfits, and multi-form identities;
- high-value placements and VMAD property linkages;
- cross-VICN synthesis for the strongest recurring identities, places, institutions, and source traditions;
- explicit reliability and contradiction handling for unstable testimony.

Remaining unknowns are **documented evidence boundaries**, not an active ingestion backlog. Examples include unsigned Owl Study authorship, the exact referent of Austella's "that person," visual iconography not exposed by the indexed data, and metaphysical questions the ESM itself leaves ambiguous.

Future work is optional and question-driven:
1. ingest a newer UNSLAAD version if supplied;
2. inspect original Japanese wording when a translation nuance matters;
3. inspect Papyrus/model/texture assets only for a specific unresolved question;
4. add newly discovered external provenance if a concrete earlier source appears.

For routine retrieval, start with `indexes/retrieval-map.md` and `analysis/source-reliability-matrix.md`.