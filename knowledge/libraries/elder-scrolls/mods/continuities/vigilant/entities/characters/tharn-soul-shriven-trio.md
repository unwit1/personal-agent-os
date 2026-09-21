# Radokhan, Ortutay, and Marosi Tharn — VIGILANT continuity

Continuity: `tes.mod.vigilant`

These three named Tharns are implemented as radiant **Soul-Shriven battlemage variants** inside the Alessian/Marukhati route.

They are distinct from:
- **Amicus Tharn**, a bespoke boss/documentary character;
- **Fervidius Tharn**, whose official ESO texts are reprinted by VIGILANT.

## Shared implementation

All three:
- template from `NPC_ 025177A1` / **Soul-Shriven**;
- belong to `FACT 025738DF` / **Soul-Shriven**;
- use `LVLI 025177A2` / `zzzCHDeathItemRqShriven`;
- have `SPEL 0251651F` / **Soul Shriven abilities**;
- use the master Imperial race;
- are spawned through `ACTI 0251532D` / **Soul-Shriven** triggers using `CHRqSoulShrivenTRGScript`;
- participate in the `QUST 0251532C` / **Feral Soul-Shriven** encounter system;
- have no unique INFO dialogue identified;
- have no bespoke quest alias identified outside the radiant Soul-Shriven system.

This makes them best understood as **named historical/cultural Soul-Shriven combatants**, not hidden quest-givers.

## Radokhan Tharn

- `NPC_ 0251654D`
- EditorID: `zzzCHRqShrivenBattleMage`
- display name: **Radokhan Tharn**
- outfit: `OTFT 0251654C` / `zzzCHOutfitHrBattlemageRust`
- armor: **Alessian Battlemage Armor**
- weapon: `WEAP 0255982E` / **Stonefire Wand**
- trigger: `REFR 0251777C`
- cell: `CELL 0206E57A` / `CHicCourtMarukh01`
- location: **Holy Brothers of Marukh Priory**

Radokhan is the most explicitly Alessian-styled member of the trio because his armor is player-facing **Alessian Battlemage Armor** and his trigger is placed directly in the Holy Brothers of Marukh Priory.

## Ortutay Tharn

- `NPC_ 02516550`
- EditorID: `zzzCHRqShrivenBattleMageIce`
- display name: **Ortutay Tharn**
- outfit: `OTFT 0251654F` / `zzzCHOutfitHrBattlemageJ`
- armor: **Marukhati Selective Armor**
- weapon: `WEAP 0255982D` / **Coldflame Wand**
- trigger: `REFR 02517762`
- cell/location: **Marukh's Underground Priory**

Ortutay is placed deeper in the Marukh priory complex and uses Selective equipment rather than the rusted Alessian battlemage set.

## Marosi Tharn

- `NPC_ 02516551`
- EditorID: `zzzCHRqShrivenBattleMageShock`
- display name: **Marosi Tharn**
- outfit: `OTFT 0251654E` / `zzzCHOutfitHrBattlemage`
- armor: **Marukhati Selective Armor**
- weapon: `WEAP 02542E11` / **Inquisitor Sword**
- trigger: `REFR 0251776B`
- cell/location: **Malada Aldmerisel**

Marosi is placed farther along the Alessian/Ayleid route in Malada Aldmerisel.

## No recoverable genealogy

The ESM gives no:
- parent/child relation;
- sibling relation;
- ancestor/descendant relation;
- dialogue mentioning House Tharn;
- link to Fervidius;
- link to Amicus;
- link to Abnur, Euraxia, Jagar, Clivia, or other later Tharns.

Their only direct family evidence is the shared surname **Tharn**.

Targeted external lore searches did not surface official Elder Scrolls counterparts for the names:
- Radokhan Tharn;
- Ortutay Tharn;
- Marosi Tharn.

Current classification:

**VIGILANT-specific Tharn family members or Tharn-associated historical figures, exact genealogy unresolved.**

## Placement significance

The three are not distributed randomly.

Their triggers appear in sequence across the Marukhati route:

1. **Radokhan** — Holy Brothers of Marukh Priory
2. **Ortutay** — Marukh's Underground Priory
3. **Marosi** — Malada Aldmerisel

This suggests Vicn is using the Tharn surname as part of the Alessian/Marukhati historical texture of this route.

The placement is strong structural evidence for association with that tradition.

It is not enough to establish that the trio are literal descendants of Amicus or Fervidius.

## Relationship to the Feral Soul-Shriven system

Like Judo of the Order of Diagna, these Tharns are individual `SvBase` choices supplied to Soul-Shriven triggers.

Their names and gear give them historical flavor, but the encounter machinery is generic.

Lorekeeper should therefore preserve both layers:

- **character label:** named Tharn
- **encounter ontology:** radiant Soul-Shriven variant

rather than promoting each one into a heavily documented historical biography without additional evidence.

## Current relation model

Recommended:

- `Radokhan Tharn --associated_with--> Alessian/Marukhati tradition` — high confidence from placement/equipment
- `Ortutay Tharn --associated_with--> Marukhati Selective` — high confidence from placement/equipment
- `Marosi Tharn --associated_with--> Marukhati Selective` — high confidence from placement/equipment
- `trio --associated_with--> House Tharn` — medium/high from surname, but genealogy unresolved
- `trio --kin_of--> Amicus Tharn` — unresolved
- `trio --kin_of--> Fervidius Tharn` — unresolved
- `trio --official TES characters` — unsupported

## Canon boundary

Radokhan, Ortutay, and Marosi Tharn are currently treated as `tes.mod.vigilant` characters.

The broader existence of House Tharn and its Alessian/Marukhati history comes from established TES lore; these specific names do not currently have licensed-source corroboration.
