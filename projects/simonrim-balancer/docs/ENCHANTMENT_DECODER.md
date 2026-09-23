# ENCH decoder checkpoint — 2026-09-23

This checkpoint decodes all 269 supplied Skyrim/SSE ENCH records using the documented 36-byte ENIT layout and joins their EFID/EFIT effects to decoded MGEF evidence.

Decoded design-facing fields include enchantment cost and amount, flags, manual-calculation state, ExtendDurationOnRecast, cast type, delivery, enchantment type, charge time, base enchantment, worn restrictions, effect composition, effect magnitudes/areas/durations, effect skills/archetypes/base costs, and effect-level condition counts.

Schema reference: UESP TES5/SSE ENCH record format as mirrored in Holastor/skyrim-record-parser at commit `533c29b34cbe430636cc608e5b1347a65d3f1fbe`.

Validation:
- ENCH records found: 269
- successfully decoded: 269
- failures: 0
- ENIT size: 36 bytes for all 269
- effect rows: 870
- effect-level conditions: 101
- descriptive baseline groups: 36
- groups with n >= 3: 27
- exact imported-baseline field deltas: 58
- approved rules: 0

Delta validation:
- 55 deltas change `effect_count`.
- 3 deltas change `enit_flags_hex` from `0x00000001` to `0x00000005`, adding `ExtendDurationOnRecast` while retaining `ManualCalc` on bound-weapon enchantments.

The estimated auto-calc field is diagnostic evidence only, not an approved balance formula. Raw plugin bytes remain authoritative.
