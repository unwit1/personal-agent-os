# SKSE64 Modified Papyrus API — Shard 4

Imported: 2026-09-24
Source: `ianpatt/skse64` master
Scripts: 8 · declarations: 255
Status: generated source-derived API shard

## FormType

Source: `scripts/modified/FormType.psc` · blob `a59985c5e8db2224e49b3f262009290a79200dda`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| property | `kNone` | `int Property kNone = 0 AutoReadOnly` | 3 |
| property | `kTES4` | `int Property kTES4 = 1 AutoReadOnly` | 4 |
| property | `kGroup` | `int Property kGroup = 2 AutoReadOnly` | 5 |
| property | `kGMST` | `int Property kGMST = 3 AutoReadOnly` | 6 |
| property | `kKeyword` | `int Property kKeyword = 4 AutoReadOnly` | 7 |
| property | `kLocationRef` | `int Property kLocationRef = 5 AutoReadOnly` | 8 |
| property | `kAction` | `int Property kAction = 6 AutoReadOnly` | 9 |
| property | `kTextureSet` | `int Property kTextureSet = 7 AutoReadOnly` | 10 |
| property | `kMenuIcon` | `int Property kMenuIcon = 8 AutoReadOnly` | 11 |
| property | `kGlobal` | `int Property kGlobal = 9 AutoReadOnly` | 12 |
| property | `kClass` | `int Property kClass = 10 AutoReadOnly` | 13 |
| property | `kFaction` | `int Property kFaction = 11 AutoReadOnly` | 14 |
| property | `kHeadPart` | `int Property kHeadPart = 12 AutoReadOnly` | 15 |
| property | `kEyes` | `int Property kEyes = 13 AutoReadOnly` | 16 |
| property | `kRace` | `int Property kRace = 14 AutoReadOnly` | 17 |
| property | `kSound` | `int Property kSound = 15 AutoReadOnly` | 18 |
| property | `kAcousticSpace` | `int Property kAcousticSpace = 16 AutoReadOnly` | 19 |
| property | `kSkill` | `int Property kSkill = 17 AutoReadOnly` | 20 |
| property | `kEffectSetting` | `int Property kEffectSetting = 18 AutoReadOnly` | 21 |
| property | `kScript` | `int Property kScript = 19 AutoReadOnly` | 22 |
| property | `kLandTexture` | `int Property kLandTexture = 20 AutoReadOnly` | 23 |
| property | `kEnchantment` | `int Property kEnchantment = 21 AutoReadOnly` | 24 |
| property | `kSpell` | `int Property kSpell = 22 AutoReadOnly` | 25 |
| property | `kScrollItem` | `int Property kScrollItem = 23 AutoReadOnly` | 26 |
| property | `kActivator` | `int Property kActivator = 24 AutoReadOnly` | 27 |
| property | `kTalkingActivator` | `int Property kTalkingActivator = 25 AutoReadOnly` | 28 |
| property | `kArmor` | `int Property kArmor = 26 AutoReadOnly` | 29 |
| property | `kBook` | `int Property kBook = 27 AutoReadOnly` | 30 |
| property | `kContainer` | `int Property kContainer = 28 AutoReadOnly` | 31 |
| property | `kDoor` | `int Property kDoor = 29 AutoReadOnly` | 32 |
| property | `kIngredient` | `int Property kIngredient = 30 AutoReadOnly` | 33 |
| property | `kLight` | `int Property kLight = 31 AutoReadOnly` | 34 |
| property | `kMisc` | `int Property kMisc = 32 AutoReadOnly` | 35 |
| property | `kApparatus` | `int Property kApparatus = 33 AutoReadOnly` | 36 |
| property | `kStatic` | `int Property kStatic = 34 AutoReadOnly` | 37 |
| property | `kStaticCollection` | `int Property kStaticCollection = 35 AutoReadOnly` | 38 |
| property | `kMovableStatic` | `int Property kMovableStatic = 36 AutoReadOnly` | 39 |
| property | `kGrass` | `int Property kGrass = 37 AutoReadOnly` | 40 |
| property | `kTree` | `int Property kTree = 38 AutoReadOnly` | 41 |
| property | `kFlora` | `int Property kFlora = 39 AutoReadOnly` | 42 |
| property | `kFurniture` | `int Property kFurniture = 40 AutoReadOnly` | 43 |
| property | `kWeapon` | `int Property kWeapon = 41 AutoReadOnly` | 44 |
| property | `kAmmo` | `int Property kAmmo = 42 AutoReadOnly` | 45 |
| property | `kNPC` | `int Property kNPC = 43 AutoReadOnly` | 46 |
| property | `kLeveledCharacter` | `int Property kLeveledCharacter = 44 AutoReadOnly` | 47 |
| property | `kKey` | `int Property kKey = 45 AutoReadOnly` | 48 |
| property | `kPotion` | `int Property kPotion = 46 AutoReadOnly` | 49 |
| property | `kIdleMarker` | `int Property kIdleMarker = 47 AutoReadOnly` | 50 |
| property | `kNote` | `int Property kNote = 48 AutoReadOnly` | 51 |
| property | `kConstructibleObject` | `int Property kConstructibleObject = 49 AutoReadOnly` | 52 |
| property | `kProjectile` | `int Property kProjectile = 50 AutoReadOnly` | 53 |
| property | `kHazard` | `int Property kHazard = 51 AutoReadOnly` | 54 |
| property | `kSoulGem` | `int Property kSoulGem = 52 AutoReadOnly` | 55 |
| property | `kLeveledItem` | `int Property kLeveledItem = 53 AutoReadOnly` | 56 |
| property | `kWeather` | `int Property kWeather = 54 AutoReadOnly` | 57 |
| property | `kClimate` | `int Property kClimate = 55 AutoReadOnly` | 58 |
| property | `kShaderParticleGeometryData` | `int Property kShaderParticleGeometryData = 56 AutoReadOnly` | 59 |
| property | `kReferenceEffect` | `int Property kReferenceEffect = 57 AutoReadOnly` | 60 |
| property | `kRegion` | `int Property kRegion = 58 AutoReadOnly` | 61 |
| property | `kNAVI` | `int Property kNAVI = 59 AutoReadOnly` | 62 |
| property | `kCell` | `int Property kCell = 60 AutoReadOnly` | 63 |
| property | `kReference` | `int Property kReference = 61 AutoReadOnly` | 64 |
| property | `kCharacter` | `int Property kCharacter = 62 AutoReadOnly` | 65 |
| property | `kMissile` | `int Property kMissile = 63 AutoReadOnly` | 66 |
| property | `kArrow` | `int Property kArrow = 64 AutoReadOnly` | 67 |
| property | `kGrenade` | `int Property kGrenade = 65 AutoReadOnly` | 68 |
| property | `kBeamProjectile` | `int Property kBeamProjectile = 66 AutoReadOnly` | 69 |
| property | `kFlameProjectile` | `int Property kFlameProjectile = 67 AutoReadOnly` | 70 |
| property | `kConeProjectile` | `int Property kConeProjectile = 68 AutoReadOnly` | 71 |
| property | `kBarrierProjectile` | `int Property kBarrierProjectile = 69 AutoReadOnly` | 72 |
| property | `kPHZD` | `int Property kPHZD = 70 AutoReadOnly` | 73 |
| property | `kWorldSpace` | `int Property kWorldSpace = 71 AutoReadOnly` | 74 |
| property | `kLand` | `int Property kLand = 72 AutoReadOnly` | 75 |
| property | `kNavMesh` | `int Property kNavMesh = 73 AutoReadOnly` | 76 |
| property | `kTLOD` | `int Property kTLOD = 74 AutoReadOnly` | 77 |
| property | `kTopic` | `int Property kTopic = 75 AutoReadOnly` | 78 |
| property | `kTopicInfo` | `int Property kTopicInfo = 76 AutoReadOnly` | 79 |
| property | `kQuest` | `int Property kQuest = 77 AutoReadOnly` | 80 |
| property | `kIdle` | `int Property kIdle = 78 AutoReadOnly` | 81 |
| property | `kPackage` | `int Property kPackage = 79 AutoReadOnly` | 82 |
| property | `kCombatStyle` | `int Property kCombatStyle = 80 AutoReadOnly` | 83 |
| property | `kLoadScreen` | `int Property kLoadScreen = 81 AutoReadOnly` | 84 |
| property | `kLeveledSpell` | `int Property kLeveledSpell = 82 AutoReadOnly` | 85 |
| property | `kANIO` | `int Property kANIO = 83 AutoReadOnly` | 86 |
| property | `kWater` | `int Property kWater = 84 AutoReadOnly` | 87 |
| property | `kEffectShader` | `int Property kEffectShader = 85 AutoReadOnly` | 88 |
| property | `kTOFT` | `int Property kTOFT = 86 AutoReadOnly` | 89 |
| property | `kExplosion` | `int Property kExplosion = 87 AutoReadOnly` | 90 |
| property | `kDebris` | `int Property kDebris = 88 AutoReadOnly` | 91 |
| property | `kImageSpace` | `int Property kImageSpace = 89 AutoReadOnly` | 92 |
| property | `kImageSpaceModifier` | `int Property kImageSpaceModifier = 90 AutoReadOnly` | 93 |
| property | `kList` | `int Property kList = 91 AutoReadOnly` | 94 |
| property | `kPerk` | `int Property kPerk = 92 AutoReadOnly` | 95 |
| property | `kBodyPartData` | `int Property kBodyPartData = 93 AutoReadOnly` | 96 |
| property | `kAddonNode` | `int Property kAddonNode = 94 AutoReadOnly` | 97 |
| property | `kActorValueInfo` | `int Property kActorValueInfo = 95 AutoReadOnly` | 98 |
| property | `kCameraShot` | `int Property kCameraShot = 96 AutoReadOnly` | 99 |
| property | `kCameraPath` | `int Property kCameraPath = 97 AutoReadOnly` | 100 |
| property | `kVoiceType` | `int Property kVoiceType = 98 AutoReadOnly` | 101 |
| property | `kMaterialType` | `int Property kMaterialType = 99 AutoReadOnly` | 102 |
| property | `kImpactData` | `int Property kImpactData = 100 AutoReadOnly` | 103 |
| property | `kImpactDataSet` | `int Property kImpactDataSet = 101 AutoReadOnly` | 104 |
| property | `kARMA` | `int Property kARMA = 102 AutoReadOnly` | 105 |
| property | `kEncounterZone` | `int Property kEncounterZone = 103 AutoReadOnly` | 106 |
| property | `kLocation` | `int Property kLocation = 104 AutoReadOnly` | 107 |
| property | `kMessage` | `int Property kMessage = 105 AutoReadOnly` | 108 |
| property | `kRagdoll` | `int Property kRagdoll = 106 AutoReadOnly` | 109 |
| property | `kDefaultObject` | `int Property kDefaultObject = 107 AutoReadOnly` | 110 |
| property | `kLightingTemplate` | `int Property kLightingTemplate = 108 AutoReadOnly` | 111 |
| property | `kMusicType` | `int Property kMusicType = 109 AutoReadOnly` | 112 |
| property | `kFootstep` | `int Property kFootstep = 110 AutoReadOnly` | 113 |
| property | `kFootstepSet` | `int Property kFootstepSet = 111 AutoReadOnly` | 114 |
| property | `kStoryBranchNode` | `int Property kStoryBranchNode = 112 AutoReadOnly` | 115 |
| property | `kStoryQuestNode` | `int Property kStoryQuestNode = 113 AutoReadOnly` | 116 |
| property | `kStoryEventNode` | `int Property kStoryEventNode = 114 AutoReadOnly` | 117 |
| property | `kDialogueBranch` | `int Property kDialogueBranch = 115 AutoReadOnly` | 118 |
| property | `kMusicTrack` | `int Property kMusicTrack = 116 AutoReadOnly` | 119 |
| property | `kDLVW` | `int Property kDLVW = 117 AutoReadOnly` | 120 |
| property | `kWordOfPower` | `int Property kWordOfPower = 118 AutoReadOnly` | 121 |
| property | `kShout` | `int Property kShout = 119 AutoReadOnly` | 122 |
| property | `kEquipSlot` | `int Property kEquipSlot = 120 AutoReadOnly` | 123 |
| property | `kRelationship` | `int Property kRelationship = 121 AutoReadOnly` | 124 |
| property | `kScene` | `int Property kScene = 122 AutoReadOnly` | 125 |
| property | `kAssociationType` | `int Property kAssociationType = 123 AutoReadOnly` | 126 |
| property | `kOutfit` | `int Property kOutfit = 124 AutoReadOnly` | 127 |
| property | `kArt` | `int Property kArt = 125 AutoReadOnly` | 128 |
| property | `kMaterial` | `int Property kMaterial = 126 AutoReadOnly` | 129 |
| property | `kMovementType` | `int Property kMovementType = 127 AutoReadOnly` | 130 |
| property | `kSoundDescriptor` | `int Property kSoundDescriptor = 128 AutoReadOnly` | 131 |
| property | `kDualCastData` | `int Property kDualCastData = 129 AutoReadOnly` | 132 |
| property | `kSoundCategory` | `int Property kSoundCategory = 130 AutoReadOnly` | 133 |
| property | `kSoundOutput` | `int Property kSoundOutput = 131 AutoReadOnly` | 134 |
| property | `kCollisionLayer` | `int Property kCollisionLayer = 132 AutoReadOnly` | 135 |
| property | `kColorForm` | `int Property kColorForm = 133 AutoReadOnly` | 136 |
| property | `kReverbParam` | `int Property kReverbParam = 134 AutoReadOnly` | 137 |

## Game

Source: `scripts/modified/Game.psc` · blob `7cdffab32bd2d7449575899376c9c1372925cf08`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetPerkPoints` | `int Function GetPerkPoints() global native` | 2 |
| function | `SetPerkPoints` | `Function SetPerkPoints(int perkPoints) global native` | 3 |
| function | `ModPerkPoints` | `Function ModPerkPoints(int perkPoints) global native` | 4 |
| function | `GetModCount` | `int Function GetModCount() native global` | 7 |
| function | `GetModByName` | `int Function GetModByName(string name) native global` | 10 |
| function | `GetModName` | `string Function GetModName(int modIndex) native global` | 13 |
| function | `GetModAuthor` | `string Function GetModAuthor(int modIndex) native global` | 16 |
| function | `GetModDescription` | `string Function GetModDescription(int modIndex) native global` | 19 |
| function | `GetModDependencyCount` | `int Function GetModDependencyCount(int modIndex) native global` | 22 |
| function | `IsPluginInstalled` | `bool Function IsPluginInstalled(string name) native global` | 27 |
| function | `GetLightModCount` | `int Function GetLightModCount() native global` | 30 |
| function | `GetLightModByName` | `int Function GetLightModByName(string name) native global` | 31 |
| function | `GetLightModName` | `string Function GetLightModName(int idx) native global` | 32 |
| function | `GetLightModAuthor` | `string Function GetLightModAuthor(int idx) native global` | 33 |
| function | `GetLightModDescription` | `string Function GetLightModDescription(int idx) native global` | 34 |
| function | `GetLightModDependencyCount` | `int Function GetLightModDependencyCount(int idx) native global` | 35 |
| function | `GetNthLightModDependency` | `int Function GetNthLightModDependency(int modIdx, int idx) native global` | 36 |
| function | `SetGameSettingFloat` | `Function SetGameSettingFloat(string setting, float value) global native` | 39 |
| function | `SetGameSettingInt` | `Function SetGameSettingInt(string setting, int value) global native` | 40 |
| function | `SetGameSettingBool` | `Function SetGameSettingBool(string setting, bool value) global native` | 41 |
| function | `SetGameSettingString` | `Function SetGameSettingString(string setting, string value) global native` | 42 |
| function | `SaveGame` | `Function SaveGame(string name) native global` | 45 |
| function | `LoadGame` | `Function LoadGame(string name) native global` | 46 |
| function | `GetNumTintMasks` | `int Function GetNumTintMasks() native global` | 51 |
| function | `GetNthTintMaskColor` | `int Function GetNthTintMaskColor(int n) native global` | 54 |
| function | `GetNthTintMaskType` | `int Function GetNthTintMaskType(int n) native global` | 57 |
| function | `SetNthTintMaskColor` | `Function SetNthTintMaskColor(int n, int color) native global` | 60 |
| function | `GetNthTintMaskTexturePath` | `string Function GetNthTintMaskTexturePath(int n) native global` | 63 |
| function | `SetNthTintMaskTexturePath` | `Function SetNthTintMaskTexturePath(string path, int n) native global` | 66 |
| function | `GetNumTintsByType` | `int Function GetNumTintsByType(int type) native global` | 86 |
| function | `GetTintMaskColor` | `int Function GetTintMaskColor(int type, int index) global native` | 89 |
| function | `SetTintMaskColor` | `Function SetTintMaskColor(int color, int type, int index) global native` | 92 |
| function | `GetTintMaskTexturePath` | `string Function GetTintMaskTexturePath(int type, int index) global native` | 95 |
| function | `SetTintMaskTexturePath` | `Function SetTintMaskTexturePath(string path, int type, int index) global native` | 98 |
| function | `UpdateTintMaskColors` | `Function UpdateTintMaskColors() global native` | 101 |
| function | `UpdateHairColor` | `Function UpdateHairColor() global native` | 104 |
| function | `GetCameraState` | `int Function GetCameraState() global` | 120 |
| function | `SetMiscStat` | `Function SetMiscStat(string name, int value) global native` | 126 |
| function | `SetPlayersLastRiddenHorse` | `Function SetPlayersLastRiddenHorse(Actor horse) global native` | 129 |
| function | `GetSkillLegendaryLevel` | `int Function GetSkillLegendaryLevel(string actorValue) global` | 134 |
| function | `SetSkillLegendaryLevel` | `Function SetSkillLegendaryLevel(string actorValue, int level) global` | 140 |
| function | `GetPlayerExperience` | `float Function GetPlayerExperience() global native` | 145 |
| function | `SetPlayerExperience` | `Function SetPlayerExperience(float exp) global native` | 148 |
| function | `GetExperienceForLevel` | `float Function GetExperienceForLevel(int currentLevel) global native` | 152 |
| function | `GetPlayerMovementMode` | `bool Function GetPlayerMovementMode() global native` | 156 |
| function | `UpdateThirdPerson` | `Function UpdateThirdPerson() global` | 159 |
| function | `UnbindObjectHotkey` | `Function UnbindObjectHotkey(int hotkey) global native` | 165 |
| function | `GetHotkeyBoundObject` | `Form Function GetHotkeyBoundObject(int hotkey) global native` | 168 |
| function | `IsObjectFavorited` | `bool Function IsObjectFavorited(Form form) global native` | 171 |
| function | `GetFormEx` | `Form Function GetFormEx(int formId) global native` | 174 |
| function | `GetDialogueTarget` | `ObjectReference Function GetDialogueTarget() global native` | 177 |
| function | `GetCurrentCrosshairRef` | `ObjectReference Function GetCurrentCrosshairRef() global native` | 180 |
| function | `GetCurrentConsoleRef` | `ObjectReference Function GetCurrentConsoleRef() global native` | 183 |
| function | `SetPlayerLevel` | `Function SetPlayerLevel(int level) global native` | 186 |

## GameData

Source: `scripts/modified/GameData.psc` · blob `e66a7018076c16db8cdedbe335de4d9d55cff4c6`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| property | `WeaponTypeHandToHand` | `int Property WeaponTypeHandToHand = 1 AutoReadOnly` | 8 |
| property | `WeaponTypeOneHandSword` | `int Property WeaponTypeOneHandSword = 2 AutoReadOnly` | 9 |
| property | `WeaponTypeOneHandDagger` | `int Property WeaponTypeOneHandDagger = 4 AutoReadOnly` | 10 |
| property | `WeaponTypeOneHandAxe` | `int Property WeaponTypeOneHandAxe = 8 AutoReadOnly` | 11 |
| property | `WeaponTypeOneHandMace` | `int Property WeaponTypeOneHandMace = 16 AutoReadOnly` | 12 |
| property | `WeaponTypeTwoHandSword` | `int Property WeaponTypeTwoHandSword = 32 AutoReadOnly` | 13 |
| property | `WeaponTypeTwoHandAxe` | `int Property WeaponTypeTwoHandAxe = 64 AutoReadOnly` | 14 |
| property | `WeaponTypeBow` | `int Property WeaponTypeBow = 128 AutoReadOnly` | 15 |
| property | `WeaponTypeStaff` | `int Property WeaponTypeStaff = 256 AutoReadOnly` | 16 |
| property | `WeaponTypeCrossbow` | `int Property WeaponTypeCrossbow = 512 AutoReadOnly` | 17 |
| function | `GetAllWeapons` | `Form[] Function GetAllWeapons(string modName, Keyword[] keywords = None, bool playable = true, bool ignoreTemplates = true, bool ignoreEnchantments = true, bool onlyEnchanted = false, int weaponTypes = 0xFFFFFFFF) global native` | 19 |
| function | `GetAllArmor` | `Form[] Function GetAllArmor(string modName, Keyword[] keywords = None, bool playable = true, bool ignoreTemplates = true, bool ignoreEnchantments = true, bool onlyEnchanted = false, bool ignoreSkin = true) global native` | 21 |
| function | `GetAllAmmo` | `Form[] Function GetAllAmmo(string modName, Keyword[] keywords = None, bool playable = true) global native` | 23 |
| function | `GetAllBooks` | `Form[] Function GetAllBooks(string modName, Keyword[] keywords = None, bool regular = true, bool spell = false, bool skill = false) global native` | 25 |
| function | `GetAllPotions` | `Form[] Function GetAllPotions(string modName, Keyword[] keywords = None, bool potions = true, bool food = false, bool poison = false) global native` | 27 |
| function | `GetAllIngredients` | `Form[] Function GetAllIngredients(string modName, Keyword[] keywords = None) global native` | 29 |
| function | `GetAllScrolls` | `Form[] Function GetAllScrolls(string modName, Keyword[] keywords = None) global native` | 31 |
| function | `GetAllKeys` | `Form[] Function GetAllKeys(string modName, Keyword[] keywords = None) global native` | 33 |
| function | `GetAllMiscItems` | `Form[] Function GetAllMiscItems(string modName, Keyword[] keywords = None) global native` | 35 |

## HeadPart extends Form

Source: `scripts/modified/HeadPart.psc` · blob `4c022c40b544bcd3adb846a9ae602dd34154cd5c`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| property | `Type_Misc` | `int Property Type_Misc = 0 AutoReadOnly` | 3 |
| property | `Type_Face` | `int Property Type_Face = 1 AutoReadOnly` | 4 |
| property | `Type_Eyes` | `int Property Type_Eyes = 2 AutoReadOnly` | 5 |
| property | `Type_Hair` | `int Property Type_Hair = 3 AutoReadOnly` | 6 |
| property | `Type_FacialHair` | `int Property Type_FacialHair = 4 AutoReadOnly` | 7 |
| property | `Type_Scar` | `int Property Type_Scar = 5 AutoReadOnly` | 8 |
| property | `Type_Brows` | `int Property Type_Brows = 6 AutoReadOnly` | 9 |
| function | `GetHeadPart` | `HeadPart Function GetHeadPart(string name) native global` | 11 |
| function | `GetType` | `int Function GetType() native` | 14 |
| function | `GetNumExtraParts` | `int Function GetNumExtraParts() native` | 16 |
| function | `GetNthExtraPart` | `HeadPart Function GetNthExtraPart(int n) native` | 17 |
| function | `HasExtraPart` | `bool Function HasExtraPart(HeadPart p) native` | 19 |
| function | `GetIndexOfExtraPart` | `int Function GetIndexOfExtraPart(HeadPart p) native` | 20 |
| function | `GetValidRaces` | `FormList Function GetValidRaces() native` | 23 |
| function | `SetValidRaces` | `Function SetValidRaces(FormList vRaces) native` | 24 |
| function | `IsExtraPart` | `bool Function IsExtraPart() native` | 27 |
| function | `GetPartName` | `string Function GetPartName() native` | 30 |

## Ingredient

Source: `scripts/modified/Ingredient.psc` · blob `2211207004469f6c40ddc8f83d1f01db7f78df3b`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetNumEffects` | `int Function GetNumEffects() native` | 2 |
| function | `GetNthEffectMagnitude` | `float Function GetNthEffectMagnitude(int index) native` | 5 |
| function | `GetNthEffectArea` | `int Function GetNthEffectArea(int index) native` | 8 |
| function | `GetNthEffectDuration` | `int Function GetNthEffectDuration(int index) native` | 11 |
| function | `GetNthEffectMagicEffect` | `MagicEffect Function GetNthEffectMagicEffect(int index) native` | 14 |
| function | `GetCostliestEffectIndex` | `int Function GetCostliestEffectIndex() native` | 17 |
| function | `SetNthEffectMagnitude` | `Function SetNthEffectMagnitude(int index, float value) native` | 20 |
| function | `SetNthEffectArea` | `Function SetNthEffectArea(int index, int value) native` | 23 |
| function | `SetNthEffectDuration` | `Function SetNthEffectDuration(int index, int value) native` | 26 |
| function | `GetIsNthEffectKnown` | `bool Function GetIsNthEffectKnown(int index) native` | 29 |
| function | `GetEffectMagnitudes` | `float[] Function GetEffectMagnitudes() native` | 32 |
| function | `GetEffectAreas` | `int[] Function GetEffectAreas() native` | 35 |
| function | `GetEffectDurations` | `int[] Function GetEffectDurations() native` | 38 |
| function | `GetMagicEffects` | `MagicEffect[] Function GetMagicEffects() native` | 41 |

## Input

Source: `scripts/modified/Input.psc` · blob `14e380527f376cf41e875b8951233f285facaade`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `IsKeyPressed` | `bool Function IsKeyPressed(Int dxKeycode) global native` | 4 |
| function | `TapKey` | `Function TapKey(Int dxKeycode) global native` | 7 |
| function | `HoldKey` | `Function HoldKey(Int dxKeycode) global native` | 10 |
| function | `ReleaseKey` | `Function ReleaseKey(Int dxKeycode) global native` | 13 |
| function | `GetNumKeysPressed` | `int Function GetNumKeysPressed() global native` | 16 |
| function | `GetNthKeyPressed` | `int Function GetNthKeyPressed(int n) global native` | 19 |
| function | `GetMappedKey` | `int Function GetMappedKey(string control, int deviceType = 0xFF) global native` | 35 |
| function | `GetMappedControl` | `string Function GetMappedControl(int keycode) global native` | 38 |

## Keyword

Source: `scripts/modified/Keyword.psc` · blob `656df848f959395c952ce457091413b1eb3f461e`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetKeyword` | `Keyword Function GetKeyword(string key) global native` | 2 |
| function | `GetString` | `string Function GetString() native` | 5 |

## LeveledActor

Source: `scripts/modified/LeveledActor.psc` · blob `2b08a3627078312142caf6b09d07dbb29eb2695a`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetNumForms` | `int Function GetNumForms() native` | 1 |
| function | `GetNthForm` | `Form Function GetNthForm(int n) native` | 2 |
| function | `GetNthLevel` | `int Function GetNthLevel(int n) native` | 4 |
| function | `SetNthLevel` | `Function SetNthLevel(int n, int level) native` | 5 |
| function | `GetNthCount` | `int Function GetNthCount(int n) native` | 7 |
| function | `SetNthCount` | `Function SetNthCount(int n, int count) native` | 8 |

