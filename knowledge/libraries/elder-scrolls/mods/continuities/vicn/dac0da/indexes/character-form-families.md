# DAc0da character form families

**Continuity:** `tes.mod.vicn.dac0da`  
**Source:** `DAc0da.esm`

DAc0da frequently represents one narrative identity through multiple separate NPC_ records. These forms should be related but **not automatically collapsed into one physical body or chronology**.

## Rolls-On-Roads

| Source | Editor ID | Displayed name | Function |
|---|---|---|---|
| `000D77` | `zDcdUqPsijicArgonian` | Rolls-On-Roads | primary Psijic Monk |
| `004930` | `zDcdUqPsijicArgonianMemospore` | Rolls-On-Roads | memospore/memory manifestation |
| `00B75A` | `zDcdUqPsijicArgonianBit` | Rolls-On-Roads | fragment/bit form used in censorship realm |
| `00CA1B` | `zDcdUqPsijicArgonianAlt` | Load Error | alternate/censored MQ05 form |

This is one of the strongest mechanical demonstrations that DAc0da treats identity as separable from a single actor body.

## Akashiya-Samon

| Source | Editor ID | Name | Function |
|---|---|---|---|
| `003152` | `zDcdUqTsaesciSamurai` | Akashiya-Samon | primary unique actor |
| `004B1D` | `zDcdBossTsaesciSamurai` | Akashiya-Samon | boss/combat state |
| `005020` | `zDcdSummonTsaesciSamurai` | Akashiya-Samon | summon state |
| `00CE92` | `zDcdUqTsaesciSamuraiGhost` | Akashiya-Samon | ghost epilogue |

The ghost epilogue is therefore structurally distinct from Samon's earlier living/combat appearances.

## Vanus Galerion

- `005183` — `zDcdUqVanus` — Vanus Galerion
- `006067` — `zDcdUqVanusGhost` — Vanus Galerion

The quest itself says the turtle Vanus is a copied/transferred memory-personality. Separate ghost/memory forms should therefore remain ontology-aware.

## Vigilant Athanasius

- `005251` — `zDcdUqAthanasius` — Vigilant Athanasius
- `006089` — `zDcdBossGhostAthanasius` — Vigilant Athanasius

The Revenant subquest can therefore represent Athanasius through a ghost branch if his ordinary body is no longer active.

## Yu'qbar

- `000D74` — `zDcdUqDreughElder` — Templar of Hahd Yu'qbar
- `006087` — `zDcdBossGhostDreughElder` — Templar of Hahd Yu'qbar

As with Athanasius, the final Worm arc has explicit ghost-state support rather than assuming one fixed survival state.

## Mannimarco

### God of Worms

- `003075` — `zDcdBossMannimarco` — Mannimarco the God of Worms
- `006105` — `zDcdSummonMannimarco` — summon form

### Necromancer's Moon

- `00606E` — `zDcdBossMannimarcoMoon` — Necromancer's Moon
- `006106` — `zDcdSummonMannimarcoMoon` — summon form

DAc0da operationally separates the God-of-Worms combat actor from the Necromancer's-Moon actor, matching Vanus's explanation that Mannimarco's mortal/divine states became separated.

## Abnur Tharn

- `005253` — `zDcdUqAbnurTharn01` — Mysterious Battlemage
- `00525B` — `zDcdUqAbnurTharn02` — Mysterious Battlemage

Both deliberately hide the displayed Abnur identity while being used in related side-quest/Worm material.

## Hgelhelm the Outcast

- `004351` — boss form
- `0048F4` — summon form
- `004B19` — unique dialogue form

All three display **Hgelhelm the Outcast**.

## Underking / Zurin

### The Underking

- `000D76` — `zDcdBossUnderking` — The Underking
- `004F8B` — `zDcdSummonUnderking` — The Underking

### Zurin Arctus

- `00AF11` — `zDcdBossUnderking2nd` — Zurin Arctus
- `00B1FB` — `zDcdSummonUnderking2nd` — Zurin Arctus

DAc0da therefore distinguishes Underking-labelled and Zurin-Arctus-labelled actor forms while narratively linking them through Mantella history.

## Ghost Choir 9

- `0079C9` — `zDcdBossGC901` — GC9
- `00B446` — `zDcdBossGC902` — GC9
- `00CB93` — `zDcdSummonGC9` — Ghost Choir 9
- `00CCCA` — `zDcdSummonCrGC9` — GC9 Instance

Ghost Choir 9 is thus represented as multiple combat/instance forms rather than one ordinary individual NPC.

## Dumac

- `00B1F8` — `zDcdBossDweKing` — Dumac's Tonalframe
- `00B1FA` — `zDcdSummonDweKing` — Dumac's Tonalframe

The actor name itself frames the entity as a **Tonalframe**, not simply Dumac's unchanged historical body.

## Arcanist

- `00B217` — `zDcdBossArcanist01` — Arcanist
- `00CBCF` — `zDcdSummonArcanist` — Arcanist
- `00CBC6` — `zDcdSummonCrArcanist` — Frayed Fate

The Frayed Fate form should remain distinct unless dialogue/scripts explicitly equate it to the ordinary Arcanist actor.

## Jill forms

- `00B75D` — `zDcdEncJill`
- `00B762` — `zDcdEncJillNoScript`
- `00C9EF` — `zDcdEncJillNoScriptQuiet`

These are implementation variants of Jill actors used under different scripting/encounter conditions.

## The Agent family

See `characters/the-agent-yaghra.md`.

Core forms include:

- Yaghra Chimera - The Agent
- The Agent
- Yaghra Bioborg - The Agent
- summon variants

The separate bodies reinforce the library rule that DAc0da's Daggerfall-Agent association is an identity/possibility relationship, not proof that each actor record is one continuous physical organism.

## Retrieval rule

When a query asks **who a character is**, retrieve the character dossier plus this form-family index.

When a query asks **what happened in a particular scene/branch**, use the exact actor FormID and quest alias rather than silently substituting another form with the same displayed name.
