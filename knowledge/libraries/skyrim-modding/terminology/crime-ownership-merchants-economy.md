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
