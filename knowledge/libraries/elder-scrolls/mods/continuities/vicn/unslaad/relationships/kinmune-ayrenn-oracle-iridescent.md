# KINMUNE / Ayrenn / Oracle Iridescent staging

Continuity: tes.mod.vicn.unslaad  
External source layer: apocryphal/developer text **ANON, ANU, ANUI-EL**

This is one of UNSLAAD's clearest cases of deliberate staging around reused apocryphal material.

## External text already in the library

The apocryphal source:

knowledge/libraries/elder-scrolls/sources/apocryphal-library/books/040008F1-anon-anu-anui-el.txt

contains the KINMUNE material and explicitly presents:
- Queen Ayrenn as KINMUNE;
- **Oracle Iridescent** as one of KINMUNE's names/titles.

This material remains external/apocryphal provenance, not official released-game canon and not Vicn-authored prose.

## UNSLAAD workshop

CELL 033A46F0 has:

- EditorID: **zzzCrbKinmuneRoom**
- Display name: **Oracle Iridescent's Workshop**

The cell contains two placements of **Fragmented Records** carrying KINMUNE excerpts.

## Clone of Ayrenn

NPC 033A47AA / zzzCrbSubBossAyrenn:
- display name: **Clone of Ayrenn**
- race: Manakin Race
- faction: World Eater Faction
- placed inside **Oracle Iridescent's Workshop**
- directly carries NPC-form **Princess Ayrenn's Greatsword**

Its death list yields:
- Princess Ayrenn's Boots
- Princess Ayrenn's Armor
- Princess Ayrenn's Gauntlets
- Princess Ayrenn's Helmet
- Princess Ayrenn's Greatsword
- **Oracle Iridescent Mask**

## Oracle Iridescent Mask

ARMO 033A995B / zzzCrbArmorKrlMask

Uses ENCH 033A996F / **Fortify Magicka** and includes a custom **Spell Absorption** effect.

## Evidence synthesis

The following chain is direct:

1. external KINMUNE text links **Ayrenn ↔ KINMUNE ↔ Oracle Iridescent**;
2. UNSLAAD creates a cell internally named **Kinmune Room** and displayed as **Oracle Iridescent's Workshop**;
3. KINMUNE fragments are placed in that room;
4. **Clone of Ayrenn** is placed in the same room;
5. the clone drops **Oracle Iridescent Mask** and Princess Ayrenn equipment.

This is strong evidence that UNSLAAD intentionally stages the apocryphal KINMUNE/Ayrenn/Oracle-Iridescent identity complex.

## Guardrail

Do not turn this into:
- official ESO canon;
- a claim that released-game Queen Ayrenn is canonically KINMUNE;
- a claim that Vicn authored the original KINMUNE text;
- proof that the Clone of Ayrenn is literally the original KINMUNE entity.

The safe statement is that **UNSLAAD deliberately reuses and dramatizes that apocryphal identity tradition**.

## Mask effect

Oracle Iridescent Mask includes a custom **Spell Absorption** effect that absorbs a percentage of Magicka from hostile spells, in addition to its Fortify-Magicka package.

This is a direct item mechanic; it should not be overinterpreted as a complete KINMUNE ability profile.

## Craft unlock

Oracle Iridescent Mask's reconstruction recipe uses **GetDeadCount** on **Clone of Ayrenn**. The mask is therefore deliberately gated behind defeating the clone in addition to appearing in the clone's death-item set.
