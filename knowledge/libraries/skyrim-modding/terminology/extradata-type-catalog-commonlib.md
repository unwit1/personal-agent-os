# Skyrim ExtraData Type Catalog — CommonLibSSE-NG

Imported: 2026-09-24
Source: `alandtse/CommonLibSSE-NG` branch `ng`
Source file: `include/RE/E/ExtraDataTypes.h`
Source blob SHA: `beb8fe8ec38ea20e99f84cd54bb60b20723bc96c`
Extracted enum slots: 192
Status: reverse-engineered finite native enum

## Why ExtraData matters

A Skyrim base form describes the shared template. **ExtraData** stores per-reference or per-inventory-instance state layered on top of that template.

Examples:
- two swords with the same WEAP base form can differ because one has `ExtraEnchantment`, `ExtraHealth`, `ExtraPoison`, `ExtraCharge`, or `ExtraHotkey`;
- one placed REFR can have ownership, scale, lock, teleport, linked-reference, enable-parent, Havok, map-marker, alias, location, or room/portal state that does not exist on the base object;
- much of this state can be represented in save ChangeForms.

## Complete enum

| Hex | Enum | CommonLib class / note | Source line |
|---|---|---|---:|
| `0X00` | `kNone` | unknown / no class annotation | 174 |
| `0X01` | `kHavok` | ExtraHavok | 175 |
| `0X02` | `kCell3D` | ExtraCell3D | 176 |
| `0X03` | `kCellWaterType` | ExtraCellWaterType | 177 |
| `0X04` | `kRegionList` | ExtraRegionList | 178 |
| `0X05` | `kSeenData` | ExtraSeenData | 179 |
| `0X06` | `kEditorID` | ExtraEditorID | 180 |
| `0X07` | `kCellMusicType` | ExtraCellMusicType | 181 |
| `0X08` | `kCellSkyRegion` | ExtraCellSkyRegion | 182 |
| `0X09` | `kProcessMiddleLow` | ExtraProcessMiddleLow | 183 |
| `0X0A` | `kDetachTime` | ExtraDetachTime | 184 |
| `0X0B` | `kPersistentCell` | ExtraPersistentCell | 185 |
| `0X0C` | `kUnk0C` | unknown / no class annotation | 186 |
| `0X0D` | `kAction` | ExtraAction | 187 |
| `0X0E` | `kStartingPosition` | ExtraStartingPosition | 188 |
| `0X0F` | `kUnk0F` | unknown / no class annotation | 189 |
| `0X10` | `kAnimGraphManager` | ExtraAnimGraphManager | 190 |
| `0X11` | `kBiped` | ExtraBiped | 191 |
| `0X12` | `kUsedMarkers` | ExtraUsedMarkers | 192 |
| `0X13` | `kDistantData` | ExtraDistantData | 193 |
| `0X14` | `kRagDollData` | ExtraRagDollData | 194 |
| `0X15` | `kContainerChanges` | ExtraContainerChanges | 195 |
| `0X16` | `kWorn` | ExtraWorn | 196 |
| `0X17` | `kWornLeft` | ExtraWornLeft | 197 |
| `0X18` | `kPackageStartLocation` | ExtraPackageStartLocation | 198 |
| `0X19` | `kPackage` | ExtraPackage | 199 |
| `0X1A` | `kTresPassPackage` | ExtraTresPassPackage | 200 |
| `0X1B` | `kRunOncePacks` | ExtraRunOncePacks | 201 |
| `0X1C` | `kReferenceHandle` | ExtraReferenceHandle | 202 |
| `0X1D` | `kFollower` | ExtraFollower | 203 |
| `0X1E` | `kLevCreaModifier` | ExtraLevCreaModifier | 204 |
| `0X1F` | `kGhost` | ExtraGhost | 205 |
| `0X20` | `kOriginalReference` | ExtraOriginalReference | 206 |
| `0X21` | `kOwnership` | ExtraOwnership | 207 |
| `0X22` | `kGlobal` | ExtraGlobal | 208 |
| `0X23` | `kRank` | ExtraRank | 209 |
| `0X24` | `kCount` | ExtraCount | 210 |
| `0X25` | `kHealth` | ExtraHealth | 211 |
| `0X26` | `kUnk26` | unknown / no class annotation | 212 |
| `0X27` | `kTimeLeft` | ExtraTimeLeft | 213 |
| `0X28` | `kCharge` | ExtraCharge | 214 |
| `0X29` | `kLight` | ExtraLight | 215 |
| `0X2A` | `kLock` | ExtraLock | 216 |
| `0X2B` | `kTeleport` | ExtraTeleport | 217 |
| `0X2C` | `kMapMarker` | ExtraMapMarker | 218 |
| `0X2D` | `kLeveledCreature` | ExtraLeveledCreature | 219 |
| `0X2E` | `kLeveledItem` | ExtraLeveledItem | 220 |
| `0X2F` | `kScale` | ExtraScale | 221 |
| `0X30` | `kMissingLinkedRefIDs` | ExtraMissingLinkedRefIDs | 222 |
| `0X31` | `kMagicCaster` | ExtraMagicCaster | 223 |
| `0X32` | `kNonActorMagicTarget` | NonActorMagicTarget | 224 |
| `0X33` | `kUnk33` | unknown / no class annotation | 225 |
| `0X34` | `kPlayerCrimeList` | ExtraPlayerCrimeList | 226 |
| `0X35` | `kUnk35` | unknown / no class annotation | 227 |
| `0X36` | `kEnableStateParent` | ExtraEnableStateParent | 228 |
| `0X37` | `kEnableStateChildren` | ExtraEnableStateChildren | 229 |
| `0X38` | `kItemDropper` | ExtraItemDropper | 230 |
| `0X39` | `kDroppedItemList` | ExtraDroppedItemList | 231 |
| `0X3A` | `kRandomTeleportMarker` | ExtraRandomTeleportMarker | 232 |
| `0X3B` | `kUnk3B` | unknown / no class annotation | 233 |
| `0X3C` | `kSavedHavokData` | ExtraSavedHavokData | 234 |
| `0X3D` | `kCannotWear` | ExtraCannotWear | 235 |
| `0X3E` | `kPoison` | ExtraPoison | 236 |
| `0X3F` | `kMagicLight` | ExtraMagicLight | 237 |
| `0X40` | `kLastFinishedSequence` | ExtraLastFinishedSequence | 238 |
| `0X41` | `kSavedAnimation` | ExtraSavedAnimation | 239 |
| `0X42` | `kNorthRotation` | ExtraNorthRotation | 240 |
| `0X43` | `kSpawnContainer` | ExtraSpawnContainer | 241 |
| `0X44` | `kFriendHits` | ExtraFriendHits | 242 |
| `0X45` | `kHeadingTarget` | ExtraHeadingTarget | 243 |
| `0X46` | `kUnk46` | unknown / no class annotation | 244 |
| `0X47` | `kRefractionProperty` | ExtraRefractionProperty | 245 |
| `0X48` | `kStartingWorldOrCell` | ExtraStartingWorldOrCell | 246 |
| `0X49` | `kHotkey` | ExtraHotkey | 247 |
| `0X4A` | `kEditorRef3DData` | ExtraEditorRef3DData | 248 |
| `0X4B` | `kEditorRefMoveData` | ExtraEditorRefMoveData | 249 |
| `0X4C` | `kInfoGeneralTopic` | ExtraInfoGeneralTopic | 250 |
| `0X4D` | `kHasNoRumors` | ExtraHasNoRumors | 251 |
| `0X4E` | `kSound` | ExtraSound | 252 |
| `0X4F` | `kTerminalState` | ExtraTerminalState | 253 |
| `0X50` | `kLinkedRef` | ExtraLinkedRef | 254 |
| `0X51` | `kLinkedRefChildren` | ExtraLinkedRefChildren | 255 |
| `0X52` | `kActivateRef` | ExtraActivateRef | 256 |
| `0X53` | `kActivateRefChildren` | ExtraActivateRefChildren | 257 |
| `0X54` | `kCanTalkToPlayer` | ExtraCanTalkToPlayer | 258 |
| `0X55` | `kObjectHealth` | ExtraObjectHealth | 259 |
| `0X56` | `kCellImageSpace` | ExtraCellImageSpace | 260 |
| `0X57` | `kNavMeshPortal` | ExtraNavMeshPortal | 261 |
| `0X58` | `kModelSwap` | ExtraModelSwap | 262 |
| `0X59` | `kRadius` | ExtraRadius | 263 |
| `0X5A` | `kUnk5A` | unknown / no class annotation | 264 |
| `0X5B` | `kFactionChanges` | ExtraFactionChanges | 265 |
| `0X5C` | `kDismemberedLimbs` | ExtraDismemberedLimbs | 266 |
| `0X5D` | `kActorCause` | ExtraActorCause | 267 |
| `0X5E` | `kMultiBound` | ExtraMultiBound | 268 |
| `0X5F` | `kMultiBoundMarkerData` | MultiBoundMarkerData | 269 |
| `0X60` | `kMultiBoundRef` | ExtraMultiBoundRef | 270 |
| `0X61` | `kReflectedRefs` | ExtraReflectedRefs | 271 |
| `0X62` | `kReflectorRefs` | ExtraReflectorRefs | 272 |
| `0X63` | `kEmittanceSource` | ExtraEmittanceSource | 273 |
| `0X64` | `kUnk64` | unknown / no class annotation | 274 |
| `0X65` | `kCombatStyle` | ExtraCombatStyle | 275 |
| `0X66` | `kUnk66` | unknown / no class annotation | 276 |
| `0X67` | `kPrimitive` | ExtraPrimitive | 277 |
| `0X68` | `kOpenCloseActivateRef` | ExtraOpenCloseActivateRef | 278 |
| `0X69` | `kAnimNoteReceiver` | ExtraAnimNoteReceiver | 279 |
| `0X6A` | `kAmmo` | ExtraAmmo | 280 |
| `0X6B` | `kPatrolRefData` | ExtraPatrolRefData | 281 |
| `0X6C` | `kPackageData` | ExtraPackageData | 282 |
| `0X6D` | `kOcclusionShape` | ExtraOcclusionShape | 283 |
| `0X6E` | `kCollisionData` | ExtraCollisionData | 284 |
| `0X6F` | `kSayTopicInfoOnceADay` | ExtraSayTopicInfoOnceADay | 285 |
| `0X70` | `kEncounterZone` | ExtraEncounterZone | 286 |
| `0X71` | `kSayTopicInfo` | ExtraSayToTopicInfo | 287 |
| `0X72` | `kOcclusionPlaneRefData` | ExtraOcclusionPlaneRefData | 288 |
| `0X73` | `kPortalRefData` | ExtraPortalRefData | 289 |
| `0X74` | `kPortal` | ExtraPortal | 290 |
| `0X75` | `kRoom` | ExtraRoom | 291 |
| `0X76` | `kHealthPerc` | ExtraHealthPerc | 292 |
| `0X77` | `kRoomRefData` | ExtraRoomRefData | 293 |
| `0X78` | `kGuardedRefData` | ExtraGuardedRefData | 294 |
| `0X79` | `kCreatureAwakeSound` | ExtraCreatureAwakeSound | 295 |
| `0X7A` | `kUnk7A` | unknown / no class annotation | 296 |
| `0X7B` | `kHorse` | ExtraHorse | 297 |
| `0X7C` | `kIgnoredBySandbox` | ExtraIgnoredBySandbox | 298 |
| `0X7D` | `kCellAcousticSpace` | ExtraCellAcousticSpace | 299 |
| `0X7E` | `kReservedMarkers` | ExtraReservedMarkers | 300 |
| `0X7F` | `kWeaponIdleSound` | ExtraWeaponIdleSound | 301 |
| `0X80` | `kWaterLightRefs` | ExtraWaterLightRefs | 302 |
| `0X81` | `kLitWaterRefs` | ExtraLitWaterRefs | 303 |
| `0X82` | `kWeaponAttackSound` | ExtraWeaponAttackSound | 304 |
| `0X83` | `kActivateLoopSound` | ExtraActivateLoopSound | 305 |
| `0X84` | `kPatrolRefInUseData` | ExtraPatrolRefInUseData | 306 |
| `0X85` | `kAshPileRef` | ExtraAshPileRef | 307 |
| `0X86` | `kCreatureMovementSound` | ExtraCreatureMovementSound | 308 |
| `0X87` | `kFollowerSwimBreadcrumbs` | ExtraFollowerSwimBreadcrumbs | 309 |
| `0X88` | `kAliasInstanceArray` | ExtraAliasInstanceArray | 310 |
| `0X89` | `kLocation` | ExtraLocation | 311 |
| `0X8A` | `kUnk8A` | unknown / no class annotation | 312 |
| `0X8B` | `kLocationRefType` | ExtraLocationRefType | 313 |
| `0X8C` | `kPromotedRef` | ExtraPromotedRef | 314 |
| `0X8D` | `kAnimationSequencer` | ExtraAnimationSequencer | 315 |
| `0X8E` | `kOutfitItem` | ExtraOutfitItem | 316 |
| `0X8F` | `kUnk8F` | unknown / no class annotation | 317 |
| `0X90` | `kLeveledItemBase` | ExtraLeveledItemBase | 318 |
| `0X91` | `kLightData` | ExtraLightData | 319 |
| `0X92` | `kSceneData` | ExtraSceneData | 320 |
| `0X93` | `kBadPosition` | ExtraBadPosition | 321 |
| `0X94` | `kHeadTrackingWeight` | ExtraHeadTrackingWeight | 322 |
| `0X95` | `kFromAlias` | ExtraFromAlias | 323 |
| `0X96` | `kShouldWear` | ExtraShouldWear | 324 |
| `0X97` | `kFavorCost` | ExtraFavorCost | 325 |
| `0X98` | `kAttachedArrows3D` | ExtraAttachedArrows3D | 326 |
| `0X99` | `kTextDisplayData` | ExtraTextDisplayData | 327 |
| `0X9A` | `kAlphaCutoff` | ExtraAlphaCutoff | 328 |
| `0X9B` | `kEnchantment` | ExtraEnchantment | 329 |
| `0X9C` | `kSoul` | ExtraSoul | 330 |
| `0X9D` | `kForcedTarget` | ExtraForcedTarget | 331 |
| `0X9E` | `kUnk9E` | unknown / no class annotation | 332 |
| `0X9F` | `kUniqueID` | ExtraUniqueID | 333 |
| `0XA0` | `kFlags` | ExtraFlags | 334 |
| `0XA1` | `kRefrPath` | ExtraRefrPath | 335 |
| `0XA2` | `kDecalGroup` | ExtraDecalGroup | 336 |
| `0XA3` | `kLockList` | ExtraLockList | 337 |
| `0XA4` | `kForcedLandingMarker` | ExtraForcedLandingMarker | 338 |
| `0XA5` | `kLargeRefOwnerCells` | ExtraLargeRefOwnerCells | 339 |
| `0XA6` | `kCellWaterEnvMap` | ExtraCellWaterEnvMap | 340 |
| `0XA7` | `kCellGrassData` | ExtraCellGrassData | 341 |
| `0XA8` | `kTeleportName` | ExtraTeleportName | 342 |
| `0XA9` | `kInteraction` | ExtraInteraction | 343 |
| `0XAA` | `kWaterData` | ExtraWaterData | 344 |
| `0XAB` | `kWaterCurrentZoneData` | ExtraWaterCurrentZoneData | 345 |
| `0XAC` | `kAttachRef` | ExtraAttachRef | 346 |
| `0XAD` | `kAttachRefChildren` | ExtraAttachRefChildren | 347 |
| `0XAE` | `kGroupConstraint` | ExtraGroupConstraint | 348 |
| `0XAF` | `kScriptedAnimDependence` | ExtraScriptedAnimDependence | 349 |
| `0XB0` | `kCachedScale` | ExtraCachedScale | 350 |
| `0XB1` | `kRaceData` | ExtraRaceData | 351 |
| `0XB2` | `kGIDBuffer` | ExtraGIDBuffer | 352 |
| `0XB3` | `kMissingRefIDs` | ExtraMissingRefIDs | 353 |
| `0XB4` | `kUnkB4` | unknown / no class annotation | 354 |
| `0XB5` | `kResourcesPreload` | ExtraResourcesPreload | 355 |
| `0XB6` | `kUnkB6` | unknown / no class annotation | 356 |
| `0XB7` | `kUnkB7` | unknown / no class annotation | 357 |
| `0XB8` | `kUnkB8` | unknown / no class annotation | 358 |
| `0XB9` | `kUnkB9` | unknown / no class annotation | 359 |
| `0XBA` | `kUnkBA` | unknown / no class annotation | 360 |
| `0XBB` | `kUnkBB` | unknown / no class annotation | 361 |
| `0XBC` | `kUnkBC` | unknown / no class annotation | 362 |
| `0XBD` | `kUnkBD` | unknown / no class annotation | 363 |
| `0XBE` | `kUnkBE` | unknown / no class annotation | 364 |
| `0XBF` | `kUnkBF` | unknown / no class annotation | 365 |

## High-value inventory-instance ExtraData

### ExtraCount
Stack count.

### ExtraHealth
Item condition/tempering-style health value used by weapon/armor instances.

### ExtraCharge
Current enchantment charge.

### ExtraEnchantment
Instance-specific enchantment data.

### ExtraPoison
Poison applied to weapon instance.

### ExtraSoul
Soul stored in soul-gem instance.

### ExtraHotkey
Favorites/hotkey assignment.

### ExtraWorn / ExtraWornLeft
Equipment-state markers.

### ExtraCannotWear / ExtraShouldWear
Instance/equipment behavior markers.

### ExtraTextDisplayData
Custom/generated display-name text data used by item naming systems.

### ExtraUniqueID
Per-instance unique identifier used by inventory/reference systems.

### ExtraFlags
Additional instance flags.

## High-value reference/world ExtraData

### ExtraOwnership
Reference ownership.

### ExtraRank
Ownership/faction rank context.

### ExtraLock
Lock data.

### ExtraTeleport
Door teleport destination.

### ExtraMapMarker
Map-marker state.

### ExtraScale / ExtraCachedScale
Reference scaling.

### ExtraLinkedRef / ExtraLinkedRefChildren
Linked-reference graph.

### ExtraEnableStateParent / ExtraEnableStateChildren
Enable-parent graph.

### ExtraLocation / ExtraLocationRefType
Location membership/reference role.

### ExtraEncounterZone
Encounter-zone association.

### ExtraPersistentCell
Persistent cell linkage.

### ExtraStartingPosition / ExtraStartingWorldOrCell
Original/start placement context.

### ExtraNorthRotation
Interior/world orientation data.

### ExtraHavok / ExtraSavedHavokData
Physics state.

### ExtraCollisionData
Instance collision metadata.

### ExtraRoom / ExtraRoomRefData / ExtraPortal / ExtraPortalRefData
Interior optimization/runtime room-portal data.

### ExtraMultiBound / ExtraMultiBoundRef
Optimization bounds.

## Actor/AI ExtraData

Examples include:
- `ExtraPackage`;
- `ExtraPackageData`;
- `ExtraPackageStartLocation`;
- `ExtraRunOncePacks`;
- `ExtraFollower`;
- `ExtraFactionChanges`;
- `ExtraCombatStyle`;
- `ExtraActorCause`;
- `ExtraHorse`;
- `ExtraForcedTarget`;
- `ExtraForcedLandingMarker`;
- `ExtraHeadTrackingWeight`;
- `ExtraIgnoredBySandbox`.

## Quest/alias/dialogue ExtraData

Examples:
- `ExtraAliasInstanceArray`;
- `ExtraFromAlias`;
- `ExtraInfoGeneralTopic`;
- `ExtraSayTopicInfo`;
- `ExtraSayTopicInfoOnceADay`;
- `ExtraSceneData`.

## Cell/environment ExtraData

Examples:
- `ExtraCellWaterType`;
- `ExtraCellMusicType`;
- `ExtraCellSkyRegion`;
- `ExtraCellImageSpace`;
- `ExtraCellAcousticSpace`;
- `ExtraCellWaterEnvMap`;
- `ExtraCellGrassData`;
- `ExtraWaterData`;
- `ExtraWaterCurrentZoneData`;
- `ExtraEmittanceSource`;
- `ExtraLightData`.

## Unknown slots

CommonLib deliberately leaves several IDs as `kUnkXX`. These are part of the enum range but do not have a confidently named semantic class in this source snapshot.

Preserve those unknowns. Do not fill them with wiki guesses unless source/runtime testing corroborates them.

## Diagnostic rules

1. **Base form equality does not imply instance equality.** Compare ExtraData when only one stack/reference misbehaves.
2. Tempering, custom enchantments, poison, charge, soul and custom names are usually **instance state**, not changes to the base ARMO/WEAP/SLGM form.
3. xEdit primarily shows plugin/base reference data; live inventory ExtraData may only exist in memory/save state.
4. ReSaver/ESS diagnostics can expose related ChangeForm state, but ExtraData enum identity and save representation are not always one-to-one.
5. Removing an item and re-adding its base form can appear to “fix” an issue because it creates a fresh instance without the old ExtraData—not because the base plugin was repaired.
6. Native plugins should use typed ExtraData accessors/classes rather than assuming byte layouts from an old runtime.
7. Unknown ExtraData IDs must remain version-scoped reverse-engineering gaps.

## Related modules

- `ess-changeforms-savegame-internals.md`
- `object-reference-lifecycle-interactions.md`
- `plugin-record-schema-items-magic.md`
- `crime-ownership-merchants-economy.md`
- `havok-collision-rigidbody-authoring.md`
