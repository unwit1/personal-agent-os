# Skyrim Modding Terminology — Container Distribution and Contextual Activation Frameworks

Imported: 2026-09-24
Status: sourced deep-ingestion pass 16

## Container Item Distributor / CID

### CID
**Expansion:** Container Item Distributor. SKSE framework that adds, removes or swaps items/leveled lists in container inventories at runtime through `_CID.ini` configs.

### _CID.ini
CID config suffix discovered under mod roots.

### Container
For CID purposes, any reference whose inventory can be accessed by the player can qualify, including ordinary chests and some actors depending on rule target.

### Distribution string
CID value describing which forms/lists to add/remove/swap, counts/chance and rule semantics.

### Add
Runtime insertion of configured item/list.

### Remove
Runtime removal of configured item/list.

### Remove All
Rule removing all matching instances/entries as supported.

### Swap
Replace one configured form/list with another.

### Swap All
Apply replacement across all matching entries.

### Leveled-list distribution
Adding LVLI entries/references into target container inventory logic at runtime.

### Container base targeting
Rule aimed at a specific container base identity.

### Reference targeting
Rule aimed at one exact placed container/reference.

### EditorID target
CID target resolved by EditorID.

### FormID~Plugin target
Stable config form identity using local FormID plus plugin filename.

### CID debug log
Framework log used to diagnose parser/target/distribution errors.

## Container Distribution Framework / CDF

### CDF
**Expansion:** Container Distribution Framework. Native runtime framework distributing items to placed container references using rule sets such as location, reference, count and item keywords.

### Reference-level distribution
CDF can choose individual placed containers dynamically rather than replacing the shared CONT base record.

### Location filter
Rule limiting distribution to containers in selected Location/world contexts.

### Container type filter
Rule selecting specific container/base categories.

### Item keyword filter
Rule constraining candidate items according to keywords.

### Merchant protection
CDF advertises logic that can avoid ordinary merchant containers by default/rule, preventing accidental vendor-economy mutation.

### Count rule
Controls quantity of item inserted.

### Better leveled-list logic
Current CDF lineage includes explicit support/updates for distributing leveled-list-based content.

### CDF runtime floor
Current main CDF build requires Skyrim SE 1.6.1130+, with separate community backport for 1.5.97.

### CDF 1.5 port
Separate runtime port providing framework version for Skyrim 1.5.97.

## Container runtime patching vs static edits

### Static CONT override
Plugin edits base container inventory. Every reference based on it inherits changed defaults and competing mods may conflict in xEdit.

### Runtime reference injection
Framework adds items to selected actual container references after load.

### Vendor-list injection
Adding items to merchant ecosystem via appropriate vendor container/list selection.

### Respawn interaction
Runtime additions may need framework-specific reapplication after container reset/respawn.

### Duplicate distribution
Same item is added through CID/CDF and a static patch/distributor simultaneously.

### Distribution provenance
Record exactly which runtime config added one item because xEdit may show no corresponding plugin override.

## Dynamic Activation Key / DAK

### DAK
**Expansion:** Dynamic Activation Key. Framework providing an alternate modifier activation action, commonly Shift+Activate, for compatible mods.

### Alternate activation
Secondary interaction invoked while configured modifier/key is held.

### DynamicActivationKey global
Papyrus-version global set while configured key is active; supporting mods can condition behavior on it.

### Activation prompt replacement
DAK integrations can change displayed activation text dynamically to describe secondary action.

### Activation perk
Perk/entry-point based pattern changing activation behavior/text under DAK condition.

### Text replacer perk
Perk mechanism used by DAK integrations to change activation prompt.

### Contextual activation
Same object exposes different action according to DAK modifier plus conditions.

### Papyrus DAK
Original/recommended script-based version described on current mod page.

### DAK DLL
Optional native implementation replacing/hooking input/state behavior for specific/current runtime builds.

### DAK hotkey
Configured keyboard/controller modifier used for secondary activation.

### SKSE Menu Framework configuration
Current 1.7.104 native DAK build can use SKSE Menu Framework to configure its key.

### DAK API
Current DLL lineage exposes API for setting keycodes/interop.

### VR binding
VR compatibility layer maps DAK modifier to VR controller buttons via Skyrim VR Tools.

### Suspended-stack issue
Community-documented Papyrus-version edge case where holding the key can accumulate suspended stacks under some implementation paths; version/patch-specific evidence rather than a universal Papyrus conclusion.

## Secondary interaction examples

- read vs take book;
- open vs peek door;
- talk vs pet/greet actor;
- ride vs pet horse;
- loot vs process carcass;
- normal crafting station vs alternate crafting mode;
- merchant talk vs direct barter;
- follower talk vs inventory;
- vanilla activation vs special religious/quest action.

### Alternate crafting station
DAK integration spawns/uses alternative station/workbench keyword while preserving ordinary activation as default.

### Crosshair reference
Object currently targeted by player's activation ray; contextual mods often query it to determine alternate behavior.

## Compatibility rules

1. Runtime container frameworks solve a different problem than SPID: container/reference inventories vs actor-base distributions.
2. CDF and CID can overlap; do not enable two configs that add identical content to same targets unless intended.
3. Static vendor/container edits can coexist with runtime distribution but duplicate entries must be checked.
4. Runtime-distributed entries may be affected by cell/container reset differently from static base contents.
5. DAK supporting mod should default safely when DAK is absent/inactive if dependency is optional.
6. Input modifier state and actual activation event are separate; don't run expensive polling when event/perk condition can express behavior.
7. Exact DAK Papyrus vs DLL implementation matters when diagnosing stack/input conflicts.

## Sources

- Container Item Distributor current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/99486
- Container Distribution Framework current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/120152
- CDF 1.5 backport: https://www.nexusmods.com/skyrimspecialedition/mods/120386
- Dynamic Activation Key: https://www.nexusmods.com/skyrimspecialedition/mods/96273
- DAK VR bindings: https://www.nexusmods.com/skyrimspecialedition/mods/164198

## Dated snapshot

CDF 3.1.0 was current as of 2026-09-24 and requires 1.6.1130+ in its main build. CID remained version 2.1.3. DAK 1.13 was updated 2026-08-30 with an optional Skyrim 1.7.104 DLL while its Papyrus implementation remained the author's recommended general version.
