# Gilded introduction scene — placed-actor resolution

Continuity: `tes.mod.clockwork`  
Scene: `05384489` / `CLWSQ02GildedIntroScene01`  
Quest: `052908C1` / *Steam-Powered*  
Location: `CELL 0537A08F` / **Nurndural - Hall of Elements**

The INFO-condition resolver sees these lines as broad Gilded candidates. The SCEN record narrows them to quest roles, and the scene's VMAD then identifies the **actual placed ACHR references** used for those roles:

- **Gilded01** — alias 3 → `ACHR 053895B2` → base `0524471A CLWLvlGildedMagic`
- **Gilded02** — alias 4 → `ACHR 053895B4` → base `0522B12E CLWLvlGildedMelee1H`
- **Gilded03** — alias 5 → `ACHR 053895B3` → base `0522B12E CLWLvlGildedMelee1H`

All three references and their scene markers are placed in the Hall of Elements.

| INFO | Placed scene actor | Text |
|---|---|---|
| `0538448D` | Gilded01 / `053895B2` | You know, sometimes. |
| `05384490` | Gilded02 / `053895B4` | Sometimes I get to thinking. |
| `05384493` | Gilded03 / `053895B3` | You know me. |
| `05384495` | Gilded01 / `053895B2` | Why don't you come away. |
| `053895A6` | Gilded02 / `053895B4` | No... I won't bite. |
| `053895A8` | Gilded03 / `053895B3` | I won't bite your face. |
| `053895AA` | Gilded01 / `053895B2` | Come away with me. |

This is now high-confidence **scene-actor-reference attribution**. The base records are leveled Gilded archetypes rather than unique persistent named individuals, so Lorekeeper still does not invent personal names.

The strict multi-candidate accounting remains unchanged for reproducibility: 519 broad-Gilded INFO records, of which these seven now have richer scene/actor/location context; 512 remain undifferentiated.
