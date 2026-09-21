# Feral Soul-Shriven encounter system

Continuity: `tes.mod.vigilant`

Primary structural anchors:
- `QUST 0251532C` — **Feral Soul-Shriven**
- `ACTI 0251532D` — **Soul-Shriven**
- script: `CHRqSoulShrivenTRGScript`
- `FACT 025738DF` — **Soul-Shriven**
- `SPEL 0251651F` — **Soul Shriven abilities**
- template: `NPC_ 025177A1` / **Soul-Shriven**
- generic death list: `LVLI 025177A2` / `zzzCHDeathItemRqShriven`

## Core function

VIGILANT implements a reusable Coldharbour encounter system in which placed triggers can spawn a named Soul-Shriven actor base.

The quest objective is generically:

**Defeat <Alias=Enemy>**

Individual trigger references provide an `SvBase` NPC.

This means a named encounter can preserve:
- a historical name;
- themed equipment;
- race;
- institutional references;

while still being implemented through one common radiant/randomized combat framework.

## Named-identity rule

A named Soul-Shriven should not automatically receive the same biography depth as a bespoke story NPC.

The current structural rule is:

**name/theme + generic Soul-Shriven template + no unique dialogue/quest ownership = lightweight named encounter identity**

Examples already analyzed include:
- Judo of the Order of Diagna;
- Radokhan Tharn;
- Ortutay Tharn;
- Marosi Tharn.

The wider extraction indicates more than thirty named variants in the same encounter family.

## Judo example

`NPC_ 0251653B` / **Judo of the Order of Diagna**:
- templates from Soul-Shriven;
- belongs to Soul-Shriven faction;
- has Soul Shriven abilities;
- uses the generic Feral Soul-Shriven system;
- is instantiated by `REFR 0251778B` in the Arena District;
- wears Knight of Diagna gear;
- carries Akaviri Black Katanas.

This preserves two simultaneous truths:

1. **historical/thematic identity:** Order of Diagna;
2. **Coldharbour implementation:** named Soul-Shriven encounter.

The second should not overwrite the first.

## Tharn examples

Three named Tharns are implemented through the same system:

### Radokhan Tharn
- trigger: `REFR 0251777C`
- base: `NPC_ 0251654D`
- location: Holy Brothers of Marukh Priory
- equipment: Alessian Battlemage Armor, Stonefire Wand

### Ortutay Tharn
- trigger: `REFR 02517762`
- base: `NPC_ 02516550`
- location: Marukh's Underground Priory
- equipment: Marukhati Selective Armor, Coldflame Wand

### Marosi Tharn
- trigger: `REFR 0251776B`
- base: `NPC_ 02516551`
- location: Malada Aldmerisel
- equipment: Marukhati Selective Armor, Inquisitor Sword

Their names, placements, and gear tie them thematically to Alessian/Marukhati history.

The generic encounter implementation means the ESM does not currently support detailed individual biographies.

## Contrast with Amicus Tharn

Amicus Tharn is structurally different:
- bespoke boss NPC;
- Broken Horns quest alias;
- four Petition documents;
- corpse-image trail;
- unique death list;
- explicit ideology;
- dedicated environmental narrative.

Therefore:

**Amicus Tharn ≠ another generic Feral Soul-Shriven Tharn.**

Shared surname and historical context can support House Tharn association, not equal narrative depth or direct genealogy.

## Encounter ecology versus historical chronology

Coldharbour places named Soul-Shriven variants in historically resonant spaces.

Examples:
- Diagna identity in Arena District;
- Tharn/Alessian identities in Marukhite priory and Malada spaces.

These placements may intentionally evoke historical associations.

They do not prove that:
- the actor historically died at that exact location;
- the actors all lived in the same era;
- the actors formed one unit;
- Coldharbour placement is a literal replay of history.

## Soul-Shriven licensed substrate

Soul-Shriven as a concept has established Elder Scrolls/ESO substrate involving souls in Coldharbour and counterfeit/reformed bodies.

VIGILANT uses that substrate as a flexible encounter/identity mechanism.

The exact named variants, placements, equipment, and cross-era associations are VIGILANT-specific.

## Retrieval ontology

For a named Feral Soul-Shriven, store separately:

### Historical/thematic identity
Example:
- Judo → Order of Diagna
- Ortutay → Tharn / Marukhati-themed identity

### Encounter implementation
- Soul-Shriven template
- Soul-Shriven faction
- trigger ref
- Feral Soul-Shriven quest

### Environmental context
- cell/location
- equipment
- nearby institutional lore

### Narrative depth
Use:
- **low** if only generic encounter evidence exists;
- **medium** if equipment/location creates strong contextual links;
- **high** only when unique dialogue, quest aliases, documents, or bespoke scripting exist.

## Relationship to manifestation ontology

This page expands the Soul-Shriven branch of:

`analysis/coldharbour-manifestation-classes.md`

That broader page also covers:
- Alessian Sleeper forms;
- memory forms;
- bosses;
- summons;
- corpses/relic representations.

## Open extraction work

Future source recovery should:
1. persist the full named Soul-Shriven variant inventory;
2. record every trigger → `SvBase` mapping;
3. capture locations and loadouts;
4. identify variants with unique scripts or non-generic quest references;
5. promote only those with additional evidence into deeper character dossiers.

## Canon boundary

The generic Soul-Shriven concept has licensed Elder Scrolls substrate.

VIGILANT's Feral Soul-Shriven quest, named variant roster, trigger system, placements, and historical theming belong to `tes.mod.vigilant`.
