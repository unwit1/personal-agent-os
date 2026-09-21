# Normalization status

This layer records deterministic/record-structural normalization performed directly against `Clockwork.esp`.

Speaker resolution prefers scene aliases and speaker-producing INFO/quest conditions. Multi-speaker results are deliberately retained as ambiguous instead of choosing a character from line wording.

## Strict structural coverage

- **888** INFO records analyzed
- **867** resolve to one or more NPC candidate speakers
- **322** resolve to a single NPC form
- **545** resolve to multiple candidate forms
- **21** have no NPC-form candidate in the strict resolver

Unique named counts:
- Lahar — **192**
- Lamashtu — **125**
- primary Amalgam — **5**

The three named-character totals equal all **322** strict single-NPC-resolved INFO records.

The multi-candidate layer is cataloged as:
- **519** broad Gilded-pool INFO records → `../dialogue/gilded-ambient.md`
- **26** eight-form Amalgam-pool INFO records → `../dialogue/amalgam-form-pool.md`

## Supplemental semantic resolution

A second pass using scene ownership, quest aliases, and quest-stage context accounts for all **21** strict unresolved records without altering the reproducible structural statistics:

- **20** are scene lines delivered through `SpeakerHorn01`, alias 0 of `CLWDialogueAmalgam`, and are semantically attributed to Amalgam's remote voice.
- **1** (`INFO 0559A4B6`) is tied by scene actor alias 3 to `CLWLvlAmalgamCenturionAmbush` / Amalgam.

See `semantic-resolution.json` and `../dialogue/amalgam-speaker-horn.md`.

The full raw source remains `../raw/dialogue-transcript.txt.gz`. Future speaker work should focus on whether the 545 multi-candidate records can be narrowed further from package/reference/scene-state data without inventing certainty.
