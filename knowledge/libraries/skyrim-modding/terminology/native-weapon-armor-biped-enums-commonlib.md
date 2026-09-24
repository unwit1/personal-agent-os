# Skyrim Native Weapon, Armor, and Biped Enums — CommonLibSSE-NG

Imported: 2026-09-24
Status: finite reverse-engineered source catalog

## Sources

- `TESObjectWEAP.h` blob `0dbb9bbcd266ce42c7b051491da3fab6cd9067e0`
- `TESObjectARMO.h` blob `9090fcc0cf0427004ad479c3ee9b906006994ccb`
- `BGSBipedObjectForm.h` blob `f0505a3834f2fbd8c0b5b96530d5849f95f65880`

Upstream: https://github.com/alandtse/CommonLibSSE-NG

## Biped Object slot mask

| Native slot flag | Bit |
|---|---|
| `kNone` | `0` |
| `kHead` | `1 << 0` |
| `kHair` | `1 << 1` |
| `kBody` | `1 << 2` |
| `kHands` | `1 << 3` |
| `kForearms` | `1 << 4` |
| `kAmulet` | `1 << 5` |
| `kRing` | `1 << 6` |
| `kFeet` | `1 << 7` |
| `kCalves` | `1 << 8` |
| `kShield` | `1 << 9` |
| `kTail` | `1 << 10` |
| `kLongHair` | `1 << 11` |
| `kCirclet` | `1 << 12` |
| `kEars` | `1 << 13` |
| `kModMouth` | `1 << 14` |
| `kModNeck` | `1 << 15` |
| `kModChestPrimary` | `1 << 16` |
| `kModBack` | `1 << 17` |
| `kModMisc1` | `1 << 18` |
| `kModPelvisPrimary` | `1 << 19` |
| `kDecapitateHead` | `1 << 20` |
| `kDecapitate` | `1 << 21` |
| `kModPelvisSecondary` | `1 << 22` |
| `kModLegRight` | `1 << 23` |
| `kModLegLeft` | `1 << 24` |
| `kModFaceJewelry` | `1 << 25` |
| `kModChestSecondary` | `1 << 26` |
| `kModShoulder` | `1 << 27` |
| `kModArmLeft` | `1 << 28` |
| `kModArmRight` | `1 << 29` |
| `kModMisc2` | `1 << 30` |
| `kFX01` | `1 << 31` |

The 32 bits correspond to numeric Biped slots 30–61 in order.

### CommonLib naming vs xEdit default naming

Current CommonLib gives conventional names for mod-reserved slots that xEdit 4.1.5f's default Skyrim labels leave as `Unnamed`, including:

- slot 44 — ModMouth;
- 45 — ModNeck;
- 46 — ModChestPrimary;
- 47 — ModBack;
- 48 — ModMisc1;
- 49 — ModPelvisPrimary;
- 52 — ModPelvisSecondary;
- 53 — ModLegRight;
- 54 — ModLegLeft;
- 55 — ModFaceJewelry;
- 56 — ModChestSecondary;
- 57 — ModShoulder;
- 58 — ModArmLeft;
- 59 — ModArmRight;
- 60 — ModMisc2.

The **bit/slot number** remains canonical. Labels are a source/tool convention and custom RACE Biped Object names can override display labels.

## Armor type

| Native armor type | Value |
|---|---:|
| `kLightArmor` | `0` |
| `kHeavyArmor` | `1` |
| `kClothing` | `2` |

ArmorType is separate from keywords such as ArmorLight/ArmorHeavy and from Biped slot masks. A patch should keep those systems coherent.

## ARMO record flags

| Flag | Bit |
|---|---|
| `kNonPlayable` | `1 << 2` |
| `kDeleted` | `1 << 5` |
| `kShield` | `1 << 6` |
| `kIgnored` | `1 << 12` |

Current native flags include NonPlayable, Deleted, Shield, and Ignored.

### Armor native layout

Current `TESObjectARMO` includes:
- race form;
- enchantable/value/weight components;
- destructible/pickup-putdown sound components;
- Biped model data;
- EQUP equip type;
- Biped slot mask;
- block/bash data;
- keywords;
- armor rating stored as CK value × 100;
- ARMA array;
- optional template armor.

## Weapon type

| Weapon type | Value |
|---|---:|
| `kHandToHandMelee` | `0` |
| `kOneHandSword` | `1` |
| `kOneHandDagger` | `2` |
| `kOneHandAxe` | `3` |
| `kOneHandMace` | `4` |
| `kTwoHandSword` | `5` |
| `kTwoHandAxe` | `6` |
| `kBow` | `7` |
| `kStaff` | `8` |
| `kCrossbow` | `9` |

The values align with the xEdit WEAP animation type catalog and give a native source for the same 0–9 families.

## Weapon hit behavior

| Behavior | Value |
|---|---:|
| `kNormal` | `0` |
| `kDismemberOnly` | `1` |
| `kExplodeOnly` | `2` |
| `kNoDismemberOrExplode` | `3` |

## Weapon rumble pattern

| Pattern | Value |
|---|---:|
| `kConstant` | `0` |
| `kPeriodicSquare` | `1` |
| `kPeriodicTriangle` | `2` |
| `kPeriodicSawtooth` | `3` |

Some current CommonLib comments mark portions of ranged/rumble data as possible Fallout leftovers. Preserve that uncertainty instead of assuming every field has an active Skyrim gameplay effect.

## WEAP record flags

| Flag | Bit |
|---|---|
| `kNonPlayable` | `1 << 2` |
| `kHasInheritedFromTemplate` | `1 << 3` |
| `kDeleted` | `1 << 5` |
| `kIgnored` | `1 << 12` |

`HasInheritedFromTemplate` is documented by CommonLib as cleared on load and set by relevant InitItemImpl processing, so it should not be treated as a normal author-controlled persistent flag without understanding that lifecycle.

## WEAP DNAM Flag2

| Flag | Bit |
|---|---|
| `kNone` | `0` |
| `kPlayerOnly` | `1 << 0` |
| `kNPCsUseAmmo` | `1 << 1` |
| `kNoJamAfterReload` | `1 << 2` |
| `kMinorCrime` | `1 << 4` |
| `kRangeFixed` | `1 << 5` |
| `kNotUsedInNormalCombat` | `1 << 6` |
| `kOverridesConditionDamage` | `1 << 7` |
| `kDontUse3rdPersonISAnim` | `1 << 8` |
| `kBurstShot` | `1 << 9` |
| `kRumbleAlternate` | `1 << 10` |
| `kLongBursts` | `1 << 11` |
| `kNonHostile` | `1 << 12` |
| `kBoundWeapon` | `1 << 13` |

High-value current entries include:
- PlayerOnly;
- NPCsUseAmmo;
- MinorCrime;
- RangeFixed;
- NotUsedInNormalCombat;
- OverridesConditionDamage;
- BurstShot;
- NonHostile;
- BoundWeapon.

Several other bits are explicitly commented as unused in current source.

## WEAP DNAM primary flags

| Flag | Bit |
|---|---|
| `kNone` | `0` |
| `kPlayerOnly` | `1 << 0` |
| `kNPCsUseAmmo` | `1 << 1` |
| `kNoJamAfterReload` | `1 << 2` |
| `kMinorCrime` | `1 << 4` |
| `kRangeFixed` | `1 << 5` |
| `kNotUsedInNormalCombat` | `1 << 6` |
| `kOverridesConditionDamage` | `1 << 7` |
| `kDontUse3rdPersonISAnim` | `1 << 8` |
| `kBurstShot` | `1 << 9` |
| `kRumbleAlternate` | `1 << 10` |
| `kLongBursts` | `1 << 11` |
| `kNonHostile` | `1 << 12` |
| `kBoundWeapon` | `1 << 13` |

High-value entries include:
- IgnoresNormalWeaponResistance;
- CantDrop;
- NonPlayable.

Several legacy bits are marked unused in current source.

## AttackAnimation IDs

| Native attack animation | ID |
|---|---:|
| `kAttackLeft` | `26` |
| `kAttackRight` | `32` |
| `kAttack3` | `38` |
| `kAttack4` | `44` |
| `kAttack5` | `50` |
| `kAttack7` | `62` |
| `kAttack8` | `68` |
| `kAttackLoop` | `74` |
| `kAttackSpin` | `80` |
| `kAttackSpin2` | `86` |
| `kPlaceMine` | `97` |
| `kPlaceMine2` | `103` |
| `kAttackThrow` | `109` |
| `kAttackThrow2` | `115` |
| `kAttackThrow3` | `121` |
| `kAttackThrow4` | `127` |
| `kAttackThrow5` | `133` |
| `kDefault` | `255` |

These numeric IDs are not OAR priorities or behavior-event names. They are native WEAP attack-animation selectors.

## Critical-data flags

| Flag | Bit |
|---|---|


`OnDeath` controls a critical-effect behavior branch in CRDT.

## Native WEAP gameplay fields

Current WEAP `Data` includes:
- speed;
- reach;
- minimum/maximum range;
- animation attack multiplier;
- damage-to-weapon multiplier;
- stagger;
- hit behavior;
- governing skill;
- resistance ActorValue;
- Flag2;
- attack animation;
- animation type;
- primary flags.

RangedData adds:
- sight FOV;
- fire rate field;
- rumble strengths/duration/pattern;
- projectile count.

## Compatibility rules

1. **ARMO**, **ARMA**, **Biped slot mask**, **EQUP**, **keywords**, and **Race support** must be treated as separate layers.
2. Armor slot labels are not immutable semantics; slot numbers/bits are.
3. WEAP animation type describes a native family, not the actual behavior/OAR animation that wins at runtime.
4. A weapon balance patch should reconcile damage, speed, reach, stagger, skill, flags and critical data independently.
5. Bound-weapon behavior can involve both WEAP flags and MagicEffect/Spell archetypes.
6. Runtime inventory ExtraData can still differentiate individual copies after the base WEAP/ARMO record is patched.
7. Fields marked unused/legacy in current reverse-engineered source should remain version-scoped and not be promoted to active Skyrim mechanics without testing.
