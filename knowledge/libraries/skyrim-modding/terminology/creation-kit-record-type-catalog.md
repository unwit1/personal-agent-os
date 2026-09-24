# Skyrim Modding Reference — Creation Kit and xEdit Record-Type Catalog

Imported: 2026-09-24
Status: broad reference catalog

This catalog is intended as a lookup map, not a substitute for each record's field schema. It tells Agent OS what major Skyrim records represent and what other layers commonly interact with them.

## Actors and character data

### NPC / NPC_
Actor base definition: identity, race, class, stats, factions, inventory, AI, packages, spells/perks, appearance/head data and templates.

### RACE
Race definition: body/head data, skeleton/model relationships, movement, spells, attacks, voices, morph/headpart compatibility and race flags.

### CLAS / Class
Class metadata including skills/training/service-related actor defaults.

### CSTY / CombatStyle
AI combat weighting/tactical parameters.

### FACT / Faction
Membership/ranks, relationships, crime/legal data, vendor/service and condition use.

### RELA / Relationship
Relationship between two actors and rank/association data.

### ASTP / AssociationType
Semantic relationship category such as parent/child/friend-like association used by relationship queries.

### VTYP / VoiceType
Voice category controlling dialogue voice availability/path and actor speech identity.

### HDPT / HeadPart
Hair/eyes/brows/scars/facial hair and other head component definitions.

### OTFT / Outfit
Item list assigned as actor outfit.

## Items and equipment

### WEAP / Weapon
Weapon gameplay/model/equip/sound/critical data.

### ARMO / Armor
Wearable inventory record with armor rating, slots, keywords and linked ArmorAddons.

### ARMA / ArmorAddon
Race/sex/body model data that actually renders equipped armor geometry.

### AMMO / Ammo
Ammunition item linked to a Projectile, damage and model/sound data.

### BOOK / Book
Readable item; can teach spell/skill or behave as ordinary book.

### ALCH / Ingestible/Potion
Potion, poison, food and other ingestible item with effects.

### INGR / Ingredient
Alchemy ingredient with discoverable effect list.

### SCRL / Scroll
Castable consumable magic item.

### SLGM / SoulGem
Soul gem capacity/value/soul-state data.

### KEYM / Key
Key item used by locks/conditions/scripts.

### MISC / MiscObject
General inventory object such as clutter/currency/materials.

### APPA / Apparatus
Alchemy apparatus class retained in scripting/data ecosystem though Skyrim's usage differs from earlier games.

## Magic and abilities

### SPEL / Spell
Spell/ability/power/disease form containing Effect Items.

### MGEF / MagicEffect
Native/script effect definition and archetype.

### ENCH / Enchantment
Effect list for weapon/armor enchantment behavior.

### SHOU / Shout
Shout form linking Words of Power and spells.

### WOOP / WordOfPower
Word-of-power data used by shouts.

### PERK / Perk
Conditions and perk entries modifying engine calculations/abilities.

### AVIF / ActorValueInfo
Metadata for actor values/skills/perk-tree presentation.

## Projectiles and impact effects

### PROJ / Projectile
Projectile flight/model/collision/explosion/impact behavior for arrows, missiles, beams, flames/cones and related classes.

### EXPL / Explosion
Area explosion/effect definition triggered by projectiles, activators, magic or scripts.

### HAZD / Hazard
Persistent area hazard that can apply spells/effects over time and be spawned by MagicEffect archetypes/scripts.

### IPCT / ImpactData
Visual/audio/decal behavior for one impact type/material interaction.

### IPDS / ImpactDataSet
Maps material/contact categories to ImpactData selections.

### ARTO / ArtObject
Visual art/model effect attached to magic/casting/hit systems.

### EFSH / EffectShader
Shader/visual effect applied to references/actors for magic/status effects.

## World objects

### STAT / Static
Non-interactive model placed in world.

### MSTT / MovableStatic
Static-like object with movable/runtime behavior.

### ACTI / Activator
Interactive world object supporting activation and scripts.

### TACT / TalkingActivator
Activator capable of dialogue/VoiceType behavior.

### DOOR / Door
Door object; placed door refs can teleport/link to other doors/cells.

### CONT / Container
Base container inventory/object definition.

### FURN / Furniture
Furniture markers/animations/entry points such as chairs, beds, crafting stations.

### FLOR / Flora
Harvestable flora base.

### TREE / Tree
Tree base object used by tree rendering/LOD/harvesting configurations.

### GRAS / Grass
Procedurally placed landscape grass object, distinct from TREE/FLOR placed refs.

### LIGH / Light
Light source parameters/model/color/radius/shadow behavior.

### IDLM / IdleMarker
Placed marker causing nearby actors/AI to use selected idle animations.

## World/cell data

### WRLD / Worldspace
Exterior world container, map/climate/water/LOD/child cells.

### CELL
Interior or exterior cell data and child reference/navmesh groups.

### LAND
Exterior terrain heights/textures/vertex data.

### LTEX / LandTexture
Landscape texture definition linking material/texture/grass data.

### REGN / Region
Worldspace region controlling weather, map/object/grass/sound and related regional generation/data.

### WATR / WaterType
Water visual/physical/sound properties.

### CLMT / Climate
Weather selection and daylight timing for worldspace.

### WTHR / Weather
Sky/cloud/fog/light/precipitation/colors/ambient outdoor state.

### NAVM / NavMesh
Actor navigation triangles/connectivity.

### ECZN / EncounterZone
Encounter level/reset/combat-zone behavior assigned to cells/locations.

### LCTN / Location
Hierarchical semantic place data.

### LCRT / LocationRefType
Semantic role tag for placed references inside Locations.

## Placement/reference records

### REFR / ObjectReference
Placed/runtime instance of most non-actor base objects.

### ACHR / ActorReference
Placed actor/NPC reference.

### PGRE / PlacedGrenade
Projectile-like placed reference type used in Bethesda formats where applicable.

### PMIS / PlacedMissile
Placed missile/projectile reference type recognized by modern xEdit schemas.

### PARW / PlacedArrow
Placed arrow/projectile reference type in applicable runtime/plugin data.

### PBAR / PlacedBarrier
Placed barrier/projectile-derived reference category where present.

### PHZD / PlacedHazard
Placed/runtime hazard reference category where present.

## Quests, dialogue and scenes

### QUST / Quest
Stateful quest/manager record with aliases, stages, objectives, scripts, dialogue/scenes.

### DIAL / Topic
Dialogue topic container.

### INFO / TopicInfo
Individual dialogue response and conditions/fragments.

### DLVW / DialogueView
Creation Kit organizational/view data for visual dialogue authoring.

### SCEN / Scene
Quest-owned multi-actor/action orchestration.

### PACK / Package
Actor AI behavior procedure tree/data/conditions.

### DLBR / DialogueBranch
Dialogue branch/entry grouping.

## Lists, globals, classification and recipes

### KYWD / Keyword
Reusable semantic tag used across forms/conditions/frameworks.

### FLST / FormList
Persistent list of arbitrary forms.

### LVLI / LeveledItem
Leveled item list.

### LVLN / LeveledActor
Leveled NPC/creature list.

### LVSP / LeveledSpell
Leveled spell list.

### GLOB / GlobalVariable
Numeric global form usable by conditions/scripts.

### COBJ / ConstructibleObject
Crafting/tempering recipe.

### EQUP / EquipType
Defines supported hand/equip slots/type behavior for items/spells.

### DOBJ / DefaultObject
Game-default object slot assignment referenced by engine systems.

### DOBJ manager
Collection/mapping of engine-known default objects, exposed through DefaultObjectManager APIs.

## Graphics and materials

### TXST / TextureSet
Record listing texture paths used for record-level alternate textures.

### MATO / MaterialObject
Material-related object data used by certain debris/impact/world systems.

### MATT / MaterialType
Physical material classification used by impact/collision/sound systems.

### IMGS / ImageSpace
Cell/camera post-processing settings.

### IMAD / ImageSpaceModifier
Temporary/dynamic post-processing modifier.

### EYES / Eyes
Legacy/game-specific eye data record family; Skyrim primarily exposes eye selection through HeadParts/Race systems, but xEdit schemas can show historical/signature relationships depending on game.

### DUAL / DualCastData
Supporting magic/dual-casting data where represented in game schemas.

## Sound and music

### SNDR / SoundDescriptor
Sound definition/source playback data.

### SOUN / Sound
Older/underlying sound record family; exact usage varies by Bethesda format generation.

### MUSC / MusicType
Conditional/category music playlist/control record.

### MUST / MusicTrack
Track-level music data in relevant schema.

### SNCT / SoundCategory
Mixer/category hierarchy and volume behavior.

### SOPM / SoundOutputModel
Spatialization/attenuation/output model.

### REVB / ReverbParameters
Reverb acoustic settings.

## Messages and UI-facing game data

### MESG / Message
Message box/notification/help text and buttons.

### LSCR / LoadScreen
Loading-screen model/text/conditions.

### GMST / GameSetting
Engine/game tuning setting stored in plugin data.

### CPTH / CameraPath
Camera path record for scripted/cinematic camera behavior where used.

### CAMS / CameraShot
Camera-shot behavior record.

## Record relationships and patching notes

### Base vs reference
Base records define what an object is; REFR/ACHR/etc. define one placed instance.

### Parent vs child record
WRLD/CELL/QUST and similar records own nested child records/groups. A “parent conflict” can differ from conflicts in child references.

### Template inheritance
NPCs, packages and other record families can inherit data from templates. Visible effective behavior may not be stored directly on the child record.

### Runtime-derived behavior
Some records are inputs to native systems; changing one field may influence behavior through hard-coded rules not expressible by the record alone.

### Schema-aware patching
Agent OS should retrieve the exact record family before recommending which fields to forward/merge.

## Catalog rules

1. Do not infer semantics solely from four-letter signature.
2. Use xEdit current schema for exact fields/subrecords.
3. Use CK documentation/game tests for behavioral meaning.
4. Base/ref distinction is mandatory in troubleshooting.
5. Asset paths often live in records but actual file winner is a separate VFS/archive layer.
6. Runtime frameworks can mutate many record families after xEdit-visible data loads.
7. Save ChangeForms can override/reference current defaults for specific forms.
8. Every automated patcher should declare which record signatures it reads/writes.
9. Unknown or game-version-specific records need source validation before modification.
10. Extend this catalog when xEdit adds/revises Skyrim record decoding.

## Sources
- xEdit/TES5Edit current schemas and source: https://github.com/TES5Edit/TES5Edit
- Tome of xEdit: https://tes5edit.github.io/docs/
- Creation Kit Wiki object/scripting references: https://ck.uesp.net/wiki/Category:Scripting
