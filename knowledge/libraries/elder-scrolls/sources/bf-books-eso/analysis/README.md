# BF Books ESO analysis

First-pass structured lore analysis for the 4,277 `BOOK` records extracted from `BF_Books_ESO.esp`.

## Coverage

- Books analyzed: **4,277 / 4,277**
- Analysis batches: **86 / 86**
- Commit cadence: one analysis commit per 50 books; final batch contains 27
- Entity candidates emitted: **61,778**
- Evidence-hashed claim seeds emitted: **11,812**
- Analysis version: `eso-books-first-pass-v1`

## Per-record fields

Each JSONL analysis row preserves the source `ordinal`, `form_id`, `editor_id`, `title`, and `text_sha256`, then adds:

- `provenance_status`
- `document_type`
- `epistemic_mode`
- `topic_tags`
- `candidate_entities`
- `claim_seeds`
- `review_status`

## Epistemic safety

This pass is a **candidate-generation layer**, not a canon-promotion layer.

- Statements in journals, letters, myths, histories, religious works, and scholarly texts remain source statements.
- `claim_seeds` are marked `candidate_only_requires_review`.
- Candidate entities are retrieval aids and may include titles, headings, or false-positive proper nouns.
- Individual ESO provenance remains pending verification against original ESO game data, UESP, or The Imperial Library.
- No candidate claim from this pass should be treated as objective fact until reviewed and promoted into a stable claim bundle with evidence pointers.

## Document-type counts

- Other/unclassified: 1,980
- Scholarly treatise: 499
- Journal: 495
- Report/account/order: 398
- Letter/correspondence: 370
- Note: 212
- Myth/legend/literary tale: 189
- Religious text: 69
- Legal/administrative: 65

## Epistemic-mode counts

- Source statement, unclassified: 2,254
- Direct/personal testimony: 1,077
- Reported scholarly testimony: 449
- Myth/legend/literary account: 439
- Administrative/normative statement: 58

## Next promotion pass

The next pass should:

1. verify per-record original ESO provenance;
2. resolve entity candidates against existing Elder Scrolls entity/topic pages;
3. deduplicate aliases and repeated texts;
4. review claim seeds in source context;
5. promote only reviewed claims into stable claim bundles;
6. connect `Supports`, `Contradicts`, and `Qualifies` edges;
7. update topic dossiers from promoted evidence rather than raw candidate frequency.

The raw book text in `../batches/` remains the authoritative evidence layer.