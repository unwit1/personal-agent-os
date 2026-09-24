# Skyrim Modding Terminology — Papyrus, Quests, Dialogue, AI, and Magic

Imported: 2026-09-24
Status: sourced deep-ingestion pass 2

This reference expands the technical wiki around Papyrus runtime behavior and Creation Kit systems that commonly interact with scripts.

## Papyrus language/runtime

### Papyrus
Skyrim's event-driven scripting language and runtime. Scripts are compiled from source and attached/bound to game forms or aliases.

### PSC
Papyrus source file. Human-editable script source.

### PEX
Compiled Papyrus bytecode executed by the game's Papyrus virtual machine.

### ScriptName
The declaration that names a Papyrus script and normally identifies its parent type with `extends`.

### Extends
Papyrus inheritance declaration. A script inherits members and behavior exposed by its parent script type.

### Native function
A Papyrus function implemented by the game engine or an extension such as SKSE rather than in Papyrus source code.

### Global function
A Papyrus function that can be called on the script type itself instead of requiring a script-instance object.

### Event
An engine/runtime callback entry point such as `OnInit`, `OnUpdate`, `OnActivate`, `OnItemAdded`, or `OnPlayerLoadGame`.

### Function
A callable Papyrus routine. Functions may accept arguments and optionally return a value.

### Property
A script field intended to be configured or accessed in a structured way. Properties often bind Papyrus logic to forms selected in the Creation Kit.

### Auto property
A property whose storage and simple getter/setter behavior are generated automatically by the compiler.

### AutoReadOnly property
A property initialized in source that exposes a read-only value after initialization.

### Script instance
A runtime instance of a compiled script bound to a specific form, alias, active magic effect, or other supported host. The same script class can have many instances.

### Attached script
A script associated with a game form or alias through record data. The script class and its per-instance property data are distinct.

### Script property binding
The association between a Papyrus property and a specific game form/value in plugin data. Missing or wrong bindings commonly produce `None` access errors or incorrect behavior.

### VMAD
xEdit/plugin terminology for the virtual-machine-adapter data attached to records. VMAD data stores Papyrus script attachments, properties, and fragment-related information in plugin records.

### Papyrus VM
The virtual machine that schedules and executes Papyrus script stacks independently from ordinary native game code.

### Stack
A currently executing or suspended chain of Papyrus function/event calls.

### Stack dump
Diagnostic output describing Papyrus stacks when the VM reports errors, overload, or other debugging state. A stack dump is not equivalent to a native crash stack.

### Papyrus budget
The amount of frame/update time the game allows Papyrus work under configured runtime settings. Increasing budgets is not a universal fix for poorly designed scripts.

### Latent function
A Papyrus call that can suspend the current stack while waiting for an engine operation or time delay to finish. Latent calls are important when reasoning about concurrency and state changes.

### Utility.Wait
A common latent Papyrus wait operation. It suspends the current stack rather than performing a CPU-blocking busy wait.

### OnInit
An initialization event sent when an eligible script instance is initialized. It is not a universal “run once forever” guarantee across every lifecycle scenario.

### OnPlayerLoadGame
An event available on appropriate player-alias/reference contexts after loading a save. It is commonly used for mod maintenance/update logic.

### OnUpdate
Event generated after registration through update APIs.

### RegisterForUpdate
Registers a script for repeating update events at an interval.

### RegisterForSingleUpdate
Registers one future update event. Scripts commonly register another single update from `OnUpdate` when they want controlled recurring polling.

### UnregisterForUpdate
Stops repeating/single update registration associated with the script.

### Polling
Repeatedly checking state on a timed update rather than reacting to a direct event. Polling can be appropriate but should be minimized when reliable event-driven alternatives exist.

### ModEvent
An SKSE-supported event/message mechanism allowing Papyrus scripts to communicate across otherwise unrelated systems without hard-form dependencies.

### State
A Papyrus language feature allowing a script to provide different event/function implementations depending on its current state.

### GoToState
Changes the active Papyrus state for a script instance.

### None
Papyrus null/no-object value. Calling a member on a `None` reference commonly produces runtime log errors.

### Cast
Papyrus type conversion using `as` or implicit/explicit conversions where supported.

### Array
An indexed collection of values of one Papyrus type.

### FormList vs Papyrus array
A FormList is a persistent game form stored in plugin/runtime game data; a Papyrus array is script-instance data. They solve different persistence/reference problems.

### Debug.Trace
Writes diagnostic text to the Papyrus log when tracing/logging is enabled.

### Debug.Notification
Displays a user-facing notification in game. It is not a substitute for structured logging in production logic.

### Papyrus log
Script/save-engine diagnostic log. It records many warnings/errors/events but is explicitly not a native crash log.

### Save-baked script state
Community shorthand for script instance/property/state data already serialized into a save. Changing plugin/script files does not imply that every existing save-side instance resets to new defaults.

### Script update/migration
Logic that detects an older mod/script state and migrates it when a save is loaded. Versioned maintenance functions are a common pattern.

## Quest systems

### Quest / QUST
A flexible game system for stages, objectives, aliases, scripts, dialogue, scenes, and persistent logic. Quests are often used as invisible manager systems even when the player never sees a journal entry.

### Start Game Enabled
Quest configuration that causes the quest to start automatically as the game initializes its quest systems.

### Quest stage
Numbered quest-state marker. Setting a stage can trigger stage fragments and can be tested by conditions/scripts.

### Quest objective
Player-facing journal objective associated with quest progression.

### Quest fragment
Creation Kit-generated Papyrus code bound to a quest stage or other quest fragment context.

### Alias
A quest-managed slot that resolves to a reference, location, or collection and lets the quest treat the resolved object as a role.

### ReferenceAlias
An alias resolving to an object reference/actor. Alias scripts can receive events in the context of the aliased reference.

### LocationAlias
An alias that resolves to a Location form.

### RefCollectionAlias
An alias capable of managing a collection of references rather than a single reference.

### Forced reference alias
Alias fill mode that points to a specific predefined reference.

### Unique actor alias
Alias fill mode that selects a specified unique actor.

### Find Matching Reference
Alias fill mode that searches for a reference matching defined conditions/rules.

### Alias conditions
Conditions used when evaluating whether a candidate can fill an alias.

### Optional alias
An alias whose failure to fill does not necessarily prevent the quest from starting/running.

### Essential alias
Quest/alias behavior that can affect whether an actor is treated as essential while occupying the alias.

### Alias package
AI package applied through a quest alias, allowing quest-specific behavior without permanently editing the actor base's ordinary package stack.

### Alias spell
Spell applied to an actor while it occupies the alias.

### Alias script
Papyrus script attached to an alias rather than directly to the underlying base form/reference.

## Dialogue and scenes

### Dialogue
Conversation content built through quests/topics/topic infos, conditions, voice types, scenes, and related structures.

### Topic / DIAL
A dialogue topic grouping one or more possible responses/topic-info records.

### TopicInfo / INFO
An individual dialogue response/entry under a topic, with conditions, speaker/response data, scripts/fragments, and links/branching behavior.

### Dialogue branch
A grouping/flow structure used to organize dialogue topics and conversation progression.

### Response
The spoken line(s) and associated metadata associated with a dialogue info.

### VoiceType
Form that identifies a voice category and determines which recorded dialogue assets are valid/available for an actor or talking activator.

### Scene
A quest-owned coordinated sequence of actor actions such as dialogue, movement, packages, timers, or scripted phases.

### Scene phase
A segment of a scene timeline. Scene actions can be organized across phases and may be conditional.

### Scene action
One unit of work in a scene, such as dialogue, package execution, timer behavior, or other supported action.

### Scene fragment
Papyrus fragment executed at scene lifecycle/phase points according to Creation Kit configuration.

### TalkingActivator
A non-actor object type capable of participating in dialogue using a voice type.

## AI packages

### AI package
A record describing actor behavior under conditions, schedules, target/location data, and a procedure tree.

### Package stack
The ordered set of packages available to an actor from actor data, aliases, quest systems, combat overrides, and related sources.

### Package condition
Condition controlling whether a package is currently eligible.

### Procedure
A lower-level AI behavior building block, such as Travel, Follow, Sandbox, Patrol, Eat, Sleep, UseMagic, or Activate.

### Procedure tree
The configured sequence/branching of procedures that makes up package behavior.

### Package template
Reusable package/procedure configuration that can expose data inputs for specific packages.

### Package data
Parameters consumed by procedures, such as a destination, target, radius, object list, or location.

### Travel package
Package/procedure configuration directing an actor to travel to a target/location.

### Follow package
Package/procedure configuration directing an actor to follow a target.

### Sandbox package
Package allowing an actor to select activities within configured constraints.

### Patrol package
Package/procedure for moving through linked/patrol locations or markers.

### ForceGreet
AI/dialogue behavior used to make an actor initiate interaction/dialogue with a target.

### Combat override package
Package stack specifically used to override normal behavior during combat conditions.

### EvaluatePackage / EVP
Forces an actor to re-evaluate its package list. It does not mean “reset every AI system.”

### ResetAI
Broader AI-reset behavior than a package reevaluation. It should not be used casually as a generic workaround.

### Linked reference / LinkRef
Reference relationship connecting one placed reference to another, often used by packages, markers, patrol chains, traps, and level logic.

### Named linked reference
Linked reference relationship distinguished by a keyword/name so multiple semantic links can exist from a reference.

### XMarker
Invisible marker reference commonly used as a target/location/anchor for packages and scripted systems.

### XMarkerHeading
Marker variant that also provides facing/orientation information.

## Magic systems

### MagicEffect / MGEF
Primary functional effect definition behind spells, enchantments, potions, scrolls, shouts, and abilities.

### Effect archetype
Engine-coded behavior category for a MagicEffect. The archetype controls substantial native behavior independently of attached Papyrus scripts.

### ActiveMagicEffect
Runtime instance of a MagicEffect applied to a target. Papyrus scripts attached to magic effects commonly extend `ActiveMagicEffect`.

### Effect item
An entry in a spell/enchantment/potion/etc. that points to a MagicEffect and supplies magnitude, duration, area, cost/conditions, or related parameters.

### Spell
A form containing one or more effect items plus casting/delivery/type metadata.

### Ability
Spell type commonly used for persistent effects while the actor has the ability.

### Lesser Power
Spell/power type with its own casting/use behavior and cooldown rules.

### Shout
Form grouping Words of Power and associated spell/effect behavior.

### Enchantment
Magic-form data applied to weapons/armor and containing effect items.

### Target condition
Condition controlling whether an effect can apply to or remain applicable to a target, depending on where the condition is configured.

### Casting type
How a magic effect is cast, such as fire-and-forget or concentration.

### Delivery
How a spell/effect reaches its target, such as self, contact/touch, aimed projectile, target actor, or target location depending on form configuration.

### Magnitude
Numeric strength parameter supplied to an effect where the archetype/script uses magnitude.

### Duration
How long an effect persists where duration is meaningful.

### Area
Radius/area parameter for effects that use an area.

## Diagnostic rules encoded for Agent OS

1. A Papyrus log is not a native crash log and temporal proximity does not prove crash causation.
2. Before diagnosing a `None` error, inspect both script logic and property/alias lifecycle.
3. Distinguish base-form scripts, reference scripts, alias scripts, and ActiveMagicEffect instances; event behavior depends on host/lifecycle.
4. Existing save-side script state can outlive mod updates. Troubleshooting must record whether testing used a new game, clean save, or existing save.
5. Prefer events to aggressive polling where reliable events exist, but do not assume every state change has a suitable event.
6. Quest aliases can alter packages/spells/scripts temporarily; do not assume actor-base records contain every behavior seen in game.
7. EvaluatePackage reevaluates package selection; it is not a universal AI repair command.
8. MagicEffect archetype behavior and Papyrus behavior must be diagnosed separately.

## Sources

- Creation Kit Wiki — Category:Scripting: https://ck.uesp.net/wiki/Category:Scripting
- Creation Kit Wiki — Operator Reference: https://ck.uesp.net/wiki/Operator_Reference
- Creation Kit Wiki — Complete Example Scripts: https://ck.uesp.net/wiki/Complete_Example_Scripts
- Creation Kit Wiki — Papyrus logging: https://ck.uesp.net/wiki/User%3ADavidJCobb/Papyrus_logging
- Creation Kit Wiki — Papyrus INI settings: https://ck.uesp.net/wiki/INI_Settings_%28Papyrus%29
- Creation Kit Wiki — Creating Custom Couriers (historical quest/alias/package example): https://ck.uesp.net/wiki/Creating_Custom_Couriers
- Creation Kit Wiki — Package Fragments: https://ck.uesp.net/wiki/Package_Fragments
- Creation Kit Wiki — Procedures category: https://ck.uesp.net/wiki/Category:Procedures
- Creation Kit Wiki — EvaluatePackage: https://ck.uesp.net/wiki/EvaluatePackage
- Creation Kit Wiki — Magic Effect: https://ck.uesp.net/wiki/Magic_Effect
- Creation Kit Wiki — TalkingActivator: https://ck.uesp.net/wiki/TalkingActivator
- Creation Kit Wiki — SKSE Script Objects: https://ck.uesp.net/wiki/Category:SKSE_Script_Objects

## Provenance notes

The Creation Kit Wiki is invaluable but historically layered. Tutorial-specific workflows, especially pages from the original 2012 LE period, are evidence for terminology and system relationships, not automatically current best practice. Runtime-sensitive claims should be cross-checked against current SKSE/CommonLib/game behavior before Agent OS recommends implementation.
