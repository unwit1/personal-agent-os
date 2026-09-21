# Coldharbour manifestation and encounter classes

Continuity: `tes.mod.vigilant`

This page separates **what a character historically was** from **how VIGILANT implements that character in Coldharbour**.

That distinction is necessary because Act 4 repeatedly reuses historical identities through Soul-Shriven variants, transformed races, memory forms, summons, corpses, relic caches, and boss manifestations.

## Soul-Shriven

Structural anchors:
- `FACT 025738DF` — **Soul-Shriven**
- `SPEL 0251651F` — **Soul Shriven abilities**
- `QUST 0251532C` — **Feral Soul-Shriven**
- `ACTI 0251532D` — **Soul-Shriven** trigger
- `CHRqSoulShrivenTRGScript`

The Feral Soul-Shriven system can instantiate named historical or themed identities by assigning an NPC base through the trigger's `SvBase` property.

Examples include:
- Judo of the Order of Diagna;
- Radokhan Tharn;
- Ortutay Tharn;
- Marosi Tharn;
- many other named variants.

### Modeling rule

A Soul-Shriven implementation is primarily:
- an encounter class;
- a Coldharbour ontological state;
- a reusable spawn/template system.

It does **not** erase the character's other historical identity.

For example:

**Judo → historical/thematic identity: Order of Diagna**

and simultaneously:

**Judo → Coldharbour implementation: named Soul-Shriven variant**

Those statements can both be true.

## Alessian Sleeper

Structural anchor:
- `RACE 020818A6` — **Alessian Sleeper Race**

Present-day Inquisitor Pepe and his later memory form use this race.

The race uses a Hagraven-based skeleton/animation implementation and a custom Pepe body/skin.

Other Alessian Sleeper/Inquisitor forms also use the race.

### Modeling rule

Alessian Sleeper should be treated primarily as a **transformed body/manifestation class**, not automatically as a political faction.

Shared race does not prove:
- all users belong to one historical unit;
- they transformed through exactly the same mechanism;
- they share ideology;
- they are one species in ordinary biological terms.

For Pelan/Pepe specifically, the ESM provides a character-level explanation:
- earlier memory forms remain humanoid;
- later Pepe uses Alessian Sleeper Race;
- Pepe says he held the Stone too long and became a soulless monster.

That explanation should not be generalized to every Sleeper without evidence.

## Memory forms

VIGILANT's thirteen major Act 4 memory quests use multiple NPC variants and scene roles for figures such as:
- Pepe/Pelan;
- Marukh;
- Pelinal;
- Morihaus;
- Alessia;
- Molag Bal;
- Dro'Zel;
- Lamae.

The memory sequence explicitly contains:
- altered memories;
- dream recursion;
- waking souls forgetting;
- visitors “not of this time and place”;
- unstable identities.

### Modeling rule

A memory-form NPC is evidence for:
- what that memory depicts;
- who the scene structurally assigns to a role;
- what that speaker says within the memory.

It is not automatically evidence that the depicted event happened exactly that way in neutral history.

Use source class:
- **memory testimony**
or
- **manipulated/unstable memory**
when appropriate.

## Boss manifestations

Several historical identities appear as boss forms long after their supposed historical endpoint.

Examples include:
- Sorcerer Manthar / Bone Lord;
- Amicus Tharn;
- Menta-Na;
- Ritho;
- other Act 4 boss identities.

A boss implementation proves:
- the game presents that named identity in combat;
- associated race/equipment/location/quest ownership.

It does not automatically prove:
- literal bodily survival from the historical era;
- resurrection;
- reincarnation;
- memory embodiment;
- Coldharbour reconstruction.

Those mechanisms must be established separately.

## Summon forms

VIGILANT sometimes creates summonable versions of named figures.

Example:
- defeating Bone Lord Manthar can yield **Necromancy Tome: Sorcerer Manthar**;
- the tome teaches **Conjure Sorcerer Manthar**;
- the summon uses a stripped-down Bone Lord-form Manthar NPC.

### Modeling rule

A summon form should be treated as a **gameplay representation derived from an identity**, not independent proof of another historical incarnation.

## Corpse and relic representations

VIGILANT often represents one identity simultaneously through:
- corpse containers;
- bones;
- rings;
- keys;
- masks;
- named relics;
- surviving or transformed NPC forms.

Jhunal is the clearest example:
- surviving Jhunal the Owl;
- three Pieces of Jhunal;
- separate Jhunal corpse/relic cache;
- Bone of Jhunal;
- Silver and Golden Rings;
- Jhunal's Egg;
- Arcana of Jhunal.

### Modeling rule

Do not force these into a simple:
**alive → died → resurrected**
sequence unless evidence supports it.

Instead encode:
- identity association;
- physical representation;
- location;
- testimony;
- unresolved ontology.

## Repeated corpse-image / memorial forms

Amicus Tharn has three **Denounced One** containers using `AmicusDead.nif`, carrying the first three *Petition to House Tharn* volumes, followed by a later living/boss Amicus carrying the fourth.

The ESM does not establish whether those are:
- literal bodies;
- statues;
- memory echoes;
- symbolic denouncements;
- repeated Coldharbour representations.

### Modeling rule

Use a neutral representation relation such as:

**Amicus → represented by → Denounced One corpse-image containers**

rather than:
**Amicus died three times**

unless later evidence establishes literal deaths.

## Named relics do not equal current equipment

Named relics can preserve a historical saint/character tradition without being worn or wielded by the corresponding present manifestation.

Example:
- **Pelan's Mask**
- **Staff of St. Pelan**

Neither is structural proof that present-day Pepe wears or wields that item.

### Modeling rule

Distinguish:
- `named_for`
- `carried_by`
- `worn_by`
- `contained_in`
- `associated_with`

rather than collapsing all item naming into ownership.

## Soul/body/history separation

For difficult Coldharbour identities, Lorekeeper should maintain at least three layers:

1. **Historical identity**
   - who the person is said to have been.

2. **Current manifestation**
   - NPC race/body/template/form used by the ESM.

3. **Causal explanation**
   - testimony or structural evidence explaining how one became the other.

When layer 3 is missing, do not invent it.

## Example: Pelan / Pepe

Historical identity:
- Pelan;
- bishop;
- Alessian associate of Marukh.

Current manifestation:
- Inquisitor Pepe;
- Alessian Sleeper Race;
- custom Sleeper body.

Causal evidence:
- Pepe says he held the Stone too long;
- he says he became an empty shell without a soul;
- the memory-form chronology shows the body change between earlier and later memories.

This is unusually strong because all three layers are represented.

## Example: Judo

Historical/thematic identity:
- named “Judo of the Order of Diagna.”

Current manifestation:
- Soul-Shriven encounter variant.

Causal explanation:
- not preserved.

Therefore:
- Order of Diagna association = structural naming/equipment evidence;
- Soul-Shriven status = structural implementation;
- how/when Judo became Soul-Shriven = unresolved.

## Example: Manthar

Historical identity:
- Alessian sorcerer/architect who disappeared with Nenyond.

Current manifestation:
- Sorcerer Manthar / Bone Lord.

Causal explanation:
- not preserved at ESM-record level.

Therefore:
- identity continuity is strong;
- transformation mechanism is unresolved.

## Retrieval guidance

When an agent asks:
- “Who was this person?” → prioritize historical identity dossier.
- “What are they in Act 4?” → include manifestation class.
- “How did they become that?” → answer only from causal evidence; otherwise explicitly mark unresolved.
- “Are these two forms the same person?” → compare direct identity statements, shared EditorIDs/models, quest aliases, dialogue, and placement before merging.

## Canon boundary

Soul-Shriven and related Coldharbour reconstitution have licensed Elder Scrolls substrate.

VIGILANT's specific memory architecture, boss identities, corpse-image trails, Sleeper transformations, relic networks, and cross-era manifestations remain mod-continuity implementation.
