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

A second full-plugin audit traversed all **36,824 physical plugin records** and produced a separate **370-record implementation-evidence layer** for player-facing or lore-structural evidence omitted by the original priority filter. This includes factions, talking activators, voice types, mechanisms, equipment, enchantments, keys, spells/effects, races/creatures, three named placed references, and explicitly classified cosmetic implementation labels. A final deep payload sweep also captured 14 MGEF `DNAM` descriptions plus the only human-readable INFO `NAM2` and `RNAM` fields. Asset paths, package parameter labels, binary false positives, and other engine-only metadata were audited but not promoted into lore claims. No natural-language VMAD/script payloads were found, and the plugin is not localized.

See:
- `analysis/source-integrity.json`
- `analysis/exhaustiveness-audit.md`
- `analysis/implementation-text-supplement.json`
- `raw/implementation-text-supplement.jsonl.gz`
- `raw/source-evidence-augmentation.jsonl`

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
- BOOK provenance passes 01-06;
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

Pass 04 located original pre-Wheels Trainwiz archive packages for **Aethernautics** (2012) and **Sotha Sil Expanded** (2012/2014) and persisted their filenames, dates, byte sizes, source URLs, and published MD5 hashes. Their binary RAR contents could not be materialized in the current retrieval environment, so the exact-text classifications remain unchanged.

Pass 05 re-tested the archive download route and confirmed that the blocker remains binary acquisition only. It also preserved deeper historical context from the already-known September 2012 Aethernautics Weaponry Tweaks page: multiple Aethernautics harquebus variants are documented before Wheels, while a third-party planned \"Cronographer\" / Sotha Sil expansion is retained only as development-history evidence. A 2015 Trainwiz post explicitly states that Aethernautics and Wheels share a canon; that relationship is recorded without treating the post as evidence that any Wheels BOOK text predates Wheels.

Future work should resume at archive-byte acquisition and deterministic text comparison. If that remains blocked, the next useful source class is a historical record-level dump, translation string table, xEdit export, or plugin-derived BOOK inventory—not another generic title/package search.

## Cross-mod continuity lineage

A separate external-metadata analysis now models the published **Trainwiz ChronoC0da** lineage without merging source corpora. It records **Sotha Sil Expanded** as a predecessor/root relationship, the published Skyrim sequence through **The Wheels of Lull**, and Trainwiz's explicit 2015 statement that **Aethernautics** and Wheels take place in the same canon.

See:
- `analysis/trainwiz-chronocoda-lineage.md`
- `analysis/trainwiz-chronocoda-lineage.json`

## Verified ChronoC0da source ingestion — 2026-09-24

Current official **Aethernautics 3.1** and **Sotha Sil Expanded 3.1** packages are now verified and represented as separate provenance-scoped continuities under the `trainwiz-chronocoda` umbrella.

Deterministic comparison gives **11 Wheels BOOK records** a current cross-continuity witness. Seven of the ten previously unresolved named works now have a current counterpart, while *Trademarks*, *Sybandis*, and *Journeys Through Sybandis* remain unmatched in these two packages.

This does **not** change historical pre-Wheels provenance counts: the verified comparison packages were released in 2025/2026. They prove current shared-work identity and edition relationships, not that the corresponding text was already present in a 2012/2014 build.

See:
- `analysis/book-provenance-pass-06-current-chronocoda-comparison.md`
- `../aethernautics/`
- `../sotha-sil-expanded/`
- `../trainwiz-chronocoda/`

## Retrieval state

The raw blocker is closed. Existing compact indexes cover the expected **1,090-record core corpus**, and a fresh deterministic materialization is now unblocked.

A fresh checkout rebuild is still recommended as a verification step before replacing committed routing/lexical derivatives. The 370-record implementation-evidence layer should remain a secondary evidence collection unless explicitly enabled, so implementation metadata does not become indistinguishable from narrative lore.

## Provenance policy

All material remains scoped to `tes.mod.wheels-of-lull` unless an explicit source relationship is verified. Character testimony, quest narration, UI/message text, implementation evidence, external/developer texts, and later synthesis remain distinct evidence classes.

No ambiguous line is silently assigned to a speaker, and no reused text is promoted into Bethesda canon merely because Wheels embeds it.
