# SKSE64 Modified Papyrus API — Shard 7

Imported: 2026-09-24
Source: `ianpatt/skse64` master
Scripts: 8 · declarations: 52
Status: generated source-derived API shard

## SoulGem

Source: `scripts/modified/SoulGem.psc` · blob `d3810107b72e30f93344760a8738efb7e7848b52`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetSoulSize` | `int Function GetSoulSize() native` | 2 |
| function | `GetGemSize` | `int Function GetGemSize() native` | 3 |

## Sound

Source: `scripts/modified/Sound.psc` · blob `04a57f5cd08c4ae14159e277e42373740811a978`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetDescriptor` | `SoundDescriptor Function GetDescriptor() native` | 1 |

## SoundDescriptor extends Form

Source: `scripts/modified/SoundDescriptor.psc` · blob `b578ac6bac002b5424976857ff74152ff9142b65`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetDecibelAttenuation` | `float Function GetDecibelAttenuation() native` | 3 |
| function | `SetDecibelAttenuation` | `Function SetDecibelAttenuation(float dbAttenuation) native` | 4 |
| function | `GetDecibelVariance` | `int Function GetDecibelVariance() native` | 6 |
| function | `SetDecibelVariance` | `Function SetDecibelVariance(int dbVariance) native` | 7 |
| function | `GetFrequencyVariance` | `int Function GetFrequencyVariance() native` | 9 |
| function | `SetFrequencyVariance` | `Function SetFrequencyVariance(int frequencyVariance) native` | 10 |
| function | `GetFrequencyShift` | `int Function GetFrequencyShift() native` | 12 |
| function | `SetFrequencyShift` | `Function SetFrequencyShift(int frequencyShift) native` | 13 |

## SpawnerTask

Source: `scripts/modified/SpawnerTask.psc` · blob `a64da2389da2dd510c9a33577e62d939298751e8`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `Create` | `int Function Create() global native` | 40 |
| function | `AddSpawn` | `Function AddSpawn(int handle, Form formToPlace, ObjectReference target, float[] positionOffset, float[] rotation, int count = 1, bool bForcePersist = false, bool bInitiallyDisabled = false) global native` | 47 |
| function | `Run` | `ObjectReference[] Function Run(int handle) global native` | 53 |
| function | `Cancel` | `Function Cancel(int handle) global native` | 58 |

## Spell

Source: `scripts/modified/Spell.psc` · blob `bf3b42adad405e2b60a766d09477f4aa3a2564d7`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetCastTime` | `float Function GetCastTime() native` | 2 |
| function | `GetPerk` | `Perk Function GetPerk() native` | 5 |
| function | `GetNumEffects` | `int Function GetNumEffects() native` | 8 |
| function | `GetNthEffectMagnitude` | `float Function GetNthEffectMagnitude(int index) native` | 11 |
| function | `GetNthEffectArea` | `int Function GetNthEffectArea(int index) native` | 14 |
| function | `GetNthEffectDuration` | `int Function GetNthEffectDuration(int index) native` | 17 |
| function | `GetNthEffectMagicEffect` | `MagicEffect Function GetNthEffectMagicEffect(int index) native` | 20 |
| function | `GetCostliestEffectIndex` | `int Function GetCostliestEffectIndex() native` | 23 |
| function | `GetMagickaCost` | `int Function GetMagickaCost() native` | 26 |
| function | `GetEffectiveMagickaCost` | `int Function GetEffectiveMagickaCost(Actor caster) native` | 29 |
| function | `SetNthEffectMagnitude` | `Function SetNthEffectMagnitude(int index, float value) native` | 32 |
| function | `SetNthEffectArea` | `Function SetNthEffectArea(int index, int value) native` | 35 |
| function | `SetNthEffectDuration` | `Function SetNthEffectDuration(int index, int value) native` | 38 |
| function | `GetEquipType` | `EquipSlot Function GetEquipType() native` | 41 |
| function | `SetEquipType` | `Function SetEquipType(EquipSlot type) native` | 42 |
| function | `GetEffectMagnitudes` | `float[] Function GetEffectMagnitudes() native` | 45 |
| function | `GetEffectAreas` | `int[] Function GetEffectAreas() native` | 48 |
| function | `GetEffectDurations` | `int[] Function GetEffectDurations() native` | 51 |
| function | `GetMagicEffects` | `MagicEffect[] Function GetMagicEffects() native` | 54 |

## StringUtil

Source: `scripts/modified/StringUtil.psc` · blob `d263a92e44874a7cf1e08fb7926f41463b27524e`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetLength` | `int Function GetLength(string s) global native` | 16 |
| function | `GetNthChar` | `string Function GetNthChar(string s, int index) global native` | 19 |
| function | `IsLetter` | `bool Function IsLetter(string c) global native` | 25 |
| function | `IsDigit` | `bool Function IsDigit(string c) global native` | 26 |
| function | `IsPunctuation` | `bool Function IsPunctuation(string c) global native` | 27 |
| function | `IsPrintable` | `bool Function IsPrintable(string c) global native` | 28 |
| function | `Find` | `int Function Find(string s, string toFind, int startIndex = 0) global native` | 32 |
| function | `Substring` | `string Function Substring(string s, int startIndex, int len = 0) global native` | 36 |
| function | `AsOrd` | `int Function AsOrd(string c) global native` | 39 |
| function | `AsChar` | `string Function AsChar(int c) global native` | 42 |
| function | `Split` | `string[] Function Split(string s, string delim) global native` | 45 |

## TextureSet

Source: `scripts/modified/TextureSet.psc` · blob `cbdf12adb14ef61b1d2a175ff29d427ae66b8cc0`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetNumTexturePaths` | `int Function GetNumTexturePaths() native` | 3 |
| function | `GetNthTexturePath` | `string Function GetNthTexturePath(int n) native` | 6 |
| function | `SetNthTexturePath` | `Function SetNthTexturePath(int n, string texturePath) native` | 9 |

## TreeObject extends Form

Source: `scripts/modified/TreeObject.psc` · blob `09989195b76f704238eed7c0e1b6708305989895`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetHarvestSound` | `SoundDescriptor Function GetHarvestSound() native` | 3 |
| function | `SetHarvestSound` | `Function SetHarvestSound(SoundDescriptor akSoundDescriptor) native` | 4 |
| function | `GetIngredient` | `Form Function GetIngredient() native` | 6 |
| function | `SetIngredient` | `Function SetIngredient(Form akIngredient) native` | 7 |

