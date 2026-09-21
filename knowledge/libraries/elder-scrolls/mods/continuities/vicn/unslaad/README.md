# UNSLAAD continuity

**Continuity ID:** tes.mod.vicn.unslaad  
**Parent continuity:** tes.mod.vicn  
**Primary source:** user-provided translated Unslaad.esm (UNSLAAD 3.0.6)  
**Source SHA-256:** 1dabd2782ad6f4af565ace37fbe198c497d18f7a9ae0d2f36d892d743454b05b  
**Source size:** 10,432,096 bytes

UNSLAAD is stored under the shared **Vicn continuity** with **VIGILANT**, **GLENMORIL**, and **DAc0da**. Source-level claims remain attributable to UNSLAAD unless another Vicn work independently supports them. Nothing in this layer is silently promoted into official Elder Scrolls canon.

## Initial direct ESM inventory

The first deterministic parser pass found **44,103 records**, including:

- 833 INFO records with **1,015 embedded response strings**
- 661 DIAL records, including 383 named/player-facing topic prompts
- 52 QUST records
- 517 NPC_ records
- 50 BOOK records with embedded DESC text
- 98 MESG records
- 59 SCEN records
- 1,740 CELL records
- 7 WRLD records

The translated ESM is not localized, so its English dialogue and book text can be extracted directly without external string tables.

## High-priority narrative chain discovered

1. 0301D8FF — **Falling Cat** (zzzCrbMq01)
2. 0302299D — **Hoarfrost** (zzzCrbMq02)
3. 03112A83 — **When You Wish Upon a Star** (zzzCrbMq03)
4. 03117B3E — **Long Winter** (zzzCrbMq04)
5. 03117B3F — **Lingering Snow** (zzzCrbMq05)
6. 031DFDFA — **Stairway to Llesw'er** (zzzCrbMq06)
7. 031DFDFB — **The Owl Flies at Dusk** (zzzCrbMq07)
8. 03465EBF — **The Final Journey** (zzzCrbMq08)
9. 0347A32B — **Loveletter to the Fifth Era** (zzzCrbMq09)
10. 0347A38C — **Under the Elder Tree** (zzzCrbMq10)

## Initial recurring/important entities

Direct NPC records include **Ulliss**, **Aisha**, **Austella**, **Jhunal the Gray**, **Ja'cobee**, **Black Owl**, **Lizz**, **Arkved the Dreamer**, **Herkel the Fool**, **Wulf the Veteran**, and **Mankar Camoran's Eye**, among many others. These are only identity/index seeds; detailed claims require dialogue, quest, scene, book, and condition evidence.

## Cross-Vicn handling

Exact-name and concept overlaps already visible in the existing corpus include **Ja'cobee**, **Ulliss**, **Aisha**, **Jhunal**, and **Black Owl/Owl** material in GLENMORIL, plus substantial Jhunal/Owl material in VIGILANT. These are queued as cross-work relationship candidates, not automatic identity/equivalence assertions.

## Next ingestion passes

1. Build a DIAL-to-INFO dialogue transcript and preserve FormID provenance.
2. Resolve quest aliases and scenes to speaker identities where the ESM structurally supports it.
3. Extract all 50 BOOK texts with provenance and distinguish official reused texts from UNSLAAD-authored material.
4. Build character, location, artifact, and concept pages from direct evidence.
5. Compare recurrent Vicn nodes against GLENMORIL/VIGILANT/DAc0da without collapsing contradictory or source-specific claims.
