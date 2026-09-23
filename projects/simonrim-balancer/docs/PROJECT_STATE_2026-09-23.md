# Simonrim Balancer — Project State — 2026-09-23

## Source-ingestion state

**Complete for the four supplied archives.**

Imported versions:
- Adamant 6.0.4
- Hand to Hand 2.0.2
- Blade and Blunt 4.0.3
- Mysticism 2.5.0

Coverage boundary:
- 6,009 plugin records
- 53 record types
- 0 unmapped record types
- 5,556 gameplay / behavioral / typed-support records
- 208 keyword identity records
- 224 presentation-support records
- 21 plugin headers
- 73 top-level source artifacts
- 476 BSA members
- 115 parsed Papyrus source files
- 169 decoded runtime/config behavior entries
- 20 FOMOD options

Remaining source limits are explicit evidence boundaries, not unfinished parsing:
- 1,619 overrides point to Skyrim/DLC baselines whose record bodies were not supplied.
- 2 native DLLs and 2 PDBs are inventoried but not reverse engineered.
- 208 attached script instances do not have matching supplied PSC source in these packages.
- Binary presentation/runtime assets are inventoried rather than converted into balance rules.

## Architecture state

Implemented evidence pipeline:

raw source → deterministic decoding → canonical Form resolution → typed relationships → exact deltas where baselines exist → observed patterns → rule candidates → review matrix

Important separation rules:
- AVIF tree lines are UI topology, not perk prerequisites; PERK CTDA is authoritative for gating.
- Strong evidence that a behavior exists is separate from evidence that it generalizes.
- Optional modules, compatibility patches, and reversion plugins carry contamination flags.
- Missing external baselines reduce generalizability instead of being guessed.
- Presentation-only data cannot independently create balance rules.

## Candidate layer

Current review corpus:
- 273 rule candidates
- 256 from repeated implementation patterns
- 17 from nontrivial author/FOMOD statements
- 17/17 explicit-author candidates have corresponding implementation evidence in the supplied archives
- 14/17 have strong implementation corroboration; 3/17 are implementation-present but baseline-limited
- 38 candidates have high evidence strength
- 235 have medium evidence strength
- 9 have medium generalizability; 264 remain low
- 50 have medium promotion readiness; 223 remain low
- 38 are high-evidence / low-generalizability cases
- **Approved rules: 0**

No candidate is automatically canonical.

## Next dependency

The most valuable next ingestion is no longer another pass over these archives. It is the matching Skyrim/Update/DLC master evidence needed to resolve the 1,619 external-baseline overrides. That would allow the balancer to distinguish absolute Simonrim values from deliberate changes to vanilla with much greater confidence.

After baseline completion, the next architecture milestones are:
1. attach exact vanilla→Simonrim deltas to candidate evidence;
2. cluster duplicate/related candidates into design-principle families;
3. identify exceptions and counterexamples explicitly;
4. review/promote narrowly scoped rules;
5. expose selective MCP/API queries for analysis and design assistance;
6. test the system against an external target mod.
