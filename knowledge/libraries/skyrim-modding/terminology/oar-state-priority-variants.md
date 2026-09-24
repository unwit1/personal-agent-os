# Open Animation Replacer 3.2.1 — Priority, State, Variants, and Config Semantics

Imported: 2026-09-24
Pinned source commit: `f4e7688b065175aff70aa523073857911e15aca3`
Status: source-backed replacement-selection model

## Hierarchy

### ReplacerMod
Top-level provider container holding:
- metadata;
- SubMods;
- condition presets;
- replacer-level state containers.

### SubMod
The actual condition + priority unit. Each SubMod owns:
- name;
- priority;
- disabled state;
- conditions;
- optional synchronized conditions;
- replacement animation files;
- interrupt/loop/echo settings;
- function sets;
- submod-scoped condition/variant state.

### ReplacementAnimation
One replacement target for an original animation path/project. Its effective priority is returned from its parent SubMod.

## Priority

`ReplacementAnimation::GetPriority()` returns the parent SubMod priority.

OAR sorts replacement animations by priority per original animation.

Therefore:
- priority belongs semantically to the SubMod;
- multiple animations inside one SubMod share that SubMod priority;
- a replacement can only compete after its SubMod/animation is enabled and its conditions pass.

## Condition evaluation

For an ordinary replacement:
- disabled replacement/submod fails before condition selection;
- no conditions means the replacement can pass that stage;
- otherwise the condition set uses `EvaluateAll`.

For synchronized animation evaluation:
- source-reference conditions are evaluated;
- optional synchronized/target conditions are separately evaluated against the target;
- both sides must pass.

## SubMod source defaults

Current source initializes:

| Setting | Default |
|---|---|
| Priority | 0 |
| Disabled | false |
| Interruptible | false |
| Replace on loop | true |
| Replace on echo | false |
| Run functions on loop | true |
| Run functions on echo | true |
| Custom blend on interrupt | false |
| Custom blend on loop | false |
| Custom blend on echo | false |

These are source defaults; explicit config/user values can override them.

## Config sources

OAR distinguishes config provenance rather than flattening it:
- author config;
- user config;
- legacy config;
- legacy ActorBase-derived config.

A SubMod can report whether it is user-configured or legacy-derived.

This is why troubleshooting should inspect **config source**, not only the visible final priority.

## JSON submod fields observed in current parser

Required/current fields include:
- `name`;
- `priority`.

Optional/current fields include:
- `description`;
- `disabled`;
- replacement animation data;
- conditions;
- synchronized conditions;
- `interruptible`;
- custom interrupt blend configuration;
- `replaceOnLoop`;
- custom loop blend configuration;
- `replaceOnEcho`;
- custom echo blend configuration;
- function execution on loop/echo.

The parser also reads older/deprecated compatibility fields such as:
- `disabledAnimations`;
- `keepRandomResultsOnLoop`;
- `shareRandomResults`.

Do not generate new configs around deprecated keys merely because current OAR still reads them.

## user.json

Current parsing explicitly recognizes `user.json` inside submod paths.

User config is a separate source from author config and can therefore make installed behavior differ from the mod author's distributed `config.json`.

When diagnosing a priority/condition mismatch:
1. inspect author config;
2. inspect user.json;
3. inspect live OAR UI/log state.

## Legacy DAR compatibility

Current parser still supports:
- `_conditions.txt`;
- numeric priority directory names;
- legacy `_CustomConditions`;
- legacy ActorBase/FormID directory patterns.

Legacy data is normalized into SubMod parse results with explicit legacy source classification.

A functioning legacy DAR folder is therefore not proof that it is using modern author JSON semantics.

## StateDataScope

Current condition API defines:

| Scope | Source value | Semantics |
|---|---|---|
| None | 0 | no state scope |
| Local | `1 << 0` | unique to reference + condition/variant instance + relevant clip |
| SubMod | `1 << 1` | unique to reference, shared inside one SubMod |
| ReplacerMod | `1 << 2` | unique to reference, shared across SubMods in one ReplacerMod |
| Reference | `1 << 3` | unique to reference, shared across matching condition instances |

State identity always includes the evaluated reference according to the source tooltips.

## Variants

Current source defines:

### Random
`VariantMode::kRandom = 0`

### Sequential
`VariantMode::kSequential = 1`

Variant-level fields include:
- disabled;
- weight;
- order/index;
- playOnce.

Replacement-level variant settings include:
- variant mode;
- variant state scope;
- blend between variants;
- reset random on loop/echo;
- share played history.

## Variant defaults

| Setting | Default |
|---|---|
| Mode | Random |
| State scope | Local |
| Blend between variants | true |
| Reset random on loop/echo | true |
| Share played history | false |

## Random vs sequential state

### Random
A state object can cache a random float/result according to scope. Reset-on-loop/echo decides whether the random selection is retained or rerolled.

### Sequential
State tracks the next sequential variant plus played history. Source comments show expiration can reset the next sequential index while retaining played history.

### playOnce
A variant marked play-once participates in the sequence/history rules rather than behaving like an unconstrained ordinary variant.

### sharePlayedHistory
Allows relevant variant state to share played-history information rather than tracking each state independently.

## Loop and echo

Loop/echo can affect three separate things:
1. replacement reevaluation;
2. condition/variant state reset;
3. configured OAR functions running again.

These are separate toggles/behaviors. “Replace on loop” does not automatically mean “reroll every stateful condition.”

## Interruptible

Interruptible enables mid-play reevaluation behavior for eligible replacements and can use a separate custom blend time.

It should not be described simply as “higher priority can interrupt”: priority selects among eligible replacements; interruptibility controls whether a playing clip is reevaluated/switchable during playback.

## Disabled layers

A replacement can be unavailable because:
- its own replacement-animation data is disabled;
- its parent SubMod is disabled;
- a variant is disabled;
- conditions fail;
- custom dependency/condition is invalid;
- target project/path does not match.

## Diagnostic sequence

When an animation is not the expected winner:

1. identify original animation/project;
2. list candidate ReplacementAnimations;
3. check replacement disabled state;
4. check SubMod disabled state;
5. identify author vs user vs legacy config source;
6. compare priorities;
7. inspect every condition result;
8. inspect TARGET/PLAYER/MOUNT/synchronized target context;
9. inspect variant mode, disabled variants and state scope;
10. inspect loop/echo reset and replace settings;
11. check whether user.json changed priority/disabled/variant state;
12. use OAR trace/animation log before changing file overwrite order.

## Important distinction from mod-manager priority

OAR SubMod priority is runtime replacement priority.

MO2/Vortex asset overwrite priority decides which physical file wins when two mods deploy the same path.

They are different systems and can both matter in one animation stack.
