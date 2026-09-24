# Skyrim Native Dialogue, TopicInfo, Branch, and Scene Enums — CommonLibSSE-NG

Imported: 2026-09-24
Status: finite reverse-engineered source catalog

## Sources

- `DialogueTypes.h` blob `75c510a4a68914f23c0e4512b6b24a68b13d6396`
- `TESTopic.h` blob `18ba9d0945fae940ff0d0e3c7ab741fcb383210b`
- `TESTopicInfo.h` blob `00d5c7d4635ecd3afc4e824db96ec78a22d2e0a0`
- `BGSDialogueBranch.h` blob `902f5da13acefa433e5f3277a998c81de402dc87`
- `BGSScene.h` blob `5ce46ba48f742a5cffbf93f2a1638892aeab4830`

Upstream: https://github.com/alandtse/CommonLibSSE-NG

## Dialogue type

| Enum | Value |
|---|---:|


Dialogue type determines the broad engine dialogue family and should not be confused with the individual DIAL subtype.

## DIAL Topic flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kDoAllBeforeRepeating` | `1 << 0` |

## DIAL subtype

| Subtype | Value |
|---|---:|
| `kCustom` | `0` |
| `kForceGreet` | `1` |
| `kRumors` | `2` |
| `kUnk3` | `3` |
| `kIntimidate` | `4` |
| `kFlatter` | `5` |
| `kBribe` | `6` |
| `kAskGift` | `7` |
| `kGift` | `8` |
| `kAskFavor` | `9` |
| `kFavor` | `10` |
| `kShowRelationships` | `11` |
| `kFollow` | `12` |
| `kReject` | `13` |
| `kScene` | `14` |
| `kShow` | `15` |
| `kAgree` | `16` |
| `kRefuse` | `17` |
| `kExitFavorState` | `18` |
| `kMoralRefusal` | `19` |
| `kFlyingMountLand` | `20` |
| `kFlyingMountCancelLand` | `21` |
| `kFlyingMountAcceptTarget` | `22` |
| `kFlyingMountRejectTarget` | `23` |
| `kFlyingMountNoTarget` | `24` |
| `kFlyingMountDestinationReached` | `25` |
| `kAttack` | `26` |
| `kPowerAttack` | `27` |
| `kBash` | `28` |
| `kHit` | `29` |
| `kFlee` | `30` |
| `kBleedout` | `31` |
| `kAvoidThreat` | `32` |
| `kDeath` | `33` |
| `kGroupStrategy` | `34` |
| `kBlock` | `35` |
| `kTaunt` | `36` |
| `kAllyKilled` | `37` |
| `kSteal` | `38` |
| `kYield` | `39` |
| `kAcceptYield` | `40` |
| `kPickpocketCombat` | `41` |
| `kAssault` | `42` |
| `kMurder` | `43` |
| `kAssaultNPC` | `44` |
| `kMurderNPC` | `45` |
| `kPickpocketNPC` | `46` |
| `kStealFromNPC` | `47` |
| `kTrespassAgainstNPC` | `48` |
| `kTrespass` | `49` |
| `kWereTransformCrime` | `50` |
| `kVoicePowerStartShort` | `51` |
| `kVoicePowerStartLong` | `52` |
| `kVoicePowerEndShort` | `53` |
| `kVoicePowerEndLong` | `54` |
| `kAlertIdle` | `55` |
| `kLostIdle` | `56` |
| `kNormalToAlert` | `57` |
| `kAlertToCombat` | `58` |
| `kNormalToCombat` | `59` |
| `kAlertToNormal` | `60` |
| `kCombatToNormal` | `61` |
| `kCombatToLost` | `62` |
| `kLostToNormal` | `63` |
| `kLostToCombat` | `64` |
| `kDetectFriendDie` | `65` |
| `kServiceRefusal` | `66` |
| `kRepair` | `67` |
| `kTravel` | `68` |
| `kTraining` | `69` |
| `kBarterExit` | `70` |
| `kRepairExit` | `71` |
| `kRecharge` | `72` |
| `kRechargeExit` | `73` |
| `kTrainingExit` | `74` |
| `kObserveCombat` | `75` |
| `kNoticeCorpse` | `76` |
| `kTimeToGo` | `77` |
| `kGoodBye` | `78` |
| `kHello` | `79` |
| `kSwingMeleeWeapon` | `80` |
| `kShootBow` | `81` |
| `kZKeyObject` | `82` |
| `kJump` | `83` |
| `kKnockOverObject` | `84` |
| `kDestroyObject` | `85` |
| `kStandonFurniture` | `86` |
| `kLockedObject` | `87` |
| `kPickpocketTopic` | `88` |
| `kPursueIdleTopic` | `89` |
| `kSharedInfo` | `90` |
| `kPlayerCastProjectileSpell` | `91` |
| `kPlayerCastSelfSpell` | `92` |
| `kPlayerShout` | `93` |
| `kIdle` | `94` |
| `kEnterSprintBreath` | `95` |
| `kEnterBowZoomBreath` | `96` |
| `kExitBowZoomBreath` | `97` |
| `kActorCollidewithActor` | `98` |
| `kPlayerinIronSights` | `99` |
| `kOutofBreath` | `100` |
| `kCombatGrunt` | `101` |
| `kLeaveWaterBreath` | `102` |

These are native topic subtypes used for hello/combat/favor/service/misc interaction families. Patching a topic's subtype can alter when the engine considers it even if the INFO conditions are unchanged.

## INFO flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kStartSceneOnEnd` | `1 << 0` |
| `kRandom` | `1 << 1` |
| `kSayOnce` | `1 << 2` |
| `kRequiresPlayerActivation` | `1 << 3` |
| `kInfoRefusal` | `1 << 4` |
| `kRandomEnd` | `1 << 5` |
| `kEndRunningScene` | `1 << 6` |
| `kIsForceGreet` | `1 << 7` |
| `kPlayerAddress` | `1 << 8` |
| `kForceSubtitle` | `1 << 9` |
| `kCanMoveWhileGreeting` | `1 << 10` |
| `kNoLIPFile` | `1 << 11` |
| `kPostProcess` | `1 << 12` |
| `kCustomSoundOutput` | `1 << 13` |
| `kSpendsFavorPoints` | `1 << 14` |

INFO flags affect response selection and lifecycle independently of CTDA conditions.

## Favor level

| Favor level | Value |
|---|---:|
| `kNone` | `0` |
| `kSmall` | `1` |
| `kMedium` | `2` |
| `kLarge` | `3` |

## INFO save ChangeFlags

| Change category | Bit |
|---|---|
| `kSaidOnce` | `(std::uint32_t)1 << 31` |

This is evidence that selected dialogue state can be save-persistent rather than fully re-derived from static INFO data.

## Emotion type

| Emotion | Value |
|---|---:|
| `kNeutral` | `0` |
| `kAnger` | `1` |
| `kDisgust` | `2` |
| `kFear` | `3` |
| `kSad` | `4` |
| `kHappy` | `5` |
| `kSurprise` | `6` |
| `kPuzzled` | `7` |

## Response-level flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kUseEmotionAnimation` | `1 << 0` |

Response emotion/flags are distinct from topic/INFO selection conditions.

## Dialogue-branch flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kTopLevel` | `1 << 0` |
| `kBlocking` | `1 << 1` |
| `kExclusive` | `1 << 2` |

Branch configuration can affect whether dialogue is treated as blocking/exclusive/related even when each INFO looks valid by itself.

## Scene actor flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kNoPlayerActivation` | `1 << 0` |
| `kOptional` | `1 << 1` |
| `kRunOnlyScenePackages` | `1 << 2` |
| `kNoCommandState` | `1 << 3` |

## Scene flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kBeginOnQuestStart` | `1 << 0` |
| `kStopOnQuestEnd` | `1 << 1` |
| `kRepeatConditionsWhileTrue` | `1 << 3` |
| `kInterruptible` | `1 << 4` |

## Scene behaviour flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kDeathPause` | `1 << 0` |
| `kDeathEnd` | `1 << 1` |
| `kCombatPause` | `1 << 2` |
| `kCombatEnd` | `1 << 3` |
| `kDialoguePause` | `1 << 4` |
| `kDialogueEnd` | `1 << 5` |
| `kOBS_COMPause` | `1 << 6` |
| `kOBS_COMEnd` | `1 << 7` |

## Scene save ChangeFlags

| Change category | Bit |
|---|---|
| `kActive` | `(std::uint32_t)1 << 31` |

## Dialogue selection stack

A useful troubleshooting order is:

1. quest running/enabled state;
2. branch/dialogue type;
3. topic subtype;
4. INFO speaker and CTDA conditions;
5. INFO flags/favor state;
6. scene ownership/action phase if scene-driven;
7. response data/emotion;
8. VoiceType and voice asset path;
9. saved INFO/scene/quest state.

## Compatibility implications

1. DIAL, INFO, branch and scene records are separate selection layers.
2. A dialogue line can disappear because the parent quest/branch/type makes it ineligible even when INFO conditions pass.
3. A scene can own/control dialogue in ways ordinary free dialogue does not.
4. Saved dialogue/scene state can make new-game and established-save behavior differ.
5. Voice assets are downstream of selection: a missing FUZ does not explain an INFO that never becomes eligible.
6. Topic subtype and dialogue type are engine enums, not arbitrary organizational labels.
7. Condition order/Run On semantics remain governed by CTDA and should be inspected with `ctda-condition-encoding-xedit.md`.
