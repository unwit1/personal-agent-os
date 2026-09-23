# The Wheels of Lull

Sub-continuity for the Skyrim mod **The Wheels of Lull**.

- Continuity ID: `tes.mod.wheels-of-lull`
- Primary source: user-provided `WheelsOfLull.esp`
- ESP SHA-256: `230b102cd1ec13f2d104da8803d32c19227ef519eaca766a00b076c322aa78bb`
- Plugin header version: `6.0.0.3`
- Source author metadata: `Trainwiz`

## Source ingestion: exhausted for the supplied ESP

Core narrative/source corpus:

- BOOK **33/33**
- QUST **32/32**
- DIAL **337/337**
- INFO **410/410**
- NPC_ **75/75**
- LCTN **33/33**
- CELL **103/103**
- MESG **53/53**
- SCEN **14/14**
- **1,090 core structured source records**

The previously corrupt raw shards `151-200` and `401-450` were regenerated deterministically from the exact verified ESP on 2026-09-23. All core raw source records are now readable.

A second full-plugin audit traversed all **36,824 physical plugin records** and added a separate **328-record implementation-text supplement** for player-facing or lore-structural evidence omitted by the original priority filter. This includes factions, talking activators, voice types, mechanisms, equipment, spells/effects, races/creatures, and three named placed references. Asset paths, package parameter labels, and other engine-only metadata were audited but not promoted into lore claims.

See:
- `analysis/source-integrity.json`
- `analysis/exhaustiveness-audit.md`
- `analysis/implementation-text-supplement.json`
- `raw/implementation-text-supplement.jsonl.gz`

## Dialogue integrity

All **410 INFO records** are source-readable.

Strict deterministic CTDA resolution:
- processed: **410**
- resolved: **332**
- intentionally unresolved: **78**
- excluded for source corruption: **0**

The repaired 52-record gap contributed **44 resolved / 8 unresolved**. Re-running the same strict resolver on the old 358-record readable baseline reproduced its previous **288 / 70** result exactly.

The broader dialogue layer still retains contextual, scene-alias, role-level, talking-activator, and candidate-set attribution where useful. Strict unresolved status is therefore a conservative evidence label, not a claim that no contextual speaker can be inferred.

## Core post-ingestion analysis

Completed:
- character, place, artifact/technology, and faction dossiers;
- 31 normalized core claims and 7 tension/canon-boundary records;
- 14 topic dossiers plus theme/reliability synthesis;
- compact routing/retrieval derivatives with 76 analysis entries;
- deterministic fingerprints for all 33 BOOK records;
- BOOK provenance passes 01-03;
- machine-readable BOOK-to-central-source relations;
- full source-integrity repair and full-plugin exhaustiveness audit.

## BOOK provenance

All **33/33 BOOK records** have raw, normalized, and comparison SHA-256 fingerprints.

Current provenance state:
- **3** verified prior/external text reuses: KINMUNE, Tatterdemalion, and The Cacophany / Xal-Gosleigh excerpt;
- **1** strong-indirect legacy Trainwiz candidate: *Harquebuses*;
- **19** continuity-local contextual/operational documents with historical origin unresolved;
- **10** named lore works with no verified pre-Wheels witness in the currently available source corpora.

Those unresolved items now represent **external historical provenance work**, not unprocessed material in `WheelsOfLull.esp`.

## Retrieval state

The raw blocker is closed. Existing compact indexes cover the expected **1,090-record core corpus**, and a fresh deterministic materialization is now unblocked.

A fresh checkout rebuild is still recommended as a verification step before replacing committed routing/lexical derivatives. The 328-record implementation-text supplement should remain a secondary evidence collection unless explicitly enabled, so implementation metadata does not become indistinguishable from narrative lore.

## Provenance policy

All material remains scoped to `tes.mod.wheels-of-lull` unless an explicit source relationship is verified. Character testimony, quest narration, UI/message text, implementation evidence, external/developer texts, and later synthesis remain distinct evidence classes.

No ambiguous line is silently assigned to a speaker, and no reused text is promoted into Bethesda canon merely because Wheels embeds it.
