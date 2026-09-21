# Gilded introduction scene — quest-alias attribution

Continuity: `tes.mod.clockwork`  
Scene: `05384489` / `CLWSQ02GildedIntroScene01`  
Quest: `052908C1` / *Steam-Powered*

These seven INFO records are broad-Gilded matches in the strict voice/faction resolver, but the SCEN record assigns each dialogue action to a specific **quest actor alias**. This narrows the narrative speaker role without pretending the underlying leveled alias is one fixed NPC form.

| INFO | Scene role | Alias | Text |
|---|---|---:|---|
| `0538448D` | Gilded01 | 3 | You know, sometimes. |
| `05384490` | Gilded02 | 4 | Sometimes I get to thinking. |
| `05384493` | Gilded03 | 5 | You know me. |
| `05384495` | Gilded01 | 3 | Why don't you come away. |
| `053895A6` | Gilded02 | 4 | No... I won't bite. |
| `053895A8` | Gilded03 | 5 | I won't bite your face. |
| `053895AA` | Gilded01 | 3 | Come away with me. |

Each still has the same broad physical candidate pool at the strict NPC-form layer. The supplemental result is therefore **high confidence at quest-role level**, not a unique base-NPC identification.

### Ambiguity accounting

The strict resolver still contains **519** broad-Gilded multi-candidate INFO records. Seven of those are now scene-bound to Gilded01/02/03, leaving **512 genuinely undifferentiated broad-Gilded records** pending deeper package/reference/context analysis.
