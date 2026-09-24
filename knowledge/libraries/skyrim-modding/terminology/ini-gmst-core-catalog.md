# Skyrim Modding Terminology — Core INI and Game Setting Catalog

Imported: 2026-09-24
Status: sourced frontier-deepening pass

This catalog prioritizes settings that frequently appear in troubleshooting or mod authoring. It deliberately excludes folklore-only tweaks unless behavior is documented/reproducible.

## INI precedence and file families

### Skyrim.ini
Primary engine/system configuration.

### SkyrimPrefs.ini
Launcher/user preference configuration, especially graphics/display/input.

### SkyrimCustom.ini
User override layer for Skyrim.ini values.

### Plugin INI fragment
Data/<PluginName>.ini loaded with active plugin in supported engine settings contexts.

### CreationKit.ini / CreationKitCustom.ini
Modern Creation Kit config/override files.

### Effective setting
Value after defaults, generated settings, custom override, profile-specific INIs and framework-level overrides.

## Papyrus settings

### [Papyrus] fUpdateBudgetMS
Default CK documentation value: 1.2 ms. Per-frame VM update budget component.

### fExtraTaskletBudgetMS
Default 1.2 ms. Additional Papyrus tasklet budget.

### fPostLoadUpdateTimeMS
Default 500 ms on PC per CK documentation. Extra VM processing around load transition.

### iMinMemoryPageSize
Default 128.

### iMaxMemoryPageSize
Default 512.

### iMaxAllocatedMemoryBytes
Default 76800 in historical CK documentation.

### bEnableLogging
Enable Papyrus logs.

### bEnableTrace
Allow Debug.Trace output.

### bLoadDebugInformation
Load compiler debug info.

### bEnableProfiling
Enable Papyrus profiling support.

### Papyrus budget tweak risk
Raising budgets can shift CPU time from rendering/gameplay to VM; not a generic FPS fix.

## General/load settings

### uGridsToLoad
Exterior loaded-cell grid dimension. Increasing it affects world loading, save behavior, memory and generated data assumptions; historically high-risk to change mid-playthrough.

### uExterior Cell Buffer
Exterior-cell buffering setting tied to loaded-grid behavior.

### bPreemptivelyUnloadCells
Cell-unloading behavior setting, often circulated in tweak guides; require measured evidence before changing.

### fMasterFilePreLoadMB
Master-file preload memory setting historically exposed in INI discussions; version/platform behavior should be tested.

## Display

### bFull Screen
Fullscreen mode flag.

### bBorderless
Borderless mode.

### iSize W / iSize H
Output resolution.

### iVSyncPresentInterval
Presentation/vsync-related setting; modern Display Tweaks can override presentation behavior.

### fDefaultWorldFOV
World FOV default.

### fDefault1stPersonFOV
First-person FOV default.

### fDefaultFOV
UI/other FOV default depending on context.

### fNearDistance
Near clipping distance.

### iShadowMapResolution
Shadow-map resolution.

### fShadowDistance
Exterior shadow draw distance.

### fInteriorShadowDistance
Interior shadow distance.

### iBlurDeferredShadowMask
Shadow filter quality/blur level.

### bDrawLandShadows
Landscape shadow toggle.

### bTreesReceiveShadows
Tree shadow receiving.

### bDrawShadows
Broad CK/game shadow toggle depending on file/context.

## Grass

### bAllowCreateGrass
Allows Creation Kit/game to create grass cache/data in relevant workflows.

### bAllowLoadGrass
Controls loading generated grass data in CK workflows.

### iMinGrassSize
Grass density control; lower value generally means denser placement.

### fGrassStartFadeDistance
Grass fade start.

### fGrassMaxStartFadeDistance
Upper fade range preference.

### fGrassMinStartFadeDistance
Lower fade range.

### b30GrassVS
Grass shader/path setting used by Skyrim SE.

## Trees/LOD

### fTreeLoadDistance
Tree draw/LOD range.

### fBlockMaximumDistance
Object LOD block maximum distance.

### fBlockLevel1Distance
LOD level transition.

### fBlockLevel0Distance
LOD level transition.

### fSplitDistanceMult
LOD split-distance multiplier.

### bDisplayLODTrees
CK rendering toggle for LOD trees.

### bDisplayLODBuildings
CK rendering toggle.

## Water

### bUseWaterReflections
Reflection toggle.

### bUseWaterRefractions
Refraction toggle.

### bUseWaterDepth
Water depth effects.

### bUseWaterDisplacements
Water displacement.

### bUseWaterHiRes
High-resolution water behavior in CK/game contexts.

## Particles

### iMaxDesired
Maximum desired particle count.

### particle budget
Higher particle limit increases visual density and GPU/CPU workload; effects can also have independent emitter counts.

## Audio

### fAudioMasterVolume
Master-volume preference family.

### bEnableAudio
Creation Kit audio toggle often disabled for CK stability/performance during authoring.

## Archive/resources

### sResourceArchiveList
List of BSAs loaded through configured archive list in older/common setups.

### sResourceArchiveList2
Additional archive list.

### bInvalidateOlderFiles
Loose-file/resource invalidation behavior used by mod-manager/manual setups.

## Save/autosave

### bSaveOnPause
Autosave on menu/pause event.

### bSaveOnTravel
Autosave on travel.

### bSaveOnWait
Autosave after waiting.

### bSaveOnRest
Autosave after sleeping.

### iAutoSaveCount
Autosave slot count.

### autosave reliability
Autosave settings affect save cadence, not save integrity guarantees. For testing, use controlled named saves.

## Interface/input

### bGamepadEnable
Controller enable setting.

### fMouseHeadingSensitivity
Mouse sensitivity family.

### bMouseAcceleration
Mouse acceleration behavior in relevant input configs.

## Game Settings / GMST examples

### fJumpHeightMin
Jump height/impulse-related game setting.

### fMoveRunMult
Run movement multiplier.

### fMoveSprintMult
Sprint multiplier.

### fCombatDistance
Combat behavior distance family.

### fSneakBaseValue
Detection/sneak calculation input family.

### fSneakLightMult
Light contribution to detection.

### fSneakSoundsMult
Sound contribution.

### fSneakRunningMult
Movement/running contribution.

### iDaysToRespawnVendor
Merchant reset timing family.

### iHoursToRespawnCell
Cell reset timing family.

### iHoursToRespawnCellCleared
Cleared-cell reset timing family.

### fBarterBuyMin
Barter pricing lower/upper formula family.

### fBarterSellMax
Barter sell-price formula family.

### fAlchemyGoldMult
Alchemy value/cost calculation family.

### fEnchantingSkillCostBase
Enchanting/cost progression family.

### iTrainingNumAllowedPerLevel
Training sessions allowed each player level.

### fPickPocketMinChance
Pickpocket chance floor.

### fPickPocketMaxChance
Pickpocket chance ceiling.

### iCrimeGoldAttack
Crime/bounty amount for assault-related action.

### iCrimeGoldMurder
Murder bounty.

### iCrimeGoldPickpocket
Pickpocket crime value.

### iCrimeGoldSteal
Theft crime formula/base family.

### fMagicCasterSkillCostBase
Spell-cost skill scaling family.

### fMagicCasterSkillCostMult
Spell-cost scaling multiplier.

### fMagicCasterPCSkillCostMult
Player-specific cost scaling family.

### fShoutTimeMult
Shout cooldown/recovery timing family.

### fArmorScalingFactor
Armor rating/damage-reduction scaling family.

### fMaxArmorRating
Maximum effective armor-related cap family.

### fPlayerMaxResistance
Player resistance cap.

### fPlayerMaxResistanceMult
Resistance cap multiplier family.

## Settings ownership

### Engine INI
Read by game executable.

### Framework INI
Read by SKSE DLL such as Display Tweaks, Engine Fixes or Papyrus Tweaks; may supersede vanilla setting behavior.

### GMST
Plugin-load-order form data, not filesystem INI.

### MCM/JSON setting
Mod-specific configuration.

### Runtime patch
Native/script code can ignore/replace effects of static setting.

## Diagnostic rules

1. Record which file/profile/framework actually owns the effective value.
2. Do not mix GMST and INI explanations.
3. Avoid cargo-cult "performance INI" bundles.
4. Change one subsystem at a time and benchmark.
5. Papyrus logging settings are diagnostics, not optimization.
6. uGrids changes are world/save-affecting and require careful controlled workflow.
7. Display Tweaks/ENB/CS can supersede vanilla display/presentation assumptions.
8. CK INI advice is not automatically valid for the game executable.

## Sources

- Creation Kit Wiki Papyrus INI defaults: https://ck.uesp.net/wiki/INI_Settings_%28Papyrus%29
- Creation Kit/Skyrim INI override behavior documented in Creation Kit reference ecosystem
- xEdit/CK/engine testing remains required for GMST semantics that lack official documentation.
