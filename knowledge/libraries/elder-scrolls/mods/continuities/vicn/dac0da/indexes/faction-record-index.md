# DAc0da custom faction record index

**Continuity:** `tes.mod.vicn.dac0da`  
**Source:** `DAc0da.esm`

DAc0da contains **24 custom FACT records**.

Most are implementation factions for hostility, vendors, search lights, or generic dialogue. A smaller subset carries meaningful narrative affiliation.

## Narrative affiliation factions

| Source | Editor ID | Display name | Narrative use |
|---|---|---|---|
| `000D63` | `zDcdFactionPsijic` | Psijic Faction | Rolls-On-Roads / Psijic-aligned actors |
| `000D64` | `zDcdFactionBlackworm` | Blackworm Faction | Mannimarco/Worm-aligned forces |
| `00304B` | `zDcdFactionAtmoran` | Atmoran Faction | Atmoran encounter actors |
| `0044B0` | `zDcdFactionSnowElf` | Snow Elf Faction | Snow-Elf / Wintercaller encounter actors |
| `006B6A` | `zDcdFactionNumidium` | Numidium Faction | Numidium machine-world actor alignment |
| `006B6B` | `zDcdFactionApo` | Apocrypha Faction | Apocryphal forms inside Numidium |

These records give direct implementation support for affiliations that were previously inferred from names/quests.

### Psijic Faction

The custom Psijic faction complements direct dialogue establishing Rolls-On-Roads as a Psijic Order operative.

Do not treat the custom faction as the complete official Elder Scrolls Psijic institution; it is DAc0da's actor-affiliation implementation.

### Blackworm Faction

The presence of `zDcdFactionBlackworm` strengthens the interpretation that DAc0da's recurring Worm Spellsword/Knight/Assassin/Berserker/Anchorite actors represent a coherent Black-Worm-aligned force rather than only similarly named independent enemies.

### Atmoran and Snow Elf factions

DAc0da mechanically distinguishes Atmoran and Snow-Elf actors into separate custom factions.

This supports the existence of opposing encounter forces in **Drowned Nighthawk**, but does not resolve the quest's deliberately contradictory history about who caused the wider conflict.

### Numidium and Apocrypha factions

Separate `Numidium` and `Apocrypha` factions support MQ04's implementation of Apocryphal intruders/contamination as a distinguishable actor group inside the Numidium environment.

They should be treated as combat/AI affiliation structures rather than proof that “Numidium Faction” is an in-world named political organization.

## Relationship / branch-control factions

| Source | Editor ID | Display name |
|---|---|---|
| `003133` | `zDcdFactionPlayerAlly` | Ally Faction |
| `0044A7` | `zDcdFactionPlayerFriend` | Friend Faction |
| `0044A8` | `zDcdFactionPlayerEnemy` | Enemy Faction |
| `0044A9` | `zDcdFactionCurrentFollow` | Follower Faction |
| `0044B1` | `zDcdFactionPeace` | Peace Faction |
| `0056FB` | `zDcdFactionWS2_Ally` | BF Ally |
| `0056FC` | `zDcdFactionWS2_Enemy` | BF Eneymy |

These are state/AI-control helpers and should not be interpreted as independent organizations.

## Dialogue / social helper factions

- `000D65` — `zDcdFactionDrifter` — Drifter Faction
- `000D66` — `zDcdFactionSolitudeCitizen` — Solitude Citizen Dialogue Faction
- `00491C` — `zDcdFactionGenDailogue` — None
- `0047F6` — `zDcdFactionAugur` — Augur Faction

These primarily route dialogue or actor behavior.

## Vendor factions

- `00491B` — `zDcdFactionVendorKani` — Kani Vendor Faction
- `004801` — `zDcdFactionVendorAugur` — Augur Vendor Faction
- `005348` — `zDcdFactionVendorDreugh` — Dreugh Vendor Faction
- `00CE79` — `zDcdFactionVendorPsijic` — Psijic Vendor Faction
- `00D02C` — `zDcdFactionVendorKanra` — Kanra Vendor Faction

The Kanra vendor faction provides additional structural support that **Mecha-Kanra** is a persistent vendor/NPC rather than only a dialogue easter egg.

## Search-light technical factions

- `0086E4` — `zDcdFactionSearchLightFriend` — Ignore Search Light Trap
- `0086E5` — `zDcdFactionSearchLighHide` — Hiding from Search Light

These are trap/stealth implementation records.

## Interpretation rule

A custom FACT record is strong evidence that DAc0da mechanically groups actors.

It is **not automatically evidence that the faction's EditorID is an in-world self-name**.

Promote a faction into an organization dossier only when dialogue, books, quests, or repeated titles independently support an institution—as with the Psijic Order or Black-Worm forces.
