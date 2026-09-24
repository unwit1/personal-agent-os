# Skyrim Modding API Catalogs

Updated: 2026-09-24

## SKSE64 modified Papyrus source

Coverage: **62 PSC scripts / 1161 extracted declarations**.

Source: https://github.com/ianpatt/skse64 · `scripts/modified/*.psc` at the 2026-09-24 ingestion snapshot.

Each shard records the exact **blob SHA for every PSC**, which is the canonical source provenance even if the upstream `master` branch later moves.

> These are the full modified PSC surfaces, not an “SKSE additions only” diff. They include vanilla declarations retained in SKSE's modified source plus SKSE extensions.

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

## How to retrieve

For a Papyrus function question:
1. identify the host script type (for example Actor, Game, ObjectReference, Form, UI);
2. use the table above to open only that shard;
3. retrieve the exact declaration and source blob/line;
4. distinguish Native, Global, instance and inherited behavior;
5. cross-check runtime support against SKSE/game version when the function is SKSE-provided.

## Current API frontier

Completed source-level catalog:
- SKSE64 `scripts/modified` — complete.

Next source-level catalogs:
- po3 Papyrus Extender;
- PapyrusUtil;
- JContainers;
- framework-specific PSC APIs where they expose meaningful public contracts;
- matching vanilla PSC baseline so SKSE-added declarations can be diffed automatically.

## Generated-data policy

API signature catalogs are safe, compact technical metadata. Full upstream source bodies are not mirrored here. The catalog stores signatures, source identity and line provenance rather than copying entire implementations.
