# Skyrim Modding Terminology — Runtime Distribution and Compatibility Frameworks

Imported: 2026-09-24
Status: sourced deep-ingestion pass 2

This reference covers modern SKSE-based frameworks that move compatibility work from static plugin overrides into runtime/config-driven distribution.

## Core design concept

### Runtime distribution
Applying forms, keywords, list membership, outfits, packages, swaps, or other data when the game loads/initializes instead of baking the same changes into many plugin overrides.

### Static patching vs runtime distribution
Static patching writes final data into a plugin. Runtime distribution computes/applies changes after plugin data loads. Runtime approaches can avoid shared-record conflicts, but they add framework/config/version dependencies and require log-driven validation.

### Config-driven framework
A native SKSE plugin that reads declarative configuration files and performs changes according to those rules.

### Runtime-generated keyword
Keyword created or exposed dynamically by a framework instead of requiring a pre-existing plugin record. Such keywords can be useful for categorization but may not exist as ordinary plugin records for every tool/workflow.

### Filter
Rule narrowing the set of forms/actors that receive a runtime change.

### Positive filter
Condition that must match for an item/actor to remain eligible.

### Exclusion filter
Condition that removes matching forms/actors from eligibility.

### Wildcard / partial-match filter
String filter matching a substring/pattern rather than exact text.

### AND filter group
Multiple requirements that must all match together.

### OR / alternative group
Multiple possible matches where satisfying one group is enough.

### Trait filter
Framework-specific numeric/boolean/category filter based on properties such as sex, uniqueness, body slot, damage, armor rating, actor level, magic-effect traits, or other typed data.

### Form filter
Filter using exact forms, FormIDs, EditorIDs, factions, races, keywords, plugins, equipment slots, or other referenced game forms.

### String filter
Filter using names, EditorIDs, keywords-as-strings, archetype names, actor values, model paths, or other string-resolvable data depending on framework.

### Chance
Deterministic or random percentage controlling whether a distribution/swap occurs. Each framework defines when chance is seeded/re-evaluated; never assume all “50%” systems reroll at the same lifecycle point.

## SPID

### SPID
**Expansion:** Spell Perk Item Distributor.  
SKSE framework by powerofthree for distributing spells, perks, items, shouts, packages, outfits, keywords, factions, and related data to NPCs from configuration files.

### _DISTR.ini
Common SPID configuration naming convention/suffix. Distribution rules are read from config files rather than requiring one plugin override per NPC.

### Distribution entry
One SPID rule describing what to distribute and which NPCs qualify.

### Distribution type
The left-side entry type such as Spell, Perk, Item, Shout, Package, Outfit, Keyword, Faction, or other supported SPID record category.

### Actor-base distribution
SPID primarily targets NPC actor-base data/eligibility rather than requiring manual edits to every NPC_ override.

### String filter in SPID
Text-based matching against supported NPC characteristics such as names/EditorIDs/keywords and other supported values.

### Form filter in SPID
Filtering against forms such as factions, races, classes, combat styles, plugins, and other supported form-based actor characteristics.

### Level filter
SPID eligibility restriction based on actor level/ranges.

### Skill filter
SPID eligibility restriction based on configured actor skill values/ranges.

### Trait filter in SPID
Eligibility rules for properties such as sex, unique status, summonable/child/leveled/teammate/starts-dead states where supported by current SPID.

### Distribution count
For item-like distributions, controls quantity where supported.

### Distribution chance
Percentage determining whether the entry is applied to an eligible actor.

### SPID deterministic distribution
Modern SPID uses stable evaluation for many chance/filter outcomes so the same rule can produce consistent NPC results rather than behaving like uncontrolled random loot each load. Confirm exact behavior against current version when design depends on deterministic seeding.

### SPID log
Runtime log recording parsing/distribution behavior and errors. Treat it as primary evidence when a DISTR rule appears not to work.

### SPIDFormatter
Utility/source component associated with SPID used to upgrade/downgrade or sanitize older/newer config syntax across format changes.

## KID

### KID
**Expansion:** Keyword Item Distributor.  
SKSE framework that distributes keywords to supported base-form types at startup using config files.

### _KID.ini
KID configuration naming convention/suffix.

### KID distribution entry
Rule declaring a keyword, target form type, filters, traits, and optional chance.

### KID target type
Form type eligible for keyword assignment. Current KID supports many classes including weapons, armor, ammo, magic effects, potions, scrolls, locations, ingredients, books, misc items, keys, soul gems, spells, activators, flora, furniture, races, talking activators, and enchantments.

### KID dynamic keyword
If configured appropriately, KID can dynamically generate a keyword by EditorID when no ordinary keyword form is found. Such keywords are runtime concepts and should not be assumed to behave like plugin-authored KEYM records in every external tool.

### Exact match
Default-style KID matching where a candidate must match a supplied exact filter value.

### Wildcard match
KID `*` partial matching against supported text such as names/EditorIDs/keywords/model paths.

### Exclusion
KID `-` modifier preventing matches.

### Exclusion wildcard
KID `-*` modifier excluding candidates containing a partial string.

### AND group
KID `+` expression requiring multiple terms together, e.g. a form matching both heavy-armor and gauntlet classification.

### KID trait
Typed filters specific to the target form type, such as armor body slot/weight/rating, weapon type/damage/weight, magic-effect values, hostile/enchantment states, or other supported properties.

### KID dependency ordering
KID sorts keyword distributions according to dependencies so newly distributed keywords can be used by later dependent entries.

### KID fixed chance
Current KID documentation describes chance outcomes as fixed across game sessions for a given distribution rather than constantly rerolled.

### KID log
Primary runtime evidence for parsed entries, generated keywords, candidate matching, and distribution failures.

## BOS

### BOS
**Expansion:** Base Object Swapper.  
SKSE/SKSEVR framework that replaces base forms for placed references at runtime based on configuration.

### _SWAP.ini
Base Object Swapper config naming convention/suffix.

### Base-form swap
Changing which base object a placed reference uses while keeping the reference itself as the world instance.

### Reference-specific swap
BOS rule targeting one particular placed reference rather than every reference using a base form.

### Form swap
BOS rule targeting references according to original base form.

### Locational swap
BOS rule applying only in selected locations/cells/worldspaces/regions/keyword-matched locations.

### Swap target
Replacement base form selected by BOS.

### Multiple swap candidates
Configuration where one original form can choose among multiple replacement bases.

### Property override
BOS modification to reference properties such as transform or flags in addition to, or sometimes without, a base swap.

### Transform override
Runtime position, rotation, or scale modification.

### Relative transform
Transform offset applied relative to the original reference transform.

### Absolute transform
Transform value replacing the original reference value.

### Record-flag override
BOS ability to set/clear supported reference flags at runtime.

### chanceS
BOS fixed/stable chance mode intended to preserve a reference's result across game sessions.

### chanceR
BOS chance mode that can reroll per new game session.

### chanceL
BOS location-oriented deterministic chance mode based on location/original base context.

### BOS conflict resolution
When multiple configs target the same swap context, current BOS has explicit conflict/config-order behavior. Validate actual winners using the BOS log rather than assuming plugin load order determines runtime config precedence.

### Reference initialization
BOS applies base swaps during reference initialization in modern versions so swapped base data/scripts can initialize as the replacement base.

### Runtime swap vs plugin override
BOS can replace world objects without editing every placed REFR record in a compatibility plugin, reducing traditional reference conflicts.

## FLM

### FLM
**Expansion:** FormList Manipulator.  
SKSE plugin/framework that adds/removes forms from FormLists at runtime using configuration files.

### _FLM.ini
FLM configuration suffix.

### Runtime FormList mutation
Adding/removing forms after plugin loading rather than shipping a static FLST override.

### FLM FormList entry
Rule specifying a target FormList, forms/groups/collections to add or remove, and optional filter.

### FLM Remove
Runtime rule removing configured forms from a FormList.

### FLM Filter
Named or inline condition based primarily on plugin presence/absence combinations.

### FLM Alias
Reusable named collection of FormLists.

### FLM Group
Reusable named collection of forms/expanded lists/collections.

### FLM Collection
Dynamically discovered group of forms selected by form type and keyword requirements/exclusions.

### FLM collection tag
Named collection construct used so later rules can reference a computed group of forms instead of enumerating them manually.

### FLM ModEvent
Runtime-triggerable rule that modifies FormLists on demand when a configured mod event is received.

### FLM flatten-list operator
Asterisk-prefix behavior that adds the contents of another FormList rather than the FormList form itself.

### Runtime list compatibility
Using FLM so multiple mods can add data to a shared FormList without all shipping competing FLST overrides.

### FLM processing order
Config files are processed in documented alphabetical/path order. Reusable filters/aliases/groups persist across config processing, so naming/order can affect availability and outcome.

## OCF as an ecosystem example

### OCF
**Expansion:** Object Categorization Framework.  
Framework/data project that categorizes game/mod forms with standardized Keywords and FormLists for other mods to use as conditions.

### Categorization framework
Shared vocabulary/data layer defining stable semantic categories such as object types/materials/uses so downstream mods do not each reinvent classification.

### Keyword categorization
Representing membership in a category by assigning a keyword.

### FormList categorization
Representing categories via membership in FormLists when a form type does not support ordinary keywords or list semantics are more useful.

### Framework consumer
A mod that reads/conditions on categories supplied by another framework rather than implementing all detection itself.

## Compatibility strategy encoded for Agent OS

1. Prefer SPID when the desired change is “give eligible NPCs X” and static NPC overrides would cause unnecessary conflicts.
2. Prefer KID when the desired change is “classify eligible forms with keyword X.”
3. Prefer BOS when the desired change is “replace/transform eligible placed world objects at runtime.”
4. Prefer FLM when the desired change is “add/remove eligible forms from a shared FormList.”
5. Do not assume runtime frameworks are conflict-free merely because they avoid ESP overrides; configs can conflict, duplicate, depend on ordering, or target incompatible data.
6. Always inspect each framework's runtime log when rules do not produce expected results.
7. Record exact framework version because config grammar and supported filters evolve.
8. When a runtime framework creates dynamic data, note whether downstream systems require a real plugin record or can consume runtime-generated state.
9. Prefer declarative runtime distribution over huge compatibility-plugin matrices when it preserves semantics and remains inspectable/testable.
10. Use static patches when the final plugin record itself must carry the combined data or when runtime mutation is unsupported/too opaque.

## Sources

- SPID upstream repository: https://github.com/powerof3/Spell-Perk-Item-Distributor
- SPID Nexus/current documentation: https://www.nexusmods.com/skyrimspecialedition/mods/36869
- KID upstream repository: https://github.com/powerof3/Keyword-Item-Distributor
- KID Nexus/current documentation: https://www.nexusmods.com/skyrimspecialedition/mods/55728
- BOS upstream repository: https://github.com/powerof3/BaseObjectSwapper
- BOS Nexus/current documentation: https://www.nexusmods.com/skyrimspecialedition/mods/60805
- FLM upstream repository: https://github.com/MaskedRPGFan/FormList-Manipulator
- FLM Nexus documentation: https://www.nexusmods.com/skyrimspecialedition/mods/74037
- Object Categorization Framework upstream: https://github.com/GroundAura/Object-Categorization-Framework
- OCF Nexus documentation: https://www.nexusmods.com/skyrimspecialedition/mods/81469

## Version/provenance notes

- KID observed current Nexus version on 2026-09-24: 4.1.0, updated 2026-08-25.
- BOS observed current Nexus changelog includes 3.5.0 support changes for Skyrim 1.7.99+.
- SPID observed Nexus version 7.3.3 dated 2026-08-26.
- FLM has an original upstream plus a 2026 community runtime port; distinguish framework/config semantics from which DLL build is compatible with a specific new Skyrim runtime.
- These frameworks evolve rapidly. Syntax and target support should always be checked against the installed/current version during implementation.
