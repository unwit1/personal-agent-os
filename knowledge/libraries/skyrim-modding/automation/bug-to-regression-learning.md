# Skyrim Mod Factory — Bug-to-Regression Learning

Created: 2026-09-24
Status: regression-record schema + promotion helper implemented

## Goal

A bug should cost the project once.

After a cause is validated, the Mod Factory should preserve enough evidence to prevent the same causal pattern from escaping again.

Implemented:
- existing `schemas/skyrim-runtime-test-v1.schema.json` for transport-neutral runtime test scenarios;
- `schemas/skyrim-bug-regression-v1.schema.json`;
- `tools/skyrim_mod_factory/promote_bug_regression.py`.

## Bug lifecycle

`reported -> reproduced -> root-caused -> fixed -> validated -> closed`

Only **root-caused or later** bugs can be promoted to regression candidates.

A symptom alone is not an analyzer rule.

Bad:
> CTD near Whiterun -> flag every Whiterun mod.

Good:
> a generated reference contains a stale FormKey after compaction -> detect the unresolved/remapped link and fixture that compaction path.

## Evidence required

Preserve:
- exact project/build;
- runtime and load order;
- reproduction;
- first causal error;
- logs/crash;
- relevant semantic diff;
- root cause;
- fix commit/artifact;
- post-fix validation.

## Regression outputs

A validated bug can produce one or more:

### Runtime test
Use `skyrim-runtime-test-v1` to prove player-visible/runtime behavior against a dedicated fixture.

### Static analyzer rule
Use `skyrim-analyzer-rule-v1` to detect malformed state before game launch.

### Mutation test
Deliberately reintroduce the defect and prove the validator catches it.

### Fixture
Minimal plugin/config/save/asset metadata needed to reproduce.

### Documentation rule
Use when the defect is a design constraint rather than mechanically detectable.

## Promotion helper

`promote_bug_regression.py` carries validated facts into a candidate packet. It deliberately does **not** invent a detection algorithm from the symptom.

This keeps correlation and folklore out of the analyzer corpus.

## Runtime test relationship

The existing runtime-test schema already models:
- target project and adapter;
- fixture kind/profile;
- safety;
- ordered actions/steps;
- assertions;
- evidence;
- cleanup;
- regression IDs.

That contract should remain transport-neutral so the same test can be driven by DevBench, SkyLink AI, AutoTest, a future Agent OS native bridge, or supervised manual execution.

## Promotion rule

Canonical prevention knowledge requires:
1. reproduction;
2. causal isolation;
3. fix;
4. independent postcondition validation;
5. smallest reliable fixture/rule.

Every promoted regression should point back to the exact bug evidence that justified it.
