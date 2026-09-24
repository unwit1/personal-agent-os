# powerofthree's Papyrus Extender — Complete PSC API Catalog

Imported: 2026-09-24
Source: https://github.com/powerof3/PapyrusExtenderSSE · ref `master`
Current repository CMake version observed during ingestion: **6.5.1**
Scripts: **8**
Declarations: **703** (592 functions, 111 events, 0 properties)
Native declarations: **592**
Global declarations: **592**
Status: generated source-derived API catalog

## Debris extends Form

Source: `Papyrus/Source/scripts/Debris.psc` · blob `13e8cdba871e316bcbc3e77bcc0c34197e8c6a77`

| Kind | Name | Declaration | Line |
|---|---|---|---:|

## FootstepSet extends Form

Source: `Papyrus/Source/scripts/FootstepSet.psc` · blob `9ac46dc3cbcf265a1f5c7b176bbf157f50657ad4`

| Kind | Name | Declaration | Line |
|---|---|---|---:|

## LightingTemplate extends Form

Source: `Papyrus/Source/scripts/LightingTemplate.psc` · blob `422342b36d0e829e82321e8779bf5e1c4ce67c4f`

| Kind | Name | Declaration | Line |
|---|---|---|---:|

## MaterialObject extends Form

Source: `Papyrus/Source/scripts/MaterialObject.psc` · blob `d289af8cef6492a608f8bb0d4032af011d03a386`

| Kind | Name | Declaration | Line |
|---|---|---|---:|

## PO3_Events_AME

Source: `Papyrus/Source/scripts/PO3_Events_AME.psc` · blob `1c7690d0404e5f0cff5475a25955522106efdfe4`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `RegisterForActorFallLongDistance` | `Function RegisterForActorFallLongDistance(ActiveMagicEffect akActiveEffect) global native` | 8 |
| function | `UnregisterForActorFallLongDistance` | `Function UnregisterForActorFallLongDistance(ActiveMagicEffect akActiveEffect) global native` | 9 |
| event | `OnActorFallLongDistance` | `Event OnActorFallLongDistance(Actor akTarget, float afFallDistance, float afFallDamage)` | 11 |
| function | `RegisterForActorKilled` | `Function RegisterForActorKilled(ActiveMagicEffect akActiveEffect) global native` | 16 |
| function | `UnregisterForActorKilled` | `Function UnregisterForActorKilled(ActiveMagicEffect akActiveEffect) global native` | 17 |
| event | `OnActorKilled` | `Event OnActorKilled(Actor akVictim, Actor akKiller)` | 19 |
| function | `RegisterForActorReanimateStart` | `Function RegisterForActorReanimateStart(ActiveMagicEffect akActiveEffect) global native` | 24 |
| function | `UnregisterForActorReanimateStart` | `Function UnregisterForActorReanimateStart(ActiveMagicEffect akActiveEffect) global native` | 25 |
| function | `RegisterForActorReanimateStop` | `Function RegisterForActorReanimateStop(ActiveMagicEffect akActiveEffect) global native` | 27 |
| function | `UnregisterForActorReanimateStop` | `Function UnregisterForActorReanimateStop(ActiveMagicEffect akActiveEffect) global native` | 28 |
| event | `OnActorReanimateStart` | `Event OnActorReanimateStart(Actor akTarget, Actor akCaster)` | 30 |
| event | `OnActorReanimateStop` | `Event OnActorReanimateStop(Actor akTarget, Actor akCaster)` | 33 |
| function | `RegisterForActorResurrected` | `Function RegisterForActorResurrected(ActiveMagicEffect akActiveEffect) global native` | 38 |
| function | `UnregisterForActorResurrected` | `Function UnregisterForActorResurrected(ActiveMagicEffect akActiveEffect) global native` | 39 |
| event | `OnActorResurrected` | `Event OnActorResurrected(Actor akTarget, bool abResetInventory)` | 41 |
| function | `RegisterForBookRead` | `Function RegisterForBookRead(ActiveMagicEffect akActiveEffect) global native` | 46 |
| function | `UnregisterForBookRead` | `Function UnregisterForBookRead(ActiveMagicEffect akActiveEffect) global native` | 47 |
| event | `OnBookRead` | `Event OnBookRead(Book akBook)` | 49 |
| function | `RegisterForCellFullyLoaded` | `Function RegisterForCellFullyLoaded(ActiveMagicEffect akActiveEffect) global native` | 54 |
| function | `UnregisterForCellFullyLoaded` | `Function UnregisterForCellFullyLoaded(ActiveMagicEffect akActiveEffect) global native` | 55 |
| event | `OnCellFullyLoaded` | `Event OnCellFullyLoaded(Cell akCell)` | 57 |
| function | `RegisterForCriticalHit` | `Function RegisterForCriticalHit(ActiveMagicEffect akActiveEffect) global native` | 62 |
| function | `UnregisterForCriticalHit` | `Function UnregisterForCriticalHit(ActiveMagicEffect akActiveEffect) global native` | 63 |
| event | `OnCriticalHit` | `Event OnCriticalHit(Actor akAggressor, Weapon akWeapon, bool abSneakHit)` | 65 |
| function | `RegisterForDisarmed` | `Function RegisterForDisarmed(ActiveMagicEffect akActiveEffect) global native` | 70 |
| function | `UnregisterForDisarmed` | `Function UnregisterForDisarmed(ActiveMagicEffect akActiveEffect) global native` | 71 |
| event | `OnDisarmed` | `Event OnDisarmed(Actor akSource, Weapon akTarget)` | 73 |
| function | `RegisterForDragonSoulGained` | `Function RegisterForDragonSoulGained(ActiveMagicEffect akActiveEffect) global native` | 78 |
| function | `UnregisterForDragonSoulGained` | `Function UnregisterForDragonSoulGained(ActiveMagicEffect akActiveEffect) global native` | 79 |
| event | `OnDragonSoulGained` | `Event OnDragonSoulGained(float afSouls)` | 81 |
| function | `RegisterForOnPlayerFastTravelEnd` | `Function RegisterForOnPlayerFastTravelEnd(ActiveMagicEffect akActiveEffect) global native` | 86 |
| function | `UnregisterForOnPlayerFastTravelEnd` | `Function UnregisterForOnPlayerFastTravelEnd(ActiveMagicEffect akActiveEffect) global native` | 87 |
| event | `OnPlayerFastTravelEnd` | `Event OnPlayerFastTravelEnd(float afTravelGameTimeHours)` | 89 |
| function | `RegisterForFastTravelConfirmed` | `Function RegisterForFastTravelConfirmed(ActiveMagicEffect akActiveEffect) global native` | 94 |
| function | `UnregisterForFastTravelConfirmed` | `Function UnregisterForFastTravelConfirmed(ActiveMagicEffect akActiveEffect) global native` | 95 |
| event | `OnFastTravelConfirmed` | `Event OnFastTravelConfirmed(ObjectReference asMarkerReference)` | 97 |
| function | `RegisterForFastTravelPrompt` | `Function RegisterForFastTravelPrompt(ActiveMagicEffect akActiveEffect) global native` | 102 |
| function | `UnregisterForFastTravelPrompt` | `Function UnregisterForFastTravelPrompt(ActiveMagicEffect akActiveEffect) global native` | 103 |
| event | `OnFastTravelPrompt` | `Event OnFastTravelPrompt(ObjectReference asMarkerReference)` | 105 |
| function | `RegisterForFurnitureEvent` | `Function RegisterForFurnitureEvent(ActiveMagicEffect akActiveEffect) global native` | 110 |
| function | `UnregisterForFurnitureEvent` | `Function UnregisterForFurnitureEvent(ActiveMagicEffect akActiveEffect) global native` | 111 |
| event | `OnEnterFurniture` | `Event OnEnterFurniture(ObjectReference akRef)` | 113 |
| event | `OnExitFurniture` | `Event OnExitFurniture(ObjectReference akRef)` | 116 |
| function | `RegisterForHitEventEx` | `Function RegisterForHitEventEx(ActiveMagicEffect akActiveEffect, Form akAggressorFilter = None, Form akSourceFilter = None, Form akProjectileFilter = None, \ int aiPowerFilter = -1, int aiSneakFilter = -1, int aiBashFilter = -1, int aiBlockFilter = -1, bool abMatch = true) global native` | 121 |
| function | `UnregisterForHitEventEx` | `Function UnregisterForHitEventEx(ActiveMagicEffect akActiveEffect, Form akAggressorFilter = None, Form akSourceFilter = None, Form akProjectileFilter = None, \ int aiPowerFilter = -1, int aiSneakFilter = -1, int aiBashFilter = -1, int aiBlockFilter = -1, bool abMatch = true) global native` | 124 |
| function | `UnregisterForAllHitEventsEx` | `Function UnregisterForAllHitEventsEx(ActiveMagicEffect akActiveEffect) global native` | 127 |
| event | `OnHitEx` | `Event OnHitEx(ObjectReference akAggressor, Form akSource, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked)` | 129 |
| function | `RegisterForItemCrafted` | `Function RegisterForItemCrafted(ActiveMagicEffect akActiveEffect) global native` | 134 |
| function | `UnregisterForItemCrafted` | `Function UnregisterForItemCrafted(ActiveMagicEffect akActiveEffect) global native` | 135 |
| event | `OnItemCrafted` | `Event OnItemCrafted(ObjectReference akBench, Location akLocation, Form akCreatedItem)` | 137 |
| function | `RegisterForItemHarvested` | `Function RegisterForItemHarvested(ActiveMagicEffect akActiveEffect) global native` | 142 |
| function | `UnregisterForItemHarvested` | `Function UnregisterForItemHarvested(ActiveMagicEffect akActiveEffect) global native` | 143 |
| event | `OnItemHarvested` | `Event OnItemHarvested(Form akProduce)` | 145 |
| function | `RegisterForLevelIncrease` | `Function RegisterForLevelIncrease(ActiveMagicEffect akActiveEffect) global native` | 150 |
| function | `UnregisterForLevelIncrease` | `Function UnregisterForLevelIncrease(ActiveMagicEffect akActiveEffect) global native` | 151 |
| event | `OnLevelIncrease` | `Event OnLevelIncrease(int aiLevel)` | 153 |
| function | `RegisterForLocationDiscovery` | `Function RegisterForLocationDiscovery(ActiveMagicEffect akActiveEffect) global native` | 158 |
| function | `UnregisterForLocationDiscovery` | `Function UnregisterForLocationDiscovery(ActiveMagicEffect akActiveEffect) global native` | 159 |
| event | `OnLocationDiscovery` | `Event OnLocationDiscovery(String asRegionName, String asWorldspaceName)` | 161 |
| function | `RegisterForObjectGrab` | `Function RegisterForObjectGrab(ActiveMagicEffect akActiveEffect) global native` | 166 |
| function | `UnregisterForObjectGrab` | `Function UnregisterForObjectGrab(ActiveMagicEffect akActiveEffect) global native` | 167 |
| event | `OnObjectGrab` | `Event OnObjectGrab(ObjectReference akObjectRef)` | 169 |
| event | `OnObjectRelease` | `Event OnObjectRelease(ObjectReference akObjectRef)` | 172 |
| function | `RegisterForObjectLoaded` | `Function RegisterForObjectLoaded(ActiveMagicEffect akActiveEffect, int formType) global native` | 177 |
| function | `UnregisterForObjectLoaded` | `Function UnregisterForObjectLoaded(ActiveMagicEffect akActiveEffect, int formType) global native` | 178 |
| function | `UnregisterForAllObjectsLoaded` | `Function UnregisterForAllObjectsLoaded(ActiveMagicEffect akActiveEffect) global native` | 179 |
| event | `OnObjectLoaded` | `Event OnObjectLoaded(ObjectReference akRef, int aiFormType)` | 181 |
| event | `OnObjectUnloaded` | `Event OnObjectUnloaded(ObjectReference akRef, int aiFormType)` | 184 |
| function | `RegisterForObjectPoisoned` | `Function RegisterForObjectPoisoned(ActiveMagicEffect akActiveEffect) global native` | 189 |
| function | `UnregisterForObjectPoisoned` | `Function UnregisterForObjectPoisoned(ActiveMagicEffect akActiveEffect) global native` | 190 |
| event | `OnObjectPoisoned` | `Event OnObjectPoisoned(Form akObject, Potion akPoison, int aiDose)` | 192 |
| function | `RegisterForQuest` | `Function RegisterForQuest(ActiveMagicEffect akActiveEffect, Quest akQuest) global native` | 197 |
| function | `UnregisterForQuest` | `Function UnregisterForQuest(ActiveMagicEffect akActiveEffect, Quest akQuest) global native` | 198 |
| function | `UnregisterForAllQuests` | `Function UnregisterForAllQuests(ActiveMagicEffect akActiveEffect) global native` | 199 |
| event | `OnQuestStart` | `Event OnQuestStart(Quest akQuest)` | 201 |
| event | `OnQuestStop` | `Event OnQuestStop(Quest akQuest)` | 204 |
| function | `RegisterForQuestStage` | `Function RegisterForQuestStage(ActiveMagicEffect akActiveEffect, Quest akQuest) global native` | 209 |
| function | `UnregisterForQuestStage` | `Function UnregisterForQuestStage(ActiveMagicEffect akActiveEffect, Quest akQuest) global native` | 210 |
| function | `UnregisterForAllQuestStages` | `Function UnregisterForAllQuestStages(ActiveMagicEffect akActiveEffect) global native` | 211 |
| event | `OnQuestStageChange` | `Event OnQuestStageChange(Quest akQuest, Int aiNewStage)` | 213 |
| function | `RegisterForShoutAttack` | `Function RegisterForShoutAttack(ActiveMagicEffect akActiveEffect) global native` | 218 |
| function | `UnregisterForShoutAttack` | `Function UnregisterForShoutAttack(ActiveMagicEffect akActiveEffect) global native` | 219 |
| event | `OnPlayerShoutAttack` | `Event OnPlayerShoutAttack(Shout akShout)` | 221 |
| function | `RegisterForSkillIncrease` | `Function RegisterForSkillIncrease(ActiveMagicEffect akActiveEffect) global native` | 226 |
| function | `UnregisterForSkillIncrease` | `Function UnregisterForSkillIncrease(ActiveMagicEffect akActiveEffect) global native` | 227 |
| event | `OnSkillIncrease` | `Event OnSkillIncrease(Int aiSkill)` | 229 |
| function | `RegisterForSoulTrapped` | `Function RegisterForSoulTrapped(ActiveMagicEffect akActiveEffect) global native` | 234 |
| function | `UnregisterForSoulTrapped` | `Function UnregisterForSoulTrapped(ActiveMagicEffect akActiveEffect) global native` | 235 |
| event | `OnSoulTrapped` | `Event OnSoulTrapped(Actor akVictim, Actor akKiller)` | 237 |
| function | `RegisterForSpellLearned` | `Function RegisterForSpellLearned(ActiveMagicEffect akActiveEffect) global native` | 242 |
| function | `UnregisterForSpellLearned` | `Function UnregisterForSpellLearned(ActiveMagicEffect akActiveEffect) global native` | 243 |
| event | `OnSpellLearned` | `Event OnSpellLearned(Spell akSpell)` | 245 |
| function | `RegisterForWeatherChange` | `Function RegisterForWeatherChange(ActiveMagicEffect akActiveEffect) global native` | 250 |
| function | `UnregisterForWeatherChange` | `Function UnregisterForWeatherChange(ActiveMagicEffect akActiveEffect) global native` | 251 |
| event | `OnWeatherChange` | `Event OnWeatherChange(Weather akOldWeather, Weather akNewWeather)` | 253 |
| function | `RegisterForMagicEffectApplyEx` | `Function RegisterForMagicEffectApplyEx(ActiveMagicEffect akActiveEffect, Form akEffectFilter, bool abMatch) global native` | 258 |
| function | `UnregisterForMagicEffectApplyEx` | `Function UnregisterForMagicEffectApplyEx(ActiveMagicEffect akActiveEffect, Form akEffectFilter, bool abMatch) global native` | 259 |
| function | `UnregisterForAllMagicEffectApplyEx` | `Function UnregisterForAllMagicEffectApplyEx(ActiveMagicEffect akActiveEffect) global native` | 260 |
| event | `OnMagicEffectApplyEx` | `Event OnMagicEffectApplyEx(ObjectReference akCaster, MagicEffect akEffect, Form akSource, bool abApplied)` | 262 |
| function | `RegisterForWeaponHit` | `Function RegisterForWeaponHit(ActiveMagicEffect akActiveEffect) global native` | 267 |
| function | `UnregisterForWeaponHit` | `Function UnregisterForWeaponHit(ActiveMagicEffect akActiveEffect) global native` | 268 |
| event | `OnWeaponHit` | `Event OnWeaponHit(ObjectReference akTarget, Form akSource, Projectile akProjectile, Int aiHitFlagMask)` | 270 |
| function | `RegisterForMagicHit` | `Function RegisterForMagicHit(ActiveMagicEffect akActiveEffect) global native` | 275 |
| function | `UnregisterForMagicHit` | `Function UnregisterForMagicHit(ActiveMagicEffect akActiveEffect) global native` | 276 |
| event | `OnMagicHit` | `Event OnMagicHit(ObjectReference akTarget, Form akSource, Projectile akProjectile)` | 278 |
| function | `RegisterForProjectileHit` | `Function RegisterForProjectileHit(ActiveMagicEffect akActiveEffect) global native` | 283 |
| function | `UnregisterForProjectileHit` | `Function UnregisterForProjectileHit(ActiveMagicEffect akActiveEffect) global native` | 284 |
| event | `OnProjectileHit` | `Event OnProjectileHit(ObjectReference akTarget, Form akSource, Projectile akProjectile)` | 286 |

## PO3_Events_Alias

Source: `Papyrus/Source/scripts/PO3_Events_Alias.psc` · blob `84c66be7d52c1a156ff43521f2bd31ce3c3f3eee`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `RegisterForActorFallLongDistance` | `Function RegisterForActorFallLongDistance(ReferenceAlias akRefAlias) global native` | 9 |
| function | `UnregisterForActorFallLongDistance` | `Function UnregisterForActorFallLongDistance(ReferenceAlias akRefAlias) global native` | 10 |
| event | `OnActorFallLongDistance` | `Event OnActorFallLongDistance(Actor akTarget, float afFallDistance, float afFallDamage)` | 12 |
| function | `RegisterForActorKilled` | `Function RegisterForActorKilled(Alias akAlias) global native` | 17 |
| function | `UnregisterForActorKilled` | `Function UnregisterForActorKilled(Alias akAlias) global native` | 18 |
| event | `OnActorKilled` | `Event OnActorKilled(Actor akVictim, Actor akKiller)` | 20 |
| function | `RegisterForActorReanimateStart` | `Function RegisterForActorReanimateStart(Alias akAlias) global native` | 25 |
| function | `UnregisterForActorReanimateStart` | `Function UnregisterForActorReanimateStart(Alias akAlias) global native` | 26 |
| function | `RegisterForActorReanimateStop` | `Function RegisterForActorReanimateStop(Alias akAlias) global native` | 28 |
| function | `UnregisterForActorReanimateStop` | `Function UnregisterForActorReanimateStop(Alias akAlias) global native` | 29 |
| event | `OnActorReanimateStart` | `Event OnActorReanimateStart(Actor akTarget, Actor akCaster)` | 31 |
| event | `OnActorReanimateStop` | `Event OnActorReanimateStop(Actor akTarget, Actor akCaster)` | 34 |
| function | `RegisterForActorResurrected` | `Function RegisterForActorResurrected(Alias akAlias) global native` | 39 |
| function | `UnregisterForActorResurrected` | `Function UnregisterForActorResurrected(Alias akAlias) global native` | 40 |
| event | `OnActorResurrected` | `Event OnActorResurrected(Actor akTarget, bool abResetInventory)` | 42 |
| function | `RegisterForBookRead` | `Function RegisterForBookRead(Alias akAlias) global native` | 47 |
| function | `UnregisterForBookRead` | `Function UnregisterForBookRead(Alias akAlias) global native` | 48 |
| event | `OnBookRead` | `Event OnBookRead(Book akBook)` | 50 |
| function | `RegisterForCellFullyLoaded` | `Function RegisterForCellFullyLoaded(Alias akAlias) global native` | 55 |
| function | `UnregisterForCellFullyLoaded` | `Function UnregisterForCellFullyLoaded(Alias akAlias) global native` | 56 |
| event | `OnCellFullyLoaded` | `Event OnCellFullyLoaded(Cell akCell)` | 58 |
| function | `RegisterForCriticalHit` | `Function RegisterForCriticalHit(Alias akAlias) global native` | 63 |
| function | `UnregisterForCriticalHit` | `Function UnregisterForCriticalHit(Alias akAlias) global native` | 64 |
| event | `OnCriticalHit` | `Event OnCriticalHit(Actor akAggressor, Weapon akWeapon, bool abSneakHit)` | 66 |
| function | `RegisterForDisarmed` | `Function RegisterForDisarmed(Alias akAlias) global native` | 71 |
| function | `UnregisterForDisarmed` | `Function UnregisterForDisarmed(Alias akAlias) global native` | 72 |
| event | `OnDisarmed` | `Event OnDisarmed(Actor akSource, Weapon akTarget)` | 74 |
| function | `RegisterForDragonSoulGained` | `Function RegisterForDragonSoulGained(Alias akAlias) global native` | 79 |
| function | `UnregisterForDragonSoulGained` | `Function UnregisterForDragonSoulGained(Alias akAlias) global native` | 80 |
| event | `OnDragonSoulGained` | `Event OnDragonSoulGained(float afSouls)` | 82 |
| function | `RegisterForOnPlayerFastTravelEnd` | `Function RegisterForOnPlayerFastTravelEnd(Alias akAlias) global native` | 87 |
| function | `UnregisterForOnPlayerFastTravelEnd` | `Function UnregisterForOnPlayerFastTravelEnd(Alias akAlias) global native` | 88 |
| event | `OnPlayerFastTravelEnd` | `Event OnPlayerFastTravelEnd(float afTravelGameTimeHours)` | 90 |
| function | `RegisterForFastTravelConfirmed` | `Function RegisterForFastTravelConfirmed(Alias akAlias) global native` | 95 |
| function | `UnregisterForFastTravelConfirmed` | `Function UnregisterForFastTravelConfirmed(Alias akAlias) global native` | 96 |
| event | `OnFastTravelConfirmed` | `Event OnFastTravelConfirmed(ObjectReference asMarkerReference)` | 98 |
| function | `RegisterForFastTravelPrompt` | `Function RegisterForFastTravelPrompt(Alias akAlias) global native` | 103 |
| function | `UnregisterForFastTravelPrompt` | `Function UnregisterForFastTravelPrompt(Alias akAlias) global native` | 104 |
| event | `OnFastTravelPrompt` | `Event OnFastTravelPrompt(ObjectReference asMarkerReference)` | 106 |
| function | `RegisterForFurnitureEvent` | `Function RegisterForFurnitureEvent(ReferenceAlias akRefAlias) global native` | 111 |
| function | `UnregisterForFurnitureEvent` | `Function UnregisterForFurnitureEvent(ReferenceAlias akRefAlias) global native` | 112 |
| event | `OnEnterFurniture` | `Event OnEnterFurniture(ObjectReference akRef)` | 114 |
| event | `OnExitFurniture` | `Event OnExitFurniture(ObjectReference akRef)` | 117 |
| function | `RegisterForHitEventEx` | `Function RegisterForHitEventEx(ReferenceAlias akRefAlias, Form akAggressorFilter = None, Form akSourceFilter = None, Form akProjectileFilter = None, \ int aiPowerFilter = -1, int aiSneakFilter = -1, int aiBashFilter = -1, int aiBlockFilter = -1, bool abMatch = true) global native` | 122 |
| function | `UnregisterForHitEventEx` | `Function UnregisterForHitEventEx(ReferenceAlias akRefAlias, Form akAggressorFilter = None, Form akSourceFilter = None, Form akProjectileFilter = None, \ int aiPowerFilter = -1, int aiSneakFilter = -1, int aiBashFilter = -1, int aiBlockFilter = -1, bool abMatch = true) global native` | 125 |
| function | `UnregisterForAllHitEventsEx` | `Function UnregisterForAllHitEventsEx(ReferenceAlias akRefAlias) global native` | 128 |
| event | `OnHitEx` | `Event OnHitEx(ObjectReference akAggressor, Form akSource, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked)` | 130 |
| function | `RegisterForItemCrafted` | `Function RegisterForItemCrafted(Alias akAlias) global native` | 135 |
| function | `UnregisterForItemCrafted` | `Function UnregisterForItemCrafted(Alias akAlias) global native` | 136 |
| event | `OnItemCrafted` | `Event OnItemCrafted(ObjectReference akBench, Location akLocation, Form akCreatedItem)` | 138 |
| function | `RegisterForItemHarvested` | `Function RegisterForItemHarvested(Alias akAlias) global native` | 143 |
| function | `UnregisterForItemHarvested` | `Function UnregisterForItemHarvested(Alias akAlias) global native` | 144 |
| event | `OnItemHarvested` | `Event OnItemHarvested(Form akProduce)` | 146 |
| function | `RegisterForLevelIncrease` | `Function RegisterForLevelIncrease(Alias akAlias) global native` | 151 |
| function | `UnregisterForLevelIncrease` | `Function UnregisterForLevelIncrease(Alias akAlias) global native` | 152 |
| event | `OnLevelIncrease` | `Event OnLevelIncrease(int aiLevel)` | 154 |
| function | `RegisterForLocationDiscovery` | `Function RegisterForLocationDiscovery(Alias akAlias) global native` | 159 |
| function | `UnregisterForLocationDiscovery` | `Function UnregisterForLocationDiscovery(Alias akAlias) global native` | 160 |
| event | `OnLocationDiscovery` | `Event OnLocationDiscovery(String asRegionName, String asWorldspaceName)` | 162 |
| function | `RegisterForObjectGrab` | `Function RegisterForObjectGrab(Alias akAlias) global native` | 167 |
| function | `UnregisterForObjectGrab` | `Function UnregisterForObjectGrab(Alias akAlias) global native` | 168 |
| event | `OnObjectGrab` | `Event OnObjectGrab(ObjectReference akObjectRef)` | 170 |
| event | `OnObjectRelease` | `Event OnObjectRelease(ObjectReference akObjectRef)` | 173 |
| function | `RegisterForObjectLoaded` | `Function RegisterForObjectLoaded(Alias akAlias, int formType) global native` | 178 |
| function | `UnregisterForObjectLoaded` | `Function UnregisterForObjectLoaded(Alias akAlias, int formType) global native` | 179 |
| function | `UnregisterForAllObjectsLoaded` | `Function UnregisterForAllObjectsLoaded(Alias akAlias) global native` | 180 |
| event | `OnObjectLoaded` | `Event OnObjectLoaded(ObjectReference akRef, int aiFormType)` | 182 |
| event | `OnObjectUnloaded` | `Event OnObjectUnloaded(ObjectReference akRef, int aiFormType)` | 185 |
| function | `RegisterForObjectPoisoned` | `Function RegisterForObjectPoisoned(Alias akAlias) global native` | 190 |
| function | `UnregisterForObjectPoisoned` | `Function UnregisterForObjectPoisoned(Alias akAlias) global native` | 191 |
| event | `OnObjectPoisoned` | `Event OnObjectPoisoned(Form akObject, Potion akPoison, int aiDose)` | 193 |
| function | `RegisterForQuest` | `Function RegisterForQuest(Alias akAlias, Quest akQuest) global native` | 198 |
| function | `UnregisterForQuest` | `Function UnregisterForQuest(Alias akAlias, Quest akQuest) global native` | 199 |
| function | `UnregisterForAllQuests` | `Function UnregisterForAllQuests(Alias akAlias) global native` | 200 |
| event | `OnQuestStart` | `Event OnQuestStart(Quest akQuest)` | 202 |
| event | `OnQuestStop` | `Event OnQuestStop(Quest akQuest)` | 205 |
| function | `RegisterForQuestStage` | `Function RegisterForQuestStage(Alias akAlias, Quest akQuest) global native` | 210 |
| function | `UnregisterForQuestStage` | `Function UnregisterForQuestStage(Alias akAlias, Quest akQuest) global native` | 211 |
| function | `UnregisterForAllQuestStages` | `Function UnregisterForAllQuestStages(Alias akAlias) global native` | 212 |
| event | `OnQuestStageChange` | `Event OnQuestStageChange(Quest akQuest, Int aiNewStage)` | 214 |
| function | `RegisterForShoutAttack` | `Function RegisterForShoutAttack(Alias akAlias) global native` | 219 |
| function | `UnregisterForShoutAttack` | `Function UnregisterForShoutAttack(Alias akAlias) global native` | 220 |
| event | `OnShoutAttack` | `Event OnShoutAttack(Shout akShout)` | 222 |
| function | `RegisterForSkillIncrease` | `Function RegisterForSkillIncrease(Alias akAlias) global native` | 227 |
| function | `UnregisterForSkillIncrease` | `Function UnregisterForSkillIncrease(Alias akAlias) global native` | 228 |
| event | `OnSkillIncrease` | `Event OnSkillIncrease(Int aiSkill)` | 230 |
| function | `RegisterForSoulTrapped` | `Function RegisterForSoulTrapped(Alias akAlias) global native` | 235 |
| function | `UnregisterForSoulTrapped` | `Function UnregisterForSoulTrapped(Alias akAlias) global native` | 236 |
| event | `OnSoulTrapped` | `Event OnSoulTrapped(Actor akVictim, Actor akKiller)` | 238 |
| function | `RegisterForSpellLearned` | `Function RegisterForSpellLearned(Alias akAlias) global native` | 243 |
| function | `UnregisterForSpellLearned` | `Function UnregisterForSpellLearned(Alias akAlias) global native` | 244 |
| event | `OnSpellLearned` | `Event OnSpellLearned(Spell akSpell)` | 246 |
| function | `RegisterForWeatherChange` | `Function RegisterForWeatherChange(Alias akAlias) global native` | 251 |
| function | `UnregisterForWeatherChange` | `Function UnregisterForWeatherChange(Alias akAlias) global native` | 252 |
| event | `OnWeatherChange` | `Event OnWeatherChange(Weather akOldWeather, Weather akNewWeather)` | 254 |
| function | `RegisterForMagicEffectApplyEx` | `Function RegisterForMagicEffectApplyEx(ReferenceAlias akRefAlias, Form akEffectFilter, bool abMatch) global native` | 259 |
| function | `UnregisterForMagicEffectApplyEx` | `Function UnregisterForMagicEffectApplyEx(ReferenceAlias akRefAlias, Form akEffectFilter, bool abMatch) global native` | 260 |
| function | `UnregisterForAllMagicEffectApplyEx` | `Function UnregisterForAllMagicEffectApplyEx(ReferenceAlias akRefAlias) global native` | 261 |
| event | `OnMagicEffectApplyEx` | `Event OnMagicEffectApplyEx(ObjectReference akCaster, MagicEffect akEffect, Form akSource, bool abApplied)` | 263 |
| function | `RegisterForWeaponHit` | `Function RegisterForWeaponHit(ReferenceAlias akRefAlias) global native` | 268 |
| function | `UnregisterForWeaponHit` | `Function UnregisterForWeaponHit(ReferenceAlias akRefAlias) global native` | 269 |
| event | `OnWeaponHit` | `Event OnWeaponHit(ObjectReference akTarget, Form akSource, Projectile akProjectile, Int aiHitFlagMask)` | 271 |
| function | `RegisterForMagicHit` | `Function RegisterForMagicHit(ReferenceAlias akRefAlias) global native` | 276 |
| function | `UnregisterForMagicHit` | `Function UnregisterForMagicHit(ReferenceAlias akRefAlias) global native` | 277 |
| event | `OnMagicHit` | `Event OnMagicHit(ObjectReference akTarget, Form akSource, Projectile akProjectile)` | 279 |
| function | `RegisterForProjectileHit` | `Function RegisterForProjectileHit(ReferenceAlias akRefAlias) global native` | 284 |
| function | `UnregisterForProjectileHit` | `Function UnregisterForProjectileHit(ReferenceAlias akRefAlias) global native` | 285 |
| event | `OnProjectileHit` | `Event OnProjectileHit(ObjectReference akTarget, Form akSource, Projectile akProjectile)` | 287 |

## PO3_Events_Form

Source: `Papyrus/Source/scripts/PO3_Events_Form.psc` · blob `ec1cbca8a226177d72c70a22642e4f1080275e17`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `RegisterForActorFallLongDistance` | `Function RegisterForActorFallLongDistance(Form akForm) global native` | 9 |
| function | `UnregisterForActorFallLongDistance` | `Function UnregisterForActorFallLongDistance(Form akForm) global native` | 10 |
| event | `OnActorFallLongDistance` | `Event OnActorFallLongDistance(Actor akTarget, float afFallDistance, float afFallDamage)` | 12 |
| function | `RegisterForActorKilled` | `Function RegisterForActorKilled(Form akForm) global native` | 17 |
| function | `UnregisterForActorKilled` | `Function UnregisterForActorKilled(Form akForm) global native` | 18 |
| event | `OnActorKilled` | `Event OnActorKilled(Actor akVictim, Actor akKiller)` | 20 |
| function | `RegisterForActorReanimateStart` | `Function RegisterForActorReanimateStart(Form akForm) global native` | 26 |
| function | `UnregisterForActorReanimateStart` | `Function UnregisterForActorReanimateStart(Form akForm) global native` | 27 |
| function | `RegisterForActorReanimateStop` | `Function RegisterForActorReanimateStop(Form akForm) global native` | 29 |
| function | `UnregisterForActorReanimateStop` | `Function UnregisterForActorReanimateStop(Form akForm) global native` | 30 |
| event | `OnActorReanimateStart` | `Event OnActorReanimateStart(Actor akTarget, Actor akCaster)` | 32 |
| event | `OnActorReanimateStop` | `Event OnActorReanimateStop(Actor akTarget, Actor akCaster)` | 35 |
| function | `RegisterForActorResurrected` | `Function RegisterForActorResurrected(Form akForm) global native` | 41 |
| function | `UnregisterForActorResurrected` | `Function UnregisterForActorResurrected(Form akForm) global native` | 42 |
| event | `OnActorResurrected` | `Event OnActorResurrected(Actor akTarget, bool abResetInventory)` | 44 |
| function | `RegisterForBookRead` | `Function RegisterForBookRead(Form akForm) global native` | 49 |
| function | `UnregisterForBookRead` | `Function UnregisterForBookRead(Form akForm) global native` | 50 |
| event | `OnBookRead` | `Event OnBookRead(Book akBook)` | 52 |
| function | `RegisterForCellFullyLoaded` | `Function RegisterForCellFullyLoaded(Form akForm) global native` | 57 |
| function | `UnregisterForCellFullyLoaded` | `Function UnregisterForCellFullyLoaded(Form akForm) global native` | 58 |
| event | `OnCellFullyLoaded` | `Event OnCellFullyLoaded(Cell akCell)` | 60 |
| function | `RegisterForCriticalHit` | `Function RegisterForCriticalHit(Form akForm) global native` | 65 |
| function | `UnregisterForCriticalHit` | `Function UnregisterForCriticalHit(Form akForm) global native` | 66 |
| event | `OnCriticalHit` | `Event OnCriticalHit(Actor akAggressor, Weapon akWeapon, bool abSneakHit)` | 68 |
| function | `RegisterForDisarmed` | `Function RegisterForDisarmed(Form akForm) global native` | 73 |
| function | `UnregisterForDisarmed` | `Function UnregisterForDisarmed(Form akForm) global native` | 74 |
| event | `OnDisarmed` | `Event OnDisarmed(Actor akSource, Weapon akTarget)` | 76 |
| function | `RegisterForDragonSoulGained` | `Function RegisterForDragonSoulGained(Form akForm) global native` | 81 |
| function | `UnregisterForDragonSoulGained` | `Function UnregisterForDragonSoulGained(Form akForm) global native` | 82 |
| event | `OnDragonSoulGained` | `Event OnDragonSoulGained(float afSouls)` | 84 |
| function | `RegisterForOnPlayerFastTravelEnd` | `Function RegisterForOnPlayerFastTravelEnd(Form akForm) global native` | 89 |
| function | `UnregisterForOnPlayerFastTravelEnd` | `Function UnregisterForOnPlayerFastTravelEnd(Form akForm) global native` | 90 |
| event | `OnPlayerFastTravelEnd` | `Event OnPlayerFastTravelEnd(float afTravelGameTimeHours)` | 92 |
| function | `RegisterForFastTravelConfirmed` | `Function RegisterForFastTravelConfirmed(Form akForm) global native` | 97 |
| function | `UnregisterForFastTravelConfirmed` | `Function UnregisterForFastTravelConfirmed(Form akForm) global native` | 98 |
| event | `OnFastTravelConfirmed` | `Event OnFastTravelConfirmed(ObjectReference asMarkerReference)` | 100 |
| function | `RegisterForFastTravelPrompt` | `Function RegisterForFastTravelPrompt(Form akForm) global native` | 105 |
| function | `UnregisterForFastTravelPrompt` | `Function UnregisterForFastTravelPrompt(Form akForm) global native` | 106 |
| event | `OnFastTravelPrompt` | `Event OnFastTravelPrompt(ObjectReference asMarkerReference)` | 108 |
| function | `RegisterForFurnitureEvent` | `Function RegisterForFurnitureEvent(Form akForm) global native` | 114 |
| function | `UnregisterForFurnitureEvent` | `Function UnregisterForFurnitureEvent(Form akForm) global native` | 115 |
| event | `OnEnterFurniture` | `Event OnEnterFurniture(ObjectReference akRef)` | 117 |
| event | `OnExitFurniture` | `Event OnExitFurniture(ObjectReference akRef)` | 120 |
| function | `RegisterForHitEventEx` | `Function RegisterForHitEventEx(Form akForm, Form akAggressorFilter = None, Form akSourceFilter = None, Form akProjectileFilter = None, \ int aiPowerFilter = -1, int aiSneakFilter = -1, int aiBashFilter = -1, int aiBlockFilter = -1, bool abMatch = true) global native` | 126 |
| function | `UnregisterForHitEventEx` | `Function UnregisterForHitEventEx(Form akForm, Form akAggressorFilter = None, Form akSourceFilter = None, Form akProjectileFilter = None, \ int aiPowerFilter = -1, int aiSneakFilter = -1, int aiBashFilter = -1, int aiBlockFilter = -1, bool abMatch = true) global native` | 129 |
| function | `UnregisterForAllHitEventsEx` | `Function UnregisterForAllHitEventsEx(Form akForm) global native` | 132 |
| event | `OnHitEx` | `Event OnHitEx(ObjectReference akAggressor, Form akSource, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked)` | 134 |
| function | `RegisterForItemCrafted` | `Function RegisterForItemCrafted(Form akForm) global native` | 139 |
| function | `UnregisterForItemCrafted` | `Function UnregisterForItemCrafted(Form akForm) global native` | 140 |
| event | `OnItemCrafted` | `Event OnItemCrafted(ObjectReference akBench, Location akLocation, Form akCreatedItem)` | 142 |
| function | `RegisterForItemHarvested` | `Function RegisterForItemHarvested(Form akForm) global native` | 147 |
| function | `UnregisterForItemHarvested` | `Function UnregisterForItemHarvested(Form akForm) global native` | 148 |
| event | `OnItemHarvested` | `Event OnItemHarvested(Form akProduce)` | 150 |
| function | `RegisterForLevelIncrease` | `Function RegisterForLevelIncrease(Form akForm) global native` | 155 |
| function | `UnregisterForLevelIncrease` | `Function UnregisterForLevelIncrease(Form akForm) global native` | 156 |
| event | `OnLevelIncrease` | `Event OnLevelIncrease(int aiLevel)` | 158 |
| function | `RegisterForLocationDiscovery` | `Function RegisterForLocationDiscovery(Form akForm) global native` | 163 |
| function | `UnregisterForLocationDiscovery` | `Function UnregisterForLocationDiscovery(Form akForm) global native` | 164 |
| event | `OnLocationDiscovery` | `Event OnLocationDiscovery(String asRegionName, String asWorldspaceName)` | 166 |
| function | `RegisterForObjectGrab` | `Function RegisterForObjectGrab(Form akForm) global native` | 171 |
| function | `UnregisterForObjectGrab` | `Function UnregisterForObjectGrab(Form akForm) global native` | 172 |
| event | `OnObjectGrab` | `Event OnObjectGrab(ObjectReference akObjectRef)` | 174 |
| event | `OnObjectRelease` | `Event OnObjectRelease(ObjectReference akObjectRef)` | 177 |
| function | `RegisterForObjectLoaded` | `Function RegisterForObjectLoaded(Form akForm, int formType) global native` | 182 |
| function | `UnregisterForObjectLoaded` | `Function UnregisterForObjectLoaded(Form akForm, int formType) global native` | 183 |
| function | `UnregisterForAllObjectsLoaded` | `Function UnregisterForAllObjectsLoaded(Form akForm) global native` | 184 |
| event | `OnObjectLoaded` | `Event OnObjectLoaded(ObjectReference akRef, int aiFormType)` | 186 |
| event | `OnObjectUnloaded` | `Event OnObjectUnloaded(ObjectReference akRef, int aiFormType)` | 189 |
| function | `RegisterForObjectPoisoned` | `Function RegisterForObjectPoisoned(Form akForm) global native` | 194 |
| function | `UnregisterForObjectPoisoned` | `Function UnregisterForObjectPoisoned(Form akForm) global native` | 195 |
| event | `OnObjectPoisoned` | `Event OnObjectPoisoned(Form akObject, Potion akPoison, int aiDose)` | 197 |
| function | `RegisterForQuest` | `Function RegisterForQuest(Form akForm, Quest akQuest) global native` | 202 |
| function | `UnregisterForQuest` | `Function UnregisterForQuest(Form akForm, Quest akQuest) global native` | 203 |
| function | `UnregisterForAllQuests` | `Function UnregisterForAllQuests(Form akForm) global native` | 204 |
| event | `OnQuestStart` | `Event OnQuestStart(Quest akQuest)` | 206 |
| event | `OnQuestStop` | `Event OnQuestStop(Quest akQuest)` | 209 |
| function | `RegisterForQuestStage` | `Function RegisterForQuestStage(Form akForm, Quest akQuest) global native` | 214 |
| function | `UnregisterForQuestStage` | `Function UnregisterForQuestStage(Form akForm, Quest akQuest) global native` | 215 |
| function | `UnregisterForAllQuestStages` | `Function UnregisterForAllQuestStages(Form akForm) global native` | 216 |
| event | `OnQuestStageChange` | `Event OnQuestStageChange(Quest akQuest, Int aiNewStage)` | 218 |
| function | `RegisterForShoutAttack` | `Function RegisterForShoutAttack(Form akForm) global native` | 223 |
| function | `UnregisterForShoutAttack` | `Function UnregisterForShoutAttack(Form akForm) global native` | 224 |
| event | `OnPlayerShoutAttack` | `Event OnPlayerShoutAttack(Shout akShout)` | 226 |
| function | `RegisterForSkillIncrease` | `Function RegisterForSkillIncrease(Form akForm) global native` | 231 |
| function | `UnregisterForSkillIncrease` | `Function UnregisterForSkillIncrease(Form akForm) global native` | 232 |
| event | `OnSkillIncrease` | `Event OnSkillIncrease(Int aiSkill)` | 234 |
| function | `RegisterForSoulTrapped` | `Function RegisterForSoulTrapped(Form akForm) global native` | 239 |
| function | `UnregisterForSoulTrapped` | `Function UnregisterForSoulTrapped(Form akForm) global native` | 240 |
| event | `OnSoulTrapped` | `Event OnSoulTrapped(Actor akVictim, Actor akKiller)` | 242 |
| function | `RegisterForSpellLearned` | `Function RegisterForSpellLearned(Form akForm) global native` | 247 |
| function | `UnregisterForSpellLearned` | `Function UnregisterForSpellLearned(Form akForm) global native` | 248 |
| event | `OnSpellLearned` | `Event OnSpellLearned(Spell akSpell)` | 250 |
| function | `RegisterForWeatherChange` | `Function RegisterForWeatherChange(Form akForm) global native` | 255 |
| function | `UnregisterForWeatherChange` | `Function UnregisterForWeatherChange(Form akForm) global native` | 256 |
| event | `OnWeatherChange` | `Event OnWeatherChange(Weather akOldWeather, Weather akNewWeather)` | 258 |
| function | `RegisterForMagicEffectApplyEx` | `Function RegisterForMagicEffectApplyEx(Form akForm, Form akEffectFilter, bool abMatch) global native` | 264 |
| function | `UnregisterForMagicEffectApplyEx` | `Function UnregisterForMagicEffectApplyEx(Form akForm, Form akEffectFilter, bool abMatch) global native` | 265 |
| function | `UnregisterForAllMagicEffectApplyEx` | `Function UnregisterForAllMagicEffectApplyEx(Form akForm) global native` | 266 |
| event | `OnMagicEffectApplyEx` | `Event OnMagicEffectApplyEx(ObjectReference akCaster, MagicEffect akEffect, Form akSource, bool abApplied)` | 268 |
| function | `RegisterForWeaponHit` | `Function RegisterForWeaponHit(Form akForm) global native` | 274 |
| function | `UnregisterForWeaponHit` | `Function UnregisterForWeaponHit(Form akForm) global native` | 275 |
| event | `OnWeaponHit` | `Event OnWeaponHit(ObjectReference akTarget, Form akSource, Projectile akProjectile, Int aiHitFlagMask)` | 277 |
| function | `RegisterForMagicHit` | `Function RegisterForMagicHit(Form akForm) global native` | 283 |
| function | `UnregisterForMagicHit` | `Function UnregisterForMagicHit(Form akForm) global native` | 284 |
| event | `OnMagicHit` | `Event OnMagicHit(ObjectReference akTarget, Form akSource, Projectile akProjectile)` | 286 |
| function | `RegisterForProjectileHit` | `Function RegisterForProjectileHit(Form akForm) global native` | 292 |
| function | `UnregisterForProjectileHit` | `Function UnregisterForProjectileHit(Form akForm) global native` | 293 |
| event | `OnProjectileHit` | `Event OnProjectileHit(ObjectReference akTarget, Form akSource, Projectile akProjectile)` | 295 |

## PO3_SKSEFunctions

Source: `Papyrus/Source/scripts/PO3_SKSEFunctions.psc` · blob `87fcdd7c399801c92449c59ddb46090b2cc93214`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetScriptsAttachedToActiveEffect` | `string[] Function GetScriptsAttachedToActiveEffect(ActiveMagicEffect akActiveEffect) global native` | 8 |
| function | `IsScriptAttachedToActiveEffect` | `Bool Function IsScriptAttachedToActiveEffect(ActiveMagicEffect akActiveEffect, string asScriptName) global native` | 10 |
| function | `GetActiveEffectSpell` | `Form Function GetActiveEffectSpell(ActiveMagicEffect akActiveEffect) global native` | 12 |
| function | `GetActiveEffects` | `MagicEffect[] Function GetActiveEffects(Actor akActor, bool abShowInactive = false) global native` | 17 |
| function | `GetActorAlpha` | `float Function GetActorAlpha(Actor akActor) global native` | 19 |
| function | `GetActorKnockState` | `int Function GetActorKnockState(Actor akActor) global native` | 21 |
| function | `GetActorRefraction` | `float Function GetActorRefraction(Actor akActor) global native` | 23 |
| function | `GetActorState` | `int Function GetActorState(Actor akActor) global native` | 25 |
| function | `GetActorSoulSize` | `int Function GetActorSoulSize(Actor akActor) global native` | 27 |
| function | `GetActorValueModifier` | `float Function GetActorValueModifier(Actor akActor, int aiModifier, string asActorValue) global native` | 29 |
| function | `GetAllActorPlayableSpells` | `Spell[] Function GetAllActorPlayableSpells(Actor akActor) global native` | 31 |
| function | `GetCriticalStage` | `int Function GetCriticalStage(Actor akActor) global native` | 33 |
| function | `GetCombatAllies` | `Actor[] Function GetCombatAllies(Actor akActor) global native` | 35 |
| function | `GetCombatTargets` | `Actor[] Function GetCombatTargets(Actor akActor) global native` | 37 |
| function | `GetCommandedActors` | `Actor[] Function GetCommandedActors(Actor akActor) global native` | 39 |
| function | `GetCommandingActor` | `Actor Function GetCommandingActor(Actor akActor) global native` | 41 |
| function | `GetEditorLocationX` | `float Function GetEditorLocationX(Actor akActor) global native` | 43 |
| function | `GetEditorLocationY` | `float Function GetEditorLocationY(Actor akActor) global native` | 45 |
| function | `GetEditorLocationZ` | `float Function GetEditorLocationZ(Actor akActor) global native` | 47 |
| function | `GetEditorLocationAngle` | `float Function GetEditorLocationAngle(Actor akActor) global native` | 49 |
| function | `GetEquippedAmmo` | `Ammo Function GetEquippedAmmo(Actor akActor) global native` | 51 |
| function | `GetEquippedAmmoEnchantment` | `Enchantment Function GetEquippedAmmoEnchantment(Actor akActor) global native` | 53 |
| function | `GetEquippedWeaponIsPoisoned` | `Bool Function GetEquippedWeaponIsPoisoned(Actor akActor, bool abLeftHand) global native` | 55 |
| function | `GetEquippedWeaponPoison` | `Potion Function GetEquippedWeaponPoison(Actor akActor, bool abLeftHand) global native` | 57 |
| function | `GetEquippedWeaponPoisonCount` | `int Function GetEquippedWeaponPoisonCount(Actor akActor, bool abLeftHand) global native` | 59 |
| function | `GetEquippedWeight` | `float Function GetEquippedWeight(Actor akActor) global native` | 61 |
| function | `GetHairColor` | `ColorForm Function GetHairColor(Actor akActor) global native` | 64 |
| function | `GetHairRGB` | `int[] Function GetHairRGB(Actor akActor) global native` | 66 |
| function | `GetHeadPartTextureSet` | `TextureSet Function GetHeadPartTextureSet(Actor akActor, int aiType) global native` | 68 |
| function | `GetLocalGravityActor` | `float Function GetLocalGravityActor(Actor akActor) global native` | 70 |
| function | `GetMount` | `Actor Function GetMount(Actor akActor) global native` | 72 |
| function | `GetObjectUnderFeet` | `ObjectReference Function GetObjectUnderFeet(Actor akActor) global native` | 74 |
| function | `GetOffersServices` | `Bool Function GetOffersServices(Actor akActor) global native` | 76 |
| function | `GetRider` | `Actor Function GetRider(Actor akActor) global native` | 78 |
| function | `GetRunningPackage` | `Package Function GetRunningPackage(Actor akActor) global native` | 80 |
| function | `GetSkinColor` | `ColorForm Function GetSkinColor(Actor akActor) global native` | 83 |
| function | `GetSkinRGB` | `int[] Function GetSkinRGB(Actor akActor) global native` | 85 |
| function | `GetTimeDead` | `float Function GetTimeDead(Actor akActor) global native` | 87 |
| function | `GetTimeOfDeath` | `float Function GetTimeOfDeath(Actor akActor) global native` | 89 |
| function | `GetVendorFaction` | `Faction Function GetVendorFaction(Actor akActor) global native` | 91 |
| function | `HasActiveMagicEffect` | `Bool Function HasActiveMagicEffect(Actor akActor, MagicEffect akEffect) global native` | 93 |
| function | `HasActiveSpell` | `Bool Function HasActiveSpell(Actor akActor, Spell akSpell) global native` | 95 |
| function | `HasDeferredKill` | `Bool Function HasDeferredKill(Actor akActor) global native` | 97 |
| function | `HasMagicEffectWithArchetype` | `Bool Function HasMagicEffectWithArchetype(Actor akActor, string asArchetype) global native` | 99 |
| function | `HasSkin` | `Bool Function HasSkin(Actor akActor, Armor akArmorToCheck) global native` | 101 |
| function | `IsActorInWater` | `Bool Function IsActorInWater(Actor akActor) global native` | 103 |
| function | `IsActorUnderwater` | `Bool Function IsActorUnderwater(Actor akActor) global native` | 105 |
| function | `IsLimbGone` | `Bool Function IsLimbGone(Actor akActor, int aiLimb) global native` | 107 |
| function | `IsPowerAttacking` | `Bool Function IsPowerAttacking(Actor akActor) global native` | 109 |
| function | `IsQuadruped` | `Bool Function IsQuadruped(Actor akActor) global native` | 111 |
| function | `IsSoulTrapped` | `Bool Function IsSoulTrapped(Actor akActor) global native` | 113 |
| function | `ApplyPoisonToEquippedWeapon` | `Bool Function ApplyPoisonToEquippedWeapon(Actor akActor, Potion akPoison, int aiCount, bool abLeftHand) global native` | 115 |
| function | `AddAllEquippedItemsToArray` | `Form[] Function AddAllEquippedItemsToArray(Actor akActor) global native` | 117 |
| function | `AddAllEquippedItemsBySlotToArray` | `Form[] Function AddAllEquippedItemsBySlotToArray(Actor akActor, int[] aiSlots) global native` | 119 |
| function | `AddBasePerk` | `Bool Function AddBasePerk(Actor akActor, Perk akPerk) global native` | 121 |
| function | `AddBaseSpell` | `Bool Function AddBaseSpell(Actor akActor, Spell akSpell) global native` | 123 |
| function | `BlendColorWithSkinTone` | `Function BlendColorWithSkinTone(Actor akActor, ColorForm akColor, int aiBlendMode, bool abAutoLuminance, float afOpacity) global native` | 125 |
| function | `DamageActorHealth` | `Bool Function DamageActorHealth(Actor akActor, float afHealthDamage, Actor akSource) global native` | 127 |
| function | `DecapitateActor` | `Function DecapitateActor(Actor akActor) global native` | 129 |
| function | `FreezeActor` | `Function FreezeActor(Actor akActor, int type, bool abFreeze) global native` | 131 |
| function | `KillNoWait` | `Function KillNoWait(Actor akActor) global native` | 133 |
| function | `LaunchArrow` | `Function LaunchArrow(Actor akActor, Ammo akAmmo, Weapon akWeapon, string asNodeName = "", int aiSource = -1, ObjectReference akTarget = None, Potion akPoison = None) global native` | 135 |
| function | `LaunchSpell` | `Function LaunchSpell(Actor akActor, Spell akSpell, int aiSource) global native` | 137 |
| function | `MixColorWithSkinTone` | `Function MixColorWithSkinTone(Actor akActor, ColorForm akColor, bool abManualMode, float afPercentage) global native` | 140 |
| function | `RemoveAddedSpells` | `Function RemoveAddedSpells(Actor akActor, string modName, Keyword[] keywords, bool abMatchAll) global native` | 142 |
| function | `RemoveArmorOfType` | `Function RemoveArmorOfType(Actor akActor, int afArmorType, int[] aiSlotsToSkip, bool abEquippedOnly) global native` | 144 |
| function | `RemoveBasePerk` | `Bool Function RemoveBasePerk(Actor akActor, Perk akPerk) global native` | 146 |
| function | `RemoveBaseSpell` | `Bool Function RemoveBaseSpell(Actor akActor, Spell akSpell) global native` | 148 |
| function | `ReplaceArmorTextureSet` | `Function ReplaceArmorTextureSet(Actor akActor, Armor akArmor, TextureSet akSourceTXST, TextureSet akTargetTXST, int aiTextureType = -1) global native` | 150 |
| function | `ReplaceFaceTextureSet` | `Function ReplaceFaceTextureSet(Actor akActor, TextureSet akMaleTXST, TextureSet akFemaleTXST, int aiTextureType = -1) global native` | 152 |
| function | `ReplaceSkinTextureSet` | `Function ReplaceSkinTextureSet(Actor akActor, TextureSet akMaleTXST, TextureSet akFemaleTXST, int aiSlotMask, int aiTextureType = -1) global native` | 154 |
| function | `ResetActor3D` | `Bool Function ResetActor3D(Actor akActor, string asFolderName) global native` | 156 |
| function | `SetActorRefraction` | `Function SetActorRefraction(Actor akActor, float afRefraction) global native` | 158 |
| function | `SetEquippedWeaponPoison` | `Bool Function SetEquippedWeaponPoison(Actor akActor, Potion akPoison, bool abLeftHand) global native` | 160 |
| function | `SetEquippedWeaponPoisonCount` | `Bool Function SetEquippedWeaponPoisonCount(Actor akActor, int aiCount, bool abLeftHand) global native` | 162 |
| function | `SetHairColor` | `Function SetHairColor(Actor akActor, ColorForm akColor) global native` | 164 |
| function | `SetHeadPartAlpha` | `Function SetHeadPartAlpha(Actor akActor, int aiPartType, float afAlpha) global native` | 166 |
| function | `SetHeadPartTextureSet` | `Function SetHeadPartTextureSet(Actor akActor, TextureSet headpartTXST, int aiType) global native` | 168 |
| function | `SetLinearVelocity` | `Function SetLinearVelocity(Actor akActor, float afX, float afY, float afZ) global native` | 170 |
| function | `SetLocalGravityActor` | `Function SetLocalGravityActor(Actor akActor, float afValue, bool abDisableGravityOnGround) global native` | 172 |
| function | `SetSkinAlpha` | `Function SetSkinAlpha(Actor akActor, float afAlpha) global native` | 174 |
| function | `SetSkinColor` | `Function SetSkinColor(Actor akActor, ColorForm akColor) global native` | 176 |
| function | `SetSoulTrapped` | `Function SetSoulTrapped(Actor akActor, bool abTrapped) global native` | 178 |
| function | `ToggleHairWigs` | `Function ToggleHairWigs(Actor akActor, bool abDisable) global native` | 180 |
| function | `UnequipAllOfType` | `Function UnequipAllOfType(Actor akActor, int afArmorType, int[] aiSlotsToSkip) global native` | 182 |
| function | `GetAssociationType` | `AssociationType Function GetAssociationType(Actorbase akBase1, Actorbase akBase2) global native` | 186 |
| function | `GetDeathItem` | `LeveledItem Function GetDeathItem(Actorbase akBase) global native` | 188 |
| function | `GetNthPerk` | `Perk Function GetNthPerk(Actorbase akBase, int aiIndex) global native` | 190 |
| function | `GetPerkCount` | `int Function GetPerkCount(Actorbase akBase) global native` | 192 |
| function | `GetRelationships` | `Actorbase[] Function GetRelationships(Actorbase akBase, AssociationType akAssocType) global native` | 194 |
| function | `SetDeathItem` | `Function SetDeathItem(Actorbase akBase, LeveledItem akLeveledItem) global native` | 196 |
| function | `GetBaseAmmoEnchantment` | `Enchantment Function GetBaseAmmoEnchantment(Ammo akAmmo) global native` | 200 |
| function | `GetScriptsAttachedToAlias` | `string[] Function GetScriptsAttachedToAlias(Alias akAlias) global native` | 204 |
| function | `IsScriptAttachedToAlias` | `Bool Function IsScriptAttachedToAlias(Alias akAlias, string asScriptName) global native` | 206 |
| function | `GetFootstepSet` | `FootstepSet Function GetFootstepSet(ArmorAddon akArma) global native` | 210 |
| function | `SetFootstepSet` | `Function SetFootstepSet(ArmorAddon akArma, FootstepSet akFootstepSet) global native` | 212 |
| function | `GetSortedActorNames` | `string[] Function GetSortedActorNames(Keyword akKeyword, string asPlural = "(s)", bool abInvertKeyword) global native` | 216 |
| function | `GetSortedNPCNames` | `string[] Function GetSortedNPCNames(ActorBase[] aiActorBases, string asPlural = "(s)") global native` | 218 |
| function | `AddActorToArray` | `Bool Function AddActorToArray(Actor akActor, Actor[] actorArray) global native` | 220 |
| function | `AddStringToArray` | `Bool Function AddStringToArray(string asString, string[] asStrings) global native` | 222 |
| function | `ArrayStringCount` | `int Function ArrayStringCount(string asString, string[] asStrings) global native` | 224 |
| function | `SortArrayString` | `string[] Function SortArrayString(string[] asStrings) global native` | 226 |
| function | `ClearBookCantBeTakenFlag` | `Function ClearBookCantBeTakenFlag(Book akBook) global native` | 230 |
| function | `ClearReadFlag` | `Function ClearReadFlag(Book akBook) global native` | 232 |
| function | `SetBookCantBeTakenFlag` | `Function SetBookCantBeTakenFlag(Book akBook) global native` | 234 |
| function | `SetReadFlag` | `Function SetReadFlag(Book akBook) global native` | 236 |
| function | `GetCellNorthRotation` | `float Function GetCellNorthRotation(Cell akCell) global native` | 240 |
| function | `GetLightingTemplate` | `LightingTemplate Function GetLightingTemplate(Cell akCell) global native` | 242 |
| function | `SetLightingTemplate` | `Function SetLightingTemplate(Cell akCell, LightingTemplate akLightingTemplate) global native` | 244 |
| function | `SetCellNorthRotation` | `Function SetCellNorthRotation(Cell akCell, float afAngle) global native` | 246 |
| function | `GivePlayerSpellBook` | `Function GivePlayerSpellBook() global native` | 250 |
| function | `DumpAnimationVariables` | `Function DumpAnimationVariables(Actor akActor, string asAnimationVarPrefix) global native` | 252 |
| function | `CanActorBeDetected` | `int Function CanActorBeDetected(Actor akActor) global native` | 256 |
| function | `CanActorDetect` | `int Function CanActorDetect(Actor akActor) global native` | 258 |
| function | `IsDetectedByAnyone` | `Bool Function IsDetectedByAnyone(Actor akActor) global native` | 260 |
| function | `ForceActorDetection` | `Function ForceActorDetection(Actor akActor) global native` | 262 |
| function | `ForceActorDetecting` | `Function ForceActorDetecting(Actor akActor) global native` | 264 |
| function | `PreventActorDetection` | `Function PreventActorDetection(Actor akActor) global native` | 266 |
| function | `PreventActorDetecting` | `Function PreventActorDetecting(Actor akActor) global native` | 268 |
| function | `ResetActorDetection` | `Function ResetActorDetection(Actor akActor) global native` | 270 |
| function | `ResetActorDetecting` | `Function ResetActorDetecting(Actor akActor) global native` | 272 |
| function | `GetAddonModels` | `Debris Function GetAddonModels(EffectShader akEffectShader) global native` | 276 |
| function | `GetEffectShaderTotalCount` | `int Function GetEffectShaderTotalCount(EffectShader akEffectShader, bool abActive) global native` | 278 |
| function | `IsEffectShaderFlagSet` | `Bool Function IsEffectShaderFlagSet(EffectShader akEffectShader, int aiFlag) global native` | 280 |
| function | `GetMembraneFillTexture` | `string Function GetMembraneFillTexture(EffectShader akEffectShader) global native` | 282 |
| function | `GetMembraneHolesTexture` | `string Function GetMembraneHolesTexture(EffectShader akEffectShader) global native` | 284 |
| function | `GetMembranePaletteTexture` | `string Function GetMembranePaletteTexture(EffectShader akEffectShader) global native` | 286 |
| function | `GetParticleFullCount` | `float Function GetParticleFullCount(EffectShader akEffectShader) global native` | 288 |
| function | `GetParticlePaletteTexture` | `string Function GetParticlePaletteTexture(EffectShader akEffectShader) global native` | 290 |
| function | `GetParticleShaderTexture` | `string Function GetParticleShaderTexture(EffectShader akEffectShader) global native` | 292 |
| function | `GetParticlePersistentCount` | `float Function GetParticlePersistentCount(EffectShader akEffectShader) global native` | 294 |
| function | `ClearEffectShaderFlag` | `Function ClearEffectShaderFlag(EffectShader akEffectShader, int aiFlag) global native` | 296 |
| function | `SetAddonModels` | `Function SetAddonModels(EffectShader akEffectShader, Debris akDebris) global native` | 298 |
| function | `SetEffectShaderFlag` | `Function SetEffectShaderFlag(EffectShader akEffectShader, int aiFlag) global native` | 300 |
| function | `SetMembraneColorKeyData` | `Function SetMembraneColorKeyData(EffectShader akEffectShader, int aiColorKey, int[] aiRGB, float afAlpha, float afTime) global native` | 302 |
| function | `SetMembraneFillTexture` | `Function SetMembraneFillTexture(EffectShader akEffectShader, string asTextureName) global native` | 304 |
| function | `SetMembraneHolesTexture` | `Function SetMembraneHolesTexture(EffectShader akEffectShader, string asTextureName) global native` | 306 |
| function | `SetMembranePaletteTexture` | `Function SetMembranePaletteTexture(EffectShader akEffectShader, string asTextureName) global native` | 308 |
| function | `SetParticleColorKeyData` | `Function SetParticleColorKeyData(EffectShader akEffectShader, int aiColorKey, int[] aiRGB, float afAlpha, float afTime) global native` | 310 |
| function | `SetParticleFullCount` | `Function SetParticleFullCount(EffectShader akEffectShader, float afParticleCount) global native` | 312 |
| function | `SetParticlePaletteTexture` | `Function SetParticlePaletteTexture(EffectShader akEffectShader, string asTextureName) global native` | 314 |
| function | `SetParticlePersistentCount` | `Function SetParticlePersistentCount(EffectShader akEffectShader, float afParticleCount) global native` | 316 |
| function | `SetParticleShaderTexture` | `Function SetParticleShaderTexture(EffectShader akEffectShader, string asTextureName) global native` | 318 |
| function | `GetEnchantmentType` | `int Function GetEnchantmentType(Enchantment akEnchantment) global native` | 323 |
| function | `AddMagicEffectToEnchantment` | `Function AddMagicEffectToEnchantment(Enchantment akEnchantment, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0, string[] asConditionList) global native` | 325 |
| function | `AddEffectItemToEnchantment` | `Function AddEffectItemToEnchantment(Enchantment akEnchantment, Enchantment akEnchantmentToCopyFrom, int aiIndex, float afCost = -1.0) global native` | 327 |
| function | `RemoveMagicEffectFromEnchantment` | `Function RemoveMagicEffectFromEnchantment(Enchantment akEnchantment, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0) global native` | 329 |
| function | `RemoveEffectItemFromEnchantment` | `Function RemoveEffectItemFromEnchantment(Enchantment akEnchantment, Enchantment akEnchantmentToMatchFrom, int aiIndex) global native` | 331 |
| function | `SetEnchantmentMagicEffect` | `Function SetEnchantmentMagicEffect(Enchantment akEnchantment, MagicEffect akMagicEffect, int aiIndex) global native` | 333 |
| function | `GetVendorFactionContainer` | `ObjectReference Function GetVendorFactionContainer(Faction akVendorFaction) global native` | 338 |
| function | `GetAllActorsInFaction` | `Actor[] Function GetAllActorsInFaction(Faction akFaction) global native` | 340 |
| function | `SetFastTravelDisabled` | `Bool Function SetFastTravelDisabled(bool abDisable) global native` | 344 |
| function | `SetFastTravelTargetFormID` | `Bool Function SetFastTravelTargetFormID(int aiDestinationFormID) global native` | 346 |
| function | `SetFastTravelTargetRef` | `Bool Function SetFastTravelTargetRef(ObjectReference akDestination) global native` | 348 |
| function | `SetFastTravelTargetString` | `Bool Function SetFastTravelTargetString(string asDestination) global native` | 350 |
| function | `SetFastTravelWaitTimeout` | `float Function SetFastTravelWaitTimeout(float afTimeout) global native` | 352 |
| function | `EvaluateConditionList` | `Bool Function EvaluateConditionList(Form akForm, ObjectReference akActionRef, ObjectReference akTargetRef) global native` | 356 |
| function | `ClearRecordFlag` | `Function ClearRecordFlag(Form akForm, int aiFlag) global native` | 358 |
| function | `GetConditionList` | `string[] Function GetConditionList(Form akForm, int aiIndex = 0) global native` | 360 |
| function | `GetDescription` | `string Function GetDescription(Form akForm) global native` | 362 |
| function | `GetFormEditorID` | `string Function GetFormEditorID(Form akForm) global native` | 364 |
| function | `GetFormModName` | `string Function GetFormModName(Form akForm, bool abLastModified) global native` | 366 |
| function | `GetScriptsAttachedToForm` | `string[] Function GetScriptsAttachedToForm(Form akForm) global native` | 368 |
| function | `IsFormInMod` | `Bool Function IsFormInMod(Form akForm, string asModName) global native` | 370 |
| function | `IsGeneratedForm` | `Bool Function IsGeneratedForm(Form akForm) global native` | 372 |
| function | `IsRecordFlagSet` | `Bool Function IsRecordFlagSet(Form akForm, int aiFlag) global native` | 374 |
| function | `IsScriptAttachedToForm` | `Bool Function IsScriptAttachedToForm(Form akForm, string asScriptName) global native` | 376 |
| function | `SetRecordFlag` | `Function SetRecordFlag(Form akForm, int aiFlag) global native` | 378 |
| function | `AddKeywordToForm` | `Function AddKeywordToForm(Form akForm, Keyword akKeyword) global native` | 380 |
| function | `MarkItemAsFavorite` | `Function MarkItemAsFavorite(Form akForm) global native` | 382 |
| function | `RemoveConditionList` | `Function RemoveConditionList(Form akForm, int aiIndex, string[] asConditionList) global native` | 384 |
| function | `ReplaceKeywordOnForm` | `Function ReplaceKeywordOnForm(Form akForm, Keyword akKeywordAdd, Keyword akKeywordRemove) global native` | 386 |
| function | `RemoveKeywordOnForm` | `Bool Function RemoveKeywordOnForm(Form akForm, Keyword akKeyword) global native` | 388 |
| function | `SetConditionList` | `Function SetConditionList(Form akForm, int aiIndex, string[] asConditionList) global native` | 390 |
| function | `UnmarkItemAsFavorite` | `Function UnmarkItemAsFavorite(Form akForm) global native` | 392 |
| function | `GetFurnitureType` | `int Function GetFurnitureType(Furniture akFurniture) global native` | 396 |
| function | `GetActivePlugins` | `String[] Function GetActivePlugins() global native` | 400 |
| function | `GetAllEnchantments` | `Enchantment[] Function GetAllEnchantments(Keyword[] akKeywords = None) global native` | 402 |
| function | `GetAllForms` | `Form[] Function GetAllForms(int aiFormType, Keyword[] akKeywords = None) global native` | 404 |
| function | `GetAllRaces` | `Race[] Function GetAllRaces(Keyword[] akKeywords = None) global native` | 406 |
| function | `GetAllSpells` | `Spell[] Function GetAllSpells(Keyword[] akKeywords = None, bool abIsPlayable = false) global native` | 408 |
| function | `GetActorsByProcessingLevel` | `Actor[] Function GetActorsByProcessingLevel(int aiLevel) global native` | 410 |
| function | `GetAllFormsInMod` | `Form[] Function GetAllFormsInMod(string asModName, int aiFormType, Keyword[] akKeywords = None) global native` | 412 |
| function | `GetAllEnchantmentsInMod` | `Enchantment[] Function GetAllEnchantmentsInMod(string asModName, Keyword[] akKeywords = None) global native` | 414 |
| function | `GetAllRacesInMod` | `Race[] Function GetAllRacesInMod(string asModName, Keyword[] akKeywords = None) global native` | 416 |
| function | `GetAllSpellsInMod` | `Spell[] Function GetAllSpellsInMod(string asModName, Keyword[] akKeywords = None, bool abIsPlayable = false) global native` | 418 |
| function | `GetAttachedCells` | `Cell[] Function GetAttachedCells() global native` | 420 |
| function | `GetFormFromEditorID` | `Form Function GetFormFromEditorID(string asEditorID) global native` | 422 |
| function | `GetGameSettingBool` | `int Function GetGameSettingBool(string asGameSetting) global native` | 424 |
| function | `GetGodMode` | `Bool Function GetGodMode() global native` | 426 |
| function | `GetLandHeight` | `float Function GetLandHeight(float afPosX, float afPosY, float afPosZ) global native` | 428 |
| function | `GetLandMaterialType` | `string Function GetLandMaterialType(float afPosX, float afPosY, float afPosZ) global native` | 430 |
| function | `GetLocalGravity` | `float[] Function GetLocalGravity() global native` | 432 |
| function | `GetNumActorsInHigh` | `int Function GetNumActorsInHigh() global native` | 434 |
| function | `GetPlayerFollowers` | `Actor[] Function GetPlayerFollowers() global native` | 436 |
| function | `GetSurfaceMaterialType` | `string Function GetSurfaceMaterialType(float afX, float afY, float afZ) global native` | 438 |
| function | `IsPluginFound` | `Bool Function IsPluginFound(string akName) global native` | 440 |
| function | `IsSurvivalModeActive` | `Bool Function IsSurvivalModeActive() global native` | 442 |
| function | `ClearCachedFactionFightReactions` | `Function ClearCachedFactionFightReactions() global native` | 444 |
| function | `SetLocalGravity` | `Function SetLocalGravity(float afXAxis, float afYAxis, float afZAxis) global native` | 446 |
| function | `UpdateCrosshairs` | `Function UpdateCrosshairs() global native` | 448 |
| function | `GetHazardArt` | `string Function GetHazardArt(Hazard akHazard) global native` | 453 |
| function | `GetHazardIMOD` | `ImageSpaceModifier Function GetHazardIMOD(Hazard akHazard) global native` | 455 |
| function | `GetHazardIMODRadius` | `float Function GetHazardIMODRadius(Hazard akHazard) global native` | 457 |
| function | `GetHazardIPDS` | `ImpactDataSet Function GetHazardIPDS(Hazard akHazard) global native` | 459 |
| function | `GetHazardLifetime` | `float Function GetHazardLifetime(Hazard akHazard) global native` | 461 |
| function | `GetHazardLight` | `Light Function GetHazardLight(Hazard akHazard) global native` | 463 |
| function | `GetHazardLimit` | `int Function GetHazardLimit(Hazard akHazard) global native` | 465 |
| function | `GetHazardRadius` | `float Function GetHazardRadius(Hazard akHazard) global native` | 467 |
| function | `GetHazardSound` | `SoundDescriptor Function GetHazardSound(Hazard akHazard) global native` | 469 |
| function | `GetHazardSpell` | `Spell Function GetHazardSpell(Hazard akHazard) global native` | 471 |
| function | `GetHazardTargetInterval` | `float Function GetHazardTargetInterval(Hazard akHazard) global native` | 473 |
| function | `IsHazardFlagSet` | `Bool Function IsHazardFlagSet(Hazard akHazard, int aiFlag) global native` | 475 |
| function | `ClearHazardFlag` | `Function ClearHazardFlag(Hazard akHazard, int aiFlag) global native` | 477 |
| function | `SetHazardArt` | `Function SetHazardArt(Hazard akHazard, string asPath) global native` | 479 |
| function | `SetHazardFlag` | `Function SetHazardFlag(Hazard akHazard, int aiFlag) global native` | 481 |
| function | `SetHazardIMOD` | `Function SetHazardIMOD(Hazard akHazard, ImageSpaceModifier akIMOD) global native` | 483 |
| function | `SetHazardIMODRadius` | `Function SetHazardIMODRadius(Hazard akHazard, float afRadius) global native` | 485 |
| function | `SetHazardIPDS` | `Function SetHazardIPDS(Hazard akHazard, ImpactDataSet akIPDS) global native` | 487 |
| function | `SetHazardLifetime` | `Function SetHazardLifetime(Hazard akHazard, float afLifetime) global native` | 489 |
| function | `SetHazardLight` | `Function SetHazardLight(Hazard akHazard, Light akLight) global native` | 491 |
| function | `SetHazardLimit` | `Function SetHazardLimit(Hazard akHazard, int aiLimit) global native` | 493 |
| function | `SetHazardRadius` | `Function SetHazardRadius(Hazard akHazard, float afRadius) global native` | 495 |
| function | `SetHazardSound` | `Function SetHazardSound(Hazard akHazard, SoundDescriptor akSound) global native` | 497 |
| function | `SetHazardSpell` | `Function SetHazardSpell(Hazard akHazard, Spell akspell) global native` | 499 |
| function | `SetHazardTargetInterval` | `Function SetHazardTargetInterval(Hazard akHazard, float afInterval) global native` | 501 |
| function | `GetAnimationEventName` | `string Function GetAnimationEventName(Idle akIdle) global native` | 505 |
| function | `GetAnimationFileName` | `string Function GetAnimationFileName(Idle akIdle) global native` | 507 |
| function | `GetLightColor` | `ColorForm Function GetLightColor(Light akLight) global native` | 511 |
| function | `GetLightFade` | `float Function GetLightFade(Light akLight) global native` | 513 |
| function | `GetLightFOV` | `float Function GetLightFOV(Light akLight) global native` | 515 |
| function | `GetLightRadius` | `float Function GetLightRadius(Light akLight) global native` | 517 |
| function | `GetLightRGB` | `int[] Function GetLightRGB(Light akLight) global native` | 519 |
| function | `GetLightShadowDepthBias` | `float Function GetLightShadowDepthBias(ObjectReference akLightObject) global native` | 521 |
| function | `GetLightType` | `int Function GetLightType(Light akLight) global native` | 523 |
| function | `SetLightColor` | `Function SetLightColor(Light akLight, ColorForm akColorform) global native` | 525 |
| function | `SetLightFade` | `Function SetLightFade(Light akLight, float afRange) global native` | 527 |
| function | `SetLightFOV` | `Function SetLightFOV(Light akLight, float afFOV) global native` | 529 |
| function | `SetLightRadius` | `Function SetLightRadius(Light akLight, float afRadius) global native` | 531 |
| function | `SetLightRGB` | `Function SetLightRGB(Light akLight, int[] aiRGB) global native` | 533 |
| function | `SetLightShadowDepthBias` | `Function SetLightShadowDepthBias(ObjectReference akLightObject, float afDepthBias) global native` | 535 |
| function | `SetLightType` | `Function SetLightType(Light akLight, int aiLightType) global native` | 537 |
| function | `GetContentFromLeveledItem` | `Form[] Function GetContentFromLeveledItem(LeveledItem akLeveledItem, ObjectReference akRef) global native` | 541 |
| function | `GetContentFromLeveledActor` | `Form[] Function GetContentFromLeveledActor(LeveledActor akLeveledActor, ObjectReference akRef) global native` | 545 |
| function | `GetContentFromLeveledSpell` | `Form[] Function GetContentFromLeveledSpell(LeveledSpell akLeveledSpell, ObjectReference akRef) global native` | 549 |
| function | `GetParentLocation` | `Location Function GetParentLocation(Location akLoc) global native` | 553 |
| function | `SetParentLocation` | `Function SetParentLocation(Location akLoc, Location akNewLoc) global native` | 555 |
| function | `GetAssociatedForm` | `Form Function GetAssociatedForm(MagicEffect akMagicEffect) global native` | 559 |
| function | `GetEffectArchetypeAsInt` | `int Function GetEffectArchetypeAsInt(MagicEffect akMagicEffect) global native` | 561 |
| function | `GetEffectArchetypeAsString` | `string Function GetEffectArchetypeAsString(MagicEffect akMagicEffect) global native` | 563 |
| function | `GetPrimaryActorValue` | `string Function GetPrimaryActorValue(MagicEffect akMagicEffect) global native` | 565 |
| function | `GetSecondaryActorValue` | `string Function GetSecondaryActorValue(MagicEffect akMagicEffect) global native` | 567 |
| function | `GetMagicEffectSound` | `SoundDescriptor Function GetMagicEffectSound(MagicEffect akMagicEffect, int aiType) global native` | 569 |
| function | `SetAssociatedForm` | `Function SetAssociatedForm(MagicEffect akMagicEffect, Form akForm) global native` | 571 |
| function | `SetMagicEffectSound` | `Function SetMagicEffectSound(MagicEffect akMagicEffect, SoundDescriptor akSoundDescriptor, int aiType) global native` | 573 |
| function | `ActorInRangeHasEffect` | `Bool Function ActorInRangeHasEffect(ObjectReference akRef, float afRadius, MagicEffect akEffect, bool abIgnorePlayer) global native` | 577 |
| function | `AddAllItemsToArray` | `Form[] Function AddAllItemsToArray(ObjectReference akRef, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` | 579 |
| function | `AddAllItemsToList` | `Function AddAllItemsToList(ObjectReference akRef, Formlist akList, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` | 581 |
| function | `AddItemsOfTypeToArray` | `Form[] Function AddItemsOfTypeToArray(ObjectReference akRef, int aiFormType, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` | 583 |
| function | `AddItemsOfTypeToList` | `Function AddItemsOfTypeToList(ObjectReference akRef, Formlist akList, int aiFormType, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` | 585 |
| function | `AddItemsWithKeywordToArray` | `Form[] Function AddItemsWithKeywordToArray(ObjectReference akRef, Keyword akKeyword, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` | 587 |
| function | `AddItemsWithKeywordToList` | `Function AddItemsWithKeywordToList(ObjectReference akRef, Formlist akList, Keyword akKeyword, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` | 589 |
| function | `AddItemsWithKeywordStringToArray` | `Form[] Function AddItemsWithKeywordStringToArray(ObjectReference akRef, String asKeywordString, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` | 591 |
| function | `AddItemsWithKeywordStringToList` | `Function AddItemsWithKeywordStringToList(ObjectReference akRef, Formlist akList, String asKeywordString, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` | 593 |
| function | `FindAllReferencesOfFormType` | `ObjectReference[] Function FindAllReferencesOfFormType(ObjectReference akRef, int formType, float afRadius) global native` | 595 |
| function | `FindAllReferencesWithKeyword` | `ObjectReference[] Function FindAllReferencesWithKeyword(ObjectReference akRef, Form keywordOrList, float afRadius, bool abMatchAll) global native` | 597 |
| function | `FindAllReferencesOfType` | `ObjectReference[] Function FindAllReferencesOfType(ObjectReference akRef, Form akFormOrList, float afRadius) global native` | 599 |
| function | `FindFirstItemInList` | `Form Function FindFirstItemInList(ObjectReference akRef, FormList akList) global native` | 601 |
| function | `GetActiveAssociatedQuests` | `Quest[] Function GetActiveAssociatedQuests(ObjectReference akRef, Bool abAllowEmptyStages = True) global native` | 603 |
| function | `GetActivateChildren` | `ObjectReference[] Function GetActivateChildren(ObjectReference akRef) global native` | 605 |
| function | `GetActiveGamebryoAnimation` | `string Function GetActiveGamebryoAnimation(ObjectReference akRef) global native` | 607 |
| function | `GetActiveMagicEffects` | `ActiveMagicEffect[] Function GetActiveMagicEffects(ObjectReference akRef, MagicEffect akMagicEffect) global native` | 609 |
| function | `GetAllAssociatedQuests` | `Quest[] Function GetAllAssociatedQuests(ObjectReference akRef, Bool abAllowEmptyStages = True) global native` | 611 |
| function | `GetActorCause` | `Actor Function GetActorCause(ObjectReference akRef) global native` | 613 |
| function | `GetAllArtObjects` | `Art[] Function GetAllArtObjects(ObjectReference akRef) global native` | 615 |
| function | `GetAllEffectShaders` | `EffectShader[] Function GetAllEffectShaders(ObjectReference akRef) global native` | 617 |
| function | `GetClosestActorFromRef` | `Actor Function GetClosestActorFromRef(ObjectReference akRef, bool abIgnorePlayer) global native` | 619 |
| function | `GetEffectShaderDuration` | `float Function GetEffectShaderDuration(ObjectReference akRef, EffectShader akShader) global native` | 621 |
| function | `GetDoorDestination` | `ObjectReference Function GetDoorDestination(ObjectReference akRef) global native` | 623 |
| function | `GetLinkedChildren` | `ObjectReference[] Function GetLinkedChildren(ObjectReference akRef, Keyword akKeyword) global native` | 625 |
| function | `GetMagicEffectSource` | `Form[] Function GetMagicEffectSource(ObjectReference akRef, MagicEffect akEffect) global native` | 627 |
| function | `GetMaterialType` | `string[] Function GetMaterialType(ObjectReference akRef, string asNodeName = "") global native` | 629 |
| function | `GetMotionType` | `int Function GetMotionType(ObjectReference akRef) global native` | 631 |
| function | `GetNumActorsWithEffectInRange` | `int Function GetNumActorsWithEffectInRange(ObjectReference akRef, float afRadius, MagicEffect akEffect, bool abignorePlayer) global native` | 633 |
| function | `GetRandomActorFromRef` | `Actor Function GetRandomActorFromRef(ObjectReference akRef, float afRadius, bool abIgnorePlayer) global native` | 635 |
| function | `GetQuestItems` | `Form[] Function GetQuestItems(ObjectReference akRef, bool abNoEquipped = false, bool abNoFavorited = false) global native` | 637 |
| function | `GetRefAliases` | `Alias[] Function GetRefAliases(ObjectReference akRef) global native` | 639 |
| function | `GetRefCount` | `int Function GetRefCount(ObjectReference akRef) global native` | 641 |
| function | `GetStoredSoulSize` | `int Function GetStoredSoulSize(ObjectReference akRef) global native` | 643 |
| function | `HasArtObject` | `int Function HasArtObject(ObjectReference akRef, Art akArtObject, bool abActive = false) global native` | 645 |
| function | `HasEffectShader` | `int Function HasEffectShader(ObjectReference akRef, EffectShader akShader, bool abActive = false) global native` | 647 |
| function | `HasNiExtraData` | `Bool Function HasNiExtraData(ObjectReference akRef, string asName) global native` | 649 |
| function | `IsCasting` | `Bool Function IsCasting(ObjectReference akRef, Form akMagicItem) global native` | 651 |
| function | `IsLoadDoor` | `Bool Function IsLoadDoor(ObjectReference akRef) global native` | 653 |
| function | `IsQuestItem` | `Bool Function IsQuestItem(ObjectReference akRef) global native` | 655 |
| function | `IsRefInWater` | `Bool Function IsRefInWater(ObjectReference akRef) global native` | 657 |
| function | `IsRefNodeInWater` | `Bool Function IsRefNodeInWater(ObjectReference akRef, String asNodeName) global native` | 659 |
| function | `IsRefUnderwater` | `Bool Function IsRefUnderwater(ObjectReference akRef) global native` | 661 |
| function | `IsVIP` | `Bool Function IsVIP(ObjectReference akRef) global native` | 663 |
| function | `ApplyMaterialShader` | `Function ApplyMaterialShader(ObjectReference akRef, MaterialObject akMatObject, float directionalThresholdAngle) global native` | 665 |
| function | `AddKeywordToRef` | `Function AddKeywordToRef(ObjectReference akRef, Keyword akKeyword) global native` | 667 |
| function | `CastEx` | `Function CastEx(ObjectReference akRef, Form akSpell, ObjectReference akTarget, Actor akBlameActor, int aiSource) global native` | 669 |
| function | `MoveToNearestNavmeshLocation` | `Function MoveToNearestNavmeshLocation(ObjectReference akRef) global native` | 671 |
| function | `RemoveAllModItems` | `Function RemoveAllModItems(ObjectReference akRef, string asModName, bool abOnlyUnequip = false) global native` | 673 |
| function | `RemoveListFromContainer` | `Function RemoveListFromContainer(ObjectReference akRef, FormList akList, bool abNoEquipped = false, bool abNoFavorited = false, bool abNoQuestItem = false, ObjectReference akDestination = None) global native` | 675 |
| function | `RemoveKeywordFromRef` | `Bool Function RemoveKeywordFromRef(ObjectReference akRef, Keyword akKeyword) global native` | 677 |
| function | `ReplaceKeywordOnRef` | `Function ReplaceKeywordOnRef(ObjectReference akRef, Keyword akKeywordAdd, Keyword akKeywordRemove) global native` | 679 |
| function | `PlayDebugShader` | `Function PlayDebugShader(ObjectReference akRef, float[] afRGBA) global native` | 681 |
| function | `ScaleObject3D` | `Function ScaleObject3D(ObjectReference akRef, string asNodeName, float afScale) global native` | 683 |
| function | `SetBaseObject` | `Function SetBaseObject(ObjectReference akRef, Form akBaseObject) global native` | 685 |
| function | `SetCollisionLayer` | `Function SetCollisionLayer(ObjectReference akRef, string asNodeName, int aiCollisionLayer) global native` | 687 |
| function | `SetDoorDestination` | `Bool Function SetDoorDestination(ObjectReference akRef, ObjectReference akDoor) global native` | 689 |
| function | `SetEffectShaderDuration` | `Function SetEffectShaderDuration(ObjectReference akRef, EffectShader akShader, float afTime, bool abAbsolute) global native` | 691 |
| function | `SetKey` | `Function SetKey(ObjectReference akRef, Key akKey) global native` | 693 |
| function | `SetLinkedRef` | `Function SetLinkedRef(ObjectReference akRef, ObjectReference akTargetRef, Keyword akKeyword = None) global native` | 695 |
| function | `SetMaterialType` | `Function SetMaterialType(ObjectReference akRef, string asNewMaterial, string asOldMaterial = "", string asNodeName = "") global native` | 697 |
| function | `SetupBodyPartGeometry` | `Function SetupBodyPartGeometry(ObjectReference akRef, actor akActor) global native` | 699 |
| function | `SetShaderType` | `Function SetShaderType(ObjectReference akRef, ObjectReference akTemplate, string asDiffusePath, int aiShaderType, int aiTextureType, bool abNoWeapons, bool abNoAlphaProperty) global native` | 701 |
| function | `StopAllShaders` | `Function StopAllShaders(ObjectReference akRef) global native` | 703 |
| function | `StopArtObject` | `Function StopArtObject(ObjectReference akRef, Art akArt) global native` | 705 |
| function | `ToggleChildNode` | `Function ToggleChildNode(ObjectReference akRef, string asNodeName, bool abDisable) global native` | 707 |
| function | `UpdateHitEffectArtNode` | `Function UpdateHitEffectArtNode(ObjectReference akRef, Art akArt, string asNewNode, float[] afTranslate, float[] afRotate, float afRelativeScale = 1.0) global native` | 709 |
| function | `GetPackageType` | `int Function GetPackageType(Package akPackage) global native` | 713 |
| function | `GetPackageIdles` | `Idle[] Function GetPackageIdles(Package akPackage) global native` | 715 |
| function | `AddPackageIdle` | `Function AddPackageIdle(Package akPackage, Idle akIdle) global native` | 717 |
| function | `RemovePackageIdle` | `Function RemovePackageIdle(Package akPackage, Idle akIdle) global native` | 719 |
| function | `GetPapyrusExtenderVersion` | `int[] Function GetPapyrusExtenderVersion() global native` | 724 |
| function | `AddMagicEffectToPotion` | `Function AddMagicEffectToPotion(Potion akPotion, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0, string[] asConditionList) global native` | 728 |
| function | `AddEffectItemToPotion` | `Function AddEffectItemToPotion(Potion akPotion, Potion akPotionToCopyFrom, int aiIndex, float afCost = -1.0) global native` | 730 |
| function | `RemoveMagicEffectFromPotion` | `Function RemoveMagicEffectFromPotion(Potion akPotion, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0) global native` | 732 |
| function | `RemoveEffectItemFromPotion` | `Function RemoveEffectItemFromPotion(Potion akPotion, Potion akPotionToMatchFrom, int aiIndex) global native` | 734 |
| function | `SetPotionMagicEffect` | `Function SetPotionMagicEffect(Potion akPotion, MagicEffect akMagicEffect, int aiIndex) global native` | 736 |
| function | `GetProjectileGravity` | `float Function GetProjectileGravity(Projectile akProjectile) global native` | 740 |
| function | `GetProjectileImpactForce` | `float Function GetProjectileImpactForce(Projectile akProjectile) global native` | 742 |
| function | `GetProjectileRange` | `float Function GetProjectileRange(Projectile akProjectile) global native` | 744 |
| function | `GetProjectileSpeed` | `float Function GetProjectileSpeed(Projectile akProjectile) global native` | 746 |
| function | `GetProjectileType` | `int Function GetProjectileType(Projectile akProjectile) global native` | 748 |
| function | `SetProjectileGravity` | `Function SetProjectileGravity(Projectile akProjectile, float afGravity) global native` | 750 |
| function | `SetProjectileImpactForce` | `Function SetProjectileImpactForce(Projectile akProjectile, float afImpactForce) global native` | 752 |
| function | `SetProjectileRange` | `Function SetProjectileRange(Projectile akProjectile, float afRange) global native` | 754 |
| function | `SetProjectileSpeed` | `Function SetProjectileSpeed(Projectile akProjectile, float afSpeed) global native` | 756 |
| function | `GetAllQuestObjectives` | `int[] Function GetAllQuestObjectives(Quest akQuest) global native` | 760 |
| function | `GetAllQuestStages` | `int[] Function GetAllQuestStages(Quest akQuest) global native` | 762 |
| function | `SetObjectiveText` | `Function SetObjectiveText(Quest akQuest, string asText, int aiIndex) global native` | 764 |
| function | `GetActorsInScene` | `Actor[] Function GetActorsInScene(Scene akScene) global native` | 768 |
| function | `IsActorInScene` | `bool Function IsActorInScene(Scene akScene, Actor akActor) global native` | 770 |
| function | `AddMagicEffectToScroll` | `Function AddMagicEffectToScroll(Scroll akScroll, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0, string[] asConditionList) global native` | 774 |
| function | `AddEffectItemToScroll` | `Function AddEffectItemToScroll(Scroll akScroll, Scroll akScrollToCopyFrom, int aiIndex, float afCost = -1.0) global native` | 776 |
| function | `RemoveMagicEffectFromScroll` | `Function RemoveMagicEffectFromScroll(Scroll akScroll, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0) global native` | 778 |
| function | `RemoveEffectItemFromScroll` | `Function RemoveEffectItemFromScroll(Scroll akScroll, Scroll akScrollToMatchFrom, int aiIndex) global native` | 780 |
| function | `SetScrollMagicEffect` | `Function SetScrollMagicEffect(Scroll akScroll, MagicEffect akMagicEffect, int aiIndex) global native` | 782 |
| function | `SetSoundDescriptor` | `Function SetSoundDescriptor(Sound akSound, SoundDescriptor akSoundDescriptor) global native` | 786 |
| function | `GetSpellType` | `int Function GetSpellType(Spell akSpell) global native` | 790 |
| function | `AddMagicEffectToSpell` | `Function AddMagicEffectToSpell(Spell akSpell, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0, string[] asConditionList) global native` | 792 |
| function | `AddEffectItemToSpell` | `Function AddEffectItemToSpell(Spell akSpell, Spell akSpellToCopyFrom, int aiIndex, float afCost = -1.0) global native` | 794 |
| function | `RemoveMagicEffectFromSpell` | `Function RemoveMagicEffectFromSpell(Spell akSpell, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0) global native` | 796 |
| function | `RemoveEffectItemFromSpell` | `Function RemoveEffectItemFromSpell(Spell akSpell, Spell akSpellToMatchFrom, int aiIndex) global native` | 798 |
| function | `SetSpellCastingType` | `Function SetSpellCastingType(Spell akSpell, int aiType) global native` | 800 |
| function | `SetSpellDeliveryType` | `Function SetSpellDeliveryType(Spell akSpell, int aiType) global native` | 802 |
| function | `SetSpellType` | `Function SetSpellType(Spell akSpell, int aiType) global native` | 804 |
| function | `SetSpellMagicEffect` | `Function SetSpellMagicEffect(Spell akSpell, MagicEffect akMagicEffect, int aiIndex) global native` | 806 |
| function | `IntToString` | `string Function IntToString(int aiValue, bool abHex) global native` | 810 |
| function | `StringToInt` | `int Function StringToInt(string asString) global native` | 812 |
| function | `GetMenuContainer` | `ObjectReference Function GetMenuContainer() global native` | 816 |
| function | `HideMenu` | `Function HideMenu(string asMenuName) global native` | 818 |
| function | `IsShowingMenus` | `Bool Function IsShowingMenus() global native` | 820 |
| function | `ShowBookMenu` | `Function ShowBookMenu(Book akBook) global native` | 822 |
| function | `ShowMenu` | `Function ShowMenu(string asMenuName) global native` | 824 |
| function | `ToggleOpenSleepWaitMenu` | `Function ToggleOpenSleepWaitMenu(bool abOpenSleepMenu) global native` | 826 |
| function | `ShowTutorialMessage` | `Function ShowTutorialMessage(Message akMessage) global native` | 828 |
| function | `GenerateRandomFloat` | `float Function GenerateRandomFloat(float afMin, float afMax) global native` | 832 |
| function | `GenerateRandomInt` | `int Function GenerateRandomInt(int afMin, int afMax) global native` | 834 |
| function | `GetSystemTime` | `int[] Function GetSystemTime() global native` | 836 |
| function | `GetArtObject` | `Art Function GetArtObject(VisualEffect akEffect) global native` | 840 |
| function | `GetArtObjectTotalCount` | `int Function GetArtObjectTotalCount(VisualEffect akEffect, bool abActive) global native` | 842 |
| function | `SetArtObject` | `Function SetArtObject(VisualEffect akEffect, Art akArt) global native` | 844 |
| function | `GetWindSpeedAsFloat` | `float Function GetWindSpeedAsFloat(Weather akWeather) global native` | 848 |
| function | `GetWindSpeedAsInt` | `int Function GetWindSpeedAsInt(Weather akWeather) global native` | 850 |
| function | `GetWeatherType` | `int Function GetWeatherType(Weather akWeather = None) global native` | 852 |

## Interpretation

- `PO3_SKSEFunctions` is the large global native utility surface.
- `PO3_Events_Form`, `PO3_Events_Alias`, and `PO3_Events_AME` expose event-registration/event callback surfaces for different Papyrus host types.
- Debris, FootstepSet, LightingTemplate, and MaterialObject add script-object APIs for record families not covered by ordinary vanilla PSCs.
- Runtime availability still depends on a compatible Papyrus Extender DLL and its native registrations.
- Exact blob SHA is preserved per PSC so future API diffs can identify additions/removals/signature changes.
