# Dealing with Daedra refinement pass 16 — evidence locator and semantic dedup QC

Date: 2026-09-24  
Continuity: `tes.mod.dealing-with-daedra`

This pass improves provenance reproducibility and catches semantic duplicates that an exact-string duplicate check could not see. It does not reopen bulk semantic extraction.

## Evidence-locator audit

Current claim corpus: **359** indexed claim records.

Papyrus-backed claim evidence:
- **18** script evidence references;
- **13** unique script filenames;
- **1** claim whose listed evidence is entirely Papyrus-based: `dwd-078`.

The source manifest records that **784 Papyrus source files** were scanned during the original archive ingestion. The current continuity retains the extracted Papyrus string-literal inventory and script filenames used by promoted claims, but it does **not** retain the complete source bodies for those 13 cited scripts.

A new machine-readable locator layer is therefore stored at:

`../indexes/evidence-locator-index.jsonl`

For each cited script it records:
- exact source filename;
- dependent claim IDs;
- original archive filename and SHA-256;
- source-manifest provenance;
- current locator precision;
- whether byte/line-level revalidation is possible from the persisted continuity.

No archive member path or script hash was invented. Until the original archive or a persisted Papyrus source copy is available, those 13 locators remain intentionally **source-filename-only**.

### Recovered message locator

The only message citation that previously had an editor ID but no FormID was:

- editor ID: `dealscorruptsignetmessage`
- resolved type/FormID: `MESG 058E6BE6`
- preserved source-record shard: `source-records/text-records-0028.jsonl.gz`

This locator is now written into both:
- `claim-seeds-04.jsonl`
- `claim-index.jsonl`

so seed/index provenance stays synchronized.

## Semantic duplicate audit

The earlier integrity audit found no exact duplicate subject/predicate/object triples. A second pass compared claim identity using shared primary evidence plus normalized proposition similarity.

Two historical duplicate pairs were found.

### Vampire Master Cyrodiil plan

- `dwd-091`
- `dwd-223`

Both cite INFO `0553A0E0` and describe the Vampire Master's plan to travel to Cyrodiil and negotiate with the Order Vampyrum.

Normalized as:
- relation: `dwd-special-rel-006`
- type: `semantic_alias_same_event`
- preferred retrieval claim: `dwd-091`
- evidence independence: none; same primary evidence.

Both historical claim IDs are retained.

### Jurger Stonearm / Forsworn offerings

- `dwd-118`
- `dwd-173`

Both describe Jurger Stonearm directing Family attacks on Forsworn whose victims can be rendered into offerings/material. Both cite INFO `053A44D7`; `dwd-118` additionally cites INFO `053A44D6`.

Normalized as:
- relation: `dwd-special-rel-007`
- type: `semantic_alias_overlapping_evidence`
- preferred retrieval claim: `dwd-118`
- evidence independence: partial overlap, not independent corroboration.

Again, both historical IDs remain valid.

The four Widows target-list claims sharing BOOK `0569E033` are **not** duplicates: each records a distinct target/couple and distinct proposed method.

## Relation QC after normalization

- structured relations: **21**
- conflicts: **7**
- uncertainty boundaries: **7**
- specialized relations: **7**
- claims carrying relation notes: **46**
- cross-role claim overlaps inside relations: **0**

Specialized relations now consist of:
- 3 semantic-alias/dedup relations;
- 3 detail/scope normalization relations;
- 1 independent placement corroboration.

## Confidence semantics

A confidence value describes confidence that the stored claim accurately represents the cited evidence at its stated scope. It is **not** a blanket assertion that an in-world speaker's theory is objectively true.

Accordingly, a claim may correctly have:
- `confidence: high`
- while its `status` is `research_hypothesis`, `explicit_source_uncertainty`, or another modal/attributed status.

The `status` field preserves the source's epistemic framing; confidence records extraction/representation confidence.

## Speaker-resolution impact

No additional individual speakers were promoted in this pass.

The remaining 171 non-single-Subject INFO records are still intentionally handled as role, faction, state-variant, multi-actor, or other contextual dialogue unless deterministic identity evidence exists. The persisted raw text shards do not contain enough of the original Papyrus/condition/voice asset material to justify guessing additional named speakers.

## Remaining high-value follow-up

1. Re-ingest the original archive if available and persist a Papyrus source manifest with archive member paths and per-file hashes; optionally retain full source text where appropriate.
2. Revalidate `dwd-078` at byte/line level because it is the only current claim whose listed evidence is exclusively Papyrus.
3. Preserve full machine-readable dialogue condition/alias routing metadata in future imports so contextual speaker refinement can proceed without reopening the original ESP.
4. Continue central Elder Scrolls work/edition normalization for verified reused books without inventing central IDs.
