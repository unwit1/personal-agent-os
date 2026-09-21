# Generic dialogue — resolved batch 01

Continuity: tes.mod.vicn.unslaad
Dialogue owner: QUST 0302012D / zzzCrbGeneric — **Unslaad Generic**
Primary source: translated Unslaad.esm 3.0.6

## Resolution method

UNSLAAD stores a large amount of character dialogue in the shared generic quest rather than in the side quest that introduces the character.

This pass resolved speakers using INFO CTDA function **72 / 0x48 (GetIsID)**. The first parameter is matched directly to an NPC record. Quest-state conditions are preserved separately and are not treated as speaker evidence.

## Coverage

- 217 INFO rows contain at least one GetIsID speaker condition.
- 120 distinct DIAL topics are represented.
- 28 named speaker labels are resolved.
- 222 speaker assignments occur because five rows permit more than one form with the same displayed identity/archetype.

Highest-volume resolved speakers include:
- Hermit — 17 rows
- Arkved the Dreamer — 15
- Pot Baba — 15
- Mifa Xanadu — 13
- Lizz — 12
- Atta — 11
- Snow Kanra — 10
- Naghu the Gardener — 9
- Cawk the Dirtbird — 9
- Fluffy — 8
- Lord of Over Here — 8
- Wulf the Veteran — 8
- Ulliss — 7
- Rat Chef — 7
- Orlando the Knowledgeable — 5

## High-value discoveries

### Fluffy / Ja'cobee identity discontinuity

After Lizz is returned:
- Lizz calls Fluffy **Ja'cobee**.
- Fluffy asks why Lizz calls him Ja'cobee and says he wants a richer name.
- Aisha independently remarks that Lizz calling Fluffy Ja'cobee feels strange.

This supports continuity between the forms while directly proving that memory/self-recognition is not stable.

### Arkved

Arkved's actual conversation is stored here, not in QUST zzzCrbSq03.

He explicitly says:
- body is merely a shell;
- forgotten places dissolve, while remembered places leave echoes;
- a child can laugh/sing a place into continued existence;
- the player should sing their own self into the world;
- the Black Owl waits in the abyss but cannot simply kill the Prisoner;
- he made his deal with **the Oneiromancer**, not the Black Owl.

### Orlando

Orlando explicitly says:
- he has met the player in the Warrens and at the Blue Star;
- Ja'cobee broke the Egg shell and the player crushed its contents;
- he and the Black Owl come from the same far northern Elder Wood.

### Hjalti

Mifa Xanadu says a little boy named **Hjalti** commissioned custom armor, left gold, and departed. She has worked on it for centuries and assumes the client is dead.

This independently reinforces the Hjalti thread already present in early UNSLAAD dialogue.

### Name / Radiance

The Sacred Anatomancer repeatedly asks the player to give up their **name**, specifically because it wants to see the name's **Radiance**.

The Hermit separately defines Radiance as an echo of a past that was never experienced and calls it a coffin rather than a guiding light.

These records should be linked but not treated as a complete definition of either Name or Radiance.

### Memory persistence

Arkved says forgotten places dissolve but remembered echoes remain.

Anaku separately says "THAT" will disappear if none of them remember it anymore. The pronouns remain deliberately unresolved, but the line independently supports memory-dependent persistence as recurring UNSLAAD vocabulary.

## Attribution cautions

- GetIsID proves a permitted speaker form for the INFO record, but additional quest/global/item conditions still determine when a row appears.
- Multi-form rows, such as Snow Kanra dialogue, should be normalized to the shared displayed identity only when the source forms are equivalent archetypes.
- Topic EditorIDs may contain a character nickname but speaker attribution should still come from conditions.
