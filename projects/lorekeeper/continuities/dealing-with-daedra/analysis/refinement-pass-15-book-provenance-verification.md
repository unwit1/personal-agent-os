# Dealing with Daedra refinement pass 15 — reused-book provenance verification

Date: 2026-09-24
Continuity: `tes.mod.dealing-with-daedra`

This pass resolves the *identity* of the two previously pending high-value centralization candidates while preserving the distinction between work identity, exact text identity, and central-repository identity.

## 1. Gallus's Encoded Journal / local “Encoded Dossier”

Local record:
- BOOK `054467AA`
- editor ID `dealsencodedjournal`
- local title `Encoded Dossier`
- full local DESC SHA-256 `4f6698017b5e99ac14281559586b2501ffc247a38487ed35c73c4b6127b64617`

The raw Dealing-with-Daedra payload was recovered from the preserved source-record shard bundle.

External Skyrim identity:
- work: *Gallus's Encoded Journal*
- author: Gallus Desidenius
- Skyrim Form ID `000CEDA6`
- editor ID `TG05GallusJournalPre`
- translated journal: `0001BB6D` / `TG05GallusJournal`

Comparison method:
1. remove the local `$FalmerFont` markup;
2. normalize whitespace;
3. compare the complete payload to a public transcription of Skyrim's encoded journal.

Result:
- 471 / 471 normalized words match;
- normalized local payload SHA-256 `f10bf3dd333a2db65030e273c5b778b68052744aa4b7f98ac3146ae792ebea3b`;
- identity status: **verified base-game text reuse**;
- exact-text status: **verified after presentation/whitespace normalization**.

References:
- https://gs11.ru/the-elder-scrolls-5-skyrim/knigi/zashifrovannyj-dnevnik-galla
- https://elderscrolls.fandom.com/wiki/Gallus%27s_Journal

The central Personal Agent OS vanilla-Skyrim work record is still absent. Do not invent a central path. When that corpus exists, route the reused journal text centrally while retaining DWD's local title, placement/context, and Falmer-font presentation as overlay metadata.

## 2. Fundaments of Alchemy

Local record:
- BOOK `05815E32`
- editor ID `dealsalchemistprimer`
- full local DESC SHA-256 `219c71fa48d53a20855ea733efac8087a8427580284f217c36c22cac6e88060a`

External work identity:
- *Fundaments of Alchemy*
- author Alyandon Mathierry
- *The Elder Scrolls IV: Oblivion* Form ID `00024567`
- also appears in ESO.

Current internal ESO witness:
`knowledge/libraries/elder-scrolls/sources/bf-books-eso/batches/books-1151-1200.jsonl`
- Form ID `01012E04`
- text SHA-256 `a0943982753526977655531c591e902239731c3890ebbe0c899b6a6eacf82e8f`

Reference:
- https://elderscrolls.fandom.com/wiki/Fundaments_of_Alchemy

### Variant comparison

The DWD wrapper and final Arcadia-specific summary were removed before comparison.

DWD also inserts the line:
`A fundamental primer on Alchemy`

After excluding that added summary line and normalizing whitespace, the DWD embedded primer and the stored ESO witness have the same word sequence except one spelling:
- DWD: `magickal`
- ESO witness: `magical`

Normalized DWD embedded-primer SHA-256 after excluding the summary line:
`693c5630ef622172bbe56ef7720977c089f13cc4629a92461b2c6e1fa74414c4`

Result:
- identity status: **verified established-work reuse**;
- text relationship: **near-exact variant**, not one exact hash;
- DWD-specific wrapper remains independent continuity evidence.

Preserve as overlay:
- Arcadia's heavily used and marginally annotated copy;
- physical deterioration;
- the added one-line description;
- summary of later diagrams/recipes;
- Cyrodilic-ingredient framing;
- gameplay/read-effect context.

## Normalization outcome

The two earlier “centralization candidates” are no longer uncertain at the work-identity level:
- Gallus: work identity + normalized text identity verified.
- Fundaments: work identity verified; ESO relation narrowed to a one-word spelling variant plus DWD-added wrapper/summary.

What remains unresolved is **central repository routing**, because stable central vanilla-Skyrim/official-work records have not yet been created for these works.

This distinction prevents both false uncertainty and premature creation of unsupported central IDs.
