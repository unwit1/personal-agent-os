# DAc0da BOOK catalog

**Continuity:** `tes.mod.vicn.dac0da`  
**Source:** `DAc0da.esm`

The plugin contains **90 BOOK records**:

- **66** spell/conjuration/item manuals with only short casting/item text;
- **13** letter/note records;
- **11** `zDcdNahdFiction_*` narrative/apocryphal texts.

Presence inside DAc0da does **not** prove DAc0da/Vicn authored the prose. Each narrative book must retain source/provenance status.

## DAc0da-specific / quest-integrated letters and notes

| Source | Editor ID | Title | Current provenance |
|---|---|---|---|
| `DAc0da.esm:0049F6` | `zDcdLetterSnowElf01` | Orders to Wintercaller Unit | DAc0da quest-integrated original/adapter; source comparison pending |
| `DAc0da.esm:0049F7` | `zDcdLetterSnowElf02` | Search Request Denied | DAc0da quest-integrated original/adapter; source comparison pending |
| `DAc0da.esm:006133` | `zDcdLetterRadiance` | Letter to a Friend | DAc0da quest-integrated; direct VIGILANT/Altano continuity link |
| `DAc0da.esm:00CA5A` | `zDcdLetterTharn01` | Tharn's Note | DAc0da Abnur side-story document |
| `DAc0da.esm:00CEDD` | `zDcdLetterSloadOrder` | Orders to N'Danda | DAc0da Sload operational document |
| `DAc0da.esm:00CEDF` | `zDcdLetterTharnWillA` | The Last Will and Testament of Abnur Tharn | DAc0da epilogue variant |
| `DAc0da.esm:00CEE0` | `zDcdLetterTharnWillB` | The Last Will and Testament of Abnur Tharn | DAc0da epilogue variant |

## Verified Daggerfall / Totem-letter reuse

The following six records are now verified as adapted reuses of the official **The Elder Scrolls II: Daggerfall** correspondence from the **Totem, Totem, Who Gets the Totem? / Who Gets the Totem** quest sequence.

They are **not Vicn-authored lore text**.

| DAc0da source | Editor ID | DAc0da title | Origin status |
|---|---|---|---|
| `DAc0da.esm:00455D` | `zDcdLetterDaggerfall01` | Letter from Queen Akorithi | verified Daggerfall official-text reuse |
| `DAc0da.esm:00455E` | `zDcdLetterDaggerfall02` | Letter from King Eadwyre | verified Daggerfall official-text reuse |
| `DAc0da.esm:00455F` | `zDcdLetterDaggerfall03` | Letter from Gortwog | verified Daggerfall official-text reuse |
| `DAc0da.esm:004560` | `zDcdLetterDaggerfall04` | Letter from King of the Worms | verified Daggerfall official-text reuse |
| `DAc0da.esm:004561` | `zDcdLetterDaggerfall05` | Letter from The Underking | verified Daggerfall official-text reuse |
| `DAc0da.esm:004562` | `zDcdLetterDaggerfall06` | Letter from Lady Brisienna | verified Daggerfall official-text reuse |

### Adaptation behavior

DAc0da preserves the substantive Daggerfall wording while resolving dynamic quest placeholders into a static in-mod form.

Examples:

- Daggerfall's dynamic `(Player's name)` becomes **Agent**.
- Eadwyre's `Noble (player's name)` becomes **Noble Agent**.
- Underking's dynamic meeting location is replaced by **the appointed place**.
- Brisienna's dynamic town/region/building destination is likewise replaced by **the appointed place**.

Minor punctuation/spacing differences also occur.

### DAc0da-specific significance

Although the letter prose itself is reused official text, DAc0da places the six-letter set inside:

- `DAc0da.esm:004563` — `zDcdLitemAgentLetter`

and places that list in the dedicated MQ01 **Agent ash pile**.

Therefore:

- **letter content** -> Daggerfall official-source provenance;
- **selection/placement as Agent loot** -> DAc0da/Vicn narrative-design evidence.

This distinction is important for the DAc0da Agent -> Daggerfall Agent / Warp in the West relationship.

## Nahd fiction / apocryphal-developer-text block

| Source | Editor ID | Title | Current provenance |
|---|---|---|---|
| `DAc0da.esm:0085FC` | `zDcdNahdFiction_001_Mojonation1487` | Djaf: Arena of Lyg | external/apocryphal source comparison pending |
| `DAc0da.esm:0085FD` | `zDcdNahdFiction_002_MK` | Ghost Choir 9 | editor ID flags MK-associated source; exact origin comparison pending |
| `DAc0da.esm:0085FE` | `zDcdNahdFiction_003_MK` | ANON/ANU/ANUI-EL | matching text/title already present in apocryphal library; reused source |
| `DAc0da.esm:0085FF` | `zDcdNahdFiction_004_MK` | The Tsaesci Creation Myth | MK-associated/source comparison pending |
| `DAc0da.esm:008600` | `zDcdNahdFiction_005_MK` | Dominion Prism Textract (Partial) | MK-associated/source comparison pending |
| `DAc0da.esm:008601` | `zDcdNahdFiction_006_MK` | et'Ada, Eight Aedra, Eat the Dreamer | MK-associated/source comparison pending |
| `DAc0da.esm:008602` | `zDcdNahdFiction_007_MK` | Lament for Pelinal | MK-associated/source comparison pending |
| `DAc0da.esm:00CE63` | `zDcdNahdFiction_008_MK` | A Type of Zero Still to Be Discovered | exact title/source already present in apocryphal library; verified developer-obscure-text reuse there |
| `DAc0da.esm:00CE64` | `zDcdNahdFiction_ESO001` | Karnwasten Temporal Tome | DAc0da alternate-reality temporal tome |
| `DAc0da.esm:00CE65` | `zDcdNahdFiction_ESO002` | Traitor's Vault Temporal Tome | DAc0da alternate-reality temporal tome |
| `DAc0da.esm:00CE66` | `zDcdNahdFiction_ESO003` | Garden of Sacred Numbers Temporal Tome | DAc0da alternate-reality temporal tome |

## Spell/item books

The remaining **66 BOOK records** are primarily summon items/spell tomes such as:

- Yaghra pearls;
- skull-based Worm/Goldborn summons;
- Dwemer lexicons;
- Black Books used as summon objects;
- idols and magatama;
- delayed rune spells;
- Numidium/quantum-themed utility spells.

Their short DESC fields generally name the summon/spell rather than provide prose lore. They remain useful as **entity/item evidence** and should be indexed during creature/artifact passes, but they are lower priority than the 24 narrative texts above.

## Next provenance work

1. exact source resolution for unresolved `NahdFiction_*_MK` records;
2. preserve DAc0da temporal-tome prose as alternate-reality evidence;
3. link DAc0da-specific letters to their quests/characters;
4. do not duplicate full apocryphal texts when the canonical library already stores them—link to the existing source instead.
