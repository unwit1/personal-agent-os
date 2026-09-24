# Central Elder Scrolls source candidates — Dealing with Daedra, batch 02

## Candidate 002 — Fundaments of Alchemy

Mod record:
- Form ID: 05815E32
- Editor ID: dealsalchemistprimer
- Work: *Fundaments of Alchemy*
- Author: Alyandon Mathierry.

## Identity verification

The work identity is now externally verified.

External game witness:
- *The Elder Scrolls IV: Oblivion*
- Form ID: `00024567`
- title: *Fundaments of Alchemy*
- author: Alyandon Mathierry
- the work also appears in ESO.

External reference:
- https://elderscrolls.fandom.com/wiki/Fundaments_of_Alchemy

The current central source library also contains an ESO compilation witness:

`knowledge/libraries/elder-scrolls/sources/bf-books-eso/batches/books-1151-1200.jsonl`
- Form ID: `01012E04`
- title: *Fundaments of Alchemy*
- author: Alyandon Mathierry
- source text SHA-256: `a0943982753526977655531c591e902239731c3890ebbe0c899b6a6eacf82e8f`

## Variant comparison

The original Dealing-with-Daedra BOOK payload was recovered from the preserved source-record shards.

Local full DESC SHA-256:
`219c71fa48d53a20855ea733efac8087a8427580284f217c36c22cac6e88060a`

After removing the Dealing-with-Daedra wrapper and its added summary line, the embedded primer and the stored ESO witness have the same normalized word sequence except for one spelling:

- Dealing with Daedra: `magickal`
- stored ESO witness: `magical`

Dealing with Daedra also inserts the line:
`A fundamental primer on Alchemy`

The local embedded-primer normalized SHA-256 after excluding that summary line is:
`693c5630ef622172bbe56ef7720977c089f13cc4629a92461b2c6e1fa74414c4`

Therefore this is best represented as a **near-exact established-work variant inside a continuity-specific wrapper**, not as an independently authored Dealing-with-Daedra book.

## Overlay-only material to preserve

- Arcadia's heavily used/marginally annotated copy;
- physical deterioration;
- the added summary line;
- mod-added summary of later diagrams/recipes;
- Cyrodilic-ingredient framing;
- gameplay/read-effect context.

## Lorekeeper treatment

The work identity is verified, but a stable central work/source record has not yet been assigned.

Recommended routing:
1. create/link a central *Fundaments of Alchemy* work when the central official-book corpus receives stable work identities;
2. preserve the Oblivion/ESO variant distinction rather than forcing one text hash;
3. retain the Dealing-with-Daedra wrapper and its tiny embedded-text variation as an overlay.

Status: **external work identity verified; central record pending**.

## Candidate 001 — Gallus's Encoded Journal

Candidate 001 has also been upgraded: the Dealing-with-Daedra payload is a whitespace-normalized exact match to the Skyrim encoded journal. See `central-source-candidates-01.md`.


## Resolution — refinement pass 17

Central routing is now complete at the work-identity level.

- work ID: `tes.work.fundaments-of-alchemy`
- central work path: `knowledge/libraries/elder-scrolls/books/works/tes.work.fundaments-of-alchemy.json`
- the Oblivion identity, ESO compilation witness, and DWD variant are retained as separate witnesses.

The DWD Arcadia wrapper and the `magickal` / `magical` spelling difference remain witness-level metadata; no single canonical normalized text has been elected.
