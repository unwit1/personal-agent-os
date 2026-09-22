# Mask / outfit identity pass

Continuity: tes.mod.vicn.unslaad
Primary source: translated Unslaad.esm 3.0.6

This pass resolves masks through **OTFT outfit membership** and NPC default outfits rather than ordinary CNTO inventory.

That distinction matters because several identity masks are worn as part of an actor's default visual/body state and do not appear as direct inventory items.

## Gray Owl's Mask

ARMO 0309D3E2 — **Gray Owl's Mask**

Appears in:
- OTFT 0309D3E4 / zzzCrbOutfitGrayOwl
- OTFT 03161AB4 / zzzCrbOutfitOwlWound

### NPC forms using Gray Owl outfit

**Jhunal the Gray** forms:
- 03112A8B / zzzCrbGrayOwl_Mq03Ghost
- 0309D3E6 / zzzCrbGrayOwl_Mq04
- 0318C84E / zzzCrbGrayOwl_Mq05

all use the Gray Owl outfit containing Gray Owl's Mask.

The wounded form:
- 03161AB5 / zzzCrbGrayOwl_Mq05Wound

uses the wounded Owl outfit, which still contains Gray Owl's Mask.

A separate actor:
- **Grayed-Out Boy**

also uses the Gray Owl outfit.

## Identity significance

This is strong implementation evidence that the **Jhunal the Gray** presentation is deliberately costumed/represented as **Gray Owl** across multiple quest phases.

It materially strengthens the dialogue evidence where Jhunal directly identifies himself as the Gray Owl.

At the same time, it does not require every Gray-Owl body/inspection actor elsewhere to be one continuous physical body.

## Void Jill Mask

ARMO 034ACE34 — **Void Jill Mask**

Appears in:
- OTFT 03416918 / zzzCrbOutfitVoidJillian01

NPC:
- **Elja the Void-Jill**

uses this full outfit.

The outfit also contains:
- Void Jill Boots
- Void Jill Cloak
- Void Jill Armor
- Void Jill Gauntlets
- Void Jill Hood
- Void Jill Mask

This confirms the Void-Jill set as Elja's authored body/combat presentation rather than only a post-boss player reward family.

## Other named masks

The current OTFT pass did not resolve direct default-outfit users for:
- Priest of Jhunal Mask
- Mask of the Hare
- Oracle Iridescent Mask

Those remain reward/reconstruction artifacts unless later outfit/placed-reference evidence identifies a wearer.

## Handling rule

Default outfit membership is strong evidence for **worn visual identity/state**.

It should be kept separate from:
- death loot;
- craft recipes;
- item names;
- actor biography.
