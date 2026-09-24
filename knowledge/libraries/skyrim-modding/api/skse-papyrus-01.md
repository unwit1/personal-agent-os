# SKSE64 Modified Papyrus API — Shard 1

Imported: 2026-09-24
Source: `ianpatt/skse64` master
Scripts: 8 · declarations: 225
Status: generated source-derived API shard

## ActiveMagicEffect

Source: `scripts/modified/ActiveMagicEffect.psc` · blob `3c0c0e3b6950ec1b98f06a657736488c7c8abf47`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetDuration` | `float Function GetDuration() native` | 2 |
| function | `GetTimeElapsed` | `float Function GetTimeElapsed() native` | 3 |
| function | `RegisterForKey` | `Function RegisterForKey(int keyCode) native` | 6 |
| function | `UnregisterForKey` | `Function UnregisterForKey(int keyCode) native` | 7 |
| function | `UnregisterForAllKeys` | `Function UnregisterForAllKeys() native` | 8 |
| event | `OnKeyDown` | `Event OnKeyDown(int keyCode)` | 10 |
| event | `OnKeyUp` | `Event OnKeyUp(int keyCode, float holdTime)` | 13 |
| function | `RegisterForControl` | `Function RegisterForControl(string control) native` | 18 |
| function | `UnregisterForControl` | `Function UnregisterForControl(string control) native` | 19 |
| function | `UnregisterForAllControls` | `Function UnregisterForAllControls() native` | 20 |
| event | `OnControlDown` | `Event OnControlDown(string control)` | 22 |
| event | `OnControlUp` | `Event OnControlUp(string control, float holdTime)` | 25 |
| function | `RegisterForMenu` | `Function RegisterForMenu(string menuName) native` | 31 |
| function | `UnregisterForMenu` | `Function UnregisterForMenu(string menuName) native` | 32 |
| function | `UnregisterForAllMenus` | `Function UnregisterForAllMenus() native` | 33 |
| event | `OnMenuOpen` | `Event OnMenuOpen(string menuName)` | 35 |
| event | `OnMenuClose` | `Event OnMenuClose(string menuName)` | 38 |
| function | `RegisterForModEvent` | `Function RegisterForModEvent(string eventName, string callbackName) native` | 51 |
| function | `UnregisterForModEvent` | `Function UnregisterForModEvent(string eventName) native` | 52 |
| function | `UnregisterForAllModEvents` | `Function UnregisterForAllModEvents() native` | 53 |
| function | `SendModEvent` | `Function SendModEvent(string eventName, string strArg = "", float numArg = 0.0) native` | 56 |
| function | `RegisterForCameraState` | `Function RegisterForCameraState() native` | 59 |
| function | `UnregisterForCameraState` | `Function UnregisterForCameraState() native` | 60 |
| event | `OnPlayerCameraState` | `Event OnPlayerCameraState(int oldState, int newState)` | 62 |
| function | `RegisterForCrosshairRef` | `Function RegisterForCrosshairRef() native` | 66 |
| function | `UnregisterForCrosshairRef` | `Function UnregisterForCrosshairRef() native` | 67 |
| event | `OnCrosshairRefChange` | `Event OnCrosshairRefChange(ObjectReference ref)` | 69 |
| function | `RegisterForActorAction` | `Function RegisterForActorAction(int actionType) native` | 73 |
| function | `UnregisterForActorAction` | `Function UnregisterForActorAction(int actionType) native` | 74 |
| event | `OnActorAction` | `Event OnActorAction(int actionType, Actor akActor, Form source, int slot)` | 76 |
| function | `RegisterForNiNodeUpdate` | `Function RegisterForNiNodeUpdate() native` | 80 |
| function | `UnregisterForNiNodeUpdate` | `Function UnregisterForNiNodeUpdate() native` | 81 |
| event | `OnNiNodeUpdate` | `Event OnNiNodeUpdate(ObjectReference akActor)` | 83 |
| function | `GetMagnitude` | `float Function GetMagnitude() native` | 87 |

## Actor

Source: `scripts/modified/Actor.psc` · blob `649cc9c43c994538fa35cd84d53fc1777db79f75`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetWornForm` | `Form Function GetWornForm(int slotMask) native` | 3 |
| function | `GetWornItemId` | `int Function GetWornItemId(int slotMask) native` | 6 |
| function | `GetEquippedObject` | `Form Function GetEquippedObject(int location) native` | 12 |
| function | `GetEquippedItemId` | `int Function GetEquippedItemId(int location) native` | 17 |
| function | `GetSpellCount` | `Int Function GetSpellCount() native` | 20 |
| function | `GetNthSpell` | `Spell Function GetNthSpell(int n) native` | 23 |
| function | `QueueNiNodeUpdate` | `Function QueueNiNodeUpdate() native` | 27 |
| function | `RegenerateHead` | `Function RegenerateHead() native` | 30 |
| property | `EquipSlot_Default` | `int Property EquipSlot_Default = 0 AutoReadOnly` | 32 |
| property | `EquipSlot_RightHand` | `int Property EquipSlot_RightHand = 1 AutoReadOnly` | 33 |
| property | `EquipSlot_LeftHand` | `int Property EquipSlot_LeftHand = 2 AutoReadOnly` | 34 |
| function | `EquipItemEx` | `Function EquipItemEx(Form item, int equipSlot = 0, bool preventUnequip = false, bool equipSound = true) native` | 37 |
| function | `EquipItemById` | `Function EquipItemById(Form item, int itemId, int equipSlot = 0, bool preventUnequip = false, bool equipSound = true) native` | 40 |
| function | `UnequipItemEx` | `Function UnequipItemEx(Form item, int equipSlot = 0, bool preventEquip = false) native` | 43 |
| function | `ChangeHeadPart` | `Function ChangeHeadPart(HeadPart hPart) native` | 47 |
| function | `ReplaceHeadPart` | `Function ReplaceHeadPart(HeadPart oPart, HeadPart newPart) native` | 51 |
| function | `UpdateWeight` | `Function UpdateWeight(float neckDelta) native` | 59 |
| function | `IsAIEnabled` | `bool Function IsAIEnabled() native` | 62 |
| function | `ResetAI` | `Function ResetAI() native` | 65 |
| function | `IsSwimming` | `bool Function IsSwimming() native` | 68 |
| function | `SheatheWeapon` | `Function SheatheWeapon() native` | 71 |
| function | `GetFurnitureReference` | `ObjectReference Function GetFurnitureReference() native` | 74 |
| function | `SetExpressionPhoneme` | `Function SetExpressionPhoneme(int index, float value) native` | 92 |
| function | `SetExpressionModifier` | `Function SetExpressionModifier(int index, float value) native` | 111 |
| function | `ResetExpressionOverrides` | `Function ResetExpressionOverrides() native` | 114 |
| function | `GetFactions` | `Faction[] Function GetFactions(int minRank, int maxRank) native` | 117 |

## ActorBase

Source: `scripts/modified/ActorBase.psc` · blob `403610ffb613f434b52c7657dfb87cfe019ead8f`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetCombatStyle` | `CombatStyle Function GetCombatStyle() native` | 2 |
| function | `SetCombatStyle` | `Function SetCombatStyle(CombatStyle cs) native` | 3 |
| function | `GetOutfit` | `Outfit Function GetOutfit(bool bSleepOutfit = false) native` | 6 |
| function | `SetClass` | `Function SetClass(Class c) native` | 9 |
| function | `GetHeight` | `float Function GetHeight() native` | 12 |
| function | `SetHeight` | `Function SetHeight(float height) native` | 13 |
| function | `GetWeight` | `float Function GetWeight() native` | 16 |
| function | `SetWeight` | `Function SetWeight(float weight) native` | 17 |
| function | `GetNumHeadParts` | `int Function GetNumHeadParts() native` | 20 |
| function | `GetNthHeadPart` | `HeadPart Function GetNthHeadPart(int slotPart) native` | 21 |
| function | `SetNthHeadPart` | `Function SetNthHeadPart(HeadPart headPart, int slotPart) native` | 22 |
| function | `GetIndexOfHeadPartByType` | `int Function GetIndexOfHeadPartByType(int type) native` | 23 |
| function | `GetNumOverlayHeadParts` | `int Function GetNumOverlayHeadParts() native` | 28 |
| function | `GetNthOverlayHeadPart` | `HeadPart Function GetNthOverlayHeadPart(int slotPart) native` | 29 |
| function | `GetIndexOfOverlayHeadPartByType` | `int Function GetIndexOfOverlayHeadPartByType(int type) native` | 30 |
| function | `GetFaceMorph` | `float Function GetFaceMorph(int index) native` | 33 |
| function | `SetFaceMorph` | `Function SetFaceMorph(float value, int index) native` | 34 |
| function | `GetFacePreset` | `int Function GetFacePreset(int index) native` | 41 |
| function | `SetFacePreset` | `Function SetFacePreset(int value, int index) native` | 42 |
| function | `GetHairColor` | `ColorForm Function GetHairColor() native` | 44 |
| function | `SetHairColor` | `Function SetHairColor(ColorForm color) native` | 45 |
| function | `GetSpellCount` | `int Function GetSpellCount() native` | 48 |
| function | `GetNthSpell` | `Spell Function GetNthSpell(int n) native` | 51 |
| function | `GetFaceTextureSet` | `TextureSet Function GetFaceTextureSet() native` | 54 |
| function | `SetFaceTextureSet` | `Function SetFaceTextureSet(TextureSet textures) native` | 55 |
| function | `GetVoiceType` | `VoiceType Function GetVoiceType() native` | 58 |
| function | `SetVoiceType` | `Function SetVoiceType(VoiceType nVoice) native` | 59 |
| function | `GetSkin` | `Armor Function GetSkin() native` | 62 |
| function | `SetSkin` | `Function SetSkin(Armor skin) native` | 63 |
| function | `GetSkinFar` | `Armor Function GetSkinFar() native` | 66 |
| function | `SetSkinFar` | `Function SetSkinFar(Armor skin) native` | 67 |
| function | `GetTemplate` | `ActorBase Function GetTemplate() native` | 70 |

## ActorValueInfo extends Form

Source: `scripts/modified/ActorValueInfo.psc` · blob `532acb37931f6f8d4151a824c58a438db97a567c`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetActorValueInfoByName` | `ActorValueInfo Function GetActorValueInfoByName(string avName) global native` | 4 |
| function | `GetAVIByName` | `ActorValueInfo Function GetAVIByName(string avName) global` | 5 |
| function | `GetActorValueInfoByID` | `ActorValueInfo Function GetActorValueInfoByID(int id) global native` | 10 |
| function | `GetAVIByID` | `ActorValueInfo Function GetAVIByID(int id) global` | 11 |
| function | `IsSkill` | `bool Function IsSkill() native` | 16 |
| function | `GetSkillUseMult` | `float Function GetSkillUseMult() native` | 19 |
| function | `SetSkillUseMult` | `Function SetSkillUseMult(float value) native` | 20 |
| function | `GetSkillOffsetMult` | `float Function GetSkillOffsetMult() native` | 22 |
| function | `SetSkillOffsetMult` | `Function SetSkillOffsetMult(float value) native` | 23 |
| function | `GetSkillImproveMult` | `float Function GetSkillImproveMult() native` | 25 |
| function | `SetSkillImproveMult` | `Function SetSkillImproveMult(float value) native` | 26 |
| function | `GetSkillImproveOffset` | `float Function GetSkillImproveOffset() native` | 28 |
| function | `SetSkillImproveOffset` | `Function SetSkillImproveOffset(float value) native` | 29 |
| function | `GetSkillExperience` | `float Function GetSkillExperience() native` | 32 |
| function | `SetSkillExperience` | `Function SetSkillExperience(float exp) native` | 35 |
| function | `AddSkillExperience` | `Function AddSkillExperience(float exp) native` | 38 |
| function | `GetExperienceForLevel` | `float Function GetExperienceForLevel(int currentLevel) native` | 42 |
| function | `GetSkillLegendaryLevel` | `int Function GetSkillLegendaryLevel() native` | 45 |
| function | `SetSkillLegendaryLevel` | `Function SetSkillLegendaryLevel(int level) native` | 48 |
| function | `GetPerkTree` | `Function GetPerkTree(FormList list, Actor akActor = None, bool unowned = true, bool allRanks = false) native` | 54 |
| function | `GetPerks` | `Perk[] Function GetPerks(Actor akActor = None, bool unowned = true, bool allRanks = false) native` | 57 |
| function | `GetCurrentValue` | `float Function GetCurrentValue(Actor akActor) native` | 60 |
| function | `GetBaseValue` | `float Function GetBaseValue(Actor akActor) native` | 63 |
| function | `GetMaximumValue` | `float Function GetMaximumValue(Actor akActor) native` | 66 |

## Alias

Source: `scripts/modified/Alias.psc` · blob `ff78ad5155f9f6f39dc603603ab6b4cb1d576eb7`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetName` | `string Function GetName() native` | 2 |
| function | `GetID` | `int Function GetID() native` | 5 |
| function | `RegisterForKey` | `Function RegisterForKey(int keyCode) native` | 8 |
| function | `UnregisterForKey` | `Function UnregisterForKey(int keyCode) native` | 9 |
| function | `UnregisterForAllKeys` | `Function UnregisterForAllKeys() native` | 10 |
| event | `OnKeyDown` | `Event OnKeyDown(int keyCode)` | 12 |
| event | `OnKeyUp` | `Event OnKeyUp(int keyCode, float holdTime)` | 15 |
| function | `RegisterForControl` | `Function RegisterForControl(string control) native` | 20 |
| function | `UnregisterForControl` | `Function UnregisterForControl(string control) native` | 21 |
| function | `UnregisterForAllControls` | `Function UnregisterForAllControls() native` | 22 |
| event | `OnControlDown` | `Event OnControlDown(string control)` | 24 |
| event | `OnControlUp` | `Event OnControlUp(string control, float holdTime)` | 27 |
| function | `RegisterForMenu` | `Function RegisterForMenu(string menuName) native` | 33 |
| function | `UnregisterForMenu` | `Function UnregisterForMenu(string menuName) native` | 34 |
| function | `UnregisterForAllMenus` | `Function UnregisterForAllMenus() native` | 35 |
| event | `OnMenuOpen` | `Event OnMenuOpen(string menuName)` | 37 |
| event | `OnMenuClose` | `Event OnMenuClose(string menuName)` | 40 |
| function | `RegisterForModEvent` | `Function RegisterForModEvent(string eventName, string callbackName) native` | 53 |
| function | `UnregisterForModEvent` | `Function UnregisterForModEvent(string eventName) native` | 54 |
| function | `UnregisterForAllModEvents` | `Function UnregisterForAllModEvents() native` | 55 |
| function | `SendModEvent` | `Function SendModEvent(string eventName, string strArg = "", float numArg = 0.0) native` | 58 |
| function | `RegisterForCameraState` | `Function RegisterForCameraState() native` | 61 |
| function | `UnregisterForCameraState` | `Function UnregisterForCameraState() native` | 62 |
| event | `OnPlayerCameraState` | `Event OnPlayerCameraState(int oldState, int newState)` | 64 |
| function | `RegisterForCrosshairRef` | `Function RegisterForCrosshairRef() native` | 68 |
| function | `UnregisterForCrosshairRef` | `Function UnregisterForCrosshairRef() native` | 69 |
| event | `OnCrosshairRefChange` | `Event OnCrosshairRefChange(ObjectReference ref)` | 71 |
| function | `RegisterForActorAction` | `Function RegisterForActorAction(int actionType) native` | 75 |
| function | `UnregisterForActorAction` | `Function UnregisterForActorAction(int actionType) native` | 76 |
| event | `OnActorAction` | `Event OnActorAction(int actionType, Actor akActor, Form source, int slot)` | 78 |
| function | `RegisterForNiNodeUpdate` | `Function RegisterForNiNodeUpdate() native` | 82 |
| function | `UnregisterForNiNodeUpdate` | `Function UnregisterForNiNodeUpdate() native` | 83 |
| event | `OnNiNodeUpdate` | `Event OnNiNodeUpdate(ObjectReference akActor)` | 85 |

## Ammo

Source: `scripts/modified/Ammo.psc` · blob `b009bbb04b5ed0cef7085bc3b84725f0c250760f`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `IsBolt` | `bool Function IsBolt() native` | 3 |
| function | `GetProjectile` | `Projectile Function GetProjectile() native` | 6 |
| function | `GetDamage` | `float Function GetDamage() native` | 9 |

## Apparatus

Source: `scripts/modified/Apparatus.psc` · blob `383592466cfc57c80432077b6f8543bfeae923a8`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetQuality` | `int Function GetQuality() native` | 2 |
| function | `SetQuality` | `Function SetQuality(int quality) native` | 3 |

## Armor

Source: `scripts/modified/Armor.psc` · blob `2265880835e0f5f3de5fca90a48e304371932b14`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetArmorRating` | `int Function GetArmorRating() native` | 1 |
| function | `GetAR` | `int Function GetAR()` | 2 |
| function | `SetArmorRating` | `Function SetArmorRating(int armorRating) native` | 6 |
| function | `SetAR` | `Function SetAR(int armorRating)` | 7 |
| function | `ModArmorRating` | `Function ModArmorRating(int modBy) native` | 11 |
| function | `ModAR` | `Function ModAR(int modBy)` | 12 |
| function | `GetModelPath` | `string Function GetModelPath(bool bFemalePath) native` | 17 |
| function | `SetModelPath` | `Function SetModelPath(string path, bool bFemalePath) native` | 18 |
| function | `GetIconPath` | `string Function GetIconPath(bool bFemalePath) native` | 21 |
| function | `SetIconPath` | `Function SetIconPath(string path, bool bFemalePath) native` | 22 |
| function | `GetMessageIconPath` | `string Function GetMessageIconPath(bool bFemalePath) native` | 25 |
| function | `SetMessageIconPath` | `Function SetMessageIconPath(string path, bool bFemalePath) native` | 26 |
| function | `GetWeightClass` | `int Function GetWeightClass() native` | 32 |
| function | `SetWeightClass` | `Function SetWeightClass(int weightClass) native` | 33 |
| function | `GetEnchantment` | `Enchantment Function GetEnchantment() native` | 36 |
| function | `SetEnchantment` | `Function SetEnchantment(Enchantment e) native` | 37 |
| function | `IsLightArmor` | `bool Function IsLightArmor()` | 40 |
| function | `IsHeavyArmor` | `bool Function IsHeavyArmor()` | 44 |
| function | `IsClothing` | `bool Function IsClothing()` | 48 |
| function | `IsBoots` | `bool Function IsBoots()` | 52 |
| function | `IsCuirass` | `bool Function IsCuirass()` | 56 |
| function | `IsGauntlets` | `bool Function IsGauntlets()` | 60 |
| function | `IsHelmet` | `bool Function IsHelmet()` | 64 |
| function | `IsShield` | `bool Function IsShield()` | 68 |
| function | `IsJewelry` | `bool Function IsJewelry()` | 72 |
| function | `IsClothingHead` | `bool Function IsClothingHead()` | 76 |
| function | `IsClothingBody` | `bool Function IsClothingBody()` | 80 |
| function | `IsClothingFeet` | `bool Function IsClothingFeet()` | 84 |
| function | `IsClothingHands` | `bool Function IsClothingHands()` | 88 |
| function | `IsClothingRing` | `bool Function IsClothingRing()` | 92 |
| function | `IsClothingRich` | `bool Function IsClothingRich()` | 96 |
| function | `IsClothingPoor` | `bool Function IsClothingPoor()` | 100 |
| function | `GetSlotMask` | `int Function GetSlotMask() native` | 110 |
| function | `SetSlotMask` | `Function SetSlotMask(int slotMask) native` | 112 |
| function | `AddSlotToMask` | `int Function AddSlotToMask(int slotMask) native` | 114 |
| function | `RemoveSlotFromMask` | `int Function RemoveSlotFromMask(int slotMask) native` | 116 |
| function | `GetMaskForSlot` | `int Function GetMaskForSlot(int slot) global native` | 119 |
| function | `GetNumArmorAddons` | `int Function GetNumArmorAddons() native` | 122 |
| function | `GetNthArmorAddon` | `ArmorAddon Function GetNthArmorAddon(int n) native` | 125 |
| property | `kSlotMask30` | `int Property kSlotMask30 = 0x00000001 AutoReadOnly` | 130 |
| property | `kSlotMask31` | `int Property kSlotMask31 = 0x00000002 AutoReadOnly` | 131 |
| property | `kSlotMask32` | `int Property kSlotMask32 = 0x00000004 AutoReadOnly` | 132 |
| property | `kSlotMask33` | `int Property kSlotMask33 = 0x00000008 AutoReadOnly` | 133 |
| property | `kSlotMask34` | `int Property kSlotMask34 = 0x00000010 AutoReadOnly` | 134 |
| property | `kSlotMask35` | `int Property kSlotMask35 = 0x00000020 AutoReadOnly` | 135 |
| property | `kSlotMask36` | `int Property kSlotMask36 = 0x00000040 AutoReadOnly` | 136 |
| property | `kSlotMask37` | `int Property kSlotMask37 = 0x00000080 AutoReadOnly` | 137 |
| property | `kSlotMask38` | `int Property kSlotMask38 = 0x00000100 AutoReadOnly` | 138 |
| property | `kSlotMask39` | `int Property kSlotMask39 = 0x00000200 AutoReadOnly` | 139 |
| property | `kSlotMask40` | `int Property kSlotMask40 = 0x00000400 AutoReadOnly` | 140 |
| property | `kSlotMask41` | `int Property kSlotMask41 = 0x00000800 AutoReadOnly` | 141 |
| property | `kSlotMask42` | `int Property kSlotMask42 = 0x00001000 AutoReadOnly` | 142 |
| property | `kSlotMask43` | `int Property kSlotMask43 = 0x00002000 AutoReadOnly` | 143 |
| property | `kSlotMask44` | `int Property kSlotMask44 = 0x00004000 AutoReadOnly` | 144 |
| property | `kSlotMask45` | `int Property kSlotMask45 = 0x00008000 AutoReadOnly` | 145 |
| property | `kSlotMask46` | `int Property kSlotMask46 = 0x00010000 AutoReadOnly` | 146 |
| property | `kSlotMask47` | `int Property kSlotMask47 = 0x00020000 AutoReadOnly` | 147 |
| property | `kSlotMask48` | `int Property kSlotMask48 = 0x00040000 AutoReadOnly` | 148 |
| property | `kSlotMask49` | `int Property kSlotMask49 = 0x00080000 AutoReadOnly` | 149 |
| property | `kSlotMask50` | `int Property kSlotMask50 = 0x00100000 AutoReadOnly` | 150 |
| property | `kSlotMask51` | `int Property kSlotMask51 = 0x00200000 AutoReadOnly` | 151 |
| property | `kSlotMask52` | `int Property kSlotMask52 = 0x00400000 AutoReadOnly` | 152 |
| property | `kSlotMask53` | `int Property kSlotMask53 = 0x00800000 AutoReadOnly` | 153 |
| property | `kSlotMask54` | `int Property kSlotMask54 = 0x01000000 AutoReadOnly` | 154 |
| property | `kSlotMask55` | `int Property kSlotMask55 = 0x02000000 AutoReadOnly` | 155 |
| property | `kSlotMask56` | `int Property kSlotMask56 = 0x04000000 AutoReadOnly` | 156 |
| property | `kSlotMask57` | `int Property kSlotMask57 = 0x08000000 AutoReadOnly` | 157 |
| property | `kSlotMask58` | `int Property kSlotMask58 = 0x10000000 AutoReadOnly` | 158 |
| property | `kSlotMask59` | `int Property kSlotMask59 = 0x20000000 AutoReadOnly` | 159 |
| property | `kSlotMask60` | `int Property kSlotMask60 = 0x40000000 AutoReadOnly` | 160 |
| property | `kSlotMask61` | `int Property kSlotMask61 = 0x80000000 AutoReadOnly` | 161 |

