# Wheels of Lull book provenance — pass 06 current ChronoC0da source comparison

Continuity: `tes.mod.wheels-of-lull`  
Audit date: 2026-09-24

The uploaded **Aethernautics Special Edition 3.1** and **Sotha Sil Expanded 3.1** packages were independently verified as the current official source packages, structurally parsed, and compared against all Wheels BOOK fingerprints.

## Result

Eleven Wheels BOOK records now have a deterministic current-package witness in Aethernautics and/or Sotha Sil Expanded.

Exact semantic matches include:

- Aethernautics ↔ Wheels: *Chronography, Volume I* and *Volume III*.
- Sotha Sil Expanded ↔ Wheels: *How Two Moon*, *Musings on Power*, *KINMUNE*, *Harquebuses*, and *Tatterdemalion*.

Verified minor/current edition variants include:

- *Chronography, Volume II*: two small wording differences.
- Aethernautics *Harquebuses*: the same body with an added author byline.
- *De Rerum Mutabilitatis*: one typo difference.
- *Wind Up and Wound Down*: punctuation-only title/byline difference.
- *The Cacophony*: same prose after repairing two mojibake quote characters in Wheels.

Seven of the ten previously unresolved named Wheels works now have a verified **current cross-continuity witness**: *Wind Up and Wound Down*, *Musings on Power*, *De Rerum Mutabilitatis*, *How Two Moon*, and all three *Chronography* volumes.

The three named works without a counterpart in these two current packages remain *Trademarks*, *Sybandis*, and *Journeys Through Sybandis*.

## Critical chronology boundary

Aethernautics 3.1 is a **2026** release and Sotha Sil Expanded 3.1 is a **2025** release. Wheels originally released in 2014. Therefore these comparisons establish shared-work identity and current edition relationships, but **do not by themselves prove that the matching texts were present in the 2012/2014 historical packages**.

Historical provenance classifications are intentionally unchanged. Older dated package witnesses or record-level historical evidence are still required to promote a text to pre-Wheels reuse solely on the basis of Aethernautics/Sotha Sil Expanded.

## New source scopes

- `tes.mod.aethernautics` — verified current 3.1 source, separate provenance scope.
- `tes.mod.sotha-sil-expanded` — verified current 3.1 source, separate provenance scope.
- `tes.mod.trainwiz-chronocoda` — umbrella graph linking these sources to Wheels without collapsing editions.

See the machine-readable companion and the new continuity-specific `analysis/shared-work-relations.json` files.
