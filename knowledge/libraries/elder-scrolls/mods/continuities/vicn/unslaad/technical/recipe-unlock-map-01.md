# Recipe unlock map 01

Continuity: tes.mod.vicn.unslaad
Primary source: translated Unslaad.esm 3.0.6

This pass resolves COBJ crafting conditions for major lore-bearing reconstruction recipes.

Condition function IDs are read directly from CTDA:
- 543 = GetQuestCompleted
- 84 = GetDeadCount

## Gray-Owl forms

After **The Owl Flies at Dusk** is completed:
- Gray OWL
- Gray EGG
- Shadow of the Gray OWL

These use the custom SnowBall crafting keyword.

**Gray Owl's Mask** is a separate recipe that unlocks earlier, after **Lingering Snow**.

## Dov-Ah-Kiin / Dragonslayer

After **Lingering Snow**:
- Dragonslayer Armor
- Dragonslayer Helmet
- Dragonslayer Gauntlets
- Dragonslayer Boots
- Dragonslayer Ring
- Dragonslayer Greatsword

After **Long Winter**:
- Dragonslayer Shield
- Dragonslayer Greatshield
- Delphine's Oathblade

This split mirrors the narrative progression from Lost Unslaad / future-Blades material into the later Dov-Ah-Kiin encounter.

## Jill / Thunder-Scale

After **VS Jill 01**:
- Thunder-Scale Boots
- Thunder-Scale Circlet
- Thunder-Scale Armor
- Thunder-Scale Gauntlets
- Thunder-Scale Spear

After **VS Jill 02**:
- Thunder-Scale Sword
- Thunder-Scale Greatsword

The two Jill trials therefore gate different pieces of the reconstructable Jill equipment family.

## Khev / Dreugh King

After **VS Dreugh King**:
- Short Muatra
- Muatra

The weapons are unenchanted in the direct EITM layer; their importance is encounter/provenance rather than a custom magic effect.

## Magnar

After **VS Idol of Magnar**:
- Magnar's Warrior Boots
- Magnar's Warrior Armor
- Magnar's Warrior Gauntlets
- Magnar's Warrior Helmet
- Magnar's Warrior Spear
- Magnar's Warrior Longspear

This is explicit post-boss reconstruction gating.

## Yngol

Recipes for Yngol's set are conditioned on the death count of **Remnant of Yngol**:
- Yngol's Boots
- Yngol's Armor
- Yngol's Coat
- Yngol's Gauntlets
- Yngol's Shield
- Yngol's War Axe
- Yngol's Battleaxe

This is direct actor-death gating rather than quest-completion gating.

## Oracle Iridescent / Ayrenn

**Oracle Iridescent Mask** uses a GetDeadCount condition referencing **Clone of Ayrenn**.

This reinforces the already-established workshop staging:
Clone of Ayrenn -> death -> Oracle Iridescent Mask reconstruction.

## Jhunal / Hare

After **The Final Journey**:
- Priest of Jhunal Mask
- Mask of the Hare

This places both mask reconstructions after the same late Atmoran quest layer.

## Staff family

### Staff of the World-Eater
Unlock:
- **The Final Journey** completed

Direct item description:
- Shouts are 50% more powerful.

A placed reward chest also exists in Frozen Abyss.

### Staff of Bormahu
Unlock:
- **Arkved** completed

Direct item description:
- time between shouts reduced by 20%.

### Staff of the Jills
Unlock:
- **Arkved** completed

Direct item description:
- time between shouts reduced by 20%.

A reward chest containing the Staff of the Jills is placed in Dragon's Peak.

### Staff of Orkey
Unlock:
- GetDeadCount on **Rackety-Nix**

Direct item description:
- reduces damage from fire magic by 25%.

A placed reward/container relation also ties it to Kjhelt of the Cult of Orkey in Frozen Abyss.

## Interpretation rule

Recipe gating is hard implementation evidence for **when the game authorizes reconstruction/crafting**.

It does not mean:
- the quest protagonist historically forged the original artifact at that moment;
- the unlock quest created the mythic item in-world;
- shared unlock conditions imply shared metaphysical origin.

Use it to distinguish post-encounter reconstruction from direct ownership or loot.
