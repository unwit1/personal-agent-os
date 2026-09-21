# Custom Shout / Voice audit

Continuity: tes.mod.vicn.unslaad
Primary source: translated Unslaad.esm 3.0.6

The ESM contains 11 custom SHOU records resolved directly to the actors that carry them.

## Rackety-Nix

Both:
- hostile/sub-boss Rackety-Nix
- summoned Rackety-Nix

carry:
- **Chaotic Fire Ball** -> Nix Fire Ball
- **Shout** -> Nix Shout

This is direct evidence that the summoned form reproduces the Voice package of the hostile creature archetype.

## Eamal the Priestess of Arkayn

Carries:
- **Shock Breath**

The Shout resolves to custom Shock Breath spell/effect records.

## Pelinaalilargus the Fox

Carries three custom Shouts:
- **Fire Breath**
- **Fireball**
- a generic-display **Shout** whose spell is internally named **Pelinal Beam Shout**

This gives the Fox/Pelinal-associated boss an unusually broad custom Voice package.

## Dregs of Alduin / Manque

Both actors carry:
- **Fireball** -> Dark Voice
- **Pus Storm Call** -> Dark Storm / Pus Storm

This is a direct implementation link between Dregs of Alduin and Manque beyond their broader World-Eater/pus context.

## Ulliss dragon family

The following all carry the same custom **Frost Breath** Shout:
- Ulliss dragon form
- Uliizkaan
- Maliizkrein

This provides a hard combat-form relationship among the three frost-dragon actors.

## Ysgrim / Ysgramor phases

### Hoary King Ysgrim
Carries:
- **Ice Storm**

### Ysgramorsbelt
Carries:
- **Shock wave**

The phase transition therefore includes a direct change in custom Voice profile rather than merely a visual/body change.

## Pus-dragon package

Manque and Dregs of Alduin share:
- Dark Voice / Fireball
- Pus Storm Call

Their shared Shouts should be indexed with the World Eater / pus-dragon family, but do not by themselves prove individual identity.

## Handling rule

A SHOU record attached to an NPC is hard implementation evidence that the actor can use that Voice package.

It does not by itself establish:
- the exact spoken dragon words when those WOOP records come from Skyrim masters and are not decoded here;
- historical authorship of the Shout;
- that two actors sharing a Shout are the same individual.
