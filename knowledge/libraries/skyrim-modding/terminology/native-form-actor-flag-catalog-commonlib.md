# Skyrim Native Form and Actor Flag Catalog — CommonLibSSE-NG

Imported: 2026-09-24
Status: reverse-engineered source-derived flag catalog

## Sources

- `TESForm.h` blob `6ea87f98951bed95c2fe9e8d9a79591fcd5562d0`
- `Actor.h` blob `83dae032ca85bd3bfe1cd53ac00e4e98c1de8e65`

Upstream: https://github.com/alandtse/CommonLibSSE-NG

## TESForm RecordFlags

| Name | Bit expression | Source line |
|---|---|---:|
| `kDestructible` | `1 << 0` | 56 |
| `kMaster` | `1 << 0` | 57 |
| `kUnlocked` | `1 << 0` | 58 |
| `kAltered` | `1 << 1` | 60 |
| `kNonPlayable` | `1 << 2` | 61 |
| `kInitialized` | `1 << 3` | 62 |
| `kNonOccluder` | `1 << 4` | 63 |
| `kDeleted` | `1 << 5` | 64 |
| `kBorderRegion` | `1 << 6` | 66 |
| `kGlobalConstant` | `1 << 6` | 67 |
| `kHasSpokenFlag` | `1 << 6` | 68 |
| `kKnown` | `1 << 6` | 69 |
| `kInPlaceableWater` | `1 << 6` | 70 |
| `kFireOff` | `1 << 7` | 72 |
| `kMustUpdate` | `1 << 8` | 73 |
| `kOnLocalMap` | `1 << 9` | 74 |
| `kPersistent` | `1 << 10` | 75 |
| `kDisabled` | `1 << 11` | 77 |
| `kUsedAsMovingPlatform` | `1 << 11` | 78 |
| `kIgnored` | `1 << 12` | 80 |
| `kEmpty` | `1 << 13` | 82 |
| `kResetDestruction` | `1 << 13` | 83 |
| `kTemporary` | `1 << 14` | 85 |
| `kVisibleWhenDistant` | `1 << 15` | 86 |
| `kRandomAnim` | `1 << 16` | 87 |
| `kDangerous` | `1 << 17` | 88 |
| `kHasCurrents` | `1 << 19` | 89 |
| `kIgnoreFriendlyHits` | `1 << 20` | 90 |
| `kStillLoading` | `1 << 21` | 91 |
| `kFormRetainsID` | `1 << 22` | 92 |
| `kDestroyed` | `1 << 23` | 93 |
| `kUnk24` | `1 << 24` | 95 |
| `kNoAIAcquire` | `1 << 25` | 97 |
| `kObstacle` | `1 << 25` | 98 |
| `kVATSTargetOverride` | `1 << 26` | 100 |
| `kDisableFade` | `1 << 27` | 101 |
| `kReflectedByAutoWater` | `1 << 28` | 103 |
| `kShowOnWorldMap` | `1 << 28` | 104 |
| `kChildCanUse` | `1 << 29` | 106 |

### Record-flag overloading

Several bit values deliberately have **multiple semantic names** because the same bit means different things for different record classes. Examples from current CommonLib:

- bit 0: `Destructible`, `Master`, or `Unlocked`;
- bit 6: `BorderRegion`, `GlobalConstant`, `HasSpokenFlag`, `Known`, or `InPlaceableWater`;
- bit 11: `Disabled` or `UsedAsMovingPlatform`;
- bit 13: `Empty` or `ResetDestruction`;
- bit 25: `NoAIAcquire` or `Obstacle`;
- bit 28: `ReflectedByAutoWater` or `ShowOnWorldMap`.

Therefore a raw header flag value is not interpretable without the parent FormType/record schema.

## TESForm InGameFormFlag

| Name | Bit expression | Source line |
|---|---|---:|
| `kNone` | `0` | 112 |
| `kWantsDelete` | `1 << 0` | 113 |
| `kForcedPersistent` | `1 << 1` | 114 |
| `kNoFavorAllowed` | `1 << 4` | 115 |
| `kIsSkyObject` | `1 << 5` | 116 |
| `kRefOriginalPersistent` | `1 << 6` | 117 |
| `kRefPermanentlyDeleted` | `1 << 7` | 118 |

These are **runtime/in-game flags**, separate from plugin record-header flags. They include forced persistence and permanent-deletion state.

## Actor runtime BOOL_BITS

| Name | Bit expression | Source line |
|---|---|---:|
| `kNone` | `0` | 175 |
| `kDelayUpdateScenegraph` | `1 << 0` | 176 |
| `kProcessMe` | `1 << 1` | 177 |
| `kMurderAlarm` | `1 << 2` | 178 |
| `kHasSceneExtra` | `1 << 3` | 179 |
| `kHeadingFixed` | `1 << 4` | 180 |
| `kSpeakingDone` | `1 << 5` | 181 |
| `kIgnoreChangeAnimationCall` | `1 << 6` | 182 |
| `kSoundFileDone` | `1 << 7` | 183 |
| `kVoiceFileDone` | `1 << 8` | 184 |
| `kInTempChangeList` | `1 << 9` | 185 |
| `kDoNotRunSayToCallback` | `1 << 10` | 186 |
| `kDead` | `1 << 11` | 187 |
| `kForceGreetingPlayer` | `1 << 12` | 188 |
| `kForceUpdateQuestTarget` | `1 << 13` | 189 |
| `kSearchingInCombat` | `1 << 14` | 190 |
| `kAttackOnNextTheft` | `1 << 15` | 191 |
| `kEvpBuffered` | `1 << 16` | 192 |
| `kResetAI` | `1 << 17` | 193 |
| `kInWater` | `1 << 18` | 194 |
| `kSwimming` | `1 << 19` | 195 |
| `kVoicePausedByScript` | `1 << 20` | 196 |
| `kWasInFrustrum` | `1 << 21` | 197 |
| `kShouldRotateToTrack` | `1 << 22` | 198 |
| `kSetOnDeath` | `1 << 23` | 199 |
| `kDoNotPadVoice` | `1 << 24` | 200 |
| `kFootIKInRange` | `1 << 25` | 201 |
| `kPlayerTeammate` | `1 << 26` | 202 |
| `kGivePlayerXP` | `1 << 27` | 203 |
| `kSoundCallbackSuccess` | `1 << 28` | 204 |
| `kUseEmotion` | `1 << 29` | 205 |
| `kGuard` | `1 << 30` | 206 |
| `kParalyzed` | `1 << 31` | 207 |

These track transient/current actor state such as water/swimming, teammate status, guard state, paralysis, voice completion and AI-reset state.

## Actor runtime BOOL_FLAGS

| Name | Bit expression | Source line |
|---|---|---:|
| `kNone` | `0` | 212 |
| `kScenePackage` | `1 << 0` | 213 |
| `kIsAMount` | `1 << 1` | 214 |
| `kMountPointClear` | `1 << 2` | 215 |
| `kGettingOnOffMount` | `1 << 3` | 216 |
| `kInRandomScene` | `1 << 4` | 217 |
| `kNoBleedoutRecovery` | `1 << 5` | 218 |
| `kInBleedoutAnimation` | `1 << 6` | 219 |
| `kCanDoFavor` | `1 << 7` | 220 |
| `kShouldAnimGraphUpdate` | `1 << 8` | 221 |
| `kCanSpeakToEssentialDown` | `1 << 9` | 222 |
| `kBribedByPlayer` | `1 << 10` | 223 |
| `kAngryWithPlayer` | `1 << 11` | 224 |
| `kIsTrespassing` | `1 << 12` | 225 |
| `kCanSpeak` | `1 << 13` | 226 |
| `kIsInKillMove` | `1 << 14` | 227 |
| `kAttackOnSight` | `1 << 15` | 228 |
| `kIsCommandedActor` | `1 << 16` | 229 |
| `kForceOneAnimgraphUpdate` | `1 << 17` | 230 |
| `kEssential` | `1 << 18` | 231 |
| `kProtected` | `1 << 19` | 232 |
| `kAttackingDisabled` | `1 << 20` | 233 |
| `kCastingDisabled` | `1 << 21` | 234 |
| `kSceneHeadTrackRotation` | `1 << 22` | 235 |
| `kForceIncMinBoneUpdate` | `1 << 23` | 236 |
| `kCrimeSearch` | `1 << 24` | 237 |
| `kMovingIntoLoadedArea` | `1 << 25` | 238 |
| `kDoNotShowOnStealthMeter` | `1 << 26` | 239 |
| `kMovementBlocked` | `1 << 27` | 240 |
| `kAllowInstantFurniturePopInPlayerCell` | `1 << 28` | 241 |
| `kForceAnimGraphUpdate` | `1 << 29` | 242 |
| `kCheckAddEffectDualCast` | `1 << 30` | 243 |
| `kUnderwater` | `1 << 31` | 244 |

High-value entries include:
- `kEssential`;
- `kProtected`;
- `kIsAMount`;
- `kGettingOnOffMount`;
- `kIsInKillMove`;
- `kIsCommandedActor`;
- `kMovementBlocked`;
- `kDoNotShowOnStealthMeter`;
- `kUnderwater`.

These are current runtime Actor flags, not simply a mirror of NPC_ ACBS flags.

## Actor ChangeFlags

| Name | Bit expression | Source line |
|---|---|---:|
| `kLifeState` | `1 << 10` | 251 |
| `kPackageExtraData` | `1 << 11` | 252 |
| `kMerchantContainer` | `1 << 12` | 253 |
| `kDismemberedLimbs` | `1 << 17` | 254 |
| `kLeveledActor` | `1 << 18` | 255 |
| `kDispModifiers` | `1 << 19` | 256 |
| `kTempModifiers` | `1 << 20` | 257 |
| `kDamageModifiers` | `1 << 21` | 258 |
| `kOverrideModifiers` | `1 << 22` | 259 |
| `kPermanentModifiers` | `1 << 23` | 260 |

These identify actor-state categories that can participate in save ChangeForms, including:
- life state;
- package extra data;
- merchant container;
- dismembered limbs;
- leveled actor data;
- display/temp/damage/override/permanent modifiers.

## Actor reference RecordFlags

| Name | Bit expression | Source line |
|---|---|---:|
| `kDeleted` | `1 << 5` | 268 |
| `kStartsDead` | `1 << 9` | 269 |
| `kPersistent` | `1 << 10` | 270 |
| `kInitiallyDisabled` | `1 << 11` | 271 |
| `kIgnored` | `1 << 12` | 272 |
| `kNoAIAcquire` | `1 << 25` | 273 |
| `kDontHavokSettle` | `1 << 29` | 274 |

This actor-specific interpretation includes:
- Deleted;
- Starts Dead;
- Persistent;
- Initially Disabled;
- Ignored;
- No AI Acquire;
- Don't Havok Settle.

## Persistence implications

### Plugin persistent flag
A record/reference may be marked persistent in plugin data.

### Forced persistent runtime flag
The engine can force runtime persistence even if a user is looking only at the original plugin header.

### Original persistent
Runtime `kRefOriginalPersistent` records original reference persistence separately.

### Permanently deleted
Runtime state can mark a reference permanently deleted even though the base plugin record still exists.

### Save ChangeFlags
Actor state such as life state or ActorValue modifiers can be persisted in ChangeForms independently of static record-header flags.

## Diagnostic rules

1. Never decode a TESForm record flag without knowing the record/FormType.
2. Static record flags and runtime in-game flags are separate bitfields.
3. Actor Essential/Protected runtime state can differ from what a simplistic NPC_ header read suggests.
4. Persistent does not mean the same thing as “currently loaded” or “high process.”
5. An initially-disabled actor and a runtime-disabled reference are distinct states.
6. Save ChangeFlags explain why state can survive after plugin defaults change.
7. For crash/debug logging, print symbolic flag names **with the parent type/context**, not only the hexadecimal bitmask.
