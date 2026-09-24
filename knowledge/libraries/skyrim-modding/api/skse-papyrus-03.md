# SKSE64 Modified Papyrus API — Shard 3

Imported: 2026-09-24
Source: `ianpatt/skse64` master
Scripts: 8 · declarations: 116
Status: generated source-derived API shard

## ConstructibleObject

Source: `scripts/modified/ConstructibleObject.psc` · blob `2168670f2d79c36b33f176615291741b6ad26b3f`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetResult` | `Form Function GetResult() native` | 3 |
| function | `SetResult` | `Function SetResult(Form result) native` | 4 |
| function | `GetResultQuantity` | `int Function GetResultQuantity() native` | 7 |
| function | `SetResultQuantity` | `Function SetResultQuantity(int quantity) native` | 8 |
| function | `GetNumIngredients` | `int Function GetNumIngredients() native` | 11 |
| function | `GetNthIngredient` | `Form Function GetNthIngredient(int n) native` | 14 |
| function | `SetNthIngredient` | `Function SetNthIngredient(Form required, int n) native` | 15 |
| function | `GetNthIngredientQuantity` | `int Function GetNthIngredientQuantity(int n) native` | 18 |
| function | `SetNthIngredientQuantity` | `Function SetNthIngredientQuantity(int value, int n) native` | 19 |
| function | `GetWorkbenchKeyword` | `Keyword Function GetWorkbenchKeyword() native` | 22 |
| function | `SetWorkbenchKeyword` | `Function SetWorkbenchKeyword(Keyword aKeyword) native` | 23 |

## DefaultObjectManager extends Form

Source: `scripts/modified/DefaultObjectManager.psc` · blob `33d9ed0f3e3111f65a2c7ef8db09e335bcb40250`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetForm` | `Form Function GetForm(string key) native` | 4 |
| function | `SetForm` | `Function SetForm(string key, Form newForm) native` | 7 |

## Enchantment

Source: `scripts/modified/Enchantment.psc` · blob `d2b8e0f0d367fdf898c4d1641ac4a5f9dd23931d`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetNumEffects` | `int Function GetNumEffects() native` | 2 |
| function | `GetNthEffectMagnitude` | `float Function GetNthEffectMagnitude(int index) native` | 5 |
| function | `GetNthEffectArea` | `int Function GetNthEffectArea(int index) native` | 8 |
| function | `GetNthEffectDuration` | `int Function GetNthEffectDuration(int index) native` | 11 |
| function | `GetNthEffectMagicEffect` | `MagicEffect Function GetNthEffectMagicEffect(int index) native` | 14 |
| function | `GetCostliestEffectIndex` | `int Function GetCostliestEffectIndex() native` | 17 |
| function | `SetNthEffectMagnitude` | `Function SetNthEffectMagnitude(int index, float value) native` | 20 |
| function | `SetNthEffectArea` | `Function SetNthEffectArea(int index, int value) native` | 23 |
| function | `SetNthEffectDuration` | `Function SetNthEffectDuration(int index, int value) native` | 26 |
| function | `GetBaseEnchantment` | `Enchantment Function GetBaseEnchantment() native` | 29 |
| function | `GetKeywordRestrictions` | `FormList Function GetKeywordRestrictions() native` | 32 |
| function | `SetKeywordRestrictions` | `Function SetKeywordRestrictions(FormList newKeywordList) native` | 35 |

## EquipSlot extends Form

Source: `scripts/modified/EquipSlot.psc` · blob `18bc9631ad52219771d8ff51105058b74661d0c4`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetNumParents` | `int Function GetNumParents() native` | 4 |
| function | `GetNthParent` | `EquipSlot Function GetNthParent(int n) native` | 7 |

## Faction

Source: `scripts/modified/Faction.psc` · blob `8f40b052debbac1fa533ae91c9073e2b347147d9`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| property | `kFaction_HiddenFromNPC` | `int property kFaction_HiddenFromNPC = 0x00000001 AutoReadOnly` | 2 |
| property | `kFaction_SpecialCombat` | `int property kFaction_SpecialCombat = 0x00000002 AutoReadOnly` | 3 |
| property | `kFaction_TrackCrime` | `int property kFaction_TrackCrime = 0x00000010 AutoReadOnly` | 4 |
| property | `kFaction_IgnoreMurder` | `int property kFaction_IgnoreMurder = 0x00000020 AutoReadOnly` | 5 |
| property | `kFaction_IgnoreAssault` | `int property kFaction_IgnoreAssault = 0x00000040 AutoReadOnly` | 6 |
| property | `kFaction_IgnoreStealing` | `int property kFaction_IgnoreStealing = 0x00000080 AutoReadOnly` | 7 |
| property | `kFaction_IgnoreTrespass` | `int property kFaction_IgnoreTrespass = 0x00000100 AutoReadOnly` | 8 |
| property | `kFaction_NoReportCrime` | `int property kFaction_NoReportCrime = 0x00000200 AutoReadOnly` | 9 |
| property | `kFaction_CrimeGoldDefaults` | `int property kFaction_CrimeGoldDefaults = 0x00000400 AutoReadOnly` | 10 |
| property | `kFaction_IgnorePickpocket` | `int property kFaction_IgnorePickpocket = 0x00000800 AutoReadOnly` | 11 |
| property | `kFaction_Vendor` | `int property kFaction_Vendor = 0x00001000 AutoReadOnly` | 12 |
| property | `kFaction_CanBeOwner` | `int property kFaction_CanBeOwner = 0x00002000 AutoReadOnly` | 13 |
| property | `kFaction_IgnoreWerewolf` | `int property kFaction_IgnoreWerewolf = 0x00004000 AutoReadOnly` | 14 |
| function | `MakeVendor` | `Function MakeVendor()` | 19 |
| function | `IsVendor` | `bool Function IsVendor()` | 23 |
| function | `ClearVendor` | `Function ClearVendor()` | 27 |
| function | `IsFactionFlagSet` | `bool Function IsFactionFlagSet(int flag) native` | 31 |
| function | `SetFactionFlag` | `Function SetFactionFlag(int flag) native` | 32 |
| function | `ClearFactionFlag` | `Function ClearFactionFlag(int flag) native` | 33 |
| function | `OnlyBuysStolenItems` | `bool Function OnlyBuysStolenItems() native` | 35 |
| function | `SetOnlyBuysStolenItems` | `Function SetOnlyBuysStolenItems(bool onlyStolen) native` | 36 |
| function | `GetVendorStartHour` | `int Function GetVendorStartHour() native` | 38 |
| function | `SetVendorStartHour` | `Function SetVendorStartHour(int hour) native` | 39 |
| function | `GetVendorEndHour` | `int Function GetVendorEndHour() native` | 41 |
| function | `SetVendorEndHour` | `Function SetVendorEndHour(int hour) native` | 42 |
| function | `GetVendorRadius` | `int Function GetVendorRadius() native` | 44 |
| function | `SetVendorRadius` | `Function SetVendorRadius(int radius) native` | 45 |
| function | `GetMerchantContainer` | `ObjectReference Function GetMerchantContainer() native` | 47 |
| function | `SetMerchantContainer` | `Function SetMerchantContainer(ObjectReference akContainer) native` | 48 |
| function | `IsNotSellBuy` | `bool Function IsNotSellBuy() native` | 50 |
| function | `SetNotSellBuy` | `Function SetNotSellBuy(bool notSellBuy) native` | 51 |
| function | `GetBuySellList` | `FormList Function GetBuySellList() native` | 53 |
| function | `SetBuySellList` | `Function SetBuySellList(FormList akList) native` | 54 |

## Flora

Source: `scripts/modified/Flora.psc` · blob `13115d27bf2ee6d4d6d8d7aa71249b67369cd227`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetHarvestSound` | `SoundDescriptor Function GetHarvestSound() native` | 1 |
| function | `SetHarvestSound` | `Function SetHarvestSound(SoundDescriptor akSoundDescriptor) native` | 2 |
| function | `GetIngredient` | `Form Function GetIngredient() native` | 4 |
| function | `SetIngredient` | `Function SetIngredient(Form akIngredient) native` | 5 |

## Form

Source: `scripts/modified/Form.psc` · blob `c8410ae0d52383d03c214e0e07d402211b5cef67`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetType` | `Int Function GetType() native` | 3 |
| function | `GetName` | `string Function GetName() native` | 6 |
| function | `SetName` | `Function SetName(string name) native` | 9 |
| function | `GetWeight` | `float Function GetWeight() native` | 12 |
| function | `SetWeight` | `Function SetWeight(float weight) native` | 15 |
| function | `SetGoldValue` | `Function SetGoldValue(int value) native` | 18 |
| function | `GetNumKeywords` | `int Function GetNumKeywords() native` | 21 |
| function | `GetNthKeyword` | `Keyword Function GetNthKeyword(int index) native` | 24 |
| function | `GetKeywords` | `Keyword[] Function GetKeywords() native` | 27 |
| function | `HasKeywordString` | `bool Function HasKeywordString(string s)` | 29 |
| function | `SetPlayerKnows` | `Function SetPlayerKnows(bool knows) native` | 40 |
| function | `RegisterForKey` | `Function RegisterForKey(int keyCode) native` | 43 |
| function | `UnregisterForKey` | `Function UnregisterForKey(int keyCode) native` | 44 |
| function | `UnregisterForAllKeys` | `Function UnregisterForAllKeys() native` | 45 |
| event | `OnKeyDown` | `Event OnKeyDown(int keyCode)` | 47 |
| event | `OnKeyUp` | `Event OnKeyUp(int keyCode, float holdTime)` | 50 |
| function | `RegisterForControl` | `Function RegisterForControl(string control) native` | 55 |
| function | `UnregisterForControl` | `Function UnregisterForControl(string control) native` | 56 |
| function | `UnregisterForAllControls` | `Function UnregisterForAllControls() native` | 57 |
| event | `OnControlDown` | `Event OnControlDown(string control)` | 59 |
| event | `OnControlUp` | `Event OnControlUp(string control, float holdTime)` | 62 |
| function | `RegisterForMenu` | `Function RegisterForMenu(string menuName) native` | 68 |
| function | `UnregisterForMenu` | `Function UnregisterForMenu(string menuName) native` | 69 |
| function | `UnregisterForAllMenus` | `Function UnregisterForAllMenus() native` | 70 |
| event | `OnMenuOpen` | `Event OnMenuOpen(string menuName)` | 72 |
| event | `OnMenuClose` | `Event OnMenuClose(string menuName)` | 75 |
| function | `RegisterForModEvent` | `Function RegisterForModEvent(string eventName, string callbackName) native` | 88 |
| function | `UnregisterForModEvent` | `Function UnregisterForModEvent(string eventName) native` | 89 |
| function | `UnregisterForAllModEvents` | `Function UnregisterForAllModEvents() native` | 90 |
| function | `SendModEvent` | `Function SendModEvent(string eventName, string strArg = "", float numArg = 0.0) native` | 93 |
| function | `RegisterForCameraState` | `Function RegisterForCameraState() native` | 96 |
| function | `UnregisterForCameraState` | `Function UnregisterForCameraState() native` | 97 |
| event | `OnPlayerCameraState` | `Event OnPlayerCameraState(int oldState, int newState)` | 99 |
| function | `RegisterForCrosshairRef` | `Function RegisterForCrosshairRef() native` | 103 |
| function | `UnregisterForCrosshairRef` | `Function UnregisterForCrosshairRef() native` | 104 |
| event | `OnCrosshairRefChange` | `Event OnCrosshairRefChange(ObjectReference ref)` | 107 |
| function | `RegisterForActorAction` | `Function RegisterForActorAction(int actionType) native` | 110 |
| function | `UnregisterForActorAction` | `Function UnregisterForActorAction(int actionType) native` | 111 |
| event | `OnActorAction` | `Event OnActorAction(int actionType, Actor akActor, Form source, int slot)` | 129 |
| function | `RegisterForNiNodeUpdate` | `Function RegisterForNiNodeUpdate() native` | 133 |
| function | `UnregisterForNiNodeUpdate` | `Function UnregisterForNiNodeUpdate() native` | 134 |
| event | `OnNiNodeUpdate` | `Event OnNiNodeUpdate(ObjectReference akActor)` | 136 |
| function | `TempClone` | `Form Function TempClone() native` | 140 |
| function | `HasWorldModel` | `bool Function HasWorldModel() native` | 143 |
| function | `GetWorldModelPath` | `string Function GetWorldModelPath() native` | 146 |
| function | `SetWorldModelPath` | `Function SetWorldModelPath(string path) native` | 147 |
| function | `GetWorldModelNumTextureSets` | `int Function GetWorldModelNumTextureSets() native` | 150 |
| function | `GetWorldModelNthTextureSet` | `TextureSet Function GetWorldModelNthTextureSet(int n) native` | 153 |
| function | `SetWorldModelNthTextureSet` | `Function SetWorldModelNthTextureSet(TextureSet nSet, int n) native` | 156 |
| function | `IsPlayable` | `bool Function IsPlayable() native` | 159 |

## FormList

Source: `scripts/modified/FormList.psc` · blob `9f5ff654e7ef77d9ebe3aec9c8fc5a34aa72ab95`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `ToArray` | `Form[] Function ToArray() native` | 2 |
| function | `AddForms` | `Function AddForms(Form[] forms) native` | 5 |

