# Skyrim Modding Terminology — Open Animation Replacer Configuration and Conditions

Imported: 2026-09-24
Status: sourced deep-ingestion pass 10

## OAR structure

### Open Animation Replacer / OAR
SKSE framework replacing animation clips according to configurable conditions, priorities, variants and runtime state.

### Replacer mod
Top-level OAR package grouping related submods.

### Submod
Condition/priority/configuration unit containing one or more replacement animations.

### Legacy DAR submod
DAR-style folder interpreted by OAR's backwards-compatibility layer.

### config.json
Author-owned OAR configuration defining metadata, conditions, priority and behavior.

### user.json
User-owned override configuration that can replace selected config values without editing distributed author config.

### Inspect mode
In-game OAR UI mode showing live configuration/condition evaluation without saving edits.

### User mode
In-game UI mode saving user changes into user.json.

### Author mode
In-game UI mode writing author configuration to config.json.

### Animation log
Runtime UI/log showing which animation clips were selected/played and their source replacers.

### Animation event log
Runtime UI/log displaying animation events from behavior/game/plugin sources.

### Preloading
OAR loading replacement animations ahead of actual gameplay use, including main-menu preloading where supported.

### Project animation limit
Per-behavior-project animation capacity expanded by OAR relative to vanilla constraints.

## Priority and matching

### Priority
Numeric ordering used when multiple eligible submods replace the same animation. Higher applicable priority wins.

### Priority collision
Multiple matching submods use same priority. OAR editor warns because outcome/intent becomes ambiguous.

### Original animation
Vanilla/current animation path that a replacement targets.

### Replacement animation
HKX clip chosen by OAR instead of the original.

### Path match
Replacement corresponds to original animation path/project.

### Replacer scope
State/condition/variant scope shared by all submods inside one replacer mod where supported.

### Submod scope
State shared only within one submod.

### Clip scope
State associated with one animation clip/replacement lifecycle.

### Evaluation target
Actor/reference against which OAR conditions are evaluated.

### Condition success
All required top-level conditions evaluate true, subject to logical wrappers/negation.

### Negated condition
Condition result inverted.

### Required project name
Submod restriction to one behavior project such as DefaultMale/DefaultFemale or another graph.

### Shared animation folder
Configuration allowing multiple submods to reference one common animation directory rather than duplicate files.

## Replacement timing

### Interruptible
Submod setting causing required conditions to be continuously reevaluated while animation plays so replacement can switch immediately.

### Replace on loop
Reevaluate replacement when a looping clip repeats.

### Replace on echo
Reevaluate on animation echo/transition mechanism.

### Custom blend time
Override controlling blend duration between outgoing and replacement animation.

### No Triggers flag
Animation clip flag that normally suppresses annotations/triggers; OAR can optionally ignore it.

### Annotation replacement
Choosing whether replacement animation's own annotations/events are used.

### Playback speed multiplier
Runtime modifier supported by current OAR API/functionality for animation playback speed.

## Variants

### Variant
One of several animations associated with one logical replacement.

### Random variant
Variant selected probabilistically.

### Variant weight
Relative probability weight.

### Sequential variant
Variant mode playing alternatives in order rather than randomly.

### Play once
Sequential-variant flag preventing that variant from repeating after sequence wraps for the current state lifecycle.

### Play First
Random-variant behavior ensuring selected intro/initial variant plays before ordinary random pool.

### Variant state
Persisted runtime data such as next sequential index or random result.

### State data scope
Scope controlling which animations/submods/replacer share random/sequence state.

### Keep result on loop
State behavior preserving random selection across loop/echo rather than rerolling constantly.

## Condition presets

### Preset
Named reusable condition block defined at replacer-mod level.

### PRESET condition
Condition referencing a reusable preset by name.

### Condition duplication
Repeated identical condition trees across submods; presets reduce this.

### Preset indirection
Submod stores preset name while actual condition definitions live in replacer config.

## Condition families

### Identity condition
Checks actor/reference/base form identity.

### Equipment condition
Checks equipped items/weapon types/slots.

### Keyword condition
Checks actor/base/equipment/location keyword state.

### Faction condition
Checks membership/rank.

### Perk condition
Checks actor perks.

### Spell condition
Checks spells/abilities.

### Magic effect condition
Checks currently active magic effects.

### ActorValue condition
Compares actor-value state.

### Graph-variable condition
Reads behavior graph bool/int/float values.

### Quest condition
Reads quest stage/running/completed state.

### Location condition
Checks cell/location hierarchy and keywords.

### Combat condition
Checks combat state, target presence, target distance/angle or related combat state.

### Movement condition
Checks direction, speed/sprinting/sneaking/surface angle and related motion state.

### Package condition
Checks current AI package.

### Scene condition
Checks actor participation in scene.

### Furniture condition
Checks current furniture use.

### Idle condition
Checks idle animation/state.

### Time/weather condition
Checks game time/weather where condition implementation supports it.

### Random condition
Stateful/probabilistic condition.

### Replacer-enabled condition
Tests whether another OAR replacer/submod is active.

### Animation timing condition
Checks elapsed/remaining/progress state of current animation where supported.

### Complex custom condition
Condition registered by another SKSE plugin through OAR API.

## OAR plugin API

### Condition API
Versioned native API allowing SKSE plugins to add custom OAR conditions.

### UI API
Native interface allowing integrations to open/close/toggle/query OAR UI and suppress UI hotkey where current API supports it.

### Essential condition
Custom-condition metadata indicating plugin/version requirement is essential to evaluate a submod correctly.

### Non-essential condition
Custom condition whose absence may be tolerated/ignored according to OAR semantics.

### Condition plugin dependency
Replacer requires a separate OAR condition plugin.

### Math Plugin
Example OAR API extension evaluating math expressions from configurable numeric inputs.

### Detection Plugin
OAR extension adding conditions based on actor detection relationships/distance/angle.

## Functions

### OAR function
Action executed from OAR animation/function configuration rather than condition-only selection.

### PlaySound
Play sound at evaluated reference.

### ModActorValue
Modify actor value.

### SetGraphVariable
Set behavior graph variable.

### ModifyGraphVariable
Adjust behavior graph variable.

### SendAnimEvent
Send behavior event.

### CastSpell
Cast spell through configured action.

### DispelSpell
Remove configured spell/effect.

### SpawnParticle
Spawn configured particle/effect.

### UnequipSlot
Unequip item from slot.

### CONDITION function
Execute child functions only when embedded conditions pass.

### RANDOM function
Choose among child functions randomly.

### ONE function
Attempt child functions in order until one succeeds.

### FILENAME function
Run child functions only for a specific replacement animation filename.

## Diagnostic rules

1. Use OAR animation log before guessing which mod supplied a clip.
2. Priority decides between simultaneous valid replacements; asset overwrite priority still matters for files with identical actual paths outside OAR organization.
3. A user.json can make installed behavior differ from author's config.json.
4. Dynamic conditions can change during animation; check Interruptible/loop/echo reevaluation settings.
5. Random/sequential variants have state scopes; do not diagnose repeat behavior without checking scope/reset lifecycle.
6. Custom-condition plugins have their own runtime/API versions.
7. OAR replacement cannot create behavior graph states/events that don't exist; use behavior patch/injection when graph logic is missing.
8. KID-generated runtime keywords require current-compatible OAR versions to be recognized reliably; version matters.

## Sources

- Open Animation Replacer upstream: https://github.com/ersh1/OpenAnimationReplacer
- OAR Nexus/current detailed documentation: https://www.nexusmods.com/skyrimspecialedition/mods/92109
- OAR example custom condition plugin: https://github.com/ersh1/OpenAnimationReplacer-ExamplePlugin
- OAR Math Plugin: https://www.nexusmods.com/skyrimspecialedition/mods/92607
- OAR Detection Plugin: https://www.nexusmods.com/skyrimspecialedition/mods/104806

## Dated snapshot

OAR v3.2.1 was observed as current on 2026-09-24, updated 2026-08-31, with support for Skyrim runtime 1.7.99+ and current UI API additions. Preserve this as dated compatibility metadata.


## Exact source-derived companion catalogs

For OAR 3.2.1, prefer these when exact version/API semantics matter:

- `oar-3.2.1-condition-catalog.md` — all 123 built-in condition names with minimum OAR version and source descriptions.
- `oar-state-priority-variants.md` — source defaults, config provenance, priority, state scopes, variants, loop/echo and synchronized evaluation.
- `../sources/oar-3.2.1-source-manifest.md` — pinned source files/SHAs.

This broad terminology file remains the conceptual overview; the source-derived companions are authoritative for 3.2.1-specific finite tables.
