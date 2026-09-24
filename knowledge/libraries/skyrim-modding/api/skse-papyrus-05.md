# SKSE64 Modified Papyrus API — Shard 5

Imported: 2026-09-24
Source: `ianpatt/skse64` master
Scripts: 8 · declarations: 132
Status: generated source-derived API shard

## LeveledItem

Source: `scripts/modified/LeveledItem.psc` · blob `d5238ecdfbc1106bdefba4e3c74bb18eb8668099`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetChanceNone` | `int function GetChanceNone() native` | 1 |
| function | `SetChanceNone` | `Function SetChanceNone(int chance) native` | 2 |
| function | `GetChanceGlobal` | `GlobalVariable Function GetChanceGlobal() native` | 4 |
| function | `SetChanceGlobal` | `Function SetChanceGlobal(GlobalVariable glob) native` | 5 |
| function | `GetNumForms` | `int Function GetNumForms() native` | 7 |
| function | `GetNthForm` | `Form Function GetNthForm(int n) native` | 8 |
| function | `GetNthLevel` | `int Function GetNthLevel(int n) native` | 10 |
| function | `SetNthLevel` | `Function SetNthLevel(int n, int level) native` | 11 |
| function | `GetNthCount` | `int Function GetNthCount(int n) native` | 13 |
| function | `SetNthCount` | `Function SetNthCount(int n, int count) native` | 14 |

## LeveledSpell

Source: `scripts/modified/LeveledSpell.psc` · blob `672b738efc26a95d93b2a6f5440340e9e5057371`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetChanceNone` | `int function GetChanceNone() native` | 1 |
| function | `SetChanceNone` | `Function SetChanceNone(int chance) native` | 2 |
| function | `GetNumForms` | `int Function GetNumForms() native` | 4 |
| function | `GetNthForm` | `Form Function GetNthForm(int n) native` | 5 |
| function | `GetNthLevel` | `int Function GetNthLevel(int n) native` | 7 |
| function | `SetNthLevel` | `Function SetNthLevel(int n, int level) native` | 8 |

## Location

Source: `scripts/modified/Location.psc` · blob `4673ec56c4d97d7b81c0e7562dc20ffc7b6941d7`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetParent` | `Location Function GetParent() native` | 1 |

## MagicEffect

Source: `scripts/modified/MagicEffect.psc` · blob `83e758ef08f1cb34050711a996192eddbbdbf467`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `SetAssociatedSkill` | `Function SetAssociatedSkill(string skill) native` | 1 |
| function | `GetResistance` | `string Function GetResistance() native` | 3 |
| function | `SetResistance` | `Function SetResistance(string skill) native` | 4 |
| function | `IsEffectFlagSet` | `bool Function IsEffectFlagSet(int flag) native` | 24 |
| function | `SetEffectFlag` | `Function SetEffectFlag(int flag) native` | 25 |
| function | `ClearEffectFlag` | `Function ClearEffectFlag(int flag) native` | 26 |
| function | `GetCastTime` | `float Function GetCastTime() native` | 28 |
| function | `SetCastTime` | `Function SetCastTime(float castTime) native` | 29 |
| function | `GetSkillLevel` | `int Function GetSkillLevel() native` | 31 |
| function | `SetSkillLevel` | `Function SetSkillLevel(int level) native` | 32 |
| function | `GetArea` | `int Function GetArea() native` | 34 |
| function | `SetArea` | `Function SetArea(int area) native` | 35 |
| function | `GetSkillUsageMult` | `float Function GetSkillUsageMult() native` | 37 |
| function | `SetSkillUsageMult` | `Function SetSkillUsageMult(float usageMult) native` | 38 |
| function | `GetBaseCost` | `float Function GetBaseCost() native` | 40 |
| function | `SetBaseCost` | `Function SetBaseCost(float cost) native` | 41 |
| function | `GetLight` | `Light Function GetLight() native` | 43 |
| function | `SetLight` | `Function SetLight(Light obj) native` | 44 |
| function | `GetHitShader` | `EffectShader Function GetHitShader() native` | 46 |
| function | `SetHitShader` | `Function SetHitShader(EffectShader obj) native` | 47 |
| function | `GetEnchantShader` | `EffectShader Function GetEnchantShader() native` | 49 |
| function | `SetEnchantShader` | `Function SetEnchantShader(EffectShader obj) native` | 50 |
| function | `GetProjectile` | `Projectile Function GetProjectile() native` | 52 |
| function | `SetProjectile` | `Function SetProjectile(Projectile obj) native` | 53 |
| function | `GetExplosion` | `Explosion Function GetExplosion() native` | 55 |
| function | `SetExplosion` | `Function SetExplosion(Explosion obj) native` | 56 |
| function | `GetCastingArt` | `Art Function GetCastingArt() native` | 58 |
| function | `SetCastingArt` | `Function SetCastingArt(Art obj) native` | 59 |
| function | `GetHitEffectArt` | `Art Function GetHitEffectArt() native` | 61 |
| function | `SetHitEffectArt` | `Function SetHitEffectArt(Art obj) native` | 62 |
| function | `GetEnchantArt` | `Art Function GetEnchantArt() native` | 64 |
| function | `SetEnchantArt` | `Function SetEnchantArt(Art obj) native` | 65 |
| function | `GetImpactDataSet` | `ImpactDataSet Function GetImpactDataSet() native` | 67 |
| function | `SetImpactDataSet` | `Function SetImpactDataSet(ImpactDataSet obj) native` | 68 |
| function | `GetEquipAbility` | `Spell Function GetEquipAbility() native` | 70 |
| function | `SetEquipAbility` | `Function SetEquipAbility(Spell obj) native` | 71 |
| function | `GetImageSpaceMod` | `ImageSpaceModifier Function GetImageSpaceMod() native` | 73 |
| function | `SetImageSpaceMod` | `Function SetImageSpaceMod(ImageSpaceModifier obj) native` | 74 |
| function | `GetPerk` | `Perk Function GetPerk() native` | 76 |
| function | `SetPerk` | `Function SetPerk(Perk obj) native` | 77 |
| function | `GetCastingType` | `int Function GetCastingType() native` | 79 |
| function | `GetDeliveryType` | `int Function GetDeliveryType() native` | 84 |
| function | `GetSounds` | `Sound[] Function GetSounds() native` | 93 |

## Math

Source: `scripts/modified/Math.psc` · blob `5b8d3fa51f9345935b4c5743c23e2f794a8ab3d8`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `LeftShift` | `int Function LeftShift(int value, int shiftBy) global native` | 1 |
| function | `RightShift` | `int Function RightShift(int value, int shiftBy) global native` | 2 |
| function | `LogicalAnd` | `int Function LogicalAnd(int arg1, int arg2) global native` | 3 |
| function | `LogicalOr` | `int Function LogicalOr(int arg1, int arg2) global native` | 4 |
| function | `LogicalXor` | `int Function LogicalXor(int arg1, int arg2) global native` | 5 |
| function | `LogicalNot` | `int Function LogicalNot(int arg1) global native` | 6 |
| function | `Log` | `float Function Log(float arg1) global native` | 7 |

## ModEvent

Source: `scripts/modified/ModEvent.psc` · blob `ea2cbff814d70a44d8a258614afafc567f531da6`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `Create` | `int Function Create(string eventName) global native` | 32 |
| function | `Send` | `bool Function Send(int handle) global native` | 36 |
| function | `Release` | `Function Release(int handle) global native` | 39 |
| function | `PushBool` | `Function PushBool(int handle, bool value) global native` | 47 |
| function | `PushInt` | `Function PushInt(int handle, int value) global native` | 48 |
| function | `PushFloat` | `Function PushFloat(int handle, float value) global native` | 49 |
| function | `PushString` | `Function PushString(int handle, string value) global native` | 50 |
| function | `PushForm` | `Function PushForm(int handle, Form value) global native` | 51 |

## NetImmerse

Source: `scripts/modified/NetImmerse.psc` · blob `066111beac8a8fe882bbf732b82c8345f1db74dd`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `HasNode` | `bool Function HasNode(ObjectReference ref, string node, bool firstPerson) native global` | 7 |
| function | `GetNodeWorldPositionX` | `float Function GetNodeWorldPositionX(ObjectReference ref, string node, bool firstPerson) native global` | 10 |
| function | `GetNodeWorldPositionY` | `float Function GetNodeWorldPositionY(ObjectReference ref, string node, bool firstPerson) native global` | 11 |
| function | `GetNodeWorldPositionZ` | `float Function GetNodeWorldPositionZ(ObjectReference ref, string node, bool firstPerson) native global` | 12 |
| function | `GetRelativeNodePositionX` | `float Function GetRelativeNodePositionX(ObjectReference ref, string nodeA, string nodeB, bool firstPerson) native global` | 15 |
| function | `GetRelativeNodePositionY` | `float Function GetRelativeNodePositionY(ObjectReference ref, string nodeA, string nodeB, bool firstPerson) native global` | 16 |
| function | `GetRelativeNodePositionZ` | `float Function GetRelativeNodePositionZ(ObjectReference ref, string nodeA, string nodeB, bool firstPerson) native global` | 17 |
| function | `GetNodeLocalPositionX` | `float Function GetNodeLocalPositionX(ObjectReference ref, string node, bool firstPerson) native global` | 19 |
| function | `GetNodeLocalPositionY` | `float Function GetNodeLocalPositionY(ObjectReference ref, string node, bool firstPerson) native global` | 20 |
| function | `GetNodeLocalPositionZ` | `float Function GetNodeLocalPositionZ(ObjectReference ref, string node, bool firstPerson) native global` | 21 |
| function | `SetNodeLocalPositionX` | `Function SetNodeLocalPositionX(ObjectReference ref, string node, float x, bool firstPerson) native global` | 23 |
| function | `SetNodeLocalPositionY` | `Function SetNodeLocalPositionY(ObjectReference ref, string node, float y, bool firstPerson) native global` | 24 |
| function | `SetNodeLocalPositionZ` | `Function SetNodeLocalPositionZ(ObjectReference ref, string node, float z, bool firstPerson) native global` | 25 |
| function | `GetNodeScale` | `float Function GetNodeScale(ObjectReference ref, string node, bool firstPerson) native global` | 28 |
| function | `SetNodeScale` | `Function SetNodeScale(ObjectReference ref, string node, float scale, bool firstPerson) native global` | 29 |
| function | `SetNodeTextureSet` | `Function SetNodeTextureSet(ObjectReference ref, string node, TextureSet tSet, bool firstPerson) native global` | 32 |
| function | `GetNodeWorldPosition` | `bool Function GetNodeWorldPosition(ObjectReference ref, string node, float[] in, bool firstPerson) native global` | 38 |
| function | `GetRelativeNodePosition` | `bool Function GetRelativeNodePosition(ObjectReference ref, string nodeA, string nodeB, float[] in, bool firstPerson) native global` | 41 |
| function | `GetNodeLocalPosition` | `bool Function GetNodeLocalPosition(ObjectReference ref, string node, float[] in, bool firstPerson) native global` | 44 |
| function | `SetNodeLocalPosition` | `bool Function SetNodeLocalPosition(ObjectReference ref, string node, float[] in, bool firstPerson) native global` | 47 |
| function | `GetNodeWorldRotationEuler` | `bool Function GetNodeWorldRotationEuler(ObjectReference ref, string node, float[] in, bool firstPerson) native global` | 51 |
| function | `GetNodeLocalRotationEuler` | `bool Function GetNodeLocalRotationEuler(ObjectReference ref, string node, float[] in, bool firstPerson) native global` | 54 |
| function | `SetNodeLocalRotationEuler` | `bool Function SetNodeLocalRotationEuler(ObjectReference ref, string node, float[] in, bool firstPerson) native global` | 57 |
| function | `GetNodeWorldRotationMatrix` | `bool Function GetNodeWorldRotationMatrix(ObjectReference ref, string node, float[] in, bool firstPerson) native global` | 61 |
| function | `GetNodeLocalRotationMatrix` | `bool Function GetNodeLocalRotationMatrix(ObjectReference ref, string node, float[] in, bool firstPerson) native global` | 64 |
| function | `SetNodeLocalRotationMatrix` | `bool Function SetNodeLocalRotationMatrix(ObjectReference ref, string node, float[] in, bool firstPerson) native global` | 67 |
| function | `SetNodePositionX` | `Function SetNodePositionX(ObjectReference ref, string node, float x, bool firstPerson) global` | 71 |
| function | `SetNodePositionY` | `Function SetNodePositionY(ObjectReference ref, string node, float y, bool firstPerson) global` | 74 |
| function | `SetNodePositionZ` | `Function SetNodePositionZ(ObjectReference ref, string node, float z, bool firstPerson) global` | 77 |
| function | `GetNodePositionX` | `float Function GetNodePositionX(ObjectReference ref, string node, bool firstPerson) global` | 81 |
| function | `GetNodePositionY` | `float Function GetNodePositionY(ObjectReference ref, string node, bool firstPerson) global` | 84 |
| function | `GetNodePositionZ` | `float Function GetNodePositionZ(ObjectReference ref, string node, bool firstPerson) global` | 87 |

## ObjectReference

Source: `scripts/modified/ObjectReference.psc` · blob `923ec3de4692cf2446bf5aa5f703b3cb594a5774`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetNumItems` | `int Function GetNumItems() native` | 3 |
| function | `GetNthForm` | `Form Function GetNthForm(int index) native` | 4 |
| function | `GetTotalItemWeight` | `float Function GetTotalItemWeight() native` | 5 |
| function | `GetTotalArmorWeight` | `float Function GetTotalArmorWeight() native` | 6 |
| function | `IsHarvested` | `bool Function IsHarvested() native` | 9 |
| function | `SetHarvested` | `Function SetHarvested(bool harvested) native` | 10 |
| function | `SetItemHealthPercent` | `Function SetItemHealthPercent(float health) native` | 13 |
| function | `SetItemMaxCharge` | `Function SetItemMaxCharge(float maxCharge) native` | 18 |
| function | `GetItemMaxCharge` | `float Function GetItemMaxCharge() native` | 20 |
| function | `GetItemCharge` | `float Function GetItemCharge() native` | 22 |
| function | `SetItemCharge` | `Function SetItemCharge(float charge) native` | 23 |
| function | `ResetInventory` | `Function ResetInventory() native` | 25 |
| function | `IsOffLimits` | `bool Function IsOffLimits() native` | 27 |
| function | `GetDisplayName` | `string Function GetDisplayName() native` | 31 |
| function | `SetDisplayName` | `bool Function SetDisplayName(string name, bool force = false) native` | 37 |
| function | `GetEnableParent` | `ObjectReference Function GetEnableParent() native` | 40 |
| function | `GetEnchantment` | `Enchantment Function GetEnchantment() native` | 43 |
| function | `SetEnchantment` | `Function SetEnchantment(Enchantment source, float maxCharge) native` | 48 |
| function | `CreateEnchantment` | `Function CreateEnchantment(float maxCharge, MagicEffect[] effects, float[] magnitudes, int[] areas, int[] durations) native` | 54 |
| function | `GetNumReferenceAliases` | `int Function GetNumReferenceAliases() native` | 57 |
| function | `GetNthReferenceAlias` | `ReferenceAlias Function GetNthReferenceAlias(int n) native` | 60 |
| function | `GetPoison` | `Potion Function GetPoison() native` | 63 |
| function | `GetAllForms` | `Function GetAllForms(FormList toFill) native` | 66 |
| function | `GetContainerForms` | `Form[] Function GetContainerForms() native` | 69 |
| function | `GetReferenceAliases` | `ReferenceAlias[] Function GetReferenceAliases() native` | 72 |

