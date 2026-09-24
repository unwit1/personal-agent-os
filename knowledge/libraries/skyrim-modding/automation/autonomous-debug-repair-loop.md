# Skyrim Mod Factory — Autonomous Debugging and Repair Loop

Created: 2026-09-24
Status: canonical failure-handling design

## Objective

When a build/test fails, Agent OS should diagnose and repair deterministic failures without repeatedly asking the user to interpret logs.

## Step 1 — Capture evidence before changing anything

Record:
- failing task;
- exact command;
- exit code;
- stdout/stderr;
- tool log;
- modified files;
- input hashes;
- output hashes;
- runtime/profile;
- previous passing commit/build.

Never destroy the original failing evidence.

## Step 2 — Identify the first causal failure

Ignore cascades until the earliest causal error is found.

Examples:
- missing master -> unresolved FormIDs -> Synthesis crash -> DynDOLOD failure;
- missing PSC dependency -> compiler errors in downstream scripts;
- wrong skeleton -> animation/physics errors;
- stale generated patch -> apparent record conflict.

## Step 3 — Classify layer

Categories:
- manifest/config;
- plugin/schema;
- master/FormID;
- Papyrus;
- native build/load;
- runtime API;
- asset/NIF/texture;
- animation/behavior;
- UI;
- world/navmesh;
- quest/dialogue;
- generated output;
- packaging;
- game crash;
- performance;
- unknown.

Route to the relevant knowledge modules and tool-error catalog.

## Step 4 — Reproduce minimally

Create or select:
- minimal plugin set;
- minimal asset set;
- clean generated-output directory;
- dedicated MO2 profile;
- known fixture save/new game.

If issue disappears, bisect dependency/mod interaction rather than changing code blindly.

## Step 5 — Generate hypotheses

Each hypothesis records:
- suspected cause;
- supporting evidence;
- contradicting evidence;
- discriminating test;
- expected result.

Run cheapest/highest-information test first.

## Step 6 — Safe auto-repair classes

Agent may automatically:
- regenerate stale outputs;
- correct deterministic syntax;
- add missing generated files;
- normalize paths;
- rerun compiler/generator;
- replace a generated artifact from source;
- fix manifest/tool-version mismatch;
- forward explicit manifest-owned fields;
- update build scripts;
- change debug logging;
- isolate a failing record/asset.

## Step 7 — Proposal-only repair classes

Require review before:
- changing gameplay intent;
- deleting a form/asset;
- changing FormIDs/compaction;
- changing plugin masters;
- rewriting navmesh;
- altering save-persistent data;
- changing quest progression;
- replacing a third-party mod's behavior;
- changing license;
- changing runtime support promises.

## Step 8 — Rebuild only downstream nodes

Use dependency graph:
source PSC change -> PEX -> package/test
plugin record change -> patchers -> LOD/generation -> test
mesh change -> BodySlide/ParallaxGen/LOD -> package/test

Do not rerun expensive unrelated generators.

## Step 9 — Regression compare

Compare:
- error set;
- warning set;
- plugin diff;
- asset diff;
- log signatures;
- performance;
- test assertions.

A repair that removes one error but introduces a new unexplained diff is not complete.

## Step 10 — Promote prevention rule

After root cause is confirmed:
- add fixture;
- add validator;
- add error signature;
- add regression test;
- update knowledge;
- link source issue/version.

The system should progressively make repeated bug classes impossible.

## Crash workflow

1. collect Crash Logger output;
2. identify runtime/build;
3. resolve involved FormIDs/plugins/classes;
4. correlate native stack with plugin/PDB if available;
5. correlate last framework logs;
6. reproduce on minimal profile;
7. disable one suspected layer at a time;
8. distinguish bad asset/data from native hook;
9. add regression fixture.

Never blame a plugin solely because its name appears near the crash.

## Papyrus workflow

1. compile source cleanly;
2. inspect exact script provider/dependencies;
3. identify stack warning/error;
4. distinguish harmless log noise from broken state;
5. inspect save persistence/instances;
6. test fresh save;
7. test migration;
8. replace polling with event/native strategy if performance is root cause.

## Plugin/data workflow

1. xEdit error check;
2. masters/unresolved forms;
3. compare origin + all overrides;
4. inspect field-level intent;
5. inspect runtime mutators;
6. inspect save ChangeForms;
7. generate minimal patch;
8. retest.

## Asset workflow

1. resolve actual winning file in VFS;
2. confirm path referenced by record/NIF/config;
3. inspect format/version;
4. round-trip/load via library where possible;
5. compare skeleton/material dependencies;
6. visual test.

## Animation workflow

1. generator success;
2. output winner;
3. OAR condition match;
4. behavior event path;
5. skeleton node;
6. framework conflict;
7. first/third person;
8. VR if supported.

## Confidence threshold

Automatic repair is allowed only when:
- failure is deterministic;
- intended semantics are explicit;
- repair is reversible;
- validator can prove postcondition.

Otherwise produce a ranked set of hypotheses and the next discriminating test, not a guess.
