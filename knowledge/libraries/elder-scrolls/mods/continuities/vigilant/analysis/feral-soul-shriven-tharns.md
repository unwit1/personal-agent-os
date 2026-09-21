# Feral Soul-Shriven Tharns

Continuity: `tes.mod.vigilant`

Primary source: user-provided `Vigilant.esm`

## Question

Do **Radokhan Tharn**, **Ortutay Tharn**, and **Marosi Tharn** represent hidden historical Tharn characters with bespoke stories, or are they themed variants inside VIGILANT's radiant Soul-Shriven system?

## Answer

Structurally, all three are **radiant Soul-Shriven variants**.

Each has:
- one named NPC base;
- one Soul-Shriven spawn trigger;
- no unique dialogue;
- no bespoke quest alias outside the radiant system;
- the generic Soul-Shriven template/faction/death-list stack.

Their names, gear, and placements make them narratively flavored, but the ESM does not currently support full biographies.

## Common parent system

The encounter quest is:

- `QUST 0251532C` / **Feral Soul-Shriven**

Its objective is:

- **Defeat <Alias=Enemy>**

The generic trigger base is:

- `ACTI 0251532D` / **Soul-Shriven**

using:
- `CHRqSoulShrivenTRGScript`.

Individual placed trigger references supply an `SvBase` NPC.

This is the same system used for:
- Judo of the Order of Diagna;
- many other named Soul-Shriven variants.

## Radokhan

Trigger:
- `REFR 0251777C`

`SvBase`:
- `NPC_ 0251654D` / **Radokhan Tharn**

Cell:
- `0206E57A` / `CHicCourtMarukh01`

Location:
- `023870E4` / **Holy Brothers of Marukh Priory**

Loadout:
- Alessian Battlemage Armor
- Stonefire Wand

## Ortutay

Trigger:
- `REFR 02517762`

`SvBase`:
- `NPC_ 02516550` / **Ortutay Tharn**

Cell/location:
- `02101AA1` / **Marukh's Underground Priory**

Loadout:
- Marukhati Selective Armor
- Coldflame Wand

## Marosi

Trigger:
- `REFR 0251776B`

`SvBase`:
- `NPC_ 02516551` / **Marosi Tharn**

Cell/location:
- `02119953` / **Malada Aldmerisel**

Loadout:
- Marukhati Selective Armor
- Inquisitor Sword

## Placement pattern

The locations form a meaningful route:

**Holy Brothers of Marukh Priory → Marukh's Underground Priory → Malada Aldmerisel**

That is the same broad historical/Alessian complex containing:
- Marukh material;
- Selective imagery;
- Caliburn;
- licensed Marukhati texts;
- other Alessian saints and relics.

The trio therefore reads as **environmental evidence of Tharn participation in the Marukhati historical layer**.

## Relationship to Amicus Tharn

Amicus is implemented completely differently:

- bespoke boss;
- dedicated quest alias in **Broken Horns**;
- four Petition documents;
- corpse-image trail;
- unique death list;
- explicit ideology.

The trio has none of those layers.

Therefore:

**Amicus Tharn ≠ merely another Feral Soul-Shriven Tharn.**

The shared surname can support a House Tharn association, but not direct kinship.

## Relationship to Fervidius Tharn

Fervidius enters VIGILANT through official-source books.

The trio:
- occupies Marukhati spaces;
- uses Marukhati/Alessian equipment;
- shares the Tharn surname.

That creates a deliberate thematic/dynastic association with the same tradition.

But no record says that any of the three are:
- Fervidius's children;
- Fervidius's ancestors;
- Fervidius's siblings;
- members of his immediate branch.

No genealogy should be inferred.

## Official-source check

Targeted searches for the exact names:
- Radokhan Tharn
- Ortutay Tharn
- Marosi Tharn

did not surface official Elder Scrolls character records.

Search results instead pointed back to VIGILANT-derived guides for at least some of these names.

Current provenance classification:

**VIGILANT-specific named Tharns built into an established House Tharn / Marukhati historical context.**

## Reliability

### A — structural
- exact NPC names;
- Imperial race;
- Soul-Shriven faction/template;
- generic Feral Soul-Shriven quest ownership;
- trigger placement;
- gear;
- one trigger per named NPC.

### Interpretive
- all three are literal members of one Tharn branch;
- all three were historical battlemages before becoming Soul-Shriven;
- their ordering represents a family chronology.

Those interpretations remain unproven.

## Lorekeeper rule

Named radiant Soul-Shriven figures should be indexed as characters, but with a lightweight ontology:

- `type: named_soul_shriven_variant`
- `narrative_depth: low unless further sources exist`
- `source: structural ESM encounter evidence`

Do not automatically promote every named radiant encounter into the same biography depth as Amicus, Gaiden, Marukh, or Pelan.
