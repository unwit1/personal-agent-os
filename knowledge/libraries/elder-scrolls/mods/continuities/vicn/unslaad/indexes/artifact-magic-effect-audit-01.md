# Artifact magic-effect audit 01

Continuity: tes.mod.vicn.unslaad
Primary source: translated Unslaad.esm 3.0.6

This pass resolves selected lore-bearing items through:

**ARMO/WEAP -> ENCH -> MGEF**

and preserves the MGEF's player-facing effect description where available.

## Dov-Ah-Kiin / Dragonslayer set

### Dragonslayer Armor
Enchant: **Dragon Bone**
Effect: **Dragon Bones**
- physical resistance increases by 1% per Dragon Soul;
- maximum 50%.

### Dragonslayer Helmet
Enchant/effect: **Dragon Horn**
- magic resistance increases by 1% per Dragon Soul;
- maximum 50%.

### Dragonslayer Boots
Enchant/effect: **Dragon Feet**
- stagger resistance increases by 1% per Dragon Soul;
- maximum 50%.

### Dragonslayer Ring
Enchant/effect: **Dragon Eye**
- critical-hit chance increases by 1% per Dragon Soul;
- maximum 50%.

### Dragonslayer Gauntlets
Enchant: **Dragon Scale**
Effect: **Reflective Ward**
- creates a ward protecting against spells while blocking.

### Dragonslayer Greatsword
Enchant/effect: **Dragonfire**

The custom Dragonfire MGEF has no explanatory DNAM text in this plugin version. Do not invent a more specific mechanism from the name alone.

### Fang of the Old Dragon
Enchant/effect:
- **Shout of Paarthurnax**

The custom MGEF is named zzzCrbMgeVoiceParrthurnax and carries a voice-push effect script.

This is direct implementation evidence for a Paarthurnax-named Voice association, not proof of artifact ownership by Paarthurnax.

## Gray-Owl / Jhunal equipment

### Darkspeaker Ring
Enchant: **Darkspeaker**
Custom effect: **Augment Destruction**
- Destruction spells are 50% stronger;
- caster is 50% weaker to Destruction spells.

### Darkstalker's Staff
Enchant: **Darkstalker**

Its three effects resolve to Skyrim-master MGEFs in this pass; exact base-effect names are intentionally not guessed.

### Shield of Magnus
Enchant: **Resist Magic**

Its effects are Skyrim-master magic effects. The important lore edge is the item name/ownership, not a novel custom MGEF.

### Gray Owl's Mask
Enchant: **Gray Owl**

Its effects also resolve only to Skyrim-master MGEFs in this pass.

## KINMUNE / Oracle Iridescent

### Oracle Iridescent Mask
Enchant: **Fortify Magicka**

Includes custom effect:
- **Spell Absorption**
- absorbs a percentage of Magicka from hostile spells.

## Aisha

### Cat Ring
Enchant/effect:
- **Perfect Landing**

Effect text:
- falling damage is negated.

## Austella

### Hoarfrost Scythe
Enchant/effect:
- **Frost Blade**

Effect text:
- target takes frost damage to Health and Stamina.

## Blades Grandmaster

### Delphine's Oathblade
Enchant:
- **Dragon Damage**

The item description explicitly says it is especially effective against dragons.

## Khev / Molag

### Muatra
Both playable and combat forms are **unenchanted WEAP records** in the direct EITM layer.

Do not invent an enchantment because of the mythic name.

### Coldfire Sword
Enchant/effect:
- Bound Sword FX

The custom effect has no explanatory player-facing description.

## Ysgrim / trial relics

### Saarthal's Sorrow
Both forms are **unenchanted** at the direct EITM layer, despite the playable weapon's item description saying it is especially deadly to Daedra.

### Fists of Ysgramor / Storm Fist
Enchant/effect:
- Shock Damage

### Thunder-Scale Jill weapons
Enchant/effect:
- Shock Damage

The effect chain is mechanical and does not independently explain Jill ontology.

## Sinak / Woodland weapons

### Anga-Mora Blade / Greatblade
Enchant:
- **Absorb Magicka**

Custom effects:
- Drain Magicka
- Frost Damage

### Herma-Mora Blade / Greatblade
Enchant:
- **Absorb Stamina**

Custom effects:
- Absorb Stamina
- Poison Damage

These effects reinforce a mechanical distinction between the two weapon families but do not by themselves define Anga-Mora or Herma-Mora cosmologically.

## Method rule

An enchantment name is implementation evidence.

Use custom MGEF descriptions when available.
Do not reverse-name unresolved Skyrim-master FormIDs from memory or guesswork.
