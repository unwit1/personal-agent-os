# Skyrim Mod Factory — Mod Archetype Playbooks

Created: 2026-09-24

These playbooks let Agent OS map a new idea to likely implementation layers, tools, checks and tests before asking low-level questions.

## 1. Balance/stat overhaul

Likely:
- plugin records;
- Synthesis/Mutagen for mass edits;
- perks/Entry Points;
- MGEF/SPEL/WEAP/ARMO/AVIF/CSTY.

Prefer:
- deterministic generated records;
- rule tables over hand-edited hundreds of forms.

Checks:
- field ownership;
- leveled variants;
- perk interactions;
- displayed vs effective values;
- Simonrim conventions if project targets Simonrim.

Tests:
- representative low/mid/high values;
- player/NPC;
- enchanted/tempered item;
- perk/no perk.

## 2. Item/loot/distribution mod

Choose among:
- static LVLI/LVLN patch;
- Synthesis load-order patch;
- SPID;
- SkyPatcher;
- container/outfit edits.

Questions to resolve internally:
- actor vs base NPC;
- chance/level/filter semantics;
- duplicate distribution;
- persistence.

Checks:
- leveled-list merge;
- recipient count;
- deterministic seed assumptions;
- merchant/container propagation.

## 3. NPC gameplay overhaul

Layers:
- NPC_;
- factions/perks/spells/packages/outfits;
- combat style;
- runtime distribution.

Avoid whole-record NPC copying.

Always separate:
- gameplay fields;
- appearance fields;
- FaceGen assets.

Tests:
- unique NPC;
- templated NPC;
- leveled actor;
- respawn;
- follower;
- hostile actor.

## 4. NPC appearance / replacer

Likely:
- NPC_ appearance fields;
- HDPT;
- texture/mesh assets;
- FaceGen;
- optional custom race/hair dependencies.

Checks:
- final NPC winner matches FaceGeom/FaceTint;
- weight/race/headparts coherent;
- no gameplay field regression.

Tests:
- new game;
- existing save appearance reset implications;
- vampire/transformation if relevant.

## 5. Armor/outfit/body mod

Layers:
- ARMO;
- ARMA;
- NIF;
- TRI;
- skeleton;
- BodySlide.

Checks:
- slot masks;
- partitions;
- race/additional races;
- _0/_1;
- weights;
- morphs;
- first/third person;
- texture paths.

Tests:
- male/female;
- body weight extremes;
- common body presets;
- crouch/combat;
- first person if applicable.

## 6. Weapon mod

Layers:
- WEAP;
- model;
- equip type;
- animation type;
- enchantment;
- sound/impact;
- optional OAR/Pandora.

Checks:
- base stats;
- collision;
- grip/node placement;
- enchant charge;
- temper recipe;
- first-person model.

## 7. Spell/magic mod

Layers:
- SPEL;
- MGEF;
- PERK;
- projectile/explosion/ARTO/EFSH;
- Papyrus/native if custom behavior.

Checks:
- archetype;
- cast type;
- delivery;
- resist;
- base cost;
- conditions;
- visuals/assets.

Tests:
- dual cast;
- concentration/fire-and-forget;
- NPC use;
- immunity/resistance;
- save/load if scripted effect.

## 8. Perk/progression mod

Layers:
- PERK;
- Entry Points;
- AVIF;
- conditions;
- UI/skill tree;
- Custom Skills if new tree.

Checks:
- condition CTDAs;
- rank chain;
- Entry Point stacking;
- skill XP math;
- legendary behavior.

## 9. Quest/dialogue mod

Require:
- QUST;
- aliases;
- Story Manager if event-started;
- DIAL/INFO;
- SCEN;
- VMAD fragments;
- voice assets.

Prefer CK/CKPE authoring for complex relationships.

Checks:
- alias IDs;
- fill;
- stage flow;
- fragments compile;
- dialogue conditions;
- voice path.

Tests:
- each branch;
- fail/alternate conditions;
- save/reload mid-scene;
- cell unload;
- actor death.

## 10. Follower mod

Layers:
- NPC;
- relationship/faction;
- packages;
- quest aliases;
- dialogue;
- outfit;
- optional custom framework.

Checks:
- follower framework compatibility;
- dismissal/home;
- bleedout/protected flags;
- package overrides;
- sandbox;
- mount/wait.

## 11. Combat mechanics mod

Choose:
- perks/Entry Points for stat formula;
- Papyrus for event gameplay;
- native for hit timing/engine hooks;
- Precision for collision;
- OAR/Pandora/MCO/SCAR ecosystem for animation/AI.

Tests:
- player/NPC;
- block/bash/power attack;
- dual wield;
- ranged/magic;
- slow time;
- high actor count.

## 12. Animation replacer

Use OAR first.

Generate:
- submod hierarchy;
- priorities;
- conditions;
- paths.

Check:
- condition collisions;
- first/third person;
- gender/race;
- weapon type;
- state transitions.

## 13. New animation behavior

Use Pandora-compatible behavior patch when graph structure changes.

Check:
- graph target;
- patch identifiers;
- events;
- output;
- skeleton;
- OAR/AMR/Payload integration.

## 14. UI/MCM mod

Layers:
- SkyUI MCM;
- Scaleform;
- native menu;
- PrismaUI/HTML if selected;
- Input.

Checks:
- exact menu identifiers;
- text input;
- gamepad;
- VR;
- localization;
- settings persistence.

## 15. Native SKSE plugin

Start with:
- CommonLibSSE-NG project;
- runtime matrix;
- Address Library;
- logging;
- versioned serialization;
- unit-testable core separated from hooks.

Checks:
- all build targets;
- relocations;
- interface versions;
- thread/lifetime safety;
- load lifecycle;
- crash logging symbols.

## 16. Worldspace/location mod

Layers:
- WRLD/CELL;
- REFR;
- LAND;
- NAVM;
- LCTN;
- water;
- portals/rooms;
- LOD.

Require CK/game visual/pathing review.

Generate:
- conflict patch;
- LOD invalidation list;
- navmesh test route.

## 17. Interior overhaul

Special risks:
- Room Bounds;
- Portals;
- navmesh;
- lighting;
- occlusion;
- door links.

Tests:
- every doorway;
- NPC traversal;
- combat;
- camera angles;
- lighting from multiple positions.

## 18. Landscape/grass/road mod

Layers:
- LAND;
- landscape textures;
- navmesh;
- grass;
- terrain LOD.

Checks:
- vertex/texture conflicts;
- no-grass exclusions;
- seam fixtures;
- regenerated terrain LOD.

## 19. Weather/lighting/rendering mod

Layers:
- WTHR;
- CLMT;
- LGTM;
- IMGS;
- lights;
- Community Shaders/ReShade/materials.

Tests:
- time of day;
- interiors/exteriors;
- weather transition;
- water;
- snow/fog;
- first-person;
- screenshots with controlled exposure.

## 20. Survival/economy mod

Layers:
- GMST;
- perks;
- magic effects;
- vendor factions;
- recipes;
- scripts;
- UI.

Tests:
- time scale;
- sleeping/waiting;
- fast travel;
- crime;
- vendor reset;
- save/load.

## 21. Creature/race mod

Layers:
- RACE;
- skeleton;
- behavior project;
- animations;
- attack data;
- BPTD;
- sounds;
- NPC/leveled actors.

Checks:
- behavior graph;
- skeleton nodes;
- attack events;
- ragdoll/collision;
- decapitation/body parts.

## 22. VR mod

Require explicit VR architecture:
- SKSEVR;
- VR Address Library;
- VRIK/HIGGS/PLANCK interactions;
- HMD/controller input;
- camera state differences.

Never infer flat-screen camera/input semantics apply.

## 23. Compatibility patch

Inputs:
- exact source versions;
- field-level intended winners;
- runtime mutators;
- assets;
- save state.

Prefer generated Synthesis patch when conflict logic can be generalized.

## 24. Framework/library mod

If building a dependency for other mod authors:
- version API;
- capability detection;
- semantic version policy;
- graceful missing/old version behavior;
- documentation;
- sample consumer;
- compatibility tests across runtimes.

## Universal outputs for every archetype

Agent should produce:
- manifest;
- architecture note;
- source lock;
- generated artifacts;
- validation report;
- compatibility touch set;
- regression fixtures;
- release notes.
