# Wheels of Lull book provenance — pass 02

Continuity: `tes.mod.wheels-of-lull`  
Source ESP SHA-256: `230b102cd1ec13f2d104da8803d32c19227ef519eaca766a00b076c322aa78bb`  
Scope: deterministic text normalization, central-source linking, and second-pass origin triage for all 33 BOOK records.

## Completed in this pass

### 1. Deterministic normalization and fingerprinting

All **33/33 BOOK records** now have three SHA-256 fingerprints in `book-normalization-index.json`:

- raw decoded BOOK text;
- presentation-markup-normalized text;
- comparison-normalized text.

The comparison fingerprint removes presentation-only Skyrim book markup and normalizes case/whitespace/smart punctuation while preserving semantic prose and placeholders. Raw plugin text remains authoritative.

This is now the preferred first step for deduplication and edition comparison. Title similarity alone is not enough to merge works.

### 2. Central-source links for the three verified reused texts

#### `0537158E` — KINMUNE

- Status: **verified external reuse; embedded variant**
- Central source:
  `knowledge/libraries/elder-scrolls/sources/apocryphal-library/books/040008F1-anon-anu-anui-el.txt`
- The central copy is visibly a different/expanded KINMUNE version, so exact deduplication is forbidden until an edition-level diff is completed.
- Wheels retains its own FormID, text fingerprint, placement, and continuity-adoption evidence.

#### `0537158F` — Tatterdemalion

- Status: **verified prior developer/community-archive text reuse**
- Central catalog:
  `knowledge/libraries/elder-scrolls/sources/imperial-library/catalog/tatterdemalion-the-lunar-province-of-secunda.md`
- The work is documented outside Wheels before the mod's release.
- Relation: `embedded_copy_or_variant`; exact variant diff remains pending.

#### `05371590` — The Cacophany

- Status: **verified excerpt from The Xal-Gosleigh Letters**
- Central catalog:
  `knowledge/libraries/elder-scrolls/sources/imperial-library/catalog/the-xal-gosleigh-letters.md`
- Relevant source section: Xal's **Day of the Power/Knowledge** letter.
- Relation: `embedded_excerpt`; Wheels preserves its local excerpt boundaries.

### 3. Strong-indirect legacy candidate: Harquebuses

`0537158D` — *Harquebuses* is now classified as:

- `probable_legacy_trainwiz_material`
- confidence: **strong indirect**
- exact prior text source: **not yet verified**

Reason: Trainwiz's Aethernautics already used harquebuses years before Wheels of Lull, so the underlying technology and terminology clearly predate Wheels. However, the current source corpus does not establish that the exact treatise text — *On the Propulsion of Matter, Mind, and Mathematics via Magickal Means...* — was published in Aethernautics or Sotha Sil Expanded. Therefore this record is **not** promoted to verified external-text reuse.

### 4. Functional triage of continuity-local documents

Nineteen records are now tagged as **continuity-local contextual/operational documents** for retrieval purposes:

- Strange Note
- Love Poem LT0782
- Reminder to all Workers
- Archeron's Diary
- Wailyard Operation Instrctions
- Thomas the Screaming Tank Engine And His Screaming Friends
- Security Pack List
- Equipment Crafting List
- Combatative Harquebus Crafting List
- Rotational Harquebus Crafting List
- Bombastic Harquebus Crafting List
- Lullian Harquebus Crafting List
- Targetian Harquebus Crafting List
- Upgate Manual
- Letter
- Message from the Eternity
- Cheater
- Forged Thalmor Orders
- Research Notes

This classification describes their **function inside the Wheels continuity**, not proof of first authorship. Their source-origin field remains unresolved unless earlier publication evidence is found.

### 5. Named works still requiring origin research

The following ten named works have no verified prior-source identity in the current central corpora and remain `origin_unresolved`:

- *Wind Up and Wound Down*
- *Musings On Power*
- *De Rerum Mutabilitatis*
- *How Two Moon*
- *Chronography, Volume I*
- *Chronography, Volume II*
- *Chronography, Volume III*
- *On Trademarks*
- *On Sybandis*
- *Journeys through Sybandis, the Nirn That Never Was*

Repository searches that merely returned shared words or broad lunar/Clockwork material were rejected as false-positive evidence. In particular, a fuzzy hit for *Musings On Power* in the ESO corpus did not contain the exact title when the source batch was inspected.

## Current provenance state

- BOOK records: **33**
- Verified prior/external reuse: **3**
- Strong-indirect legacy candidate: **1**
- Continuity-local functional classification with unresolved origin: **19**
- Named works with unresolved origin: **10**
- Deterministically fingerprinted: **33/33**

These classes are intentionally non-exclusive at the conceptual level: "continuity-local" describes usage in Wheels; "origin unresolved" describes historical provenance.

## Next provenance work

1. Perform exact/near-exact edition diffs for KINMUNE, Tatterdemalion, and the Xal-Gosleigh excerpt using the new comparison fingerprints.
2. Search archived Trainwiz/Sotha Sil Expanded/Aethernautics sources for the exact *Harquebuses* treatise text.
3. Research the ten unresolved named works against archived forum posts, old mod assets, Imperial Library mirrors, and developer-text collections.
4. Promote only evidence-backed source relationships into the central work registry.
5. The former 52-INFO raw-shard gap was repaired from the exact verified ESP on 2026-09-23; BOOK provenance work no longer has a dialogue-integrity dependency.

## Integrity boundary

This pass does not repair or infer anything from:
- `raw/source-records-0151-0200.jsonl.gz`
- `raw/source-records-0401-0450.jsonl.gz`

The BOOK corpus used here is fully readable and independent of those damaged dialogue shards.
