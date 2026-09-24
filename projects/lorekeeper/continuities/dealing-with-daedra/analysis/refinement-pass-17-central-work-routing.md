# Dealing with Daedra refinement pass 17 — central work routing

Date: 2026-09-24  
Continuity: `tes.mod.dealing-with-daedra`

This pass closes the remaining central-work routing gap for the two high-value reused books verified in refinement pass 15.

## Central normalized work records created

### Gallus's Encoded Journal

Central work:
- work ID: `tes.work.gallus-encoded-journal`
- path: `knowledge/libraries/elder-scrolls/books/works/tes.work.gallus-encoded-journal.json`

Dealing with Daedra witness:
- BOOK `054467AA`
- editor ID `dealsencodedjournal`
- local title: `Encoded Dossier`
- relation: exact text after removing Falmer-font presentation markup and normalizing whitespace
- local presentation/placement remains a DWD overlay.

The central work record also retains the verified Skyrim identity:
- FormID `000CEDA6`
- editor ID `TG05GallusJournalPre`
- author Gallus Desidenius

The related translated Skyrim journal `0001BB6D` / `TG05GallusJournal` is recorded as a related witness/record rather than silently conflated with the encoded text.

### Fundaments of Alchemy

Central work:
- work ID: `tes.work.fundaments-of-alchemy`
- path: `knowledge/libraries/elder-scrolls/books/works/tes.work.fundaments-of-alchemy.json`

The work record keeps separate witnesses for:
- Oblivion FormID `00024567` identity;
- the local BF Books ESO compilation witness `01012E04`;
- DWD BOOK `05815E32`.

The DWD witness remains a near-exact variant plus continuity wrapper. Its Arcadia-specific annotations/framing, added summary material, physical-state framing, and one-word `magickal` / `magical` difference remain local witness metadata.

## Work/witness policy

The central `knowledge/libraries/elder-scrolls/books/` layer now explicitly separates:
- **work identity** — stable cross-source identity;
- **witness identity** — game/source/mod-specific record;
- **variant/overlay metadata** — spelling, wrapper, annotation, placement, presentation, and other source-specific changes.

Creating a work record does **not** elect one witness as the canonical normalized text.

Both new work records therefore use:
- `work_identity_status: verified`
- `canonical_text_status: not_elected`

This lets mod continuities reference a shared work without duplicating or flattening variant text.

## DWD routing result

`normalized/book-source-relations.json` now routes:
- `054467AA` → `tes.work.gallus-encoded-journal`
- `05815E32` → `tes.work.fundaments-of-alchemy`

The earlier `central_record_pending` state is resolved for these two works.

## Remaining central-source work

The central normalized book catalog is still very small. These two records establish the work/witness pattern but do not imply that the broader vanilla/official Elder Scrolls book corpus has been normalized.

Future imports should:
1. assign stable work IDs only after identity verification;
2. keep game/source-specific witnesses separate;
3. preserve text hashes and variant relationships;
4. avoid copying known central work text into every mod continuity;
5. retain mod-specific wrappers and placement as continuity overlays.
