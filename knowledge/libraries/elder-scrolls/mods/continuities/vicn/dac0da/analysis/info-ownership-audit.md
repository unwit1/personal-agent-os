# DAc0da INFO ownership audit

**Continuity:** `tes.mod.vicn.dac0da`  
**Source:** `DAc0da.esm`  
**INFO records:** **1,027**

A deterministic parser traced every INFO record through its containing type-7 DIAL group and then through the parent DIAL's `QNAM` field.

## Result

- INFO records parsed: **1,027**
- INFO records without a DIAL parent: **0**
- INFO records whose DIAL parent could not be resolved: **0**
- INFO records whose DIAL has no QNAM quest owner: **0**
- INFO records whose DIAL has multiple QNAM quest owners: **0**

Therefore:

> **Every DAc0da INFO record has exactly one deterministically resolved owning quest.**

There is no hidden pool of orphan dialogue outside the quest structure.

## INFO count by owning quest

| Local QUST | Quest | INFO count |
|---|---|---:|
| `00B21B` | Numidium Tertius | 239 |
| `0052C2` | Echoes of Mnemolichite | 171 |
| `004B1C` | Drowned Nighthawk | 157 |
| `00491D` | Generic Dialogue | 69 |
| `00AA0C` | The Call of Landfall | 50 |
| `00525E` | Abnur Tharn | 37 |
| `004475` | The Sea of Causality | 35 |
| `004981` | Patchwork | 26 |
| `00CA1E` | Censored Fate | 26 |
| `0050DC` | The End of All Wishes | 24 |
| `000D9F` | Citizen Dialogue | 18 |
| `00CDD9` | Cheese Party | 18 |
| `00C9F1` | Rella Mozzarella | 17 |
| `00B420` | Scene of Ghost Choir | 16 |
| `00CEA7` | Epi Samon Gen | 16 |
| `004931` | Negative Legacy | 15 |
| `006134` | The Sea of Radiance | 15 |
| `00B3A8` | VS GC9 | 14 |
| `00CE40` | Sload Radio | 12 |
| `0047F5` | Dialogue Augur | 11 |
| `00B5EE` | VS Zurin Arctus | 10 |
| `00CEE1` | Epi Abnur | 8 |
| `005FBE` | Group Battle: The Revenant | 7 |
| `00CE94` | Epilogue Samon | 7 |
| `00CA5B` | Pan-Argonia | 4 |
| `0047E5` | Augur of the Obscure | 3 |
| `005303` | Option: Dreugh | 2 |

Quests absent from this table have no owned INFO dialogue.

## Coverage consequence

All dialogue-bearing owners above now fall into one of these completed first-pass categories:

- numbered main-quest reconstruction;
- major side-quest reconstruction;
- epilogue pass;
- boss/scene pass;
- Augur pass;
- Sload Radio / Cheese / alternate ending pass;
- Generic Dialogue pass;
- Citizen Dialogue pass.

This means future DAc0da dialogue work should be **targeted refinement**, not another broad scan for missing quest dialogue.

## Remaining caution

This audit proves structural ownership, not perfect semantic extraction.

A future verification pass may still find:

- a conditional branch whose significance deserves its own dossier;
- a speaker-condition edge case;
- a short combat line that strengthens an existing concept.

But there is no unowned dialogue corpus left to discover.
