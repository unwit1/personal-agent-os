# Clockwork

Sub-continuity for the Skyrim mod **Clockwork**.

- Continuity ID: `tes.mod.clockwork`
- Primary source: user-provided `Clockwork.esp`
- ESP SHA-256: `6850eb707a5b47f60fcec7bfb3494a4d7e909549c6c199cca81fc18780f73406`
- Continuity policy: mod-added lore may reference official Elder Scrolls material but must not overwrite or silently become Bethesda continuity.

## Ingested source corpus

- **13/13 BOOK records** are preserved as individual files in `books/`.
- **242 DIAL topics / 888 INFO records** are represented in the raw dialogue corpus.
- **520 direct response strings** expand to **1,103 effective response strings** after following Skyrim `DNAM` response-data reuse.
- **12 QUST records** are preserved in the raw quest corpus.
- Player-facing quest pages are browsable in `quests/`.
- Core Clockwork characters and Ludwig's chronology are browsable in `entities/` and `events/`.

## Dialogue normalization

The current resolver uses scene actor aliases and speaker-producing conditions such as `GetIsID`, `GetInFaction`, and `GetIsVoiceType`.

- 867 / 888 INFO records resolve to one or more plausible speaker candidates.
- 322 INFO records resolve to a single NPC form.
- 21 INFO records remain unresolved.
- Named-character dialogue is only promoted when attribution is unique; broad Gilded/faction/voice-type matches remain ambiguous evidence.

See `normalized/resolution-stats.json`.

## Browse

- `books/` — exact decoded in-game book/note text
- `raw/` — archival dialogue and quest record text extracted from the ESP
- `quests/` — journal stages, objectives, and resolved aliases for player-facing quests
- `entities/characters/` — evidence-backed Clockwork character pages
- `events/ludwig-clockwork-timeline.md` — dated chronology from Ludwig's journals
- `claim-seeds.json` — initial evidence-backed claims with FormID provenance
- `source-manifest.json` — source/book manifest and hashes

## Provenance rule

Clockwork testimony remains scoped to this continuity. In particular, Lamashtu's statements about Kagrenac, the Heart of Lorkhan, and her own death are preserved as character testimony rather than converted into an objective answer to the canonical Dwemer disappearance.
