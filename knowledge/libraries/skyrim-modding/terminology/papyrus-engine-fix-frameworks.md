# Skyrim Modding Terminology — Papyrus Engine Fixes and VM Tweak Frameworks

Imported: 2026-09-24
Status: sourced deep-ingestion pass 14

## Papyrus Tweaks NG

### Papyrus Tweaks NG
SKSE/SKSEVR native plugin providing fixes, optional VM tweaks, logger improvements and experimental changes to Skyrim's Papyrus engine.

### Fix
Framework setting intended to correct known vanilla Papyrus bug with minimal semantic change.

### VM Tweak
Optional behavior/performance/config change to script engine; not universally necessary.

### Logger Tweak
Change affecting Papyrus logging/debugging rather than game logic.

### Experimental tweak
Option whose side effects/testing are incomplete; should not be enabled by default in automated recommendations.

### PapyrusTweaks.ini
Configuration under `Data/SKSE/Plugins` generated/read by Papyrus Tweaks NG.

### Toggle Scripts Command Fix
Fix preserving intended script-paused state around save/stack-dump operations.

### Negative Script Page Allocation Fix
Fix for pathological VM memory allocation using negative page size under some conditions.

### IsHostileToActor Crash Fix
Prevents native Papyrus crash when function receives None/null actor parameter.

### Delayed script breakage fix
Fix for vanilla soft-dependency issue where missing script dependencies can silently break scripts later; fix can restore operation but cannot reconstruct data already absent in existing saves.

### Native call speed-up
Experimental/advanced VM optimization accelerating selected native calls; current versions provide exclusion controls for script classes/quests because compatibility risk exists.

### Stack dump timeout
Configurable time Papyrus attempts to dump stacks before giving up; disabling timeout can create locked states.

### VR playroom tweak
VR-specific guard/behavior around Papyrus stack dumping in playroom/startup context.

## Soft dependencies

### Papyrus soft dependency
Script references another script/type/function expected to be optional.

### Missing soft dependency
Referenced external script absent. Vanilla behavior can cause delayed breakage rather than cleanly ignoring every reference.

### Native registration soft dependency
Papyrus script declares native function but supplying SKSE DLL is absent/incompatible.

### Stub source
PSC declaration used for compilation even though implementation comes from native DLL at runtime.

### Compile dependency vs runtime dependency
Author needs PSC sources to compile; user needs PEX and runtime DLL/framework but not necessarily PSC source.

### Broken native binding
PEX calls native function whose DLL failed to load/register, producing runtime errors.

## VM settings

### VM page
Papyrus memory allocation page used for stack/data allocation.

### Memory page size
INI/tweak controlling VM allocation chunks.

### Max allocated memory bytes
Papyrus memory limit/tweak concept; values and implementations vary by framework/version.

### Budget
Milliseconds per frame Papyrus scheduler can spend.

### Extra tasklet budget
Additional processing window for Papyrus tasks.

### Post-load update budget
Extra script time allowed during loading transition.

### Overbudget warning
VM reports script/task workload exceeding configured budget.

### Stack dump
Diagnostic attempt to serialize/report script stacks under overload/error.

### Stack dump storm
Repeated large dumps worsening performance/logging while underlying script problem persists.

### Logging overhead
Very verbose Papyrus logging can add I/O and contention, especially during error storms.

### Trace throttling
Technique reducing repeated identical debug traces.

## Script profiling and diagnostics

### StartScriptProfiling
Engine API enabling profiler for one script.

### StartObjectProfiling
Profiles scripts associated with an object.

### StartStackProfiling
Profiles specific stack.

### VM profiling
Measuring actual script/event/function time rather than assuming log errors imply performance cost.

### Soft-dependency recovery
Testing framework fix on new save vs existing save because old save may already have missing serialized fields/instances.

## Other fix frameworks

### po3 Tweaks Papyrus changes
powerofthree's Tweaks includes selected Papyrus/game script-engine related fixes/tweaks alongside non-Papyrus engine changes.

### Scrambled Bugs
Native bug-fix framework covering many engine/gameplay issues; some features alter script-observed behavior but it is not a Papyrus VM replacement.

### Bug Fixes SSE
Native bug-fix plugin family correcting engine issues, including cases observable through scripts.

### Engine Fixes
Broader runtime-fix suite that can influence save/loading/file handles and systems interacting with scripts.

### Fix overlap
Two native frameworks patch same vanilla code path. Version documentation must establish compatibility; do not assume more fixes can always be stacked.

## Diagnostic rules

1. Papyrus Tweaks NG default fixes and optional experimental VM tweaks are different risk classes.
2. Never increase VM budgets/memory blindly to hide a runaway script.
3. Existing-save damage from previously broken soft dependencies may not be reconstructible by installing the fix later.
4. A missing native DLL can look like Papyrus errors even though PSC/PEX are present.
5. Profile before attributing FPS issues to Papyrus.
6. Keep one source of truth for overlapping native engine patches and follow current compatibility docs.
7. Treat logger tweaks as diagnostics; turning off logs does not fix underlying script errors.

## Sources

- Papyrus Tweaks NG upstream: https://github.com/Nightfallstorm/PapyrusTweaks
- Papyrus Tweaks NG Nexus/current documentation: https://www.nexusmods.com/skyrimspecialedition/mods/77779
- po3 Tweaks upstream: https://github.com/powerof3/po3-Tweaks
- Bug Fixes SSE / Scrambled Bugs source family: https://github.com/KernalsEgg/SKSE64Plugins
- Creation Kit Papyrus INI settings: https://ck.uesp.net/wiki/INI_Settings_%28Papyrus%29

## Dated snapshot

Papyrus Tweaks NG 4.1.1 was observed as current on 2026-09-24. Its page explicitly separates Fixes, VMTweaks, LoggerTweaks and Experimental options and states default settings do not inherently raise/lower FPS.
