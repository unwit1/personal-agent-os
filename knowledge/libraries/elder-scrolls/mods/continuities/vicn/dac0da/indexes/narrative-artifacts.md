# DAc0da narrative artifact index

**Continuity:** `tes.mod.vicn.dac0da`  
**Source:** `DAc0da.esm`

This index includes items whose names, quest ownership, placement, or inventory relationships carry narrative meaning. Routine combat loot is excluded.

## Yngol / Atmora

### Ahzidal's Runic Bracelet

- `DAc0da.esm:00434F`
- Editor ID: `zDcdArmorYngolBracelet`
- FULL: **Ahzidal's Runic Bracelet**

The form is directly referenced by `zDcdSqYngol` — **Drowned Nighthawk**.

Yngol's dialogue says the runic bracelet was given to him by the famous Saarthal enchanter who now calls himself **Ahzidal**. The item record provides structural support that the bracelet is an actual quest object, not only a spoken anecdote.

### Yngol's Forgehammer

- `DAc0da.esm:004335`
- FULL: **Yngol's Forgehammer**
- description: **Damage increases with smithing skill level.**

The item is directly placed in the Yngol epilogue reward chest `zDcdTreasAtmoranChest_YngolHammer`.

This makes it branch-aftermath evidence tied to the Yngol epilogue state.

## Abnur Tharn / Varen Aquilarios

### Varen Aquilarios' Shield

- `DAc0da.esm:00CEF9`
- Editor ID: `zDcdArmorRyRShield`
- FULL: **Varen Aquilarios' Shield**

The form is directly referenced by `zDcdEpiQAbnur` — the Abnur epilogue.

Abnur's will says he leaves the **Shield of Varen Aquilarios** to the player. The concrete armor form confirms that the bequest is implemented as a real reward artifact.

## Prisoner / nymic objects

### Bendu Olo Olo

- `DAc0da.esm:00CEFF`
- Editor ID: `zdcdItemNamePrisoner`
- record type: MISC
- FULL: **Bendu Olo Olo**

The quest `zDcdSqPrisoner` stores this form in a script property named **NymicObj**.

A companion MESG record `DAc0da.esm:00CEFD` also displays **Bendu Olo Olo**.

This is strong structural evidence for a tangible name/nymic object in **In Grabbers' Hands**. The exact runtime rename behavior remains unavailable without compiled/source Papyrus.

### Book of the Prisoner

- `DAc0da.esm:00CF00`
- Editor ID: `zDcdPrisonerBook`
- record type: MISC
- FULL: **Book of the Prisoner**

The quest creates this object on/relative to the selected Boss alias and advances when the player acquires it.

Together with `NymicObj`, it is part of DAc0da's mechanical **stolen-name / Prisoner** sequence.

## Seven abstract Totems

DAc0da defines seven MISC objects used by **Cheese Party**:

| Source | FULL |
|---|---|
| `004F91` | **Totem of Sarcasm** |
| `004F90` | **Totem of Obsession** |
| `004F8F` | **Totem of Innocence** |
| `005F58` | **Totem of Divinity** |
| `005F57` | **Totem of Lamentation** |
| `00634C` | **Totem of the Prisoner** |
| `00CC5D` | **Totem of Entanglement** |

Sheogorath's dialogue gives several of these conceptual/identity associations:

- Divinity appears with **Reman's face**.
- Lamentation is a crying figure and prompts Mara/Mannimarco references.
- Prisoner has **no face** and is accused of hiding inside a shell.
- Entanglement is told it does not know who it is and has never been a person before.

These associations come from the quest dialogue, not merely the editor IDs.

### Agent loot connection

`Totem of Obsession` is present in the dedicated MQ01 **Agent ash pile**.

Several later **Entangled Agent** containers also contain or reference Totem-related material.

This makes the Totem system part of DAc0da's broader Agent/identity/possibility imagery rather than a completely isolated Sheogorath joke, while exact one-to-one identities remain unresolved.

## Mannimarco / Worm artifacts

### Rod of the Worm

- `DAc0da.esm:003077`
- FULL: **Rod of the Worm**
- description: **Bashing raises a corpse. Summon limit +2.**

### Staff of the Worm

- `DAc0da.esm:006070`
- FULL: **Staff of the Worm**
- description: **Bashing raises a corpse. Summon limit +1.**

The two separately named implements fit DAc0da's distinction between Mannimarco's mortal/corporeal and divine/God-of-Worms states, but the item records alone do not prove which metaphysical state each weapon uniquely belongs to.

## Zurin Arctus / Underking

Named weapon forms include:

- `0049EF` — **The Underking's Blade**
- `009BDD` — **Wilt-Flower Saber**
- `009BDE` — **Wilt-Flower Greatsaber**
- `009BDF` — **Wilt-Flower Greatsaber (Dual)**

The dedicated Zurin boss form carries the dual Wilt-Flower weapon.

These items are combat/form evidence for the Zurin encounter; their names should not be treated as independent historical sources for Zurin's official biography.

## Dumac

DAc0da defines a full **King Dumac** equipment set, including:

- King Dumac's Boots
- King Dumac's Armor
- King Dumac's Gauntlets
- King Dumac's Helmet
- King Dumac's Cloak
- `00B1F4` — **King Dumac's Sword**
- `00B1F5` — **King Dumac's Greatsword**
- `00B409` — **Dumac's Gear**

The separate summon BOOK is explicitly titled **Lexicon: Dumac's Tonalframe**.

This supports the quest's own distinction between the historical Dumac and the manifested **Dumac's Tonalframe** actor.

## Kagrenac

DAc0da defines:

- **Kagrenac's Hat**
- **Kagrenac's Robes**
- **Kagrenac's Gloves**
- **Kagrenac's Boots**
- `00B3DA` — **Kagrenac's Left Arm**
- `00B3DF` — **Kagrenac's Right Arm**

The Right Arm is mechanically a crossbow-like weapon whose attacks ignore armor.

These are DAc0da artifact/equipment forms associated with its expanded Dwemer technology layer; their presence does not independently establish that the historical Kagrenac literally possessed these exact game-item forms.

## Retrieval rule

Artifact evidence is strongest for:

- proving that a spoken item is concretely implemented;
- tying an item to a quest/character reward state;
- distinguishing alternate actor/loadout forms;
- tracing repeated identity symbols such as the Totems.

Do not use combat enchantments or editor IDs alone to construct historical lore without supporting dialogue, quest, or written evidence.


## Tsaesci / dragon-hunting weapons

### Brah-Sagari

- `DAc0da.esm:00315A`
- Editor ID: `zDcdIchKatana1H`
- FULL: **Brah-Sagari**
- description: **Especially effective against dragons.**

### Tino-Ri

- `DAc0da.esm:00315B`
- Editor ID: `zDcdIchKatana2H`
- FULL: **Tino-Ri**
- description: **Especially effective against dragons. Power attacking creates an air blade.**

These weapons provide mechanical support for Akashiya-Samon's Dragonguard/dragon-hunter role.

## Snow-Drake / Auri-El halberds

### Snow Drake Halberd

- `DAc0da.esm:004359`
- FULL: **Snow Drake Halberd**
- description: **Bashing creates an ice storm.**

### Auriel's Halberd

- `DAc0da.esm:00435A`
- FULL: **Auriel's Halberd**
- description: **Bashing creates a thunderbolt.**

These belong to the Snow-Drake/Snow-Elf/Atmoran encounter layer and should be co-retrieved with **Drowned Nighthawk** and the Wintercaller material.

## Tsa the Dozing Rat idols

DAc0da defines three recurring MISC objects:

- `004730` — **Idol of Tsa the Dozing Rat**
- `004732` — **Silver Idol of Tsa the Dozing Rat**
- `004731` — **Golden Idol of Tsa the Dozing Rat**

These appear in Atmoran/random totem reward pools, including the Yngol epilogue chest through `zDcdLitemTotem`.

No processed dialogue has yet established a full identity or cult explanation for **Tsa the Dozing Rat**, so the objects should remain an indexed cultural/reward motif rather than a completed theological claim.

## Additional Underking equipment

- `DAc0da.esm:00B40B`
- Editor ID: `zDcdArmorZurinBodyPlayable`
- FULL: **The Underking's Hatred**

The item name belongs to DAc0da's Zurin/Underking combat symbolism and should not be treated as an independent historical title without supporting dialogue.
