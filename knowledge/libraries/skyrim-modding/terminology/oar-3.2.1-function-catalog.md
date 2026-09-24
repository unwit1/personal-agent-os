# Open Animation Replacer 3.2.1 — Built-in Function Catalog

Imported: 2026-09-24
Pinned source commit: `f4e7688b065175aff70aa523073857911e15aca3`
Source: `src/Functions.h` blob `c0b9e519df9e1e5a9c1192c32d5519d8bd5fd01c`
Function API source: `src/API/OpenAnimationReplacer-FunctionTypes.h` blob `33320efcbbaa87a59597d5c094951d8f6283099f`
Valid built-in functions: **14**
Status: finite source-derived catalog

## Catalog

| Function | C++ class | Minimum OAR | Description | Source line |
|---|---|---:|---|---:|
| `CONDITION` | `CONDITIONFunction` | 3.0.0 | Run a set of functions only if the specified conditions evaluate to true. | 62 |
| `RANDOM` | `RANDOMFunction` | 3.0.0 | Runs one random function from the contained function set. | 110 |
| `ONE` | `ONEFunction` | 3.0.0 | Attempts to run functions from the contained function set in top-down order, until the first one succeeds. Mostly intended to be used with CONDITION functions inside, or other functions that contain an internal check before running. | 130 |
| `PlaySound` | `PlaySoundFunction` | 3.0.0 | Plays a sound at the ref's location. | 150 |
| `ModActorValue` | `ModActorValueFunction` | 3.0.0 | Modifies an actor value by a given value. | 170 |
| `SetGraphVariable` | `SetGraphVariableFunction` | 3.0.0 | Sets a graph variable. | 193 |
| `SendAnimEvent` | `SendAnimEventFunction` | 3.0.0 | Sends a behavior graph event. | 216 |
| `CastSpell` | `CastSpellFunction` | 3.0.0 | Casts a spell. | 237 |
| `DispelSpell` | `DispelSpellFunction` | 3.0.0 | Dispels a spell. | 263 |
| `SpawnParticle` | `SpawnParticleFunction` | 3.0.0 | Spawns a particle. | 283 |
| `UnequipSlot` | `UnequipSlotFunction` | 3.0.0 | Unequips an item from the specified slot. | 317 |
| `ModifyGraphVariable` | `ModifyGraphVariableFunction` | 3.1.0 | Modifies a graph variable. | 340 |
| `FILENAME` | `FILENAMEFunction` | 3.1.0 | Runs functions from the contained function set only if the current replacement animation matches the specified filename. | 363 |
| `SetPlaybackSpeedMultiplier` | `SetPlaybackSpeedMultiplierFunction` | 3.2.0 | Sets the playback speed multiplier of the current animation clip. | 385 |

## Sentinel

- `! INVALID !` — `InvalidFunction`, version 0.0.0: The function was not found!

## Function families

### Control-flow functions
- `CONDITION` — runs child functions only if nested conditions pass.
- `RANDOM` — runs one random function from a child set.
- `ONE` — attempts children top-down until one succeeds.
- `FILENAME` — gates child functions on the active replacement filename.

### Game/runtime effects
- `PlaySound`
- `ModActorValue`
- `SetGraphVariable`
- `ModifyGraphVariable`
- `SendAnimEvent`
- `CastSpell`
- `DispelSpell`
- `SpawnParticle`
- `UnequipSlot`
- `SetPlaybackSpeedMultiplier`

## Version boundaries

- Most function support begins at **3.0.0**.
- `ModifyGraphVariable` and `FILENAME` require **3.1.0**.
- `SetPlaybackSpeedMultiplier` requires **3.2.0**.

A replacer using a newer function on an older OAR install is an API-version compatibility problem, not an animation-file conflict.

## Function API types

Current public function API distinguishes:
- normal built-in functions;
- custom functions registered by another SKSE plugin.

Function components include:
- multi/function-set;
- form;
- numeric;
- NiPoint3/vector;
- keyword;
- text;
- bool;
- nested condition set;
- custom component.

## Execution timing

Functions can be attached to OAR animation/replacement lifecycle triggers. SubMod settings separately control whether function sets rerun on loop and echo.

Do not conflate:
- choosing a replacement;
- reevaluating conditions;
- resetting variant/condition state;
- running OAR functions.

They are separate stages/toggles.

## Diagnostics

1. Verify OAR minimum version for each configured function.
2. A valid replacement can play even if an optional function fails; diagnose the function provider/action separately.
3. `CONDITION` nests OAR conditions inside the action layer and can fail even when the SubMod's top-level conditions passed.
4. `FILENAME` operates on the current replacement filename, not the vanilla original path.
5. Graph-variable and animation-event functions require the underlying behavior graph to expose/use the relevant variable/event.
6. Playback-speed changes affect the active clip; they do not create new behavior states.
7. Custom functions require their own provider plugin/API compatibility.

## Related

- `oar-3.2.1-condition-catalog.md`
- `oar-state-priority-variants.md`
- `oar-config-condition-system.md`
- `../sources/oar-3.2.1-source-manifest.md`
