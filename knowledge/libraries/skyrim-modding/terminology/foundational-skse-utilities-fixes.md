# Skyrim Modding Terminology — Foundational SKSE Utilities, Limits, and Runtime Fixes

Imported: 2026-09-24
Status: sourced deep-ingestion pass 23

This module covers small/native dependencies and fixes whose absence can break otherwise unrelated mods or create engine behavior that is easy to misdiagnose as a load-order issue.

## ConsoleUtilSSE NG

### ConsoleUtilSSE NG
CommonLibSSE-NG port of ConsoleUtil allowing Papyrus scripts/native integrations to execute Skyrim console commands programmatically.

### ExecuteCommand
Papyrus/native functionality sending a console command to game console interpreter.

### ExecuteCommandTarget
ConsoleUtil function/pattern executing a command against a specified ObjectReference as console target.

### Console command bridge
Script calls functionality otherwise accessible only through developer console.

### ConsoleUtil dependency
Mod can compile/load ordinary PEX scripts but fail at runtime when ConsoleUtil's native functions are missing.

### Console command side effect
Executing console commands from scripts can alter save state just like manual console use.

### Console target
Reference against which targeted console command operates.

### Command injection risk
Do not pass untrusted arbitrary strings into ConsoleUtil in frameworks exposed to AI/web/external data.

## Scaleform Translation Plus Plus NG

### ST++
Scaleform Translation Plus Plus family extending Skyrim/SkyUI translation lookup.

### Translation nesting
Translation value can reference another translation key and be recursively resolved.

### English fallback
If active language lacks translation, framework can fall back to English rather than showing raw missing key.

### UTF-16 translation
Support/fixes for languages requiring UTF-16 encoding.

### Interface translation
Files under `Data/Interface/Translations/` mapping `$KEY` tokens to localized strings.

### Missing $KEY
UI displays untranslated key literal because translation file/key/encoding/framework lookup failed.

### Translation recursion
Nested keys resolve repeatedly; malformed cycles/deep nesting must be guarded by implementation.

### CommonLibSSE-NG translation DLL
Current NG build targets multiple Skyrim SE/AE runtime versions from one DLL where supported.

## Animation Queue Fix

### Animation Queue Fix
SKSE native fix preventing animation-load request queue from overflowing/lagging/crashing when many animations need to load at once.

### Animation load queue
Engine queue of animation files/clips waiting to be loaded.

### Queue overload
Too many animation requests arrive before loader consumes them, producing delayed animation, A-pose/T-pose or CTD in extreme cases.

### Animation preload
OAR/DAR-style framework loads replacement animations early to reduce mid-play delay.

### Skip preloading
OAR experimental/config mode can avoid ordinary preload behavior; whether Animation Queue Fix is required depends on current OAR configuration/version.

### A-pose
Actor shows static bind/default pose because expected animation did not load/play in time or graph lacks valid output.

### T-pose
Common generic term for missing animation pose; Skyrim's actual visible fallback may resemble A-pose depending on skeleton/clip.

### Animation variety pressure
Huge OAR/DAR stacks increase number of clips and can stress loading even when behavior graph is otherwise valid.

## Paired Animation Improvements

### Paired Animation Improvements / PAI
SKSE native fix/improvement for paired/synchronized animations.

### Paired animation
Animation involving two actors/references synchronized to one interaction, such as killmove, paired idle, mount/dismount or special interaction.

### Annotation in paired animation
Timed events inside synchronized clips that vanilla handling may not propagate correctly; PAI improves annotation support.

### Paired alignment
Engine aligns participants to expected interaction transforms.

### Paired desync
Actors drift/misalign or events trigger on only one participant.

### Mount/dismount paired animation
Horse/dragon interactions are paired animation cases; PAI changelog specifically fixed a dragon-mount regression.

### Paired resource
Authoring/sample assets documenting vanilla paired-animation event semantics.

## Actor Limit Fix

### Actor Limit Fix
SKSE native plugin increasing several vanilla actor-processing limits.

### Mover limit
Maximum number of nearby actors receiving full movement processing at one time.

### Morph limit
Maximum number of actors whose facial expressions/lip-sync are processed.

### Static actor array
Vanilla fixed-size array of actors prioritized largely by distance for limited processing tasks.

### Floating actors
Symptom when engine mover limit is exceeded and some actors fail normal locomotion processing.

### Frozen faces
Actors beyond morph-processing limit lack facial animation/lip-sync.

### Actor-density bottleneck
Cities/battles with many high-processing actors can hit engine actor limits even when CPU still has headroom.

### Limit increase
Raising hard/static limits does not remove actual CPU workload; huge actor counts can still become performance-heavy.

### ActorLimitFix.json
Runtime configuration selecting increased limits/features.

## Recursion Monitor

### Recursion Monitor
SKSE plugin detecting pathological Papyrus recursion and interrupting/limiting it to prevent severe framerate collapse.

### Recursive script
Papyrus function/event calls itself directly/indirectly.

### Unbounded recursion
No valid terminating condition, producing ever-growing stacks/work.

### Recursion depth
Number of nested recursive calls.

### Recursion guard
Runtime protection stopping recursive path beyond threshold/unsafe behavior.

### Recursion hitch
Severe VM/frame impact from runaway recursive script before guard/stack failure.

### Recursion log
Diagnostic evidence identifying problematic script/function chain.

### Runtime support drift
Recursion Monitor's old DLL can become incompatible with newer Address Library/runtime; current bug reports must be checked before recommending it universally.

## Save Unbaker

### Save Unbaker
powerofthree SKSE plugin making selected data always load from current plugins instead of save-baked ChangeForm values.

### Unbake
Ignore/remove authority of saved value for selected field so plugin record becomes authoritative again at load.

### Baked NPC weight
NPC weight stored in save can preserve old value after NPC appearance plugin update.

### Opposite Gender Anims baked flag
NPC OGA flag can be saved; Save Unbaker can force current plugin value.

### Persistent reference transform
Position/rotation of some persistent statics/furniture/flora can be baked into save.

### Door transform unbake
Current Save Unbaker can also address persistent door transforms.

### Plugin-authority restoration
Goal is not deleting whole ChangeForm but overriding selected save-side field with current plugin data.

### Unbaker scope
Only selected fields/reference categories are affected; it is not a general "make save clean" tool.

### Mid-save appearance update
Common use case: NPC replacer changes weight; unbaker allows new plugin weight to apply without fresh game for that field.

### Player exclusion
Current Save Unbaker intentionally excludes player weight from NPC weight unbake.

## Cell load freeze fix

### Skyrim Cell Load Freeze Fix NG
Native patch targeting specific engine deadlock during cell loading.

### Deadlock
Threads each hold one lock while waiting for another lock held by the other, preventing progress indefinitely.

### Lock-order inversion
Two code paths acquire lock A/B in opposite order.

### Freeze vs CTD
Deadlock leaves process running but nonresponsive; no native exception/crash log may be generated.

### Thread dump
Best evidence for deadlock; examine threads waiting on locks rather than crash stack.

### Specific deadlock fix
Patch reorders lock acquisition for known engine path; does not solve every freeze.

## Animated Static Reload Fix

### Animated Static Reload Fix
SKSE plugin fixing looping animated statics that fail to restart their animation after loading a save/cell state.

### Animated static
MSTT/STAT-like world model with looping Gamebryo/NIF animation.

### Loop restart
Reinitialize looping animation when reference 3D reloads.

### Frozen animated static
Water wheel/machinery/etc. visually stops after load even though reference exists.

### Asset vs engine bug
NIF may be valid; runtime failed to reactivate loop.

## Barter Limit Fix

### Barter Limit Fix
SKSE plugin fixing vanilla integer/transfer bug when merchant gold/item counts exceed 32,767.

### 32,767 limit
Signed 16-bit boundary implicated in vanilla barter transfer issue.

### High-gold merchant
Vendor with more than 32,767 gold can fail to pay player correctly without fix.

### High-count purchase
Similar bug can affect buying if merchant has extremely high count of one item.

### Barter overflow symptom
Player receives zero/wrong transfer despite merchant appearing wealthy.

## Foundational-utility diagnosis

### Transitive utility dependency
Feature mod requires utility indirectly through script/API; missing utility may present as errors in feature mod.

### Native fix overlap
Two fix DLLs hook same function; current compatibility documentation decides whether they can stack.

### Runtime-specific build
Utility that worked on 1.6.1170 can fail on 1.7.99/1.7.104 after executable changes.

### Silent utility failure
DLL fails to load/register; dependent PEX still exists and produces misleading Papyrus errors.

### Utility log
First place to confirm hook/API was installed successfully.

## Diagnostic rules

1. Check utility DLL logs before diagnosing dependent mods.
2. A native "fix" only fixes its documented bug; do not use it as generic troubleshooting superstition.
3. Save Unbaker changes which source has authority for selected fields; it does not reset quests/scripts generally.
4. Animation Queue Fix addresses load pressure, not malformed behavior graphs.
5. Paired Animation Improvements addresses paired animation handling, not ordinary single-actor OAR selection.
6. Actor Limit Fix raises hard processing limits but can increase actual workload.
7. ConsoleUtil commands can permanently modify save state; treat scripted commands as consequential.
8. Translation++ fixes translation resolution/encoding, not missing localized plugin STRINGS files.
9. Deadlock freezes need hang/thread evidence, not only crash logs.

## Sources

- ConsoleUtilSSE NG: https://www.nexusmods.com/skyrimspecialedition/mods/76649
- Scaleform Translation Plus Plus NG: https://www.nexusmods.com/skyrimspecialedition/mods/77359
- Animation Queue Fix: https://www.nexusmods.com/skyrimspecialedition/mods/82395
- Paired Animation Improvements: https://www.nexusmods.com/skyrimspecialedition/mods/99621
- Actor Limit Fix: https://www.nexusmods.com/skyrimspecialedition/mods/32349
- Recursion Monitor: https://www.nexusmods.com/skyrimspecialedition/mods/76867
- Save Unbaker: https://www.nexusmods.com/skyrimspecialedition/mods/85565
- Skyrim Cell load Freeze fix NG: https://www.nexusmods.com/skyrimspecialedition/mods/160704
- Animated Static Reload Fix NG: https://www.nexusmods.com/skyrimspecialedition/mods/69331
- Barter Limit Fix: https://www.nexusmods.com/skyrimspecialedition/mods/77173

## Dated notes

As of 2026-09-24: ConsoleUtilSSE NG 1.6.1 was updated 2026-08-22; Animation Queue Fix 1.0.2 and Paired Animation Improvements 1.0.3 were updated 2026-08-31; Actor Limit Fix version 9 was updated 2026-08-26; Save Unbaker 1.0.6 was updated 2026-08-26; Cell Load Freeze Fix NG 0.0.5 was updated 2026-08-24.
