# powerofthree Papyrus Extender — Source-Derived API Catalog

Imported: 2026-09-24
Upstream: `powerof3/PapyrusExtenderSSE` master
Status: source-derived implementation reference

## Scope

Upstream README describes Papyrus Extender as an SKSE64/VR plugin expanding Papyrus with hundreds of functions, 37 events, and four additional script object types.

The current source snapshot inspected here contains:
- `379` declarations in `PO3_SKSEFunctions.psc`;
- `37` event names implemented for Form-hosted registration;
- matching event registration surfaces for Alias and ActiveMagicEffect hosts;
- four added Form-derived script object stubs.

The source declaration count can move ahead of README marketing counts. Prefer the pinned PSC blob as the exact API surface for implementation work.

## Source blobs

- `Papyrus/Source/scripts/PO3_SKSEFunctions.psc` — `87fcdd7c399801c92449c59ddb46090b2cc93214`
- `Papyrus/Source/scripts/PO3_Events_Form.psc` — `ec1cbca8a226177d72c70a22642e4f1080275e17`
- `Papyrus/Source/scripts/PO3_Events_Alias.psc` — `84c66be7d52c1a156ff43521f2bd31ce3c3f3eee`
- `Papyrus/Source/scripts/PO3_Events_AME.psc` — `1c7690d0404e5f0cff5475a25955522106efdfe4`
- `Papyrus/Source/scripts/Debris.psc` — `13e8cdba871e316bcbc3e77bcc0c34197e8c6a77`
- `Papyrus/Source/scripts/FootstepSet.psc` — `9ac46dc3cbcf265a1f5c7b176bbf157f50657ad4`
- `Papyrus/Source/scripts/LightingTemplate.psc` — `422342b36d0e829e82321e8779bf5e1c4ce67c4f`
- `Papyrus/Source/scripts/MaterialObject.psc` — `d289af8cef6492a608f8bb0d4032af011d03a386`

## Additional script object types

| Script object | Parent |
|---|---|
| `Debris` | `Form` |
| `FootstepSet` | `Form` |
| `LightingTemplate` | `Form` |
| `MaterialObject` | `Form` |

These let Papyrus type signatures refer directly to engine forms that vanilla/older Papyrus did not expose as dedicated script classes.

## Event surface

The extender exposes the following event names. Registration is provided in host-specific variants for Form, Alias/ReferenceAlias, and ActiveMagicEffect where applicable.

| Event |
|---|
| `OnActorFallLongDistance` |
| `OnActorKilled` |
| `OnActorReanimateStart` |
| `OnActorReanimateStop` |
| `OnActorResurrected` |
| `OnBookRead` |
| `OnCellFullyLoaded` |
| `OnCriticalHit` |
| `OnDisarmed` |
| `OnDragonSoulGained` |
| `OnPlayerFastTravelEnd` |
| `OnFastTravelConfirmed` |
| `OnFastTravelPrompt` |
| `OnEnterFurniture` |
| `OnExitFurniture` |
| `OnHitEx` |
| `OnItemCrafted` |
| `OnItemHarvested` |
| `OnLevelIncrease` |
| `OnLocationDiscovery` |
| `OnObjectGrab` |
| `OnObjectRelease` |
| `OnObjectLoaded` |
| `OnObjectUnloaded` |
| `OnObjectPoisoned` |
| `OnQuestStart` |
| `OnQuestStop` |
| `OnQuestStageChange` |
| `OnPlayerShoutAttack` |
| `OnSkillIncrease` |
| `OnSoulTrapped` |
| `OnSpellLearned` |
| `OnWeatherChange` |
| `OnMagicEffectApplyEx` |
| `OnWeaponHit` |
| `OnMagicHit` |
| `OnProjectileHit` |

### Event-host pattern

- `PO3_Events_Form` — register a Form/script object.
- `PO3_Events_Alias` — register Alias or ReferenceAlias.
- `PO3_Events_AME` — register ActiveMagicEffect.

This lets authors choose a lifecycle-appropriate listener instead of inventing a polling quest solely to observe world events.

## Global function catalog

The table below is the exact declaration surface of `PO3_SKSEFunctions.psc` in this source snapshot.

| Line | Return | Function | Arguments | Modifiers |
|---:|---|---|---|---|
| 8 | `string[]` | `GetScriptsAttachedToActiveEffect` | `ActiveMagicEffect akActiveEffect` | `global native` |
| 10 | `Bool` | `IsScriptAttachedToActiveEffect` | `ActiveMagicEffect akActiveEffect, string asScriptName` | `global native` |
| 12 | `Form` | `GetActiveEffectSpell` | `ActiveMagicEffect akActiveEffect` | `global native` |
| 17 | `MagicEffect[]` | `GetActiveEffects` | `Actor akActor, bool abShowInactive = false` | `global native` |
| 19 | `float` | `GetActorAlpha` | `Actor akActor` | `global native` |
| 21 | `int` | `GetActorKnockState` | `Actor akActor` | `global native` |
| 23 | `float` | `GetActorRefraction` | `Actor akActor` | `global native` |
| 25 | `int` | `GetActorState` | `Actor akActor` | `global native` |
| 27 | `int` | `GetActorSoulSize` | `Actor akActor` | `global native` |
| 29 | `float` | `GetActorValueModifier` | `Actor akActor, int aiModifier, string asActorValue` | `global native` |
| 31 | `Spell[]` | `GetAllActorPlayableSpells` | `Actor akActor` | `global native` |
| 33 | `int` | `GetCriticalStage` | `Actor akActor` | `global native` |
| 35 | `Actor[]` | `GetCombatAllies` | `Actor akActor` | `global native` |
| 37 | `Actor[]` | `GetCombatTargets` | `Actor akActor` | `global native` |
| 39 | `Actor[]` | `GetCommandedActors` | `Actor akActor` | `global native` |
| 41 | `Actor` | `GetCommandingActor` | `Actor akActor` | `global native` |
| 43 | `float` | `GetEditorLocationX` | `Actor akActor` | `global native` |
| 45 | `float` | `GetEditorLocationY` | `Actor akActor` | `global native` |
| 47 | `float` | `GetEditorLocationZ` | `Actor akActor` | `global native` |
| 49 | `float` | `GetEditorLocationAngle` | `Actor akActor` | `global native` |
| 51 | `Ammo` | `GetEquippedAmmo` | `Actor akActor` | `global native` |
| 53 | `Enchantment` | `GetEquippedAmmoEnchantment` | `Actor akActor` | `global native` |
| 55 | `Bool` | `GetEquippedWeaponIsPoisoned` | `Actor akActor, bool abLeftHand` | `global native` |
| 57 | `Potion` | `GetEquippedWeaponPoison` | `Actor akActor, bool abLeftHand` | `global native` |
| 59 | `int` | `GetEquippedWeaponPoisonCount` | `Actor akActor, bool abLeftHand` | `global native` |
| 61 | `float` | `GetEquippedWeight` | `Actor akActor` | `global native` |
| 64 | `ColorForm` | `GetHairColor` | `Actor akActor` | `global native` |
| 66 | `int[]` | `GetHairRGB` | `Actor akActor` | `global native` |
| 68 | `TextureSet` | `GetHeadPartTextureSet` | `Actor akActor, int aiType` | `global native` |
| 70 | `float` | `GetLocalGravityActor` | `Actor akActor` | `global native` |
| 72 | `Actor` | `GetMount` | `Actor akActor` | `global native` |
| 74 | `ObjectReference` | `GetObjectUnderFeet` | `Actor akActor` | `global native` |
| 76 | `Bool` | `GetOffersServices` | `Actor akActor` | `global native` |
| 78 | `Actor` | `GetRider` | `Actor akActor` | `global native` |
| 80 | `Package` | `GetRunningPackage` | `Actor akActor` | `global native` |
| 83 | `ColorForm` | `GetSkinColor` | `Actor akActor` | `global native` |
| 85 | `int[]` | `GetSkinRGB` | `Actor akActor` | `global native` |
| 87 | `float` | `GetTimeDead` | `Actor akActor` | `global native` |
| 89 | `float` | `GetTimeOfDeath` | `Actor akActor` | `global native` |
| 91 | `Faction` | `GetVendorFaction` | `Actor akActor` | `global native` |
| 93 | `Bool` | `HasActiveMagicEffect` | `Actor akActor, MagicEffect akEffect` | `global native` |
| 95 | `Bool` | `HasActiveSpell` | `Actor akActor, Spell akSpell` | `global native` |
| 97 | `Bool` | `HasDeferredKill` | `Actor akActor` | `global native` |
| 99 | `Bool` | `HasMagicEffectWithArchetype` | `Actor akActor, string asArchetype` | `global native` |
| 101 | `Bool` | `HasSkin` | `Actor akActor, Armor akArmorToCheck` | `global native` |
| 103 | `Bool` | `IsActorInWater` | `Actor akActor` | `global native` |
| 105 | `Bool` | `IsActorUnderwater` | `Actor akActor` | `global native` |
| 107 | `Bool` | `IsLimbGone` | `Actor akActor, int aiLimb` | `global native` |
| 109 | `Bool` | `IsPowerAttacking` | `Actor akActor` | `global native` |
| 111 | `Bool` | `IsQuadruped` | `Actor akActor` | `global native` |
| 113 | `Bool` | `IsSoulTrapped` | `Actor akActor` | `global native` |
| 115 | `Bool` | `ApplyPoisonToEquippedWeapon` | `Actor akActor, Potion akPoison, int aiCount, bool abLeftHand` | `global native` |
| 117 | `Form[]` | `AddAllEquippedItemsToArray` | `Actor akActor` | `global native` |
| 119 | `Form[]` | `AddAllEquippedItemsBySlotToArray` | `Actor akActor, int[] aiSlots` | `global native` |
| 121 | `Bool` | `AddBasePerk` | `Actor akActor, Perk akPerk` | `global native` |
| 123 | `Bool` | `AddBaseSpell` | `Actor akActor, Spell akSpell` | `global native` |
| 125 | `void` | `BlendColorWithSkinTone` | `Actor akActor, ColorForm akColor, int aiBlendMode, bool abAutoLuminance, float afOpacity` | `global native` |
| 127 | `Bool` | `DamageActorHealth` | `Actor akActor, float afHealthDamage, Actor akSource` | `global native` |
| 129 | `void` | `DecapitateActor` | `Actor akActor` | `global native` |
| 131 | `void` | `FreezeActor` | `Actor akActor, int type, bool abFreeze` | `global native` |
| 133 | `void` | `KillNoWait` | `Actor akActor` | `global native` |
| 135 | `void` | `LaunchArrow` | `Actor akActor, Ammo akAmmo, Weapon akWeapon, string asNodeName = "", int aiSource = -1, ObjectReference akTarget = None, Potion akPoison = None` | `global native` |
| 137 | `void` | `LaunchSpell` | `Actor akActor, Spell akSpell, int aiSource` | `global native` |
| 140 | `void` | `MixColorWithSkinTone` | `Actor akActor, ColorForm akColor, bool abManualMode, float afPercentage` | `global native` |
| 142 | `void` | `RemoveAddedSpells` | `Actor akActor, string modName, Keyword[] keywords, bool abMatchAll` | `global native` |
| 144 | `void` | `RemoveArmorOfType` | `Actor akActor, int afArmorType, int[] aiSlotsToSkip, bool abEquippedOnly` | `global native` |
| 146 | `Bool` | `RemoveBasePerk` | `Actor akActor, Perk akPerk` | `global native` |
| 148 | `Bool` | `RemoveBaseSpell` | `Actor akActor, Spell akSpell` | `global native` |
| 150 | `void` | `ReplaceArmorTextureSet` | `Actor akActor, Armor akArmor, TextureSet akSourceTXST, TextureSet akTargetTXST, int aiTextureType = -1` | `global native` |
| 152 | `void` | `ReplaceFaceTextureSet` | `Actor akActor, TextureSet akMaleTXST, TextureSet akFemaleTXST, int aiTextureType = -1` | `global native` |
| 154 | `void` | `ReplaceSkinTextureSet` | `Actor akActor, TextureSet akMaleTXST, TextureSet akFemaleTXST, int aiSlotMask, int aiTextureType = -1` | `global native` |
| 156 | `Bool` | `ResetActor3D` | `Actor akActor, string asFolderName` | `global native` |
| 158 | `void` | `SetActorRefraction` | `Actor akActor, float afRefraction` | `global native` |
| 160 | `Bool` | `SetEquippedWeaponPoison` | `Actor akActor, Potion akPoison, bool abLeftHand` | `global native` |
| 162 | `Bool` | `SetEquippedWeaponPoisonCount` | `Actor akActor, int aiCount, bool abLeftHand` | `global native` |
| 164 | `void` | `SetHairColor` | `Actor akActor, ColorForm akColor` | `global native` |
| 166 | `void` | `SetHeadPartAlpha` | `Actor akActor, int aiPartType, float afAlpha` | `global native` |
| 168 | `void` | `SetHeadPartTextureSet` | `Actor akActor, TextureSet headpartTXST, int aiType` | `global native` |
| 170 | `void` | `SetLinearVelocity` | `Actor akActor, float afX, float afY, float afZ` | `global native` |
| 172 | `void` | `SetLocalGravityActor` | `Actor akActor, float afValue, bool abDisableGravityOnGround` | `global native` |
| 174 | `void` | `SetSkinAlpha` | `Actor akActor, float afAlpha` | `global native` |
| 176 | `void` | `SetSkinColor` | `Actor akActor, ColorForm akColor` | `global native` |
| 178 | `void` | `SetSoulTrapped` | `Actor akActor, bool abTrapped` | `global native` |
| 180 | `void` | `ToggleHairWigs` | `Actor akActor, bool abDisable` | `global native` |
| 182 | `void` | `UnequipAllOfType` | `Actor akActor, int afArmorType, int[] aiSlotsToSkip` | `global native` |
| 186 | `AssociationType` | `GetAssociationType` | `Actorbase akBase1, Actorbase akBase2` | `global native` |
| 188 | `LeveledItem` | `GetDeathItem` | `Actorbase akBase` | `global native` |
| 190 | `Perk` | `GetNthPerk` | `Actorbase akBase, int aiIndex` | `global native` |
| 192 | `int` | `GetPerkCount` | `Actorbase akBase` | `global native` |
| 194 | `Actorbase[]` | `GetRelationships` | `Actorbase akBase, AssociationType akAssocType` | `global native` |
| 196 | `void` | `SetDeathItem` | `Actorbase akBase, LeveledItem akLeveledItem` | `global native` |
| 200 | `Enchantment` | `GetBaseAmmoEnchantment` | `Ammo akAmmo` | `global native` |
| 204 | `string[]` | `GetScriptsAttachedToAlias` | `Alias akAlias` | `global native` |
| 206 | `Bool` | `IsScriptAttachedToAlias` | `Alias akAlias, string asScriptName` | `global native` |
| 210 | `FootstepSet` | `GetFootstepSet` | `ArmorAddon akArma` | `global native` |
| 212 | `void` | `SetFootstepSet` | `ArmorAddon akArma, FootstepSet akFootstepSet` | `global native` |
| 216 | `string[]` | `GetSortedActorNames` | `Keyword akKeyword, string asPlural = "(s` | `", bool abInvertKeyword) global native` |
| 218 | `string[]` | `GetSortedNPCNames` | `ActorBase[] aiActorBases, string asPlural = "(s` | `") global native` |
| 220 | `Bool` | `AddActorToArray` | `Actor akActor, Actor[] actorArray` | `global native` |
| 222 | `Bool` | `AddStringToArray` | `string asString, string[] asStrings` | `global native` |
| 224 | `int` | `ArrayStringCount` | `string asString, string[] asStrings` | `global native` |
| 226 | `string[]` | `SortArrayString` | `string[] asStrings` | `global native` |
| 230 | `void` | `ClearBookCantBeTakenFlag` | `Book akBook` | `global native` |
| 232 | `void` | `ClearReadFlag` | `Book akBook` | `global native` |
| 234 | `void` | `SetBookCantBeTakenFlag` | `Book akBook` | `global native` |
| 236 | `void` | `SetReadFlag` | `Book akBook` | `global native` |
| 240 | `float` | `GetCellNorthRotation` | `Cell akCell` | `global native` |
| 242 | `LightingTemplate` | `GetLightingTemplate` | `Cell akCell` | `global native` |
| 244 | `void` | `SetLightingTemplate` | `Cell akCell, LightingTemplate akLightingTemplate` | `global native` |
| 246 | `void` | `SetCellNorthRotation` | `Cell akCell, float afAngle` | `global native` |
| 250 | `void` | `GivePlayerSpellBook` | `` | `global native` |
| 252 | `void` | `DumpAnimationVariables` | `Actor akActor, string asAnimationVarPrefix` | `global native` |
| 256 | `int` | `CanActorBeDetected` | `Actor akActor` | `global native` |
| 258 | `int` | `CanActorDetect` | `Actor akActor` | `global native` |
| 260 | `Bool` | `IsDetectedByAnyone` | `Actor akActor` | `global native` |
| 262 | `void` | `ForceActorDetection` | `Actor akActor` | `global native` |
| 264 | `void` | `ForceActorDetecting` | `Actor akActor` | `global native` |
| 266 | `void` | `PreventActorDetection` | `Actor akActor` | `global native` |
| 268 | `void` | `PreventActorDetecting` | `Actor akActor` | `global native` |
| 270 | `void` | `ResetActorDetection` | `Actor akActor` | `global native` |
| 272 | `void` | `ResetActorDetecting` | `Actor akActor` | `global native` |
| 276 | `Debris` | `GetAddonModels` | `EffectShader akEffectShader` | `global native` |
| 278 | `int` | `GetEffectShaderTotalCount` | `EffectShader akEffectShader, bool abActive` | `global native` |
| 280 | `Bool` | `IsEffectShaderFlagSet` | `EffectShader akEffectShader, int aiFlag` | `global native` |
| 282 | `string` | `GetMembraneFillTexture` | `EffectShader akEffectShader` | `global native` |
| 284 | `string` | `GetMembraneHolesTexture` | `EffectShader akEffectShader` | `global native` |
| 286 | `string` | `GetMembranePaletteTexture` | `EffectShader akEffectShader` | `global native` |
| 288 | `float` | `GetParticleFullCount` | `EffectShader akEffectShader` | `global native` |
| 290 | `string` | `GetParticlePaletteTexture` | `EffectShader akEffectShader` | `global native` |
| 292 | `string` | `GetParticleShaderTexture` | `EffectShader akEffectShader` | `global native` |
| 294 | `float` | `GetParticlePersistentCount` | `EffectShader akEffectShader` | `global native` |
| 296 | `void` | `ClearEffectShaderFlag` | `EffectShader akEffectShader, int aiFlag` | `global native` |
| 298 | `void` | `SetAddonModels` | `EffectShader akEffectShader, Debris akDebris` | `global native` |
| 300 | `void` | `SetEffectShaderFlag` | `EffectShader akEffectShader, int aiFlag` | `global native` |
| 302 | `void` | `SetMembraneColorKeyData` | `EffectShader akEffectShader, int aiColorKey, int[] aiRGB, float afAlpha, float afTime` | `global native` |
| 304 | `void` | `SetMembraneFillTexture` | `EffectShader akEffectShader, string asTextureName` | `global native` |
| 306 | `void` | `SetMembraneHolesTexture` | `EffectShader akEffectShader, string asTextureName` | `global native` |
| 308 | `void` | `SetMembranePaletteTexture` | `EffectShader akEffectShader, string asTextureName` | `global native` |
| 310 | `void` | `SetParticleColorKeyData` | `EffectShader akEffectShader, int aiColorKey, int[] aiRGB, float afAlpha, float afTime` | `global native` |
| 312 | `void` | `SetParticleFullCount` | `EffectShader akEffectShader, float afParticleCount` | `global native` |
| 314 | `void` | `SetParticlePaletteTexture` | `EffectShader akEffectShader, string asTextureName` | `global native` |
| 316 | `void` | `SetParticlePersistentCount` | `EffectShader akEffectShader, float afParticleCount` | `global native` |
| 318 | `void` | `SetParticleShaderTexture` | `EffectShader akEffectShader, string asTextureName` | `global native` |
| 323 | `int` | `GetEnchantmentType` | `Enchantment akEnchantment` | `global native` |
| 325 | `void` | `AddMagicEffectToEnchantment` | `Enchantment akEnchantment, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0, string[] asConditionList` | `global native` |
| 327 | `void` | `AddEffectItemToEnchantment` | `Enchantment akEnchantment, Enchantment akEnchantmentToCopyFrom, int aiIndex, float afCost = -1.0` | `global native` |
| 329 | `void` | `RemoveMagicEffectFromEnchantment` | `Enchantment akEnchantment, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0` | `global native` |
| 331 | `void` | `RemoveEffectItemFromEnchantment` | `Enchantment akEnchantment, Enchantment akEnchantmentToMatchFrom, int aiIndex` | `global native` |
| 333 | `void` | `SetEnchantmentMagicEffect` | `Enchantment akEnchantment, MagicEffect akMagicEffect, int aiIndex` | `global native` |
| 338 | `ObjectReference` | `GetVendorFactionContainer` | `Faction akVendorFaction` | `global native` |
| 340 | `Actor[]` | `GetAllActorsInFaction` | `Faction akFaction` | `global native` |
| 344 | `Bool` | `SetFastTravelDisabled` | `bool abDisable` | `global native` |
| 346 | `Bool` | `SetFastTravelTargetFormID` | `int aiDestinationFormID` | `global native` |
| 348 | `Bool` | `SetFastTravelTargetRef` | `ObjectReference akDestination` | `global native` |
| 350 | `Bool` | `SetFastTravelTargetString` | `string asDestination` | `global native` |
| 352 | `float` | `SetFastTravelWaitTimeout` | `float afTimeout` | `global native` |
| 356 | `Bool` | `EvaluateConditionList` | `Form akForm, ObjectReference akActionRef, ObjectReference akTargetRef` | `global native` |
| 358 | `void` | `ClearRecordFlag` | `Form akForm, int aiFlag` | `global native` |
| 360 | `string[]` | `GetConditionList` | `Form akForm, int aiIndex = 0` | `global native` |
| 362 | `string` | `GetDescription` | `Form akForm` | `global native` |
| 364 | `string` | `GetFormEditorID` | `Form akForm` | `global native` |
| 366 | `string` | `GetFormModName` | `Form akForm, bool abLastModified` | `global native` |
| 368 | `string[]` | `GetScriptsAttachedToForm` | `Form akForm` | `global native` |
| 370 | `Bool` | `IsFormInMod` | `Form akForm, string asModName` | `global native` |
| 372 | `Bool` | `IsGeneratedForm` | `Form akForm` | `global native` |
| 374 | `Bool` | `IsRecordFlagSet` | `Form akForm, int aiFlag` | `global native` |
| 376 | `Bool` | `IsScriptAttachedToForm` | `Form akForm, string asScriptName` | `global native` |
| 378 | `void` | `SetRecordFlag` | `Form akForm, int aiFlag` | `global native` |
| 380 | `void` | `AddKeywordToForm` | `Form akForm, Keyword akKeyword` | `global native` |
| 382 | `void` | `MarkItemAsFavorite` | `Form akForm` | `global native` |
| 384 | `void` | `RemoveConditionList` | `Form akForm, int aiIndex, string[] asConditionList` | `global native` |
| 386 | `void` | `ReplaceKeywordOnForm` | `Form akForm, Keyword akKeywordAdd, Keyword akKeywordRemove` | `global native` |
| 388 | `Bool` | `RemoveKeywordOnForm` | `Form akForm, Keyword akKeyword` | `global native` |
| 390 | `void` | `SetConditionList` | `Form akForm, int aiIndex, string[] asConditionList` | `global native` |
| 392 | `void` | `UnmarkItemAsFavorite` | `Form akForm` | `global native` |
| 396 | `int` | `GetFurnitureType` | `Furniture akFurniture` | `global native` |
| 400 | `String[]` | `GetActivePlugins` | `` | `global native` |
| 402 | `Enchantment[]` | `GetAllEnchantments` | `Keyword[] akKeywords = None` | `global native` |
| 404 | `Form[]` | `GetAllForms` | `int aiFormType, Keyword[] akKeywords = None` | `global native` |
| 406 | `Race[]` | `GetAllRaces` | `Keyword[] akKeywords = None` | `global native` |
| 408 | `Spell[]` | `GetAllSpells` | `Keyword[] akKeywords = None, bool abIsPlayable = false` | `global native` |
| 410 | `Actor[]` | `GetActorsByProcessingLevel` | `int aiLevel` | `global native` |
| 412 | `Form[]` | `GetAllFormsInMod` | `string asModName, int aiFormType, Keyword[] akKeywords = None` | `global native` |
| 414 | `Enchantment[]` | `GetAllEnchantmentsInMod` | `string asModName, Keyword[] akKeywords = None` | `global native` |
| 416 | `Race[]` | `GetAllRacesInMod` | `string asModName, Keyword[] akKeywords = None` | `global native` |
| 418 | `Spell[]` | `GetAllSpellsInMod` | `string asModName, Keyword[] akKeywords = None, bool abIsPlayable = false` | `global native` |
| 420 | `Cell[]` | `GetAttachedCells` | `` | `global native` |
| 422 | `Form` | `GetFormFromEditorID` | `string asEditorID` | `global native` |
| 424 | `int` | `GetGameSettingBool` | `string asGameSetting` | `global native` |
| 426 | `Bool` | `GetGodMode` | `` | `global native` |
| 428 | `float` | `GetLandHeight` | `float afPosX, float afPosY, float afPosZ` | `global native` |
| 430 | `string` | `GetLandMaterialType` | `float afPosX, float afPosY, float afPosZ` | `global native` |
| 432 | `float[]` | `GetLocalGravity` | `` | `global native` |
| 434 | `int` | `GetNumActorsInHigh` | `` | `global native` |
| 436 | `Actor[]` | `GetPlayerFollowers` | `` | `global native` |
| 438 | `string` | `GetSurfaceMaterialType` | `float afX, float afY, float afZ` | `global native` |
| 440 | `Bool` | `IsPluginFound` | `string akName` | `global native` |
| 442 | `Bool` | `IsSurvivalModeActive` | `` | `global native` |
| 444 | `void` | `ClearCachedFactionFightReactions` | `` | `global native` |
| 446 | `void` | `SetLocalGravity` | `float afXAxis, float afYAxis, float afZAxis` | `global native` |
| 448 | `void` | `UpdateCrosshairs` | `` | `global native` |
| 453 | `string` | `GetHazardArt` | `Hazard akHazard` | `global native` |
| 455 | `ImageSpaceModifier` | `GetHazardIMOD` | `Hazard akHazard` | `global native` |
| 457 | `float` | `GetHazardIMODRadius` | `Hazard akHazard` | `global native` |
| 459 | `ImpactDataSet` | `GetHazardIPDS` | `Hazard akHazard` | `global native` |
| 461 | `float` | `GetHazardLifetime` | `Hazard akHazard` | `global native` |
| 463 | `Light` | `GetHazardLight` | `Hazard akHazard` | `global native` |
| 465 | `int` | `GetHazardLimit` | `Hazard akHazard` | `global native` |
| 467 | `float` | `GetHazardRadius` | `Hazard akHazard` | `global native` |
| 469 | `SoundDescriptor` | `GetHazardSound` | `Hazard akHazard` | `global native` |
| 471 | `Spell` | `GetHazardSpell` | `Hazard akHazard` | `global native` |
| 473 | `float` | `GetHazardTargetInterval` | `Hazard akHazard` | `global native` |
| 475 | `Bool` | `IsHazardFlagSet` | `Hazard akHazard, int aiFlag` | `global native` |
| 477 | `void` | `ClearHazardFlag` | `Hazard akHazard, int aiFlag` | `global native` |
| 479 | `void` | `SetHazardArt` | `Hazard akHazard, string asPath` | `global native` |
| 481 | `void` | `SetHazardFlag` | `Hazard akHazard, int aiFlag` | `global native` |
| 483 | `void` | `SetHazardIMOD` | `Hazard akHazard, ImageSpaceModifier akIMOD` | `global native` |
| 485 | `void` | `SetHazardIMODRadius` | `Hazard akHazard, float afRadius` | `global native` |
| 487 | `void` | `SetHazardIPDS` | `Hazard akHazard, ImpactDataSet akIPDS` | `global native` |
| 489 | `void` | `SetHazardLifetime` | `Hazard akHazard, float afLifetime` | `global native` |
| 491 | `void` | `SetHazardLight` | `Hazard akHazard, Light akLight` | `global native` |
| 493 | `void` | `SetHazardLimit` | `Hazard akHazard, int aiLimit` | `global native` |
| 495 | `void` | `SetHazardRadius` | `Hazard akHazard, float afRadius` | `global native` |
| 497 | `void` | `SetHazardSound` | `Hazard akHazard, SoundDescriptor akSound` | `global native` |
| 499 | `void` | `SetHazardSpell` | `Hazard akHazard, Spell akspell` | `global native` |
| 501 | `void` | `SetHazardTargetInterval` | `Hazard akHazard, float afInterval` | `global native` |
| 505 | `string` | `GetAnimationEventName` | `Idle akIdle` | `global native` |
| 507 | `string` | `GetAnimationFileName` | `Idle akIdle` | `global native` |
| 511 | `ColorForm` | `GetLightColor` | `Light akLight` | `global native` |
| 513 | `float` | `GetLightFade` | `Light akLight` | `global native` |
| 515 | `float` | `GetLightFOV` | `Light akLight` | `global native` |
| 517 | `float` | `GetLightRadius` | `Light akLight` | `global native` |
| 519 | `int[]` | `GetLightRGB` | `Light akLight` | `global native` |
| 521 | `float` | `GetLightShadowDepthBias` | `ObjectReference akLightObject` | `global native` |
| 523 | `int` | `GetLightType` | `Light akLight` | `global native` |
| 525 | `void` | `SetLightColor` | `Light akLight, ColorForm akColorform` | `global native` |
| 527 | `void` | `SetLightFade` | `Light akLight, float afRange` | `global native` |
| 529 | `void` | `SetLightFOV` | `Light akLight, float afFOV` | `global native` |
| 531 | `void` | `SetLightRadius` | `Light akLight, float afRadius` | `global native` |
| 533 | `void` | `SetLightRGB` | `Light akLight, int[] aiRGB` | `global native` |
| 535 | `void` | `SetLightShadowDepthBias` | `ObjectReference akLightObject, float afDepthBias` | `global native` |
| 537 | `void` | `SetLightType` | `Light akLight, int aiLightType` | `global native` |
| 541 | `Form[]` | `GetContentFromLeveledItem` | `LeveledItem akLeveledItem, ObjectReference akRef` | `global native` |
| 545 | `Form[]` | `GetContentFromLeveledActor` | `LeveledActor akLeveledActor, ObjectReference akRef` | `global native` |
| 549 | `Form[]` | `GetContentFromLeveledSpell` | `LeveledSpell akLeveledSpell, ObjectReference akRef` | `global native` |
| 553 | `Location` | `GetParentLocation` | `Location akLoc` | `global native` |
| 555 | `void` | `SetParentLocation` | `Location akLoc, Location akNewLoc` | `global native` |
| 559 | `Form` | `GetAssociatedForm` | `MagicEffect akMagicEffect` | `global native` |
| 561 | `int` | `GetEffectArchetypeAsInt` | `MagicEffect akMagicEffect` | `global native` |
| 563 | `string` | `GetEffectArchetypeAsString` | `MagicEffect akMagicEffect` | `global native` |
| 565 | `string` | `GetPrimaryActorValue` | `MagicEffect akMagicEffect` | `global native` |
| 567 | `string` | `GetSecondaryActorValue` | `MagicEffect akMagicEffect` | `global native` |
| 569 | `SoundDescriptor` | `GetMagicEffectSound` | `MagicEffect akMagicEffect, int aiType` | `global native` |
| 571 | `void` | `SetAssociatedForm` | `MagicEffect akMagicEffect, Form akForm` | `global native` |
| 573 | `void` | `SetMagicEffectSound` | `MagicEffect akMagicEffect, SoundDescriptor akSoundDescriptor, int aiType` | `global native` |
| 577 | `Bool` | `ActorInRangeHasEffect` | `ObjectReference akRef, float afRadius, MagicEffect akEffect, bool abIgnorePlayer` | `global native` |
| 579 | `Form[]` | `AddAllItemsToArray` | `ObjectReference akRef, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false` | `global native` |
| 581 | `void` | `AddAllItemsToList` | `ObjectReference akRef, Formlist akList, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false` | `global native` |
| 583 | `Form[]` | `AddItemsOfTypeToArray` | `ObjectReference akRef, int aiFormType, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false` | `global native` |
| 585 | `void` | `AddItemsOfTypeToList` | `ObjectReference akRef, Formlist akList, int aiFormType, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false` | `global native` |
| 587 | `Form[]` | `AddItemsWithKeywordToArray` | `ObjectReference akRef, Keyword akKeyword, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false` | `global native` |
| 589 | `void` | `AddItemsWithKeywordToList` | `ObjectReference akRef, Formlist akList, Keyword akKeyword, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false` | `global native` |
| 591 | `Form[]` | `AddItemsWithKeywordStringToArray` | `ObjectReference akRef, String asKeywordString, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false` | `global native` |
| 593 | `void` | `AddItemsWithKeywordStringToList` | `ObjectReference akRef, Formlist akList, String asKeywordString, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false` | `global native` |
| 595 | `ObjectReference[]` | `FindAllReferencesOfFormType` | `ObjectReference akRef, int formType, float afRadius` | `global native` |
| 597 | `ObjectReference[]` | `FindAllReferencesWithKeyword` | `ObjectReference akRef, Form keywordOrList, float afRadius, bool abMatchAll` | `global native` |
| 599 | `ObjectReference[]` | `FindAllReferencesOfType` | `ObjectReference akRef, Form akFormOrList, float afRadius` | `global native` |
| 601 | `Form` | `FindFirstItemInList` | `ObjectReference akRef, FormList akList` | `global native` |
| 603 | `Quest[]` | `GetActiveAssociatedQuests` | `ObjectReference akRef, Bool abAllowEmptyStages = True` | `global native` |
| 605 | `ObjectReference[]` | `GetActivateChildren` | `ObjectReference akRef` | `global native` |
| 607 | `string` | `GetActiveGamebryoAnimation` | `ObjectReference akRef` | `global native` |
| 609 | `ActiveMagicEffect[]` | `GetActiveMagicEffects` | `ObjectReference akRef, MagicEffect akMagicEffect` | `global native` |
| 611 | `Quest[]` | `GetAllAssociatedQuests` | `ObjectReference akRef, Bool abAllowEmptyStages = True` | `global native` |
| 613 | `Actor` | `GetActorCause` | `ObjectReference akRef` | `global native` |
| 615 | `Art[]` | `GetAllArtObjects` | `ObjectReference akRef` | `global native` |
| 617 | `EffectShader[]` | `GetAllEffectShaders` | `ObjectReference akRef` | `global native` |
| 619 | `Actor` | `GetClosestActorFromRef` | `ObjectReference akRef, bool abIgnorePlayer` | `global native` |
| 621 | `float` | `GetEffectShaderDuration` | `ObjectReference akRef, EffectShader akShader` | `global native` |
| 623 | `ObjectReference` | `GetDoorDestination` | `ObjectReference akRef` | `global native` |
| 625 | `ObjectReference[]` | `GetLinkedChildren` | `ObjectReference akRef, Keyword akKeyword` | `global native` |
| 627 | `Form[]` | `GetMagicEffectSource` | `ObjectReference akRef, MagicEffect akEffect` | `global native` |
| 629 | `string[]` | `GetMaterialType` | `ObjectReference akRef, string asNodeName = ""` | `global native` |
| 631 | `int` | `GetMotionType` | `ObjectReference akRef` | `global native` |
| 633 | `int` | `GetNumActorsWithEffectInRange` | `ObjectReference akRef, float afRadius, MagicEffect akEffect, bool abignorePlayer` | `global native` |
| 635 | `Actor` | `GetRandomActorFromRef` | `ObjectReference akRef, float afRadius, bool abIgnorePlayer` | `global native` |
| 637 | `Form[]` | `GetQuestItems` | `ObjectReference akRef, bool abNoEquipped = false, bool abNoFavorited = false` | `global native` |
| 639 | `Alias[]` | `GetRefAliases` | `ObjectReference akRef` | `global native` |
| 641 | `int` | `GetRefCount` | `ObjectReference akRef` | `global native` |
| 643 | `int` | `GetStoredSoulSize` | `ObjectReference akRef` | `global native` |
| 645 | `int` | `HasArtObject` | `ObjectReference akRef, Art akArtObject, bool abActive = false` | `global native` |
| 647 | `int` | `HasEffectShader` | `ObjectReference akRef, EffectShader akShader, bool abActive = false` | `global native` |
| 649 | `Bool` | `HasNiExtraData` | `ObjectReference akRef, string asName` | `global native` |
| 651 | `Bool` | `IsCasting` | `ObjectReference akRef, Form akMagicItem` | `global native` |
| 653 | `Bool` | `IsLoadDoor` | `ObjectReference akRef` | `global native` |
| 655 | `Bool` | `IsQuestItem` | `ObjectReference akRef` | `global native` |
| 657 | `Bool` | `IsRefInWater` | `ObjectReference akRef` | `global native` |
| 659 | `Bool` | `IsRefNodeInWater` | `ObjectReference akRef, String asNodeName` | `global native` |
| 661 | `Bool` | `IsRefUnderwater` | `ObjectReference akRef` | `global native` |
| 663 | `Bool` | `IsVIP` | `ObjectReference akRef` | `global native` |
| 665 | `void` | `ApplyMaterialShader` | `ObjectReference akRef, MaterialObject akMatObject, float directionalThresholdAngle` | `global native` |
| 667 | `void` | `AddKeywordToRef` | `ObjectReference akRef, Keyword akKeyword` | `global native` |
| 669 | `void` | `CastEx` | `ObjectReference akRef, Form akSpell, ObjectReference akTarget, Actor akBlameActor, int aiSource` | `global native` |
| 671 | `void` | `MoveToNearestNavmeshLocation` | `ObjectReference akRef` | `global native` |
| 673 | `void` | `RemoveAllModItems` | `ObjectReference akRef, string asModName, bool abOnlyUnequip = false` | `global native` |
| 675 | `void` | `RemoveListFromContainer` | `ObjectReference akRef, FormList akList, bool abNoEquipped = false, bool abNoFavorited = false, bool abNoQuestItem = false, ObjectReference akDestination = None` | `global native` |
| 677 | `Bool` | `RemoveKeywordFromRef` | `ObjectReference akRef, Keyword akKeyword` | `global native` |
| 679 | `void` | `ReplaceKeywordOnRef` | `ObjectReference akRef, Keyword akKeywordAdd, Keyword akKeywordRemove` | `global native` |
| 681 | `void` | `PlayDebugShader` | `ObjectReference akRef, float[] afRGBA` | `global native` |
| 683 | `void` | `ScaleObject3D` | `ObjectReference akRef, string asNodeName, float afScale` | `global native` |
| 685 | `void` | `SetBaseObject` | `ObjectReference akRef, Form akBaseObject` | `global native` |
| 687 | `void` | `SetCollisionLayer` | `ObjectReference akRef, string asNodeName, int aiCollisionLayer` | `global native` |
| 689 | `Bool` | `SetDoorDestination` | `ObjectReference akRef, ObjectReference akDoor` | `global native` |
| 691 | `void` | `SetEffectShaderDuration` | `ObjectReference akRef, EffectShader akShader, float afTime, bool abAbsolute` | `global native` |
| 693 | `void` | `SetKey` | `ObjectReference akRef, Key akKey` | `global native` |
| 695 | `void` | `SetLinkedRef` | `ObjectReference akRef, ObjectReference akTargetRef, Keyword akKeyword = None` | `global native` |
| 697 | `void` | `SetMaterialType` | `ObjectReference akRef, string asNewMaterial, string asOldMaterial = "", string asNodeName = ""` | `global native` |
| 699 | `void` | `SetupBodyPartGeometry` | `ObjectReference akRef, actor akActor` | `global native` |
| 701 | `void` | `SetShaderType` | `ObjectReference akRef, ObjectReference akTemplate, string asDiffusePath, int aiShaderType, int aiTextureType, bool abNoWeapons, bool abNoAlphaProperty` | `global native` |
| 703 | `void` | `StopAllShaders` | `ObjectReference akRef` | `global native` |
| 705 | `void` | `StopArtObject` | `ObjectReference akRef, Art akArt` | `global native` |
| 707 | `void` | `ToggleChildNode` | `ObjectReference akRef, string asNodeName, bool abDisable` | `global native` |
| 709 | `void` | `UpdateHitEffectArtNode` | `ObjectReference akRef, Art akArt, string asNewNode, float[] afTranslate, float[] afRotate, float afRelativeScale = 1.0` | `global native` |
| 713 | `int` | `GetPackageType` | `Package akPackage` | `global native` |
| 715 | `Idle[]` | `GetPackageIdles` | `Package akPackage` | `global native` |
| 717 | `void` | `AddPackageIdle` | `Package akPackage, Idle akIdle` | `global native` |
| 719 | `void` | `RemovePackageIdle` | `Package akPackage, Idle akIdle` | `global native` |
| 724 | `int[]` | `GetPapyrusExtenderVersion` | `` | `global native` |
| 728 | `void` | `AddMagicEffectToPotion` | `Potion akPotion, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0, string[] asConditionList` | `global native` |
| 730 | `void` | `AddEffectItemToPotion` | `Potion akPotion, Potion akPotionToCopyFrom, int aiIndex, float afCost = -1.0` | `global native` |
| 732 | `void` | `RemoveMagicEffectFromPotion` | `Potion akPotion, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0` | `global native` |
| 734 | `void` | `RemoveEffectItemFromPotion` | `Potion akPotion, Potion akPotionToMatchFrom, int aiIndex` | `global native` |
| 736 | `void` | `SetPotionMagicEffect` | `Potion akPotion, MagicEffect akMagicEffect, int aiIndex` | `global native` |
| 740 | `float` | `GetProjectileGravity` | `Projectile akProjectile` | `global native` |
| 742 | `float` | `GetProjectileImpactForce` | `Projectile akProjectile` | `global native` |
| 744 | `float` | `GetProjectileRange` | `Projectile akProjectile` | `global native` |
| 746 | `float` | `GetProjectileSpeed` | `Projectile akProjectile` | `global native` |
| 748 | `int` | `GetProjectileType` | `Projectile akProjectile` | `global native` |
| 750 | `void` | `SetProjectileGravity` | `Projectile akProjectile, float afGravity` | `global native` |
| 752 | `void` | `SetProjectileImpactForce` | `Projectile akProjectile, float afImpactForce` | `global native` |
| 754 | `void` | `SetProjectileRange` | `Projectile akProjectile, float afRange` | `global native` |
| 756 | `void` | `SetProjectileSpeed` | `Projectile akProjectile, float afSpeed` | `global native` |
| 760 | `int[]` | `GetAllQuestObjectives` | `Quest akQuest` | `global native` |
| 762 | `int[]` | `GetAllQuestStages` | `Quest akQuest` | `global native` |
| 764 | `void` | `SetObjectiveText` | `Quest akQuest, string asText, int aiIndex` | `global native` |
| 768 | `Actor[]` | `GetActorsInScene` | `Scene akScene` | `global native` |
| 770 | `bool` | `IsActorInScene` | `Scene akScene, Actor akActor` | `global native` |
| 774 | `void` | `AddMagicEffectToScroll` | `Scroll akScroll, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0, string[] asConditionList` | `global native` |
| 776 | `void` | `AddEffectItemToScroll` | `Scroll akScroll, Scroll akScrollToCopyFrom, int aiIndex, float afCost = -1.0` | `global native` |
| 778 | `void` | `RemoveMagicEffectFromScroll` | `Scroll akScroll, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0` | `global native` |
| 780 | `void` | `RemoveEffectItemFromScroll` | `Scroll akScroll, Scroll akScrollToMatchFrom, int aiIndex` | `global native` |
| 782 | `void` | `SetScrollMagicEffect` | `Scroll akScroll, MagicEffect akMagicEffect, int aiIndex` | `global native` |
| 786 | `void` | `SetSoundDescriptor` | `Sound akSound, SoundDescriptor akSoundDescriptor` | `global native` |
| 790 | `int` | `GetSpellType` | `Spell akSpell` | `global native` |
| 792 | `void` | `AddMagicEffectToSpell` | `Spell akSpell, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0, string[] asConditionList` | `global native` |
| 794 | `void` | `AddEffectItemToSpell` | `Spell akSpell, Spell akSpellToCopyFrom, int aiIndex, float afCost = -1.0` | `global native` |
| 796 | `void` | `RemoveMagicEffectFromSpell` | `Spell akSpell, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0` | `global native` |
| 798 | `void` | `RemoveEffectItemFromSpell` | `Spell akSpell, Spell akSpellToMatchFrom, int aiIndex` | `global native` |
| 800 | `void` | `SetSpellCastingType` | `Spell akSpell, int aiType` | `global native` |
| 802 | `void` | `SetSpellDeliveryType` | `Spell akSpell, int aiType` | `global native` |
| 804 | `void` | `SetSpellType` | `Spell akSpell, int aiType` | `global native` |
| 806 | `void` | `SetSpellMagicEffect` | `Spell akSpell, MagicEffect akMagicEffect, int aiIndex` | `global native` |
| 810 | `string` | `IntToString` | `int aiValue, bool abHex` | `global native` |
| 812 | `int` | `StringToInt` | `string asString` | `global native` |
| 816 | `ObjectReference` | `GetMenuContainer` | `` | `global native` |
| 818 | `void` | `HideMenu` | `string asMenuName` | `global native` |
| 820 | `Bool` | `IsShowingMenus` | `` | `global native` |
| 822 | `void` | `ShowBookMenu` | `Book akBook` | `global native` |
| 824 | `void` | `ShowMenu` | `string asMenuName` | `global native` |
| 826 | `void` | `ToggleOpenSleepWaitMenu` | `bool abOpenSleepMenu` | `global native` |
| 828 | `void` | `ShowTutorialMessage` | `Message akMessage` | `global native` |
| 832 | `float` | `GenerateRandomFloat` | `float afMin, float afMax` | `global native` |
| 834 | `int` | `GenerateRandomInt` | `int afMin, int afMax` | `global native` |
| 836 | `int[]` | `GetSystemTime` | `` | `global native` |
| 840 | `Art` | `GetArtObject` | `VisualEffect akEffect` | `global native` |
| 842 | `int` | `GetArtObjectTotalCount` | `VisualEffect akEffect, bool abActive` | `global native` |
| 844 | `void` | `SetArtObject` | `VisualEffect akEffect, Art akArt` | `global native` |
| 848 | `float` | `GetWindSpeedAsFloat` | `Weather akWeather` | `global native` |
| 850 | `int` | `GetWindSpeedAsInt` | `Weather akWeather` | `global native` |
| 852 | `int` | `GetWeatherType` | `Weather akWeather = None` | `global native` |

## Implementation routing

Before creating a custom native DLL, search this catalog for existing operations in these families:

- actor state, AI, race and combat;
- armor, weapons and worn-item instance state;
- base-form/keyword/form-list mutation;
- cell/worldspace/weather/environment queries;
- ColorForm/light/material/shader manipulation;
- ConstructibleObject and crafting access;
- EffectShader/Art/VisualEffect control;
- furniture and idle inspection;
- leveled-item/actor/spell resolution;
- MagicEffect archetype and sound access;
- ObjectReference inventory, linked refs, doors, collision, materials and node state;
- Package data;
- potion/scroll/spell EffectItem mutation;
- projectile physics;
- quest stages/objectives and scene actors;
- menus and utility/system-time operations.

## Automation rules for Agent OS

When a mod idea asks for behavior that might be achievable through Papyrus Extender:

1. Search exact function/event names before proposing a custom SKSE plugin.
2. Check whether the function changes:
   - a base form;
   - one ObjectReference;
   - an inventory instance;
   - loaded 3D/material state;
   - save-persistent state.
3. Check required object lifecycle (loaded 3D, active effect, alias, etc.).
4. Prefer extender events over frequent polling where a matching event exists.
5. Treat functions that mutate shared base forms as globally visible to every reference using that base.
6. Treat node/material/3D calls as loaded-state operations and guard accordingly.
7. Record Papyrus Extender version/blob in generated mod manifests.
8. Add runtime smoke tests around native calls that can fail when the provider DLL is absent or version-incompatible.
9. Keep PSC compile stubs and runtime DLL compatibility as separate validation checks.

## Related modules

- `papyrus-core-api-map.md`
- `papyrus-event-registration-messaging.md`
- `papyrus-language-semantics-states-properties-fragments.md`
- `actor-process-levels-simulation.md`
- `extradata-type-catalog-commonlib.md`
- `visual-effects-artobjects-particles.md`
- `skse-plugin-lifecycle-loading.md`
