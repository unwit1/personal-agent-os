# Skyrim Modding Terminology — Followers, Relationships, Favor, and Companion AI

Imported: 2026-09-24
Status: sourced deep-ingestion pass 13

## Relationship system

### Relationship / RELA
Record defining directional/bidirectional relationship rank and association between two actors.

### Relationship rank
Engine integer describing hostility/friendship/favor levels used by dialogue, marriage, follower and AI conditions.

### Enemy
Negative relationship state.

### Rival
Negative relationship state less severe than enemy depending on system.

### Acquaintance
Neutral/basic relationship.

### Friend
Positive relationship.

### Confidant
Higher positive relationship.

### Ally
High positive relationship.

### Lover
Highest relationship tier used by marriage/romance conditions.

### SetRelationshipRank
Papyrus operation changing relationship rank at runtime.

### GetRelationshipRank
Reads relationship rank.

### AssociationType
Semantic label such as parent/child/spouse/sibling/etc. attached to RELA.

### Family relationship
Relationship APIs evaluating family association.

## Favor system

### Favor
Vanilla system for NPC requests, dialogue services and relationship progression.

### Favor points
Numeric favor state.

### ModFavorPoints
Papyrus adjustment.

### ModFavorPointsWithGlobal
Adjusts favor with global multiplier/state.

### Doing favor
Actor state while executing favor interaction.

### SetDoingFavor
Controls favor-state flag.

### No Favor Allowed
Actor state blocking favor requests.

### Persuasion
Speech check outcome modifying dialogue/favor.

### Intimidation
Speech/level/personality check.

### Bribe
Gold payment for dialogue/favor outcome.

### Favor dialogue
Dialogue branches conditioned on favor state/relationship.

## Vanilla follower system

### DialogueFollower quest
Vanilla/default-object follower dialogue/management quest.

### PotentialFollowerFaction
Faction used to mark actors eligible for vanilla follower recruitment.

### CurrentFollowerFaction
Faction/rank commonly tracking active follower state.

### Follower alias
Quest alias holding current follower.

### Follower package
Alias package causing follower to follow player.

### Follower wait
Follower AI/package state waiting at a location.

### Follower distance
Near/medium/far following package parameters.

### Follower inventory
Actor inventory exposed through follower trade dialogue.

### Follower teammate
PlayerTeammate state granting teammate combat/UI behavior.

### SetPlayerTeammate
Papyrus function changing teammate state.

### Essential/protected follower
Actor protection configuration preventing accidental death according to mod design.

### Follower dismissal
Quest/dialogue logic clearing aliases/factions/packages and returning actor to home/default package.

### Follower home
Editor/reference/location to which follower returns after dismissal.

### Follower sandbox
Package used while waiting/at home.

### Hireling
Follower requiring payment, typically managed through hireling quest/dialogue state.

### Housecarl
Vanilla follower role assigned by hold/Thane quests.

### Animal follower
Separate vanilla follower slot/quest architecture for pets/animals.

## Companion framework concepts

### Multi-follower framework
Mod replacing/extending vanilla single-follower management with additional aliases/packages/state.

### Framework-managed follower
Actor taken over by a follower framework; direct manipulation of vanilla follower factions/aliases can conflict.

### Import follower
Framework operation taking control of an actor originally authored with vanilla/custom follower logic.

### Custom follower framework
Follower mod with its own quest/package/dialogue system not intended to be imported into generic frameworks.

### Standalone follower
Mod-added NPC with independent assets/dialogue/quest, sometimes using vanilla follower system and sometimes custom.

### Follower AI package stack
Combination of actor base packages, quest alias packages, combat overrides and framework packages.

### Follower command mode
State allowing player to direct follower to move/use/interact.

### Wait state
Framework/vanilla state suspending normal following.

### Teleport catch-up
Framework moves distant/stuck follower near player.

### Summon follower
Scripted teleport of companion to player.

### Outfit management
Framework system controlling follower worn outfit separately from ordinary inventory.

### Follower mount
Framework support for follower horses/mount behavior.

### Follower stealth
Framework AI controls for sneak/invisibility/combat engagement.

## Marriage

### PotentialMarriageFaction
Faction making NPC eligible for vanilla marriage dialogue under appropriate relationship/quest conditions.

### RelationshipMarriage quest
Vanilla marriage ceremony/state quest family.

### Spouse
Actor stored by marriage quest/relationship state.

### Spouse home
Player-selected household to which spouse moves.

### Marriage dialogue
Dialogue gated by amulet/relationship/quest state.

### Marriage compatibility
Follower mods with custom dialogue/quests may need explicit marriage support rather than only faction addition.

## Common failure modes

### Follower won't follow
Recruitment dialogue ran but follower alias/faction/package not filled/active.

### Follower stuck waiting
Wait package/state not cleared after dialogue/framework event.

### Follower returns home
Follow quest stopped/dismissed or higher-priority home/default package wins.

### Duplicate follower management
Generic framework and custom follower's own quest both manipulate packages/factions.

### Missing trade dialogue
Follower faction/alias/dialogue conditions not satisfied.

### Custom follower broken by import
Generic follower framework overwrote assumptions of custom quest/AI.

### Lost follower
Alias/reference remains valid but actor pathing/cell state leaves them far away; distinguish from deleted/missing reference.

## Diagnostic rules

1. Vanilla follower eligibility, active follower alias, faction state and teammate flag are separate.
2. Custom followers may not be safe to import into multi-follower frameworks.
3. Alias packages often override NPC base packages while follower quest is running.
4. Follower pathing failures can be navmesh issues rather than follower quest bugs.
5. Dismissal must clear every framework-owned state it established.
6. Marriage eligibility is not equivalent to follower eligibility.
7. Established saves preserve quest aliases/faction/package state across mod updates.

## Sources

- Creation Kit Wiki DefaultObjectManager — DialogueFollower/PotentialFollower references: https://ck.uesp.net/wiki/DefaultObjectManager_Script
- Creation Kit Wiki Creating Custom Couriers for alias/package patterns: https://ck.uesp.net/wiki/Creating_Custom_Couriers
- Creation Kit Wiki scripting category for relationship/teammate/favor APIs: https://ck.uesp.net/wiki/Category:Scripting
## Native relationship-level enum — CommonLibSSE-NG

Source: `include/RE/B/BGSRelationship.h` blob `c75028ab4dafc2f08147b85fc79f1ed40f631959`.

| Native value | Relationship level |
|---:|---|
| 0 | Lover |
| 1 | Ally |
| 2 | Confidant |
| 3 | Friend |
| 4 | Acquaintance |
| 5 | Rival |
| 6 | Foe |
| 7 | Enemy |
| 8 | Archnemesis |

Current CommonLib also exposes relationship `Secret = 1 << 7`, save ChangeFlag `RelationshipData = 1 << 1`, and record flags `Deleted = 1 << 5`, `Secret = 1 << 6`, `Ignored = 1 << 12`.

### Static relationship vs saved runtime state

A `RELA` form links two NPC_ bases, an AssociationType, and a relationship level. Runtime APIs such as `SetRelationshipRank` can alter relationship state in an established save. Therefore:

1. the static RELA record is not necessarily the final relationship observed in a save;
2. relationship level is separate from faction reaction (`Neutral/Enemy/Ally/Friend`);
3. relationship rank is separate from follower alias/faction/teammate state;
4. patching RELA does not automatically clear a saved relationship override.

