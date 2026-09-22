# BF Books ESO processing layer

This directory is a deterministic, review-oriented processing layer over the 4,277 full-text records in `../batches/`.

## Rules

- One analysis batch corresponds to exactly one source batch: 50 books, except the final 27.
- Automated topic/entity links are retrieval candidates, not promoted facts.
- Claim candidates quote or tightly preserve source sentences and remain `unreviewed_candidate`.
- A book's testimony is not converted into an objective historical fact.
- Exact text-hash matches to the already reviewed Apocryphal Library provenance ledger may inherit that source classification as corroboration.
- The `ZOS` editor-ID prefix remains a discovery hint, not independent proof of official provenance.
- Contradictions are candidates for review; incompatible testimony is preserved rather than collapsed.

## Per-book fields

Each row retains source identity plus genre/epistemic classification, reliability cues, existing-topic links, existing book-catalog links, unresolved named-entity candidates, and evidence-grounded claim candidates.

Global retrieval, claim-candidate and contradiction-candidate indexes are generated only after all 4,277 books are processed.
