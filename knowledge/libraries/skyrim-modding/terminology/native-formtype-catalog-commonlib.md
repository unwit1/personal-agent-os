# Skyrim Native FormType Catalog — CommonLibSSE-NG

Imported: 2026-09-24
Source: `alandtse/CommonLibSSE-NG` branch `ng`
Source file: `include/RE/F/FormTypes.h`
Source blob SHA: `2a20a595a556815ccda8585a40c3212934e148c9`
Extracted FormTypes: 138
Status: reverse-engineered finite native enum

## Catalog

| ID | Hex | Native enum | Plugin/runtime signature | CommonLib class/note | Source line |
|---:|---:|---|---|---|---:|
| 0 | `0x00` | `None` | `NONE` | TESForm | 140 |
| 1 | `0x01` | `PluginInfo` | `TES4` | — | 141 |
| 2 | `0x02` | `FormGroup` | `GRUP` | — | 142 |
| 3 | `0x03` | `GameSetting` | `GMST` | — | 143 |
| 4 | `0x04` | `Keyword` | `KYWD` | BGSKeyword | 144 |
| 5 | `0x05` | `LocationRefType` | `LCRT` | BGSLocationRefType | 145 |
| 6 | `0x06` | `Action` | `AACT` | BGSAction | 146 |
| 7 | `0x07` | `TextureSet` | `TXST` | BGSTextureSet | 147 |
| 8 | `0x08` | `MenuIcon` | `MICN` | BGSMenuIcon | 148 |
| 9 | `0x09` | `Global` | `GLOB` | TESGlobal | 149 |
| 10 | `0x0A` | `Class` | `CLAS` | TESClass | 150 |
| 11 | `0x0B` | `Faction` | `FACT` | TESFaction | 151 |
| 12 | `0x0C` | `HeadPart` | `HDPT` | BGSHeadPart | 152 |
| 13 | `0x0D` | `Eyes` | `EYES` | TESEyes | 153 |
| 14 | `0x0E` | `Race` | `RACE` | TESRace | 154 |
| 15 | `0x0F` | `Sound` | `SOUN` | TESSound | 155 |
| 16 | `0x10` | `AcousticSpace` | `ASPC` | BGSAcousticSpace | 156 |
| 17 | `0x11` | `Skill` | `SKIL` | — | 157 |
| 18 | `0x12` | `MagicEffect` | `MGEF` | EffectSetting | 158 |
| 19 | `0x13` | `Script` | `SCPT` | Script | 159 |
| 20 | `0x14` | `LandTexture` | `LTEX` | TESLandTexture | 160 |
| 21 | `0x15` | `Enchantment` | `ENCH` | EnchantmentItem | 161 |
| 22 | `0x16` | `Spell` | `SPEL` | SpellItem | 162 |
| 23 | `0x17` | `Scroll` | `SCRL` | ScrollItem | 163 |
| 24 | `0x18` | `Activator` | `ACTI` | TESObjectACTI | 164 |
| 25 | `0x19` | `TalkingActivator` | `TACT` | BGSTalkingActivator | 165 |
| 26 | `0x1A` | `Armor` | `ARMO` | TESObjectARMO | 166 |
| 27 | `0x1B` | `Book` | `BOOK` | TESObjectBOOK | 167 |
| 28 | `0x1C` | `Container` | `CONT` | TESObjectCONT | 168 |
| 29 | `0x1D` | `Door` | `DOOR` | TESObjectDOOR | 169 |
| 30 | `0x1E` | `Ingredient` | `INGR` | IngredientItem | 170 |
| 31 | `0x1F` | `Light` | `LIGH` | TESObjectLIGH | 171 |
| 32 | `0x20` | `Misc` | `MISC` | TESObjectMISC | 172 |
| 33 | `0x21` | `Apparatus` | `APPA` | BGSApparatus | 173 |
| 34 | `0x22` | `Static` | `STAT` | TESObjectSTAT | 174 |
| 35 | `0x23` | `StaticCollection` | `SCOL` | BGSStaticCollection | 175 |
| 36 | `0x24` | `MovableStatic` | `MSTT` | BGSMovableStatic | 176 |
| 37 | `0x25` | `Grass` | `GRAS` | TESGrass | 177 |
| 38 | `0x26` | `Tree` | `TREE` | TESObjectTREE | 178 |
| 39 | `0x27` | `Flora` | `FLOR` | TESFlora | 179 |
| 40 | `0x28` | `Furniture` | `FURN` | TESFurniture | 180 |
| 41 | `0x29` | `Weapon` | `WEAP` | TESObjectWEAP | 181 |
| 42 | `0x2A` | `Ammo` | `AMMO` | TESAmmo | 182 |
| 43 | `0x2B` | `NPC` | `NPC_` | TESNPC | 183 |
| 44 | `0x2C` | `LeveledNPC` | `LVLN` | TESLevCharacter | 184 |
| 45 | `0x2D` | `KeyMaster` | `KEYM` | TESKey | 185 |
| 46 | `0x2E` | `AlchemyItem` | `ALCH` | AlchemyItem | 186 |
| 47 | `0x2F` | `IdleMarker` | `IDLM` | BGSIdleMarker | 187 |
| 48 | `0x30` | `Note` | `NOTE` | BGSNote | 188 |
| 49 | `0x31` | `ConstructibleObject` | `COBJ` | BGSConstructibleObject | 189 |
| 50 | `0x32` | `Projectile` | `PROJ` | BGSProjectile | 190 |
| 51 | `0x33` | `Hazard` | `HAZD` | BGSHazard | 191 |
| 52 | `0x34` | `SoulGem` | `SLGM` | TESSoulGem | 192 |
| 53 | `0x35` | `LeveledItem` | `LVLI` | TESLevItem | 193 |
| 54 | `0x36` | `Weather` | `WTHR` | TESWeather | 194 |
| 55 | `0x37` | `Climate` | `CLMT` | TESClimate | 195 |
| 56 | `0x38` | `ShaderParticleGeometryData` | `SPGD` | BGSShaderParticleGeometryData | 196 |
| 57 | `0x39` | `ReferenceEffect` | `RFCT` | BGSReferenceEffect | 197 |
| 58 | `0x3A` | `Region` | `REGN` | TESRegion | 198 |
| 59 | `0x3B` | `Navigation` | `NAVI` | NavMeshInfoMap | 199 |
| 60 | `0x3C` | `Cell` | `CELL` | TESObjectCELL | 200 |
| 61 | `0x3D` | `Reference` | `REFR` | TESObjectREFR | 201 |
| 62 | `0x3E` | `ActorCharacter` | `ACHR` | Actor / Character / PlayerCharacter | 202 |
| 63 | `0x3F` | `ProjectileMissile` | `PMIS` | MissileProjectile | 203 |
| 64 | `0x40` | `ProjectileArrow` | `PARW` | ArrowProjectile | 204 |
| 65 | `0x41` | `ProjectileGrenade` | `PGRE` | GrenadeProjectile | 205 |
| 66 | `0x42` | `ProjectileBeam` | `PBEA` | BeamProjectile | 206 |
| 67 | `0x43` | `ProjectileFlame` | `PFLA` | FlameProjectile | 207 |
| 68 | `0x44` | `ProjectileCone` | `PCON` | ConeProjectile | 208 |
| 69 | `0x45` | `ProjectileBarrier` | `PBAR` | BarrierProjectile | 209 |
| 70 | `0x46` | `PlacedHazard` | `PHZD` | Hazard | 210 |
| 71 | `0x47` | `WorldSpace` | `WRLD` | TESWorldSpace | 211 |
| 72 | `0x48` | `Land` | `LAND` | TESObjectLAND | 212 |
| 73 | `0x49` | `NavMesh` | `NAVM` | NavMesh | 213 |
| 74 | `0x4A` | `TLOD` | `TLOD` | — | 214 |
| 75 | `0x4B` | `Dialogue` | `DIAL` | TESTopic | 215 |
| 76 | `0x4C` | `Info` | `INFO` | TESTopicInfo | 216 |
| 77 | `0x4D` | `Quest` | `QUST` | TESQuest | 217 |
| 78 | `0x4E` | `Idle` | `IDLE` | TESIdleForm | 218 |
| 79 | `0x4F` | `Package` | `PACK` | TESPackage / DialoguePackage | 219 |
| 80 | `0x50` | `CombatStyle` | `CSTY` | TESCombatStyle | 220 |
| 81 | `0x51` | `LoadScreen` | `LSCR` | TESLoadScreen | 221 |
| 82 | `0x52` | `LeveledSpell` | `LVSP` | TESLevSpell | 222 |
| 83 | `0x53` | `AnimatedObject` | `ANIO` | TESObjectANIO | 223 |
| 84 | `0x54` | `Water` | `WATR` | TESWaterForm | 224 |
| 85 | `0x55` | `EffectShader` | `EFSH` | TESEffectShader | 225 |
| 86 | `0x56` | `TOFT` | `TOFT` | — | 226 |
| 87 | `0x57` | `Explosion` | `EXPL` | BGSExplosion | 227 |
| 88 | `0x58` | `Debris` | `DEBR` | BGSDebris | 228 |
| 89 | `0x59` | `ImageSpace` | `IMGS` | TESImageSpace | 229 |
| 90 | `0x5A` | `ImageAdapter` | `IMAD` | TESImageSpaceModifier | 230 |
| 91 | `0x5B` | `FormList` | `FLST` | BGSListForm | 231 |
| 92 | `0x5C` | `Perk` | `PERK` | BGSPerk | 232 |
| 93 | `0x5D` | `BodyPartData` | `BPTD` | BGSBodyPartData | 233 |
| 94 | `0x5E` | `AddonNode` | `ADDN` | BGSAddonNode | 234 |
| 95 | `0x5F` | `ActorValueInfo` | `AVIF` | ActorValueInfo | 235 |
| 96 | `0x60` | `CameraShot` | `CAMS` | BGSCameraShot | 236 |
| 97 | `0x61` | `CameraPath` | `CPTH` | BGSCameraPath | 237 |
| 98 | `0x62` | `VoiceType` | `VTYP` | BGSVoiceType | 238 |
| 99 | `0x63` | `MaterialType` | `MATT` | BGSMaterialType | 239 |
| 100 | `0x64` | `Impact` | `IPCT` | BGSImpactData | 240 |
| 101 | `0x65` | `ImpactDataSet` | `IPDS` | BGSImpactDataSet | 241 |
| 102 | `0x66` | `Armature` | `ARMA` | TESObjectARMA | 242 |
| 103 | `0x67` | `EncounterZone` | `ECZN` | BGSEncounterZone | 243 |
| 104 | `0x68` | `Location` | `LCTN` | BGSLocation | 244 |
| 105 | `0x69` | `Message` | `MESG` | BGSMessage | 245 |
| 106 | `0x6A` | `Ragdoll` | `RGDL` | BGSRagdoll | 246 |
| 107 | `0x6B` | `DefaultObject` | `DOBJ` | BGSDefaultObjectManager | 247 |
| 108 | `0x6C` | `LightingMaster` | `LGTM` | BGSLightingTemplate | 248 |
| 109 | `0x6D` | `MusicType` | `MUSC` | BGSMusicType | 249 |
| 110 | `0x6E` | `Footstep` | `FSTP` | BGSFootstep | 250 |
| 111 | `0x6F` | `FootstepSet` | `FSTS` | BGSFootstepSet | 251 |
| 112 | `0x70` | `StoryManagerBranchNode` | `SMBN` | BGSStoryManagerBranchNode | 252 |
| 113 | `0x71` | `StoryManagerQuestNode` | `SMQN` | BGSStoryManagerQuestNode | 253 |
| 114 | `0x72` | `StoryManagerEventNode` | `SMEN` | BGSStoryManagerEventNode | 254 |
| 115 | `0x73` | `DialogueBranch` | `DLBR` | BGSDialogueBranch | 255 |
| 116 | `0x74` | `MusicTrack` | `MUST` | BGSMusicTrackFormWrapper | 256 |
| 117 | `0x75` | `DialogueView` | `DLVW` | — | 257 |
| 118 | `0x76` | `WordOfPower` | `WOOP` | TESWordOfPower | 258 |
| 119 | `0x77` | `Shout` | `SHOU` | TESShout | 259 |
| 120 | `0x78` | `EquipSlot` | `EQUP` | BGSEquipSlot | 260 |
| 121 | `0x79` | `Relationship` | `RELA` | BGSRelationship | 261 |
| 122 | `0x7A` | `Scene` | `SCEN` | BGSScene | 262 |
| 123 | `0x7B` | `AssociationType` | `ASTP` | BGSAssociationType | 263 |
| 124 | `0x7C` | `Outfit` | `OTFT` | BGSOutfit | 264 |
| 125 | `0x7D` | `ArtObject` | `ARTO` | BGSArtObject | 265 |
| 126 | `0x7E` | `MaterialObject` | `MATO` | BGSMaterialObject | 266 |
| 127 | `0x7F` | `MovementType` | `MOVT` | BGSMovementType | 267 |
| 128 | `0x80` | `SoundRecord` | `SNDR` | BGSSoundDescriptorForm | 268 |
| 129 | `0x81` | `DualCastData` | `DUAL` | BGSDualCastData | 269 |
| 130 | `0x82` | `SoundCategory` | `SNCT` | BGSSoundCategory | 270 |
| 131 | `0x83` | `SoundOutputModel` | `SOPM` | BGSSoundOutput | 271 |
| 132 | `0x84` | `CollisionLayer` | `COLL` | BGSCollisionLayer | 272 |
| 133 | `0x85` | `ColorForm` | `CLFM` | BGSColorForm | 273 |
| 134 | `0x86` | `ReverbParam` | `REVB` | BGSReverbParameters | 274 |
| 135 | `0x87` | `LensFlare` | `LENS` | BGSLensFlare | 275 |
| 136 | `0x88` | `LensSprite` | `LSPR` | — | 276 |
| 137 | `0x89` | `VolumetricLighting` | `VOLI` | BGSVolumetricLighting | 277 |

## Boundary

CommonLib defines `Max` immediately after `VolumetricLighting`; in this source snapshot `Max = 0x8A`, so valid cataloged values are 0x00–0x89.

## Why this is not identical to the xEdit record-signature catalog

The native enum mixes several categories:

### Top-level plugin record types
Examples: `NPC_`, `MGEF`, `CELL`, `PERK`, `ARMO`.

### File/container/meta types
Examples:
- `PluginInfo` / TES4;
- `FormGroup` / GRUP.

### Runtime placed-reference types
Examples:
- `REFR`;
- `ACHR`;
- projectile runtime forms such as `PMIS`, `PARW`, `PGRE`, `PBEA`, `PFLA`, `PCON`, `PBAR`;
- `PHZD`.

### Legacy/rare/internal enum slots
Examples include entries such as `SKIL`, `NOTE`, `TLOD`, `TOFT`, `LSPR` that may not appear as ordinary supported Skyrim top-level records in the same way as the main xEdit `wbRecord` catalog.

Therefore, **native FormType ID**, **plugin top-level signature**, and **runtime class** are related but not interchangeable concepts.

## Diagnostic use

### Crash logs
A native crash may identify an object by `FormType` or class rather than xEdit signature. This table bridges the two.

### Papyrus / SKSE
Functions that return a numeric form type can be mapped to this native vocabulary, but verify the exact API's numbering/translation rather than assuming every interface exposes raw `RE::FormType`.

### Runtime references
A placed Actor can have runtime FormType `ActorCharacter / ACHR` while its base is an `NPC_ / TESNPC`.

### Projectiles
The base `PROJ` record defines projectile behavior, while live missiles/arrows/etc. use specialized runtime form classes/types.

## Related catalogs

- `plugin-record-signature-catalog-xedit.md` — top-level xEdit record definitions.
- `extradata-type-catalog-commonlib.md` — per-instance ExtraData.
- `condition-function-catalog-xedit.md` — CTDA function indices.
- `actorvalue-catalog-xedit.md` — ActorValue enum.
