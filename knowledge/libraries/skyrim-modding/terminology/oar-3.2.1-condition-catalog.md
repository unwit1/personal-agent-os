# Open Animation Replacer 3.2.1 — Built-in Condition Catalog

Imported: 2026-09-24
Pinned source commit: `f4e7688b065175aff70aa523073857911e15aca3`
Source: `src/Conditions.h` blob `d4559c9c3bfc100596a2370dd7108180045862d0`
Built-in user-facing conditions: **123**
Status: finite source-derived catalog

## Catalog

| Condition | C++ class | Minimum OAR | Description | Source line |
|---|---|---:|---|---:|
| `OR` | `ORCondition` | 1.0.0 | Checks if any of the child conditions are true. | 92 |
| `AND` | `ANDCondition` | 1.0.0 | Checks if all of the child conditions are true. | 113 |
| `IsForm` | `IsFormCondition` | 1.0.0 | Checks if the ref matches the specified form. | 134 |
| `IsEquipped` | `IsEquippedCondition` | 1.0.0 | Checks if the ref has the specified form equipped in the right or left hand. | 155 |
| `IsEquippedType` | `IsEquippedTypeCondition` | 1.0.0 | Checks if the ref has an item of the specified type equipped in the right or left hand. | 182 |
| `IsEquippedHasKeyword` | `IsEquippedHasKeywordCondition` | 1.0.0 | Checks if the ref has an item equipped in the right or left hand that has the specified keyword. | 214 |
| `IsEquippedPower` | `IsEquippedPowerCondition` | 1.0.0 | Checks if the ref has the specified spell equipped in the power slot. | 241 |
| `IsWorn` | `IsWornCondition` | 1.0.0 | Checks if the ref has the specified form equipped in any slot. | 264 |
| `IsWornHasKeyword` | `IsWornHasKeywordCondition` | 1.0.0 | Checks if the ref has an item equipped in any slot that has the specified keyword. | 285 |
| `IsFemale` | `IsFemaleCondition` | 1.0.0 | Checks if the ref is female. | 306 |
| `IsChild` | `IsChildCondition` | 1.0.0 | Checks if the ref is a child. | 317 |
| `IsPlayerTeammate` | `IsPlayerTeammateCondition` | 1.0.0 | Checks if the ref is a teammate of the player. | 328 |
| `IsInInterior` | `IsInInteriorCondition` | 1.0.0 | Checks if the ref is in an interior cell. | 339 |
| `IsInFaction` | `IsInFactionCondition` | 1.0.0 | Checks if the ref is in the specified faction. | 350 |
| `HasKeyword` | `HasKeywordCondition` | 1.0.0 | Checks if the ref has the specified keyword. | 371 |
| `HasMagicEffect` | `HasMagicEffectCondition` | 1.0.0 | Checks if the ref is currently affected by the specified magic effect. | 392 |
| `HasMagicEffectWithKeyword` | `HasMagicEffectWithKeywordCondition` | 1.0.0 | Checks if the ref is currently affected by a magic effect that has the specified keyword. | 415 |
| `HasPerk` | `HasPerkCondition` | 1.0.0 | Checks if the ref has the specified perk. | 438 |
| `HasSpell` | `HasSpellCondition` | 1.0.0 | Checks if the ref has the specified spell or shout. | 459 |
| `CompareValues` | `CompareValues` | 1.0.0 | Compares two values. | 480 |
| `Level` | `LevelCondition` | 1.0.0 | Tests the actor's level against the specified value. | 519 |
| `IsActorBase` | `IsActorBaseCondition` | 1.0.0 | Checks if the ref's actor base form is the specified form. | 546 |
| `IsRace` | `IsRaceCondition` | 1.0.0 | Checks if the ref's race is the specified race. | 569 |
| `CurrentWeather` | `CurrentWeatherCondition` | 1.0.0 | Checks if the current weather is the specified weather. | 592 |
| `CurrentGameTime` | `CurrentGameTimeCondition` | 1.0.0 | Tests the current game time against the specified time. | 614 |
| `Random` | `RandomCondition` | 2.3.0 | Compares a random value with a numeric value. | 640 |
| `IsUnique` | `IsUniqueCondition` | 1.0.0 | Checks if the ref is flagged as unique. | 699 |
| `IsClass` | `IsClassCondition` | 1.0.0 | Checks if the ref's class is the specified class. | 710 |
| `IsCombatStyle` | `IsCombatStyleCondition` | 1.0.0 | Checks if the ref's combat style is the specified combat style. | 733 |
| `IsVoiceType` | `IsVoiceTypeCondition` | 1.0.0 | Checks if the ref's voice type is the specified voice type. | 756 |
| `IsAttacking` | `IsAttackingCondition` | 1.0.0 | Checks if the ref is attacking. | 779 |
| `IsRunning` | `IsRunningCondition` | 1.0.0 | Checks if the ref is running. | 790 |
| `IsSneaking` | `IsSneakingCondition` | 1.0.0 | Checks if the ref is sneaking. | 801 |
| `IsSprinting` | `IsSprintingCondition` | 1.0.0 | Checks if the ref is sprinting. | 812 |
| `IsInAir` | `IsInAirCondition` | 1.0.0 | Checks if the ref is in the air. | 823 |
| `IsInCombat` | `IsInCombatCondition` | 1.0.0 | Checks if the ref is in combat. | 834 |
| `IsWeaponDrawn` | `IsWeaponDrawnCondition` | 1.0.0 | Checks if the ref has a weapon drawn. | 845 |
| `IsInLocation` | `IsInLocationCondition` | 1.0.0 | Checks if the ref is in the specified location. | 856 |
| `HasRefType` | `HasRefTypeCondition` | 1.0.0 | Checks if the ref has the specified LocRefType attached. | 879 |
| `IsParentCell` | `IsParentCellCondition` | 1.0.0 | Checks if the ref is currently in the specified cell. | 901 |
| `IsWorldSpace` | `IsWorldSpaceCondition` | 1.0.0 | Checks if the ref is currently in the specified worldspace. | 923 |
| `FactionRank` | `FactionRankCondition` | 1.0.0 | Tests the ref's faction rank against the specified rank. | 945 |
| `IsMovementDirection` | `IsMovementDirectionCondition` | 1.0.0 | Checks if the ref is moving in the specified direction. | 975 |
| `IsEquippedShout` | `IsEquippedShoutCondition` | 1.0.0 | Checks if the ref has the specified shout equipped. | 1001 |
| `HasGraphVariable` | `HasGraphVariableCondition` | 1.0.0 | Checks if the ref has the specified graph variable. | 1024 |
| `SubmergeLevel` | `SubmergeLevelCondition` | 1.0.0 | Tests the ref's water submerge level (0-1) against a numeric value. | 1049 |
| `IsReplacerEnabled` | `IsReplacerEnabledCondition` | 1.0.0 | Checks if there's a replacer submod enabled with the given name. Leave the submod name empty to check if any submods are enabled in the replacer mod. | 1072 |
| `IsCurrentPackage` | `IsCurrentPackageCondition` | 1.0.0 | Checks if the ref's currently running the specified package. | 1097 |
| `IsWornInSlotHasKeyword` | `IsWornInSlotHasKeywordCondition` | 1.0.0 | Checks if the ref has an item worn in the specified slot that has the specified keyword. | 1120 |
| `Scale` | `ScaleCondition` | 1.0.0 | Tests the ref's scale against a numeric value. | 1146 |
| `Height` | `HeightCondition` | 1.0.0 | Tests the actor's height against a numeric value. | 1169 |
| `Weight` | `WeightCondition` | 1.0.0 | Tests the actor's weight against a numeric value. | 1192 |
| `MovementSpeed` | `MovementSpeedCondition` | 1.0.0 | Tests the ref's movement speed of a given type against a numeric value. | 1215 |
| `CurrentMovementSpeed` | `CurrentMovementSpeedCondition` | 1.0.0 | Tests the ref's current movement speed against a numeric value. | 1245 |
| `WindSpeed` | `WindSpeedCondition` | 1.0.0 | Tests the current weather's wind speed against a numeric value. | 1268 |
| `WindAngleDifference` | `WindAngleDifferenceCondition` | 1.0.0 | Tests the difference between current weather's wind angle and the ref's angle against a numeric value. | 1292 |
| `CrimeGold` | `CrimeGoldCondition` | 1.0.0 | Tests the actor's current crime gold against a numeric value. | 1320 |
| `IsBlocking` | `IsBlockingCondition` | 1.1.0 | Checks if the ref is blocking. | 1345 |
| `IsCombatState` | `IsCombatStateCondition` | 1.1.0 | Checks if the ref's current combat state matches the given state. | 1356 |
| `InventoryCount` | `InventoryCountCondition` | 1.1.0 | Tests the actor's current inventory count of a specified form against a numeric value. | 1383 |
| `FallDistance` | `FallDistanceCondition` | 1.1.0 | Gets the actor's current fall distance and tests it against a numeric value. | 1409 |
| `FallDamage` | `FallDamageCondition` | 1.1.0 | Calculates the actor's fall damage if they landed at this moment and tests it against a numeric value. | 1433 |
| `CurrentPackageType` | `CurrentPackageTypeCondition` | 3.0.0 | Checks if the actor's current package is of a given type. | 1457 |
| `IsOnMount` | `IsOnMountCondition` | 1.1.0 | Checks if the ref is riding a mount. | 1484 |
| `IsRiding` | `IsRidingCondition` | 1.1.0 | Checks if the ref is riding the specified form. | 1495 |
| `IsRidingHasKeyword` | `IsRidingHasKeywordCondition` | 1.1.0 | Checks if the ref is riding a form with the specified keyword. | 1519 |
| `IsBeingRidden` | `IsBeingRiddenCondition` | 1.1.0 | Checks if the ref is currently mounted by someone. | 1540 |
| `IsBeingRiddenBy` | `IsBeingRiddenByCondition` | 1.1.0 | Checks if the ref is currently mounted by the specified form. | 1551 |
| `CurrentFurniture` | `CurrentFurnitureCondition` | 1.1.0 | Checks if the ref is currently occupying the specified furniture. | 1575 |
| `CurrentFurnitureHasKeyword` | `CurrentFurnitureHasKeywordCondition` | 1.1.0 | Checks if the ref is currently occupying furniture with the specified keyword. | 1599 |
| `HasTarget` | `HasTargetCondition` | 1.1.0 | Checks if the actor has a target of a given type. | 1640 |
| `CurrentTargetDistance` | `CurrentTargetDistanceCondition` | 1.1.0 | Tests the distance to an actor's current target against a numeric value. | 1653 |
| `CurrentTargetRelationship` | `CurrentTargetRelationshipCondition` | 1.1.0 | Tests the relationship between the actor and their current target against a numeric value. | 1678 |
| `EquippedObjectWeight` | `EquippedObjectWeightCondition` | 1.2.0 | Tests the weight of the object currently equipped in the right or left hand against a numeric value. | 1709 |
| `CurrentCastingType` | `CurrentCastingTypeCondition` | 1.2.0 | Checks if the actor's current casting type of the given casting source is the required type. | 1752 |
| `CurrentDeliveryType` | `CurrentDeliveryTypeCondition` | 1.2.0 | Checks if the actor's current delivery type of the given casting source is the required type. | 1779 |
| `IsQuestStageDone` | `IsQuestStageDoneCondition` | 1.2.0 | Checks if the specified stage in the given quest has been completed. | 1806 |
| `CurrentWeatherHasFlag` | `CurrentWeatherHasFlagCondition` | 1.2.0 | Checks if the current weather has the specified flag enabled. | 1828 |
| `InventoryCountHasKeyword` | `InventoryCountHasKeywordCondition` | 1.2.0 | Tests the actor's current inventory count of all items with a specified keyword against a numeric value. | 1854 |
| `CurrentTargetRelativeAngle` | `CurrentTargetRelativeAngleCondition` | 1.2.0 | Tests the relative angle between an actor and their current target. | 1880 |
| `CurrentTargetLineOfSight` | `CurrentTargetLineOfSightCondition` | 1.2.0 | Checks if the actor's current target is in their line of sight, or if the actor is in their current target's line of sight. | 1910 |
| `CurrentRotationSpeed` | `CurrentRotationSpeedCondition` | 1.2.0 | Tests the ref's current rotation speed against a numeric value. | 1932 |
| `IsTalking` | `IsTalkingCondition` | 1.2.0 | Checks if the ref is talking either in monologue or in dialogue. | 1955 |
| `IsGreetingPlayer` | `IsGreetingPlayerCondition` | 1.2.0 | Checks if the ref is greeting the player. | 1966 |
| `IsInScene` | `IsInSceneCondition` | 1.2.0 | Checks if the ref is currently in a scene. | 1977 |
| `IsInSpecifiedScene` | `IsInSpecifiedSceneCondition` | 1.2.0 | Checks if the ref is currently in the specified scene. | 1988 |
| `IsScenePlaying` | `IsScenePlayingCondition` | 1.2.0 | Checks if a specific scene is currently playing. | 2009 |
| `IsDoingFavor` | `IsDoingFavorCondition` | 1.2.0 | Checks if the ref has been asked to do something by the player. | 2029 |
| `AttackState` | `AttackStateCondition` | 1.3.0 | Checks the actor's attack state. | 2040 |
| `IsMenuOpen` | `IsMenuOpenCondition` | 1.3.0 | Checks if a specific menu is currently open. | 2070 |
| `TARGET` | `TARGETCondition` | 1.3.0 | Checks if all of the child conditions are true, but evaluates them for the current target instead. | 2091 |
| `PLAYER` | `PLAYERCondition` | 1.3.0 | Checks if all of the child conditions are true, but evaluates them for the player instead. | 2118 |
| `LightLevel` | `LightLevelCondition` | 2.0.0 | Tests the current strength of lighting on this ref against the specified value. | 2142 |
| `LocationHasKeyword` | `LocationHasKeywordCondition` | 2.0.0 | Checks if the current location has the specified keyword. | 2167 |
| `LifeState` | `LifeStateCondition` | 2.1.0 | Checks the actor's life state. | 2188 |
| `SitSleepState` | `SitSleepStateCondition` | 2.1.0 | Checks the actor's sit/sleep state. | 2218 |
| `XOR` | `XORCondition` | 2.1.0 | Checks if only one of the child conditions is true (Exclusive OR). | 2248 |
| `PRESET` | `PRESETCondition` | 2.2.0 | Evaluate a condition preset defined in the replacer mod in place of this condition. Useful if you want to reuse the same set of conditions in multiple submods.  Manage condition presets in the replacer mod and don't forget to save the config! | 2269 |
| `MOUNT` | `MOUNTCondition` | 2.2.0 | Checks if all of the child conditions are true, but evaluates them for the mount instead. | 2292 |
| `IsAttackTypeKeyword` | `IsAttackTypeKeywordCondition` | 2.2.0 | Checks if the performed attack type is equal to the specified keyword. | 2316 |
| `IsAttackTypeFlag` | `IsAttackTypeFlagCondition` | 2.2.0 | Checks if the performed attack has the specified flag enabled. | 2339 |
| `MovementSurfaceAngle` | `MovementSurfaceAngleCondition` | 2.3.0 | Tests the angle of the surface that the ref is walking on against a numeric value. The angle is calculated by comparing the surface's normal vector and the ref's forward vector. | 2367 |
| `LocationCleared` | `LocationClearedCondition` | 2.2.0 | Checks if the current location is cleared. | 2437 |
| `IsSummoned` | `IsSummonedCondition` | 2.2.0 | Checks if the ref is a summoned creature. | 2448 |
| `IsEquippedHasEnchantment` | `IsEquippedHasEnchantmentCondition` | 2.2.0 | Checks if the ref has an item equipped in the right or left hand that has the specified enchantment. | 2459 |
| `IsEquippedHasEnchantmentWithKeyword` | `IsEquippedHasEnchantmentWithKeywordCondition` | 2.2.0 | Checks if the ref has an item equipped in the right or left hand that has an enchantment with the specified keyword. | 2484 |
| `IsOnStairs` | `IsOnStairsCondition` | 2.3.0 | Checks if the ref is on stairs. Keep in mind that not all stairs in the game are marked as such. | 2509 |
| `SurfaceMaterial` | `SurfaceMaterialCondition` | 2.3.0 | Checks if the surface the ref is standing on has a specified material ID. | 2520 |
| `IsOverEncumbered` | `IsOverEncumberedCondition` | 2.3.0 | Checks if the ref is over-encumbered. | 2549 |
| `IsTrespassing` | `IsTrespassingCondition` | 2.3.0 | Checks if the ref is trespassing. | 2560 |
| `IsGuard` | `IsGuardCondition` | 2.3.0 | Checks if the ref is a guard. | 2571 |
| `IsCrimeSearching` | `IsCrimeSearchingCondition` | 2.3.0 | Checks if the ref is searching for a criminal. | 2582 |
| `IsCombatSearching` | `IsCombatSearchingCondition` | 2.3.0 | Checks if the ref is searching for a target in combat. | 2593 |
| `IdleTime` | `IdleTimeCondition` | 2.3.0 | Compares the time the actor has spent idling with a numeric value. | 2604 |
| `IsAboveWater` | `IsAboveWaterCondition` | 3.0.0 | Checks if the actor is above water - as in, if it fell straight down, it'd hit water. | 2651 |
| `MagicEffectElapsedTime` | `MagicEffectElapsedTimeCondition` | 3.0.0 | Compares the time the ref has been affected by the specified magic effect with a numeric value. | 2671 |
| `IsWornInSlot` | `IsWornInSlotCondition` | 3.0.0 | Checks if the ref has an item worn in the specified slot. | 2698 |
| `InventoryWeight` | `InventoryWeightCondition` | 3.0.0 | Tests the actor's total inventory weight, or the current encumbrance percentage, against a numeric value. | 2722 |
| `IsGhost` | `IsGhostCondition` | 3.0.0 | Checks if the ref is in the ghost (invulnerable) state. Not related to in-game ghosts. | 2748 |
| `IsSwimming` | `IsSwimmingCondition` | 3.0.0 | Checks if the actor is swimming. | 2759 |
| `IsStaggered` | `IsStaggeredCondition` | 3.1.0 | Checks if the actor is staggered. | 2770 |
| `CastingSpell` | `CastingSpellCondition` | 3.1.0 | Checks if the actor is currently casting a spell with the specified casting source. | 2781 |
| `HasBoundWeaponEquipped` | `HasBoundWeaponEquippedCondition` | 3.2.0 | Checks if the ref has a bound weapon equipped in the right or left hand. | 2805 |

## Parser/error sentinel conditions

- `! INVALID !` — class `InvalidCondition`, minimum 0.0.0: The condition was not found!
- `! DEPRECATED !` — class `DeprecatedCondition`, minimum 0.0.0: The condition has been deprecated in the current version of Open Animation Replacer. This submod needs to be updated.

## Condition API version

| Enum | Value | Meaning |
|---|---|---|
| `kOld_Normal` | `0` | legacy pre-versioning compatibility identity |
| `kOld_Custom` | `1` | legacy pre-versioning compatibility identity |
| `kOld_Preset` | `2` | legacy pre-versioning compatibility identity |
| `V3` | `3` | first proper versioned condition API |
| `V4` | `4` | current API generation in this source snapshot |
| `Latest` | `V4` | alias to current latest API |

## Condition type

| Type | Value |
|---|---|
| `kNormal` | `0` |
| `kCustom` | `1` |
| `kPreset` | `2` |

## Condition component types

| Component | Value |
|---|---|
| `kMulti` | `implicit` |
| `kForm` | `implicit` |
| `kNumeric` | `implicit` |
| `kNiPoint3` | `implicit` |
| `kKeyword` | `implicit` |
| `kText` | `implicit` |
| `kBool` | `implicit` |
| `kComparison` | `implicit` |
| `kState` | `implicit` |
| `kCustom` | `implicit` |
| `kPreset` | `implicit` |

These component types form the configurable arguments of conditions: nested condition sets, forms, numbers, vectors, keywords, text, bools, comparisons, state, custom components and presets.

## Essential state

| State | Value | Runtime intent |
|---|---|---|
| `kEssential` | `implicit` | missing/invalid provider should invalidate correct evaluation |
| `kNonEssential_True` | `implicit` | missing non-essential condition may be treated as true |
| `kNonEssential_False` | `implicit` | missing non-essential condition may be treated as false |

## Stateful built-ins

Several built-ins maintain runtime state rather than recomputing a timeless predicate.

### Random
Minimum OAR 2.3.0. Stores a random float and exposes Local/SubMod/ReplacerMod scopes. It can reset on loop/echo.

### MovementSurfaceAngle
Minimum OAR 2.3.0. Maintains smoothed surface-normal state. Source fixes its state scope to **SubMod**.

### IdleTime
Minimum OAR 2.3.0. Tracks accumulated idle time. Source fixes its state scope to **Reference**.

Stateful conditions are why two identical-looking condition trees can behave differently when their scope/reset settings differ.

## Compatibility rules

1. A condition's **minimum OAR version is part of its schema**.
2. A custom condition's provider plugin and API version are part of the dependency.
3. Invalid/deprecated conditions do not become valid merely because their text resembles an older DAR condition.
4. Logical wrappers such as OR, AND, XOR, TARGET, PLAYER, MOUNT and PRESET change evaluation context/structure.
5. Dynamic conditions can change while a clip is playing, but whether the replacement reacts immediately also depends on submod interrupt/loop/echo settings.
6. State scope is separate from submod priority.
7. The built-in catalog is finite for this source snapshot; custom plugins make the overall ecosystem open-ended.
