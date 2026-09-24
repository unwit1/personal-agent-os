# Skyrim Modding Terminology — Crime, Ownership, Merchants, and Economy

Imported: 2026-09-24
Status: sourced deep-ingestion pass 11

## Ownership

### Ownership
Game data determining whether a reference/container/item belongs to an actor or faction and whether taking/using it constitutes theft/trespass.

### Actor owner
Specific ActorBase/reference ownership assigned to an object/cell.

### Faction owner
Faction assigned as owner.

### Cell ownership
Ownership inherited/applied to references within a cell depending on record/reference configuration.

### Reference ownership
Ownership set directly on a placed reference.

### SetActorOwner
Papyrus operation changing object/cell ownership to an actor.

### SetFactionOwner
Papyrus operation changing ownership to a faction.

### Stolen item
Inventory item carrying theft ownership metadata relative to player.

### StolenItemValueCrime
Tracked/statistical value of stolen items that contributed to crime.

### StolenItemValueNoCrime
Stolen-item value tracked without a crime event in specific circumstances.

### Trespass
Crime/state resulting from being in restricted owned space when conditions warrant.

### IsTrespassing
Actor condition/API reporting trespass state.

## Crime factions

### Crime faction
Faction that tracks/report crimes and bounty for an actor/region.

### GetCrimeFaction
Actor API returning the faction to which an actor reports crimes.

### SetCrimeFaction
Actor API changing crime-faction association.

### Bounty
Crime gold tracked on a crime faction.

### Crime gold
Total bounty owed to a faction.

### Violent crime gold
Bounty attributed to violent crimes.

### Non-violent crime gold
Bounty attributed to non-violent crimes.

### GetCrimeGold
Faction API returning current bounty.

### ModCrimeGold
Adjust faction bounty.

### SetCrimeGold
Set faction bounty.

### PlayerPayCrimeGold
Faction API/process resolving payment/jail/confiscation options according to parameters.

### Crime group
Related crime-faction system in which factions can share crime relationships.

### IsFactionInCrimeGroup
Condition/API testing crime-group relationship.

### Report crime
Actor/engine action adding crime to player's relevant crime faction.

### Alarm
Actor reaction/event that reports crime and alerts guards/NPCs.

### SendAssaultAlarm
Papyrus call reporting assault to relevant systems.

### SendStealAlarm
Reports theft alarm.

### SendTrespassAlarm
Reports trespass.

### Arrest
Guard/crime system transition where actor attempts to arrest player.

### IsArrested
Actor state indicating arrest condition.

### Jail
Crime-resolution state sending player to faction/hold jail.

### ServeTime
Game/Papyrus operation processing jail sentence.

### Confiscation
Removal/storage of stolen or player items during arrest/jail according to crime system.

## Faction relations

### Faction
Actor grouping with membership ranks, reactions, crime behavior, vendor/service roles and conditions.

### Faction rank
Numeric membership rank.

### Faction reaction
Friendly/ally/enemy relationship between factions.

### SetAlly
Define allied relationship.

### SetEnemy
Define enemy relationship.

### ModReaction
Adjust faction reaction values.

### Player faction
Default-object faction representing player.

### Guard faction
Default-object guard faction used by engine systems.

### Vendor faction
Faction/keyword/data relationship controlling merchant behavior in some vanilla setups.

## Merchants

### Merchant
Actor whose dialogue/package/faction/container setup enables barter.

### ShowBarterMenu
Papyrus/API operation opening barter interface with a merchant.

### Merchant container
Hidden/reference container storing a vendor's sale inventory/gold separately from visible actor inventory.

### Vendor gold
Currency available to merchant for purchases from player.

### Vendor inventory
Items exposed for sale based on merchant container/faction/list rules.

### Vendor chest
Common community term for merchant container.

### Respawning merchant inventory
Merchant container/list content refreshed according to cell/container/merchant reset behavior.

### Buy/sell filter
Vendor faction/list/keyword restrictions determining which item categories merchant accepts.

### VendorItem keyword
Keyword families classifying sellable categories in vanilla merchant systems.

### Leveled vendor inventory
Leveled lists inside merchant container determining stock by level/chance.

### Merchant reset
Refresh of container gold/stock after game-time/reset interval.

### Barter price
Final buy/sell price after base value, Speech, perks, disposition and game settings.

### Base gold value
Form monetary value before barter modifiers.

### Speech modifier
Speechcraft/perk contribution to price.

### Buy price
Gold player pays.

### Sell price
Gold merchant pays.

### Favor cost
Relationship/favor-related economic value separate from merchant barter.

## Services and dialogue

### Service flags
Actor/faction/service metadata enabling barter/training/other services.

### Trainer
Actor configured to train one skill to a maximum training level.

### Training menu
UI/service opened through ShowTrainingMenu or dialogue.

### Gift menu
Inventory transfer UI used in follower/relationship contexts.

### Favor
System tracking NPC favor points/disposition and enabling favor dialogue/actions.

### Bribe
Dialogue/crime/favor action spending gold to alter outcome.

### Intimidation
Dialogue/favor action resolved through actor/player values and conditions.

### Persuasion
Dialogue/favor action using speech/disposition checks.

## Economy modding patterns

### Global price multiplier
Changing Game Settings/perks affecting broad barter economics.

### Item-value rebalance
Static/runtime patch changing base form gold values.

### Merchant-stock injection
Adding items to vendor lists/containers through patches or runtime distributors.

### Merchant-container conflict
Multiple mods overriding same hidden vendor container/leved lists.

### Runtime vendor distribution
Config-driven addition of items/categories to merchants avoiding direct static conflicts where framework supports it.

### Economy overhaul
Coordinated changes to item values, merchant gold, loot, crafting, rewards and barter formulas.

## Diagnostic rules

1. Merchant-visible inventory may come from hidden container, not actor inventory.
2. Ownership and crime faction are distinct; owned item theft can report to actor's relevant crime faction.
3. Changing faction membership can affect crime, hostility, dialogue and merchant behavior simultaneously.
4. Vendor stock issues require checking container/list resets and save-persisted inventory state.
5. Barter price changes can be record, perk entry point, Game Setting or script/runtime patch—not just item base value.
6. Crime/bounty changes are faction-scoped; identify which crime faction actor/hold uses.

## Sources

- CK Wiki GetCrimeFaction: https://ck.uesp.net/wiki/GetCrimeFaction_-_Actor
- CK Wiki GetCrimeGoldNonViolent and related Faction APIs: https://ck.uesp.net/wiki/GetCrimeGoldNonViolent_-_Faction
- CK Wiki scripting API index: https://ck.uesp.net/wiki/Category:Scripting
- CK Wiki DefaultObjectManager: https://ck.uesp.net/wiki/DefaultObjectManager_Script
## Native Faction crime/vendor data — CommonLibSSE-NG

Source: `include/RE/T/TESFaction.h` blob `619fad4d15b1fbc2bff6ae49416787d65b2b54dd`.

### Faction DATA flags

| Flag | Bit |
|---|---|
| HiddenFromNPC | 1 << 0 |
| SpecialCombat | 1 << 1 |
| PlayerIsExpelled | 1 << 2 |
| PlayerIsEnemy | 1 << 3 |
| TrackCrime | 1 << 6 |
| IgnoresCrimes_Murder | 1 << 7 |
| IgnoresCrimes_Assault | 1 << 8 |
| IgnoresCrimes_Stealing | 1 << 9 |
| IgnoresCrimes_Trespass | 1 << 10 |
| DoNotReportCrimesAgainstMembers | 1 << 11 |
| CrimeGold_UseDefaults | 1 << 12 |
| IgnoresCrimes_Pickpocket | 1 << 13 |
| Vendor | 1 << 14 |
| CanBeOwner | 1 << 15 |
| IgnoresCrimes_Werewolf | 1 << 16 |

The current CommonLib identifiers preserve a few historical spelling typos in source; this knowledge entry normalizes their English labels while retaining the source SHA.

## Crime values

Current native `FACTION_CRIME_DATA_VALUES` stores:

- arrest behavior;
- attack-on-sight behavior;
- murder crime gold;
- assault crime gold;
- trespass crime gold;
- pickpocket crime gold;
- stealing gold multiplier;
- escape-jail crime gold;
- werewolf crime gold.

### Crime infrastructure references

`FACTION_CRIME_DATA` also links:
- jail marker;
- wait marker;
- stolen-items container;
- player inventory container;
- crime group FormList;
- jail outfit.

This is why crime behavior is not reducible to one bounty number.

## Vendor data

Current `FACTION_VENDOR_DATA_VALUES` includes:
- start hour;
- end hour;
- location radius;
- buys stolen;
- not buy/sell;
- buys non-stolen.

`FACTION_VENDOR_DATA` adds:
- vendor location;
- vendor conditions;
- vendor buy/sell FormList;
- merchant container;
- last reset day.

### Merchant-container distinction

A faction/vendor can be configured correctly while a merchant still appears empty or stale if:
- the merchant container is wrong/missing;
- the vendor location/conditions fail;
- the container has not reset;
- runtime inventory state/save changes override expectations.

## Faction save ChangeFlags

Current CommonLib exposes:
- `FactionFlags = 1 << 1`
- `FactionReactions = 1 << 2`
- `FactionCrimeCounts = 1 << 31`

Faction crime/reaction state can therefore persist independently from the static FACT record.

## Native faction operations

Current CommonLib exposes native operations for:
- crime gold totals, violent/nonviolent splits and infamy;
- stolen item values;
- ignore-crime tests;
- crime-group membership;
- player enemy/expelled state;
- vendor/owner/service checks;
- modifying and paying crime gold;
- sending player to jail;
- setting ally/enemy/fight reactions.

## Compatibility rules

1. `Vendor`, `CanBeOwner`, and `TrackCrime` are independent faction capabilities.
2. Crime ignore flags are per category; “ignores crimes” is not one Boolean.
3. Vendor faction data and the NPC's AI/package/service availability both matter.
4. Faction reactions, actor relationships, and runtime combat hostility are separate systems.
5. Static FACT patching does not automatically clear saved crime counts/reaction state.
6. Ownership of one inventory instance/reference can still be overridden by ExtraOwnership even when faction ownership is configured.

