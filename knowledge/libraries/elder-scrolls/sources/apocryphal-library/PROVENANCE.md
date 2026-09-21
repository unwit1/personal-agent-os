# Apocryphal Library provenance

All **784 BOOK records** extracted from `LB_ApocryphaBooks.esp` now have an origin classification. The plugin is a compilation source, not automatic authority for the original continuity of each text.

## Completed classification

| Status | Count | Retrieval meaning |
|---|---:|---|
| `verified_mod_original_text` | 389 | Apocryphal Library/mod-continuity material; do not silently use as Bethesda/ZeniMax canon. |
| `verified_official_game_text` | 288 | Imported/matched official in-game Elder Scrolls material. |
| `verified_mod_construct_text` | 67 | Environmental/filler/constructed material, including Mage Script and empty records; normally exclude from lore claims. |
| `verified_external_author_text` | 35 | Out-of-game external/community lore writing; keep separate from official and mod-original material. |
| `verified_developer_text` | 5 | Out-of-game/developer or obscure text; keep separate from in-game primary sources. |
| Unresolved | **0** | Classification complete. |

Total: **784 / 784**. The authoritative machine-readable ledger is [`provenance-triage.json`](./provenance-triage.json).

## Canon and retrieval rules

1. Presence in the compilation never by itself establishes official canon.
2. Preserve compilation FormID, editor ID, text path, and source provenance after identifying an earlier source.
3. Strict official-lore retrieval should include `verified_official_game_text` by default and exclude other classes unless explicitly requested.
4. Developer/obscure, external/community, and mod-original material must remain separately filterable.
5. `verified_mod_construct_text` should normally be excluded from semantic lore retrieval unless the query concerns the compilation, environmental storytelling, scripts/languages, or source archaeology.
6. Conflicting claims retain source class and provenance rather than being flattened into a single asserted fact.
7. Editor-ID markers are discovery hints, not proof.

## Source-author distinction

Apocryphal Library's author describes the mod as a mixture of newly written books and notes, texts from older Elder Scrolls games, writings from authors hosted by The Imperial Library, developer works, and deliberately unreadable/translated environmental material. The author specifically warns users to credit the correct original author rather than assuming every included text is theirs. Origin class is therefore stored separately from compilation provenance.

## Existing normalized catalog links

- [Daedric Worship and the Dark Elves](../../../books/catalog/daedric-worship-and-the-dark-elves.md) — official ESO text with a full-text copy supplied by the compilation.
- [Parables of Saint Vorys](../../../books/catalog/parables-of-saint-vorys.md) — official ESO text with a full-text copy supplied by the compilation.

## Historical overlays

Early verification used additive overlays under [`provenance/`](./provenance/) while the baseline ledger was mostly unresolved. They remain audit history, but the current authoritative classification state is `provenance-triage.json`.
