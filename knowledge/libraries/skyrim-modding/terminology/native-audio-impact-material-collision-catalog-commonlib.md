# Skyrim Native Audio, Impact, Material, and Collision-Layer Catalog — CommonLibSSE-NG

Imported: 2026-09-24
Status: finite reverse-engineered source catalog

## Sources

- `SoundLevels.h` blob `1c24367528ecfc3e3efb4d628dd1c21b7174cfc8`
- `BGSSoundCategory.h` blob `63506bbb7caaf4c523f7b90e75465c09e4ec6e0d`
- `BGSSoundOutput.h` blob `f06a6219e45518c5f9826b3d058f005dd49fc5c9`
- `BGSImpactData.h` blob `481dc4ed15598e644037467ba135012df843e498`
- `ImpactResults.h` blob `91a53e73cc84d4778cad5ea95f3c4a9f95ef4524`
- `MaterialIDs.h` blob `c6eb7de4f20ee3bda871cfa443525af97854055c`
- `CollisionLayers.h` blob `cc6331b49432cffc916da5c10e009f64799ef42e`

Upstream: https://github.com/alandtse/CommonLibSSE-NG

## Sound level

| Enum | Value |
|---|---:|
| `kLoud` | `0` |
| `kNormal` | `1` |
| `kSilent` | `2` |
| `kVeryLoud` | `3` |
| `kQuiet` | `4` |

Sound level is a gameplay/audio metadata enum and is not the same thing as a SoundCategory volume slider or SoundOutput attenuation distance.

## SoundCategory flags

| Flag | Bit |
|---|---|
| `kNone` | `0` |
| `kMuteWhenSubmerged` | `1 << 0` |
| `kShouldAppearOnMenu` | `1 << 1` |

A SoundCategory can also have:
- a parent category;
- attenuation;
- static volume multiplier;
- default menu value;
- runtime volume multiplier;
- runtime frequency multiplier.

This creates a category hierarchy: changing a child sound descriptor is not the same as changing its parent category gain.

## SoundOutput type

| Type | Value |
|---|---:|
| `kUsesHRTF` | `0` |
| `kDefinedSpeakerOutput` | `1` |

## SoundOutput flags

| Flag | Bit |
|---|---|
| `kNone` | `0` |
| `kAttenuatesWithDistance` | `1 << 0` |
| `kAllowsRumble` | `1 << 1` |

A SoundOutput can additionally define:
- reverb send percentage;
- min/max attenuation distance;
- a five-point attenuation curve;
- explicit speaker-channel output/bias.

### HRTF vs speaker output

The output model can use HRTF or a defined speaker-output model. Do not infer 2D/3D behavior solely from the audio file.

## Impact orientation

| Orientation | Value |
|---|---:|
| `kSurfaceNormal` | `0` |
| `kProjVector` | `1` |
| `kProjReflect` | `2` |

## Impact result override

| Result | Value |
|---|---:|
| `kNone` | `0` |
| `kDestroy` | `1` |
| `kBounce` | `2` |
| `kImpale` | `3` |
| `kStick` | `4` |

Impact data also contains:
- effect duration;
- angle threshold;
- placement radius;
- sound level;
- no-decal flag;
- decal texture sets;
- two sound descriptors;
- optional Hazard;
- decal data.

## Havok/physics material IDs

Current CommonLib exposes **89 named Material IDs** in this source snapshot.

| Material | Numeric ID |
|---|---:|
| `kNone` | `0` |
| `kStoneBroken` | `131151687` |
| `kBlockBlade1Hand` | `165778930` |
| `kMeat` | `220124585` |
| `kCarriageWheel` | `322207473` |
| `kMetalLight` | `346811165` |
| `kWoodLight` | `365420259` |
| `kSnow` | `398949039` |
| `kGravel` | `428587608` |
| `kChainMetal` | `438912228` |
| `kBottle` | `493553910` |
| `kWood` | `500811281` |
| `kAsh` | `534864873` |
| `kSkin` | `591247106` |
| `kBlockBlunt` | `593401068` |
| `kDLC1DeerSkin` | `617099282` |
| `kInsect` | `668408902` |
| `kBarrel` | `732141076` |
| `kCeramicMedium` | `781661019` |
| `kBasket` | `790784366` |
| `kIce` | `873356572` |
| `kGlassStairs` | `880200008` |
| `kStoneStairs` | `899511101` |
| `kWater` | `1024582599` |
| `kDraugrSkeleton` | `1028101969` |
| `kBlade1Hand` | `1060167844` |
| `kBook` | `1264672850` |
| `kCarpet` | `1286705471` |
| `kMetalSolid` | `1288358971` |
| `kAxe1Hand` | `1305674443` |
| `kBlockBlade2Hand` | `1312943906` |
| `kOrganicLarge` | `1322093133` |
| `kAmulet` | `1440721808` |
| `kWoodStairs` | `1461712277` |
| `kMud` | `1486385281` |
| `kBoulderSmall` | `1550912982` |
| `kSnowStairs` | `1560365355` |
| `kStoneHeavy` | `1570821952` |
| `kCharacterBumper` | `1574477864` |
| `kTrap` | `1591009235` |
| `kBowsStaves` | `1607128641` |
| `kAlduin` | `1730220269` |
| `kBlockBowsStaves` | `1763418903` |
| `kWoodAsStairs` | `1803571212` |
| `kSteelGreatSword` | `1820198263` |
| `kGrass` | `1848600814` |
| `kBoulderLarge` | `1885326971` |
| `kStoneAsStairs` | `1886078335` |
| `kBlade2Hand` | `2022742644` |
| `kBottleSmall` | `2025794648` |
| `kBoneActor` | `2058949504` |
| `kSand` | `2168343821` |
| `kMetalHeavy` | `2229413539` |
| `kDLC1SabreCatPelt` | `2290050264` |
| `kIceForm` | `2431524493` |
| `kDragon` | `2518321175` |
| `kBlade1HandSmall` | `2617944780` |
| `kSkinSmall` | `2632367422` |
| `kPotsPans` | `2742858142` |
| `kSkinSkeleton` | `2821299363` |
| `kBlunt1Hand` | `2872791301` |
| `kStoneStairsBroken` | `2892392795` |
| `kSkinLarge` | `2965929619` |
| `kOrganic` | `2974920155` |
| `kBone` | `3049421844` |
| `kWoodHeavy` | `3070783559` |
| `kChain` | `3074114406` |
| `kDirt` | `3106094762` |
| `kGhost` | `3312543676` |
| `kSkinMetalLarge` | `3387452107` |
| `kBlockAxe` | `3400476823` |
| `kArmorLight` | `3424720541` |
| `kShieldLight` | `3448167928` |
| `kCoin` | `3589100606` |
| `kBlockBlunt2Hand` | `3662306947` |
| `kShieldHeavy` | `3702389584` |
| `kArmorHeavy` | `3708432437` |
| `kArrow` | `3725505938` |
| `kGlass` | `3739830338` |
| `kStone` | `3741512247` |
| `kWaterPuddle` | `3764646153` |
| `kCloth` | `3839073443` |
| `kSkinMetalSmall` | `3855001958` |
| `kWard` | `3895166727` |
| `kWeb` | `3934839107` |
| `kTrailerSteelSword` | `3941234649` |
| `kBlunt2Hand` | `3969592277` |
| `kDLC1SwingingBridge` | `4239621792` |
| `kBoulderMedium` | `4283869410` |

These are hashed/numeric Havok material identities used by collision/impact/footstep systems. They are **not** FormIDs to MATT records.

### Material diagnostic rule

A visible stone floor can still sound like wood if its actual collision shape/chunk carries the Wood material ID. Texture appearance and physics material are independent.

## Collision layers

Current CommonLib exposes **56 named collision-layer enum entries** including aliases.

| Layer | ID / expression |
|---|---:|
| `kUnidentified` | `0` |
| `kStatic` | `1` |
| `kAnimStatic` | `2` |
| `kTransparent` | `3` |
| `kClutter` | `4` |
| `kWeapon` | `5` |
| `kProjectile` | `6` |
| `kSpell` | `7` |
| `kBiped` | `8` |
| `kTrees` | `9` |
| `kProps` | `10` |
| `kWater` | `11` |
| `kTrigger` | `12` |
| `kTerrain` | `13` |
| `kTrap` | `14` |
| `kNonCollidable` | `15` |
| `kCloudTrap` | `16` |
| `kGround` | `17` |
| `kPortal` | `18` |
| `kDebrisSmall` | `19` |
| `kDebrisLarge` | `20` |
| `kAcousticSpace` | `21` |
| `kActorZone` | `22` |
| `kProjectileZone` | `23` |
| `kGasTrap` | `24` |
| `kShellCasting` | `25` |
| `kTransparentSmall` | `26` |
| `kInvisibleWall` | `27` |
| `kTransparentSmallAnim` | `28` |
| `kWard` | `29` |
| `kCharController` | `30` |
| `kStairHelper` | `31` |
| `kDeadBip` | `32` |
| `kBipedNoCC` | `33` |
| `kAvoidBox` | `34` |
| `kCollisionBox` | `35` |
| `kCameraSphere` | `36` |
| `kDoorDetection` | `37` |
| `kConeProjectile` | `38` |
| `kCameraPick` | `39` |
| `kItemPick` | `40` |
| `kLineOfSight` | `41` |
| `kLOS` | `kLineOfSight` |
| `kPathPick` | `42` |
| `kCustomPick1` | `43` |
| `kCustomPick2` | `44` |
| `kSpellExplosion` | `45` |
| `kDroppingPick` | `46` |
| `kUnused1` | `47` |
| `kUnused2` | `48` |
| `kUnused3` | `49` |
| `kUnused4` | `50` |
| `kUnused5` | `51` |
| `kUnused6` | `52` |
| `kUnused7` | `53` |
| `kInvalid` | `54` |

High-value layers include:
- Static / AnimStatic;
- Clutter;
- Weapon;
- Projectile;
- Spell;
- Biped;
- Water;
- Trigger;
- Terrain;
- Trap;
- NonCollidable;
- Portal;
- AcousticSpace;
- Ward;
- CharController;
- StairHelper;
- InvisibleWall;
- CameraPick / ItemPick / LineOfSight / PathPick;
- SpellExplosion.

`kLOS` aliases `kLineOfSight`.

## Layer vs material

### Collision layer
Answers **what kind of physics/query object is this and what should it collide/query against?**

### Material ID
Answers **what surface/material response should impacts/footsteps/physics use?**

A shape can therefore have the correct collision layer but the wrong material, or vice versa.

## Audio/impact trace

For a wrong impact/footstep sound, trace:

1. visible NIF;
2. actual collision shape/chunk;
3. collision layer;
4. material ID;
5. material/impact mapping;
6. IPDS → IPCT selection;
7. impact SoundDescriptor;
8. SoundCategory;
9. SoundOutput attenuation/reverb;
10. runtime SRD/audio-overhaul changes.

## Diagnostic rules

1. Do not conflate material ID with MATT FormID.
2. Do not conflate SoundLevel with category volume.
3. SoundOutput determines attenuation/spatial/reverb behavior independently of the audio asset itself.
4. Impact orientation/result determines visual/physical response independently of the material's sound choice.
5. Raycast/LOS/item-pick layers explain why an object can physically collide yet be ignored by a particular query.
6. Mesh-only collision fixes can change footsteps/impacts with no ESP conflict.
7. Runtime sound distributors can still change SNDR/EFSH/weapon audio after static load.
