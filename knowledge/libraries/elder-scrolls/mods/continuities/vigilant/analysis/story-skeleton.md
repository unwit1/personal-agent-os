# VIGILANT story skeleton — first record-derived pass

This page deliberately stops short of a finished lore interpretation. It records the narrative architecture visible directly in `Vigilant.esm` so later dialogue, books, scenes, aliases, and conditions can be layered onto a stable provenance base.

## Source boundary

Primary evidence is the user-provided `Vigilant.esm` by Vicn (header version `182`), dependent on `Skyrim.esm` and `Update.esm`. VIGILANT is treated as `tes.mod.vigilant`, an explicit mod continuity. References to established Elder Scrolls figures do not make VIGILANT-specific events or explanations part of Bethesda base canon.

## Major quest strata visible in the ESM

### Vigilant / Altano chain (`zzzAoMMq00`–`zzzAoMMq10`)

The numbered quest records form an obvious primary sequence by EditorID. They begin with **Vigilant of Stendarr**, whose objectives have the player join the Vigilants and meet Altano, then continue through **Bloodsucker**, **He Who Cannot Be Touched**, **Lazy Afternoon**, **The Eye of Madness**, **Dine and Dash**, **Thus Spoke Khajiit**, **Old Regrets**, **No Mercy**, **The Endless Fall**, and **The Landing**.

The objective text establishes recurring involvement by **Altano**, encounters with Daedra and vampires, a hunt for witches, conflict involving **Molag Bal**, and a late objective to destroy the **Mace of Molag Bal**. Motives and causal interpretation should come from dialogue and scene ordering rather than quest titles alone.

### Blood Matron chain (`zzzBMMq01`–`03`)

The records **Empty Cells**, **Remnants**, and **The Blood Matron** form a compact numbered sequence. The final quest explicitly names **Lamae Bal** in its aliases/objectives and includes both defeating her and freeing her from Molag Bal's curse.

### Bruiant / Child of Oblivion layer (`zzzCOMq01` and related `zzzCO*` records)

**Child of Oblivion** sends the player to **Gwyneth**, then the **Bruiant Mansion**, asks the player to investigate an incident, defeat **Julius**, and escape. Related CO records include a generic-dialogue quest, a guide quest, and **Successor**. The plugin contains multiple journals, letters, reports, and notes tied to this mansion/story cluster.

### Coldharbour layer (`zzzCH*`)

`zzzCHMQ00` is explicitly named **Coldharbour**, followed by `zzzCHMQ01` **Aetherius** and `zzzCHMQ02` **Exsultate Jubilate**. Around that spine sits a much larger body of memory quests, side quests, bosses, NPCs, books, and world/cell content.

The memory-quest titles directly invoke or allude to major historical/mythic figures and episodes: **The Grand Inquisitor**, **The Mad King**, **Knight of Hounds**, **Johan the Fool**, **Adabal**, **Remains of the Miracle**, **Temptation of Marukh**, **The Nameless Bard**, **Beyond the Shores of Madness**, **Pelinal the Bloody**, **After the Storm**, **The Final Night**, and **Paravania the Man-Bull**. Separate records include **Alessia**, **Pelinal Whitestrake**, **Morihaus**, **Belharza**, **Marukh**, **Jyggalag**, and many others. These are VIGILANT representations/testimony until compared against base-canon sources.

### Alternate/skip routing

Two quests, **Spinner's Needle 1** and **Spinner's Needle 2**, explicitly contain objectives saying they can **skip to Act 4**. One route involves stabbing **Altano** before he reaches the Temple; another involves stabbing **Bal** before entering the mansion; both direct the player to **Orlando** and then to press forward.

## High-priority entities for the next normalization pass

**Altano**, **Orlando**, **Molag Bal/Bal**, **Lamae Bal**, **Gwyneth**, **Julius**, **Alessia**, **Pelinal Whitestrake**, **Morihaus**, **Marukh**, **Belharza**, **Carene**, and the recurring Coldharbour bosses/saints should be resolved first.

## Evidence still needed before a full story synopsis

1. Resolve INFO speakers and branch ownership for all 1,225 INFO records / 1,698 response strings.
2. Parse SCEN records and quest aliases to reconstruct scene order and actor roles.
3. Separate narrative books/notes from spell tomes and inventory-only BOOK records, then connect document evidence to quests/locations.
4. Build identity clusters for duplicate NPC forms and transformed/boss/summon variants.
5. Reconstruct Coldharbour location graph from worldspaces, cells, doors, and placed references.
6. Compare VIGILANT claims about canonical figures/events to base Elder Scrolls evidence without flattening contradictions.
