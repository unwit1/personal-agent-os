# Skyrim Modding Terminology — Papyrus Language Semantics, States, Properties, Arrays, and Fragments

Imported: 2026-09-24
Status: sourced deep-ingestion pass 25

## Script identity

### ScriptName
Declares the Papyrus class name. Filename and ScriptName should correspond for normal source organization.

### Extends
Inheritance relationship between one Papyrus script class and a parent type such as Quest, ObjectReference, Actor, ReferenceAlias, ActiveMagicEffect or Form.

### Hidden
Script attribute hiding it from normal Creation Kit script attachment lists while remaining usable as code/API.

### Conditional
Script/property attribute allowing selected variables/properties to be read by CK condition system.

### Native
Function implementation supplied by engine/SKSE DLL rather than Papyrus bytecode body.

### Global function
Function callable on script class rather than an instance.

### Instance script
Script attached to a form, alias, quest, magic effect or reference and holding per-instance state.

## Variables and properties

### Variable
Named script-local/member storage.

### Property
Papyrus member exposed for CK fill, Auto generation, conditions or external access depending on modifiers.

### Auto property
Compiler generates hidden backing variable plus Get/Set accessors.

### AutoReadOnly
Compiler-managed constant-like property initialized in source and not externally settable.

### Property getter
Custom function body returning property value.

### Property setter
Custom function body handling assignments.

### Filled property
CK/plugin stores reference/value into script property on attached script instance.

### Unfilled property
Property remains None/default at runtime.

### Property persistence
Property values on a running script instance can be serialized in save; changing plugin/source defaults does not necessarily replace established-save values.

### None
Papyrus null value for object/reference/script types.

### None access
Calling method/property on None, a common runtime error.

### Cast
`as Type` conversion between compatible Papyrus types.

### Failed cast
Cast returns None for incompatible object.

## Primitive/value types

### Bool
Boolean True/False.

### Int
32-bit signed integer-like Papyrus value.

### Float
Floating-point value.

### String
Papyrus string.

### Form
Base object reference to game forms.

### ObjectReference
Placed/runtime reference type.

### Array
Fixed-length collection of one Papyrus element type.

### Struct
Modern SKSE/Papyrus language extension support varies by compiler/runtime; do not assume Fallout 4 language features exist in Skyrim without specific framework/compiler evidence.

## Arrays

### Array length
Fixed size available via `.Length`.

### Array index
Zero-based access.

### New array
`new Type[size]` allocation.

### Array property
Property whose value is array.

### Array persistence
Elements serialized with script instance if held in persistent state.

### Out-of-bounds
Index below zero or >= Length; runtime error.

### Resize pattern
Papyrus arrays are fixed-length, so resizing requires new array and copying unless framework utility provides collection abstraction.

### FormList vs array
FormList is game form collection mutable through engine APIs; Papyrus array is VM value container.

## Functions

### Function
Callable Papyrus routine.

### Event
Engine/framework callback block; syntactically similar to function but invoked by runtime.

### Return type
Declared type returned by function.

### Parameter
Typed input argument.

### Optional parameter
Parameter with default value.

### Local variable
Variable scoped to function/event.

### Latent function
Native/Papyrus function that can suspend stack and resume later.

### Non-latent function
Completes without yielding VM stack.

### Self
Current script instance.

### Parent
Reference to parent-class implementation for inherited functions/events.

### Function override
Child script defines same function/event signature to replace/extend parent behavior.

## States

### State
Named alternate set of event/function implementations inside one script instance.

### Empty state
Default unnamed state.

### GoToState
Switch current script state.

### GetState
Return active state name.

### State-local event implementation
Same event can behave differently depending on current state.

### State gating
Technique preventing repeated interaction by changing to state where event handler is absent/different.

### State persistence
Current script state can be saved with instance.

### State migration hazard
Renaming/removing a state can leave established-save script instance pointing at state name no longer implemented as expected.

## Control flow

### If / ElseIf / Else
Conditional branching.

### While
Loop.

### Return
Exit function/event.

### && / ||
Boolean AND/OR with short-circuit behavior according to Papyrus language semantics.

### !
Boolean negation.

### Comparison
`== != < > <= >=`.

### Arithmetic
Numeric operators with Int/Float conversion rules.

### String concatenation
`+` combines strings/values through conversion rules.

## Events and lifecycle

### OnInit
Called when script instance initializes, not every time reference 3D loads.

### OnLoad
Object reference's 3D loads.

### OnUnload
3D unloads.

### OnReset
Reference/cell reset lifecycle.

### OnPlayerLoadGame
SKSE-added event commonly used for post-load maintenance.

### ActiveMagicEffect lifecycle
OnEffectStart/OnEffectFinish bracket one applied effect instance.

### Alias lifecycle
ReferenceAlias/LocationAlias fill/clear state tied to Quest.

## Script fragments

### Fragment
Small Papyrus code generated/associated with CK editor field such as quest stage, dialogue INFO, package, scene or perk.

### Quest fragment
Code executed when quest stage fragment runs.

### TopicInfo fragment
Dialogue INFO fragment executed at configured point.

### Package fragment
Package start/change/end fragment.

### Scene fragment
Scene lifecycle/action code.

### Perk fragment
Perk-related CK-generated code where supported.

### Fragment script
Compiler-generated script class containing one or more fragment functions.

### Fragment filename
CK-managed generated source/PEX name, often opaque.

### Fragment property
CK can add properties to generated fragment class.

### Fragment ownership
Treat generated fragment source as CK-owned; renaming/restructuring manually can break editor references.

### Fragment bloat
Large logic inside many fragments is hard to maintain; prefer calling named functions on regular scripts.

## Imports

### Import
Makes another script's global functions/types available without repeatedly qualifying class name.

### Namespace collision
Two imported scripts expose same global function names; explicit qualification can disambiguate.

## Compilation

### PSC
Papyrus source.

### PEX
Compiled bytecode.

### Compiler flags file
Defines special annotations/flags.

### Import path
Directories compiler searches for parent/type PSC definitions.

### Native stub
PSC declaration for functions implemented by SKSE/native DLL.

### Compile succeeds/runtime fails
Compiler only verifies declared signatures/types; missing native DLL/function can still fail at runtime.

### Decompiled PEX
Recovered approximate source representation. Not guaranteed identical to original PSC names/comments/control structure.

### Champollion
Community Papyrus decompiler used to inspect PEX when source absent.

## Concurrency model

### Stack
One event/function execution chain.

### Multiple stacks
Same script instance can have multiple event stacks depending on events/latent yields; do not assume all event handling is serialized by object identity.

### Race condition
Two stacks read/modify shared script variables in timing-dependent order.

### Guard variable
Bool/state used to prevent reentrant work.

### Latent reentrancy
Function sets state, waits, and another event runs before first resumes.

### Event queue
VM schedules callbacks; event arrival does not guarantee immediate execution.

## Common errors

### Cannot call member function on a None object
Null reference/property/cast.

### Cannot open store for class
Required PEX/dependency script missing or incompatible.

### Native function not found
PEX declares native function but supplying DLL failed/mismatch.

### Property not found
Saved/plugin property mapping no longer matches current script definition.

### Cannot bind script
Script class/type mismatch or missing parent/dependency.

### Stack dump
VM diagnostic under pressure/error, not by itself proof one particular script caused FPS loss.

## Design rules

1. Prefer regular named scripts for substantial logic; fragments should delegate.
2. Treat property/state changes as save-persistent API/schema when supporting upgrades.
3. Check None after optional lookups/casts.
4. Avoid long latent critical sections without reentrancy guards.
5. Prefer events over frequent polling.
6. Compile against same dependency/API generation expected at runtime.
7. Preserve PSC source and compiler inputs in version control.
8. Test established-save migration whenever class properties/states/lifecycle change.

## Sources

- Creation Kit Wiki Papyrus scripting reference: https://ck.uesp.net/wiki/Category:Scripting
- Creation Kit Wiki Notepad++/compiler setup: https://ck.uesp.net/wiki/Notepad%2B%2B_Setup
- SKSE64 Papyrus source/API: https://github.com/ianpatt/skse64
- Champollion ecosystem for PEX inspection
