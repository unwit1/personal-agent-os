# SKSE64 Modified Papyrus API — Shard 6

Imported: 2026-09-24
Source: `ianpatt/skse64` master
Scripts: 8 · declarations: 151
Status: generated source-derived API shard

## Outfit

Source: `scripts/modified/Outfit.psc` · blob `7a64041d9f84b6fd3e0a2cf0234f3fce39b32eb7`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetNumParts` | `int Function GetNumParts() native` | 2 |
| function | `GetNthPart` | `Form Function GetNthPart(int n) native` | 3 |

## Perk

Source: `scripts/modified/Perk.psc` · blob `22e724cf5e87a240e419e24b2a113e59cf19bd86`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetNextPerk` | `Perk Function GetNextPerk() native` | 1 |
| function | `GetNumEntries` | `int Function GetNumEntries() native` | 3 |
| function | `GetNthEntryRank` | `int Function GetNthEntryRank(int n) native` | 5 |
| function | `SetNthEntryRank` | `bool Function SetNthEntryRank(int n, int rank) native` | 6 |
| function | `GetNthEntryPriority` | `int Function GetNthEntryPriority(int n) native` | 8 |
| function | `SetNthEntryPriority` | `bool Function SetNthEntryPriority(int n, int priority) native` | 9 |
| function | `GetNthEntryQuest` | `Quest Function GetNthEntryQuest(int n) native` | 11 |
| function | `SetNthEntryQuest` | `bool Function SetNthEntryQuest(int n, Quest newQuest) native` | 12 |
| function | `GetNthEntryStage` | `int Function GetNthEntryStage(int n) native` | 14 |
| function | `SetNthEntryStage` | `bool Function SetNthEntryStage(int n, int stage) native` | 15 |
| function | `GetNthEntrySpell` | `Spell Function GetNthEntrySpell(int n) native` | 17 |
| function | `SetNthEntrySpell` | `bool Function SetNthEntrySpell(int n, Spell newSpell) native` | 18 |
| function | `GetNthEntryLeveledList` | `LeveledItem Function GetNthEntryLeveledList(int n) native` | 20 |
| function | `SetNthEntryLeveledList` | `bool Function SetNthEntryLeveledList(int n, LeveledItem lList) native` | 21 |
| function | `GetNthEntryText` | `string Function GetNthEntryText(int n) native` | 23 |
| function | `SetNthEntryText` | `bool Function SetNthEntryText(int n, string newText) native` | 24 |
| function | `GetNthEntryValue` | `float Function GetNthEntryValue(int n, int i) native` | 26 |
| function | `SetNthEntryValue` | `bool Function SetNthEntryValue(int n, int i, float value) native` | 27 |

## Potion

Source: `scripts/modified/Potion.psc` · blob `d356430eaeb720a4eaecf72c11472adbbcc7538e`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `IsFood` | `bool Function IsFood() native` | 2 |
| function | `IsPoison` | `bool Function IsPoison() native` | 5 |
| function | `GetNumEffects` | `int Function GetNumEffects() native` | 8 |
| function | `GetNthEffectMagnitude` | `float Function GetNthEffectMagnitude(int index) native` | 11 |
| function | `GetNthEffectArea` | `int Function GetNthEffectArea(int index) native` | 14 |
| function | `GetNthEffectDuration` | `int Function GetNthEffectDuration(int index) native` | 17 |
| function | `GetNthEffectMagicEffect` | `MagicEffect Function GetNthEffectMagicEffect(int index) native` | 20 |
| function | `GetCostliestEffectIndex` | `int Function GetCostliestEffectIndex() native` | 23 |
| function | `SetNthEffectMagnitude` | `Function SetNthEffectMagnitude(int index, float value) native` | 26 |
| function | `SetNthEffectArea` | `Function SetNthEffectArea(int index, int value) native` | 29 |
| function | `SetNthEffectDuration` | `Function SetNthEffectDuration(int index, int value) native` | 32 |
| function | `GetUseSound` | `SoundDescriptor Function GetUseSound() native` | 35 |
| function | `GetEffectMagnitudes` | `float[] Function GetEffectMagnitudes() native` | 38 |
| function | `GetEffectAreas` | `int[] Function GetEffectAreas() native` | 41 |
| function | `GetEffectDurations` | `int[] Function GetEffectDurations() native` | 44 |
| function | `GetMagicEffects` | `MagicEffect[] Function GetMagicEffects() native` | 47 |

## Quest

Source: `scripts/modified/Quest.psc` · blob `87d0f24b398389d5ed1bafbd525c28246b69b2ae`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetQuest` | `Quest Function GetQuest(string editorId) global native` | 3 |
| function | `GetID` | `string Function GetID() native` | 6 |
| function | `GetPriority` | `int Function GetPriority() native` | 9 |
| function | `GetNumAliases` | `int Function GetNumAliases() native` | 12 |
| function | `GetNthAlias` | `Alias Function GetNthAlias(int index) native` | 15 |
| function | `GetAliasByName` | `Alias Function GetAliasByName(string name) native` | 18 |
| function | `GetAliasById` | `Alias Function GetAliasById(int aliasId) native` | 21 |
| function | `GetAliases` | `Alias[] Function GetAliases() native` | 24 |

## Race

Source: `scripts/modified/Race.psc` · blob `67c3f38fd8c81bc084c04d9315fa8d1cc12b42c5`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetSpellCount` | `int Function GetSpellCount() native` | 2 |
| function | `GetNthSpell` | `Spell Function GetNthSpell(int n) native` | 5 |
| function | `IsRaceFlagSet` | `bool Function IsRaceFlagSet(int n) native` | 8 |
| function | `SetRaceFlag` | `Function SetRaceFlag(int n) native` | 11 |
| function | `ClearRaceFlag` | `Function ClearRaceFlag(int n) native` | 14 |
| function | `GetDefaultVoiceType` | `VoiceType Function GetDefaultVoiceType(bool female) native` | 17 |
| function | `SetDefaultVoiceType` | `Function SetDefaultVoiceType(bool female, VoiceType voice) native` | 20 |
| function | `GetSkin` | `Armor Function GetSkin() native` | 23 |
| function | `SetSkin` | `Function SetSkin(Armor skin) native` | 24 |
| function | `GetNumPlayableRaces` | `int Function GetNumPlayableRaces() native global` | 27 |
| function | `GetNthPlayableRace` | `Race Function GetNthPlayableRace(int n) native global` | 30 |
| function | `GetRace` | `Race Function GetRace(string editorId) native global` | 33 |
| property | `kRace_Playable` | `int property kRace_Playable = 0x00000001 AutoReadOnly` | 36 |
| property | `kRace_FaceGenHead` | `int property kRace_FaceGenHead = 0x00000002 AutoReadOnly` | 37 |
| property | `kRace_Child` | `int property kRace_Child = 0x00000004 AutoReadOnly` | 38 |
| property | `kRace_TiltFrontBack` | `int property kRace_TiltFrontBack = 0x00000008 AutoReadOnly` | 39 |
| property | `kRace_TiltLeftRight` | `int property kRace_TiltLeftRight = 0x00000010 AutoReadOnly` | 40 |
| property | `kRace_NoShadow` | `int property kRace_NoShadow = 0x00000020 AutoReadOnly` | 41 |
| property | `kRace_Swims` | `int property kRace_Swims = 0x00000040 AutoReadOnly` | 42 |
| property | `kRace_Flies` | `int property kRace_Flies = 0x00000080 AutoReadOnly` | 43 |
| property | `kRace_Walks` | `int property kRace_Walks = 0x00000100 AutoReadOnly` | 44 |
| property | `kRace_Immobile` | `int property kRace_Immobile = 0x00000200 AutoReadOnly` | 45 |
| property | `kRace_NotPushable` | `int property kRace_NotPushable = 0x00000400 AutoReadOnly` | 46 |
| property | `kRace_NoCombatInWater` | `int property kRace_NoCombatInWater = 0x00000800 AutoReadOnly` | 47 |
| property | `kRace_NoRotatingToHeadTrack` | `int property kRace_NoRotatingToHeadTrack = 0x00001000 AutoReadOnly` | 48 |
| property | `kRace_UseHeadTrackAnim` | `int property kRace_UseHeadTrackAnim = 0x00008000 AutoReadOnly` | 49 |
| property | `kRace_SpellsAlignWithMagicNode` | `int property kRace_SpellsAlignWithMagicNode = 0x00010000 AutoReadOnly` | 50 |
| property | `kRace_UseWorldRaycasts` | `int property kRace_UseWorldRaycasts = 0x00020000 AutoReadOnly` | 51 |
| property | `kRace_AllowRagdollCollision` | `int property kRace_AllowRagdollCollision = 0x00040000 AutoReadOnly` | 52 |
| property | `kRace_CantOpenDoors` | `int property kRace_CantOpenDoors = 0x00100000 AutoReadOnly` | 53 |
| property | `kRace_AllowPCDialogue` | `int property kRace_AllowPCDialogue = 0x00200000 AutoReadOnly` | 54 |
| property | `kRace_NoKnockdowns` | `int property kRace_NoKnockdowns = 0x00400000 AutoReadOnly` | 55 |
| property | `kRace_AllowPickpocket` | `int property kRace_AllowPickpocket = 0x00800000 AutoReadOnly` | 56 |
| property | `kRace_AlwaysUseProxyController` | `int property kRace_AlwaysUseProxyController = 0x01000000 AutoReadOnly` | 57 |
| property | `kRace_AllowMultipleMembraneShaders` | `int property kRace_AllowMultipleMembraneShaders = 0x20000000 AutoReadOnly` | 58 |
| property | `kRace_AvoidsRoads` | `int property kRace_AvoidsRoads = 0x80000000 AutoReadOnly` | 59 |
| function | `IsPlayable` | `bool Function IsPlayable()` | 61 |
| function | `MakePlayable` | `Function MakePlayable()` | 65 |
| function | `MakeUnplayable` | `Function MakeUnplayable()` | 69 |
| function | `IsChildRace` | `bool Function IsChildRace()` | 73 |
| function | `MakeChildRace` | `Function MakeChildRace()` | 77 |
| function | `MakeNonChildRace` | `Function MakeNonChildRace()` | 81 |
| function | `CanFly` | `bool Function CanFly()` | 85 |
| function | `MakeCanFly` | `Function MakeCanFly()` | 89 |
| function | `MakeNonFlying` | `Function MakeNonFlying()` | 93 |
| function | `CanSwim` | `bool Function CanSwim()` | 97 |
| function | `MakeCanSwim` | `Function MakeCanSwim()` | 101 |
| function | `MakeNonSwimming` | `Function MakeNonSwimming()` | 105 |
| function | `CanWalk` | `bool Function CanWalk()` | 109 |
| function | `MakeCanWalk` | `Function MakeCanWalk()` | 113 |
| function | `MakeNonWalking` | `Function MakeNonWalking()` | 117 |
| function | `IsImmobile` | `bool Function IsImmobile()` | 121 |
| function | `MakeImmobile` | `Function MakeImmobile()` | 125 |
| function | `MakeMobile` | `Function MakeMobile()` | 129 |
| function | `IsNotPushable` | `bool Function IsNotPushable()` | 133 |
| function | `MakeNotPushable` | `Function MakeNotPushable()` | 137 |
| function | `MakePushable` | `Function MakePushable()` | 141 |
| function | `NoKnockdowns` | `bool Function NoKnockdowns()` | 145 |
| function | `MakeNoKnockdowns` | `Function MakeNoKnockdowns()` | 149 |
| function | `ClearNoKNockdowns` | `Function ClearNoKNockdowns()` | 153 |
| function | `NoCombatInWater` | `bool Function NoCombatInWater()` | 157 |
| function | `SetNoCombatInWater` | `Function SetNoCombatInWater()` | 161 |
| function | `ClearNoCombatInWater` | `Function ClearNoCombatInWater()` | 165 |
| function | `AvoidsRoads` | `bool Function AvoidsRoads()` | 169 |
| function | `SetAvoidsRoads` | `Function SetAvoidsRoads()` | 173 |
| function | `ClearAvoidsRoads` | `Function ClearAvoidsRoads()` | 177 |
| function | `AllowPickpocket` | `bool Function AllowPickpocket()` | 181 |
| function | `SetAllowPickpocket` | `Function SetAllowPickpocket()` | 185 |
| function | `ClearAllowPickpocket` | `Function ClearAllowPickpocket()` | 189 |
| function | `AllowPCDialogue` | `bool Function AllowPCDialogue()` | 193 |
| function | `SetAllowPCDialogue` | `Function SetAllowPCDialogue()` | 197 |
| function | `ClearAllowPCDialogue` | `Function ClearAllowPCDialogue()` | 201 |
| function | `CantOpenDoors` | `bool Function CantOpenDoors()` | 205 |
| function | `SetCantOpenDoors` | `Function SetCantOpenDoors()` | 209 |
| function | `ClearCantOpenDoors` | `Function ClearCantOpenDoors()` | 213 |
| function | `NoShadow` | `bool Function NoShadow()` | 217 |
| function | `SetNoShadow` | `Function SetNoShadow()` | 221 |
| function | `ClearNoShadow` | `Function ClearNoShadow()` | 225 |

## SKSE

Source: `scripts/modified/SKSE.psc` · blob `889a96b80b6ec69acee63c5ba655bc4d2b28486b`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetVersion` | `int Function GetVersion() global native` | 5 |
| function | `GetVersionMinor` | `int Function GetVersionMinor() global native` | 7 |
| function | `GetVersionBeta` | `int Function GetVersionBeta() global native` | 9 |
| function | `GetVersionRelease` | `int Function GetVersionRelease() global native` | 12 |
| function | `GetScriptVersionRelease` | `int Function GetScriptVersionRelease() global` | 15 |
| function | `GetPluginVersion` | `int Function GetPluginVersion(string name) global native` | 20 |

## Scroll

Source: `scripts/modified/Scroll.psc` · blob `cdf1666153af15eaf4825f54f108b2a379e377df`

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
| function | `SetNthEffectMagnitude` | `Function SetNthEffectMagnitude(int index, float value) native` | 26 |
| function | `SetNthEffectArea` | `Function SetNthEffectArea(int index, int value) native` | 29 |
| function | `SetNthEffectDuration` | `Function SetNthEffectDuration(int index, int value) native` | 32 |
| function | `GetEquipType` | `EquipSlot Function GetEquipType() native` | 35 |
| function | `SetEquipType` | `Function SetEquipType(EquipSlot type) native` | 36 |
| function | `GetEffectMagnitudes` | `float[] Function GetEffectMagnitudes() native` | 39 |
| function | `GetEffectAreas` | `int[] Function GetEffectAreas() native` | 42 |
| function | `GetEffectDurations` | `int[] Function GetEffectDurations() native` | 45 |
| function | `GetMagicEffects` | `MagicEffect[] Function GetMagicEffects() native` | 48 |

## Shout

Source: `scripts/modified/Shout.psc` · blob `0a18151324fecfaa399456f9f1403e2db3d7d853`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetNthWordOfPower` | `WordOfPower Function GetNthWordOfPower(int n) native` | 1 |
| function | `GetNthSpell` | `Spell Function GetNthSpell(int n) native` | 2 |
| function | `GetNthRecoveryTime` | `float Function GetNthRecoveryTime(int n) native` | 3 |
| function | `SetNthWordOfPower` | `Function SetNthWordOfPower(int n, WordOfPower aWoop) native` | 5 |
| function | `SetNthSpell` | `Function SetNthSpell(int n, Spell aSpell) native` | 6 |
| function | `SetNthRecoveryTime` | `Function SetNthRecoveryTime(int n, float time) native` | 7 |

