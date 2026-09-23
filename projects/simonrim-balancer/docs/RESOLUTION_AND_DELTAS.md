# FormID Resolution and Override Evidence — 2026-09-23

## Canonical Form identity

For the supplied Skyrim plugins, a record/reference FormID is normalized as:

<origin plugin>:<lower 24-bit object id>

The high byte is interpreted against the source plugin's ordered master list:

- slot below master count: the named master owns the Form
- slot equal to master count: the current plugin owns a new Form
- slot above master count: unresolved/error

All 5,988 non-header records, 11,676 original deterministic relations, and 3,951 effect references resolve without a slot failure in this snapshot.

## Override baseline policy

The balancer does not pretend an unimported Skyrim/DLC record body is available. For an override, it searches the current plugin's masters in reverse order and uses the nearest imported master containing the same canonical Form as the exact comparison baseline.

Baseline states:

- none_new_record
- imported_master
- external_master_not_imported

Current counts:

- 3,832 new local Forms
- 2,156 overrides
- 537 overrides with exact imported baselines
- 1,619 overrides with external/unimported baselines
- 567 canonical Forms with multiple imported versions
- 1,145 imported override-chain rows
- 484 exact-baseline overrides change bytes
- 53 are byte-identical forwards
- 311 typed field deltas currently emitted

## Identical forwards

An identical forwarded record is compatibility/load-order evidence, not evidence that the author deliberately selected every value in that record. Rule inference must exclude identical forwards unless another source supports authorship of the relevant value.

## Optional module semantics

FOMOD descriptions and package structure are normalized into roles such as main, standalone_main, integration_addon, feature_addon, compatibility_patch, reversion, and optional_module.

Reversion plugins are boundary evidence. For example, Blade and Blunt's no-sprint module restores fSprintStaminaDrainMult from 0 to 8 and neutralizes sprint-related stamina effects; the no-casting/jump/sneak/swim modules likewise neutralize the corresponding stamina mechanics. No Power Attack Changes rewrites/removes a substantial perk-effect/condition structure rather than merely changing one scalar.

This is why the balancer compares structural deltas, not only numbers.
