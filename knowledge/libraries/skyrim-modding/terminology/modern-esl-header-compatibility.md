# Skyrim Modding Terminology — Modern ESL Range, Header 1.71, and Backported Compatibility

Imported: 2026-09-24
Status: sourced deep-ingestion pass 14

## Creations-era plugin format changes

### Plugin header version 1.70
Pre-Creations-era Skyrim SE plugin header generation commonly used by runtime families through 1.6.659/older builds.

### Plugin header version 1.71
Plugin header generation introduced by Bethesda's December 2023 Creations update. Older runtimes do not natively understand every associated loader/range change.

### Extended ESL range
Creations-era expansion increasing new-record capacity in ESL-flagged plugins from the old range to 4096 local records.

### Old ESL range
Pre-Creations light-plugin local FormID allocation convention with narrower usable new-record space.

### New ESL range
Extended local light-plugin record range supported natively by newer runtimes/Creation Kit.

### Header-version incompatibility
Older executable attempts to load newer 1.71 plugin format and can fail/crash even if the plugin's record semantics would otherwise be usable.

### FormID range incompatibility
Plugin uses newly valid extended ESL local IDs that older runtime mapping does not recognize without backport support.

## Backported Extended ESL Support / BEES

### BEES
**Expansion:** Backported Extended ESL Support. SKSE plugin by Nukem9 backporting Creations-era extended ESL/header handling to older Skyrim SE runtimes.

### BackportedESLSupport.dll
Native plugin implementing loader/container hooks required for old runtimes to accept modern plugin headers/light-range data.

### Loader hook
Native patch modifying plugin loader behavior to understand header/range features absent from old executable.

### Container hook
Native patch extending internal storage/index behavior needed for larger ESL range.

### Native-support cutoff
BEES code checks whether current game version already includes Bethesda's native extended ESL support and skips its hooks there.

### BEES log
`BackportedESLSupport.log` under SKSE logs, reporting relevant plugin/header conditions.

### Backport requirement
A new Creation/modern mod may legitimately require BEES on 1.5.97/older AE runtime even if it contains no native DLL itself.

### False "wrong game version" diagnosis
Modern plugin crashes older runtime because plugin header/light range is unsupported, not because mod necessarily requires AE content/API.

### BEES vs Address Library
BEES changes plugin loading/data support; Address Library resolves executable addresses for native SKSE DLLs. One does not replace the other.

### BEES vs ESL flag
BEES does not make arbitrary oversized plugin automatically ESL-compatible; plugin still must meet valid light-plugin record/form constraints.

## Creation Kit implications

### Modern CK-created ESL
Plugin created/resaved with newer CK can receive header/record range semantics requiring newer runtime or BEES.

### Extended ObjectID
ObjectID values in newly expanded light range that were invalid for old runtime.

### Compact-to-ESL after expansion
Modern tools may allow compaction into larger ESL range; such output needs appropriate runtime compatibility.

### Cross-runtime release
Author targeting both current and 1.5.97-era users should document whether files require BEES and whether any native components separately support those runtimes.

### Header downgrade
Manually changing header version number without understanding extended FormIDs/loader assumptions is unsafe and not a substitute for proper backport compatibility.

## Runtime matrix

### Native extended-ESL runtime
Game executable implementing Bethesda's current header/light-range rules.

### Backported extended-ESL runtime
Older executable plus BEES.

### Unsupported old runtime
Older executable without BEES attempting to load modern header/range files.

### Plugin-only compatibility
ESP/ESL works with BEES, but bundled native DLL may still fail due ABI/runtime mismatch.

### Creation dependency compatibility
Official/new Creations may use modern formats/assets and therefore require both plugin-loader compatibility and any content/runtime assumptions they introduce.

## Diagnostic rules

1. Record exact plugin header and local FormID range when old-runtime users crash before main menu.
2. Do not assume “ESL flagged” means universally loadable on all Skyrim SE runtimes.
3. BEES solves loader/light-range compatibility; it does not port SKSE DLLs.
4. Do not hand-edit 1.71→1.70 header version as a generic compatibility fix.
5. If a mod author compacts using extended range, declare minimum runtime/BEES requirement.
6. When troubleshooting missing masters after Creations updates, include official Resource Pack/Creation files and modern ESL compatibility in the dependency check.
7. xEdit/CK behavior itself should be version-scoped; older tools may not fully understand newer format changes.

## Sources

- Backported Extended ESL Support upstream: https://github.com/Nukem9/skyrimse-backported-esl-support
- BEES README explaining header 1.71 and 4096-record expansion: https://github.com/Nukem9/skyrimse-backported-esl-support/blob/master/README.md
- Bethesda Creations update patch notes: https://bethesda.net/en-US/news/the-elder-scrolls-v-skyrim-special-edition-creations-update-patch-notes
- xEdit current documentation: https://tes5edit.github.io/docs/
