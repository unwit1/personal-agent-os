# powerofthree Papyrus Extender — Event Registration and Callback Catalog

Imported: 2026-09-24
Upstream: `powerof3/PapyrusExtenderSSE` master
Status: source-derived event API

Papyrus Extender exposes parallel registration APIs for Form-like receivers, Alias receivers, and ActiveMagicEffect receivers.

## PO3_Events_Form

Source blob: `ec1cbca8a226177d72c70a22642e4f1080275e17`

### Registration functions

| Line | Function | Arguments |
|---:|---|---|
| 9 | `RegisterForActorFallLongDistance` | `Form akForm` |
| 10 | `UnregisterForActorFallLongDistance` | `Form akForm` |
| 17 | `RegisterForActorKilled` | `Form akForm` |
| 18 | `UnregisterForActorKilled` | `Form akForm` |
| 26 | `RegisterForActorReanimateStart` | `Form akForm` |
| 27 | `UnregisterForActorReanimateStart` | `Form akForm` |
| 29 | `RegisterForActorReanimateStop` | `Form akForm` |
| 30 | `UnregisterForActorReanimateStop` | `Form akForm` |
| 41 | `RegisterForActorResurrected` | `Form akForm` |
| 42 | `UnregisterForActorResurrected` | `Form akForm` |
| 49 | `RegisterForBookRead` | `Form akForm` |
| 50 | `UnregisterForBookRead` | `Form akForm` |
| 57 | `RegisterForCellFullyLoaded` | `Form akForm` |
| 58 | `UnregisterForCellFullyLoaded` | `Form akForm` |
| 65 | `RegisterForCriticalHit` | `Form akForm` |
| 66 | `UnregisterForCriticalHit` | `Form akForm` |
| 73 | `RegisterForDisarmed` | `Form akForm` |
| 74 | `UnregisterForDisarmed` | `Form akForm` |
| 81 | `RegisterForDragonSoulGained` | `Form akForm` |
| 82 | `UnregisterForDragonSoulGained` | `Form akForm` |
| 89 | `RegisterForOnPlayerFastTravelEnd` | `Form akForm` |
| 90 | `UnregisterForOnPlayerFastTravelEnd` | `Form akForm` |
| 97 | `RegisterForFastTravelConfirmed` | `Form akForm` |
| 98 | `UnregisterForFastTravelConfirmed` | `Form akForm` |
| 105 | `RegisterForFastTravelPrompt` | `Form akForm` |
| 106 | `UnregisterForFastTravelPrompt` | `Form akForm` |
| 114 | `RegisterForFurnitureEvent` | `Form akForm` |
| 115 | `UnregisterForFurnitureEvent` | `Form akForm` |
| 132 | `UnregisterForAllHitEventsEx` | `Form akForm` |
| 139 | `RegisterForItemCrafted` | `Form akForm` |
| 140 | `UnregisterForItemCrafted` | `Form akForm` |
| 147 | `RegisterForItemHarvested` | `Form akForm` |
| 148 | `UnregisterForItemHarvested` | `Form akForm` |
| 155 | `RegisterForLevelIncrease` | `Form akForm` |
| 156 | `UnregisterForLevelIncrease` | `Form akForm` |
| 163 | `RegisterForLocationDiscovery` | `Form akForm` |
| 164 | `UnregisterForLocationDiscovery` | `Form akForm` |
| 171 | `RegisterForObjectGrab` | `Form akForm` |
| 172 | `UnregisterForObjectGrab` | `Form akForm` |
| 182 | `RegisterForObjectLoaded` | `Form akForm, int formType` |
| 183 | `UnregisterForObjectLoaded` | `Form akForm, int formType` |
| 184 | `UnregisterForAllObjectsLoaded` | `Form akForm` |
| 194 | `RegisterForObjectPoisoned` | `Form akForm` |
| 195 | `UnregisterForObjectPoisoned` | `Form akForm` |
| 202 | `RegisterForQuest` | `Form akForm, Quest akQuest` |
| 203 | `UnregisterForQuest` | `Form akForm, Quest akQuest` |
| 204 | `UnregisterForAllQuests` | `Form akForm` |
| 214 | `RegisterForQuestStage` | `Form akForm, Quest akQuest` |
| 215 | `UnregisterForQuestStage` | `Form akForm, Quest akQuest` |
| 216 | `UnregisterForAllQuestStages` | `Form akForm` |
| 223 | `RegisterForShoutAttack` | `Form akForm` |
| 224 | `UnregisterForShoutAttack` | `Form akForm` |
| 231 | `RegisterForSkillIncrease` | `Form akForm` |
| 232 | `UnregisterForSkillIncrease` | `Form akForm` |
| 239 | `RegisterForSoulTrapped` | `Form akForm` |
| 240 | `UnregisterForSoulTrapped` | `Form akForm` |
| 247 | `RegisterForSpellLearned` | `Form akForm` |
| 248 | `UnregisterForSpellLearned` | `Form akForm` |
| 255 | `RegisterForWeatherChange` | `Form akForm` |
| 256 | `UnregisterForWeatherChange` | `Form akForm` |
| 264 | `RegisterForMagicEffectApplyEx` | `Form akForm, Form akEffectFilter, bool abMatch` |
| 265 | `UnregisterForMagicEffectApplyEx` | `Form akForm, Form akEffectFilter, bool abMatch` |
| 266 | `UnregisterForAllMagicEffectApplyEx` | `Form akForm` |
| 274 | `RegisterForWeaponHit` | `Form akForm` |
| 275 | `UnregisterForWeaponHit` | `Form akForm` |
| 283 | `RegisterForMagicHit` | `Form akForm` |
| 284 | `UnregisterForMagicHit` | `Form akForm` |
| 292 | `RegisterForProjectileHit` | `Form akForm` |
| 293 | `UnregisterForProjectileHit` | `Form akForm` |

### Callback events

| Line | Event | Arguments |
|---:|---|---|
| 12 | `OnActorFallLongDistance` | `Actor akTarget, float afFallDistance, float afFallDamage` |
| 20 | `OnActorKilled` | `Actor akVictim, Actor akKiller` |
| 32 | `OnActorReanimateStart` | `Actor akTarget, Actor akCaster` |
| 35 | `OnActorReanimateStop` | `Actor akTarget, Actor akCaster` |
| 44 | `OnActorResurrected` | `Actor akTarget, bool abResetInventory` |
| 52 | `OnBookRead` | `Book akBook` |
| 60 | `OnCellFullyLoaded` | `Cell akCell` |
| 68 | `OnCriticalHit` | `Actor akAggressor, Weapon akWeapon, bool abSneakHit` |
| 76 | `OnDisarmed` | `Actor akSource, Weapon akTarget` |
| 84 | `OnDragonSoulGained` | `float afSouls` |
| 92 | `OnPlayerFastTravelEnd` | `float afTravelGameTimeHours` |
| 100 | `OnFastTravelConfirmed` | `ObjectReference asMarkerReference` |
| 108 | `OnFastTravelPrompt` | `ObjectReference asMarkerReference` |
| 117 | `OnEnterFurniture` | `ObjectReference akRef` |
| 120 | `OnExitFurniture` | `ObjectReference akRef` |
| 134 | `OnHitEx` | `ObjectReference akAggressor, Form akSource, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked` |
| 142 | `OnItemCrafted` | `ObjectReference akBench, Location akLocation, Form akCreatedItem` |
| 150 | `OnItemHarvested` | `Form akProduce` |
| 158 | `OnLevelIncrease` | `int aiLevel` |
| 166 | `OnLocationDiscovery` | `String asRegionName, String asWorldspaceName` |
| 174 | `OnObjectGrab` | `ObjectReference akObjectRef` |
| 177 | `OnObjectRelease` | `ObjectReference akObjectRef` |
| 186 | `OnObjectLoaded` | `ObjectReference akRef, int aiFormType` |
| 189 | `OnObjectUnloaded` | `ObjectReference akRef, int aiFormType` |
| 197 | `OnObjectPoisoned` | `Form akObject, Potion akPoison, int aiDose` |
| 206 | `OnQuestStart` | `Quest akQuest` |
| 209 | `OnQuestStop` | `Quest akQuest` |
| 218 | `OnQuestStageChange` | `Quest akQuest, Int aiNewStage` |
| 226 | `OnPlayerShoutAttack` | `Shout akShout` |
| 234 | `OnSkillIncrease` | `Int aiSkill` |
| 242 | `OnSoulTrapped` | `Actor akVictim, Actor akKiller` |
| 250 | `OnSpellLearned` | `Spell akSpell` |
| 258 | `OnWeatherChange` | `Weather akOldWeather, Weather akNewWeather` |
| 268 | `OnMagicEffectApplyEx` | `ObjectReference akCaster, MagicEffect akEffect, Form akSource, bool abApplied` |
| 277 | `OnWeaponHit` | `ObjectReference akTarget, Form akSource, Projectile akProjectile, Int aiHitFlagMask` |
| 286 | `OnMagicHit` | `ObjectReference akTarget, Form akSource, Projectile akProjectile` |
| 295 | `OnProjectileHit` | `ObjectReference akTarget, Form akSource, Projectile akProjectile` |

## PO3_Events_Alias

Source blob: `84c66be7d52c1a156ff43521f2bd31ce3c3f3eee`

### Registration functions

| Line | Function | Arguments |
|---:|---|---|
| 9 | `RegisterForActorFallLongDistance` | `ReferenceAlias akRefAlias` |
| 10 | `UnregisterForActorFallLongDistance` | `ReferenceAlias akRefAlias` |
| 17 | `RegisterForActorKilled` | `Alias akAlias` |
| 18 | `UnregisterForActorKilled` | `Alias akAlias` |
| 25 | `RegisterForActorReanimateStart` | `Alias akAlias` |
| 26 | `UnregisterForActorReanimateStart` | `Alias akAlias` |
| 28 | `RegisterForActorReanimateStop` | `Alias akAlias` |
| 29 | `UnregisterForActorReanimateStop` | `Alias akAlias` |
| 39 | `RegisterForActorResurrected` | `Alias akAlias` |
| 40 | `UnregisterForActorResurrected` | `Alias akAlias` |
| 47 | `RegisterForBookRead` | `Alias akAlias` |
| 48 | `UnregisterForBookRead` | `Alias akAlias` |
| 55 | `RegisterForCellFullyLoaded` | `Alias akAlias` |
| 56 | `UnregisterForCellFullyLoaded` | `Alias akAlias` |
| 63 | `RegisterForCriticalHit` | `Alias akAlias` |
| 64 | `UnregisterForCriticalHit` | `Alias akAlias` |
| 71 | `RegisterForDisarmed` | `Alias akAlias` |
| 72 | `UnregisterForDisarmed` | `Alias akAlias` |
| 79 | `RegisterForDragonSoulGained` | `Alias akAlias` |
| 80 | `UnregisterForDragonSoulGained` | `Alias akAlias` |
| 87 | `RegisterForOnPlayerFastTravelEnd` | `Alias akAlias` |
| 88 | `UnregisterForOnPlayerFastTravelEnd` | `Alias akAlias` |
| 95 | `RegisterForFastTravelConfirmed` | `Alias akAlias` |
| 96 | `UnregisterForFastTravelConfirmed` | `Alias akAlias` |
| 103 | `RegisterForFastTravelPrompt` | `Alias akAlias` |
| 104 | `UnregisterForFastTravelPrompt` | `Alias akAlias` |
| 111 | `RegisterForFurnitureEvent` | `ReferenceAlias akRefAlias` |
| 112 | `UnregisterForFurnitureEvent` | `ReferenceAlias akRefAlias` |
| 128 | `UnregisterForAllHitEventsEx` | `ReferenceAlias akRefAlias` |
| 135 | `RegisterForItemCrafted` | `Alias akAlias` |
| 136 | `UnregisterForItemCrafted` | `Alias akAlias` |
| 143 | `RegisterForItemHarvested` | `Alias akAlias` |
| 144 | `UnregisterForItemHarvested` | `Alias akAlias` |
| 151 | `RegisterForLevelIncrease` | `Alias akAlias` |
| 152 | `UnregisterForLevelIncrease` | `Alias akAlias` |
| 159 | `RegisterForLocationDiscovery` | `Alias akAlias` |
| 160 | `UnregisterForLocationDiscovery` | `Alias akAlias` |
| 167 | `RegisterForObjectGrab` | `Alias akAlias` |
| 168 | `UnregisterForObjectGrab` | `Alias akAlias` |
| 178 | `RegisterForObjectLoaded` | `Alias akAlias, int formType` |
| 179 | `UnregisterForObjectLoaded` | `Alias akAlias, int formType` |
| 180 | `UnregisterForAllObjectsLoaded` | `Alias akAlias` |
| 190 | `RegisterForObjectPoisoned` | `Alias akAlias` |
| 191 | `UnregisterForObjectPoisoned` | `Alias akAlias` |
| 198 | `RegisterForQuest` | `Alias akAlias, Quest akQuest` |
| 199 | `UnregisterForQuest` | `Alias akAlias, Quest akQuest` |
| 200 | `UnregisterForAllQuests` | `Alias akAlias` |
| 210 | `RegisterForQuestStage` | `Alias akAlias, Quest akQuest` |
| 211 | `UnregisterForQuestStage` | `Alias akAlias, Quest akQuest` |
| 212 | `UnregisterForAllQuestStages` | `Alias akAlias` |
| 219 | `RegisterForShoutAttack` | `Alias akAlias` |
| 220 | `UnregisterForShoutAttack` | `Alias akAlias` |
| 227 | `RegisterForSkillIncrease` | `Alias akAlias` |
| 228 | `UnregisterForSkillIncrease` | `Alias akAlias` |
| 235 | `RegisterForSoulTrapped` | `Alias akAlias` |
| 236 | `UnregisterForSoulTrapped` | `Alias akAlias` |
| 243 | `RegisterForSpellLearned` | `Alias akAlias` |
| 244 | `UnregisterForSpellLearned` | `Alias akAlias` |
| 251 | `RegisterForWeatherChange` | `Alias akAlias` |
| 252 | `UnregisterForWeatherChange` | `Alias akAlias` |
| 259 | `RegisterForMagicEffectApplyEx` | `ReferenceAlias akRefAlias, Form akEffectFilter, bool abMatch` |
| 260 | `UnregisterForMagicEffectApplyEx` | `ReferenceAlias akRefAlias, Form akEffectFilter, bool abMatch` |
| 261 | `UnregisterForAllMagicEffectApplyEx` | `ReferenceAlias akRefAlias` |
| 268 | `RegisterForWeaponHit` | `ReferenceAlias akRefAlias` |
| 269 | `UnregisterForWeaponHit` | `ReferenceAlias akRefAlias` |
| 276 | `RegisterForMagicHit` | `ReferenceAlias akRefAlias` |
| 277 | `UnregisterForMagicHit` | `ReferenceAlias akRefAlias` |
| 284 | `RegisterForProjectileHit` | `ReferenceAlias akRefAlias` |
| 285 | `UnregisterForProjectileHit` | `ReferenceAlias akRefAlias` |

### Callback events

| Line | Event | Arguments |
|---:|---|---|
| 12 | `OnActorFallLongDistance` | `Actor akTarget, float afFallDistance, float afFallDamage` |
| 20 | `OnActorKilled` | `Actor akVictim, Actor akKiller` |
| 31 | `OnActorReanimateStart` | `Actor akTarget, Actor akCaster` |
| 34 | `OnActorReanimateStop` | `Actor akTarget, Actor akCaster` |
| 42 | `OnActorResurrected` | `Actor akTarget, bool abResetInventory` |
| 50 | `OnBookRead` | `Book akBook` |
| 58 | `OnCellFullyLoaded` | `Cell akCell` |
| 66 | `OnCriticalHit` | `Actor akAggressor, Weapon akWeapon, bool abSneakHit` |
| 74 | `OnDisarmed` | `Actor akSource, Weapon akTarget` |
| 82 | `OnDragonSoulGained` | `float afSouls` |
| 90 | `OnPlayerFastTravelEnd` | `float afTravelGameTimeHours` |
| 98 | `OnFastTravelConfirmed` | `ObjectReference asMarkerReference` |
| 106 | `OnFastTravelPrompt` | `ObjectReference asMarkerReference` |
| 114 | `OnEnterFurniture` | `ObjectReference akRef` |
| 117 | `OnExitFurniture` | `ObjectReference akRef` |
| 130 | `OnHitEx` | `ObjectReference akAggressor, Form akSource, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked` |
| 138 | `OnItemCrafted` | `ObjectReference akBench, Location akLocation, Form akCreatedItem` |
| 146 | `OnItemHarvested` | `Form akProduce` |
| 154 | `OnLevelIncrease` | `int aiLevel` |
| 162 | `OnLocationDiscovery` | `String asRegionName, String asWorldspaceName` |
| 170 | `OnObjectGrab` | `ObjectReference akObjectRef` |
| 173 | `OnObjectRelease` | `ObjectReference akObjectRef` |
| 182 | `OnObjectLoaded` | `ObjectReference akRef, int aiFormType` |
| 185 | `OnObjectUnloaded` | `ObjectReference akRef, int aiFormType` |
| 193 | `OnObjectPoisoned` | `Form akObject, Potion akPoison, int aiDose` |
| 202 | `OnQuestStart` | `Quest akQuest` |
| 205 | `OnQuestStop` | `Quest akQuest` |
| 214 | `OnQuestStageChange` | `Quest akQuest, Int aiNewStage` |
| 222 | `OnShoutAttack` | `Shout akShout` |
| 230 | `OnSkillIncrease` | `Int aiSkill` |
| 238 | `OnSoulTrapped` | `Actor akVictim, Actor akKiller` |
| 246 | `OnSpellLearned` | `Spell akSpell` |
| 254 | `OnWeatherChange` | `Weather akOldWeather, Weather akNewWeather` |
| 263 | `OnMagicEffectApplyEx` | `ObjectReference akCaster, MagicEffect akEffect, Form akSource, bool abApplied` |
| 271 | `OnWeaponHit` | `ObjectReference akTarget, Form akSource, Projectile akProjectile, Int aiHitFlagMask` |
| 279 | `OnMagicHit` | `ObjectReference akTarget, Form akSource, Projectile akProjectile` |
| 287 | `OnProjectileHit` | `ObjectReference akTarget, Form akSource, Projectile akProjectile` |

## PO3_Events_AME

Source blob: `1c7690d0404e5f0cff5475a25955522106efdfe4`

### Registration functions

| Line | Function | Arguments |
|---:|---|---|
| 8 | `RegisterForActorFallLongDistance` | `ActiveMagicEffect akActiveEffect` |
| 9 | `UnregisterForActorFallLongDistance` | `ActiveMagicEffect akActiveEffect` |
| 16 | `RegisterForActorKilled` | `ActiveMagicEffect akActiveEffect` |
| 17 | `UnregisterForActorKilled` | `ActiveMagicEffect akActiveEffect` |
| 24 | `RegisterForActorReanimateStart` | `ActiveMagicEffect akActiveEffect` |
| 25 | `UnregisterForActorReanimateStart` | `ActiveMagicEffect akActiveEffect` |
| 27 | `RegisterForActorReanimateStop` | `ActiveMagicEffect akActiveEffect` |
| 28 | `UnregisterForActorReanimateStop` | `ActiveMagicEffect akActiveEffect` |
| 38 | `RegisterForActorResurrected` | `ActiveMagicEffect akActiveEffect` |
| 39 | `UnregisterForActorResurrected` | `ActiveMagicEffect akActiveEffect` |
| 46 | `RegisterForBookRead` | `ActiveMagicEffect akActiveEffect` |
| 47 | `UnregisterForBookRead` | `ActiveMagicEffect akActiveEffect` |
| 54 | `RegisterForCellFullyLoaded` | `ActiveMagicEffect akActiveEffect` |
| 55 | `UnregisterForCellFullyLoaded` | `ActiveMagicEffect akActiveEffect` |
| 62 | `RegisterForCriticalHit` | `ActiveMagicEffect akActiveEffect` |
| 63 | `UnregisterForCriticalHit` | `ActiveMagicEffect akActiveEffect` |
| 70 | `RegisterForDisarmed` | `ActiveMagicEffect akActiveEffect` |
| 71 | `UnregisterForDisarmed` | `ActiveMagicEffect akActiveEffect` |
| 78 | `RegisterForDragonSoulGained` | `ActiveMagicEffect akActiveEffect` |
| 79 | `UnregisterForDragonSoulGained` | `ActiveMagicEffect akActiveEffect` |
| 86 | `RegisterForOnPlayerFastTravelEnd` | `ActiveMagicEffect akActiveEffect` |
| 87 | `UnregisterForOnPlayerFastTravelEnd` | `ActiveMagicEffect akActiveEffect` |
| 94 | `RegisterForFastTravelConfirmed` | `ActiveMagicEffect akActiveEffect` |
| 95 | `UnregisterForFastTravelConfirmed` | `ActiveMagicEffect akActiveEffect` |
| 102 | `RegisterForFastTravelPrompt` | `ActiveMagicEffect akActiveEffect` |
| 103 | `UnregisterForFastTravelPrompt` | `ActiveMagicEffect akActiveEffect` |
| 110 | `RegisterForFurnitureEvent` | `ActiveMagicEffect akActiveEffect` |
| 111 | `UnregisterForFurnitureEvent` | `ActiveMagicEffect akActiveEffect` |
| 127 | `UnregisterForAllHitEventsEx` | `ActiveMagicEffect akActiveEffect` |
| 134 | `RegisterForItemCrafted` | `ActiveMagicEffect akActiveEffect` |
| 135 | `UnregisterForItemCrafted` | `ActiveMagicEffect akActiveEffect` |
| 142 | `RegisterForItemHarvested` | `ActiveMagicEffect akActiveEffect` |
| 143 | `UnregisterForItemHarvested` | `ActiveMagicEffect akActiveEffect` |
| 150 | `RegisterForLevelIncrease` | `ActiveMagicEffect akActiveEffect` |
| 151 | `UnregisterForLevelIncrease` | `ActiveMagicEffect akActiveEffect` |
| 158 | `RegisterForLocationDiscovery` | `ActiveMagicEffect akActiveEffect` |
| 159 | `UnregisterForLocationDiscovery` | `ActiveMagicEffect akActiveEffect` |
| 166 | `RegisterForObjectGrab` | `ActiveMagicEffect akActiveEffect` |
| 167 | `UnregisterForObjectGrab` | `ActiveMagicEffect akActiveEffect` |
| 177 | `RegisterForObjectLoaded` | `ActiveMagicEffect akActiveEffect, int formType` |
| 178 | `UnregisterForObjectLoaded` | `ActiveMagicEffect akActiveEffect, int formType` |
| 179 | `UnregisterForAllObjectsLoaded` | `ActiveMagicEffect akActiveEffect` |
| 189 | `RegisterForObjectPoisoned` | `ActiveMagicEffect akActiveEffect` |
| 190 | `UnregisterForObjectPoisoned` | `ActiveMagicEffect akActiveEffect` |
| 197 | `RegisterForQuest` | `ActiveMagicEffect akActiveEffect, Quest akQuest` |
| 198 | `UnregisterForQuest` | `ActiveMagicEffect akActiveEffect, Quest akQuest` |
| 199 | `UnregisterForAllQuests` | `ActiveMagicEffect akActiveEffect` |
| 209 | `RegisterForQuestStage` | `ActiveMagicEffect akActiveEffect, Quest akQuest` |
| 210 | `UnregisterForQuestStage` | `ActiveMagicEffect akActiveEffect, Quest akQuest` |
| 211 | `UnregisterForAllQuestStages` | `ActiveMagicEffect akActiveEffect` |
| 218 | `RegisterForShoutAttack` | `ActiveMagicEffect akActiveEffect` |
| 219 | `UnregisterForShoutAttack` | `ActiveMagicEffect akActiveEffect` |
| 226 | `RegisterForSkillIncrease` | `ActiveMagicEffect akActiveEffect` |
| 227 | `UnregisterForSkillIncrease` | `ActiveMagicEffect akActiveEffect` |
| 234 | `RegisterForSoulTrapped` | `ActiveMagicEffect akActiveEffect` |
| 235 | `UnregisterForSoulTrapped` | `ActiveMagicEffect akActiveEffect` |
| 242 | `RegisterForSpellLearned` | `ActiveMagicEffect akActiveEffect` |
| 243 | `UnregisterForSpellLearned` | `ActiveMagicEffect akActiveEffect` |
| 250 | `RegisterForWeatherChange` | `ActiveMagicEffect akActiveEffect` |
| 251 | `UnregisterForWeatherChange` | `ActiveMagicEffect akActiveEffect` |
| 258 | `RegisterForMagicEffectApplyEx` | `ActiveMagicEffect akActiveEffect, Form akEffectFilter, bool abMatch` |
| 259 | `UnregisterForMagicEffectApplyEx` | `ActiveMagicEffect akActiveEffect, Form akEffectFilter, bool abMatch` |
| 260 | `UnregisterForAllMagicEffectApplyEx` | `ActiveMagicEffect akActiveEffect` |
| 267 | `RegisterForWeaponHit` | `ActiveMagicEffect akActiveEffect` |
| 268 | `UnregisterForWeaponHit` | `ActiveMagicEffect akActiveEffect` |
| 275 | `RegisterForMagicHit` | `ActiveMagicEffect akActiveEffect` |
| 276 | `UnregisterForMagicHit` | `ActiveMagicEffect akActiveEffect` |
| 283 | `RegisterForProjectileHit` | `ActiveMagicEffect akActiveEffect` |
| 284 | `UnregisterForProjectileHit` | `ActiveMagicEffect akActiveEffect` |

### Callback events

| Line | Event | Arguments |
|---:|---|---|
| 11 | `OnActorFallLongDistance` | `Actor akTarget, float afFallDistance, float afFallDamage` |
| 19 | `OnActorKilled` | `Actor akVictim, Actor akKiller` |
| 30 | `OnActorReanimateStart` | `Actor akTarget, Actor akCaster` |
| 33 | `OnActorReanimateStop` | `Actor akTarget, Actor akCaster` |
| 41 | `OnActorResurrected` | `Actor akTarget, bool abResetInventory` |
| 49 | `OnBookRead` | `Book akBook` |
| 57 | `OnCellFullyLoaded` | `Cell akCell` |
| 65 | `OnCriticalHit` | `Actor akAggressor, Weapon akWeapon, bool abSneakHit` |
| 73 | `OnDisarmed` | `Actor akSource, Weapon akTarget` |
| 81 | `OnDragonSoulGained` | `float afSouls` |
| 89 | `OnPlayerFastTravelEnd` | `float afTravelGameTimeHours` |
| 97 | `OnFastTravelConfirmed` | `ObjectReference asMarkerReference` |
| 105 | `OnFastTravelPrompt` | `ObjectReference asMarkerReference` |
| 113 | `OnEnterFurniture` | `ObjectReference akRef` |
| 116 | `OnExitFurniture` | `ObjectReference akRef` |
| 129 | `OnHitEx` | `ObjectReference akAggressor, Form akSource, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked` |
| 137 | `OnItemCrafted` | `ObjectReference akBench, Location akLocation, Form akCreatedItem` |
| 145 | `OnItemHarvested` | `Form akProduce` |
| 153 | `OnLevelIncrease` | `int aiLevel` |
| 161 | `OnLocationDiscovery` | `String asRegionName, String asWorldspaceName` |
| 169 | `OnObjectGrab` | `ObjectReference akObjectRef` |
| 172 | `OnObjectRelease` | `ObjectReference akObjectRef` |
| 181 | `OnObjectLoaded` | `ObjectReference akRef, int aiFormType` |
| 184 | `OnObjectUnloaded` | `ObjectReference akRef, int aiFormType` |
| 192 | `OnObjectPoisoned` | `Form akObject, Potion akPoison, int aiDose` |
| 201 | `OnQuestStart` | `Quest akQuest` |
| 204 | `OnQuestStop` | `Quest akQuest` |
| 213 | `OnQuestStageChange` | `Quest akQuest, Int aiNewStage` |
| 221 | `OnPlayerShoutAttack` | `Shout akShout` |
| 229 | `OnSkillIncrease` | `Int aiSkill` |
| 237 | `OnSoulTrapped` | `Actor akVictim, Actor akKiller` |
| 245 | `OnSpellLearned` | `Spell akSpell` |
| 253 | `OnWeatherChange` | `Weather akOldWeather, Weather akNewWeather` |
| 262 | `OnMagicEffectApplyEx` | `ObjectReference akCaster, MagicEffect akEffect, Form akSource, bool abApplied` |
| 270 | `OnWeaponHit` | `ObjectReference akTarget, Form akSource, Projectile akProjectile, Int aiHitFlagMask` |
| 278 | `OnMagicHit` | `ObjectReference akTarget, Form akSource, Projectile akProjectile` |
| 286 | `OnProjectileHit` | `ObjectReference akTarget, Form akSource, Projectile akProjectile` |

## Extracted totals

- Registration/management function declarations across the three event scripts: **207**
- Event callback declarations across the three event scripts: **111**

These declaration totals are source-structure counts and are not necessarily identical to a project README's marketing/API-summary count because one logical event can have register + unregister + unregister-all functions and can be exposed for several receiver families.

## Design rules

1. Choose the receiver family matching the script lifecycle: Form, Alias, or ActiveMagicEffect.
2. Pair registrations with appropriate unregistration/cleanup.
3. Treat extended hit/magic/projectile events as richer provider-specific callbacks, not vanilla OnHit replacements.
4. Preserve provider version when using event signatures; event payloads can expand across releases.
5. Avoid registering globally for high-frequency events when a narrower filtered registration exists.
