# Actor / Equipment / Inventory Decoder — 2026-09-23

This checkpoint captures the gameplay-bearing actor/equipment records in the supplied Simonrim corpus while deliberately excluding facegen/model noise from balance inference.

## Coverage

- NPC_: 51 / 51
- CLAS: 2 / 2
- RACE: 2 / 2
- OTFT: 3 / 3
- CONT: 22 / 22
- ARMO: 7 / 7
- ALCH: 6 / 6
- AMMO: 6 / 6
- Decode failures: 0

Relationships:
- NPC spell links: 71
- NPC perk links: 145
- NPC inventory rows: 29
- Merchant/container inventory rows: 408
- Outfit item rows: 9

## Summon modeling

The 51 Mysticism NPC records preserve:
- character flags and summonability
- level/PC-level-mult fields and calculation bounds
- health/magicka/stamina offsets
- template inheritance flags and template references
- base/mod skill arrays
- AI aggression/confidence/morality/assistance
- spells, perks, inventory, factions
- class, race, combat-style, outfit and package-list references

50/51 supplied NPCs carry the Summonable flag and 49/51 use a template reference. Because template bodies for many Skyrim/DLC actors are external to this snapshot, the Balancer must distinguish explicit Mysticism fields from inherited vanilla values.

## Classes and races

Two Mysticism classes are decoded with full skill/attribute weights.

The two race records preserve skill boosts, base health/magicka/stamina, regeneration, carry/mass, unarmed damage/reach, movement/size flags and equipment capabilities. Facegen/tint/model data remains raw provenance but is not treated as a balance signal.

## Equipment and consumables

- Two exact imported Adamant ARMO overrides exist and both are modified:
  - Bound Shield: armor rating 26 -> 28 and Adamant bound-shield enchantment added.
  - Mystic Bound Shield: armor rating 36 -> 34 and the same Adamant enchantment added.
- Six Adamant investor consumables are decoded with value, weight and exact effect tuples.
- Six ammunition records are decoded with projectile, flags, damage, value and weight.

## Guardrails

- Template inheritance is not expanded unless the template record body exists in the snapshot.
- Cosmetic race/face/model data is retained as source evidence but excluded from balance pattern mining.
- Vendor/container contents are distribution evidence, not necessarily a universal design rule.
- No observation is an approved Simonrim rule.
