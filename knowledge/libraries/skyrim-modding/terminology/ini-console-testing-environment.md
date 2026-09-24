# Skyrim Modding Terminology — INI Settings, Console, and Test Environment

Imported: 2026-09-24
Status: sourced deep-ingestion pass 6

## Configuration layers

### Skyrim.ini
Game configuration file containing engine/gameplay/system settings, including many Papyrus and archive-related settings.

### SkyrimPrefs.ini
Preference-oriented settings, commonly graphics/display/input options written by launcher/game.

### SkyrimCustom.ini
Optional user override file used by many setups to place custom settings without editing generated/default INIs directly.

### Profile-specific INI
Mod-manager-managed copies of INI files associated with one profile rather than the user's global My Games files.

### INI precedence
Order in which game/default/custom/profile/tool-managed settings override each other. Diagnose the effective value rather than assuming the file manually edited is the one Skyrim reads.

### BethINI / BethINI Pie
External utility ecosystem for configuring Skyrim INI settings through curated presets/options. Tool recommendations/settings should be version-specific.

### Game Setting / GMST
Game data setting stored through game/plugin records rather than ordinary filesystem INI configuration.

### INI setting vs GMST
INI settings configure engine/runtime behavior from files; GMST records are plugin-load-order game data. Similar names do not imply the same storage/override mechanism.

## Papyrus INI concepts

### bEnableLogging
Papyrus setting enabling log output.

### bEnableTrace
Papyrus setting enabling Debug.Trace output when logging is configured.

### bLoadDebugInformation
Papyrus setting controlling debug information loading.

### fUpdateBudgetMS
VM time budget for update work.

### fExtraTaskletBudgetMS
Additional tasklet execution budget.

### fPostLoadUpdateTimeMS
Extra script processing time during loading before load screen removal. CK documentation notes it can matter when complex cell/Story Manager quest setup must complete near load transitions.

### iMinMemoryPageSize
Papyrus VM stack-page memory allocation setting.

### VM tuning
Changing Papyrus budgets/memory values. Treat as advanced environment tuning and measure outcomes; internet “performance INI” values can be harmful.

## Console

### Developer console
In-game command interface for querying/changing runtime state.

### Targeted reference
Object selected in console; many commands operate on that specific reference.

### prid
Console command selecting a reference by ID.

### help
Search command for forms/commands by name/string.

### sqv
**Expansion:** ShowQuestVars. Displays quest variables/alias-related state useful for diagnosis.

### sqs
**Expansion:** ShowQuestStages. Shows quest stages and completion flags.

### getstage
Returns current quest stage.

### setstage
Sets a quest stage and can trigger fragments/logic. Consequential debugging action; do not use casually on production saves.

### startquest
Starts a quest.

### stopquest
Stops a quest. Can break quest state if used without understanding lifecycle.

### resetquest
Resets quest state according to engine behavior. Not a generic save cleaner.

### getav
Displays actor value.

### getavinfo
Shows more detailed actor-value information where supported.

### setav
Sets base/current actor value semantics according to command behavior; can create test state not equivalent to normal gameplay progression.

### modav
Modifies actor value.

### forceav
Forces actor value and can bypass ordinary modifier layers. Useful for testing but can create persistent/unrepresentative state.

### showinventory
Displays reference inventory and instance information.

### inv
Inventory shorthand/listing in supported console contexts.

### disable / enable
Changes reference enable state. On persistent references this can save into the game and is not merely visual debugging.

### recycleactor
Resets/reinitializes actor state aggressively. Dangerous for unique/quest actors; never a first-line recommendation.

### resetai
Resets actor AI state.

### evp
EvaluatePackage; forces actor to reevaluate packages but does not reset combat/pathing generally.

### tcl
Toggle collision for player/test movement. Useful to inspect inaccessible geometry but does not prove navmesh connectivity.

### tai
Toggle AI globally.

### tcai
Toggle combat AI.

### pcb
Purge cell buffers; useful for test reload scenarios.

### coc
Center On Cell, teleports to a named cell for testing.

### cow
Center On World, teleports to exterior coordinates.

### tfc
Toggle free camera for visual inspection.

### sucsm
Set free-camera movement speed.

### tm
Toggle menus/HUD. Can hide console itself; remember current state.

### save
Create named save through console for controlled test checkpoints.

## Test profiles

### Minimal reproduction profile
Mod-manager profile containing only dependencies and suspected components needed to reproduce a bug.

### Clean-room test
Testing in isolated game/mod-manager directories without unrelated user configuration.

### New-game baseline
Fresh save to eliminate established-save state as a variable.

### Existing-save migration case
Copy of an established save used specifically to test update compatibility.

### Golden save
Controlled reproducible save positioned/configured for repeated regression testing.

### Test cell
Dedicated interior/exterior space used to exercise assets/scripts/gameplay in isolation.

### COC marker
Cell/editor setup allowing direct console transition to the test environment.

### Deterministic test
Procedure that gives the same expected input/state/result across runs.

### Regression test
Repeatable test preserving behavior that previously failed/fixed.

### A/B test
Two controlled configurations differing by one variable.

### Binary-search isolation
Disable/enable half of candidate components iteratively to narrow a large conflict set.

### Test contamination
Prior console commands, save state, cached/generated files or leftover assets influencing supposedly clean results.

## Environment variables in troubleshooting

Record:
- game/runtime build;
- store/distribution;
- game root;
- Documents/My Games path;
- mod manager/profile;
- INI source and overrides;
- generated outputs;
- plugin load order;
- asset priority;
- SKSE DLL list;
- root injectors;
- Windows/GPU driver;
- save identity.

## Diagnostic rules

1. Verify which INI file/profile is effective before changing settings.
2. Do not solve mod logic problems by blindly applying internet INI “performance tweaks.”
3. Console state-changing commands can become serialized in the save and contaminate later tests.
4. EVP tests package selection, not navmesh correctness.
5. A minimal profile is stronger evidence than repeatedly changing dozens of mods on the main profile.
6. Preserve a golden save/new-game path for regression testing.
7. Record every test change so successful fixes are reproducible.

## Sources

- Creation Kit Wiki Papyrus INI settings: https://ck.uesp.net/wiki/INI_Settings_%28Papyrus%29
- Creation Kit Wiki EvaluatePackage: https://ck.uesp.net/wiki/EvaluatePackage
- Creation Kit Wiki Cell View / test navigation context: https://ck.uesp.net/wiki/Cell_View_Window
- Creation Kit Wiki console/designer debug references: https://ck.uesp.net/wiki/Category:Console_Commands
