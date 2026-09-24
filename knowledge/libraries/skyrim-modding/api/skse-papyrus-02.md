# SKSE64 Modified Papyrus API — Shard 2

Imported: 2026-09-24
Source: `ianpatt/skse64` master
Scripts: 8 · declarations: 108
Status: generated source-derived API shard

## ArmorAddon extends Form

Source: `scripts/modified/ArmorAddon.psc` · blob `a26e98952381b1720ef49b3b7c9b3c0be5ba9521`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetModelPath` | `string Function GetModelPath(bool firstPerson, bool female) native` | 4 |
| function | `SetModelPath` | `Function SetModelPath(string path, bool firstPerson, bool female) native` | 7 |
| function | `GetModelNumTextureSets` | `int Function GetModelNumTextureSets(bool first, bool female) native` | 10 |
| function | `GetModelNthTextureSet` | `TextureSet Function GetModelNthTextureSet(int n, bool first, bool female) native` | 13 |
| function | `SetModelNthTextureSet` | `Function SetModelNthTextureSet(TextureSet texture, int n, bool first, bool female) native` | 16 |
| function | `GetNumAdditionalRaces` | `int Function GetNumAdditionalRaces() native` | 19 |
| function | `GetNthAdditionalRace` | `Race Function GetNthAdditionalRace(int n) native` | 22 |
| function | `GetSlotMask` | `int Function GetSlotMask() native` | 29 |
| function | `SetSlotMask` | `Function SetSlotMask(int slotMask) native` | 31 |
| function | `AddSlotToMask` | `int Function AddSlotToMask(int slotMask) native` | 33 |
| function | `RemoveSlotFromMask` | `int Function RemoveSlotFromMask(int slotMask) native` | 35 |
| function | `GetMaskForSlot` | `int Function GetMaskForSlot(int slot) global` | 39 |

## Art extends Form

Source: `scripts/modified/Art.psc` · blob `605f52d3cc269d55d4541fcd691f21d1403896a4`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetModelPath` | `string Function GetModelPath() native` | 3 |
| function | `SetModelPath` | `Function SetModelPath(string path) native` | 4 |

## Book

Source: `scripts/modified/Book.psc` · blob `7abf7218b5fa195fde4ec486d8f78dbb955d4177`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetSpell` | `Spell Function GetSpell() native` | 2 |
| function | `GetSkill` | `Int Function GetSkill() native` | 3 |
| function | `IsRead` | `bool Function IsRead() native` | 4 |
| function | `IsTakeable` | `bool Function IsTakeable() native` | 5 |

## Camera

Source: `scripts/modified/Camera.psc` · blob `e624334097b699641ffc6b9baf64730258e310f2`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetCameraState` | `int Function GetCameraState() global native` | 18 |
| function | `UpdateThirdPerson` | `Function UpdateThirdPerson() global native` | 21 |
| function | `GetWorldFieldOfView` | `float Function GetWorldFieldOfView() global native` | 24 |
| function | `GetWorldFOV` | `float Function GetWorldFOV() global` | 25 |
| function | `SetWorldFieldOfView` | `Function SetWorldFieldOfView(float fov) global native` | 30 |
| function | `SetWorldFOV` | `Function SetWorldFOV(float fov) global` | 31 |
| function | `GetFirstPersonFieldOfView` | `float Function GetFirstPersonFieldOfView() global native` | 36 |
| function | `GetFirstPersonFOV` | `float Function GetFirstPersonFOV() global` | 37 |
| function | `SetFirstPersonFieldOfView` | `Function SetFirstPersonFieldOfView(float fov) global native` | 42 |
| function | `SetFirstPersonFOV` | `Function SetFirstPersonFOV(float fov) global` | 43 |

## Cell

Source: `scripts/modified/Cell.psc` · blob `113de4f3aa67797113b4174a9838c5ff1590f1f6`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetNumRefs` | `int Function GetNumRefs(int formTypeFilter = 0) native` | 2 |
| function | `GetNthRef` | `ObjectReference Function GetNthRef(int n, int formTypeFilter = 0) native` | 5 |
| function | `GetWaterLevel` | `float Function GetWaterLevel() native` | 8 |
| function | `GetActualWaterLevel` | `float Function GetActualWaterLevel() native` | 11 |

## ColorComponent

Source: `scripts/modified/ColorComponent.psc` · blob `62a7b9123a7c1ae025afb0da7f35dc6c5b4ab3d1`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetAlpha` | `int Function GetAlpha(int argb) global native` | 3 |
| function | `GetRed` | `int Function GetRed(int argb) global native` | 4 |
| function | `GetGreen` | `int Function GetGreen(int argb) global native` | 5 |
| function | `GetBlue` | `int Function GetBlue(int argb) global native` | 6 |
| function | `GetHue` | `float Function GetHue(int argb) global native` | 8 |
| function | `GetSaturation` | `float Function GetSaturation(int argb) global native` | 9 |
| function | `GetValue` | `float Function GetValue(int argb) global native` | 10 |
| function | `SetAlpha` | `int Function SetAlpha(int argb, int a) global native` | 12 |
| function | `SetRed` | `int Function SetRed(int argb, int r) global native` | 13 |
| function | `SetGreen` | `int Function SetGreen(int argb, int g) global native` | 14 |
| function | `SetBlue` | `int Function SetBlue(int argb, int b) global native` | 15 |
| function | `SetHue` | `int Function SetHue(int argb, float h) global native` | 17 |
| function | `SetSaturation` | `int Function SetSaturation(int argb, float s) global native` | 18 |
| function | `SetValue` | `int Function SetValue(int argb, float v) global native` | 19 |

## ColorForm extends Form

Source: `scripts/modified/ColorForm.psc` · blob `a7a1a9514b8b3d8a99b39e2eb7481180e4596060`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetColor` | `int Function GetColor() native` | 3 |
| function | `SetColor` | `Function SetColor(int color) native` | 4 |
| function | `GetRed` | `int Function GetRed()` | 6 |
| function | `GetGreen` | `int Function GetGreen()` | 10 |
| function | `GetBlue` | `int Function GetBlue()` | 14 |
| function | `GetHue` | `float Function GetHue()` | 18 |
| function | `GetSaturation` | `float Function GetSaturation()` | 22 |
| function | `GetValue` | `float Function GetValue()` | 26 |

## CombatStyle extends Form

Source: `scripts/modified/CombatStyle.psc` · blob `93b1a2b1a28705b2cbc4cbbcba7c2b06027b46bc`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetOffensiveMult` | `float Function GetOffensiveMult() native` | 4 |
| function | `GetDefensiveMult` | `float Function GetDefensiveMult() native` | 5 |
| function | `GetGroupOffensiveMult` | `float Function GetGroupOffensiveMult() native` | 6 |
| function | `GetAvoidThreatChance` | `float Function GetAvoidThreatChance() native` | 7 |
| function | `GetMeleeMult` | `float Function GetMeleeMult() native` | 8 |
| function | `GetRangedMult` | `float Function GetRangedMult() native` | 9 |
| function | `GetMagicMult` | `float Function GetMagicMult() native` | 10 |
| function | `GetShoutMult` | `float Function GetShoutMult() native` | 11 |
| function | `GetStaffMult` | `float Function GetStaffMult() native` | 12 |
| function | `GetUnarmedMult` | `float Function GetUnarmedMult() native` | 13 |
| function | `SetOffensiveMult` | `Function SetOffensiveMult(float mult) native` | 15 |
| function | `SetDefensiveMult` | `Function SetDefensiveMult(float mult) native` | 16 |
| function | `SetGroupOffensiveMult` | `Function SetGroupOffensiveMult(float mult) native` | 17 |
| function | `SetAvoidThreatChance` | `Function SetAvoidThreatChance(float chance) native` | 18 |
| function | `SetMeleeMult` | `Function SetMeleeMult(float mult) native` | 19 |
| function | `SetRangedMult` | `Function SetRangedMult(float mult) native` | 20 |
| function | `SetMagicMult` | `Function SetMagicMult(float mult) native` | 21 |
| function | `SetShoutMult` | `Function SetShoutMult(float mult) native` | 22 |
| function | `SetStaffMult` | `Function SetStaffMult(float mult) native` | 23 |
| function | `SetUnarmedMult` | `Function SetUnarmedMult(float mult) native` | 24 |
| function | `GetMeleeAttackStaggeredMult` | `float Function GetMeleeAttackStaggeredMult() native` | 27 |
| function | `GetMeleePowerAttackStaggeredMult` | `float Function GetMeleePowerAttackStaggeredMult() native` | 28 |
| function | `GetMeleePowerAttackBlockingMult` | `float Function GetMeleePowerAttackBlockingMult() native` | 29 |
| function | `GetMeleeBashMult` | `float Function GetMeleeBashMult() native` | 30 |
| function | `GetMeleeBashRecoiledMult` | `float Function GetMeleeBashRecoiledMult() native` | 31 |
| function | `GetMeleeBashAttackMult` | `float Function GetMeleeBashAttackMult() native` | 32 |
| function | `GetMeleeBashPowerAttackMult` | `float Function GetMeleeBashPowerAttackMult() native` | 33 |
| function | `GetMeleeSpecialAttackMult` | `float Function GetMeleeSpecialAttackMult() native` | 34 |
| function | `GetAllowDualWielding` | `bool Function GetAllowDualWielding() native` | 35 |
| function | `SetMeleeAttackStaggeredMult` | `Function SetMeleeAttackStaggeredMult(float mult) native` | 37 |
| function | `SetMeleePowerAttackStaggeredMult` | `Function SetMeleePowerAttackStaggeredMult(float mult) native` | 38 |
| function | `SetMeleePowerAttackBlockingMult` | `Function SetMeleePowerAttackBlockingMult(float mult) native` | 39 |
| function | `SetMeleeBashMult` | `Function SetMeleeBashMult(float mult) native` | 40 |
| function | `SetMeleeBashRecoiledMult` | `Function SetMeleeBashRecoiledMult(float mult) native` | 41 |
| function | `SetMeleeBashAttackMult` | `Function SetMeleeBashAttackMult(float mult) native` | 42 |
| function | `SetMeleeBashPowerAttackMult` | `Function SetMeleeBashPowerAttackMult(float mult) native` | 43 |
| function | `SetMeleeSpecialAttackMult` | `Function SetMeleeSpecialAttackMult(float mult) native` | 44 |
| function | `SetAllowDualWielding` | `Function SetAllowDualWielding(bool allow) native` | 45 |
| function | `GetCloseRangeDuelingCircleMult` | `float Function GetCloseRangeDuelingCircleMult() native` | 48 |
| function | `GetCloseRangeDuelingFallbackMult` | `float Function GetCloseRangeDuelingFallbackMult() native` | 49 |
| function | `GetCloseRangeFlankingFlankDistance` | `float Function GetCloseRangeFlankingFlankDistance() native` | 50 |
| function | `GetCloseRangeFlankingStalkTime` | `float Function GetCloseRangeFlankingStalkTime() native` | 51 |
| function | `SetCloseRangeDuelingCircleMult` | `Function SetCloseRangeDuelingCircleMult(float mult) native` | 53 |
| function | `SetCloseRangeDuelingFallbackMult` | `Function SetCloseRangeDuelingFallbackMult(float mult) native` | 54 |
| function | `SetCloseRangeFlankingFlankDistance` | `Function SetCloseRangeFlankingFlankDistance(float mult) native` | 55 |
| function | `SetCloseRangeFlankingStalkTime` | `Function SetCloseRangeFlankingStalkTime(float mult) native` | 56 |
| function | `GetLongRangeStrafeMult` | `float Function GetLongRangeStrafeMult() native` | 59 |
| function | `SetLongRangeStrafeMult` | `Function SetLongRangeStrafeMult(float mult) native` | 60 |
| function | `GetFlightHoverChance` | `float Function GetFlightHoverChance() native` | 63 |
| function | `GetFlightDiveBombChance` | `float Function GetFlightDiveBombChance() native` | 64 |
| function | `GetFlightFlyingAttackChance` | `float Function GetFlightFlyingAttackChance() native` | 65 |
| function | `SetFlightHoverChance` | `Function SetFlightHoverChance(float chance) native` | 67 |
| function | `SetFlightDiveBombChance` | `Function SetFlightDiveBombChance(float chance) native` | 68 |
| function | `SetFlightFlyingAttackChance` | `Function SetFlightFlyingAttackChance(float mult) native` | 69 |

