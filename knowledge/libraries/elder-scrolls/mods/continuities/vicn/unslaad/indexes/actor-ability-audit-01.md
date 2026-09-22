# Actor intrinsic-ability audit 01

Continuity: tes.mod.vicn.unslaad
Primary source: translated Unslaad.esm 3.0.6

This pass reads custom NPC-attached **SPLO** and **PRKR** records.

Its purpose is to separate:
- intrinsic actor/form abilities;
- shared proxy/body packages;
- generic boss/difficulty scaffolding.

## High-value shared ability packages

### Ulliss / Lizz
Both:
- Ulliss 030022F6
- Lizz 030CE5F5

carry the exact same custom spell:
- **Ulliss Ability** / zzzCrbUlliss

Lizz also uses the Half-Dragon Child race while Ulliss uses the Half-Dragon race.

This is strong implementation support for direct inherited/form continuity between mother and daughter.

### Austella / Hoarfrost Witch
Both:
- Austella 030188B1
- Hoarfrost Witch 032E87A1

carry:
- **Austera Ability** / zzzCrbAustera
- custom Austera Combat AI effect.

The Hoarfrost Witch is a Training-Faction proxy, so shared ability means **Austella-style combat/body package**, not necessarily literal identity.

### Gray Owl / Grayed-Out Boy
Secret Gray Owl:
- **Gray Owl Abilities** / KIN variant
- Kin Resist
- No Detection

Grayed-Out Boy:
- **Gray Owl Abilities** / non-KIN variant
- generic boss difficulty package.

This directly links the training/proxy actor to the Gray-Owl combat archetype while preserving form differences.

### Khev / Molag
Khev the Dreugh King:
- **Khev01 abilities**
- Khev01 Combat AI

Molag the Lord of Lies:
- **Khev02 abilities**
- Khev02 Combat AI

The naming makes Molag's boss package an explicit second Khev-phase implementation even though the displayed identity is Molag.

### Priest of Jhunal / Mnegmegh
Both:
- Priest of Jhunal
- Mnegmegh the Banner-Lamp

carry the same:
- **Jhunal Priest abilities**

Mnegmegh additionally has an ice/ghost visual package.

This is hard implementation evidence for a shared priestly combat archetype.

## Other useful actor-specific abilities

### Clone of Ayrenn
Carries:
- **Ayrenn Ability**
- Metal Death Ability

This strengthens the clone as a purpose-built Ayrenn proxy in Oracle Iridescent's Workshop.

### Dov-Ah-Kiin
Carries:
- **Dovahkiin Abilities**
- custom Dovahkiin Combat AI
- a custom summon-multiplier perk
- Dragonrend-weakening perk

This belongs beside the spectral-dragon and Dragon-Soul equipment graph.

### Elja the Void-Jill
Carries:
- **Hollowed Jill Ability**
- custom necro/Jill visual effect.

### Aisha forms
Ghost Aisha carries:
- Ghost Ability.

Sabre Aisha carries:
- Sabre Aisha abilities.

These are form-state packages, not separate identities by default.

## Technical families that should not be over-read

Many unrelated bosses share:
- Boss Difficulty
- Damage Difficulty
- Increase Detection
- a perk displayed as **Dragonskin**

Because these appear across unrelated actors, they are combat-balancing infrastructure rather than reliable narrative lineage evidence.

## Evidence rule

Shared actor ability is strong evidence for:
- shared combat/form implementation;
- proxy/reconstruction relationships;
- intentional state linkage.

It is weaker evidence for:
- same soul;
- same historical individual;
- biological descent;
- metaphysical identity.

Use dialogue, quests, race, placement, and form history to decide whether a shared ability can support a stronger claim.
