# The Black Worm — identity gap and supplementary resolution

Continuity: `tes.mod.vigilant`

Known direct quest anchor:
- `QUST 02129061` / `zzzCHSubQuest03` — **The Black Worm**
- alias `blackworm` → `NPC_ 020AEFE3` / **Black Worm**
- alias `Prisoner` → `NPC_ 0223C4B1` / Dremora Worm Keeper
- member of `FLST 0251EABB` / the Act 4 starter list

Known narrative anchor:
- **Jhunal the Owl** says a figure he calls the **Black Worm** learned secret arts from him, then used Jhunal as a test subject and tore him into pieces.

## What is established

The supplied VIGILANT 1.8.2 ESM now proves that the Act 4 side quest directly contains a specific NPC named **Black Worm**.

The quest actor:
- asks the player to open his cell;
- refuses to identify himself;
- refuses to explain why he is imprisoned.

Jhunal separately refers to a Black Worm who learned from him and mutilated him.

The name/quest identity is now direct; the strict personal-equivalence question between the imprisoned actor and Jhunal's historical attacker remains a final identity-link question rather than a missing quest-body problem.

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

## Mannimarco identity — source-separated

The **currently persisted ESM extraction** still contains no direct line stating that the Black Worm is Mannimarco.

However, the supplementary Nexus background article by **a123999** explicitly identifies the Black Worm as a **scattered portion of Mannimarco's spirit**, adding that sufficient parts can form the King of Worms.

Source record:
- `sources/supplementary/a123999-vigilant-backgrounds.md`

Lorekeeper should therefore preserve two layers:

- **ESM-only:** identity unresolved beyond Jhunal's testimony and the quest title.
- **supplementary commentary:** Black Worm = fragment/scattered part of Mannimarco's spirit.

Do not rewrite the ESM layer as though the plugin itself contains a direct Mannimarco-name line.

## Relationship to Jhunal's flesh art

Jhunal also claims knowledge of a **secret art of flesh**, and `BOOK 0218B1BA` / *The Art of the Ayleids* is credited to Jhunal.

Because the Black Worm is said to have learned secret arts from Jhunal and then experimented on him, the attacker belongs to the same broad **Jhunal / flesh-art / bodily-fragmentation** cluster.

However, the retained source layer does not establish exactly which techniques the Black Worm learned or used.

## Current classification

**High-confidence testimony:** a figure called the Black Worm was Jhunal's student/learner and later mutilated him.

**High-confidence structure:** Act 4 includes `NPC_ 020AEFE3` / **Black Worm** as the direct actor of *The Black Worm*.

**High-confidence direct dialogue:** the actor is an evasive prisoner asking to be freed.

**Supplementary identity:** a123999 identifies the Black Worm as a scattered part of Mannimarco's spirit.

**Still unresolved:** strict proof that the imprisoned actor is the exact historical manifestation that mutilated Jhunal, and direct ESM proof of the Mannimarco identity.

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


## Cross-Vicn corroboration search

A repository-wide search across the currently ingested GLENMORIL, UNSLAAD, and DAc0da corpora found no direct later record naming:
- **Black Worm**;
- **Mannimarco**;
- **King of Worms**

in a way that corroborates the VIGILANT identity claim.

Therefore the Mannimarco-fragment identification remains:

**supplementary a123999 commentary, not direct cross-Vicn ESM corroboration.**

This search result strengthens the need to preserve the source boundary rather than treating the identity as universally confirmed across Vicn works.


## Direct-source dossier

See:
- `entities/characters/black-worm.md`
- `analysis/act4-direct-source-recovery.md`
- `dialogue/act4/recovered-sidequests.md`
