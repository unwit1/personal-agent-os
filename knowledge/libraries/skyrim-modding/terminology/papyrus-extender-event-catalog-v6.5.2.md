# powerofthree's Papyrus Extender v6.5.2 — Event Catalog

Imported: 2026-09-24
Release: `v6.5.2`
Status: finite source-derived event surface

## Source contexts

| Receiver context | PSC | Blob SHA | Event declarations | Registration/helper declarations |
|---|---|---|---:|---:|
| Alias | `Papyrus/Source/scripts/PO3_Events_Alias.psc` | `84c66be7d52c1a156ff43521f2bd31ce3c3f3eee` | 37 | 69 |
| ActiveMagicEffect | `Papyrus/Source/scripts/PO3_Events_AME.psc` | `1c7690d0404e5f0cff5475a25955522106efdfe4` | 37 | 69 |
| Form | `Papyrus/Source/scripts/PO3_Events_Form.psc` | `ec1cbca8a226177d72c70a22642e4f1080275e17` | 37 | 69 |

Each source exposes 37 event declarations. The same logical engine event can be registered to a Form, Alias/ReferenceAlias, or ActiveMagicEffect, depending on the dedicated provider script.

## Event signatures by receiver context

| # | Alias event | ActiveMagicEffect event | Form event |
|---:|---|---|---|
| 1 | `OnActorFallLongDistance(Actor akTarget, float afFallDistance, float afFallDamage)` | `OnActorFallLongDistance(Actor akTarget, float afFallDistance, float afFallDamage)` | `OnActorFallLongDistance(Actor akTarget, float afFallDistance, float afFallDamage)` |
| 2 | `OnActorKilled(Actor akVictim, Actor akKiller)` | `OnActorKilled(Actor akVictim, Actor akKiller)` | `OnActorKilled(Actor akVictim, Actor akKiller)` |
| 3 | `OnActorReanimateStart(Actor akTarget, Actor akCaster)` | `OnActorReanimateStart(Actor akTarget, Actor akCaster)` | `OnActorReanimateStart(Actor akTarget, Actor akCaster)` |
| 4 | `OnActorReanimateStop(Actor akTarget, Actor akCaster)` | `OnActorReanimateStop(Actor akTarget, Actor akCaster)` | `OnActorReanimateStop(Actor akTarget, Actor akCaster)` |
| 5 | `OnActorResurrected(Actor akTarget, bool abResetInventory)` | `OnActorResurrected(Actor akTarget, bool abResetInventory)` | `OnActorResurrected(Actor akTarget, bool abResetInventory)` |
| 6 | `OnBookRead(Book akBook)` | `OnBookRead(Book akBook)` | `OnBookRead(Book akBook)` |
| 7 | `OnCellFullyLoaded(Cell akCell)` | `OnCellFullyLoaded(Cell akCell)` | `OnCellFullyLoaded(Cell akCell)` |
| 8 | `OnCriticalHit(Actor akAggressor, Weapon akWeapon, bool abSneakHit)` | `OnCriticalHit(Actor akAggressor, Weapon akWeapon, bool abSneakHit)` | `OnCriticalHit(Actor akAggressor, Weapon akWeapon, bool abSneakHit)` |
| 9 | `OnDisarmed(Actor akSource, Weapon akTarget)` | `OnDisarmed(Actor akSource, Weapon akTarget)` | `OnDisarmed(Actor akSource, Weapon akTarget)` |
| 10 | `OnDragonSoulGained(float afSouls)` | `OnDragonSoulGained(float afSouls)` | `OnDragonSoulGained(float afSouls)` |
| 11 | `OnPlayerFastTravelEnd(float afTravelGameTimeHours)` | `OnPlayerFastTravelEnd(float afTravelGameTimeHours)` | `OnPlayerFastTravelEnd(float afTravelGameTimeHours)` |
| 12 | `OnFastTravelConfirmed(ObjectReference asMarkerReference)` | `OnFastTravelConfirmed(ObjectReference asMarkerReference)` | `OnFastTravelConfirmed(ObjectReference asMarkerReference)` |
| 13 | `OnFastTravelPrompt(ObjectReference asMarkerReference)` | `OnFastTravelPrompt(ObjectReference asMarkerReference)` | `OnFastTravelPrompt(ObjectReference asMarkerReference)` |
| 14 | `OnEnterFurniture(ObjectReference akRef)` | `OnEnterFurniture(ObjectReference akRef)` | `OnEnterFurniture(ObjectReference akRef)` |
| 15 | `OnExitFurniture(ObjectReference akRef)` | `OnExitFurniture(ObjectReference akRef)` | `OnExitFurniture(ObjectReference akRef)` |
| 16 | `OnHitEx(ObjectReference akAggressor, Form akSource, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked)` | `OnHitEx(ObjectReference akAggressor, Form akSource, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked)` | `OnHitEx(ObjectReference akAggressor, Form akSource, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked)` |
| 17 | `OnItemCrafted(ObjectReference akBench, Location akLocation, Form akCreatedItem)` | `OnItemCrafted(ObjectReference akBench, Location akLocation, Form akCreatedItem)` | `OnItemCrafted(ObjectReference akBench, Location akLocation, Form akCreatedItem)` |
| 18 | `OnItemHarvested(Form akProduce)` | `OnItemHarvested(Form akProduce)` | `OnItemHarvested(Form akProduce)` |
| 19 | `OnLevelIncrease(int aiLevel)` | `OnLevelIncrease(int aiLevel)` | `OnLevelIncrease(int aiLevel)` |
| 20 | `OnLocationDiscovery(String asRegionName, String asWorldspaceName)` | `OnLocationDiscovery(String asRegionName, String asWorldspaceName)` | `OnLocationDiscovery(String asRegionName, String asWorldspaceName)` |
| 21 | `OnObjectGrab(ObjectReference akObjectRef)` | `OnObjectGrab(ObjectReference akObjectRef)` | `OnObjectGrab(ObjectReference akObjectRef)` |
| 22 | `OnObjectRelease(ObjectReference akObjectRef)` | `OnObjectRelease(ObjectReference akObjectRef)` | `OnObjectRelease(ObjectReference akObjectRef)` |
| 23 | `OnObjectLoaded(ObjectReference akRef, int aiFormType)` | `OnObjectLoaded(ObjectReference akRef, int aiFormType)` | `OnObjectLoaded(ObjectReference akRef, int aiFormType)` |
| 24 | `OnObjectUnloaded(ObjectReference akRef, int aiFormType)` | `OnObjectUnloaded(ObjectReference akRef, int aiFormType)` | `OnObjectUnloaded(ObjectReference akRef, int aiFormType)` |
| 25 | `OnObjectPoisoned(Form akObject, Potion akPoison, int aiDose)` | `OnObjectPoisoned(Form akObject, Potion akPoison, int aiDose)` | `OnObjectPoisoned(Form akObject, Potion akPoison, int aiDose)` |
| 26 | `OnQuestStart(Quest akQuest)` | `OnQuestStart(Quest akQuest)` | `OnQuestStart(Quest akQuest)` |
| 27 | `OnQuestStop(Quest akQuest)` | `OnQuestStop(Quest akQuest)` | `OnQuestStop(Quest akQuest)` |
| 28 | `OnQuestStageChange(Quest akQuest, Int aiNewStage)` | `OnQuestStageChange(Quest akQuest, Int aiNewStage)` | `OnQuestStageChange(Quest akQuest, Int aiNewStage)` |
| 29 | `OnShoutAttack(Shout akShout)` | `OnPlayerShoutAttack(Shout akShout)` | `OnPlayerShoutAttack(Shout akShout)` |
| 30 | `OnSkillIncrease(Int aiSkill)` | `OnSkillIncrease(Int aiSkill)` | `OnSkillIncrease(Int aiSkill)` |
| 31 | `OnSoulTrapped(Actor akVictim, Actor akKiller)` | `OnSoulTrapped(Actor akVictim, Actor akKiller)` | `OnSoulTrapped(Actor akVictim, Actor akKiller)` |
| 32 | `OnSpellLearned(Spell akSpell)` | `OnSpellLearned(Spell akSpell)` | `OnSpellLearned(Spell akSpell)` |
| 33 | `OnWeatherChange(Weather akOldWeather, Weather akNewWeather)` | `OnWeatherChange(Weather akOldWeather, Weather akNewWeather)` | `OnWeatherChange(Weather akOldWeather, Weather akNewWeather)` |
| 34 | `OnMagicEffectApplyEx(ObjectReference akCaster, MagicEffect akEffect, Form akSource, bool abApplied)` | `OnMagicEffectApplyEx(ObjectReference akCaster, MagicEffect akEffect, Form akSource, bool abApplied)` | `OnMagicEffectApplyEx(ObjectReference akCaster, MagicEffect akEffect, Form akSource, bool abApplied)` |
| 35 | `OnWeaponHit(ObjectReference akTarget, Form akSource, Projectile akProjectile, Int aiHitFlagMask)` | `OnWeaponHit(ObjectReference akTarget, Form akSource, Projectile akProjectile, Int aiHitFlagMask)` | `OnWeaponHit(ObjectReference akTarget, Form akSource, Projectile akProjectile, Int aiHitFlagMask)` |
| 36 | `OnMagicHit(ObjectReference akTarget, Form akSource, Projectile akProjectile)` | `OnMagicHit(ObjectReference akTarget, Form akSource, Projectile akProjectile)` | `OnMagicHit(ObjectReference akTarget, Form akSource, Projectile akProjectile)` |
| 37 | `OnProjectileHit(ObjectReference akTarget, Form akSource, Projectile akProjectile)` | `OnProjectileHit(ObjectReference akTarget, Form akSource, Projectile akProjectile)` | `OnProjectileHit(ObjectReference akTarget, Form akSource, Projectile akProjectile)` |

## Known source-name inconsistency

The registration function is `RegisterForShoutAttack` in all three contexts, but v6.5.2 declares:

- Alias: `OnShoutAttack(Shout akShout)`
- ActiveMagicEffect: `OnPlayerShoutAttack(Shout akShout)`
- Form: `OnPlayerShoutAttack(Shout akShout)`

Do not normalize this away in generated code or documentation. Use the exact event name for the receiver context/version.

## Registration APIs

The event providers include ordinary register/unregister pairs plus several filtered/multi-registration families.

### Hit Event Ex

Supports filters for aggressor, source, projectile and additional hit semantics. Also exposes `UnregisterForAllHitEventsEx`.

### Object Loaded

Registration includes a FormType integer, with `UnregisterForAllObjectsLoaded`.

### Quest

Register/unregister against a specific Quest plus `UnregisterForAllQuests`.

### Quest Stage

Register/unregister against a specific Quest plus `UnregisterForAllQuestStages`.

### Magic Effect Apply Ex

Register/unregister with effect filter + match behavior, plus all-registration cleanup.

### Furniture event

Reference-oriented registration produces both enter and exit callbacks.

### Object grab

One registration family produces both grab and release callbacks.

### Object loaded

One registration family produces both loaded and unloaded callbacks.

### Actor reanimation

Separate Start and Stop registration functions/events.

## Event families represented

- actor fall, death, reanimation and resurrection;
- books;
- cell loading;
- critical hits and disarm;
- dragon souls;
- fast travel prompt/confirmation/end;
- furniture enter/exit;
- extended hit events;
- crafting and harvesting;
- player/skill level increases;
- location discovery;
- object grab/release/load/unload/poison;
- quest start/stop/stage;
- shout attacks;
- soul trapping;
- spell learning;
- weather changes;
- magic-effect application;
- weapon, magic and projectile hit events.

## Lifecycle rules

1. Registration is state. Register once at an appropriate lifecycle point and unregister when the receiver no longer needs events.
2. Alias and ActiveMagicEffect lifetime differs from a persistent quest Form. Choose receiver context intentionally.
3. Save persistence can retain registrations across load depending on VM state; mod updates must consider stale registrations.
4. Filtered registration APIs should be paired with the matching filtered or all-unregister API.
5. Exact event names/signatures are versioned API contracts.
6. A missing callback can be caused by failed native registration, wrong receiver type, lifecycle teardown, filter mismatch, or the provider DLL not loading.
