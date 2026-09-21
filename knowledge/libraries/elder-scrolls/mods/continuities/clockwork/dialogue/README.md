# Clockwork dialogue

Browseable dialogue derived directly from `Clockwork.esp`.

## Speaker-resolution policy

Only INFO records with a **single resolved speaker** are promoted to a named-character transcript. Records resolving to a faction, shared voice type, or multiple candidate NPCs stay in the raw/normalized evidence layer instead of being guessed from wording.

## Current transcripts

- `lahar/` — all **192** uniquely attributable Lahar INFO records.
- `amalgam.md` — all **5** INFO records uniquely attributable to primary Amalgam NPC `05510DF1`.
- Lamashtu has **125** uniquely attributable INFO records in the normalized extraction and is the next transcript staging target.

The raw corpus remains in `../raw/dialogue-transcript.txt.gz`; speaker-resolution coverage is in `../normalized/resolution-stats.json`.
