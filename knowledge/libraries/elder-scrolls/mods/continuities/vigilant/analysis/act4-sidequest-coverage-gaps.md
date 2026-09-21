# Act 4 side-quest coverage and remaining extraction gaps

Continuity: `tes.mod.vigilant`

This page tracks which quests in `FLST 0251EABB` / `zzzCHAct4QuestStarterList` already have usable Lorekeeper reconstruction and which still need raw dialogue, quest-alias, placement, or Papyrus recovery.

It is intentionally conservative: **starter-list membership proves orchestration, not narrative content.**

## Current coverage

### Strongly reconstructed or dossiered

#### Madness — `zzzCHSubQuest05`
Current repository material already ties the quest to the Dro'Zel / mad-cat-king / bard recurrence cluster.

Useful anchors include:
- the Dro'Zel dossier;
- *A Vision in Malada* stanza 4 mapping;
- three Madness scenes with king-shadow aliases;
- wider Coldharbour memory/story analysis.

Status: **substantial narrative coverage already present.**

#### Pitier — `zzzCHSubQuest06`
The scene index resolves the quest's `Renald` role to **Aredhel**, and the repository already contains:
- Aredhel dossier;
- Aredhel/Renald identity analysis;
- Diagna/Coldharbour cluster work.

Status: **substantial identity coverage already present.**

#### Paladin Melus — `zzzCHSubQuest09`
Now covered by:
- `entities/characters/melus-petilius.md`
- *A Vision in Malada* stanza 6 mapping
- `SCEN 021C1EA7`

Status: **core recurrence motif reconstructed; graverobber identity/mechanism still open.**

#### Broken Horns — `zzzCHSubQuest13`
Now covered by:
- Belharza dossier;
- Amicus Tharn dossier and petition analysis;
- Act 4 orchestration;
- `analysis/broken-horns-final-memory-handoff.md`

Status: **high-confidence structural reconstruction.**

#### Bald Man-Ape — `zzzCHSubQuest14`
Covered by the Saklas dossier and Jhunal's Library investigation.

Status: **substantial structural/dialogue coverage already present.**

#### The Saint's Corpse — `zzzChSubQuest15`
Now has a Gravekeeper structural dossier plus:
- dedicated Gravekeeper dialogue scenes;
- Gravekeeper's House topology.

Status: **structural coverage present; full dialogue/content extraction still incomplete.**

## Partial structural coverage

### Knight of Arkay — `zzzCHSubQuest10`

The scene index preserves:
- `SCEN 021C31F3`
- speaker: **Sir Torolf**

A dedicated structural dossier now exists at `entities/characters/sir-torolf.md`.

Status: **named speaker and stable character node recovered; narrative body still missing.**

### Kyne's Dragon — `zzzCHSubQuest11`

The scene index preserves:
- `SCEN 022C374B`
- speaker: **Kahkaankrein**

Broken Horns also stores a property pointing to **Kyne's Dragon**, making the quest structurally relevant to the Belharza/Morihaus/final-memory complex.

A dedicated structural dossier now exists at `entities/characters/kahkaankrein.md`.

Status: **named speaker + cross-quest linkage + stable character node recovered; narrative body still missing.**

## Starter-list membership only or near-only

The following quests are confirmed members of the Act 4 starter list, but the current browsable repository does not yet contain enough quest-specific narrative evidence for a reliable dossier:

- `zzzCHSubQuest01` — **More Skooma**
- `zzzCHSubQuest02` — **Archer of Kyne**
- `zzzCHSubQuest07` — **Knight of Julianos**
- `zzzCHSubQuest08` — **Knight of Zenithar**
- `zzzCHSubQuest12` — **Knight of Kynareth**

### The Black Worm caution

Jhunal testimony elsewhere refers to a **Black Worm** who tore Jhunal apart.

That creates a potentially important connection to `zzzCHSubQuest03` / *The Black Worm*, but the currently persisted quest-specific evidence does not yet prove that the side quest's title refers to the exact same entity or episode.

Do not identify the Black Worm with **Mannimarco** merely from the epithet. The current VIGILANT repository layer does not contain a direct Mannimarco identification.

Status: **identity/source-gap analysis now preserved in `analysis/black-worm-identity-gap.md`; exact quest body still missing.**

## Funeral — `zzzCHSubQuest04`

The repository contains extensive material involving:
- Funeral Temple;
- Manthar;
- Silorn;
- Nenyond;
- funerary/charnel complexes.

However, searches for the generic word **Funeral** collide heavily with those location and relic records.

The quest-specific narrative body of `zzzCHSubQuest04` has not yet been cleanly isolated from the broader Funeral Temple corpus.

Status: **structural separation now preserved in `analysis/funeral-sidequest-structure.md`; Sister/SisterDead bases, dialogue, and runtime body still need recovery.**

## Why this gap map matters

Without this page, repeated continuation passes risk:
- mistaking a quest title for a reconstructed storyline;
- equating similarly named characters or concepts without evidence;
- repeatedly searching already-completed clusters;
- over-promoting scene-only characters into full biographies.

The next raw-source priority for Act 4 side quests should be:

1. **More Skooma**
2. **Archer of Kyne**
3. **Knight of Julianos**
4. **Knight of Zenithar**
5. **Knight of Kynareth**
6. **The Black Worm** — exact quest body after identity-gap analysis
7. **Kyne's Dragon / Kahkaankrein** — full dialogue/alias body
8. **Knight of Arkay / Sir Torolf** — full dialogue/alias body
9. **Funeral** — Sister/SisterDead resolution

This ordering is an **extraction priority**, not a lore-importance ranking: it favors quests with existing cross-links that can unlock other unresolved relationships.

## Source limitation

The current repository retains strong structural extraction from the original VIGILANT ESM, but the source plugin bytes and external Papyrus PEX bodies are not currently available through the connected source layer.

Accordingly:
- scene and quest IDs are structural evidence;
- starter-list membership is structural evidence;
- existing resolved dialogue is usable testimony;
- missing narrative detail should remain explicitly missing rather than reconstructed from title semantics.
