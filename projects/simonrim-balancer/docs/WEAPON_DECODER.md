# WEAP decoder checkpoint — 2026-09-23

This checkpoint decodes all 216 supplied Skyrim/SSE WEAP records with the documented 100-byte DNAM layout.

Decoded design-facing fields include animation type, speed, reach, stagger, governing skill, ranges, weapon flags, critical data, enchantment charge, equip/enchantment references, keywords, and sound detection. Unknown/reserved offsets remain explicitly unknown rather than inferred.

Schema reference: UESP TES5/SSE WEAP record format as mirrored in Holastor/skyrim-record-parser at commit 533c29b34cbe430636cc608e5b1347a65d3f1fbe.

Validation:
- WEAP records found: 216
- successfully decoded: 216
- failures: 0
- DNAM size: 100 bytes for all 216
- descriptive baseline groups: 21
- groups with n >= 3: 18
- exact imported-baseline field deltas: 18
- approved rules: 0

Guardrail: weapon baseline rows and deltas are evidence, not approved Simonrim rules.
