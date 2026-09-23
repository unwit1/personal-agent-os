# CSTY decoder checkpoint — 2026-09-23

This checkpoint decodes all 62 supplied Blade and Blunt CSTY records using the documented TES5/SSE combat-style field layouts.

Decoded fields include general offensive/defensive/equipment multipliers, threat avoidance, melee stagger/power-attack/bash weights, close-range dueling/flanking behavior, long-range strafe weighting, flight behavior, and DATA flags for Dueling, Flanking, and Allow Dual Wielding.

Schema reference: UESP TES5/SSE CSTY record format as mirrored in Holastor/skyrim-record-parser at commit `533c29b34cbe430636cc608e5b1347a65d3f1fbe`.

Validation:
- CSTY records found: 62
- successfully decoded: 62
- failures: 0
- all 62 use full-size CSGD(40), CSME(32), CSCR(16), CSLR(4), CSFL(32), DATA(4)
- descriptive groups: 12
- groups with n >= 3: 7
- exact imported baselines: 0
- external Skyrim.esm baselines: 62
- approved rules: 0

Exception retained: `csDraugrMagic` has neither Dueling nor Flanking set. It is preserved verbatim rather than coerced to the documented usual flag pattern.
