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


## Native archetype ID table — CommonLibSSE-NG

Source: `alandtse/CommonLibSSE-NG/include/RE/E/EffectArchetypes.h` blob `ec299b8d2ebe615e13ba1cb4f46217aca0409b45`.

| Native enum | Value |
|---|---:|
| `kNone` | `static_cast<std::underlying_type_t<ArchetypeID>>(-1)` |
| `kValueModifier` | `0` |
| `kScript` | `1` |
| `kDispel` | `2` |
| `kCureDisease` | `3` |
| `kAbsorb` | `4` |
| `kDualValueModifier` | `5` |
| `kCalm` | `6` |
| `kDemoralize` | `7` |
| `kFrenzy` | `8` |
| `kDisarm` | `9` |
| `kCommandSummoned` | `10` |
| `kInvisibility` | `11` |
| `kLight` | `12` |
| `kDarkness` | `13` |
| `kNightEye` | `14` |
| `kLock` | `15` |
| `kOpen` | `16` |
| `kBoundWeapon` | `17` |
| `kSummonCreature` | `18` |
| `kDetectLife` | `19` |
| `kTelekinesis` | `20` |
| `kParalysis` | `21` |
| `kReanimate` | `22` |
| `kSoulTrap` | `23` |
| `kTurnUndead` | `24` |
| `kGuide` | `25` |
| `kWerewolfFeed` | `26` |
| `kCureParalysis` | `27` |
| `kCureAddiction` | `28` |
| `kCurePoison` | `29` |
| `kConcussion` | `30` |
| `kValueAndParts` | `31` |
| `kAccumulateMagnitude` | `32` |
| `kStagger` | `33` |
| `kPeakValueModifier` | `34` |
| `kCloak` | `35` |
| `kWerewolf` | `36` |
| `kSlowTime` | `37` |
| `kRally` | `38` |
| `kEnhanceWeapon` | `39` |
| `kSpawnHazard` | `40` |
| `kEtherealize` | `41` |
| `kBanish` | `42` |
| `kSpawnScriptedRef` | `43` |
| `kDisguise` | `44` |
| `kGrabActor` | `45` |
| `kVampireLord` | `46` |

This source exposes **47 numbered archetypes (0–46)** plus `None = -1`. It confirms native identities for behaviors that are only partially documented in the historical Creation Kit wiki, including Calm, Demoralize, Frenzy, Disarm, CommandSummoned, Darkness, NightEye, DetectLife, CureDisease/Paralysis/Addiction/Poison, Concussion, Cloak, EnhanceWeapon, Etherealize, Disguise, GrabActor and VampireLord.

### Archetype definition flags

CommonLib's native archetype metadata exposes:

| Flag | Bit |
|---|---|
| `kNone` | `0` |
| `kHiddenInEditor` | `1 << 0` |
| `kIsActorValueUsed` | `1 << 1` |
| `kIsFormUsed` | `1 << 2` |
| `kUnk3` | `1 << 3` |
| `kAllowStacking` | `1 << 4` |
| `kCannotMultiCast` | `1 << 5` |
| `kCreatesRef` | `1 << 6` |
| `kCustomSkillUse` | `1 << 7` |
| `kRewardsSkillUseWithoutTarget` | `1 << 8` |
| `kAddsEffectToCaster` | `1 << 9` |

These flags describe **the archetype definition itself**, such as whether:
- an ActorValue is used;
- an associated Form is used;
- stacking is allowed;
- multicasting is forbidden;
- the archetype creates a reference;
- skill use is custom;
- an effect is added to the caster.

They are distinct from per-MGEF DATA flags.

## Exact MGEF DATA flags — CommonLibSSE-NG

Source: `alandtse/CommonLibSSE-NG/include/RE/E/EffectSetting.h` blob `54392d1f425912ccab4cd8c2934bee9fb7cce443`.

| MGEF flag | Bit |
|---|---|
| `kNone` | `0` |
| `kHostile` | `1 << 0` |
| `kRecover` | `1 << 1` |
| `kDetrimental` | `1 << 2` |
| `kSnapToNavMesh` | `1 << 3` |
| `kNoHitEvent` | `1 << 4` |
| `kDispelWithKeywords` | `1 << 8` |
| `kNoDuration` | `1 << 9` |
| `kNoMagnitude` | `1 << 10` |
| `kNoArea` | `1 << 11` |
| `kFXPersist` | `1 << 12` |
| `kGoryVisuals` | `1 << 14` |
| `kHideInUI` | `1 << 15` |
| `kNoRecast` | `1 << 17` |
| `kPowerAffectsMagnitude` | `1 << 21` |
| `kPowerAffectsDuration` | `1 << 22` |
| `kPainless` | `1 << 26` |
| `kNoHitEffect` | `1 << 27` |
| `kNoDeathDispel` | `1 << 28` |

Notable native flags beyond the older shorthand in this module include:
- SnapToNavMesh;
- NoHitEvent;
- DispelWithKeywords;
- FXPersist;
- GoryVisuals;
- HideInUI;
- NoRecast;
- PowerAffectsMagnitude;
- PowerAffectsDuration;
- Painless;
- NoHitEffect;
- NoDeathDispel.

### Native MGEF data layout

Current CommonLib resolves these fields directly in `EffectSettingData`:
- flags;
- base cost;
- associated form;
- associated skill;
- resistance ActorValue;
- counter-effect count;
- light;
- taper weight/curve/duration;
- effect/enchant shaders;
- minimum skill;
- second ActorValue weight;
- archetype;
- primary/secondary ActorValues;
- projectile;
- explosion;
- casting type;
- delivery;
- casting/hit/enchant art;
- ImpactDataSet;
- skill-use multiplier;
- dual-cast data/scale;
- hit/enchant visuals;
- equip ability;
- ImageSpaceModifier;
- perk;
- casting sound level;
- AI score/delay.

This is the native counterpart to the xEdit/CK MGEF schema and provides a source-backed map for runtime plugins.

## Source reconciliation

The historical CK descriptions explain intended behavior; CommonLib provides the current reverse-engineered numeric identities and structure. Where the two differ in naming/detail:
1. preserve both;
2. treat numeric IDs/layout as CommonLib-version-scoped;
3. treat gameplay semantics as validated only where documentation/source/runtime evidence agrees.
