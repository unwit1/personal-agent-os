# Central Elder Scrolls source candidates — Dealing with Daedra

## Candidate 001 — Gallus's Encoded Journal

Mod record:
- Form ID: 054467AA
- Editor ID: dealsencodedjournal
- Local title: *Encoded Dossier*
- Rendering: Falmer font / encoded presentation.

## Identity verification

The imported payload is now verified as reused Skyrim text rather than merely a narrative match.

External Skyrim witness:
- Work: *Gallus's Encoded Journal*
- Author: Gallus Desidenius
- Skyrim Form ID: `000CEDA6`
- Skyrim editor ID: `TG05GallusJournalPre`
- translated journal witness: `0001BB6D` / `TG05GallusJournal`

Comparison against the recovered Dealing-with-Daedra raw BOOK payload:
- remove the `$FalmerFont` presentation tag;
- normalize whitespace;
- 471 words compare identically to the public encoded-journal transcription;
- normalized Dealing witness SHA-256: `f10bf3dd333a2db65030e273c5b778b68052744aa4b7f98ac3146ae792ebea3b`;
- full local DESC SHA-256: `4f6698017b5e99ac14281559586b2501ffc247a38487ed35c73c4b6127b64617`.

External verification references:
- https://gs11.ru/the-elder-scrolls-5-skyrim/knigi/zashifrovannyj-dnevnik-galla
- https://elderscrolls.fandom.com/wiki/Gallus%27s_Journal

## Lorekeeper treatment

The work identity and normalized text identity are verified, but the central Personal Agent OS source record does not yet exist.

Recommended routing:
1. create/link a central Skyrim work/source record for *Gallus's Encoded Journal* when the central vanilla-book corpus is ingested;
2. route the reused 471-word journal payload to that central work;
3. keep the Dealing-with-Daedra local title (*Encoded Dossier*), placement/context, and Falmer-font wrapper as continuity-local overlay metadata;
4. do not generate a duplicate mod-original lore history from the reused journal prose.

Status: **external identity and text verified; central repository record pending**.


## Resolution — refinement pass 17

Central routing is now complete at the work-identity level.

- work ID: `tes.work.gallus-encoded-journal`
- central work path: `knowledge/libraries/elder-scrolls/books/works/tes.work.gallus-encoded-journal.json`
- DWD witness remains BOOK `054467AA` with local title/presentation/placement preserved as overlay metadata.

A single canonical normalized text has not been elected; the work record intentionally keeps witness identity separate from text-edition identity.
