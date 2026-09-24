# Skyrim Native AI, Package, Process, Detection, and Movement Enums — CommonLibSSE-NG

Imported: 2026-09-24
Status: finite reverse-engineered source catalog

## Sources

- `TESPackage.h` blob `902cf237ff9f2bcd0db7a8bf646b840ddaaa0542`
- `AIProcess.h` blob `fc690a12f496d8addf03e7a1a7a3f185d6c896f9`
- `ProcessType.h` blob `c7fc09a9b0617dcca69d0f857703cb7c10dd8af7`
- `DetectionPriorities.h` blob `03e2960f0559469157739ea4f32414c752876b8a`
- `FightReactions.h` blob `3ee1aaadf3f7ee0e48eb9a1834169570a3c07a5d`
- `Crime.h` blob `7c5f11a834917759998be57a9830247fa3593280`
- `Movement.h` blob `d3547b9f823015528dd028ad147127b97398fb8c`

Upstream: https://github.com/alandtse/CommonLibSSE-NG

## Package object types

| Name | Value |
|---|---|
| `kNone` | `0` |
| `kACTI` | `1` |
| `kARMO` | `2` |
| `kBOOK` | `3` |
| `kCONT` | `4` |
| `kDOOR` | `5` |
| `kINGR` | `6` |
| `kLIGH` | `7` |
| `kMISC` | `8` |
| `kFLOR` | `9` |
| `kFURN` | `10` |
| `kWEAP` | `11` |
| `kAMMO` | `12` |
| `kKEYM` | `13` |
| `kALCH` | `14` |
| `kFOOD` | `15` |

These identify the broad object category a package target can request/acquire.

## Package types

| Name | Value |
|---|---|
| `kNone` | `static_cast<std::underlying_type_t<PACKAGE_TYPE>>(-1)` |
| `kExplore` | `0` |
| `kFollow` | `1` |
| `kEscort` | `2` |
| `kEat` | `3` |
| `kSleep` | `4` |
| `kWander` | `5` |
| `kTravel` | `6` |
| `kAccompany` | `7` |
| `kUseItemAt` | `8` |
| `kAmbush` | `9` |
| `kFleeNotCombat` | `10` |
| `kCastMagic` | `11` |
| `kSandbox` | `12` |
| `kPatrol` | `13` |
| `kGuard` | `14` |
| `kDialogue` | `15` |
| `kUseWeapon` | `16` |
| `kFind` | `17` |
| `kPackage` | `18` |
| `kPackageTemplate` | `19` |
| `kActivate` | `20` |
| `kAlarm` | `21` |
| `kFlee` | `22` |
| `kTrespass` | `23` |
| `kSpectator` | `24` |
| `kReactToDead` | `25` |
| `kGetUpFromChairBed` | `26` |
| `kDoNothing` | `27` |
| `kInGameDialogue` | `28` |
| `kSurface` | `29` |
| `kSearchForAttacker` | `30` |
| `kAvoidPlayer` | `31` |
| `kReactToDestroyedObject` | `32` |
| `kReactToGrenadeOrMine` | `33` |
| `kStealWarning` | `34` |
| `kPickPocketWarning` | `35` |
| `kMovementBlocked` | `36` |
| `kVampireFeed` | `37` |
| `kCannibal` | `38` |
| `kLanding` | `39` |
| `kUnused` | `40` |
| `kMountActor` | `41` |
| `kDismountActor` | `42` |
| `kClearMountPosition` | `43` |
| `kTotal` | `44` |

Current source defines package values 0–43 plus `None`, with `kTotal = 44`.

High-value types include Follow, Escort, Wander, Travel, Sandbox, Patrol, Guard, Dialogue, Flee, Trespass, Spectator, VampireFeed, MountActor and DismountActor.

## Package procedure types

| Name | Value |
|---|---|
| `kNone` | `static_cast<std::underlying_type_t<PACKAGE_PROCEDURE_TYPE>>(-1)` |
| `kExploreTravel` | `0` |
| `kExploreWander` | `1` |
| `ExploreActivate` | `2` |
| `kExploreAcquire` | `3` |
| `kSleep` | `4` |
| `kEat` | `5` |
| `kFollowWithEscort` | `6` |
| `kAmbushFollow` | `7` |
| `kEscortActor` | `8` |
| `kEscortObject` | `9` |
| `kDialogue` | `10` |
| `kAlarm` | `11` |
| `kActivate` | `12` |
| `kGreet` | `13` |
| `kObserveCombat` | `14` |
| `kObserveDialogue` | `15` |
| `kTalkToDead` | `16` |
| `kFlee` | `17` |
| `kTrespass` | `18` |
| `kGetUpFromChairBed` | `19` |
| `kExploreNPC` | `20` |
| `kMountActor` | `21` |
| `kDismountActor` | `22` |
| `kDoNothing` | `23` |
| `kExploreAcquireGeneric` | `24` |
| `kAccompany` | `25` |
| `kUseItemAt` | `26` |
| `kVampireFeed` | `27` |
| `kAmbush` | `28` |
| `kSurface` | `29` |
| `kFleeNotCombat` | `30` |
| `kSearchForAttacker` | `31` |
| `kClearMountPosition` | `32` |
| `kWaitForDialogue` | `33` |
| `kAvoidPlayer` | `34` |
| `kSandbox` | `35` |
| `kPatrol` | `36` |
| `kReactToDestroyedObject` | `37` |
| `kReactToGrenadeOrMine` | `38` |
| `kGuard` | `39` |
| `kStealWarning` | `40` |
| `kPickPocketWarning` | `41` |
| `kUseWeapon` | `42` |
| `kFollowWithoutEscort` | `43` |
| `kMovementBlocked` | `44` |
| `kCannibal` | `45` |
| `kPackage` | `46` |
| `kLanding` | `47` |
| `kKeepAnEyeOn` | `48` |

Procedure type is not identical to package type. A package can use a procedure tree whose native procedure identity is more specific than the high-level package classification.

Examples:
- `FollowWithEscort` vs `FollowWithoutEscort`;
- `ExploreTravel`, `ExploreWander`, `ExploreAcquire`, and `ExploreNPC`;
- `MountActor` and `DismountActor`;
- `KeepAnEyeOn`.

## Package event-action types

| Name | Value |
|---|---|
| `kBegin` | `0` |

These correspond to package lifecycle/action phases such as Begin, End, Change and Patrol.

## Package interrupt targets

| Name | Value |
|---|---|
| `kNone` | `static_cast<std::underlying_type_t<PACK_INTERRUPT_TARGET>>(-1)` |
| `kSpectator` | `0` |
| `kObserveDead` | `0x1` |
| `kGuardWarn` | `0x2` |
| `kCombat` | `0x3` |

## Package general flags

| Name | Value |
|---|---|
| `kNone` | `0` |
| `kOffersServices` | `1 << 0` |
| `kMustComplete` | `1 << 2` |
| `kMaintainSpeedAtGoal` | `1 << 3` |
| `kUnlocksDoorsAtPackageStart` | `1 << 6` |
| `kUnlocksDoorsAtPackageEnd` | `1 << 7` |
| `kContinueIfPCNear` | `1 << 9` |
| `kOncePerDay` | `1 << 10` |
| `kCreated` | `1 << 11` |
| `kPreferredSpeed` | `1 << 13` |
| `kAlwaysSneak` | `1 << 17` |
| `kAllowSwimming` | `1 << 18` |
| `kIgnoreCombat` | `1 << 20` |
| `kWeaponsUnequipped` | `1 << 21` |
| `kWeaponDrawn` | `1 << 23` |
| `kNoCombatAlert` | `1 << 27` |
| `kWearSleepOutfit` | `1 << 29` |

These include:
- OffersServices;
- MustComplete;
- MaintainSpeedAtGoal;
- door-unlock behavior;
- ContinueIfPCNear;
- OncePerDay;
- preferred-speed use;
- AlwaysSneak;
- AllowSwimming;
- IgnoreCombat;
- weapon drawn/unequipped;
- NoCombatAlert;
- WearSleepOutfit.

## Preferred package speed

| Name | Value |
|---|---|
| `kWalk` | `0` |
| `kJog` | `1` |
| `kRun` | `2` |
| `kFastWalk` | `3` |

## Package interrupt/behavior flags

| Name | Value |
|---|---|
| `kNone` | `0` |
| `kHellosToPlayer` | `1 << 0` |
| `kRandomConversations` | `1 << 1` |
| `kObserveCombatBehaviour` | `1 << 2` |
| `kGreetCorpseBehaviour` | `1 << 3` |
| `kReactionToPlayerActions` | `1 << 4` |
| `kFriendlyFireComments` | `1 << 5` |
| `kAggroRadiusBehavior` | `1 << 6` |
| `kAllowIdleChatter` | `1 << 7` |
| `kWorldInteractions` | `1 << 9` |

These control whether package execution can participate in:
- player hellos;
- random conversations;
- observing combat/dialogue;
- corpse greeting;
- reacting to player actions;
- friendly-fire comments;
- aggro-radius behavior;
- idle chatter;
- world interactions.

## Package schedule day values

| Name | Value |
|---|---|
| `kAny` | `-1` |
| `kSunday` | `0` |
| `kMonday` | `1` |
| `kTuesday` | `2` |
| `kWednesday` | `3` |
| `kThursday` | `4` |
| `kFriday` | `5` |
| `kSaturday` | `6` |
| `kWeekdays` | `7` |
| `kWeekends` | `8` |
| `kMondayWednesdayFriday` | `9` |
| `kTuesdayThursday` | `10` |

A package schedule also stores:
- month;
- date;
- hour;
- minute;
- duration in minutes.

## Actor process levels

| Name | Value |
|---|---|
| `kNone` | `static_cast<std::underlying_type_t<PROCESS_TYPE>>(-1)` |
| `kHigh` | `0` |
| `kMiddleHigh` | `1` |
| `kMiddleLow` | `2` |
| `kLow` | `3` |

Exact meanings:
- High = 0;
- MiddleHigh = 1;
- MiddleLow = 2;
- Low = 3.

This matches the process-level module already in the corpus and gives the native enum source.

## Low-process flags

| Name | Value |
|---|---|
| `kNone` | `0` |
| `kTargetActivated` | `1 << 0` |
| `kCurrentActionComplete` | `1 << 1` |
| `kIsAggressor` | `1 << 2` |
| `kAlert` | `1 << 3` |
| `kFollower` | `1 << 4` |
| `kPackageDoneOnce` | `1 << 5` |
| `kPackageIdleDone` | `1 << 6` |

Low-process actors retain a much smaller set of state, including target activation, action completion, aggressor/alert/follower state and package completion markers.

## Detection priorities

| Name | Value |
|---|---|
| `kNone` | `0` |
| `kVeryLow` | `1` |
| `kLow` | `2` |
| `kNormal` | `3` |
| `kHigh` | `4` |
| `kCritical` | `5` |

Native detection queries can request different priority levels. Do not assume every detection check has identical scheduling/urgency.

## Faction fight reactions

| Name | Value |
|---|---|
| `kNeutral` | `0` |
| `kEnemy` | `1` |
| `kAlly` | `2` |
| `kFriend` | `3` |

Reaction values are:
- Neutral;
- Enemy;
- Ally;
- Friend.

These are native reaction categories, distinct from numeric relationship ranks and faction reaction values stored in plugin data.

## Crime types

| Name | Value |
|---|---|
| `kNone` | `static_cast<std::underlying_type_t<CRIME_TYPE>>(-1)` |
| `kSteal` | `0` |
| `kPickpocket` | `1` |
| `kTrespass` | `2` |
| `kAttack` | `3` |
| `kMurder` | `4` |
| `kEscape` | `5` |
| `kWerewolf` | `6` |
| `kTotal` | `7` |

The current source exposes seven crime categories plus `None`.

## Movement speed directions

| Name | Value |
|---|---|


Movement type data stores directional speed dimensions for left/right/forward/back plus rotations, with separate walk/run speed sets.

## AIProcess state relationships

Current `AIProcess` stores:
- middle-low, middle-high, and high-process data pointers;
- current package;
- cached actor dimensions and speeds;
- equipped forms;
- follow/target/arrest handles;
- low-process flags;
- process level;
- combat/package/pathing state booleans.

This explains why an actor's package Form can be correct while its **currently running package/process state** is different.

## Diagnostic rules

1. Distinguish package **type**, **procedure type**, and the actor's **current running package**.
2. Alias package overrides and scenes can replace the base NPC package stack at runtime.
3. A valid package can still fail because target resolution, schedule, condition, navmesh, collision, process level, or interruption behavior prevents execution.
4. Process level controls how much AI is actively simulated; persistent actors are not automatically High Process.
5. Relationship rank, faction fight reaction, hostility, crime state and detection priority are separate systems.
6. Package `IgnoreCombat` and actor/combat-controller state can conflict with intuitive assumptions about AI.
7. Low-process package completion/state flags can make an unloaded actor appear to “skip” physical behavior and catch up later.
8. When diagnosing follower/AI problems, log package type + procedure + process level + target/location + navmesh result together.
