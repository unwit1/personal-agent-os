# Black Hand — VIGILANT continuity

- Continuity: `tes.mod.vigilant`
- Type: Sithis-linked guide/servitor concept
- Evidence status: partial ESM implementation + supplementary identity/background
- Related systems: Sithis' Eye Ring, Black Hand dialogue conditions, crafting/reaction system
- Supplementary source: `sources/supplementary/a123999-vigilant-backgrounds.md`

## Direct ESM-level evidence

The currently persisted ESM analysis does not yet contain a full Black Hand quest or named-member dossier.

It does, however, preserve a broader **Black Hand / Sithis gameplay-dialogue system**.

The clearest structural anchor appears through **Sithis' Eye Ring**:
- the ring uses the **Eye of Sithis** enchantment;
- its effect is **Twin Souls**;
- the ring participates in dedicated crafting;
- a `zzzCHSithisEyeReactionTrigger` exists;
- multiple dialogue conditions are tied to the wider Black Hand/Sithis system.

This is enough to establish that “Black Hand” is not merely a phrase from commentary. VIGILANT contains an implemented Sithis-linked interaction layer around it.

The currently persisted extraction does **not** yet preserve:
- the full Black Hand member roster;
- exact Black Hand NPC FormIDs;
- a dedicated Black Hand faction record;
- all dialogue responses governed by the ring/trigger;
- the runtime reason Twin Souls matters to Black Hand encounters.

## Supplementary identity/background

The a123999 VIGILANT background article describes the **Black Hand** as:
- the five young children of the **Night Mother**;
- guides for dead or cursed mortals;
- entities who lead those souls toward **Sithis**.

Source:
- `sources/supplementary/a123999-vigilant-backgrounds.md`

This gives the system a coherent narrative role that the current ESM-only extraction has not yet reconstructed.

Lorekeeper should keep the source layers separate:

- **ESM:** Black Hand/Sithis reaction, ring, crafting, and dialogue-condition system exists.
- **supplementary commentary:** Black Hand are the Night Mother's five children acting as guides toward Sithis.

## Night Mother boundary

The term **Night Mother** appears throughout Elder Scrolls lore with multiple traditions and interpretations.

The supplementary VIGILANT claim should therefore not be generalized into a base-canon statement that the Dark Brotherhood's Night Mother literally has these five VIGILANT Black Hand children.

Store it under the VIGILANT continuity overlay.

## Relationship to Manthar

Sorcerer Manthar can drop **Sithis' Eye Ring**.

That places Manthar inside the Black Hand/Sithis item system.

It does **not** prove:
- Manthar belongs to the Black Hand;
- Sithis transformed Manthar into the Bone Lord;
- the Black Hand caused his historical disappearance.

The existing Manthar analysis correctly treats the ring as a broader system item rather than transformation evidence.

## Ontology

Current safe model:

**Black Hand → Sithis-linked guidance/encounter concept with an implemented reaction/item system.**

Do not yet model it as:
- a conventional mortal guild;
- the Dark Brotherhood's Black Hand leadership rank;
- a faction with known five ESM NPC records.

The supplementary article's “five children” language may refer to a metaphysical group rather than the standard Dark Brotherhood organizational term.

## Relationship map

- **Black Hand → associated with → Sithis**
- **Black Hand → supplementary role → guide dead/cursed mortals**
- **Night Mother → supplementary parent/source → five Black Hand children**
- **Sithis' Eye Ring → participates in → Black Hand interaction system**
- **Manthar → can carry/drop → Sithis' Eye Ring**
- **Manthar → not thereby proven member of → Black Hand**

## Recovery work

Future ESM/script extraction should target:
- all dialogue conditions involving the Black Hand;
- `zzzCHSithisEyeReactionTrigger`;
- NPC/reference records linked to those dialogues;
- any Black Hand-specific faction/keyword/editor IDs;
- exact behavior triggered by Sithis' Eye Ring.

## Canon boundary

The VIGILANT Black Hand identity and five-child guidance role belong to `tes.mod.vigilant`. Any relationship to established Night Mother/Sithis/Dark Brotherhood lore must retain source separation.
