# Clockwork dialogue

Browseable dialogue derived directly from `Clockwork.esp`.

## Speaker-resolution policy

Only INFO records with a **single resolved NPC speaker** are promoted to the strict named-character transcript layer. Records resolving to a faction/shared voice/multiple NPCs stay explicitly ambiguous. Scene dialogue delivered through non-NPC objects may receive a separate **supplemental semantic attribution** when scene/quest wiring supports it.

## Named-character transcripts — all 322 strict unique-NPC INFO records

- `lahar/` — all **192** uniquely attributable Lahar INFO records.
- `lamashtu/` — all **125** uniquely attributable Lamashtu INFO records.
- `amalgam.md` — all **5** INFO records uniquely attributable to primary Amalgam NPC `05510DF1`.

## Multi-candidate dialogue — 545 INFO records

- `gilded-ambient.md` — **519** records resolving to the broad Gilded actor pool.
- `amalgam-form-pool.md` — **26** records resolving to the eight Amalgam NPC/encounter forms.

## Supplemental scene/quest resolution

- `amalgam-speaker-horn.md` — **20** technically unresolved INFO records whose scene actor is `SpeakerHorn01` in the `CLWDialogueAmalgam` quest; semantically attributed to Amalgam's remote voice.
- `INFO 0559A4B6` — the remaining technically unresolved record is tied by its scene actor alias to `CLWLvlAmalgamCenturionAmbush` / Amalgam.

Thus the strict resolver still reports **21 unresolved** NPC-form speakers, but the supplemental scene/quest pass accounts for all 21 semantically. See `../normalized/semantic-resolution.json`.

The complete raw dialogue corpus remains in `../raw/dialogue-transcript.txt.gz`.
