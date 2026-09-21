# Coldharbour world model — structural and testimonial pass

Continuity: `tes.mod.vigilant`

## Structural worldspaces

The ESM contains distinct worldspaces for:

- `0206C8A8` / `zCHWasteland` — **White Wasteland**
- `0206D275` / `zCHMolagWorld` — **Coldharbour**
- `02078779` / `zCHTrueEndWorld` — **Elder Field**
- `020B2AEE` / `zCHColosseumWorld` — **Arena**
- `022C5DB1` / `zCHOldForestWorld` — **Old Forest**
- `022DA92A` / `zCHWhaleGraceyardWorld` — **Whale Graveyard**

These are implementation facts: the mod treats them as distinct world partitions even when narrative dialogue may describe them as connected dream/Oblivion layers.

## Major named cells presently identified

- **Mathmalatu Priory** (`0207FB11`)
- **Waterfront** memory cell (`02138F9A`) plus numerous Waterfront houses, towers, sewers, shops, and the Prison Tower
- **Malada** and its named sub-sites (`021157FC`, `0211821A`, `0211B381`, `02119953`, `0211BC4B`)
- **Sancremor** tower sub-sites (`0211E11F`, `0211E8D4`, `02120DA9`, `02121AA2`)
- **White-Gold Tower** memory cell (`0228A47A`)
- **Imperial City Prison** memory cell (`0212BE8C`)
- two separate **Aetherius** cells (`021353E4` `zzzCHAetheriusGood`; `02136194` `zzzCHAetheriusBad`)
- **Throne of Order** (`02125B35`)

The duplicate Aetherius cells are a strong implementation clue that the endgame can represent different Aetherius states/outcomes; the exact branching conditions remain a later script/stage task.

## Inquisitor Pepe's account of the wasteland

In `zzzCHMQ00` / *Coldharbour*, Inquisitor Pepe identifies his location as the former **Mathmalatu Priory** of the Alessian Order. He describes the surrounding wasteland as a place where even the blessed and powerful have ended up, and he directs the player through the Waterfront/Imperial City route.

Pepe also claims that:

- Molag Bal is the "playwright" of the tragedy and its inhabitants are puppets;
- Jyggalag's Army of Order has overrun most of the land after the Battle of Weye;
- Molag Bal sustains a barrier by consuming souls;
- the barrier is failing and Greymarch threatens the remaining Imperial City region;
- Varla rules territory after swearing allegiance to Molag Bal;
- the Waterfront repeatedly survived Alessian burnings but later suffered the Thrassian Plague.

These are **named-character testimony**. Some claims are corroborated structurally by Order-themed cells, the Throne of Order, named factions/NPCs, and the geography implemented by the mod, but the historical/cosmological explanations remain Pepe's account until cross-checked against other VIGILANT sources.

## Main-quest endgame evidence

`zzzCHMQ01` / **Aetherius** contains a Molag Bal return form who tells the player that opening the gate has put Aetherius within his reach, thanks the player, and says Stendarr is dead. `zzzCHMQ02` / **Exsultate Jubilate** has Molag Bal frame the encounter as the ending of a dream and ask the player to identify both him and themselves.

This links the physical progression through Coldharbour to the mod's recurring identity/dream problem: the endgame is not only escape or conquest, but a confrontation over **what Molag Bal is, what the player is, and how the dream ends**.

## Open technical questions

- stage/script conditions selecting `zzzCHAetheriusGood` versus `zzzCHAetheriusBad`;
- exact door/reference graph between White Wasteland, Coldharbour, memory cells, Elder Field, and Aetherius;
- how the 13 memory quests gate `zzzCHMQ00/01/02` stages;
- which world-state claims by Pepe are literal current geography versus remembered/constructed history;
- how Jyggalag/Order progression changes the worldspace over time.
