# Summon-chain audit

Continuity: tes.mod.vicn.unslaad
Primary source: translated Unslaad.esm 3.0.6

A deterministic BOOK -> SPEL -> MGEF -> associated NPC pass resolves **32 summon-teaching records**.

The chain is structural, not name-based:
1. BOOK DATA points to the taught SPEL.
2. SPEL EFID points to the summon MGEF.
3. MGEF DATA associated-item points to the summoned NPC form.

## Complete resolved list

1. Spell Tome: Conjure Yah Miin -> Yah Miin
2. Spell Tome: Conjure Pogaan-Sinak -> Pogaan-Sinak
3. Spell Tome: Conjure Ru-Sinak -> Ru-Sinak
4. Spell Tome: Conjure Rein-Sinak -> Rein-Sinak
5. Spell Tome: Conjure Mal-Sinak -> Mal-Sinak
6. Spell Tome: Conjure Mal Brendon -> Mal Brendon
7. Spell Tome: Conjure Brendon -> Brendon
8. Spell Tome: Conjure Pot Boy -> Pot Boy
9. Spell Tome: Conjure Black Soul Gem Pot Boy -> Black Soul Gem Pot Boy
10. Spell Tome: Conjure Soul Gem Pot Boy -> Soul Gem Pot Boy
11. Spell Tome: Conjure Dwemer Pot Boy -> Dwemer Pot Boy
12. Spell Tome: Conjure Silver Pot Boy -> Silver Pot Boy
13. Spell Tome: Conjure Golden Pot Boy -> Golden Pot Boy
14. Beast Bone: Warrior of Tsun -> Warrior of Tsun
15. Beast Bone: Storm Atronach Bear -> Storm Atronach Bear
16. Spell Tome: Conjure Lesion -> Lesion
17. Spell Tome: Conjure Dilon -> Dilon
18. Spell Tome: Conjure Hoarfrost Guardian -> Hoarfrost Guardian
19. Dragon Bone: Draco-Nord Sahqon -> Draco-Nord Sahqon
20. Dragon Bone: Draco-Nord Fonaar -> Draco-Nord Fonaar
21. Spell Tome: Conjure Dilon Sivaas -> Dilon Sivaas
22. Dragon Bone: Stamina Devourer -> Stamina Devourer
23. Dragon Bone: Magicka Devourer -> Magicka Devourer
24. Dreugh Egg: Hor Warrior -> Hor Warrior
25. Dreugh Egg: Hor Priest -> Hor Priest
26. Spell Tome: Conjure Dagonic Watcher -> Dagonic Watcher
27. Spell Tome: Conjure Giant Hoarfrost Guardian -> Giant Hoarfrost Guardian
28. Spell Tome: Conjure Dragon Pus -> Dragon Pus
29. Spell Tome: Conjure Evenaar -> Evenaar
30. Dragon Bone: Draco-Nord Veddu -> Draco-Nord Veddu
31. Spell Tome: Conjure Freezing Enbarr -> Freezing Enbarr
32. Dragon Bone: Rackety-Nix -> Rackety-Nix

## Implementation pattern

Many summoned forms share a race and display identity with hostile/boss forms while omitting hostile factions and, frequently, custom death loot.

Examples:
- Sinak summons share exact Sinak custom races with Owl-Faction hostile forms.
- Hor Priest/Warrior summons share Dreugh custom races with Lyg-Crab-Faction hostile forms.
- Dagonic Watcher summon shares Watcher Race with Dagon-Faction Watchers.
- Draco-Nord summons share Dragonord Gargoyle Race with 500-Companion hostile variants.
- Warrior of Tsun summon shares Atmoran Bear Race with the trial boss.
- Freezing Enbarr summon shares horse race with the hostile Frost-Power version.

Therefore the safe relation is generally:
**summoned proxy/form of the same creature archetype**, not automatically the original individual encountered elsewhere.

## Guardrail

Do not infer from a summon spell alone that:
- the summoned actor is the exact historical/boss individual;
- faction membership carries over when the summon form lacks it;
- a summon copy has the same death-history or social allegiance as the hostile form.

The race/name/form relationship is implementation evidence; individual identity requires more.
