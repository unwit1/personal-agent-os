# Skyrim Modding Terminology — Modern Runtime Frameworks and Animation/Combat APIs

Imported: 2026-09-24
Status: sourced deep-ingestion pass 4

## SkyPatcher

### SkyPatcher
SKSE runtime patching framework that applies configuration-driven changes to game forms at load/runtime rather than requiring prebuilt compatibility ESP patches for every target mod.

### SkyPatcher patcher
Subsystem/config family targeting a record category or gameplay domain.

### SkyPatcher INI
Declarative configuration consumed by a SkyPatcher module.

### Runtime form patch
Modification to loaded form data performed in memory after plugin records have been loaded.

### Dynamic compatibility
Pattern where configuration applies rules to whatever eligible forms exist in the current load order, reducing the need for explicit per-mod static patches.

### Automatic load-order adaptation
Runtime patchers can discover records from newly installed mods and apply broad rules without regenerating an ESP, provided the configuration criteria still match correctly.

### Runtime patch provenance
Because changes do not necessarily appear as ordinary plugin overrides in xEdit, debugging must inspect SkyPatcher configs/logs as well as static records.

### SkyPatcher Keyword Framework
Framework using SkyPatcher to add standardized semantic keywords across vanilla and mod-added forms so downstream mods can consume consistent categories.

### Runtime patch conflict
Two runtime patchers/configs may modify the same field/data in incompatible ways even when xEdit shows no plugin conflict.

### Runtime application order
Order in which runtime patchers/config files execute can affect final in-memory values. Do not assume plugin load order alone predicts runtime-patched state.

### SkyPatcher runtime families
Current files observed in 2026 distinguish SE 1.5.97, AE 1.6.640+/1.6.1170+/GOG and VR builds. Exact runtime compatibility remains native-plugin-sensitive.

## powerofthree's Tweaks

### po3 Tweaks
SKSE/VR native plugin collection implementing bug fixes and configurable gameplay/engine tweaks.

### Tweak plugin
Native plugin whose behavior is controlled through configuration switches rather than one fixed feature.

### Bug-fix framework
Shared native mod that fixes many engine edge cases and becomes a transitive dependency for a modlist's behavior assumptions.

### Native tweak interaction
Two engine-fix/tweak frameworks can touch similar code paths or game rules; compatibility should be checked by feature rather than by mod name alone.

## powerofthree's Papyrus Extender

### Papyrus Extender
SKSE64/VR plugin adding hundreds of Papyrus functions, events and script objects beyond vanilla/SKSE.

### Native Papyrus extension
C++ function/event exposed into Papyrus so script authors can access engine state not available in vanilla Papyrus.

### Extended event
New event source registered by a native plugin and delivered to scripts.

### Script-object extension
New Papyrus-visible object/class or functions bound to existing game types.

### API dependency
Mod scripts can require Papyrus Extender at runtime even when the ESP has no hard master dependency.

## Behavior Data Injector

### BDI
**Expansion:** Behavior Data Injector. SKSE plugin that injects custom animation graph variables and animation events at runtime through configs, avoiding some behavior-file patch requirements.

### Animation graph variable
Named bool/int/float value in a Havok behavior graph used by animation logic and readable/settable through engine/Papyrus/conditions.

### Runtime graph-variable injection
Adding graph variables to behavior projects in memory rather than generating modified HKX behavior files.

### Runtime animation-event injection
Adding event identifiers to behavior graphs so animation annotations or code can trigger new events without static behavior patches.

### BDI config
Declarative configuration describing graph variables/events to inject.

### BDI Universal Support
Compatibility build/fork adding AE/VR/current-runtime support beyond the original 1.5.97-only release.

### Serializable primitive actor state
BDI ecosystem usage can expose per-actor graph variables that other systems use as lightweight shared state; treat lifecycle/serialization details as implementation-specific.

## Payload Interpreter

### Payload Interpreter
SKSE plugin interpreting payload strings attached to animation annotations and converting them into runtime instructions.

### Animation annotation
Metadata/event marker embedded in an animation clip.

### Payload
String suffix attached to an annotation, separated from the annotation event name, used by Payload Interpreter as command data.

### Payload instruction
Structured `@COMMAND|arg|arg...` expression interpreted when its animation annotation fires.

### Dummy event / PIE
Animation event supplied specifically to host Payload Interpreter commands at arbitrary animation timestamps.

### Asynchronous payload
Payload command scheduled with a delay rather than executed immediately.

### Animation-driven scripting
Pattern where gameplay actions are synchronized precisely to animation markers without polling Papyrus timing.

## Animation Motion Revolution

### AMR
**Expansion:** Animation Motion Revolution. Native animation framework used by modern combat/animation mods to control actor motion/root-motion behavior from animation data.

### Root motion
Translation/rotation encoded in animation that moves the character, as distinct from game movement code moving the actor while an animation plays.

### Animation-driven movement
Actor motion synchronized to an animation clip rather than approximated through speed values alone.

### Motion data
Translation/rotation information associated with an animation and interpreted by a runtime framework.

## Precision

### Precision
SKSE native combat framework that replaces/extends melee hit detection with animation/weapon-geometry-aware collision and exposes a plugin API.

### Weapon collision
Runtime collision representation associated with weapon/body geometry rather than vanilla abstract attack reach alone.

### Hitbox
Collision volume/shape used to determine contact.

### Hurtbox
Target collision area representing body parts/actor geometry that can receive hits.

### Attack collision
Collision active during attack windows.

### Collision callback
API event/callback triggered when Precision evaluates contact/hit-related state.

### Precision API
Native cross-plugin API that allows other SKSE plugins to query/integrate with Precision.

### API version
Versioned interface identifier requested by dependent plugins to ensure compatible function layout.

### Dynamic API lookup
Precision exposes a request function from its DLL; dependent plugins can locate the loaded module/export and cache the returned interface pointer.

## Framework interaction principles

### Static behavior patch
Generated HKX modification through Pandora/Nemesis/FNIS.

### Runtime behavior injection
BDI-style graph variable/event injection without changing static HKX files.

### Runtime animation replacement
OAR-style choice of which animation clip is played.

### Animation payload execution
Payload Interpreter reacts to markers inside the selected animation.

### Root-motion control
AMR-style movement interpretation.

### Combat collision
Precision-style physical attack collision.

These are separate layers and may all participate in one combat mod.

## Diagnostic rules

1. A modern combat/animation stack can include Pandora, BDI, OAR, Payload Interpreter, AMR, Precision and po3 frameworks simultaneously; identify the failing layer instead of disabling "animation mods" generically.
2. Runtime patchers can conflict invisibly to xEdit because final changes occur in memory.
3. Native frameworks remain runtime/SKSE/version-sensitive even if their INI/config syntax looks unchanged.
4. Shared APIs should be version-checked. A DLL loading successfully does not prove another plugin requested the right API version.
5. For animation-timed gameplay, inspect annotation/payload/event timing before blaming Papyrus.
6. BDI can eliminate some behavior patch requirements, but not every behavior graph modification can be reduced to injected variables/events.
7. SkyPatcher, SPID, KID, BOS and FLM overlap conceptually as runtime data mutation but target different record/data patterns and have different semantics.

## Sources

- SkyPatcher Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/106659
- SkyPatcher Keyword Framework: https://www.nexusmods.com/skyrimspecialedition/mods/127024
- po3 Tweaks upstream: https://github.com/powerof3/po3-Tweaks
- powerofthree Papyrus Extender: https://github.com/powerof3/PapyrusExtenderSSE
- Behavior Data Injector: https://www.nexusmods.com/skyrimspecialedition/mods/78146
- BDI Universal Support: https://www.nexusmods.com/skyrimspecialedition/mods/78159
- Payload Interpreter: https://github.com/D7ry/PayloadInterpreter
- Animation Motion Revolution: https://github.com/alexsylex/AnimationMotionRevolution
- Precision: https://github.com/ersh1/Precision
- Precision API header: https://github.com/ersh1/Precision/blob/main/src/PrecisionAPI.h

## Dated notes

Behavior Data Injector Universal Support file observed 2026-09-24 was updated 2026-08-24 with CommonLibSSE-NG support including Skyrim 1.7.99. SkyPatcher had separate current-runtime downloads in August 2026. Treat these compatibility observations as dated.
