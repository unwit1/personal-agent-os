# Clockwork dialogue

Browseable dialogue derived directly from `Clockwork.esp`.

## Speaker-resolution policy

Only INFO records with a **single resolved NPC speaker** are promoted to the strict named-character transcript layer. Faction/shared-voice/multi-NPC matches remain ambiguous at physical-form level. SCEN and quest wiring may add a separate **supplemental semantic or alias-role attribution** without rewriting strict counts.

## Named-character transcripts — all 322 strict unique-NPC INFO records

- `lahar/` — **192** Lahar INFO records.
- `lamashtu/` — **125** Lamashtu INFO records.
- `amalgam.md` — **5** primary-Amalgam INFO records.

## Multi-candidate dialogue — 545 strict INFO records

- `gilded-ambient.md` — **519** records in the broad Gilded actor pool.
- `amalgam-form-pool.md` — **26** records in the eight-form Amalgam pool.

### Gilded scene-role refinement

SCEN `05384489` / `CLWSQ02GildedIntroScene01` binds **7** of the 519 broad-Gilded records to the quest roles `Gilded01`, `Gilded02`, or `Gilded03`. They remain multi-candidate physical NPCs, but only **512** broad-Gilded records remain truly undifferentiated.

See `gilded-intro-scene.md` and `../technical/scene-role-resolution.json`.

## Supplemental scene/quest resolution

- `amalgam-speaker-horn.md` — **20** technically unresolved INFO records delivered through `SpeakerHorn01`, semantically attributed to Amalgam.
- `INFO 0559A4B6` — the remaining strict no-candidate INFO record is tied by SCEN alias to the Amalgam encounter.

Thus the strict resolver still reports **21** no-NPC-candidate records for reproducibility, while the supplemental layer accounts for all 21 semantically. See `../normalized/semantic-resolution.json`.

The complete raw corpus remains in `../raw/dialogue-transcript.txt.gz`.
