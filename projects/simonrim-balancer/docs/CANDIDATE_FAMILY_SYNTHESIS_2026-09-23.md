# Candidate Family Synthesis — 2026-09-23

This checkpoint advances P7 review structure after supplied-source ingestion was exhausted.

## Input

- 273 rule candidates from the current review matrix.
- 256 repeated implementation-pattern candidates.
- 17 explicit author/FOMOD candidates.
- Approved rules remain **0**.

## Deterministic family pass

The 273 candidates are grouped into **149 review families**.

- **66** families contain more than one candidate.
- **56** families span more than one Simonrim mod.
- **13** families contain at least one member with promotion-readiness score >= 55.
- Every original candidate remains individually addressable through `candidate_family_members.csv`.

For observed implementation candidates, the family signature:
1. removes the per-row `observed center` numeric payload;
2. replaces remaining numeric literals with `<num>`;
3. preserves categorical/mechanical structure.

For explicit author claims, the first pass groups statements by author-described module role such as reversion, compatibility patch, feature addon, integration addon, optional module, or runtime settings.

This is intentionally conservative. Family membership means “review these together,” not “these are one rule.”

## High-value review families

Several families are especially useful once vanilla/DLC baselines are available:

- **Perk entry-point magnitude multiplication** appears across Adamant, Blade and Blunt, Hand to Hand, and Mysticism.
- **Apply Combat Hit Spell / Select Spell** appears across Adamant, Blade and Blunt, and Hand to Hand.
- **Incoming spell magnitude multiplication** appears across Adamant, Blade and Blunt, and Hand to Hand.
- **Power-attack damage multiplication** appears in Adamant and Hand to Hand.
- **Conjuration target-location summon profiles** recur across Adamant and Mysticism.
- **Explosion and hazard delivery shapes** recur across Adamant and Mysticism.
- Author-described **reversion modules** form a seven-candidate Blade and Blunt family that is useful for identifying deliberate main-file behavior by contrast.
- Author-described **compatibility**, **feature-addon**, and **integration-addon** families remain separated from main-file evidence so optional-module behavior cannot silently become a suite-wide rule.

## Guardrails

- Cross-mod recurrence does not by itself establish author intent.
- A normalized family signature can contain materially different numeric values.
- Alternative profiles and counterexamples remain attached at the candidate level.
- Missing Skyrim/Update/DLC baselines still limit causal interpretation of 1,619 external overrides.
- No candidate or family is auto-promoted.
- `approved_rule` remains false until explicit review.

## Outputs

- `data/derived/2026-09-23/candidate_families.csv`
- `data/derived/2026-09-23/candidate_family_members.csv`
- `data/derived/2026-09-23/candidate_family_checkpoint_compact.json`

## Next dependency

The next true ingestion task remains P6 baseline expansion: import the matching Skyrim.esm, Update.esm, Dawnguard.esm, HearthFires.esm, Dragonborn.esm, and any required Creation masters needed by the unresolved external override set. After that, recompute exact vanilla→Simonrim deltas and roll the stronger evidence back into these families.
