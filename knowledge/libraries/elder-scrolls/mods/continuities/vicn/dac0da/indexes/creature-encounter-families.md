# DAc0da creature / encounter family index

**Continuity:** `tes.mod.vicn.dac0da`  
**Source:** `DAc0da.esm`

This index records meaningful actor families and named transformations. It intentionally omits many level-scaled duplicates unless they add a distinct morphology, title, identity, or narrative role.

## Jills

DAc0da defines three main Jill actor variants:

| Source | Editor ID | FULL | Use |
|---|---|---|---|
| `00B75D` | `zDcdEncJill` | Jill | standard scripted encounter |
| `00B762` | `zDcdEncJillNoScript` | Jill | non-scripted encounter variant |
| `00C9EF` | `zDcdEncJillNoScriptQuiet` | Jill | quiet/non-scripted variant |

Multiple Jill actors are physically placed in **Mozarella Spacetime / Blind Realm**, surrounding the alternate Sheogorath and bitten Rolls-On-Roads forms.

That placement strongly supports the Rella Mozzarella route's interpretation of the Blind Realm as an active Jillian censorship/correction space.

## Yaghra base morphologies

DAc0da uses several recurrent Yaghra body plans:

- **Yaghra** — ordinary melee form
- **Yaghra Shaman**
- **Yaghra Matron**
- **Yaghra Larva**
- **Yaghra Strider**
- **Yaghra Warrior**
- **Yaghra Sitter**

These are implemented as separate races/encounter families rather than one generic enemy skin.

### Named Yaghra individuals

Several Yaghra subbosses have personal names/titles:

| Source | FULL | Race / form | Placement |
|---|---|---|---|
| `005DFD` | **Bar'zay the Wizard** | Yaghra | Yaghra Breeding Ground |
| `005E30` | **Bo'nan the Yaghra Champion** | Yaghra Draugr | Yaghra Breeding Ground |
| `005E3B` | **Ha'seg the Wise** | Yaghra Spider | Yaghra Breeding Ground |
| `005E7B` | **Anares the Daughter of Khev** | Yaghra Matron | Yaghra Breeding Ground |
| `005EE8` | **Ab'voon the Egg Keeper** | Yaghra Worm | Disposal Cave |

The personal names, kinship title (**Daughter of Khev**), occupational titles, and “Wise/Champion/Wizard/Egg Keeper” roles show that DAc0da does not present every Yaghra merely as anonymous fauna.

The records do not by themselves establish a complete Yaghra society or language, so the safe inference is simply that the mod contains individualized/named Yaghra roles.

## Yaghra chimera / Agent line

Major forms:

- `0043F6` — **Yaghra Chimera - The Agent**
- `004410` — **The Agent**
- `00458C` — **Yaghra Bioborg - The Agent**
- `0048BB` — summon **Yaghra Chimera - The Agent**
- `0043F7` — **Yaghra Chimera Prototype**
- `0053F6` — mutated prototype expressed as **Yaghra Strider**

The Agent family is indexed separately in `characters/the-agent-yaghra.md`.

The prototype forms are physically placed in the **Disposal Cave** where Athanasius is found, tying the chimera experiments directly to the Sload/Yaghra processing route.

## Sload

### Base combat/caster forms

DAc0da distinguishes:

- **Sea Sload**
- **Sea Sload Psychomancer**
- **Sload Necromancer**
- **Sload Druglord**
- **Sload Zombie**

This matches the broader quest evidence for mind magic, necromancy, drug/psychotherapy language, and body alteration.

### Named Sload

- `00306C` — **N'Danda**
- `005161` — **Zombified N'Danda**
- `005EBA` — **U'tulka**

N'Danda's zombified form is physically placed in **Neo-Thras Capital**.

### Sload Floater

`00CE3D` / `zDcdTemplateSloadRadio` is named **Sload Floater** and is used by the Sload Radio layer.

The broader dialogue repeatedly treats floaters as airborne Sload vessels/platforms.

## Dreugh / Hahd

DAc0da's named Dreugh-family forms are tightly centered on Yu'qbar:

- `000D74` — **Templar of Hahd Yu'qbar**
- `000D75` — **Templar of Hahd** treasure/corpse form
- `006087` — ghost **Templar of Hahd Yu'qbar**

The small number of dedicated forms contrasts with the large Yaghra/Sload combat families and supports Yu'qbar's role as a specific cultural witness rather than a generic Dreugh faction encounter.

## Dragons and draconic forms

### Golden dragon thread

- `0033BC` — unnamed golden dragon **???**
- `005036` — **Tsuunalinfaxtir**

The first is used by Golden Dragon Flight; the second is the named golden dragon at the Drowned Nighthawk climax.

Their shared archetype/visual setup supports a narrative relationship, but distinct FormIDs mean exact same-actor identity remains an evidence comparison rather than a raw-record fact.

### Atmoran dragon-hybrid forms

DAc0da defines:

- `zDcdTempleteDragonNordM` — **Draco-Nord**
- male/female Draco-Nord encounter families
- `0051B1` — **Haalj the Half-Drake**, race **Weredrake**

Haalj's form is especially important because his dialogue history says he was born to a **Snow Drake**.

### Worm / necromancer dragon

`003104` — **Worm's Midwife**

- race: Zombie Dragon
- used as the Boss alias of `zDcdSqWormSub02` — **Group Battle: The Sload City**
- physically placed in the Neo-Thras sub-region

This makes the Sload-city battle's boss a deliberately necromantic/dragon hybrid rather than an ordinary dragon.

## Mnemic Warder

`005501` / `zdcdSubBossFleshHuskBlue`:

- FULL: **Mnemic Warder**
- race: Flesh Husk
- placed in **Ul'voric 2nd Neural Corridor**

The name and placement make it a useful encounter marker for the Sload neural/memory-processing environment.

The actor record alone does not define its metaphysical relation to mnemolichite; that connection should remain contextual rather than asserted as identity.

## Atmoran / Snow-Elf combat families

DAc0da also defines broad contextual encounter groups:

- **Atmoran Warrior**
- **Atmoran Archer**
- **Atmoran Clever-Man**
- **Wintercaller Soldier**
- **Wintercaller Mage**

Named actors such as Hgelhelm, Haalj, and Sindwen should be preferred for historical claims; generic combat-family names establish the existence of organized opposing forces but not individual testimony.

## Retrieval rule

Use this index when a lore question depends on:

- whether two differently named actors are variants of the same character;
- whether a creature family has distinct roles/morphologies;
- whether a named transformation is implemented as a separate race/form;
- where a boss or transformed actor is physically placed.

Do not infer culture, intelligence, or chronology solely from combat-class names when dialogue or quest evidence is absent.


## Worm Cult / necromancer forces

DAc0da distinguishes several recurring Black-Worm combat roles:

- **Worm Spellsword**
- **Worm Knight**
- **Worm Assassin**
- **Worm Berserker**
- **Worm's Sacrifice**
- **Worm's Midwife**

Named Worm Anchorites:

- `0043CE` — **Bolor Savel the Worm Anchorite**
- `0043D0` — **Mercator Hosidus the Worm Anchorite**
- `0043D1` — **Camilla Lollia the Worm Anchorite**

Important boss/state forms:

- `003104` — **Worm's Midwife**
- `003075` — **Mannimarco the God of Worms**
- `00606E` — **Necromancer's Moon**

These forces cluster around the Sload-city / Revenant-Gate side of **Echoes of Mnemolichite**.

## Goldborn

DAc0da defines a distinct gold/bone encounter ecology:

- **Goldborn**
- **Goldborn Crawler**
- **Goldborn Wheeler**
- **Goldborn Guardian**
- **Goldborn Colossus**
- **Goldborn Skirmisher**
- **Goldborn Storm**

Representative source forms:

- `005F2A` — Goldborn
- `005F59` — Goldborn Crawler
- `005F61` — Goldborn Wheeler
- `005F53` / `005F56` — Goldborn Guardian
- `005F52` — Goldborn Colossus
- `005FC2` — Goldborn Skirmisher
- `005FD8` — Goldborn Storm

Many also have separate summon and auto-delete variants. Their encounter-family structure is concrete; their exact metaphysical origin should remain quest-contextual rather than inferred from the gold/bone naming alone.

## Dwemereth / Dwemer encounter family

DAc0da defines humanoid Dwemer-derived or Dwemer-associated roles including:

- **Dwarven Warrior**
- **Dwarven Worker**
- **Dwarven Architon**
- **Dwemer Specter**
- **Nchunak the Evangelist**
- **Nchunak the Second**
- **Dumac's Tonalframe**
- **Mecha-Kanra**

Representative forms:

- `0084E9` — Dwarven Warrior
- `0084F7` — Dwarven Worker
- `008585` — Dwarven Architon
- `00CBF9` / `00CBFC` — Dwemer Specter
- `006B69` — **Nchunak the Evangelist**
- `00858C` — **Nchunak the Second**
- `00B1F8` — **Dumac's Tonalframe**
- `00D024` — **Mecha-Kanra**

The separate worker/warrior labels are useful machine-world role vocabulary. Named boss forms should be analyzed individually rather than treated as generic species representatives.

## Apocryphal encounter family

DAc0da implements an Apocrypha-linked combat ecology inside the Numidium material:

- **Apocryphal Hound**
- **Apocryphal Hunter**
- **Arcanist**
- **Frayed Fate**

Representative forms:

- `0085A7` — Apocryphal Hound
- `0085B2` — Apocryphal Hunter
- `00B217` — Arcanist
- `00CBC6` — Frayed Fate
- `00CBCF` — Arcanist summon

These forms support the MQ04 evidence that Apocryphal contamination has entered Numidium and is being isolated into an Adjacent Place.
