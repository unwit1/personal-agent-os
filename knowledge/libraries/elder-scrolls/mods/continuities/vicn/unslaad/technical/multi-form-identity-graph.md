# Multi-form identity graph

Continuity: tes.mod.vicn.unslaad
Primary source: translated Unslaad.esm 3.0.6

UNSLAAD frequently represents one narrative identity through multiple NPC forms, races, factions, outfits, and quest states.

Lorekeeper should merge at the **narrative identity** layer only where direct evidence supports continuity, while preserving implementation forms separately.

## Ulliss

Forms include:

- 0302525C — Ulliss / Half-Dragon Race / UnslaadFaction
- 030022F6 — Ulliss / Half-Dragon Race / UnslaadFaction
- 03025223 — Ulliss / Skyrim DragonRace / Ulliss Dragon Faction
- 0319BAAC — Ulliss ghost / Half-Dragon Race / UnslaadFaction

Direct dialogue/quest evidence treats these as states/forms of Ulliss.

Safe merge:
- narrative identity = Ulliss

Preserve:
- human/half-dragon form
- dragon form
- ghost form

as distinct implementation/body states.

## Jhunal the Gray / Gray Owl

Jhunal forms:

- 03112A8B — Jhunal the Gray / ghost/Bell-Tower form / UnslaadFaction
- 0309D3E6 — Jhunal the Gray / Owl Faction
- 03161AB5 — wounded Jhunal the Gray / UnslaadFaction
- 0318C84E — Jhunal the Gray / Owl Faction + World Eater Faction / carries Darkstalker's Staff

All use the same base humanoid race implementation.

They also wear Gray-Owl identity outfits/masks across several phases.

Separate body:
- 031DD5B4 — **Gray Owl**
- custom Gray Owl Race
- Owl Faction

Direct dialogue says Jhunal the Gray is the Gray Owl, while Dragon's Peak placement also shows separate Jhunal/Gray-Owl body representations.

Safe model:
- shared/linked narrative identity network;
- multiple bodies/states/representations;
- no forced one-body continuity.

## Aisha

Forms include:

- 0302011D — Aisha / Cat Race / UnslaadFaction
- 03025261 — dead Aisha / Cat Race / UnslaadFaction
- 0319E2FF — ghost Aisha / Cat Race / UnslaadFaction
- 030866E2 — wounded/sabre Aisha / Wound Aisha Race / UnslaadFaction
- 030FBD2E — **Dilon Aisha** / Pus Beast Race / World Eater Faction

The first four are clearly Aisha state variants.

Dilon Aisha is a corrupted/hostile Aisha-named form and should remain a **linked corrupted manifestation**, not silently overwrite ordinary Aisha's identity state.

## Ja'cobee / Fluffy

- 0313878F — Ja'cobee / Kedama Race / UnslaadFaction + merchant Kedama faction
- 03004906 — Fluffy / Kedama Race / UnslaadFaction + merchant Kedama faction

Epilogue dialogue explicitly calls Fluffy **"Ja'cobee of this side."**

Safe model:
- direct identity/continuity relationship;
- separate side/state/form entries retained because the story explicitly distinguishes them.

## Elja / Void-Jill transformation

- 033F2767 — Elja the Void-Jill / humanoid race / 500 Companion + Frost Power factions / full Void-Jill outfit
- 0341691A — Eljaalithathisalif Hate-Fire / Dragonord Gargoyle Race / 500 Companion Faction

The quest implementation treats these as pre-/post-transformation forms.

Safe merge:
- narrative actor = Elja/Jill trial identity

Preserve:
- humanoid Void-Jill state
- transformed Hate-Fire body

## Ysgrim / Ysgramorsbelt

- 033F2794 — Hoary King Ysgrim
- 03414017 — Ysgramorsbelt

Both use:
- custom **Ysgramor Race**
- 500 Companion Faction
- Frost Power Excursion Faction

They carry different relics and different custom Shouts.

The shared race/faction/trial sequence strongly supports one Ysgrim/Ysgramor representation family, while the exact metaphysical relation between phases remains an implementation/narrative question.

## Khev the Dreugh King

- 033D8503 — Khev hologram/source form
- 03407434 — Khev boss form

Both use:
- Dreughman Race
- Lyg Crab Faction
- Muatra combat form

The boss additionally belongs to 500 Companion and Frost Power factions.

Safe merge:
- narrative identity = Khev the Dreugh King

Preserve:
- hologram/recording form
- boss/combat form

## Identity policy

Merge narrative identity only when supported by:
- dialogue;
- quest aliases;
- explicit same-name state transitions;
- shared implementation plus direct narrative continuity.

Do not merge solely from:
- same race;
- same faction;
- same equipment;
- same display name;
- same model.

This is especially important in VICN's repeated-body, mask, memory, dream, and timeline material.

## Merge confidence classes

Use three merge states:

### Confirmed narrative identity
Direct dialogue/quest transition supports one actor across forms.
Examples:
- Ulliss;
- ordinary Aisha state forms;
- Khev hologram/boss;
- Ja'cobee/Fluffy relationship as explicitly described by the epilogue.

### Linked manifestation
The source strongly links forms but preserves a meaningful body/state distinction.
Examples:
- Jhunal the Gray / separate Gray Owl body;
- Dilon Aisha;
- Elja / Hate-Fire transformation;
- Ysgrim / Ysgramor trial family.

### Implementation similarity only
Same race, faction, outfit, spell, display name, or model without direct continuity evidence.

Lorekeeper must not promote this third class into identity.

This classification is especially important for VICN, where deliberate repetition of bodies, masks, names, and roles is part of the narrative design.
