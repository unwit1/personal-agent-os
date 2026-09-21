# DAc0da faction record index

**Continuity:** `tes.mod.vicn.dac0da`  
**Source:** `DAc0da.esm`

DAc0da defines **24 FACT records**. Most are implementation/control factions; only a subset represent lore-relevant groups.

## Lore-relevant faction records

| Source | Editor ID | Display name |
|---|---|---|
| `000D64` | `zDcdFactionBlackworm` | **Blackworm Faction** |
| `000D63` | `zDcdFactionPsijic` | **Psijic Faction** |
| `00304B` | `zDcdFactionAtmoran` | **Atmoran Faction** |
| `0044B0` | `zDcdFactionSnowElf` | **Snow Elf Faction** |
| `006B6B` | `zDcdFactionApo` | **Apocrypha Faction** |
| `006B6A` | `zDcdFactionNumidium` | **Numidium Faction** |

These confirm that DAc0da mechanically groups actors under the same broad alignments used in the dialogue/quest layer.

## Character/vendor/dialogue factions

- `0047F6` — Augur Faction
- `004801` — Augur Vendor Faction
- `005348` — Dreugh Vendor Faction
- `00CE79` — Psijic Vendor Faction
- `00491B` — Kani Vendor Faction
- `00D02C` — Kanra Vendor Faction
- `00491C` — Generic Dialogue faction

These are primarily interaction scaffolding and should not be promoted into new organizations.

## Relationship/control factions

DAc0da also defines generic:

- Ally
- Friend
- Enemy
- Peace
- Follower
- battle ally/enemy
- Search-Light friend/hide
- Solitude citizen
- Drifter

These are implementation-state records rather than lore organizations.

## Evidence rule

Use FACT records to confirm:

- actors are mechanically grouped;
- certain encounter families share hostility/friendship rules;
- a broad organization exists in implementation.

Do not infer ideology, leadership, or history from the faction name alone.
