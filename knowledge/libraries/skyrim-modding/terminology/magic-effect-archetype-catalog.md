# Skyrim Modding Terminology — MagicEffect Archetype Catalog

Imported: 2026-09-24
Status: sourced finite-engine catalog pass

MagicEffect archetypes are native engine behaviors layered underneath any Papyrus scripts attached to a MGEF. A scripted effect can therefore have both archetype behavior and script behavior.

## Core archetypes

### Absorb
Transfers up to effect magnitude from a target ActorValue to caster. Commonly Health, Magicka or Stamina.

### Accum. Magnitude
Ward-related archetype that ramps an ActorValue from zero toward configured magnitude over time.

### Banish
Removes qualifying summoned actors up to the configured magnitude/level relationship.

### Bound Weapon
Creates/equips a configured weapon and dispels it when effect expires or weapon is sheathed according to vanilla behavior.

### Guide
Creates a trail of configured Hazard objects from caster toward nearest quest target, used by Clairvoyance-style effects.

### Invisibility
Sets invisibility state until broken. Invisibility does not silence spell noise/detection effects.

### Light
Creates/configures a light associated with the effect's visual attachment. Correct Hit Effect Art/node setup is part of visible result.

### Lock
Engine archetype intended to lock a target. CK documentation notes ordinary magic targeting makes this effectively unusable without script/object-target workarounds.

### Open
Engine archetype intended to unlock a target; same ordinary-targeting limitation as Lock.

### Paralysis
Paralyzes target and sets Paralyze ActorValue/state. CK documentation notes Recover must be set for expected behavior and targets should normally exclude ImmuneParalysis.

### Peak Value Modifier
Modifies an ActorValue while enforcing non-stacking behavior among effects sharing configured keyword/group semantics; commonly used for strongest-effect-wins style bonuses.

### Rally
Raises Confidence for targets up to magnitude/level rules.

### Reanimate
Animates a dead target under caster control.

### Script
No special native gameplay effect beyond attached Papyrus/visual/audio data. Use when behavior is entirely scripted.

### Slow Time
Globally slows world time relative to player according to multiplier semantics.

### Soul Trap
If target dies while effect active, engine attempts to fill suitable soul gem held by caster.

### Spawn Hazard
Creates configured Hazard at target and normally preserves caster ownership so hostile/allied filtering follows caster.

### Spawn Scripted Ref
Specialized engine archetype used by Throw Voice-style behavior where an explosion/placed activator drives result.

### Stagger
Applies target stagger according to magnitude in roughly 0–1 range. Duration acts as a stagger cooldown/retrigger relationship.

### Summon Creature
Creates configured ActorBase/creature under caster control and cleans/fades it on death/end according to summoned-actor semantics.

### Telekinesis
Enables distant manipulation of target ObjectReference and sets telekinesis state.

### Turn Undead
Fear-like flee effect hard-coded to ActorTypeUndead targets; conditions alone cannot make non-undead targets qualify.

### Value and Parts
Poorly documented native archetype. Treat behavior as reverse-engineering/test-required rather than relying on name.

### Value Modifier
Modifies configured ActorValue by effect magnitude. Recover determines whether value is restored on expiry versus repeatedly/permanently modified according to engine behavior.

### Werewolf
Changes target Race to configured race and participates in transformation semantics.

### Werewolf Feed
Sets/uses eaten/feed state on a dead actor for werewolf feeding behavior.

## Frequently referenced native-behavior families

### Demoralize-like behavior
Fear/flee behavior exists in engine magic systems even where CK archetype naming/documentation differs by source/version. Validate exact current archetype enum before authoring new native-only effect.

### Frenzy-like behavior
Aggression/combat manipulation can be expressed through engine effects/ActorValues. Do not invent undocumented archetype names solely from spell school labels.

### Calm-like behavior
Hostility/aggression suppression likewise may be implemented by underlying engine magic behavior plus actor values/conditions.

### Cloak behavior
Cloak spells use engine delivery/secondary-spell mechanics. Diagnose cloak spell, MGEF and emitted spell separately rather than assuming one simple area MGEF.

## Associated Items

### Assoc. Item 1
Archetype-specific form/value defining the main native target, such as ActorValue, Weapon, Light, Race, Hazard or summoned ActorBase.

### Assoc. Item 2
Secondary archetype-specific value; Peak Value Modifier and Dual Value-style effects can use it for grouping/secondary behavior.

### 2nd AV Weight
Magnitude multiplier for secondary ActorValue in dual-value calculations.

## Archetype interaction with flags

### Hostile
Marks effect as attack/hostile and enables resistance/crime/combat semantics where applicable.

### Detrimental
Makes ActorValue modification negative/harmful in engine handling; not every harmful effect should blindly use it.

### Recover
Restores modified ActorValue when effect ends for supported modifier archetypes. Changes Value Modifier/PVM semantics substantially.

### No Magnitude
UI/editor parameter suppression flag rather than proof native code never consults magnitude.

### No Duration
UI/editor availability flag rather than absolute guarantee archetype ignores duration.

### No Area
UI/editor availability flag.

## Conditions

### Effect-side condition
Checked when/repeated as MagicEffect instance is applied according to casting type. Determines whether target receives effect.

### Spell-side effect-item condition
Attached to EffectItem in parent spell/enchantment/potion; controls whether effect entry is active/applied.

### Concentration inversion
CK documentation notes ordinary-duration effects generally recheck spell-side conditions while active but apply MGEF once, whereas concentration casting can reapply MGEF each second and therefore recheck effect-side conditions repeatedly.

## Costs and skill

### Base Cost
MGEF input to auto-calculated spell/enchantment cost.

### Magic Skill
Skill associated with effect.

### Minimum Skill Level
NPC/UI spell-rank requirement/display tier input.

### Skill Usage Mult
XP/skill-use multiplier for spells using effect.

### Auto Calculate
Parent spell/enchantment cost calculation based on effect cost, magnitude, duration, skill and perk modifiers.

## Taper

### Taper Duration
Post-duration tail period.

### Taper Weight
Starting strength multiplier of taper.

### Taper Curve
Power curve controlling taper decay. Extreme negative values can produce pathological growth/divergence.

### Recover+taper interaction
CK documentation notes Recover effects do not use taper magnitude curve like ordinary effects; duration persistence remains but value behavior differs.

## Visual/data chain

A MagicEffect can also reference:
- Casting Art
- Casting Light
- Hit Effect Art
- Hit Shader
- Enchant Art
- Enchant Shader
- Projectile
- Explosion
- ImpactDataSet
- ImageSpaceModifier
- sounds
- Papyrus scripts

Archetype behavior and these visual/audio/script layers should be diagnosed separately.

## Diagnostic rules

1. Identify archetype before debugging attached script.
2. Do not emulate engine-native modifier behavior with polling Papyrus if an appropriate native archetype/perk entry exists.
3. Hard-coded archetype restrictions can override otherwise-valid conditions.
4. Hostile/Detrimental/Recover flags change engine semantics and should not be copied mechanically between effects.
5. Spell-side and MGEF-side conditions are evaluated at different lifecycle points.
6. Cost/magnitude problems can come from perk entry points and parent EffectItems even when MGEF looks correct.
7. Script archetype is the clean baseline for effects intended to be fully Papyrus-driven.

## Source

Primary: Creation Kit Wiki Magic Effect page: https://ck.uesp.net/wiki/Magic_Effect

The CK Wiki is historical/community-maintained. Archetype names/behavior above are treated as documented Skyrim behavior where explicitly described; poorly documented cases remain flagged for source/runtime testing rather than filled with folklore.
