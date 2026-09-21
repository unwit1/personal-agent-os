# Clockwork

Sub-continuity for the Skyrim mod **Clockwork**.

- Continuity ID: `tes.mod.clockwork`
- Primary source: user-provided `Clockwork.esp`
- ESP SHA-256: `6850eb707a5b47f60fcec7bfb3494a4d7e909549c6c199cca81fc18780f73406`
- Continuity policy: mod-added lore may reference official Elder Scrolls material but must not overwrite or silently become Bethesda continuity.

## Ingested source corpus

- **13/13 BOOK records** are preserved as individual files in `books/`.
- **242 DIAL topics / 888 INFO records** are represented in the raw dialogue corpus.
- **520 direct response strings** expand to **1,103 effective response strings** after Skyrim `DNAM` response-data reuse.
- **12 QUST records** are preserved in the raw quest corpus.
- Player-facing quest pages are browsable in `quests/`.
- Core characters, relationships, and Ludwig's chronology are browsable in `entities/` and `events/`.
- Continuity-local concept/location/technology pages are browsable in `topics/`.
- `dialogue/lahar/` contains all **192** INFO records uniquely attributable to Lahar; `dialogue/amalgam.md` contains the **5** uniquely attributable primary-Amalgam INFO records.

## Dialogue normalization

The resolver uses scene actor aliases and speaker-producing conditions such as `GetIsID`, `GetInFaction`, and `GetIsVoiceType`.

- 867 / 888 INFO records resolve to one or more plausible speaker candidates.
- 322 INFO records resolve to a single NPC form.
- 21 INFO records remain unresolved.
- Major unique counts: Lahar 192; Lamashtu 125; primary Amalgam 5.
- Named-character transcripts promote only unique attribution. Broad Gilded/faction/voice-type matches remain ambiguous evidence.

See `normalized/resolution-stats.json`.

## Browse

- `books/` — exact decoded in-game book/note text
- `raw/` — archival dialogue and quest record text extracted from the ESP
- `dialogue/` — speaker-resolved browseable transcript material
- `quests/` — journal stages, objectives, and resolved aliases
- `topics/` — evidence-backed Clockwork lore topics
- `entities/characters/` — character pages
- `entities/relationships.md` — relationship index with evidence/status
- `events/ludwig-clockwork-timeline.md` — dated Ludwig/Clockwork chronology
- `claim-seeds.json` — evidence-backed claim seeds
- `source-manifest.json` — source/book manifest and hashes

## Provenance rule

Clockwork testimony remains scoped to this continuity. In particular, Lamashtu's statements about Kagrenac, the Heart of Lorkhan, and her own death remain character testimony rather than an objective answer to the canonical Dwemer disappearance.
