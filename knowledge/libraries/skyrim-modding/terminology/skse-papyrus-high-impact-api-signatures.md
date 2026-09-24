# High-Impact SKSE Papyrus API Signatures

Imported: 2026-09-24
Upstream: `ianpatt/skse64` master
Status: source-derived provider reference

## Scope

These are exact declaration lines from high-impact PSC classes distributed in SKSE's `scripts/modified` tree.

Important: this is **the SKSE-provided class surface**, not an additions-only diff against vanilla. A later vanilla-vs-SKSE reconciliation pass should classify which declarations are genuinely added or changed by SKSE.

## Game

Source blob: `7cdffab32bd2d7449575899376c9c1372925cf08`

| Line | Declaration |
|---:|---|
| 2 | `int Function GetPerkPoints() global native` |
| 3 | `Function SetPerkPoints(int perkPoints) global native` |
| 4 | `Function ModPerkPoints(int perkPoints) global native` |
| 7 | `int Function GetModCount() native global` |
| 10 | `int Function GetModByName(string name) native global` |
| 13 | `string Function GetModName(int modIndex) native global` |
| 16 | `string Function GetModAuthor(int modIndex) native global` |
| 19 | `string Function GetModDescription(int modIndex) native global` |
| 22 | `int Function GetModDependencyCount(int modIndex) native global` |
| 27 | `bool Function IsPluginInstalled(string name) native global` |
| 30 | `int Function GetLightModCount() native global` |
| 31 | `int Function GetLightModByName(string name) native global` |
| 32 | `string Function GetLightModName(int idx) native global` |
| 33 | `string Function GetLightModAuthor(int idx) native global` |
| 34 | `string Function GetLightModDescription(int idx) native global` |
| 35 | `int Function GetLightModDependencyCount(int idx) native global` |
| 36 | `int Function GetNthLightModDependency(int modIdx, int idx) native global` |
| 39 | `Function SetGameSettingFloat(string setting, float value) global native` |
| 40 | `Function SetGameSettingInt(string setting, int value) global native` |
| 41 | `Function SetGameSettingBool(string setting, bool value) global native` |
| 42 | `Function SetGameSettingString(string setting, string value) global native` |
| 45 | `Function SaveGame(string name) native global` |
| 46 | `Function LoadGame(string name) native global` |
| 51 | `int Function GetNumTintMasks() native global` |
| 54 | `int Function GetNthTintMaskColor(int n) native global` |
| 57 | `int Function GetNthTintMaskType(int n) native global` |
| 60 | `Function SetNthTintMaskColor(int n, int color) native global` |
| 63 | `string Function GetNthTintMaskTexturePath(int n) native global` |
| 66 | `Function SetNthTintMaskTexturePath(string path, int n) native global` |
| 86 | `int Function GetNumTintsByType(int type) native global` |
| 89 | `int Function GetTintMaskColor(int type, int index) global native` |
| 92 | `Function SetTintMaskColor(int color, int type, int index) global native` |
| 95 | `string Function GetTintMaskTexturePath(int type, int index) global native` |
| 98 | `Function SetTintMaskTexturePath(string path, int type, int index) global native` |
| 101 | `Function UpdateTintMaskColors() global native` |
| 104 | `Function UpdateHairColor() global native` |
| 120 | `int Function GetCameraState() global` |
| 126 | `Function SetMiscStat(string name, int value) global native` |
| 129 | `Function SetPlayersLastRiddenHorse(Actor horse) global native` |
| 134 | `int Function GetSkillLegendaryLevel(string actorValue) global` |
| 140 | `Function SetSkillLegendaryLevel(string actorValue, int level) global` |
| 145 | `float Function GetPlayerExperience() global native` |
| 148 | `Function SetPlayerExperience(float exp) global native` |
| 152 | `float Function GetExperienceForLevel(int currentLevel) global native` |
| 156 | `bool Function GetPlayerMovementMode() global native` |
| 159 | `Function UpdateThirdPerson() global` |
| 165 | `Function UnbindObjectHotkey(int hotkey) global native` |
| 168 | `Form Function GetHotkeyBoundObject(int hotkey) global native` |
| 171 | `bool Function IsObjectFavorited(Form form) global native` |
| 174 | `Form Function GetFormEx(int formId) global native` |
| 177 | `ObjectReference Function GetDialogueTarget() global native` |
| 180 | `ObjectReference Function GetCurrentCrosshairRef() global native` |
| 183 | `ObjectReference Function GetCurrentConsoleRef() global native` |
| 186 | `Function SetPlayerLevel(int level) global native` |

## Form

Source blob: `c8410ae0d52383d03c214e0e07d402211b5cef67`

| Line | Declaration |
|---:|---|
| 3 | `Int Function GetType() native` |
| 6 | `string Function GetName() native` |
| 9 | `Function SetName(string name) native` |
| 12 | `float Function GetWeight() native` |
| 15 | `Function SetWeight(float weight) native` |
| 18 | `Function SetGoldValue(int value) native` |
| 21 | `int Function GetNumKeywords() native` |
| 24 | `Keyword Function GetNthKeyword(int index) native` |
| 27 | `Keyword[] Function GetKeywords() native` |
| 29 | `bool Function HasKeywordString(string s)` |
| 40 | `Function SetPlayerKnows(bool knows) native` |
| 43 | `Function RegisterForKey(int keyCode) native` |
| 44 | `Function UnregisterForKey(int keyCode) native` |
| 45 | `Function UnregisterForAllKeys() native` |
| 47 | `Event OnKeyDown(int keyCode)` |
| 50 | `Event OnKeyUp(int keyCode, float holdTime)` |
| 55 | `Function RegisterForControl(string control) native` |
| 56 | `Function UnregisterForControl(string control) native` |
| 57 | `Function UnregisterForAllControls() native` |
| 59 | `Event OnControlDown(string control)` |
| 62 | `Event OnControlUp(string control, float holdTime)` |
| 68 | `Function RegisterForMenu(string menuName) native` |
| 69 | `Function UnregisterForMenu(string menuName) native` |
| 70 | `Function UnregisterForAllMenus() native` |
| 72 | `Event OnMenuOpen(string menuName)` |
| 75 | `Event OnMenuClose(string menuName)` |
| 88 | `Function RegisterForModEvent(string eventName, string callbackName) native` |
| 89 | `Function UnregisterForModEvent(string eventName) native` |
| 90 | `Function UnregisterForAllModEvents() native` |
| 93 | `Function SendModEvent(string eventName, string strArg = "", float numArg = 0.0) native` |
| 96 | `Function RegisterForCameraState() native` |
| 97 | `Function UnregisterForCameraState() native` |
| 99 | `Event OnPlayerCameraState(int oldState, int newState)` |
| 103 | `Function RegisterForCrosshairRef() native` |
| 104 | `Function UnregisterForCrosshairRef() native` |
| 107 | `Event OnCrosshairRefChange(ObjectReference ref)` |
| 110 | `Function RegisterForActorAction(int actionType) native` |
| 111 | `Function UnregisterForActorAction(int actionType) native` |
| 129 | `Event OnActorAction(int actionType, Actor akActor, Form source, int slot)` |
| 133 | `Function RegisterForNiNodeUpdate() native` |
| 134 | `Function UnregisterForNiNodeUpdate() native` |
| 136 | `Event OnNiNodeUpdate(ObjectReference akActor)` |
| 140 | `Form Function TempClone() native` |
| 143 | `bool Function HasWorldModel() native` |
| 146 | `string Function GetWorldModelPath() native` |
| 147 | `Function SetWorldModelPath(string path) native` |
| 150 | `int Function GetWorldModelNumTextureSets() native` |
| 153 | `TextureSet Function GetWorldModelNthTextureSet(int n) native` |
| 156 | `Function SetWorldModelNthTextureSet(TextureSet nSet, int n) native` |
| 159 | `bool Function IsPlayable() native` |

## ObjectReference

Source blob: `923ec3de4692cf2446bf5aa5f703b3cb594a5774`

| Line | Declaration |
|---:|---|
| 3 | `int Function GetNumItems() native` |
| 4 | `Form Function GetNthForm(int index) native` |
| 5 | `float Function GetTotalItemWeight() native` |
| 6 | `float Function GetTotalArmorWeight() native` |
| 9 | `bool Function IsHarvested() native` |
| 10 | `Function SetHarvested(bool harvested) native` |
| 13 | `Function SetItemHealthPercent(float health) native` |
| 18 | `Function SetItemMaxCharge(float maxCharge) native` |
| 20 | `float Function GetItemMaxCharge() native` |
| 22 | `float Function GetItemCharge() native` |
| 23 | `Function SetItemCharge(float charge) native` |
| 25 | `Function ResetInventory() native` |
| 27 | `bool Function IsOffLimits() native` |
| 31 | `string Function GetDisplayName() native` |
| 37 | `bool Function SetDisplayName(string name, bool force = false) native` |
| 40 | `ObjectReference Function GetEnableParent() native` |
| 43 | `Enchantment Function GetEnchantment() native` |
| 48 | `Function SetEnchantment(Enchantment source, float maxCharge) native` |
| 54 | `Function CreateEnchantment(float maxCharge, MagicEffect[] effects, float[] magnitudes, int[] areas, int[] durations) native` |
| 57 | `int Function GetNumReferenceAliases() native` |
| 60 | `ReferenceAlias Function GetNthReferenceAlias(int n) native` |
| 63 | `Potion Function GetPoison() native` |
| 66 | `Function GetAllForms(FormList toFill) native` |
| 69 | `Form[] Function GetContainerForms() native` |
| 72 | `ReferenceAlias[] Function GetReferenceAliases() native` |

## Actor

Source blob: `649cc9c43c994538fa35cd84d53fc1777db79f75`

| Line | Declaration |
|---:|---|
| 3 | `Form Function GetWornForm(int slotMask) native` |
| 6 | `int Function GetWornItemId(int slotMask) native` |
| 12 | `Form Function GetEquippedObject(int location) native` |
| 17 | `int Function GetEquippedItemId(int location) native` |
| 20 | `Int Function GetSpellCount() native` |
| 23 | `Spell Function GetNthSpell(int n) native` |
| 27 | `Function QueueNiNodeUpdate() native` |
| 30 | `Function RegenerateHead() native` |
| 37 | `Function EquipItemEx(Form item, int equipSlot = 0, bool preventUnequip = false, bool equipSound = true) native` |
| 40 | `Function EquipItemById(Form item, int itemId, int equipSlot = 0, bool preventUnequip = false, bool equipSound = true) native` |
| 43 | `Function UnequipItemEx(Form item, int equipSlot = 0, bool preventEquip = false) native` |
| 47 | `Function ChangeHeadPart(HeadPart hPart) native` |
| 51 | `Function ReplaceHeadPart(HeadPart oPart, HeadPart newPart) native` |
| 59 | `Function UpdateWeight(float neckDelta) native` |
| 62 | `bool Function IsAIEnabled() native` |
| 65 | `Function ResetAI() native` |
| 68 | `bool Function IsSwimming() native` |
| 71 | `Function SheatheWeapon() native` |
| 74 | `ObjectReference Function GetFurnitureReference() native` |
| 92 | `Function SetExpressionPhoneme(int index, float value) native` |
| 111 | `Function SetExpressionModifier(int index, float value) native` |
| 114 | `Function ResetExpressionOverrides() native` |
| 117 | `Faction[] Function GetFactions(int minRank, int maxRank) native` |

## ActorBase

Source blob: `403610ffb613f434b52c7657dfb87cfe019ead8f`

| Line | Declaration |
|---:|---|
| 2 | `CombatStyle Function GetCombatStyle() native` |
| 3 | `Function SetCombatStyle(CombatStyle cs) native` |
| 6 | `Outfit Function GetOutfit(bool bSleepOutfit = false) native` |
| 9 | `Function SetClass(Class c) native` |
| 12 | `float Function GetHeight() native` |
| 13 | `Function SetHeight(float height) native` |
| 16 | `float Function GetWeight() native` |
| 17 | `Function SetWeight(float weight) native` |
| 20 | `int Function GetNumHeadParts() native` |
| 21 | `HeadPart Function GetNthHeadPart(int slotPart) native` |
| 22 | `Function SetNthHeadPart(HeadPart headPart, int slotPart) native` |
| 23 | `int Function GetIndexOfHeadPartByType(int type) native` |
| 28 | `int Function GetNumOverlayHeadParts() native` |
| 29 | `HeadPart Function GetNthOverlayHeadPart(int slotPart) native` |
| 30 | `int Function GetIndexOfOverlayHeadPartByType(int type) native` |
| 33 | `float Function GetFaceMorph(int index) native` |
| 34 | `Function SetFaceMorph(float value, int index) native` |
| 41 | `int Function GetFacePreset(int index) native` |
| 42 | `Function SetFacePreset(int value, int index) native` |
| 44 | `ColorForm Function GetHairColor() native` |
| 45 | `Function SetHairColor(ColorForm color) native` |
| 48 | `int Function GetSpellCount() native` |
| 51 | `Spell Function GetNthSpell(int n) native` |
| 54 | `TextureSet Function GetFaceTextureSet() native` |
| 55 | `Function SetFaceTextureSet(TextureSet textures) native` |
| 58 | `VoiceType Function GetVoiceType() native` |
| 59 | `Function SetVoiceType(VoiceType nVoice) native` |
| 62 | `Armor Function GetSkin() native` |
| 63 | `Function SetSkin(Armor skin) native` |
| 66 | `Armor Function GetSkinFar() native` |
| 67 | `Function SetSkinFar(Armor skin) native` |
| 70 | `ActorBase Function GetTemplate() native` |

## ActiveMagicEffect

Source blob: `3c0c0e3b6950ec1b98f06a657736488c7c8abf47`

| Line | Declaration |
|---:|---|
| 2 | `float Function GetDuration() native` |
| 3 | `float Function GetTimeElapsed() native` |
| 6 | `Function RegisterForKey(int keyCode) native` |
| 7 | `Function UnregisterForKey(int keyCode) native` |
| 8 | `Function UnregisterForAllKeys() native` |
| 10 | `Event OnKeyDown(int keyCode)` |
| 13 | `Event OnKeyUp(int keyCode, float holdTime)` |
| 18 | `Function RegisterForControl(string control) native` |
| 19 | `Function UnregisterForControl(string control) native` |
| 20 | `Function UnregisterForAllControls() native` |
| 22 | `Event OnControlDown(string control)` |
| 25 | `Event OnControlUp(string control, float holdTime)` |
| 31 | `Function RegisterForMenu(string menuName) native` |
| 32 | `Function UnregisterForMenu(string menuName) native` |
| 33 | `Function UnregisterForAllMenus() native` |
| 35 | `Event OnMenuOpen(string menuName)` |
| 38 | `Event OnMenuClose(string menuName)` |
| 51 | `Function RegisterForModEvent(string eventName, string callbackName) native` |
| 52 | `Function UnregisterForModEvent(string eventName) native` |
| 53 | `Function UnregisterForAllModEvents() native` |
| 56 | `Function SendModEvent(string eventName, string strArg = "", float numArg = 0.0) native` |
| 59 | `Function RegisterForCameraState() native` |
| 60 | `Function UnregisterForCameraState() native` |
| 62 | `Event OnPlayerCameraState(int oldState, int newState)` |
| 66 | `Function RegisterForCrosshairRef() native` |
| 67 | `Function UnregisterForCrosshairRef() native` |
| 69 | `Event OnCrosshairRefChange(ObjectReference ref)` |
| 73 | `Function RegisterForActorAction(int actionType) native` |
| 74 | `Function UnregisterForActorAction(int actionType) native` |
| 76 | `Event OnActorAction(int actionType, Actor akActor, Form source, int slot)` |
| 80 | `Function RegisterForNiNodeUpdate() native` |
| 81 | `Function UnregisterForNiNodeUpdate() native` |
| 83 | `Event OnNiNodeUpdate(ObjectReference akActor)` |
| 87 | `float Function GetMagnitude() native` |

## MagicEffect

Source blob: `83e758ef08f1cb34050711a996192eddbbdbf467`

| Line | Declaration |
|---:|---|
| 1 | `Function SetAssociatedSkill(string skill) native` |
| 3 | `string Function GetResistance() native` |
| 4 | `Function SetResistance(string skill) native` |
| 24 | `bool Function IsEffectFlagSet(int flag) native` |
| 25 | `Function SetEffectFlag(int flag) native` |
| 26 | `Function ClearEffectFlag(int flag) native` |
| 28 | `float Function GetCastTime() native` |
| 29 | `Function SetCastTime(float castTime) native` |
| 31 | `int Function GetSkillLevel() native` |
| 32 | `Function SetSkillLevel(int level) native` |
| 34 | `int Function GetArea() native` |
| 35 | `Function SetArea(int area) native` |
| 37 | `float Function GetSkillUsageMult() native` |
| 38 | `Function SetSkillUsageMult(float usageMult) native` |
| 40 | `float Function GetBaseCost() native` |
| 41 | `Function SetBaseCost(float cost) native` |
| 43 | `Light Function GetLight() native` |
| 44 | `Function SetLight(Light obj) native` |
| 46 | `EffectShader Function GetHitShader() native` |
| 47 | `Function SetHitShader(EffectShader obj) native` |
| 49 | `EffectShader Function GetEnchantShader() native` |
| 50 | `Function SetEnchantShader(EffectShader obj) native` |
| 52 | `Projectile Function GetProjectile() native` |
| 53 | `Function SetProjectile(Projectile obj) native` |
| 55 | `Explosion Function GetExplosion() native` |
| 56 | `Function SetExplosion(Explosion obj) native` |
| 58 | `Art Function GetCastingArt() native` |
| 59 | `Function SetCastingArt(Art obj) native` |
| 61 | `Art Function GetHitEffectArt() native` |
| 62 | `Function SetHitEffectArt(Art obj) native` |
| 64 | `Art Function GetEnchantArt() native` |
| 65 | `Function SetEnchantArt(Art obj) native` |
| 67 | `ImpactDataSet Function GetImpactDataSet() native` |
| 68 | `Function SetImpactDataSet(ImpactDataSet obj) native` |
| 70 | `Spell Function GetEquipAbility() native` |
| 71 | `Function SetEquipAbility(Spell obj) native` |
| 73 | `ImageSpaceModifier Function GetImageSpaceMod() native` |
| 74 | `Function SetImageSpaceMod(ImageSpaceModifier obj) native` |
| 76 | `Perk Function GetPerk() native` |
| 77 | `Function SetPerk(Perk obj) native` |
| 79 | `int Function GetCastingType() native` |
| 84 | `int Function GetDeliveryType() native` |
| 93 | `Sound[] Function GetSounds() native` |

## UI

Source blob: `2a8f18921c3ba382ea326ae677c686e75f8db99d`

| Line | Declaration |
|---:|---|
| 47 | `bool Function IsMenuOpen(string menuName) global native` |
| 57 | `Function SetBool(string menuName, string target, bool value) global native` |
| 58 | `Function SetInt(string menuName, string target, int value) global native` |
| 59 | `Function SetFloat(string menuName, string target, float value) global native` |
| 60 | `Function SetString(string menuName, string target, string value) global native` |
| 61 | `Function SetNumber(string menuName, string target, float value) global` |
| 71 | `bool	Function GetBool(string menuName, string target) global native` |
| 72 | `int		Function GetInt(string menuName, string target) global native` |
| 73 | `float	Function GetFloat(string menuName, string target) global native` |
| 74 | `string	Function GetString(string menuName, string target) global native` |
| 75 | `float	Function GetNumber(string menuName, string target) global` |
| 86 | `Function Invoke(string menuName, string target) global` |
| 90 | `Function InvokeBool(string menuName, string target, bool arg) global native` |
| 91 | `Function InvokeInt(string menuName, string target, int arg) global native` |
| 92 | `Function InvokeFloat(string menuName, string target, float arg) global native` |
| 93 | `Function InvokeString(string menuName, string target, string arg) global native` |
| 94 | `Function InvokeNumber(string menuName, string target, float arg) global` |
| 98 | `Function InvokeBoolA(string menuName, string target, bool[] args) global native` |
| 99 | `Function InvokeIntA(string menuName, string target, int[] args) global native` |
| 100 | `Function InvokeFloatA(string menuName, string target, float[] args) global native` |
| 101 | `Function InvokeStringA(string menuName, string target, string[] args) global native` |
| 102 | `Function InvokeNumberA(string menuName, string target, float[] args) global` |
| 107 | `Function InvokeForm(string menuName, string target, Form arg) global native` |
| 111 | `bool Function IsTextInputEnabled() global native` |
| 116 | `Function OpenCustomMenu(string swfPath, int flags = 0) global native` |
| 119 | `Function CloseCustomMenu() global native` |

## Input

Source blob: `14e380527f376cf41e875b8951233f285facaade`

| Line | Declaration |
|---:|---|
| 4 | `bool Function IsKeyPressed(Int dxKeycode) global native` |
| 7 | `Function TapKey(Int dxKeycode) global native` |
| 10 | `Function HoldKey(Int dxKeycode) global native` |
| 13 | `Function ReleaseKey(Int dxKeycode) global native` |
| 16 | `int Function GetNumKeysPressed() global native` |
| 19 | `int Function GetNthKeyPressed(int n) global native` |
| 35 | `int Function GetMappedKey(string control, int deviceType = 0xFF) global native` |
| 38 | `string Function GetMappedControl(int keycode) global native` |

## NetImmerse

Source blob: `066111beac8a8fe882bbf732b82c8345f1db74dd`

| Line | Declaration |
|---:|---|
| 7 | `bool Function HasNode(ObjectReference ref, string node, bool firstPerson) native global` |
| 10 | `float Function GetNodeWorldPositionX(ObjectReference ref, string node, bool firstPerson) native global` |
| 11 | `float Function GetNodeWorldPositionY(ObjectReference ref, string node, bool firstPerson) native global` |
| 12 | `float Function GetNodeWorldPositionZ(ObjectReference ref, string node, bool firstPerson) native global` |
| 15 | `float Function GetRelativeNodePositionX(ObjectReference ref, string nodeA, string nodeB, bool firstPerson) native global` |
| 16 | `float Function GetRelativeNodePositionY(ObjectReference ref, string nodeA, string nodeB, bool firstPerson) native global` |
| 17 | `float Function GetRelativeNodePositionZ(ObjectReference ref, string nodeA, string nodeB, bool firstPerson) native global` |
| 19 | `float Function GetNodeLocalPositionX(ObjectReference ref, string node, bool firstPerson) native global` |
| 20 | `float Function GetNodeLocalPositionY(ObjectReference ref, string node, bool firstPerson) native global` |
| 21 | `float Function GetNodeLocalPositionZ(ObjectReference ref, string node, bool firstPerson) native global` |
| 23 | `Function SetNodeLocalPositionX(ObjectReference ref, string node, float x, bool firstPerson) native global` |
| 24 | `Function SetNodeLocalPositionY(ObjectReference ref, string node, float y, bool firstPerson) native global` |
| 25 | `Function SetNodeLocalPositionZ(ObjectReference ref, string node, float z, bool firstPerson) native global` |
| 28 | `float Function GetNodeScale(ObjectReference ref, string node, bool firstPerson) native global` |
| 29 | `Function SetNodeScale(ObjectReference ref, string node, float scale, bool firstPerson) native global` |
| 32 | `Function SetNodeTextureSet(ObjectReference ref, string node, TextureSet tSet, bool firstPerson) native global` |
| 38 | `bool Function GetNodeWorldPosition(ObjectReference ref, string node, float[] in, bool firstPerson) native global` |
| 41 | `bool Function GetRelativeNodePosition(ObjectReference ref, string nodeA, string nodeB, float[] in, bool firstPerson) native global` |
| 44 | `bool Function GetNodeLocalPosition(ObjectReference ref, string node, float[] in, bool firstPerson) native global` |
| 47 | `bool Function SetNodeLocalPosition(ObjectReference ref, string node, float[] in, bool firstPerson) native global` |
| 51 | `bool Function GetNodeWorldRotationEuler(ObjectReference ref, string node, float[] in, bool firstPerson) native global` |
| 54 | `bool Function GetNodeLocalRotationEuler(ObjectReference ref, string node, float[] in, bool firstPerson) native global` |
| 57 | `bool Function SetNodeLocalRotationEuler(ObjectReference ref, string node, float[] in, bool firstPerson) native global` |
| 61 | `bool Function GetNodeWorldRotationMatrix(ObjectReference ref, string node, float[] in, bool firstPerson) native global` |
| 64 | `bool Function GetNodeLocalRotationMatrix(ObjectReference ref, string node, float[] in, bool firstPerson) native global` |
| 67 | `bool Function SetNodeLocalRotationMatrix(ObjectReference ref, string node, float[] in, bool firstPerson) native global` |
| 71 | `Function SetNodePositionX(ObjectReference ref, string node, float x, bool firstPerson) global` |
| 74 | `Function SetNodePositionY(ObjectReference ref, string node, float y, bool firstPerson) global` |
| 77 | `Function SetNodePositionZ(ObjectReference ref, string node, float z, bool firstPerson) global` |
| 81 | `float Function GetNodePositionX(ObjectReference ref, string node, bool firstPerson) global` |
| 84 | `float Function GetNodePositionY(ObjectReference ref, string node, bool firstPerson) global` |
| 87 | `float Function GetNodePositionZ(ObjectReference ref, string node, bool firstPerson) global` |

## Utility

Source blob: `c8d5405fa2738cacfce57086f22f9a43dcab8a34`

| Line | Declaration |
|---:|---|
| 2 | `float Function GetINIFloat(string ini) global native` |
| 3 | `int Function GetINIInt(string ini) global native` |
| 4 | `bool Function GetINIBool(string ini) global native` |
| 5 | `string Function GetINIString(string ini) global native` |
| 10 | `float[] Function CreateFloatArray(int size, float fill = 0.0) global native` |
| 11 | `int[] Function CreateIntArray(int size, int fill = 0) global native` |
| 12 | `bool[] Function CreateBoolArray(int size, bool fill = false) global native` |
| 13 | `string[] Function CreateStringArray(int size, string fill = "") global native` |
| 14 | `Form[] Function CreateFormArray(int size, Form fill = None) global native` |
| 15 | `Alias[] Function CreateAliasArray(int size, Alias fill = None) global native` |
| 17 | `float[] Function ResizeFloatArray(float[] source, int size, float fill = 0.0) global native` |
| 18 | `int[] Function ResizeIntArray(int[] source, int size, int fill = 0) global native` |
| 19 | `bool[] Function ResizeBoolArray(bool[] source, int size, bool fill = false) global native` |
| 20 | `string[] Function ResizeStringArray(string[] source, int size, string fill = "") global native` |
| 21 | `Form[] Function ResizeFormArray(Form[] source, int size, Form fill = None) global native` |
| 22 | `Alias[] Function ResizeAliasArray(Alias[] source, int size, Alias fill = None) global native` |

## WornObject

Source blob: `94f844cc13d780a837aa984b9b240441cbed5562`

| Line | Declaration |
|---:|---|
| 13 | `float Function GetItemHealthPercent(Actor akActor, int handSlot, int slotMask) global native` |
| 14 | `Function SetItemHealthPercent(Actor akActor, int handSlot, int slotMask, float health) global native` |
| 18 | `Function SetItemMaxCharge(Actor akActor, int handSlot, int slotMask, float maxCharge) global native` |
| 21 | `float Function GetItemMaxCharge(Actor akActor, int handSlot, int slotMask) global native` |
| 23 | `float Function GetItemCharge(Actor akActor, int handSlot, int slotMask) global native` |
| 30 | `string Function GetDisplayName(Actor akActor, int handSlot, int slotMask) global native` |
| 36 | `bool Function SetDisplayName(Actor akActor, int handSlot, int slotMask, string name, bool force = false) global native` |
| 39 | `Enchantment Function GetEnchantment(Actor akActor, int handSlot, int slotMask) global native` |
| 44 | `Function SetEnchantment(Actor akActor, int handSlot, int slotMask, Enchantment source, float maxCharge) global native` |
| 50 | `Function CreateEnchantment(Actor akActor, int handSlot, int slotMask, float maxCharge, MagicEffect[] effects, float[] magnitudes, int[] areas, int[] durations) global native` |
| 53 | `int Function GetNumReferenceAliases(Actor akActor, int handSlot, int slotMask) global native` |
| 56 | `ReferenceAlias Function GetNthReferenceAlias(Actor akActor, int handSlot, int slotMask, int n) global native` |
| 59 | `Potion Function GetPoison(Actor akActor, int handSlot, int slotMask) global native` |
| 62 | `ReferenceAlias[] Function GetReferenceAliases(Actor akActor, int handSlot, int slotMask) global native` |

## Diagnostic use

- If a script compiles against a declaration here but fails with **native function not found**, the supplying SKSE/runtime registration failed or the installed PEX/source generation does not match the runtime.
- `ObjectReference`/ `WornObject` methods often act on instance ExtraData rather than changing the base form.
- `ActorBase` changes shared NPC_ template data; `Actor` changes one runtime actor/reference.
- `NetImmerse` node calls require compatible/loaded 3D.
- `UI` calls require exact menu paths/Scaleform targets.
- `Game` plugin/load-order methods must distinguish full and light plugins.
- Registration events on Form/ActiveMagicEffect are lifecycle state and may persist in saves.
