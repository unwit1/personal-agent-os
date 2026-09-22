# Race and faction ontology — first technical pass

Continuity: tes.mod.vicn.unslaad

This page records only high-value custom implementation groupings. Creation-Kit races and factions can be technical containers and must not be treated automatically as metaphysical species or social organizations.

## Half-Dragon forms

### Half-Dragon Race — 030022F5
Named members include:
- Ulliss — multiple human/ghost forms;
- Austella — living and ghost forms;
- Hoarfrost Witch.

### Half-Dragon Child Race — 030CE5EF
Named member:
- Lizz.

Ulliss's dragon form uses Skyrim DragonRace instead of the Half-Dragon race.

Thus the implementation explicitly supports multiple bodily forms under one narrative Ulliss identity.

## Owl forms

### Gray Owl Race — 031DD5B1
Used by the secret-boss **Gray Owl**.

### Black Owl Race — 031DFE13
Used by **Black Owl**.

Human/Jhunal-looking Gray-Owl forms use a different base race while joining Owl Faction.

Therefore race is not a safe proxy for Owl identity.

## Dreugh / Lyg forms

### Dreughman Race — 033CDD38
Members include:
- Khev the Dreugh King;
- Khev hologram/source form;
- Molag the Lord of Lies;
- Dreugh.

These actors also participate in Lyg Crab Faction.

## Ysgramor forms

### Ysgramor Race — 033F2788
Members:
- Hoary King Ysgrim;
- Ysgramorsbelt.

This is direct implementation support for treating those boss phases as one Ysgrim/Ysgramor representation family, while not requiring them to be one physical body.

## Woodland / Sinak forms

Separate custom races exist for:
- Mal-Sinak;
- Rein-Sinak;
- Ru-Sinak;
- Pogaan-Sinak

and their larger/toor variants.

Many are members of Owl Faction and drop Woodland Man Roots.

This is a strong implementation bridge among Sinak creatures, Woodland material, and the Owl network.

## Manakin Race — 03350B98

This broad race includes many visually/humanoid special actors such as:
- Idol of Magnar;
- Mnegmegh the Banner-Lamp;
- Clone of Ayrenn;
- Hermit;
- Snow Guardian Jokul;
- Atmoran Idol;
- Domhnall the Royal Guard;
- Forgotten Prisoner;
- Scab the Executioner.

Because the membership is narratively heterogeneous, **Manakin Race is clearly not a single in-world species claim**.

## Key lesson

Use:
- race = body/model/behavior implementation evidence;
- faction = alliance/hostility/package implementation evidence;
- dialogue/quests/placed lore = narrative identity evidence.

Only merge those layers when multiple sources agree.

## Full custom-race catalog

The exhaustive lore-facing custom-race index is now stored at:

- indexes/custom-race-catalog.md

It records all **57 custom RACE records used by named NPC forms**, with FormID, EditorID, named-form count, and representative users.

The named NPC form layer is separately sharded across:
- indexes/npc-forms-a-f.md
- indexes/npc-forms-g-m.md
- indexes/npc-forms-n-s.md
- indexes/npc-forms-t-z.md
- indexes/npc-form-families.md

Together these indexes make race/body changes and duplicate-name states explicit instead of relying on name matching.
