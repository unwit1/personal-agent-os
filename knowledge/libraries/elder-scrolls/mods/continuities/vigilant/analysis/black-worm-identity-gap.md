# The Black Worm — identity and source gap

Continuity: `tes.mod.vigilant`

Known structural anchor:
- `zzzCHSubQuest03` — **The Black Worm**
- member of `FLST 0251EABB` / the Act 4 starter list

Known narrative anchor:
- **Jhunal the Owl** says a figure he calls the **Black Worm** learned secret arts from him, then used Jhunal as a test subject and tore him into pieces.

## What is established

The repository currently preserves two independent facts:

1. Act 4 contains a side quest explicitly titled **The Black Worm**.
2. Jhunal directly refers to a **Black Worm** who learned from him and later mutilated him.

Those facts create a strong candidate connection, but the currently retained extraction does not include enough quest-specific aliases, dialogue, scene attribution, placement, or script data to prove that the side-quest title and Jhunal's attacker are the same instantiated character.

Accordingly, Lorekeeper should model:

**Black Worm (Jhunal testimony) ↔ probable but unconfirmed relation ↔ The Black Worm side quest**

rather than silently merging them.

## Jhunal testimony

Jhunal's surviving dialogue says the Black Worm:
- learned secret arts from Jhunal;
- later used Jhunal as a test subject;
- tore Jhunal into pieces;
- left Jhunal requiring hundreds of years to recover even to his later Owl-sized state.

The physical implementation of Jhunal strongly corroborates the **fragmentation** portion of that testimony:
- one speaking **Jhunal the Owl** is placed in Jhunal's Library;
- three actors named **Piece of Jhunal** are placed beside him.

This does not independently identify the attacker, but it makes the mutilation claim materially represented in the plugin.

## Mannimarco caution

The epithet **Black Worm** naturally resembles Elder Scrolls naming associated with worm/necromancer imagery, but the currently persisted VIGILANT corpus contains **no direct Mannimarco identification** for this figure.

Therefore do not encode:
- Black Worm = Mannimarco;
- Black Worm = King of Worms;
- The Black Worm quest = Mannimarco encounter;

unless a future exact-source pass recovers explicit evidence.

## Relationship to Jhunal's flesh art

Jhunal also claims knowledge of a **secret art of flesh**, and `BOOK 0218B1BA` / *The Art of the Ayleids* is credited to Jhunal.

Because the Black Worm is said to have learned secret arts from Jhunal and then experimented on him, the attacker belongs to the same broad **Jhunal / flesh-art / bodily-fragmentation** cluster.

However, the retained source layer does not establish exactly which techniques the Black Worm learned or used.

## Current classification

**High-confidence testimony:** a figure called the Black Worm was Jhunal's student/learner and later mutilated him.

**High-confidence structure:** Act 4 includes a quest titled *The Black Worm*.

**Unresolved:** whether these two anchors refer to the exact same actor/episode.

## Required future extraction

Priority source recovery should target:
- `zzzCHSubQuest03` quest aliases;
- dialogue topics/INFO records conditioned on the quest;
- SCEN records owned by the quest;
- named NPCs and placements referenced by the quest;
- VMAD properties and stage fragments;
- external PEX bodies if available.

## Canon boundary

The Black Worm/Jhunal relationship is VIGILANT-continuity material. No official-canon identity should be assigned without independent evidence.
