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
- All **322 single-NPC-resolved INFO records** have browseable named-character transcripts: Lahar 192, Lamashtu 125, primary Amalgam 5.
- All **545 multi-candidate INFO records** are explicitly cataloged: 519 broad Gilded-pool and 26 Amalgam-form-pool records.
- The strict resolver's **21 no-NPC-candidate records** are all accounted for by a supplemental scene/quest pass: 20 Amalgam speaker-horn lines and one Amalgam encounter-scene line.

## Dialogue normalization

The strict resolver uses scene actor aliases and speaker-producing conditions such as `GetIsID`, `GetInFaction`, and `GetIsVoiceType`. It preserves ambiguity instead of assigning lines from wording.

A supplemental semantic layer then uses scene ownership, quest aliases, and quest-state evidence for non-NPC delivery forms. The lower-level statistics remain unchanged for reproducibility.

See `normalized/resolution-stats.json` and `normalized/semantic-resolution.json`.

## Browse

- `books/` — exact decoded in-game book/note text
- `raw/` — archival dialogue and quest record text extracted from the ESP
- `dialogue/` — strict speaker transcripts, ambiguity pools, and supplemental diegetic attributions
- `quests/` — journal stages, objectives, and resolved aliases
- `topics/` — evidence-backed Clockwork lore topics
- `entities/characters/` — character pages
- `entities/relationships.md` — relationship index with evidence/status
- `events/ludwig-clockwork-timeline.md` — dated Ludwig/Clockwork chronology
- `claim-seeds.json` — evidence-backed claim seeds
- `source-manifest.json` — source/book manifest and hashes

## Provenance rule

Clockwork testimony remains scoped to this continuity. In particular, Lamashtu's statements about Kagrenac, the Heart of Lorkhan, and her own death remain character testimony rather than an objective answer to the canonical Dwemer disappearance.
