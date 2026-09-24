# powerofthree's Papyrus Extender v6.5.2 — Function Declaration Catalog

Imported: 2026-09-24
Source: `powerof3/PapyrusExtenderSSE` tag `v6.5.2`
Source file: `Papyrus/Source/scripts/PO3_SKSEFunctions.psc`
Source blob SHA: `87fcdd7c399801c92449c59ddb46090b2cc93214`
Source declarations parsed: **379**
Status: finite source-derived declaration catalog

## Important count distinction

The upstream README advertises **374 functions** for v6.5.2. This PSC contains **379 native function declarations**, including **59 declarations under the source's explicit `DEPRECATED` section**.

Therefore this file is a **source declaration catalog**, not a claim that all 379 declarations should be counted as current user-facing functions.

## Section counts

| Source section | Declarations |
|---|---:|
| ACTIVE EFFECT | 3 |
| ACTOR | 23 |
| DEPRECATED | 59 |
| ACTORBASE | 6 |
| AMMO | 1 |
| ALIAS | 2 |
| ARMOR/ADDONS | 2 |
| ARRAYS | 6 |
| BOOK | 4 |
| CELL | 4 |
| DEBUG | 2 |
| DETECTION | 9 |
| EFFECTSHADER | 22 |
| ENCHANTMENT | 6 |
| FACTION | 2 |
| FASTTRAVEL | 5 |
| FORM | 19 |
| FURNITURE | 1 |
| GAME | 25 |
| HAZARD | 25 |
| IDLE | 2 |
| LIGHT | 14 |
| LEVELED ITEM | 1 |
| LEVELED NPC | 1 |
| LEVELED SPELL | 1 |
| LOCATION | 2 |
| MAGIC EFFECTS | 8 |
| OBJECTREFERENCES | 67 |
| PACKAGES | 4 |
| PAPYRUS EXTENDER | 1 |
| POTION | 5 |
| PROJECTILES | 9 |
| QUEST | 3 |
| SCENE | 2 |
| SCROLL | 5 |
| SOUND | 1 |
| SPELL | 9 |
| STRINGS | 9 |
| UTILITY | 3 |
| VISUALEFFECTS | 3 |
| WEATHER | 3 |

## Complete declaration index

| Section | Line | Function | Exact declaration |
|---|---:|---|---|
| ACTIVE EFFECT | 8 | `GetScriptsAttachedToActiveEffect` | `string[] Function GetScriptsAttachedToActiveEffect(ActiveMagicEffect akActiveEffect) global native` |
| ACTIVE EFFECT | 10 | `IsScriptAttachedToActiveEffect` | `Bool Function IsScriptAttachedToActiveEffect(ActiveMagicEffect akActiveEffect, string asScriptName) global native` |
| ACTIVE EFFECT | 12 | `GetActiveEffectSpell` | `Form Function GetActiveEffectSpell(ActiveMagicEffect akActiveEffect)  global native` |
| ACTOR | 17 | `GetActiveEffects` | `MagicEffect[] Function GetActiveEffects(Actor akActor, bool abShowInactive = false) global native` |
| ACTOR | 19 | `GetActorAlpha` | `float Function GetActorAlpha(Actor akActor) global native` |
| ACTOR | 21 | `GetActorKnockState` | `int Function GetActorKnockState(Actor akActor) global native` |
| ACTOR | 23 | `GetActorRefraction` | `float Function GetActorRefraction(Actor akActor) global native` |
| ACTOR | 25 | `GetActorState` | `int Function GetActorState(Actor akActor) global native` |
| ACTOR | 27 | `GetActorSoulSize` | `int Function GetActorSoulSize(Actor akActor) global native` |
| ACTOR | 29 | `GetActorValueModifier` | `float Function GetActorValueModifier(Actor akActor, int aiModifier, string asActorValue) global native` |
| ACTOR | 31 | `GetAllActorPlayableSpells` | `Spell[] Function GetAllActorPlayableSpells(Actor akActor) global native` |
| ACTOR | 33 | `GetCriticalStage` | `int Function GetCriticalStage(Actor akActor) global native` |
| ACTOR | 35 | `GetCombatAllies` | `Actor[] Function GetCombatAllies(Actor akActor) global native` |
| ACTOR | 37 | `GetCombatTargets` | `Actor[] Function GetCombatTargets(Actor akActor) global native` |
| ACTOR | 39 | `GetCommandedActors` | `Actor[] Function GetCommandedActors(Actor akActor) global native` |
| ACTOR | 41 | `GetCommandingActor` | `Actor Function GetCommandingActor(Actor akActor) global native` |
| ACTOR | 43 | `GetEditorLocationX` | `float Function GetEditorLocationX(Actor akActor) global native` |
| ACTOR | 45 | `GetEditorLocationY` | `float Function GetEditorLocationY(Actor akActor) global native` |
| ACTOR | 47 | `GetEditorLocationZ` | `float Function GetEditorLocationZ(Actor akActor) global native` |
| ACTOR | 49 | `GetEditorLocationAngle` | `float Function GetEditorLocationAngle(Actor akActor) global native` |
| ACTOR | 51 | `GetEquippedAmmo` | `Ammo Function GetEquippedAmmo(Actor akActor) global native` |
| ACTOR | 53 | `GetEquippedAmmoEnchantment` | `Enchantment Function GetEquippedAmmoEnchantment(Actor akActor) global native` |
| ACTOR | 55 | `GetEquippedWeaponIsPoisoned` | `Bool Function GetEquippedWeaponIsPoisoned(Actor akActor, bool abLeftHand) global native` |
| ACTOR | 57 | `GetEquippedWeaponPoison` | `Potion Function GetEquippedWeaponPoison(Actor akActor, bool abLeftHand) global native` |
| ACTOR | 59 | `GetEquippedWeaponPoisonCount` | `int Function GetEquippedWeaponPoisonCount(Actor akActor, bool abLeftHand) global native` |
| ACTOR | 61 | `GetEquippedWeight` | `float Function GetEquippedWeight(Actor akActor) global native` |
| DEPRECATED | 64 | `GetHairColor` | `ColorForm Function GetHairColor(Actor akActor) global native` |
| DEPRECATED | 66 | `GetHairRGB` | `int[] Function GetHairRGB(Actor akActor) global native` |
| DEPRECATED | 68 | `GetHeadPartTextureSet` | `TextureSet Function GetHeadPartTextureSet(Actor akActor, int aiType) global native` |
| DEPRECATED | 70 | `GetLocalGravityActor` | `float Function GetLocalGravityActor(Actor akActor) global native` |
| DEPRECATED | 72 | `GetMount` | `Actor Function GetMount(Actor akActor) global native` |
| DEPRECATED | 74 | `GetObjectUnderFeet` | `ObjectReference Function GetObjectUnderFeet(Actor akActor) global native` |
| DEPRECATED | 76 | `GetOffersServices` | `Bool Function GetOffersServices(Actor akActor) global native` |
| DEPRECATED | 78 | `GetRider` | `Actor Function GetRider(Actor akActor) global native` |
| DEPRECATED | 80 | `GetRunningPackage` | `Package Function GetRunningPackage(Actor akActor) global native` |
| DEPRECATED | 83 | `GetSkinColor` | `ColorForm Function GetSkinColor(Actor akActor) global native` |
| DEPRECATED | 85 | `GetSkinRGB` | `int[] Function GetSkinRGB(Actor akActor) global native` |
| DEPRECATED | 87 | `GetTimeDead` | `float Function GetTimeDead(Actor akActor) global native` |
| DEPRECATED | 89 | `GetTimeOfDeath` | `float Function GetTimeOfDeath(Actor akActor) global native` |
| DEPRECATED | 91 | `GetVendorFaction` | `Faction Function GetVendorFaction(Actor akActor) global native` |
| DEPRECATED | 93 | `HasActiveMagicEffect` | `Bool Function HasActiveMagicEffect(Actor akActor, MagicEffect akEffect) global native` |
| DEPRECATED | 95 | `HasActiveSpell` | `Bool Function HasActiveSpell(Actor akActor, Spell akSpell) global native` |
| DEPRECATED | 97 | `HasDeferredKill` | `Bool Function HasDeferredKill(Actor akActor) global native` |
| DEPRECATED | 99 | `HasMagicEffectWithArchetype` | `Bool Function HasMagicEffectWithArchetype(Actor akActor, string asArchetype) global native` |
| DEPRECATED | 101 | `HasSkin` | `Bool Function HasSkin(Actor akActor, Armor akArmorToCheck) global native` |
| DEPRECATED | 103 | `IsActorInWater` | `Bool Function IsActorInWater(Actor akActor) global native` |
| DEPRECATED | 105 | `IsActorUnderwater` | `Bool Function IsActorUnderwater(Actor akActor) global native` |
| DEPRECATED | 107 | `IsLimbGone` | `Bool Function IsLimbGone(Actor akActor, int aiLimb) global native` |
| DEPRECATED | 109 | `IsPowerAttacking` | `Bool Function IsPowerAttacking(Actor akActor) global native` |
| DEPRECATED | 111 | `IsQuadruped` | `Bool Function IsQuadruped(Actor akActor) global native` |
| DEPRECATED | 113 | `IsSoulTrapped` | `Bool Function IsSoulTrapped(Actor akActor) global native` |
| DEPRECATED | 115 | `ApplyPoisonToEquippedWeapon` | `Bool Function ApplyPoisonToEquippedWeapon(Actor akActor, Potion akPoison, int aiCount, bool abLeftHand) global native` |
| DEPRECATED | 117 | `AddAllEquippedItemsToArray` | `Form[] Function AddAllEquippedItemsToArray(Actor akActor) global native` |
| DEPRECATED | 119 | `AddAllEquippedItemsBySlotToArray` | `Form[] Function AddAllEquippedItemsBySlotToArray(Actor akActor, int[] aiSlots) global native` |
| DEPRECATED | 121 | `AddBasePerk` | `Bool Function AddBasePerk(Actor akActor, Perk akPerk) global native` |
| DEPRECATED | 123 | `AddBaseSpell` | `Bool Function AddBaseSpell(Actor akActor, Spell akSpell) global native` |
| DEPRECATED | 125 | `BlendColorWithSkinTone` | `Function BlendColorWithSkinTone(Actor akActor, ColorForm akColor, int aiBlendMode, bool abAutoLuminance, float afOpacity) global native` |
| DEPRECATED | 127 | `DamageActorHealth` | `Bool Function DamageActorHealth(Actor akActor, float afHealthDamage, Actor akSource) global native` |
| DEPRECATED | 129 | `DecapitateActor` | `Function DecapitateActor(Actor akActor) global native` |
| DEPRECATED | 131 | `FreezeActor` | `Function FreezeActor(Actor akActor, int type, bool abFreeze) global native` |
| DEPRECATED | 133 | `KillNoWait` | `Function KillNoWait(Actor akActor) global native` |
| DEPRECATED | 135 | `LaunchArrow` | `Function LaunchArrow(Actor akActor, Ammo akAmmo, Weapon akWeapon, string asNodeName = "", int aiSource = -1, ObjectReference akTarget = None, Potion akPoison = None) global native` |
| DEPRECATED | 137 | `LaunchSpell` | `Function LaunchSpell(Actor akActor, Spell akSpell, int aiSource) global native` |
| DEPRECATED | 140 | `MixColorWithSkinTone` | `Function MixColorWithSkinTone(Actor akActor, ColorForm akColor, bool abManualMode, float afPercentage) global native` |
| DEPRECATED | 142 | `RemoveAddedSpells` | `Function RemoveAddedSpells(Actor akActor, string modName, Keyword[] keywords, bool abMatchAll) global native` |
| DEPRECATED | 144 | `RemoveArmorOfType` | `Function RemoveArmorOfType(Actor akActor, int afArmorType, int[] aiSlotsToSkip, bool abEquippedOnly) global native` |
| DEPRECATED | 146 | `RemoveBasePerk` | `Bool Function RemoveBasePerk(Actor akActor, Perk akPerk) global native` |
| DEPRECATED | 148 | `RemoveBaseSpell` | `Bool Function RemoveBaseSpell(Actor akActor, Spell akSpell) global native` |
| DEPRECATED | 150 | `ReplaceArmorTextureSet` | `Function ReplaceArmorTextureSet(Actor akActor, Armor akArmor, TextureSet akSourceTXST, TextureSet akTargetTXST, int aiTextureType = -1) global native` |
| DEPRECATED | 152 | `ReplaceFaceTextureSet` | `Function ReplaceFaceTextureSet(Actor akActor, TextureSet akMaleTXST, TextureSet akFemaleTXST, int aiTextureType = -1) global native` |
| DEPRECATED | 154 | `ReplaceSkinTextureSet` | `Function ReplaceSkinTextureSet(Actor akActor, TextureSet akMaleTXST, TextureSet akFemaleTXST, int aiSlotMask, int aiTextureType = -1) global native` |
| DEPRECATED | 156 | `ResetActor3D` | `Bool Function ResetActor3D(Actor akActor, string asFolderName) global native` |
| DEPRECATED | 158 | `SetActorRefraction` | `Function SetActorRefraction(Actor akActor, float afRefraction) global native` |
| DEPRECATED | 160 | `SetEquippedWeaponPoison` | `Bool Function SetEquippedWeaponPoison(Actor akActor, Potion akPoison, bool abLeftHand) global native` |
| DEPRECATED | 162 | `SetEquippedWeaponPoisonCount` | `Bool Function SetEquippedWeaponPoisonCount(Actor akActor, int aiCount, bool abLeftHand) global native` |
| DEPRECATED | 164 | `SetHairColor` | `Function SetHairColor(Actor akActor, ColorForm akColor) global native` |
| DEPRECATED | 166 | `SetHeadPartAlpha` | `Function SetHeadPartAlpha(Actor akActor, int aiPartType, float afAlpha) global native` |
| DEPRECATED | 168 | `SetHeadPartTextureSet` | `Function SetHeadPartTextureSet(Actor akActor, TextureSet headpartTXST, int aiType) global native` |
| DEPRECATED | 170 | `SetLinearVelocity` | `Function SetLinearVelocity(Actor akActor, float afX, float afY, float afZ) global native` |
| DEPRECATED | 172 | `SetLocalGravityActor` | `Function SetLocalGravityActor(Actor akActor, float afValue, bool abDisableGravityOnGround) global native` |
| DEPRECATED | 174 | `SetSkinAlpha` | `Function SetSkinAlpha(Actor akActor, float afAlpha) global native` |
| DEPRECATED | 176 | `SetSkinColor` | `Function SetSkinColor(Actor akActor, ColorForm akColor) global native` |
| DEPRECATED | 178 | `SetSoulTrapped` | `Function SetSoulTrapped(Actor akActor, bool abTrapped) global native` |
| DEPRECATED | 180 | `ToggleHairWigs` | `Function ToggleHairWigs(Actor akActor, bool abDisable) global native` |
| DEPRECATED | 182 | `UnequipAllOfType` | `Function UnequipAllOfType(Actor akActor, int afArmorType, int[] aiSlotsToSkip) global native` |
| ACTORBASE | 186 | `GetAssociationType` | `AssociationType Function GetAssociationType(Actorbase akBase1, Actorbase akBase2) global native` |
| ACTORBASE | 188 | `GetDeathItem` | `LeveledItem Function GetDeathItem(Actorbase akBase) global native` |
| ACTORBASE | 190 | `GetNthPerk` | `Perk Function GetNthPerk(Actorbase akBase, int aiIndex) global native` |
| ACTORBASE | 192 | `GetPerkCount` | `int Function GetPerkCount(Actorbase akBase) global native` |
| ACTORBASE | 194 | `GetRelationships` | `Actorbase[] Function GetRelationships(Actorbase akBase, AssociationType akAssocType) global native` |
| ACTORBASE | 196 | `SetDeathItem` | `Function SetDeathItem(Actorbase akBase, LeveledItem akLeveledItem) global native` |
| AMMO | 200 | `GetBaseAmmoEnchantment` | `Enchantment Function GetBaseAmmoEnchantment(Ammo akAmmo) global native` |
| ALIAS | 204 | `GetScriptsAttachedToAlias` | `string[] Function GetScriptsAttachedToAlias(Alias akAlias) global native` |
| ALIAS | 206 | `IsScriptAttachedToAlias` | `Bool Function IsScriptAttachedToAlias(Alias akAlias, string asScriptName) global native` |
| ARMOR/ADDONS | 210 | `GetFootstepSet` | `FootstepSet Function GetFootstepSet(ArmorAddon akArma) global native` |
| ARMOR/ADDONS | 212 | `SetFootstepSet` | `Function SetFootstepSet(ArmorAddon akArma, FootstepSet akFootstepSet) global native` |
| ARRAYS | 216 | `GetSortedActorNames` | `string[] Function GetSortedActorNames(Keyword akKeyword, string asPlural = "(s)", bool abInvertKeyword) global native` |
| ARRAYS | 218 | `GetSortedNPCNames` | `string[] Function GetSortedNPCNames(ActorBase[] aiActorBases, string asPlural = "(s)") global native` |
| ARRAYS | 220 | `AddActorToArray` | `Bool Function AddActorToArray(Actor akActor, Actor[] actorArray) global native` |
| ARRAYS | 222 | `AddStringToArray` | `Bool Function AddStringToArray(string asString, string[] asStrings) global native` |
| ARRAYS | 224 | `ArrayStringCount` | `int Function ArrayStringCount(string asString, string[] asStrings) global native` |
| ARRAYS | 226 | `SortArrayString` | `string[] Function SortArrayString(string[] asStrings) global native` |
| BOOK | 230 | `ClearBookCantBeTakenFlag` | `Function ClearBookCantBeTakenFlag(Book akBook) global native` |
| BOOK | 232 | `ClearReadFlag` | `Function ClearReadFlag(Book akBook) global native` |
| BOOK | 234 | `SetBookCantBeTakenFlag` | `Function SetBookCantBeTakenFlag(Book akBook) global native` |
| BOOK | 236 | `SetReadFlag` | `Function SetReadFlag(Book akBook) global native` |
| CELL | 240 | `GetCellNorthRotation` | `float Function GetCellNorthRotation(Cell akCell) global native` |
| CELL | 242 | `GetLightingTemplate` | `LightingTemplate Function GetLightingTemplate(Cell akCell) global native` |
| CELL | 244 | `SetLightingTemplate` | `Function SetLightingTemplate(Cell akCell, LightingTemplate akLightingTemplate) global native` |
| CELL | 246 | `SetCellNorthRotation` | `Function SetCellNorthRotation(Cell akCell, float afAngle) global native` |
| DEBUG | 250 | `GivePlayerSpellBook` | `Function GivePlayerSpellBook() global native` |
| DEBUG | 252 | `DumpAnimationVariables` | `Function DumpAnimationVariables(Actor akActor, string asAnimationVarPrefix) global native` |
| DETECTION | 256 | `CanActorBeDetected` | `int Function CanActorBeDetected(Actor akActor) global native` |
| DETECTION | 258 | `CanActorDetect` | `int Function CanActorDetect(Actor akActor) global native` |
| DETECTION | 260 | `IsDetectedByAnyone` | `Bool Function IsDetectedByAnyone(Actor akActor) global native` |
| DETECTION | 262 | `ForceActorDetection` | `Function ForceActorDetection(Actor akActor) global native` |
| DETECTION | 264 | `ForceActorDetecting` | `Function ForceActorDetecting(Actor akActor) global native` |
| DETECTION | 266 | `PreventActorDetection` | `Function PreventActorDetection(Actor akActor) global native` |
| DETECTION | 268 | `PreventActorDetecting` | `Function PreventActorDetecting(Actor akActor) global native` |
| DETECTION | 270 | `ResetActorDetection` | `Function ResetActorDetection(Actor akActor) global native` |
| DETECTION | 272 | `ResetActorDetecting` | `Function ResetActorDetecting(Actor akActor) global native` |
| EFFECTSHADER | 276 | `GetAddonModels` | `Debris Function GetAddonModels(EffectShader akEffectShader) global native` |
| EFFECTSHADER | 278 | `GetEffectShaderTotalCount` | `int Function GetEffectShaderTotalCount(EffectShader akEffectShader, bool abActive) global native` |
| EFFECTSHADER | 280 | `IsEffectShaderFlagSet` | `Bool Function IsEffectShaderFlagSet(EffectShader akEffectShader, int aiFlag) global native` |
| EFFECTSHADER | 282 | `GetMembraneFillTexture` | `string Function GetMembraneFillTexture(EffectShader akEffectShader) global native` |
| EFFECTSHADER | 284 | `GetMembraneHolesTexture` | `string Function GetMembraneHolesTexture(EffectShader akEffectShader) global native` |
| EFFECTSHADER | 286 | `GetMembranePaletteTexture` | `string Function GetMembranePaletteTexture(EffectShader akEffectShader) global native` |
| EFFECTSHADER | 288 | `GetParticleFullCount` | `float Function GetParticleFullCount(EffectShader akEffectShader) global native` |
| EFFECTSHADER | 290 | `GetParticlePaletteTexture` | `string Function GetParticlePaletteTexture(EffectShader akEffectShader) global native` |
| EFFECTSHADER | 292 | `GetParticleShaderTexture` | `string Function GetParticleShaderTexture(EffectShader akEffectShader) global native` |
| EFFECTSHADER | 294 | `GetParticlePersistentCount` | `float Function GetParticlePersistentCount(EffectShader akEffectShader) global native` |
| EFFECTSHADER | 296 | `ClearEffectShaderFlag` | `Function ClearEffectShaderFlag(EffectShader akEffectShader, int aiFlag) global native` |
| EFFECTSHADER | 298 | `SetAddonModels` | `Function SetAddonModels(EffectShader akEffectShader, Debris akDebris) global native` |
| EFFECTSHADER | 300 | `SetEffectShaderFlag` | `Function SetEffectShaderFlag(EffectShader akEffectShader, int aiFlag) global native` |
| EFFECTSHADER | 302 | `SetMembraneColorKeyData` | `Function SetMembraneColorKeyData(EffectShader akEffectShader, int aiColorKey, int[] aiRGB, float afAlpha, float afTime) global native` |
| EFFECTSHADER | 304 | `SetMembraneFillTexture` | `Function SetMembraneFillTexture(EffectShader akEffectShader, string asTextureName) global native` |
| EFFECTSHADER | 306 | `SetMembraneHolesTexture` | `Function SetMembraneHolesTexture(EffectShader akEffectShader, string asTextureName) global native` |
| EFFECTSHADER | 308 | `SetMembranePaletteTexture` | `Function SetMembranePaletteTexture(EffectShader akEffectShader, string asTextureName) global native` |
| EFFECTSHADER | 310 | `SetParticleColorKeyData` | `Function SetParticleColorKeyData(EffectShader akEffectShader, int aiColorKey, int[] aiRGB, float afAlpha, float afTime) global native` |
| EFFECTSHADER | 312 | `SetParticleFullCount` | `Function SetParticleFullCount(EffectShader akEffectShader, float afParticleCount) global native` |
| EFFECTSHADER | 314 | `SetParticlePaletteTexture` | `Function SetParticlePaletteTexture(EffectShader akEffectShader, string asTextureName) global native` |
| EFFECTSHADER | 316 | `SetParticlePersistentCount` | `Function SetParticlePersistentCount(EffectShader akEffectShader, float afParticleCount) global native` |
| EFFECTSHADER | 318 | `SetParticleShaderTexture` | `Function SetParticleShaderTexture(EffectShader akEffectShader, string asTextureName) global native` |
| ENCHANTMENT | 323 | `GetEnchantmentType` | `int Function GetEnchantmentType(Enchantment akEnchantment) global native` |
| ENCHANTMENT | 325 | `AddMagicEffectToEnchantment` | `Function AddMagicEffectToEnchantment(Enchantment akEnchantment, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0, string[] asConditionList) global native` |
| ENCHANTMENT | 327 | `AddEffectItemToEnchantment` | `Function AddEffectItemToEnchantment(Enchantment akEnchantment, Enchantment akEnchantmentToCopyFrom, int aiIndex, float afCost = -1.0) global native` |
| ENCHANTMENT | 329 | `RemoveMagicEffectFromEnchantment` | `Function RemoveMagicEffectFromEnchantment(Enchantment akEnchantment, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0) global native` |
| ENCHANTMENT | 331 | `RemoveEffectItemFromEnchantment` | `Function RemoveEffectItemFromEnchantment(Enchantment akEnchantment, Enchantment akEnchantmentToMatchFrom, int aiIndex) global native` |
| ENCHANTMENT | 333 | `SetEnchantmentMagicEffect` | `Function SetEnchantmentMagicEffect(Enchantment akEnchantment, MagicEffect akMagicEffect, int aiIndex) global native` |
| FACTION | 338 | `GetVendorFactionContainer` | `ObjectReference Function GetVendorFactionContainer(Faction akVendorFaction)  global native` |
| FACTION | 340 | `GetAllActorsInFaction` | `Actor[] Function GetAllActorsInFaction(Faction akFaction) global native` |
| FASTTRAVEL | 344 | `SetFastTravelDisabled` | `Bool Function SetFastTravelDisabled(bool abDisable) global native` |
| FASTTRAVEL | 346 | `SetFastTravelTargetFormID` | `Bool Function SetFastTravelTargetFormID(int aiDestinationFormID) global native` |
| FASTTRAVEL | 348 | `SetFastTravelTargetRef` | `Bool Function SetFastTravelTargetRef(ObjectReference akDestination) global native` |
| FASTTRAVEL | 350 | `SetFastTravelTargetString` | `Bool Function SetFastTravelTargetString(string asDestination) global native` |
| FASTTRAVEL | 352 | `SetFastTravelWaitTimeout` | `float Function SetFastTravelWaitTimeout(float afTimeout) global native` |
| FORM | 356 | `EvaluateConditionList` | `Bool Function EvaluateConditionList(Form akForm, ObjectReference akActionRef, ObjectReference akTargetRef) global native` |
| FORM | 358 | `ClearRecordFlag` | `Function ClearRecordFlag(Form akForm, int aiFlag) global native` |
| FORM | 360 | `GetConditionList` | `string[] Function GetConditionList(Form akForm, int aiIndex = 0) global native` |
| FORM | 362 | `GetDescription` | `string Function GetDescription(Form akForm) global native` |
| FORM | 364 | `GetFormEditorID` | `string Function GetFormEditorID(Form akForm) global native` |
| FORM | 366 | `GetFormModName` | `string Function GetFormModName(Form akForm, bool abLastModified) global native` |
| FORM | 368 | `GetScriptsAttachedToForm` | `string[] Function GetScriptsAttachedToForm(Form akForm) global native` |
| FORM | 370 | `IsFormInMod` | `Bool Function IsFormInMod(Form akForm, string asModName) global native` |
| FORM | 372 | `IsGeneratedForm` | `Bool Function IsGeneratedForm(Form akForm) global native` |
| FORM | 374 | `IsRecordFlagSet` | `Bool Function IsRecordFlagSet(Form akForm, int aiFlag) global native` |
| FORM | 376 | `IsScriptAttachedToForm` | `Bool Function IsScriptAttachedToForm(Form akForm, string asScriptName) global native` |
| FORM | 378 | `SetRecordFlag` | `Function SetRecordFlag(Form akForm, int aiFlag) global native` |
| FORM | 380 | `AddKeywordToForm` | `Function AddKeywordToForm(Form akForm, Keyword akKeyword) global native` |
| FORM | 382 | `MarkItemAsFavorite` | `Function MarkItemAsFavorite(Form akForm) global native` |
| FORM | 384 | `RemoveConditionList` | `Function RemoveConditionList(Form akForm, int aiIndex, string[] asConditionList) global native` |
| FORM | 386 | `ReplaceKeywordOnForm` | `Function ReplaceKeywordOnForm(Form akForm, Keyword akKeywordAdd, Keyword akKeywordRemove) global native` |
| FORM | 388 | `RemoveKeywordOnForm` | `Bool Function RemoveKeywordOnForm(Form akForm, Keyword akKeyword) global native` |
| FORM | 390 | `SetConditionList` | `Function SetConditionList(Form akForm, int aiIndex, string[] asConditionList) global native` |
| FORM | 392 | `UnmarkItemAsFavorite` | `Function UnmarkItemAsFavorite(Form akForm) global native` |
| FURNITURE | 396 | `GetFurnitureType` | `int Function GetFurnitureType(Furniture akFurniture) global native` |
| GAME | 400 | `GetActivePlugins` | `String[] Function GetActivePlugins() global native` |
| GAME | 402 | `GetAllEnchantments` | `Enchantment[] Function GetAllEnchantments(Keyword[] akKeywords = None) global native` |
| GAME | 404 | `GetAllForms` | `Form[] Function GetAllForms(int aiFormType, Keyword[] akKeywords = None) global native` |
| GAME | 406 | `GetAllRaces` | `Race[] Function GetAllRaces(Keyword[] akKeywords = None) global native` |
| GAME | 408 | `GetAllSpells` | `Spell[] Function GetAllSpells(Keyword[] akKeywords = None, bool abIsPlayable = false) global native` |
| GAME | 410 | `GetActorsByProcessingLevel` | `Actor[] Function GetActorsByProcessingLevel(int aiLevel) global native` |
| GAME | 412 | `GetAllFormsInMod` | `Form[] Function GetAllFormsInMod(string asModName, int aiFormType, Keyword[] akKeywords = None) global native` |
| GAME | 414 | `GetAllEnchantmentsInMod` | `Enchantment[] Function GetAllEnchantmentsInMod(string asModName, Keyword[] akKeywords = None) global native` |
| GAME | 416 | `GetAllRacesInMod` | `Race[] Function GetAllRacesInMod(string asModName, Keyword[] akKeywords = None) global native` |
| GAME | 418 | `GetAllSpellsInMod` | `Spell[] Function GetAllSpellsInMod(string asModName, Keyword[] akKeywords = None, bool abIsPlayable = false) global native` |
| GAME | 420 | `GetAttachedCells` | `Cell[] Function GetAttachedCells() global native` |
| GAME | 422 | `GetFormFromEditorID` | `Form Function GetFormFromEditorID(string asEditorID) global native` |
| GAME | 424 | `GetGameSettingBool` | `int Function GetGameSettingBool(string asGameSetting) global native` |
| GAME | 426 | `GetGodMode` | `Bool Function GetGodMode() global native` |
| GAME | 428 | `GetLandHeight` | `float Function GetLandHeight(float afPosX, float afPosY, float afPosZ) global native` |
| GAME | 430 | `GetLandMaterialType` | `string Function GetLandMaterialType(float afPosX, float afPosY, float afPosZ) global native` |
| GAME | 432 | `GetLocalGravity` | `float[] Function GetLocalGravity() global native` |
| GAME | 434 | `GetNumActorsInHigh` | `int Function GetNumActorsInHigh() global native` |
| GAME | 436 | `GetPlayerFollowers` | `Actor[] Function GetPlayerFollowers() global native` |
| GAME | 438 | `GetSurfaceMaterialType` | `string Function GetSurfaceMaterialType(float afX, float afY, float afZ) global native` |
| GAME | 440 | `IsPluginFound` | `Bool Function IsPluginFound(string akName) global native` |
| GAME | 442 | `IsSurvivalModeActive` | `Bool Function IsSurvivalModeActive() global native` |
| GAME | 444 | `ClearCachedFactionFightReactions` | `Function ClearCachedFactionFightReactions() global native` |
| GAME | 446 | `SetLocalGravity` | `Function SetLocalGravity(float afXAxis, float afYAxis, float afZAxis) global native` |
| GAME | 448 | `UpdateCrosshairs` | `Function UpdateCrosshairs()  global native` |
| HAZARD | 453 | `GetHazardArt` | `string Function GetHazardArt(Hazard akHazard) global native` |
| HAZARD | 455 | `GetHazardIMOD` | `ImageSpaceModifier Function GetHazardIMOD(Hazard akHazard) global native` |
| HAZARD | 457 | `GetHazardIMODRadius` | `float Function GetHazardIMODRadius(Hazard akHazard) global native` |
| HAZARD | 459 | `GetHazardIPDS` | `ImpactDataSet Function GetHazardIPDS(Hazard akHazard) global native` |
| HAZARD | 461 | `GetHazardLifetime` | `float Function GetHazardLifetime(Hazard akHazard) global native` |
| HAZARD | 463 | `GetHazardLight` | `Light Function GetHazardLight(Hazard akHazard) global native` |
| HAZARD | 465 | `GetHazardLimit` | `int Function GetHazardLimit(Hazard akHazard) global native` |
| HAZARD | 467 | `GetHazardRadius` | `float Function GetHazardRadius(Hazard akHazard) global native` |
| HAZARD | 469 | `GetHazardSound` | `SoundDescriptor Function GetHazardSound(Hazard akHazard) global native` |
| HAZARD | 471 | `GetHazardSpell` | `Spell Function GetHazardSpell(Hazard akHazard) global native` |
| HAZARD | 473 | `GetHazardTargetInterval` | `float Function GetHazardTargetInterval(Hazard akHazard) global native` |
| HAZARD | 475 | `IsHazardFlagSet` | `Bool Function IsHazardFlagSet(Hazard akHazard, int aiFlag) global native` |
| HAZARD | 477 | `ClearHazardFlag` | `Function ClearHazardFlag(Hazard akHazard, int aiFlag) global native` |
| HAZARD | 479 | `SetHazardArt` | `Function SetHazardArt(Hazard akHazard, string asPath) global native` |
| HAZARD | 481 | `SetHazardFlag` | `Function SetHazardFlag(Hazard akHazard, int aiFlag) global native` |
| HAZARD | 483 | `SetHazardIMOD` | `Function SetHazardIMOD(Hazard akHazard, ImageSpaceModifier akIMOD) global native` |
| HAZARD | 485 | `SetHazardIMODRadius` | `Function SetHazardIMODRadius(Hazard akHazard, float afRadius) global native` |
| HAZARD | 487 | `SetHazardIPDS` | `Function SetHazardIPDS(Hazard akHazard, ImpactDataSet akIPDS) global native` |
| HAZARD | 489 | `SetHazardLifetime` | `Function SetHazardLifetime(Hazard akHazard, float afLifetime) global native` |
| HAZARD | 491 | `SetHazardLight` | `Function SetHazardLight(Hazard akHazard, Light akLight) global native` |
| HAZARD | 493 | `SetHazardLimit` | `Function SetHazardLimit(Hazard akHazard, int aiLimit) global native` |
| HAZARD | 495 | `SetHazardRadius` | `Function SetHazardRadius(Hazard akHazard, float afRadius) global native` |
| HAZARD | 497 | `SetHazardSound` | `Function SetHazardSound(Hazard akHazard, SoundDescriptor akSound) global native` |
| HAZARD | 499 | `SetHazardSpell` | `Function SetHazardSpell(Hazard akHazard, Spell akspell) global native` |
| HAZARD | 501 | `SetHazardTargetInterval` | `Function SetHazardTargetInterval(Hazard akHazard, float afInterval) global native` |
| IDLE | 505 | `GetAnimationEventName` | `string Function GetAnimationEventName(Idle akIdle) global native` |
| IDLE | 507 | `GetAnimationFileName` | `string Function GetAnimationFileName(Idle akIdle) global native` |
| LIGHT | 511 | `GetLightColor` | `ColorForm Function GetLightColor(Light akLight) global native` |
| LIGHT | 513 | `GetLightFade` | `float Function GetLightFade(Light akLight) global native` |
| LIGHT | 515 | `GetLightFOV` | `float Function GetLightFOV(Light akLight) global native` |
| LIGHT | 517 | `GetLightRadius` | `float Function GetLightRadius(Light akLight) global native` |
| LIGHT | 519 | `GetLightRGB` | `int[] Function GetLightRGB(Light akLight) global native` |
| LIGHT | 521 | `GetLightShadowDepthBias` | `float Function GetLightShadowDepthBias(ObjectReference akLightObject) global native` |
| LIGHT | 523 | `GetLightType` | `int Function GetLightType(Light akLight) global native` |
| LIGHT | 525 | `SetLightColor` | `Function SetLightColor(Light akLight, ColorForm akColorform) global native` |
| LIGHT | 527 | `SetLightFade` | `Function SetLightFade(Light akLight, float afRange) global native` |
| LIGHT | 529 | `SetLightFOV` | `Function SetLightFOV(Light akLight, float afFOV) global native` |
| LIGHT | 531 | `SetLightRadius` | `Function SetLightRadius(Light akLight, float afRadius) global native` |
| LIGHT | 533 | `SetLightRGB` | `Function SetLightRGB(Light akLight, int[] aiRGB) global native` |
| LIGHT | 535 | `SetLightShadowDepthBias` | `Function SetLightShadowDepthBias(ObjectReference akLightObject, float afDepthBias) global native` |
| LIGHT | 537 | `SetLightType` | `Function SetLightType(Light akLight, int aiLightType) global native` |
| LEVELED ITEM | 541 | `GetContentFromLeveledItem` | `Form[] Function GetContentFromLeveledItem(LeveledItem akLeveledItem, ObjectReference akRef) global native` |
| LEVELED NPC | 545 | `GetContentFromLeveledActor` | `Form[] Function GetContentFromLeveledActor(LeveledActor akLeveledActor, ObjectReference akRef) global native` |
| LEVELED SPELL | 549 | `GetContentFromLeveledSpell` | `Form[] Function GetContentFromLeveledSpell(LeveledSpell akLeveledSpell, ObjectReference akRef) global native` |
| LOCATION | 553 | `GetParentLocation` | `Location Function GetParentLocation(Location akLoc) global native` |
| LOCATION | 555 | `SetParentLocation` | `Function SetParentLocation(Location akLoc, Location akNewLoc) global native` |
| MAGIC EFFECTS | 559 | `GetAssociatedForm` | `Form Function GetAssociatedForm(MagicEffect akMagicEffect) global native` |
| MAGIC EFFECTS | 561 | `GetEffectArchetypeAsInt` | `int Function GetEffectArchetypeAsInt(MagicEffect akMagicEffect) global native` |
| MAGIC EFFECTS | 563 | `GetEffectArchetypeAsString` | `string Function GetEffectArchetypeAsString(MagicEffect akMagicEffect) global native` |
| MAGIC EFFECTS | 565 | `GetPrimaryActorValue` | `string Function GetPrimaryActorValue(MagicEffect akMagicEffect) global native` |
| MAGIC EFFECTS | 567 | `GetSecondaryActorValue` | `string Function GetSecondaryActorValue(MagicEffect akMagicEffect) global native` |
| MAGIC EFFECTS | 569 | `GetMagicEffectSound` | `SoundDescriptor Function GetMagicEffectSound(MagicEffect akMagicEffect, int aiType) global native` |
| MAGIC EFFECTS | 571 | `SetAssociatedForm` | `Function SetAssociatedForm(MagicEffect akMagicEffect, Form akForm) global native` |
| MAGIC EFFECTS | 573 | `SetMagicEffectSound` | `Function SetMagicEffectSound(MagicEffect akMagicEffect, SoundDescriptor akSoundDescriptor, int aiType) global native` |
| OBJECTREFERENCES | 577 | `ActorInRangeHasEffect` | `Bool Function ActorInRangeHasEffect(ObjectReference akRef, float afRadius, MagicEffect akEffect, bool abIgnorePlayer) global native` |
| OBJECTREFERENCES | 579 | `AddAllItemsToArray` | `Form[] Function AddAllItemsToArray(ObjectReference akRef, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` |
| OBJECTREFERENCES | 581 | `AddAllItemsToList` | `Function AddAllItemsToList(ObjectReference akRef, Formlist akList, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` |
| OBJECTREFERENCES | 583 | `AddItemsOfTypeToArray` | `Form[] Function AddItemsOfTypeToArray(ObjectReference akRef, int aiFormType, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` |
| OBJECTREFERENCES | 585 | `AddItemsOfTypeToList` | `Function AddItemsOfTypeToList(ObjectReference akRef, Formlist akList, int aiFormType, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` |
| OBJECTREFERENCES | 587 | `AddItemsWithKeywordToArray` | `Form[] Function AddItemsWithKeywordToArray(ObjectReference akRef, Keyword akKeyword, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` |
| OBJECTREFERENCES | 589 | `AddItemsWithKeywordToList` | `Function AddItemsWithKeywordToList(ObjectReference akRef, Formlist akList, Keyword akKeyword, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` |
| OBJECTREFERENCES | 591 | `AddItemsWithKeywordStringToArray` | `Form[] Function AddItemsWithKeywordStringToArray(ObjectReference akRef, String asKeywordString, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` |
| OBJECTREFERENCES | 593 | `AddItemsWithKeywordStringToList` | `Function AddItemsWithKeywordStringToList(ObjectReference akRef, Formlist akList, String asKeywordString, bool abNoEquipped = true, bool abNoFavorited = false, bool abNoQuestItem = false) global native` |
| OBJECTREFERENCES | 595 | `FindAllReferencesOfFormType` | `ObjectReference[] Function FindAllReferencesOfFormType(ObjectReference akRef, int formType, float afRadius) global native` |
| OBJECTREFERENCES | 597 | `FindAllReferencesWithKeyword` | `ObjectReference[] Function FindAllReferencesWithKeyword(ObjectReference akRef, Form keywordOrList, float afRadius, bool abMatchAll) global native` |
| OBJECTREFERENCES | 599 | `FindAllReferencesOfType` | `ObjectReference[] Function FindAllReferencesOfType(ObjectReference akRef, Form akFormOrList, float afRadius) global native` |
| OBJECTREFERENCES | 601 | `FindFirstItemInList` | `Form Function FindFirstItemInList(ObjectReference akRef, FormList akList) global native` |
| OBJECTREFERENCES | 603 | `GetActiveAssociatedQuests` | `Quest[] Function GetActiveAssociatedQuests(ObjectReference akRef, Bool abAllowEmptyStages = True) global native` |
| OBJECTREFERENCES | 605 | `GetActivateChildren` | `ObjectReference[] Function GetActivateChildren(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 607 | `GetActiveGamebryoAnimation` | `string Function GetActiveGamebryoAnimation(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 609 | `GetActiveMagicEffects` | `ActiveMagicEffect[] Function GetActiveMagicEffects(ObjectReference akRef, MagicEffect akMagicEffect) global native` |
| OBJECTREFERENCES | 611 | `GetAllAssociatedQuests` | `Quest[] Function GetAllAssociatedQuests(ObjectReference akRef, Bool abAllowEmptyStages = True) global native` |
| OBJECTREFERENCES | 613 | `GetActorCause` | `Actor Function GetActorCause(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 615 | `GetAllArtObjects` | `Art[] Function GetAllArtObjects(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 617 | `GetAllEffectShaders` | `EffectShader[] Function GetAllEffectShaders(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 619 | `GetClosestActorFromRef` | `Actor Function GetClosestActorFromRef(ObjectReference akRef, bool abIgnorePlayer) global native` |
| OBJECTREFERENCES | 621 | `GetEffectShaderDuration` | `float Function GetEffectShaderDuration(ObjectReference akRef, EffectShader akShader) global native` |
| OBJECTREFERENCES | 623 | `GetDoorDestination` | `ObjectReference Function GetDoorDestination(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 625 | `GetLinkedChildren` | `ObjectReference[] Function GetLinkedChildren(ObjectReference akRef, Keyword akKeyword) global native` |
| OBJECTREFERENCES | 627 | `GetMagicEffectSource` | `Form[] Function GetMagicEffectSource(ObjectReference akRef, MagicEffect akEffect) global native` |
| OBJECTREFERENCES | 629 | `GetMaterialType` | `string[] Function GetMaterialType(ObjectReference akRef, string asNodeName = "") global native` |
| OBJECTREFERENCES | 631 | `GetMotionType` | `int Function GetMotionType(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 633 | `GetNumActorsWithEffectInRange` | `int Function GetNumActorsWithEffectInRange(ObjectReference akRef, float afRadius, MagicEffect akEffect, bool abignorePlayer) global native` |
| OBJECTREFERENCES | 635 | `GetRandomActorFromRef` | `Actor Function GetRandomActorFromRef(ObjectReference akRef, float afRadius, bool abIgnorePlayer) global native` |
| OBJECTREFERENCES | 637 | `GetQuestItems` | `Form[] Function GetQuestItems(ObjectReference akRef, bool abNoEquipped = false, bool abNoFavorited = false) global native` |
| OBJECTREFERENCES | 639 | `GetRefAliases` | `Alias[] Function GetRefAliases(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 641 | `GetRefCount` | `int Function GetRefCount(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 643 | `GetStoredSoulSize` | `int Function GetStoredSoulSize(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 645 | `HasArtObject` | `int Function HasArtObject(ObjectReference akRef, Art akArtObject, bool abActive = false) global native` |
| OBJECTREFERENCES | 647 | `HasEffectShader` | `int Function HasEffectShader(ObjectReference akRef, EffectShader akShader, bool abActive = false) global native` |
| OBJECTREFERENCES | 649 | `HasNiExtraData` | `Bool Function HasNiExtraData(ObjectReference akRef, string asName) global native` |
| OBJECTREFERENCES | 651 | `IsCasting` | `Bool Function IsCasting(ObjectReference akRef, Form akMagicItem) global native` |
| OBJECTREFERENCES | 653 | `IsLoadDoor` | `Bool Function IsLoadDoor(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 655 | `IsQuestItem` | `Bool Function IsQuestItem(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 657 | `IsRefInWater` | `Bool Function IsRefInWater(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 659 | `IsRefNodeInWater` | `Bool Function IsRefNodeInWater(ObjectReference akRef, String asNodeName) global native` |
| OBJECTREFERENCES | 661 | `IsRefUnderwater` | `Bool Function IsRefUnderwater(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 663 | `IsVIP` | `Bool Function IsVIP(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 665 | `ApplyMaterialShader` | `Function ApplyMaterialShader(ObjectReference akRef, MaterialObject akMatObject, float directionalThresholdAngle) global native` |
| OBJECTREFERENCES | 667 | `AddKeywordToRef` | `Function AddKeywordToRef(ObjectReference akRef, Keyword akKeyword) global native` |
| OBJECTREFERENCES | 669 | `CastEx` | `Function CastEx(ObjectReference akRef, Form akSpell, ObjectReference akTarget, Actor akBlameActor, int aiSource) global native` |
| OBJECTREFERENCES | 671 | `MoveToNearestNavmeshLocation` | `Function MoveToNearestNavmeshLocation(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 673 | `RemoveAllModItems` | `Function RemoveAllModItems(ObjectReference akRef, string asModName, bool abOnlyUnequip = false) global native` |
| OBJECTREFERENCES | 675 | `RemoveListFromContainer` | `Function RemoveListFromContainer(ObjectReference akRef, FormList akList, bool abNoEquipped = false, bool abNoFavorited = false, bool abNoQuestItem = false, ObjectReference akDestination = None)  global native` |
| OBJECTREFERENCES | 677 | `RemoveKeywordFromRef` | `Bool Function RemoveKeywordFromRef(ObjectReference akRef, Keyword akKeyword) global native` |
| OBJECTREFERENCES | 679 | `ReplaceKeywordOnRef` | `Function ReplaceKeywordOnRef(ObjectReference akRef, Keyword akKeywordAdd, Keyword akKeywordRemove) global native` |
| OBJECTREFERENCES | 681 | `PlayDebugShader` | `Function PlayDebugShader(ObjectReference akRef, float[] afRGBA) global native` |
| OBJECTREFERENCES | 683 | `ScaleObject3D` | `Function ScaleObject3D(ObjectReference akRef, string asNodeName, float afScale) global native` |
| OBJECTREFERENCES | 685 | `SetBaseObject` | `Function SetBaseObject(ObjectReference akRef, Form akBaseObject) global native` |
| OBJECTREFERENCES | 687 | `SetCollisionLayer` | `Function SetCollisionLayer(ObjectReference akRef, string asNodeName, int aiCollisionLayer) global native` |
| OBJECTREFERENCES | 689 | `SetDoorDestination` | `Bool Function SetDoorDestination(ObjectReference akRef, ObjectReference akDoor) global native` |
| OBJECTREFERENCES | 691 | `SetEffectShaderDuration` | `Function SetEffectShaderDuration(ObjectReference akRef, EffectShader akShader, float afTime, bool abAbsolute) global native` |
| OBJECTREFERENCES | 693 | `SetKey` | `Function SetKey(ObjectReference akRef, Key akKey) global native` |
| OBJECTREFERENCES | 695 | `SetLinkedRef` | `Function SetLinkedRef(ObjectReference akRef, ObjectReference akTargetRef, Keyword akKeyword = None) global native` |
| OBJECTREFERENCES | 697 | `SetMaterialType` | `Function SetMaterialType(ObjectReference akRef, string asNewMaterial, string asOldMaterial = "", string asNodeName = "") global native` |
| OBJECTREFERENCES | 699 | `SetupBodyPartGeometry` | `Function SetupBodyPartGeometry(ObjectReference akRef, actor akActor) global native` |
| OBJECTREFERENCES | 701 | `SetShaderType` | `Function SetShaderType(ObjectReference akRef, ObjectReference akTemplate, string asDiffusePath, int aiShaderType, int aiTextureType, bool abNoWeapons, bool abNoAlphaProperty) global native` |
| OBJECTREFERENCES | 703 | `StopAllShaders` | `Function StopAllShaders(ObjectReference akRef) global native` |
| OBJECTREFERENCES | 705 | `StopArtObject` | `Function StopArtObject(ObjectReference akRef, Art akArt) global native` |
| OBJECTREFERENCES | 707 | `ToggleChildNode` | `Function ToggleChildNode(ObjectReference akRef, string asNodeName, bool abDisable) global native` |
| OBJECTREFERENCES | 709 | `UpdateHitEffectArtNode` | `Function UpdateHitEffectArtNode(ObjectReference akRef, Art akArt, string asNewNode, float[] afTranslate, float[] afRotate, float afRelativeScale = 1.0) global native` |
| PACKAGES | 713 | `GetPackageType` | `int Function GetPackageType(Package akPackage) global native` |
| PACKAGES | 715 | `GetPackageIdles` | `Idle[] Function GetPackageIdles(Package akPackage) global native` |
| PACKAGES | 717 | `AddPackageIdle` | `Function AddPackageIdle(Package akPackage, Idle akIdle) global native` |
| PACKAGES | 719 | `RemovePackageIdle` | `Function RemovePackageIdle(Package akPackage, Idle akIdle) global native` |
| PAPYRUS EXTENDER | 724 | `GetPapyrusExtenderVersion` | `int[] Function GetPapyrusExtenderVersion() global native` |
| POTION | 728 | `AddMagicEffectToPotion` | `Function AddMagicEffectToPotion(Potion akPotion, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0, string[] asConditionList) global native` |
| POTION | 730 | `AddEffectItemToPotion` | `Function AddEffectItemToPotion(Potion akPotion, Potion akPotionToCopyFrom, int aiIndex, float afCost = -1.0) global native` |
| POTION | 732 | `RemoveMagicEffectFromPotion` | `Function RemoveMagicEffectFromPotion(Potion akPotion, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0) global native` |
| POTION | 734 | `RemoveEffectItemFromPotion` | `Function RemoveEffectItemFromPotion(Potion akPotion, Potion akPotionToMatchFrom, int aiIndex) global native` |
| POTION | 736 | `SetPotionMagicEffect` | `Function SetPotionMagicEffect(Potion akPotion, MagicEffect akMagicEffect, int aiIndex) global native` |
| PROJECTILES | 740 | `GetProjectileGravity` | `float Function GetProjectileGravity(Projectile akProjectile) global native` |
| PROJECTILES | 742 | `GetProjectileImpactForce` | `float Function GetProjectileImpactForce(Projectile akProjectile) global native` |
| PROJECTILES | 744 | `GetProjectileRange` | `float Function GetProjectileRange(Projectile akProjectile) global native` |
| PROJECTILES | 746 | `GetProjectileSpeed` | `float Function GetProjectileSpeed(Projectile akProjectile) global native` |
| PROJECTILES | 748 | `GetProjectileType` | `int Function GetProjectileType(Projectile akProjectile) global native` |
| PROJECTILES | 750 | `SetProjectileGravity` | `Function SetProjectileGravity(Projectile akProjectile, float afGravity) global native` |
| PROJECTILES | 752 | `SetProjectileImpactForce` | `Function SetProjectileImpactForce(Projectile akProjectile, float afImpactForce) global native` |
| PROJECTILES | 754 | `SetProjectileRange` | `Function SetProjectileRange(Projectile akProjectile, float afRange) global native` |
| PROJECTILES | 756 | `SetProjectileSpeed` | `Function SetProjectileSpeed(Projectile akProjectile, float afSpeed) global native` |
| QUEST | 760 | `GetAllQuestObjectives` | `int[] Function GetAllQuestObjectives(Quest akQuest) global native` |
| QUEST | 762 | `GetAllQuestStages` | `int[] Function GetAllQuestStages(Quest akQuest) global native` |
| QUEST | 764 | `SetObjectiveText` | `Function SetObjectiveText(Quest akQuest, string asText, int aiIndex) global native` |
| SCENE | 768 | `GetActorsInScene` | `Actor[] Function GetActorsInScene(Scene akScene) global native` |
| SCENE | 770 | `IsActorInScene` | `bool Function IsActorInScene(Scene akScene, Actor akActor) global native` |
| SCROLL | 774 | `AddMagicEffectToScroll` | `Function AddMagicEffectToScroll(Scroll akScroll, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0, string[] asConditionList) global native` |
| SCROLL | 776 | `AddEffectItemToScroll` | `Function AddEffectItemToScroll(Scroll akScroll, Scroll akScrollToCopyFrom, int aiIndex, float afCost = -1.0) global native` |
| SCROLL | 778 | `RemoveMagicEffectFromScroll` | `Function RemoveMagicEffectFromScroll(Scroll akScroll, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0) global native` |
| SCROLL | 780 | `RemoveEffectItemFromScroll` | `Function RemoveEffectItemFromScroll(Scroll akScroll, Scroll akScrollToMatchFrom, int aiIndex) global native` |
| SCROLL | 782 | `SetScrollMagicEffect` | `Function SetScrollMagicEffect(Scroll akScroll, MagicEffect akMagicEffect, int aiIndex) global native` |
| SOUND | 786 | `SetSoundDescriptor` | `Function SetSoundDescriptor(Sound akSound, SoundDescriptor akSoundDescriptor) global native` |
| SPELL | 790 | `GetSpellType` | `int Function GetSpellType(Spell akSpell) global native` |
| SPELL | 792 | `AddMagicEffectToSpell` | `Function AddMagicEffectToSpell(Spell akSpell, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0, string[] asConditionList) global native` |
| SPELL | 794 | `AddEffectItemToSpell` | `Function AddEffectItemToSpell(Spell akSpell, Spell akSpellToCopyFrom, int aiIndex, float afCost = -1.0) global native` |
| SPELL | 796 | `RemoveMagicEffectFromSpell` | `Function RemoveMagicEffectFromSpell(Spell akSpell, MagicEffect akMagicEffect, float afMagnitude, int aiArea, int aiDuration, float afCost = 0.0) global native` |
| SPELL | 798 | `RemoveEffectItemFromSpell` | `Function RemoveEffectItemFromSpell(Spell akSpell, Spell akSpellToMatchFrom, int aiIndex) global native` |
| SPELL | 800 | `SetSpellCastingType` | `Function SetSpellCastingType(Spell akSpell, int aiType) global native` |
| SPELL | 802 | `SetSpellDeliveryType` | `Function SetSpellDeliveryType(Spell akSpell, int aiType) global native` |
| SPELL | 804 | `SetSpellType` | `Function SetSpellType(Spell akSpell, int aiType) global native` |
| SPELL | 806 | `SetSpellMagicEffect` | `Function SetSpellMagicEffect(Spell akSpell, MagicEffect akMagicEffect, int aiIndex) global native` |
| STRINGS | 810 | `IntToString` | `string Function IntToString(int aiValue, bool abHex) global native` |
| STRINGS | 812 | `StringToInt` | `int Function StringToInt(string asString) global native` |
| STRINGS | 816 | `GetMenuContainer` | `ObjectReference Function GetMenuContainer() global native` |
| STRINGS | 818 | `HideMenu` | `Function HideMenu(string asMenuName) global native` |
| STRINGS | 820 | `IsShowingMenus` | `Bool Function IsShowingMenus() global native` |
| STRINGS | 822 | `ShowBookMenu` | `Function ShowBookMenu(Book akBook) global native` |
| STRINGS | 824 | `ShowMenu` | `Function ShowMenu(string asMenuName) global native` |
| STRINGS | 826 | `ToggleOpenSleepWaitMenu` | `Function ToggleOpenSleepWaitMenu(bool abOpenSleepMenu) global native` |
| STRINGS | 828 | `ShowTutorialMessage` | `Function ShowTutorialMessage(Message akMessage) global native` |
| UTILITY | 832 | `GenerateRandomFloat` | `float Function GenerateRandomFloat(float afMin, float afMax) global native` |
| UTILITY | 834 | `GenerateRandomInt` | `int Function GenerateRandomInt(int afMin, int afMax) global native` |
| UTILITY | 836 | `GetSystemTime` | `int[] Function GetSystemTime() global native` |
| VISUALEFFECTS | 840 | `GetArtObject` | `Art Function GetArtObject(VisualEffect akEffect) global native` |
| VISUALEFFECTS | 842 | `GetArtObjectTotalCount` | `int Function GetArtObjectTotalCount(VisualEffect akEffect, bool abActive) global native` |
| VISUALEFFECTS | 844 | `SetArtObject` | `Function SetArtObject(VisualEffect akEffect, Art akArt) global native` |
| WEATHER | 848 | `GetWindSpeedAsFloat` | `float Function GetWindSpeedAsFloat(Weather akWeather) global native` |
| WEATHER | 850 | `GetWindSpeedAsInt` | `int Function GetWindSpeedAsInt(Weather akWeather) global native` |
| WEATHER | 852 | `GetWeatherType` | `int Function GetWeatherType(Weather akWeather = None) global native` |

## Retrieval guidance

Prefer the section matching the subsystem being debugged. In particular:

- **ACTOR / ACTORBASE** — runtime actor and base NPC data;
- **FORM** — editor IDs, record flags, conditions, keywords, descriptions, scripts;
- **GAME** — loaded plugins/forms, processing levels, settings and global searches;
- **OBJECTREFERENCES** — inventory, shaders, linked refs, materials, collision, nearby refs and reference state;
- **MAGIC EFFECTS / SPELL / POTION / SCROLL / ENCHANTMENT** — mutable magic data;
- **HAZARD / LIGHT / PROJECTILES / WEATHER** — environment/effect records;
- **DETECTION** — detection overrides/queries;
- **FASTTRAVEL** — fast-travel state/target controls;
- **UI / STRINGS / UTILITY** — menu and utility helpers;
- **DEPRECATED** — compatibility surface; avoid for new design unless migration requires it.

## Runtime caution

A PSC declaration can compile while its native function is unavailable if the Papyrus Extender DLL is missing, failed to load, or is the wrong runtime build. Diagnose the native plugin log/runtime before treating that as a Papyrus language error.
