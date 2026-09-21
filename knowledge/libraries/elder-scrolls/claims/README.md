# Claims

Evidence-backed claims, citations/provenance, competing interpretations, contradictions, and unreliable-source handling.

## Claim-bundle convention

Claim bundles are currently stored as human-readable Markdown so they remain Git-browsable before the reusable Knowledge Library database layer is implemented.

Each promoted claim should have:

- a stable claim ID;
- a concise proposition;
- continuity scope;
- status such as supported, attributed, disputed, qualified, or unresolved;
- epistemic mode;
- confidence;
- evidence pointers;
- optional `Supports`, `Contradicts`, and `Qualifies` edges;
- relationships that can later be materialized into structured entity/relationship tables.

### Stable ID guidance

Use lowercase dot-separated IDs that encode continuity/domain/entity/relation where practical.

Examples:

- `vicn.jhunal.gray-owl.direct-identity`
- `vicn.saarthal.anti-ysgramor-testimony`
- `unslaad.ulliss.revival-costs-dragon-soul`

Claim IDs should remain stable even if the explanatory Markdown moves.

## Evidence rule

A claim may point to:

1. raw game/plugin record IDs;
2. normalized source records;
3. source-specific dialogue/book/message pages;
4. parent synthesis pages, only when the synthesis itself is the claim being represented.

Prefer raw/normalized source evidence over synthesis pages when available.

## Epistemic rule

Distinguish:

- deterministic implementation fact;
- direct participant testimony;
- reported historical testimony;
- myth/dream/prophecy;
- system/UI statement;
- reused external text;
- cross-work synthesis;
- unresolved interpretation.

A character saying something happened is not automatically the same as the library asserting it objectively happened.

## Contradiction rule

Do not delete or silently merge incompatible claims.

Represent both claims and connect them using:

- `Contradicts`
- `Qualifies`
- `Supports`

The future SQLite/structured claim graph should preserve these same stable IDs and edges.

## Current VICN coverage

See:
- `vicn-claim-coverage.md` for generated bundle/claim/edge coverage and remaining review targets;
- `vicn-claim-index.jsonl` for compact machine-readable claims;
- `vicn-claim-edges.jsonl` for stable support/contradiction/qualification edges.

Do not maintain a hand-written exhaustive bundle list here; the generated coverage report is canonical for current claim-bundle inventory.

## Migration target

When the reusable Knowledge Library subsystem is implemented, these Markdown bundles should be machine-migrated into:

- entities;
- relationships;
- claims;
- evidence;
- contradiction/support edges;
- provenance records.

The Markdown should remain a browsable report/export rather than becoming the only source of structure.

## Generated structured indexes

- `vicn-claim-index.jsonl` — deterministic claim rows generated from the reviewed VICN Markdown bundles.
- `vicn-claim-edges.jsonl` — deterministic `supports`, `contradicts`, and `qualifies` edges between stable claim IDs.

The Markdown bundles remain the reviewable source. The JSONL files are compact machine-retrieval/migration surfaces and should be regenerated when claim bundles change.
