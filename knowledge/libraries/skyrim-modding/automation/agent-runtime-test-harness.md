# Skyrim Mod Factory — AI-Driven Runtime Test Harness

Created: 2026-09-24
Status: canonical testing architecture

## Purpose

Turn Skyrim runtime testing from:
edit -> launch -> user manually reproduces -> user describes result -> guess

into:
edit -> build -> launch fixture -> agent drives/observes scenario -> assert -> repair -> rerun

## Runtime adapter candidates

Agent OS should abstract over:
- SkyLink AI;
- DevBench;
- SkyrimNet MCP for SkyrimNet-dependent projects;
- console/Papyrus bridges;
- future native Agent OS test plugin.

## Test profile

Every automated project should support a dedicated MO2 profile with:
- known executable runtime;
- only required dependencies;
- debug versions/logging;
- test plugin;
- fixture save(s);
- generated output mods;
- runtime MCP/test plugin;
- deterministic INIs.

Never use the user's primary long-play save for autonomous destructive testing.

## Test fixture types

### New-game fixture
Used for:
- initialization;
- quest start;
- distributions;
- MCM/default settings;
- save schema first-write.

### Controlled location fixture
Player positioned in a deterministic interior/exterior with known actors/objects.

### Combat fixture
Known actor set, equipment and hostility.

### Quest fixture
Known stage/aliases and explicitly constructed preconditions.

### Established-save migration fixture
Save produced by the previous released mod version.

### Stress fixture
Many actors/items/effects/events for performance/limit testing.

## Runtime assertion protocol

Every test has:

- id;
- setup commands/actions;
- preconditions;
- trigger;
- observations;
- assertions;
- cleanup;
- timeout;
- allowed nondeterminism;
- evidence artifacts.

Example:

```yaml
id: enchanted-fragment-drop
setup:
  - spawn_fixture_actor: TestBandit
  - equip: TestIronSword
trigger:
  - kill: TestBandit
assert:
  - corpse_inventory_contains:
      editor_id: DEMO_BrokenFragment
      count: ">=1"
  - papyrus_errors_owned_by_mod: 0
cleanup:
  - delete_fixture_actors: true
```

## Read -> act -> read

Never assume a runtime action succeeded because the MCP call returned without transport error.

For every state mutation:
1. read baseline;
2. execute;
3. wait for actual game event/state transition;
4. re-read;
5. compare.

## Event waits

Prefer:
- quest-stage event;
- inventory event;
- death event;
- location change;
- menu event;
- spell/effect event;
- ModEvent;
- condition polling with bounded timeout.

Avoid blind sleeps where a state predicate can be observed.

## Game safety state

Before consequential runtime actions, query:
- loaded save/new-game state;
- loading screen;
- menu/pause state;
- killmove/death transition;
- save in progress;
- fast-travel transition;
- cell attach/load state.

Abort/retry rather than executing during unsafe transition.

## Screenshot/vision assertions

Use screenshot/render evidence for:
- mesh visibility;
- material/shader;
- UI;
- object placement;
- clipping;
- animation pose;
- map marker;
- lighting.

Vision assertions are **advisory** unless paired with deterministic state when possible.

Store:
- screenshot;
- camera/player transform;
- weather/time;
- render framework;
- expected reference image or explicit criteria.

## Log assertions

After every scenario collect deltas for:
- SKSE/plugin logs;
- Papyrus log;
- Crash Logger;
- OAR/Pandora;
- SPID/KID/BOS/SkyPatcher;
- Agent OS test adapter.

A test can fail because behavior passed but introduced a new owned ERROR/FATAL.

## Performance assertions

Measure representative:
- frame time;
- script VM health;
- event/update rate;
- native hook time if instrumented;
- actor scan size;
- memory/handle growth;
- load/save duration.

Compare to baseline fixture.

## Automatic repair integration

On failure:
1. freeze evidence;
2. classify data/script/native/asset/runtime layer;
3. query static plane;
4. query runtime plane;
5. generate discriminating test;
6. apply only reversible deterministic fix;
7. rebuild affected nodes;
8. rerun failed test and nearby regressions.

## Test generation from implementation manifest

Agent OS should automatically generate tests for every declared feature.

Examples:

### Distribution
- positive recipient;
- negative recipient;
- duplicate prevention;
- save/load persistence.

### Quest
- valid start;
- invalid conditions;
- each stage transition;
- alias resolution;
- save/load mid-quest.

### Magic
- apply;
- expire;
- resist/immune;
- magnitude/duration;
- stacking.

### UI
- open/close;
- controller;
- keyboard;
- text entry;
- resolution/UI scale.

### Native
- startup;
- new game;
- load;
- revert;
- save;
- dependency absent;
- API version mismatch.

### Asset
- present;
- missing dependency produces expected validation failure;
- first/third person;
- male/female/race variants.

## Future dedicated Agent OS test plugin

Long term, build a small native `AgentOSTestBridge.dll` exposing a strictly test-oriented MCP/local interface:
- query Form/Actor/Quest values;
- wait for engine events;
- call allowlisted Papyrus functions;
- teleport to test cells;
- spawn tagged disposable fixtures;
- take screenshots;
- expose VM/frame/load health;
- mark scenario start/end;
- revert to fixture save;
- capture structured assertions.

Keep it **development-profile only** and separate from release artifacts.
