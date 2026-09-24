# Skyrim Native ActorBase, AI, and Race Enums — CommonLibSSE-NG

Imported: 2026-09-24
Status: finite reverse-engineered source catalog

## Sources

- `TESActorBaseData.h` blob `cba251d7cc126c936531463cba80d61cd0d170f1`
- `TESAIForm.h` blob `0756d8f1ee29cb242ea01060ce28650ddda34c5e`
- `TESRace.h` blob `96024ef7e215a376be01eae8dd8dcfc9be001ffc`

Upstream: https://github.com/alandtse/CommonLibSSE-NG

## ActorBase ACBS flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kFemale` | `1 << 0` |
| `kEssential` | `1 << 1` |
| `kIsChargenFacePreset` | `1 << 2` |
| `kRespawn` | `1 << 3` |
| `kAutoCalcStats` | `1 << 4` |
| `kUnique` | `1 << 5` |
| `kDoesntAffectStealthMeter` | `1 << 6` |
| `kPCLevelMult` | `1 << 7` |
| `kUsesTemplate` | `1 << 8` |
| `kCalcForAllTemplates` | `1 << 9` |
| `kProtected` | `1 << 11` |
| `kNoRumors` | `1 << 13` |
| `kSummonable` | `1 << 14` |
| `kDoesntBleed` | `1 << 16` |
| `kBleedoutOverride` | `1 << 18` |
| `kOppositeGenderAnims` | `1 << 19` |
| `kSimpleActor` | `1 << 20` |
| `kLoopedScript` | `1 << 21` |
| `kNoActivation` | `1 << 23` |
| `kLoopedAudio` | `1 << 28` |
| `kIsGhost` | `1 << 29` |
| `kInvulnerable` | `1 << 31` |

These are NPC/actor-base flags, not the same bitfield as runtime `Actor::BOOL_FLAGS`.

High-impact fields include:
- Female;
- Essential;
- Respawn;
- AutoCalcStats;
- Unique;
- Doesn't Affect Stealth Meter;
- PC Level Mult;
- Uses Template;
- Protected;
- Summonable;
- Doesn't Bleed;
- Opposite Gender Anims;
- Simple Actor;
- No Activation;
- Ghost;
- Invulnerable.

## Actor template-use flags

| Template component | Bit |
|---|---|
| `kNone` | `0` |
| `kTraits` | `1 << 0` |
| `kStats` | `1 << 1` |
| `kFactions` | `1 << 2` |
| `kSpells` | `1 << 3` |
| `kAIData` | `1 << 4` |
| `kAIPackages` | `1 << 5` |
| `kUnused` | `1 << 6` |
| `kBaseData` | `1 << 7` |
| `kInventory` | `1 << 8` |
| `kScript` | `1 << 9` |
| `kAIDefPackList` | `1 << 10` |
| `kAttackData` | `1 << 11` |
| `kKeywords` | `1 << 12` |
| `kCopiedTemplate` | `1 << 15` |

A templated NPC can inherit different categories independently. Therefore a patch must ask **which component is inherited**, not merely whether the NPC “uses a template.”

Important categories include:
- Traits;
- Stats;
- Factions;
- Spells;
- AI Data;
- AI Packages;
- Base Data;
- Inventory;
- Script;
- AI Default Package List;
- Attack Data;
- Keywords.

### Template patch rule

If a template-use bit is enabled, directly editing a corresponding field on the child NPC may not produce the expected runtime result because the effective value comes from its template chain.

## AI aggression

| Enum | Value |
|---|---|
| `kCalmed` | `static_cast<std::underlying_type_t<ACTOR_AGGRESSION>>(-1)` |
| `kUnaggressive` | `0` |
| `kAggressive` | `1` |
| `kVeryAggressive` | `2` |
| `kFrenzied` | `3` |

`Calmed = -1` is a special state alongside the ordinary 0–3 aggression values.

## AI assistance

| Enum | Value |
|---|---|
| `kHelpsNobody` | `0` |
| `kHelpsAllies` | `1` |
| `kHelpsFriends` | `2` |

## AI confidence

| Enum | Value |
|---|---|
| `kCowardly` | `0` |
| `kCautious` | `1` |
| `kAverage` | `2` |
| `kBrave` | `3` |
| `kFoolhardy` | `4` |

## AI mood

| Enum | Value |
|---|---|
| `kNeutral` | `0` |
| `kAngry` | `1` |
| `kFear` | `2` |
| `kHappy` | `3` |
| `kSad` | `4` |
| `kSurprised` | `5` |
| `kPuzzled` | `6` |
| `kDisgusted` | `7` |

## AI morality

| Enum | Value |
|---|---|
| `kAnyCrime` | `0` |
| `kViolenceAgainstEnemy` | `1` |
| `kPropertyCrimeOnly` | `2` |
| `kNoCrime` | `3` |

## AIDT runtime structure

Current CommonLib represents AI data with bit-packed:
- aggression;
- confidence;
- energy level;
- morality;
- mood;
- assistance;
- aggro-radius behavior;
- three aggro radius thresholds;
- No Slow Approach.

The three aggro-radius channels are:
- warn;
- warn and attack;
- attack.

This is separate from CombatStyle and package logic.

## Race size

| Enum | Value |
|---|---|
| `kSmall` | `0` |
| `kMedium` | `1` |
| `kLarge` | `2` |
| `kExtraLarge` | `3` |

## Primary Race flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kPlayable` | `1 << 0` |
| `kFaceGenHead` | `1 << 1` |
| `kChild` | `1 << 2` |
| `kTiltFrontBack` | `1 << 3` |
| `kTiltLeftRight` | `1 << 4` |
| `kNoShadow` | `1 << 5` |
| `kSwims` | `1 << 6` |
| `kFlies` | `1 << 7` |
| `kWalks` | `1 << 8` |
| `kImmobile` | `1 << 9` |
| `kNotPushable` | `1 << 10` |
| `kNoCombatInWater` | `1 << 11` |
| `kNoRotatingToHeadTrack` | `1 << 12` |
| `kDontShowBloodSpray` | `1 << 13` |
| `kDontShowBloodDecal` | `1 << 14` |
| `kUseHeadTrackAnims` | `1 << 15` |
| `kSpellsAlignWithMagicNode` | `1 << 16` |
| `kUseWorldRaycastsForFootIK` | `1 << 17` |
| `kAllowRagdollCollision` | `1 << 18` |
| `kRegenHPInCombat` | `1 << 19` |
| `kCantOpenDoors` | `1 << 20` |
| `kAllowPCDialogue` | `1 << 21` |
| `kNoKnockdowns` | `1 << 22` |
| `kAllowPickpocket` | `1 << 23` |
| `kAlwaysUseProxyController` | `1 << 24` |
| `kDontShowWeaponBlood` | `1 << 25` |
| `kOverlayHeadPartList` | `1 << 26` |
| `kOverrideHeadPartList` | `1 << 27` |
| `kCanPickupItems` | `1 << 28` |
| `kAllowMultipleMembraneShaders` | `1 << 29` |
| `kCanDualWield` | `1 << 30` |
| `kAvoidsRoads` | `1 << 31` |

These govern broad engine behavior such as:
- playable/child status;
- head generation;
- swimming/flying/walking;
- mobility/pushability;
- combat in water;
- head tracking;
- blood visuals;
- Foot IK;
- ragdoll collision;
- in-combat HP regeneration;
- door opening;
- player dialogue;
- knockdowns;
- pickpocketing;
- proxy-controller use;
- head-part list overlay/override;
- item pickup;
- multiple membrane shaders;
- dual wielding;
- road avoidance.

## Secondary Race flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kUseAdvancedAvoidance` | `1 << 0` |
| `kNonHostile` | `1 << 1` |
| `kAllowMountedCombat` | `1 << 4` |

Current secondary flags include advanced avoidance, NonHostile and AllowMountedCombat.

## Race equipment capability flags

| Flag | Bit/value |
|---|---|
| `kNone` | `0` |
| `kHandToHandMelee` | `1 << 0` |
| `kOneHandSword` | `1 << 1` |
| `kOneHandDagger` | `1 << 2` |
| `kOneHandAxe` | `1 << 3` |
| `kOneHandMace` | `1 << 4` |
| `kTwoHandSword` | `1 << 5` |
| `kTwoHandAxe` | `1 << 6` |
| `kBow` | `1 << 7` |
| `kStaff` | `1 << 8` |
| `kSpell` | `1 << 9` |
| `kShield` | `1 << 10` |
| `kTorch` | `1 << 11` |
| `kCrossbow` | `1 << 12` |

These describe what equipment/action families the race supports, including:
- hand-to-hand;
- one/two-handed weapon families;
- bow/crossbow;
- staff;
- spell;
- shield;
- torch.

A race lacking an equipment capability can break an otherwise-valid weapon/equip setup even when the NPC and item records look correct.

## Race tint-layer semantic types

| Tint type | Value |
|---|---|
| `kNone` | `0` |
| `kLipColor` | `1` |
| `kCheekColor` | `2` |
| `kEyeliner` | `3` |
| `kEyeSocketUpper` | `4` |
| `kEyeSocketLower` | `5` |
| `kSkinTone` | `6` |
| `kPaint` | `7` |
| `kLaughLines` | `8` |
| `kCheekColorLower` | `9` |
| `kNose` | `10` |
| `kChin` | `11` |
| `kNeck` | `12` |
| `kForehead` | `13` |
| `kDirt` | `14` |

These distinguish face-tint categories such as lip/cheek/eyeliner/skin tone/paint/laugh lines/nose/chin/neck/forehead/dirt.

## Native Race data fields

Current `RACE_DATA` also carries:
- seven skill boosts;
- male/female height and weight;
- starting Health/Magicka/Stamina;
- base carry weight and mass;
- acceleration/deceleration;
- Biped Object IDs for head/hair/shield/body;
- injured-health threshold;
- regeneration values;
- unarmed damage/reach;
- aiming and flight parameters;
- mount/dismount/camera offsets.

## Compatibility diagnostics

1. **NPC ACBS, AIDT, RACE and runtime Actor state are different layers.**
2. Template inheritance can make the visible child NPC fields misleading if the relevant template-use bit is set.
3. Essential/Protected exist as ActorBase semantics and also appear in runtime Actor flags; check both static source and established-save/runtime state.
4. Race flags can suppress doors, dialogue, pickpocketing, knockdowns, dual wielding or mounted combat independent of packages/scripts.
5. AI aggression/confidence/assistance/morality are not CombatStyle values.
6. Race equipment capability and WEAP animation/equip types are separate compatibility checks.
7. Race head-part/tint semantics affect FaceGen and RaceMenu compatibility but remain distinct from NPC FaceGen assets.
