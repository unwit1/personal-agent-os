# Skyrim Native Actor State Catalog — CommonLibSSE-NG

Imported: 2026-09-24
Source: `alandtse/CommonLibSSE-NG` branch `ng`
Source file: `include/RE/A/ActorState.h`
Source blob SHA: `f3d4d73edd5a65988edd5d1a0d33bc2e9c4731cf`
Status: finite reverse-engineered source catalog

## Life state

| ID | State |
|---:|---|
| 0 | `kAlive` |
| 1 | `kDying` |
| 2 | `kDead` |
| 3 | `kUnconcious` |
| 4 | `kReanimate` |
| 5 | `kRecycle` |
| 6 | `kRestrained` |
| 7 | `kEssentialDown` |
| 8 | `kBleedout` |

CommonLib's `IsBleedingOut()` treats both `kEssentialDown` and `kBleedout` as bleeding-out states. `kReanimate` is explicitly recognized by `IsReanimated()`.

## Attack state

| ID | State |
|---:|---|
| 0 | `kNone` |
| 1 | `kDraw` |
| 2 | `kSwing` |
| 3 | `kHit` |
| 4 | `kNextAttack` |
| 5 | `kFollowThrough` |
| 6 | `kBash` |
| 8 | `kBowDraw` |
| 9 | `kBowAttached` |
| 10 | `kBowDrawn` |
| 11 | `kBowReleasing` |
| 12 | `kBowReleased` |
| 13 | `kBowNextAttack` |
| 14 | `kBowFollowThrough` |
| 15 | `kFire` |
| 16 | `kFiring` |
| 17 | `kFired` |

The current enum intentionally has no value 7. Do not normalize these into a contiguous ordinal sequence.

## Fly state

| ID | State |
|---:|---|
| 0 | `kNone` |
| 1 | `kTakeOff` |
| 2 | `kCruising` |
| 3 | `kHovering` |
| 4 | `kLanding` |
| 5 | `kPerching` |
| 6 | `kAction` |

CommonLib's helper considers all states except `kNone` and `kPerching` to be flying.

## Knock state

| ID | State |
|---:|---|
| 0 | `kNormal` |
| 1 | `kExplode` |
| 2 | `kExplodeLeadIn` |
| 3 | `kOut` |
| 4 | `kOutLeadIn` |
| 5 | `kQueued` |
| 6 | `kGetUp` |
| 7 | `kDown` |
| 8 | `kWaitForTaskQueue` |

## Sit / sleep state

| ID | State |
|---:|---|
| 0 | `kNormal` |
| 1 | `kWantToSit` |
| 2 | `kWaitingForSitAnim` |
| 3 | `kIsSitting` |
| static_cast | `kRidingMount` |
| 4 | `kWantToStand` |
| 5 | `kWantToSleep` |
| 6 | `kWaitingForSleepAnim` |
| 7 | `kIsSleeping` |
| 8 | `kWantToWake` |

`kRidingMount` aliases the same numeric value as `kIsSitting`. Context determines whether the actor is mounted or using ordinary furniture.

## Weapon state

| ID | State |
|---:|---|
| 0 | `kSheathed` |
| 1 | `kWantToDraw` |
| 2 | `kDrawing` |
| 3 | `kDrawn` |
| 4 | `kWantToSheathe` |
| 5 | `kSheathing` |

CommonLib's `IsWeaponDrawn()` returns true for `kDrawn`, `kWantToSheathe`, and `kSheathing`.

## Packed runtime state

### ActorState1 bitfields

Current reverse-engineered fields include:

- moving back / forward / right / left;
- walking;
- running;
- sprinting;
- sneaking;
- swimming;
- sit/sleep state;
- fly state;
- life state;
- knock state;
- melee attack state.

### ActorState2 bitfields

Current reverse-engineered fields include:

- talking to player;
- force run;
- force sneak;
- head tracking;
- reanimating;
- weapon state;
- want blocking;
- flight blocked;
- recoil;
- allow flying;
- staggered.

## Diagnostic implications

1. Runtime actor state is not the same thing as NPC_ base flags.
2. Essential-down and ordinary bleedout are different enum values even though both satisfy the helper predicate.
3. Sitting and riding share a raw numeric state in the sit/sleep enum.
4. Attack-state IDs are not contiguous.
5. A weapon can be behaviorally "drawn" during a sheathing transition.
6. Animation-event state and native ActorState can disagree transiently; native code should use the engine state relevant to the feature being implemented.
7. These values are runtime/process state and are not guaranteed to be meaningful for an unloaded actor with no active process.
