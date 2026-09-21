# Normalization status

This layer records deterministic/record-structural normalization performed directly against `Clockwork.esp`.

Speaker resolution prefers scene aliases and speaker-producing INFO/quest conditions. Multi-speaker results are deliberately retained as ambiguous instead of choosing a character from line wording.

## Coverage

- **888** INFO records analyzed
- **867** resolve to one or more candidate speakers
- **322** resolve to a single NPC form
- **545** resolve to multiple candidate forms
- **21** remain unresolved

Unique named counts:
- Lahar — **192**
- Lamashtu — **125**
- primary Amalgam — **5**

The three named-character totals equal all **322** single-NPC-resolved INFO records, so the unique-speaker transcript pass is complete.

The multi-candidate layer is now explicitly cataloged:
- **519** broad Gilded-pool INFO records → `../dialogue/gilded-ambient.md`
- **26** eight-form Amalgam-pool INFO records → `../dialogue/amalgam-form-pool.md`

The full raw source remains `../raw/dialogue-transcript.txt.gz`. Future normalization should focus on the 545 ambiguity cases and 21 unresolved records using stronger scene, quest-state, reference, package, and condition context rather than textual guessing.
