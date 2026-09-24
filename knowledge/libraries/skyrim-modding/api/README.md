# Skyrim Modding API Catalogs

Updated: 2026-09-24

## Source-level coverage summary

| Provider | Source representation | Coverage |
|---|---|---:|
| SKSE64 | modified PSC source | 62 scripts / 1,161 declarations |
| powerofthree's Papyrus Extender | PSC source | 8 scripts / 703 declarations |
| PapyrusUtil | PSC source | 6 scripts / 538 declarations |
| JContainers | current C++ Papyrus registration metadata | 189 registration statements |

These catalogs are provider/version scoped. They are evidence of the source API surface at the recorded snapshot, not proof that a user's installed runtime has loaded every native function successfully.

## SKSE64 modified Papyrus source

Coverage: **62 PSC scripts / 1,161 extracted declarations**.

Source: https://github.com/ianpatt/skse64 · `scripts/modified/*.psc` at the 2026-09-24 ingestion snapshot.

Each shard records the exact **blob SHA for every PSC**, which is the canonical source provenance even if upstream `master` later moves.

> These are full modified PSC surfaces, not an “SKSE additions only” diff. They include vanilla declarations retained in SKSE's modified source plus SKSE extensions.

| Shard | Scripts | Declarations | Script types |
|---|---:|---:|---|
| [skse-papyrus-01.md](skse-papyrus-01.md) | 8 | 225 | ActiveMagicEffect, Actor, ActorBase, ActorValueInfo, Alias, Ammo, Apparatus, Armor |
| [skse-papyrus-02.md](skse-papyrus-02.md) | 8 | 108 | ArmorAddon, Art, Book, Camera, Cell, ColorComponent, ColorForm, CombatStyle |
| [skse-papyrus-03.md](skse-papyrus-03.md) | 8 | 116 | ConstructibleObject, DefaultObjectManager, Enchantment, EquipSlot, Faction, Flora, Form, FormList |
| [skse-papyrus-04.md](skse-papyrus-04.md) | 8 | 255 | FormType, Game, GameData, HeadPart, Ingredient, Input, Keyword, LeveledActor |
| [skse-papyrus-05.md](skse-papyrus-05.md) | 8 | 132 | LeveledItem, LeveledSpell, Location, MagicEffect, Math, ModEvent, NetImmerse, ObjectReference |
| [skse-papyrus-06.md](skse-papyrus-06.md) | 8 | 151 | Outfit, Perk, Potion, Quest, Race, SKSE, Scroll, Shout |
| [skse-papyrus-07.md](skse-papyrus-07.md) | 8 | 52 | SoulGem, Sound, SoundDescriptor, SpawnerTask, Spell, StringUtil, TextureSet, TreeObject |
| [skse-papyrus-08.md](skse-papyrus-08.md) | 6 | 122 | UI, UICallback, Utility, Weapon, Weather, WornObject |

## powerofthree's Papyrus Extender

[po3-papyrus-extender.md](po3-papyrus-extender.md)

Coverage: **8 PSC scripts / 703 declarations**, including the large `PO3_SKSEFunctions` global-native surface and Form/Alias/ActiveMagicEffect event APIs.

The catalog retains exact source PSC blob SHAs and declaration lines.

## PapyrusUtil

[papyrusutil-api.md](papyrusutil-api.md)

Coverage: **6 PSC scripts / 538 declarations** across:

- StorageUtil;
- JsonUtil;
- ActorUtil;
- ObjectUtil;
- MiscUtil;
- PapyrusUtil.

This is the canonical source-level companion to the persistence/architecture module in `../terminology/papyrusutil-jcontainers-persistent-data.md`.

## JContainers

Current upstream source generates/binds much of its Papyrus API from C++ reflection metadata rather than storing the public J* PSC files as the canonical source surface.

- [jcontainers-collections-databases.md](jcontainers-collections-databases.md) — **149** registration statements across JValue, JArray, JMap, JFormMap, JIntMap, JDB, and JFormDB.
- [jcontainers-utilities.md](jcontainers-utilities.md) — **40** registration statements across JContainers, JLua, JString, and JAtomic.

Total current registration surface cataloged: **189 statements**.

The catalogs preserve source header blob SHAs and exact registration expressions. They intentionally do not invent generated Papyrus return/parameter types when the C++ reflection metadata was not fully resolved.

## Retrieval strategy

For a Papyrus/API question:

1. identify the provider and host class/script;
2. retrieve only the corresponding catalog/shard;
3. use the exact declaration or registration metadata;
4. preserve source blob/commit provenance;
5. distinguish compile-time declaration from runtime registration;
6. cross-check game/SKSE/framework compatibility;
7. consult the relevant terminology module for lifecycle/persistence/semantic caveats.

## API provenance rules

- A **PSC declaration** proves the compile-time script API surface for that source snapshot.
- A **Native PSC function** still depends on a compatible native plugin registering it at runtime.
- A **C++ registration entry** proves a native binding is generated/registered by that source path, but an exact generated PSC signature should not be fabricated if the reflection type mapping has not been resolved.
- A repository `master`/branch name is not immutable; each source file's blob SHA is retained.
- Historical distributed PSCs remain historical evidence when current upstream generation metadata has superseded them.

## Current API frontier

Completed or substantially closed:
- SKSE64 modified PSC catalog — complete for the upstream modified-source tree.
- powerofthree Papyrus Extender PSC catalog — complete for the current upstream PSC tree.
- PapyrusUtil PSC catalog — complete for the current upstream PSC tree.
- JContainers Papyrus registration surface — complete for the current `src/api_3` registration classes.

Remaining:
- matching vanilla PSC baseline and automated SKSE-added diff;
- exact generated JContainers PSC type signatures from the reflection type mapper;
- public PSC/native API surfaces for other major frameworks where source contracts are available;
- version-to-version automated API diffs;
- CommonLib class/member graph generation from pinned Doxygen/source snapshots.

## Generated-data policy

API signature/registration catalogs are compact technical metadata. Full upstream implementations are not mirrored here. Store signatures, registration statements, source identity and line/blob provenance rather than wholesale source bodies.
