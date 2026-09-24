# Skyrim Modding Terminology — Runtime Property, Sound, and String Injection

Imported: 2026-09-24
Status: sourced deep-ingestion pass 17

This module covers runtime frameworks that change final in-memory form properties after ordinary plugin load, often eliminating conflicts that would otherwise require static record patches.

## Sound Record Distributor / SRD

### SRD
**Expansion:** Sound Record Distributor. SKSE framework distributing sound-record relationships to loaded forms at runtime.

### Sound distribution
Runtime replacement/addition of sound fields on target records.

### SRD config
JSON/JSONC/YAML configuration tied to plugins or loaded globally.

### Plugin-tied config
Config whose filename/association causes SRD to process it in relation to one loaded plugin.

### Global config
Config not tied to one plugin, processed according to framework file ordering.

### SRD processing order
Game forms load first; SRD then applies plugin-associated configs followed by other configs in alphabetical order according to current documentation.

### Runtime sound load order
Concept that audio field choices can be resolved by SRD configs separately from ESP record load order.

### Weapon sound patch
Example: assign dagger-specific impact/attack sounds without overriding WEAP records.

### Region sound patch
Runtime alteration of REGN sound data so weather mod and audio overhaul need fewer static compatibility patches.

### Footstep/heel sound distribution
Runtime assigning alternate sound relationships to equipment/actor categories.

### Sound field conflict
Two SRD rules modify same final sound property; xEdit static conflict view cannot show final runtime winner.

### SRD YAML
Compact configuration format supported by current SRD.

### SRD JSONC
JSON configuration with comments/syntax support.

## Dynamic String Distributor / DSD

### DSD
**Expansion:** Dynamic String Distributor. Runtime text-replacement/distribution framework used to change translatable/display strings without shipping a broad plugin override.

### Runtime string patch
Change a loaded form's visible/localized string value in memory.

### DSD JSON
Machine-readable mapping of forms/fields/string values for runtime replacement.

### String distribution
Applying translated/alternate display text to forms after ordinary plugin data load.

### Translation patch without ESP
Using DSD to localize/change mod strings without duplicating whole form records in a translation plugin.

### Activate Text Override
RNAM/activation text-like string field frequently targeted by interaction-icon/text frameworks.

### DSD patch
Config replacing strings for forms from an original mod while preserving non-string record edits from other plugins.

### DSDifyer
Toolset of xEdit/Python scripts for extracting form strings into DSD-ready configuration.

### DSD xEdit exporter
xEdit script that exports selected plugin strings to DSD JSON, reducing manual transcription.

### Runtime translation layer
Translation exists after plugin load rather than by replacing embedded/localized plugin text directly.

### Text drawn by native plugin
String generated directly by SKSE DLL/UI logic; not necessarily replaceable by DSD because it may not originate in form strings.

### DSD version pin
Translation package should record original mod version/string extraction snapshot because IDs/text can change across releases.

## Item Property Manipulator / IPM

### IPM
**Expansion:** Item Property Manipulator. CommonLibSSE-NG SKSE framework changing properties of supported form types using `_IPM.ini` configuration.

### _IPM.ini
Config suffix/location convention for IPM rules.

### Item section
Config block selecting target form type/forms and properties to mutate.

### Filter
Reusable plugin-presence condition controlling whether rule applies.

### Collection
Dynamically built set of one form type selected by keywords/exclusions.

### Group
Reusable list of explicit forms and/or collections.

### OnStart
Mode applying changes when Skyrim starts/forms are loaded.

### OnGameReload
Mode reapplying changes on start and game reload.

### Disabled/on-demand
Mode parsing rule but only executing via Papyrus API.

### Property mutation
Changing loaded form value such as name, gold value, weight, damage, speed, reach, armor, spell cost/type, light radius/color or other supported property.

### Runtime value override
Final in-memory value differs from every static ESP override.

### Global-variable-backed property
IPM can source some values from a GlobalVariable so settings can be data-driven.

### Collection exclude
Explicit forms/plugins omitted from keyword-defined collection.

### IPM Papyrus execution
Scripts can trigger parsed item sections on demand.

### IPM debug log
Runtime evidence for parsed files/forms/property changes.

## Runtime patch precedence

### Static winner
Value xEdit identifies after plugin load order.

### Runtime winner
Value remaining after all native/script runtime patchers mutate static winner.

### Runtime patch stack
Ordered collection of systems such as SkyPatcher, IPM, SRD, DSD, KID, BOS, FLM, SPID, CDF and script/native changes.

### Hidden conflict
Two runtime systems modify same field without an ESP-level conflict.

### Runtime provenance
Need to record framework/config/rule that produced final in-game value.

### Reapply-on-load
Framework reapplies property changes when save loads, potentially overriding script/save-time changes.

### One-shot startup mutation
Patch only occurs once during process initialization.

## Diagnostic rules

1. xEdit can correctly show the static winner while game shows another value because runtime patchers changed it.
2. Identify every runtime framework capable of mutating the affected field.
3. Check framework config processing order and logs.
4. DSD translations should be version-scoped to the original mod's current strings/forms.
5. SRD can eliminate audio/weather static conflicts, but two SRD configs can still conflict.
6. IPM OnGameReload can intentionally overwrite a value changed by another runtime script after prior load.
7. Do not create an ESP compatibility patch for a runtime-generated conflict until you know whether the runtime framework will overwrite it afterward.

## Sources

- Sound Record Distributor current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/77815
- Item Property Manipulator current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/95795
- IPM config docs: https://www.nexusmods.com/skyrimspecialedition/articles/5573
- IPM item property docs: https://www.nexusmods.com/skyrimspecialedition/articles/5576
- Dynamic String Distributor tooling: https://www.nexusmods.com/skyrimspecialedition/mods/114102
- DSD xEdit exporter: https://www.nexusmods.com/skyrimspecialedition/mods/129369

## Dated snapshot

SRD 1.5.3 was current as of 2026-09-24, updated 2026-08-24. IPM 0.5.2 is a CommonLibSSE-NG framework supporting SE/AE/VR. Exact field support and runtime ordering should be checked against installed versions.
