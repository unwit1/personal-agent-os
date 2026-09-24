# Skyrim Modding Terminology — Survival, Camping, Needs, and Exposure Frameworks

Imported: 2026-09-24
Status: sourced deep-ingestion pass 15

## Survival-state dimensions

### Hunger
Need state increasing over game time and applying penalties/benefits according to framework.

### Fatigue
Sleep/rest need state.

### Cold / Exposure
Environmental state representing accumulated thermal stress.

### Warmth
Equipment/environment value reducing exposure gain.

### Coverage
Clothing/armor property representing weather protection.

### Wetness
State representing water/rain exposure affecting cold systems in some survival mods.

### Shelter
Environmental classification indicating protection from weather/exposure.

### Heat source
Campfire/interior/keyword/reference that reduces cold/exposure.

### Food satiation
Magnitude/duration of hunger relief.

### Sleep debt
Accumulated fatigue debt.

### Survival clock
Game-time-driven update system evaluating needs.

### Needs tick
Periodic update evaluating survival state.

### Environment sampling
Reading weather, region, altitude, water, shelter, temperature or nearby fires.

## Official Survival Mode

### Survival Mode
Bethesda Creation adding hunger, fatigue, cold/exposure and travel/disease changes.

### Survival enabled
Game setting/state toggling official mode.

### Warmth rating
Armor/clothing survival statistic.

### Cold region
Area/weather classification contributing cold.

### Freezing water
Water exposure producing severe cold/health consequences under Survival Mode.

### Hunger penalty
Player state effects based on food need.

### Fatigue penalty
Player state effects based on sleep need.

### Disabled fast travel
Core Survival Mode rule restricting ordinary map fast travel.

### Level-up on sleep
Survival rule requiring sleep to complete level-up.

### Carry-weight reduction
Survival rule modifying player carry capacity.

### Disease severity
Survival-oriented disease interaction.

### Survival UI
HUD/status icons/messages displaying hunger/cold/fatigue.

### Survival compatibility patch
Mod adjusting food, armor warmth, regions, races or other content so it participates in official Survival Mode.

## Campfire

### Campfire
Chesko framework/mod providing camping, placeable fires/tents and extensibility used by survival mods including Frostfall.

### Campfire framework
Papyrus/native/resource layer exposing camping objects, perk/skill style systems and APIs to add compatible equipment/features.

### Campfire object
Placeable campsite element.

### Campfire fire
Heat/light/cooking source with lifecycle/fuel state.

### Fuel
Resource consumed to build/maintain fire.

### Tent
Placeable shelter providing sleep/survival effects.

### Placement system
World interaction allowing player to position camp objects before construction.

### Campfire skill
Custom progression/perk mechanism used by framework.

### Campfire Dev Kit
Authoring resources/API for third-party Campfire-compatible mods.

### Equipment profile
Framework registration/data describing warmth/coverage or camping equipment integration.

## Frostfall

### Frostfall
Exposure/hypothermia survival mod built around temperature, weather, wetness, clothing and camping integration.

### Exposure
Primary cold-risk value.

### Exposure rate
Rate at which exposure increases/decreases.

### Exposure protection
Combined resistance from clothing, race, effects and environment.

### Hypothermia stage
Progressive penalties at higher exposure.

### Wetness
Water/rain state increasing exposure rate.

### Temperature
Environment value derived from region/weather/time/altitude/interior and compatibility data.

### Frostfall region data
Compatibility metadata classifying worldspace/regions for temperature.

### Interior classification
Warm/cold/sheltered interior behavior.

### Frostfall compatibility framework
Mechanism used to adjust temperature/weather support for other climate/world mods.

### Exposure pause
Framework behavior suspending exposure during selected contexts such as dialogue.

### Death by Exposure
Optional lethal consequence at severe exposure.

## Compatibility patterns

### Food keyword integration
Needs system recognizes foods through keywords/form lists/runtime classification.

### Armor warmth integration
Armor receives warmth/coverage metadata through records/config/scripts/framework.

### Race survival modifier
Vampires/werewolves/custom races receive special hunger/cold behavior.

### Weather integration
Climate/weather overhaul changes environment classification and needs compatibility data.

### Worldspace integration
Custom worldspaces require climate/exposure metadata.

### Interior warmth patch
Player homes/dungeons may need explicit shelter/temperature classification.

### Survival-system overlap
Two frameworks independently apply hunger/cold/fatigue penalties and double-count the same need.

### Needs disable patch
Patch disabling one dimension so two survival mods can coexist without duplicates.

### Fast-travel conflict
Survival mod blocks travel while another mod/menu enables alternative travel system.

## Script/performance design

### Time-based update
Needs calculated from elapsed game time rather than frame-by-frame loops.

### Catch-up calculation
Framework processes needs accrued while sleeping/waiting/fast traveling/loading.

### Paused context
Menus/dialogue/loading where survival timers may pause or catch up.

### Location-change refresh
Recalculate environment when player enters new cell/location.

### Weather-change refresh
Recalculate on weather transition.

### Equipment-change refresh
Recalculate warmth/coverage after armor changes.

### Condition spell
Ability/effect used to represent survival state penalties instead of constant script stat writes.

## Diagnostic rules

1. Identify which mod owns each dimension: hunger, fatigue, cold, wetness, camping and travel.
2. Survival bugs often involve time/weather/location/equipment events rather than simple load-order conflicts.
3. Custom worldspaces and weather mods need environment integration.
4. Established saves persist survival globals/quests; uninstalling mid-save can leave state.
5. Do not run per-frame Papyrus polling for slow-moving needs when game-time/event-driven updates suffice.
6. Fast-travel restriction and teleport/travel mods are separate systems.
7. Race transformations can require re-evaluation of survival immunities/modifiers.

## Sources

- Campfire upstream: https://github.com/chesko256/Campfire
- Frostfall historical/current source materials within Campfire repository: https://github.com/chesko256/Campfire
- Official Survival Mode description/Creation ecosystem: Bethesda Creations documentation and Survival Mode Creation
- Creation Kit events/API for sleep, location, weather/equipment state: https://ck.uesp.net/wiki/Category:Scripting

## Provenance note

Campfire/Frostfall are historically influential frameworks and their documentation may target older runtime/tool generations, but their architecture remains important to understanding survival mod compatibility. Exact modern DLL/script patches should be version-checked.
