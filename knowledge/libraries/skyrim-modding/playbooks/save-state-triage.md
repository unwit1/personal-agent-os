# Playbook — Skyrim Save-State and Mod-Update Triage

Updated: 2026-09-24
Status: high-consequence operational playbook

Use when a problem exists only on an established save, appears after updating/removing a mod, or may involve ReSaver/Papyrus/native serialization.

## Safety boundary

Never modify the only copy of a save. Preserve together:
- ESS;
- SKSE co-save;
- relevant external per-save data;
- modlist/load order;
- current and prior mod versions.

Do not automate destructive save edits without a mod-specific repair contract or strong structural evidence.

## 1. Compare state scopes

Determine whether the affected data lives in:
- plugin defaults/records;
- reference ChangeForms;
- quest state;
- Papyrus instances/variables/arrays/stacks;
- SKSE co-save native serialization;
- PapyrusUtil/JContainers data;
- external JSON/INI/FISS settings;
- generated runtime references/forms.

## 2. New-game differential

Test the same installed mod configuration on a new save.

Works new / fails old:
- migration/persisted state likely.

Fails both:
- current install/plugin/asset/runtime likely.

Fails only new:
- startup initialization/config/quest fill differences or old save contains compensating state.

## 3. Update analysis

Record:
- source version;
- target version;
- whether scripts changed;
- whether FormIDs/plugin filename changed;
- whether masters changed;
- whether native serialization schema changed;
- whether author documents update procedure;
- whether clean/new save is required.

## 4. ReSaver interpretation

ReSaver/FallrimTools parses:
- plugin list;
- FormID arrays;
- ChangeForms;
- Papyrus data;
- created forms;
- stacks/instances;
- other save structures.

Useful targeted categories include:
- unattached instances;
- undefined elements;
- nonexistent created-form instances;
- null FormList entries;
- Havok movement ChangeForms;
- truncation/broken Papyrus indications.

A label is not automatic permission to delete the item.

## 5. When restoration is safer

Prefer restoring missing/old mod version temporarily when:
- save contains many unresolved forms/scripts;
- uninstall was unsupported;
- quest currently running;
- native serialization schema vanished;
- exact clean-up steps require the original mod.
Then perform author-supported shutdown/uninstall/migration if possible.

## 6. Quest/alias state

Inspect:
- active quest/stages;
- filled aliases;
- persistent refs;
- alias scripts;
- packages/spells applied through aliases;
- Story Manager-managed quests;
- scene state.
Deleting a quest's script instance without reconciling the quest can leave worse state.

## 7. Native co-save state

If an SKSE plugin changed:
- confirm plugin loaded successfully;
- compare serialization unique ID/version behavior;
- inspect plugin log for load/migration errors;
- keep matching co-save with ESS;
- do not delete co-save merely because crash occurs unless evidence points there.

## 8. External state

Check mod directories under:
- SKSE/Plugins;
- MCM/Settings;
- JSON/config paths;
- JContainers/PapyrusUtil-specific storage;
- Documents/My Games config paths.
A “fresh save” may still load global external configuration.

## 9. Repair decision ladder

Least destructive first:
1. Correct current missing dependency/version.
2. Restore expected asset/script/DLL.
3. Run supported in-mod migration.
4. Roll back to earlier save/version.
5. Use targeted ReSaver cleanup backed by identified invalid structure.
6. Only as last resort, deeper manual ChangeForm/Papyrus surgery.

## 10. Validation

After repair:
- save under new filename;
- exit/relaunch game;
- reload repaired save;
- reproduce original scenario;
- inspect logs;
- create another save and reload it;
- verify quests/NPCs/world state;
- retain untouched original.

## Sources
- FallrimTools/ReSaver: https://github.com/mdfairch/FallrimTools
- FallrimTools ESS source: https://github.com/mdfairch/FallrimTools/blob/main/src/main/java/resaver/ess/ESS.java
- SKSE/CommonLib serialization APIs: https://github.com/alandtse/CommonLibSSE-NG
