# Skyrim Mod Factory — Automated Test Fixture Catalog

Created: 2026-09-24

A fixture is a minimal reproducible environment used to prove one class of behavior.

## F01 — Empty baseline

Purpose:
- plugin loads;
- masters resolve;
- no feature activation.

Contents:
- official masters;
- SKSE/framework minimum as required;
- target mod.

## F02 — New game

Purpose:
- initialization;
- script registration;
- default settings;
- first-time distribution.

Assertions:
- no errors;
- expected initial records/state;
- no stale migration path.

## F03 — Save/load cycle

Sequence:
1. initialize feature;
2. save;
3. quit;
4. reload;
5. compare state.

Use for:
- Papyrus;
- SKSE serialization;
- external JSON;
- runtime distribution persistence.

## F04 — Upgrade from prior release

Keep fixture saves for each released persistence schema.

Assertions:
- migration executes once;
- old fields map/default correctly;
- no duplicated registrations/distribution.

## F05 — Uninstall/disable

Only run if project promises uninstall behavior.

Never infer clean uninstall from absence of immediate crash.

## F06 — FormID/master integrity

Fixture deliberately removes/renames a dependency.

Expected:
- build validator fails before game launch.

## F07 — ESL boundary

Fixture:
- form count near allowed range;
- references from configs;
- compaction candidate.

Expected:
- compaction requires explicit policy;
- all remapped references update.

## F08 — Conflict-forwarding

Create two small fixture plugins that edit different fields of same record.

Expected generated patch:
- preserves intended field from each;
- does not copy unrelated loser values.

## F09 — Runtime mutator overlap

Two configs target same form through SPID/KID/BOS/SkyPatcher/OAR as applicable.

Expected:
- analyzer reports overlap/order;
- runtime log matches predicted result.

## F10 — NPC dark-face fixture

Intentional mismatch between NPC_ appearance and FaceGen.

Expected:
- appearance validator detects mismatch or requires FaceGen regeneration.

## F11 — Armor slot/partition fixture

Intentional ARMO/ARMA/NIF partition mismatch.

Expected:
- mesh/data validator flags inconsistent slot coverage.

## F12 — Missing texture/NIF path

Expected:
- asset closure fails before game.

## F13 — Broken Papyrus dependency

Remove one PSC declaration/native provider.

Expected:
- compile/dependency gate fails.

## F14 — Registration duplication

Save/load or update scenario where OnInit-based code would register twice.

Expected:
- runtime assertion sees single intended registration.

## F15 — OAR priority collision

Two valid submods match same actor/action.

Expected:
- resolver identifies final selection and warns when project did not declare overlap intent.

## F16 — Pandora failed patch

Include malformed/invalid behavior edit.

Expected:
- generator log parser maps failure to patch/component and blocks promotion.

## F17 — Native missing relocation/API

Simulate unsupported runtime/interface.

Expected:
- plugin fails gracefully or refuses load with actionable log, not CTD.

## F18 — Native serialization migration

Load co-save from older schema.

Expected:
- migration succeeds or cleanly ignores incompatible data according to policy.

## F19 — Quest alias failure

Fixture makes alias fill impossible.

Expected:
- test demonstrates quest does not progress and diagnostics point to alias fill before fragment logic.

## F20 — Dialogue condition matrix

Run positive and negative actor/location/faction/global conditions.

Expected:
- only intended INFO becomes eligible.

## F21 — Navmesh route

Script/manual route through edited navmesh:
- door -> interior;
- narrow passage;
- combat movement;
- follower traversal.

Requires game observation, but path and expected checkpoints are generated automatically.

## F22 — Portal/room visibility

Visit every portal direction and camera angle.

Capture:
- disappearing geometry;
- light pop;
- wrong room membership.

## F23 — Water seam

Cross edited CELL boundaries at controlled time/weather.

Compare:
- flow;
- height;
- material/type;
- distant water.

## F24 — Leveled-list distribution

Run controlled levels and repeated spawns.

Check:
- expected item/actor distribution;
- chance-none behavior;
- no duplicate injections.

## F25 — Performance stress

Configurable:
- actor count;
- inventory size;
- Papyrus event frequency;
- animation count;
- draw load.

Capture baseline vs mod.

## F26 — VR camera/input

For VR-supporting project:
- first person;
- VR camera state;
- left/right controller;
- virtual keyboard;
- HIGGS/VRIK/PLANCK interaction where applicable.

## F27 — Packaging matrix

For every FOMOD option combination in supported matrix:
- simulate selected files;
- assert dependencies;
- assert no missing sources;
- validate final tree.

## F28 — Clean build reproducibility

Build twice from same locked sources.

Expected:
- semantic plugin diff empty;
- generated file set identical;
- hashes identical where tools are deterministic;
- documented non-determinism otherwise.

## Fixture storage model

Store durable fixture definitions in Git.
Store large save files/assets locally or in release/test storage with hashes and metadata.

Every bug fix should attempt to add the smallest fixture that would have caught it before release.
