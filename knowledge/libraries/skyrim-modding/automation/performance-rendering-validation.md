# Skyrim Mod Factory — Performance, Rendering, and Visual Regression Stack

Created: 2026-09-24
Status: canonical measurement architecture

## Goal

An AI must not claim a mod is performant because code "looks efficient." Performance is a measured property under a reproducible scene.

## Reproducible scene driver — devbench

Use devbench record/replay and scenario tools to make benchmark runs repeatable.

Record:
- entry save/cell;
- trajectory and view direction;
- time/weather;
- feature state;
- scenario/event boundaries.

Replay the same recipe for baseline and candidate build.

## High-level frame telemetry — PresentMon

PresentMon can capture Windows graphics presentation metrics including CPU/GPU/display frame durations and latency.

Capture at minimum:
- frame time distribution;
- CPU frame time;
- GPU frame time when available;
- present latency;
- dropped/outlier frames;
- capture interval/sample count.

Store:
- hardware;
- driver;
- resolution;
- display refresh/VRR;
- renderer stack;
- runtime;
- modlist/profile;
- benchmark recipe hash.

### Comparison

Do not compare one average FPS number.

Prefer:
- median;
- 1%/0.1%-style low/frame-time percentiles where statistically appropriate;
- p95/p99 frame time;
- stutter count above a project threshold;
- scenario-segment deltas.

## Native code profiling — Tracy

For Agent OS-authored CommonLib/SKSE plugins:
- compile a profiling build;
- add scoped zones to hot hooks/tasks;
- expose feature toggles through devbench;
- replay the same scenario;
- align devbench EventBus boundaries with Tracy capture.

Measure:
- call count;
- total time;
- self time;
- allocation hotspots;
- worker/main/render thread contention.

Community Shaders already demonstrates Tracy-enabled development patterns.

## Graphics debugging — RenderDoc

Use when the feature touches:
- Community Shaders/HLSL;
- materials;
- PBR/parallax;
- render targets;
- first-person pass;
- water;
- reflections;
- UI rendering.

Agent workflow:
1. reproduce using a known camera/weather/time;
2. capture one frame;
3. inspect problematic draw call;
4. inspect shader/resource bindings;
5. compare baseline/candidate;
6. save capture metadata/evidence.

Community Shaders documents launching Skyrim through MO2 under RenderDoc and child-process capture.

## Shader regression

For authored HLSL:
- compile all relevant permutations;
- treat warnings as configured;
- compare bytecode when a refactor claims no semantic change;
- run visual/render-target tests when behavior changes.

Community Shaders currently ships a `verify-shader-refactor` workflow that compares compiled DXBC across a git base/worktree and uses hlslkit for shader validation; this is a useful reference design.

## Papyrus performance

Measure separately from native/render:
- VM update health;
- stack count/growth;
- event rate;
- update frequency;
- number of actors/forms iterated;
- log storm rate.

Use profiling only when needed; always-on verbose logs can alter workload.

## Asset performance

Automated asset checks:
- texture dimensions/compression/mipmaps;
- NIF triangle count;
- skin/bone influence count;
- collision complexity;
- particle emitter rates;
- shader/material features;
- LOD availability.

Do not impose universal triangle/texture thresholds. Compare against intended screen size, reuse count, platform and scene density.

## Visual regression

### Deterministic screenshots
Use:
- DevBench or AutoTest fixed scenes;
- fixed FOV/camera;
- fixed weather/time;
- fixed display/render settings.

Compare:
- NPC head/neck seams;
- missing/purple textures;
- mesh position;
- UI;
- lighting;
- LOD transitions;
- water seams.

### Vision model
A vision model may flag candidate differences, but should not be sole proof.

Store:
- baseline screenshot;
- candidate screenshot;
- pixel/perceptual diff;
- AI description;
- deterministic scene metadata.

## VR performance

VR requires its own benchmark:
- headset/runtime;
- render resolution;
- reprojection state;
- target refresh;
- CPU/GPU frame timing.

A flat-screen PresentMon result cannot establish VR comfort/performance.

## Performance gates

A project manifest can define budgets such as:
- no new p99 frame-time regression > X ms in fixture;
- no main-thread hook > X microseconds p95;
- no persistent Papyrus stack growth;
- no unbounded memory/handle growth;
- load/save delta below project threshold.

The threshold must come from project goals and baseline evidence, not a universal folklore number.

## Automatic diagnosis hints

### CPU regression
Check:
- Papyrus loops;
- actor scans;
- native main-thread hooks;
- behavior/AI actor density.

### GPU regression
Check:
- shader feature/pass;
- texture resolution;
- shadow/light count;
- mesh draw/triangle count;
- particles;
- PBR/parallax;
- transparency/overdraw.

### Stutter
Check:
- shader compilation;
- asset streaming;
- animation loading;
- Papyrus/event bursts;
- synchronous file/network work;
- cell load.

### Freeze
Use devbench off-thread health plus thread/crash evidence; a frozen frame counter can also mean pause/loading, so correlate lifecycle/task state.

## Evidence requirement

Every performance claim in release notes should be traceable to:
- benchmark recipe;
- baseline build;
- candidate build;
- sample data;
- hardware/context;
- analysis script/version.

