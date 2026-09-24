# SKSE64 Modified Papyrus API — Shard 8

Imported: 2026-09-24
Source: `ianpatt/skse64` master
Scripts: 6 · declarations: 122
Status: generated source-derived API shard

## UI

Source: `scripts/modified/UI.psc` · blob `2a8f18921c3ba382ea326ae677c686e75f8db99d`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `IsMenuOpen` | `bool Function IsMenuOpen(string menuName) global native` | 47 |
| function | `SetBool` | `Function SetBool(string menuName, string target, bool value) global native` | 57 |
| function | `SetInt` | `Function SetInt(string menuName, string target, int value) global native` | 58 |
| function | `SetFloat` | `Function SetFloat(string menuName, string target, float value) global native` | 59 |
| function | `SetString` | `Function SetString(string menuName, string target, string value) global native` | 60 |
| function | `SetNumber` | `Function SetNumber(string menuName, string target, float value) global` | 61 |
| function | `GetBool` | `bool Function GetBool(string menuName, string target) global native` | 71 |
| function | `GetInt` | `int Function GetInt(string menuName, string target) global native` | 72 |
| function | `GetFloat` | `float Function GetFloat(string menuName, string target) global native` | 73 |
| function | `GetString` | `string Function GetString(string menuName, string target) global native` | 74 |
| function | `GetNumber` | `float Function GetNumber(string menuName, string target) global` | 75 |
| function | `Invoke` | `Function Invoke(string menuName, string target) global` | 86 |
| function | `InvokeBool` | `Function InvokeBool(string menuName, string target, bool arg) global native` | 90 |
| function | `InvokeInt` | `Function InvokeInt(string menuName, string target, int arg) global native` | 91 |
| function | `InvokeFloat` | `Function InvokeFloat(string menuName, string target, float arg) global native` | 92 |
| function | `InvokeString` | `Function InvokeString(string menuName, string target, string arg) global native` | 93 |
| function | `InvokeNumber` | `Function InvokeNumber(string menuName, string target, float arg) global` | 94 |
| function | `InvokeBoolA` | `Function InvokeBoolA(string menuName, string target, bool[] args) global native` | 98 |
| function | `InvokeIntA` | `Function InvokeIntA(string menuName, string target, int[] args) global native` | 99 |
| function | `InvokeFloatA` | `Function InvokeFloatA(string menuName, string target, float[] args) global native` | 100 |
| function | `InvokeStringA` | `Function InvokeStringA(string menuName, string target, string[] args) global native` | 101 |
| function | `InvokeNumberA` | `Function InvokeNumberA(string menuName, string target, float[] args) global` | 102 |
| function | `InvokeForm` | `Function InvokeForm(string menuName, string target, Form arg) global native` | 107 |
| function | `IsTextInputEnabled` | `bool Function IsTextInputEnabled() global native` | 111 |
| function | `OpenCustomMenu` | `Function OpenCustomMenu(string swfPath, int flags = 0) global native` | 116 |
| function | `CloseCustomMenu` | `Function CloseCustomMenu() global native` | 119 |

## UICallback

Source: `scripts/modified/UICallback.psc` · blob `9bef9f80944bbe41c6cdee83253830c59b851038`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `Create` | `int Function Create(string menuName, string target) global native` | 27 |
| function | `Send` | `bool Function Send(int handle) global native` | 31 |
| function | `Release` | `Function Release(int handle) global native` | 34 |
| function | `PushBool` | `Function PushBool(int handle, bool value) global native` | 37 |
| function | `PushInt` | `Function PushInt(int handle, int value) global native` | 38 |
| function | `PushFloat` | `Function PushFloat(int handle, float value) global native` | 39 |
| function | `PushString` | `Function PushString(int handle, string value) global native` | 40 |
| function | `PushBoolA` | `Function PushBoolA(int handle, bool[] args) global native` | 43 |
| function | `PushIntA` | `Function PushIntA(int handle, int[] args) global native` | 44 |
| function | `PushFloatA` | `Function PushFloatA(int handle, float[] args) global native` | 45 |
| function | `PushStringA` | `Function PushStringA(int handle, string[] args) global native` | 46 |

## Utility

Source: `scripts/modified/Utility.psc` · blob `c8d5405fa2738cacfce57086f22f9a43dcab8a34`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetINIFloat` | `float Function GetINIFloat(string ini) global native` | 2 |
| function | `GetINIInt` | `int Function GetINIInt(string ini) global native` | 3 |
| function | `GetINIBool` | `bool Function GetINIBool(string ini) global native` | 4 |
| function | `GetINIString` | `string Function GetINIString(string ini) global native` | 5 |
| function | `CreateFloatArray` | `float[] Function CreateFloatArray(int size, float fill = 0.0) global native` | 10 |
| function | `CreateIntArray` | `int[] Function CreateIntArray(int size, int fill = 0) global native` | 11 |
| function | `CreateBoolArray` | `bool[] Function CreateBoolArray(int size, bool fill = false) global native` | 12 |
| function | `CreateStringArray` | `string[] Function CreateStringArray(int size, string fill = "") global native` | 13 |
| function | `CreateFormArray` | `Form[] Function CreateFormArray(int size, Form fill = None) global native` | 14 |
| function | `CreateAliasArray` | `Alias[] Function CreateAliasArray(int size, Alias fill = None) global native` | 15 |
| function | `ResizeFloatArray` | `float[] Function ResizeFloatArray(float[] source, int size, float fill = 0.0) global native` | 17 |
| function | `ResizeIntArray` | `int[] Function ResizeIntArray(int[] source, int size, int fill = 0) global native` | 18 |
| function | `ResizeBoolArray` | `bool[] Function ResizeBoolArray(bool[] source, int size, bool fill = false) global native` | 19 |
| function | `ResizeStringArray` | `string[] Function ResizeStringArray(string[] source, int size, string fill = "") global native` | 20 |
| function | `ResizeFormArray` | `Form[] Function ResizeFormArray(Form[] source, int size, Form fill = None) global native` | 21 |
| function | `ResizeAliasArray` | `Alias[] Function ResizeAliasArray(Alias[] source, int size, Alias fill = None) global native` | 22 |

## Weapon

Source: `scripts/modified/Weapon.psc` · blob `865e1177bf80a476841b47d1d25268c31d8073a7`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetBaseDamage` | `int Function GetBaseDamage() native` | 2 |
| function | `SetBaseDamage` | `Function SetBaseDamage(int damage) native` | 3 |
| function | `GetCritDamage` | `int Function GetCritDamage() native` | 5 |
| function | `SetCritDamage` | `Function SetCritDamage(int damage) native` | 6 |
| function | `GetReach` | `float Function GetReach() native` | 8 |
| function | `SetReach` | `Function SetReach(float reach) native` | 9 |
| function | `GetMinRange` | `float Function GetMinRange() native` | 11 |
| function | `SetMinRange` | `Function SetMinRange(float minRange) native` | 12 |
| function | `GetMaxRange` | `float Function GetMaxRange() native` | 14 |
| function | `SetMaxRange` | `Function SetMaxRange(float maxRange) native` | 15 |
| function | `GetSpeed` | `float Function GetSpeed() native` | 17 |
| function | `SetSpeed` | `Function SetSpeed(float speed) native` | 18 |
| function | `GetStagger` | `float Function GetStagger() native` | 20 |
| function | `SetStagger` | `Function SetStagger(float stagger) native` | 21 |
| function | `GetWeaponType` | `int Function GetWeaponType() native` | 23 |
| function | `SetWeaponType` | `Function SetWeaponType(int type) native` | 24 |
| function | `GetModelPath` | `string Function GetModelPath() native` | 27 |
| function | `SetModelPath` | `Function SetModelPath(string path) native` | 28 |
| function | `GetIconPath` | `string Function GetIconPath() native` | 31 |
| function | `SetIconPath` | `Function SetIconPath(string path) native` | 32 |
| function | `GetMessageIconPath` | `string Function GetMessageIconPath() native` | 35 |
| function | `SetMessageIconPath` | `Function SetMessageIconPath(string path) native` | 36 |
| function | `GetEnchantment` | `Enchantment Function GetEnchantment() native` | 39 |
| function | `SetEnchantment` | `Function SetEnchantment(Enchantment e) native` | 40 |
| function | `GetEnchantmentValue` | `int Function GetEnchantmentValue() native` | 43 |
| function | `SetEnchantmentValue` | `Function SetEnchantmentValue(int value) native` | 44 |
| function | `GetEquippedModel` | `Static Function GetEquippedModel() native` | 47 |
| function | `SetEquippedModel` | `Function SetEquippedModel(Static model) native` | 48 |
| function | `GetEquipType` | `EquipSlot Function GetEquipType() native` | 51 |
| function | `SetEquipType` | `Function SetEquipType(EquipSlot type) native` | 52 |
| function | `GetSkill` | `string Function GetSkill() native` | 54 |
| function | `SetSkill` | `Function SetSkill(string skill) native` | 55 |
| function | `GetResist` | `string Function GetResist() native` | 63 |
| function | `SetResist` | `Function SetResist(string resist) native` | 64 |
| function | `GetCritEffect` | `Spell Function GetCritEffect() native` | 67 |
| function | `SetCritEffect` | `Function SetCritEffect(Spell ce) native` | 68 |
| function | `GetCritEffectOnDeath` | `bool Function GetCritEffectOnDeath() native` | 71 |
| function | `SetCritEffectOnDeath` | `Function SetCritEffectOnDeath(bool ceod) native` | 72 |
| function | `GetCritMultiplier` | `float Function GetCritMultiplier() native` | 75 |
| function | `SetCritMultiplier` | `Function SetCritMultiplier(float crit) native` | 76 |
| function | `GetTemplate` | `Weapon Function GetTemplate() native` | 79 |
| function | `IsBattleaxe` | `bool Function IsBattleaxe()` | 81 |
| function | `IsBow` | `bool Function IsBow()` | 85 |
| function | `IsDagger` | `bool Function IsDagger()` | 89 |
| function | `IsGreatsword` | `bool Function IsGreatsword()` | 93 |
| function | `IsMace` | `bool Function IsMace()` | 97 |
| function | `IsStaff` | `bool Function IsStaff()` | 101 |
| function | `IsSword` | `bool Function IsSword()` | 105 |
| function | `IsWarhammer` | `bool Function IsWarhammer()` | 109 |
| function | `IsWarAxe` | `bool Function IsWarAxe()` | 113 |

## Weather

Source: `scripts/modified/Weather.psc` · blob `d5097ef361bec855cc3e4a9a7b5e4e6233c867b3`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetSunGlare` | `float Function GetSunGlare() native` | 3 |
| function | `GetSunDamage` | `float Function GetSunDamage() native` | 6 |
| function | `GetWindDirection` | `float Function GetWindDirection() native` | 9 |
| function | `GetWindDirectionRange` | `float Function GetWindDirectionRange() native` | 12 |
| function | `GetFogDistance` | `float Function GetFogDistance(bool day, int type) native` | 18 |

## WornObject

Source: `scripts/modified/WornObject.psc` · blob `94f844cc13d780a837aa984b9b240441cbed5562`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetItemHealthPercent` | `float Function GetItemHealthPercent(Actor akActor, int handSlot, int slotMask) global native` | 13 |
| function | `SetItemHealthPercent` | `Function SetItemHealthPercent(Actor akActor, int handSlot, int slotMask, float health) global native` | 14 |
| function | `SetItemMaxCharge` | `Function SetItemMaxCharge(Actor akActor, int handSlot, int slotMask, float maxCharge) global native` | 18 |
| function | `GetItemMaxCharge` | `float Function GetItemMaxCharge(Actor akActor, int handSlot, int slotMask) global native` | 21 |
| function | `GetItemCharge` | `float Function GetItemCharge(Actor akActor, int handSlot, int slotMask) global native` | 23 |
| function | `GetDisplayName` | `string Function GetDisplayName(Actor akActor, int handSlot, int slotMask) global native` | 30 |
| function | `SetDisplayName` | `bool Function SetDisplayName(Actor akActor, int handSlot, int slotMask, string name, bool force = false) global native` | 36 |
| function | `GetEnchantment` | `Enchantment Function GetEnchantment(Actor akActor, int handSlot, int slotMask) global native` | 39 |
| function | `SetEnchantment` | `Function SetEnchantment(Actor akActor, int handSlot, int slotMask, Enchantment source, float maxCharge) global native` | 44 |
| function | `CreateEnchantment` | `Function CreateEnchantment(Actor akActor, int handSlot, int slotMask, float maxCharge, MagicEffect[] effects, float[] magnitudes, int[] areas, int[] durations) global native` | 50 |
| function | `GetNumReferenceAliases` | `int Function GetNumReferenceAliases(Actor akActor, int handSlot, int slotMask) global native` | 53 |
| function | `GetNthReferenceAlias` | `ReferenceAlias Function GetNthReferenceAlias(Actor akActor, int handSlot, int slotMask, int n) global native` | 56 |
| function | `GetPoison` | `Potion Function GetPoison(Actor akActor, int handSlot, int slotMask) global native` | 59 |
| function | `GetReferenceAliases` | `ReferenceAlias[] Function GetReferenceAliases(Actor akActor, int handSlot, int slotMask) global native` | 62 |

