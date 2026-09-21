# Normalization status

This layer records deterministic/record-structural normalization performed directly against `Clockwork.esp`.

Speaker resolution prefers scene aliases and speaker-producing INFO/quest conditions. Multi-speaker results are deliberately retained as ambiguous instead of choosing a character from line wording.

Current coverage is recorded in `resolution-stats.json`:
- 888 INFO records analyzed
- 867 resolve to one or more candidate speakers
- 322 resolve to a single NPC form
- 21 remain unresolved
- unique named counts: Lahar 192, Lamashtu 125, primary Amalgam 5

Browseable uniquely attributed transcript material is being staged under `../dialogue/`. This pass completes Lahar and primary Amalgam. The raw full dialogue source remains `../raw/dialogue-transcript.txt.gz`.

Future normalization should persist compact condition-level INFO/QUST indexes and continue resolving the broad Gilded/faction/voice-type ambiguity set without guessing.
