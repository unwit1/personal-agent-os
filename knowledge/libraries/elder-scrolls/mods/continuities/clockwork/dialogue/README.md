# Clockwork dialogue

Browseable dialogue derived directly from `Clockwork.esp`.

## Speaker-resolution policy

Only INFO records with a **single resolved speaker** are promoted to a named-character transcript. Records resolving to a faction, shared voice type, or multiple candidate NPCs remain explicitly ambiguous instead of being guessed from wording.

## Named-character transcripts — all 322 unique-speaker INFO records

- `lahar/` — all **192** uniquely attributable Lahar INFO records.
- `lamashtu/` — all **125** uniquely attributable Lamashtu INFO records.
- `amalgam.md` — all **5** INFO records uniquely attributable to primary Amalgam NPC `05510DF1`.

## Multi-candidate dialogue — 545 INFO records

- `gilded-ambient.md` — **519** records resolving to the broad Gilded actor pool; retained as collective/ambient evidence.
- `amalgam-form-pool.md` — **26** records resolving to the eight Amalgam NPC/encounter forms; full INFO text retained without choosing one physical form.

## Unresolved

- **21** INFO records currently have no resolved speaker candidate.

The complete raw dialogue corpus remains in `../raw/dialogue-transcript.txt.gz`; speaker-resolution coverage is recorded in `../normalized/resolution-stats.json`.
