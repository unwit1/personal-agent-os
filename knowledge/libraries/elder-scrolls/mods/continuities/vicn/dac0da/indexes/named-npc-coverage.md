# DAc0da named NPC coverage ledger

**Continuity:** `tes.mod.vicn.dac0da`  
**Source:** `DAc0da.esm`  
**Source SHA-256:** `455f07f3bba5de5b1b5a84c882be3309a66fd3d503866e05658b99896dfdb00e`

## Deterministic counts

The plugin contains:

- **554 NPC_ records**
- **274 NPC_ records with a FULL/display name**
- **146 unique display names**

This ledger classifies all 146 unique display names by the level of lore treatment they require.

It is a coverage ledger, not a claim that every display name denotes a unique historical person.

## Coverage result

| Class | Unique display names | Coverage rule |
|---|---:|---|
| Major/story identities | **36** | dedicated dossier, quest analysis, boss dossier, epilogue, or explicit identity/form-family treatment |
| Named forms / subbosses / summons / special encounters | **32** | covered by quest, named-encounter, creature-family, form-family, or scene analysis |
| Generic encounter / cultural / leveled roles | **78** | covered at encounter-family/faction/race level; no individual biography warranted |
| Unclassified high-value names | **0** | none remain after this pass |
| **Total** | **146** | all unique FULL names classified |

## A — major / story identities — 36

These names participate directly in plot, cosmology, dialogue, epilogues, or identity-state mechanics and already have dedicated or equivalent high-value coverage:

- Akashiya-Samon
- Arcanist
- Augur of the Obscure
- Beynhaal
- Crabbimarco
- Dumac's Tonalframe
- GC9
- Ghost Choir 9
- Girl
- Haalj Hgelhelmson
- Haalj the Half-Drake
- Hgelhelm the Outcast
- Load Error
- Malmanius the Child of Radiance
- Mannimarco the God of Worms
- Mecha-Kanra
- Messenger of House Tharn
- Mysterious Battlemage
- N'Danda
- Nchunak the Evangelist
- Necromancer's Moon
- O.Y.A.R.S.A
- Rolls-On-Roads
- Sindwen the Wintercaller
- Templar of Hahd Yu'qbar
- The Agent
- The Underking
- Tsuunalinfaxtir
- Vanus Galerion
- Vigilant Athanasius
- Yaghra Bioborg - The Agent
- Yaghra Chimera - The Agent
- Yngol
- Yngol the Tsunaltir
- Zombified N'Danda
- Zurin Arctus

### Identity notes

Several of these names are intentionally **not** independent persons:

- **Load Error** is the alternate/censored Rolls-On-Roads form.
- **Mysterious Battlemage** is the hidden displayed identity used by Abnur Tharn forms.
- **GC9 / Ghost Choir 9** are related implementation/instance names.
- **Yaghra Agent** forms are DAc0da Agent manifestations, not automatically one unchanged body.
- **Dumac's Tonalframe** is explicitly a Tonalframe rather than a simple historical-body label.
- **Haalj the Half-Drake** is a transformed Haalj form.

See `indexes/character-form-families.md`.

## B — named forms / subbosses / summons / special encounters — 32

These are individually named, but current evidence supports indexing them as a special form or encounter rather than inflating each into an unsupported biography:

- **???** — unnamed golden dragon from Golden Dragon Flight
- Ab'voon the Egg Keeper
- Anares the Daughter of Khev
- Archangel of Xrib
- Bar'zay the Wizard
- Blue Dugal
- Bo'nan the Yaghra Champion
- Bolor Savel the Worm Anchorite
- Camilla Lollia the Worm Anchorite
- Crab Spirit
- Essence of Necromancy
- Eye of Orgnum
- Frayed Fate
- GC9 Instance
- Ha'seg the Wise
- Hare's Servant
- Hgelhelmson of the Lineage of Fal
- Khemkel's Wooden Idol
- Lokir
- Lokir of These Parts
- Mercator Hosidus the Worm Anchorite
- Mnemic Warder
- Nchunak the Second
- Revenant
- Spirit of Ilni
- Spirit of Myn
- Storm Left Fist
- Storm Right Fist
- Thundernach Lord
- U'tulka
- Worm's Midwife
- Yaghra Chimera Prototype

### Already resolved special cases

**Lokir / Lokir of These Parts:** MQ00 now establishes that Rolls-On-Roads summoned a Daedra and ordered it to assume a form familiar to the player. The Lokir appearance is therefore a memory/perception-selected disguise rather than evidence for Lokir's bodily survival. Evidence: `DAc0da.esm:00AA56`, `00AA58`.

**Crab Spirit:** MQ02's memospore scene resolves the Crab Spirit as the speaker who addresses a **Vestige** and begins giving Molag-Bal advice before the Augur interrupts it as the wrong memory intended for an old friend. This is already preserved in `analysis/mq02-negative-legacy.md`.

**Nchunak the Second:** preserved as a distinct actor/summon from **Nchunak the Evangelist** in `indexes/numidium-bosses.md` and encounter-family coverage.

**Named Yaghra / Worm Anchorites:** preserved in `indexes/creature-encounter-families.md` and the Black-Worm organization coverage.

**Archangel of Xrib / Eye of Orgnum / Blue Dugal / Hare's Servant / Khemkel's Wooden Idol / U'tulka / Mnemic Warder:** preserved in `indexes/named-encounter-actors.md`.

**Spirit of Ilni / Spirit of Myn / Storm fists / Thundernach Lord / Essence of Necromancy / Revenant:** current evidence is summon/combat-state evidence; no unprocessed dialogue biography is implied by the name alone.

## C — generic encounter / cultural / leveled roles — 78

These names are deliberately handled at species, faction, race, encounter-family, or generic-dialogue level:

- Angel of Xrib
- Apocryphal Hound
- Apocryphal Hunter
- Atmoran
- Atmoran Archer
- Atmoran Bear
- Atmoran Clever-Man
- Atmoran Warrior
- Citizen
- Draco-Nord
- Dunmer
- Dwarven Architon
- Dwarven Warrior
- Dwarven Worker
- Dwemer Specter
- Fire Orb
- Flesh Husk
- Flesh Stalker
- Frost Atronach
- Frost Spriggan
- Glowing Hushed One
- Glowing Hushed Reaver
- Goldborn
- Goldborn Colossus
- Goldborn Crawler
- Goldborn Guardian
- Goldborn Skirmisher
- Goldborn Storm
- Goldborn Wheeler
- Half-Drake
- Horker
- Ice Serpent
- Ice Wraith
- Imperial Archer
- Imperial General
- Imperial Mage
- Imperial Soldier
- Jill
- Khajiit
- Nord Warrior
- Pseudo Dragon
- Redguard
- Sea Flesh Atronach
- Sea Flesh Husk
- Sea Sload
- Sea Sload Psychomancer
- Sload Druglord
- Sload Floater
- Sload Necromancer
- Sload Zombie
- Snow Fox
- Solitude Guard
- Solitude Navy Archer
- Solitude Navy Commander
- Solitude Navy Soldier
- Templar of Hahd
- Thalmor Agent
- Thalmor Archer
- Thalmor Justiciar
- Thalmor Soldier
- White Stag
- Wintercaller Mage
- Wintercaller Soldier
- Wood Wraith
- Woodland Man-Thing
- Worm Assassin
- Worm Berserker
- Worm Cultist
- Worm Knight
- Worm Spellsword
- Worm's Sacrifice
- Yaghra
- Yaghra Larva
- Yaghra Matron
- Yaghra Shaman
- Yaghra Sitter
- Yaghra Strider
- Yaghra Warrior

These are covered through:

- `indexes/creature-encounter-families.md`
- `indexes/custom-race-morphology-index.md`
- `indexes/faction-record-index.md`
- `analysis/generic-dialogue-pass-01.md`
- relevant quest/location files

Voice-type combat barks are treated as cultural/faction evidence and are not silently assigned to one named individual.

## Named-NPC completeness conclusion

At the level of **unique displayed NPC names**, no high-value unclassified actor remains after this pass.

This does **not** mean every one of 554 NPC_ records should receive a standalone markdown page. Most of the remaining raw records are:

- leveled variants;
- treasure/corpse forms;
- summon copies;
- auto-delete combat forms;
- alternate equipment/combat templates;
- duplicated actor states already represented through a form family.

The correct next step is therefore **not** to generate 554 biographies.

Future NPC work should be evidence-triggered: create or expand a dossier only when a raw actor form adds dialogue, unique scripts, meaningful faction membership, a distinct transformation, or cross-Vicn identity evidence.
