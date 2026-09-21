# Normalization status

This layer records deterministic/record-structural normalization performed directly against `Clockwork.esp`.

Speaker resolution prefers scene aliases and speaker-producing INFO/quest conditions. Multi-speaker results are deliberately retained as ambiguous instead of choosing a character from line wording.

Current coverage is recorded in `resolution-stats.json`. The next machine-data pass should persist full condition-level normalized INFO/QUST JSON and then build retrieval indexes from those records.
