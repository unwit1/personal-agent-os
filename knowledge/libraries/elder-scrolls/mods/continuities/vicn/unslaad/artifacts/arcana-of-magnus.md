# Arcana of Magnus / fire of Magnus

Continuity: tes.mod.vicn.unslaad  
Primary dialogue: Lingering Snow  
Effect representation: ACTI 031969F8 / zzzCrbFXMagnusFire

## Direct UNSLAAD testimony

When spared, Jhunal the Gray offers the player "the knowledge of Magnus."

INFO 03196A0A has Jhunal identify the power as an **Arcana of Magnus** that he stole from **Saarthal**.

Subsequent scene lines call it:
- the fire of Magnus;
- ancient fire;
- warm;
- a fire that spreads death.

The ESM includes an effect activator named **zzzCrbFXMagnusFire**, but this pass has not identified a uniquely named inventory item representing the Arcana.

## Cross-VICN corroboration

VIGILANT independently contains a very close tradition.

Sir Berich says:
- Jhunal stole a fire rune / one of the Wisdoms of Magnus from Saarthal;
- the stolen flame affected those who approached it.

VIGILANT also contains Arcana-of-Jhunal / Arcane-Fire material around Burnt Casimir.

This is one of the strongest repeated **Jhunal + Saarthal + Magnus-fire** claims across VICN works.

## Distinctions

Do not automatically merge the Arcana of Magnus with:
- Ember of Atmora;
- Arcana of Dragon Souls;
- Owl barrier Arcana;
- generic Eye-of-Magnus model assets;
- every Jhunal-associated fire.

The recurring Saarthal/Magnus theft claim is high confidence; exact object identity across plugins remains unresolved.

## Placed-reference context

REFR 031969F9 places ACTI 031969F8 / zzzCrbFXMagnusFire in exterior CELL 030B49A7 of **Northern Sanctuary**.

The **Mural of Jhunal** is also placed in the same exterior cell. This co-location is direct implementation evidence and makes Northern Sanctuary a priority site for visual/script analysis of the late Jhunal arc.

## Implementation resolution

Mq05 VMAD exposes the linked property family:
- `MagnusFire`;
- `MagnusFireLit`;
- `MagnusFireBoom`;
- `MagnusBeacon`.

Combined with ACTI 031969F8 / `zzzCrbFXMagnusFire` and its Northern Sanctuary placement, this resolves the **quest-effect implementation** of the Arcana/fire-of-Magnus sequence.

What is not resolved is a separate unique inventory-object identity. The safest model is therefore:

**Arcana of Magnus = named knowledge/power represented through a scripted/effect sequence, with no independently established unique carried item in the current extraction.**

This closes the object-identity question for ingestion purposes while preserving the cross-plugin uncertainty over whether VIGILANT's corresponding Magnus-fire object is literally the same object.
