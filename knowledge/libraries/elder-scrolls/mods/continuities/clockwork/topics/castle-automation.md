# Castle automation and domestic systems

Continuity: `tes.mod.clockwork`  
Topic type: technology / domestic infrastructure

Clockwork Castle's automation extends well beyond the Travel Machine. Dialogue and interactive records show a house designed to reduce routine labor across transport, storage, hygiene, food, crafting, and display.

## Pneumatic transport

The pneumatic tube network can route items between castle rooms. The ESP includes separate controls for transferring receptacle contents to the:

- Mage's Study
- Work Room
- Kitchen
- Travel Room
- Armoury

It also has inventory-sorting controls that move appropriate carried items into room-specific storage.

Evidence: Lahar's pneumatic-terminal tour; `ACTI 0503E9F5` through `0503E9FF`.

## Automatic/category sorting

The castle contains dedicated interactables for:

- alchemical ingredients → specimen cabinets
- soul gems → vacant/filled soul-gem cabinets
- food → categorized barrels
- smithing materials → material containers
- scrolls → scroll chest
- books/documents → alphabetized bookcases

The Mage's Study bookcases are explicitly divided alphabetically A through Z in the container records.

Representative evidence:
- `ACTI 0502C6A9` — Sort Alchemy Ingredients Into Cabinet
- `ACTI 0502C6AB` — Sort Soul Gems Into Cabinets
- `ACTI 0502CC23` — Sort Food Into Barrels
- `ACTI 05038DDC` — Sort Smithing Materials Into Containers
- `ACTI 0502D712` — Sort Scrolls Into Chest
- `ACTI 0502DC83` — Sort Books Into Bookcases
- `CONT 0502BBCC` through `0502C145` — alphabetized bookcase set

## Crafting infrastructure

Named records include:
- `FURN 053B74EE` — Dwemer Forge
- `FURN 053B7530` — Dwemer Smelter
- `ACTI 05319855` — Arcane Enchanter
- `ACTI 05319851` — Alchemy Lab

The Staff Enchanter is an additional optional post-restoration upgrade constructed by Lahar.

## Armoury as archive/museum

Lahar describes part of the Armoury as a museum where he places mementos of the player's accomplishments in Skyrim. The ESP supports this with weapon/claw/mask mounts and multiple **Heraldic Shield** messages tied to thane achievements.

This makes the castle not only a home but a personalized archive of the player's external history.

Evidence: Armoury tour dialogue; `ACTI 0508B961`, `0508E5A9`, weapon-rack activators; `MESG 0508DA66`–`0508DA6D` and `0508D4F2`.

## Interpretive significance

The house's systems repeatedly remove the need for repetitive physical labor. That is convenient for the player, but it also reinforces Ludwig's story: the same infrastructure can make extreme isolation materially sustainable.

## Record-level network maps

The implementation layer now preserves the exact routing graphs rather than only named controls:

- `../technical/pneumatic-network.md` — Pneumatic Tube Receptacle endpoints and transfer/sort edges.
- `../technical/travel-machine-network.md` — Travel Room destination selector and portal graph.

Both systems depend on castle machinery state, reinforcing that the restored steam network is a shared infrastructure layer rather than a set of unrelated conveniences.
