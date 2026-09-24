# Dealing with Daedra book provenance refinement — pass 03

> **Historical-state note (2026-09-24):** This pass predates refinement pass 15. The Gallus and *Fundaments of Alchemy* work identities have since been externally verified; only stable central Personal Agent OS work/source records remain pending. See `refinement-pass-15-book-provenance-verification.md` and `../normalized/book-source-relations.json` for current status.

This pass converts the existing provenance and deduplication notes into a machine-readable routing layer.

## Central-source candidates

### Gallus/Mercer encoded journal — BOOK 054467AA

The record remains a strong base-game-reuse candidate because its content tracks the Skyrim Thieves Guild Gallus/Mercer/Karliah investigation.

No stable central Personal Agent OS work/source record was found in the repository search performed during this refinement.

Result:
- preserve the Dealing with Daedra BOOK as local provenance;
- mark it as an embedded base-game-story-text candidate;
- do **not** invent a central work ID;
- defer exact-text identity until a canonical Skyrim witness is available.

### Fundaments of Alchemy — BOOK 05815E32

The main primer is an established Elder Scrolls work attributed to Alyandon Mathierry, while Dealing with Daedra adds Arcadia-specific wrapper material.

A second witness exists in the current source library:

`knowledge/libraries/elder-scrolls/sources/bf-books-eso/batches/books-1151-1200.jsonl`
- Form ID: `01012E04`
- title: *Fundaments of Alchemy*
- author: Alyandon Mathierry
- text SHA-256: `a0943982753526977655531c591e902239731c3890ebbe0c899b6a6eacf82e8f`
- provenance: official ESO text via compilation plugin, still pending per-record source verification.

This is useful as a candidate external witness, but it is **not** promoted here to a stable canonical work ID.

The Dealing with Daedra overlay retains Arcadia's annotations/use, physical condition, later-diagram summary, Cyrodilic framing, and gameplay context.

## Exact local duplicate groups

Two previously audited groups are now represented structurally:

1. Deep Bible / supposed translated copy — two BOOK records, identical text hash.
2. Five magical-school reference books — five BOOK records, identical ciphertext hash.

These groups must count as one semantic text instance each when evaluating independent evidence.

## Output

See `../normalized/book-source-relations.json`.

This pass improves routing and deduplication without changing any lore proposition or source-authority judgment beyond what the prior evidence already supported.
