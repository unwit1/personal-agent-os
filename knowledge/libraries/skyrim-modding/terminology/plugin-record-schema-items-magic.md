# Skyrim Plugin Record Schema — Items, Magic, Crafting, and Leveled Data

Imported: 2026-09-24
Status: field-level schema deepening

## WEAP

Common fields:
- EDID/FULL;
- model;
- icons;
- enchantment;
- enchantment amount;
- equip slot;
- keywords;
- DATA value/weight/damage;
- DNAM speed/reach/stagger/skill/resist/flags and weapon behavior;
- critical data;
- sounds;
- impact data;
- first-person model relationships.

Patch semantics:
- Damage, speed and reach can be independently changed by balance mods.
- Animation type/keywords affect behavior and OAR/framework conditions.
- Instance temper/enchantment is not fully represented by base WEAP.

## ARMO

Fields:
- name/model/icon;
- Object Effect;
- biped slots;
- armor type;
- armor rating;
- value/weight;
- keywords;
- ARMA list;
- equip sound;
- race/skin relationships.

## ARMA — Armor Addon

Fields:
- male/female first/third-person models;
- race applicability;
- biped slots;
- skin texture;
- footstep data;
- additional races;
- model data.

Patch semantics:
- ARMO chooses gameplay item/slots; ARMA supplies body models/race support. Both must agree.

## AMMO

Fields:
- projectile;
- damage;
- value;
- flags;
- model/name/keywords.

## PROJ

Fields:
- projectile type;
- speed/gravity/range;
- collision radius;
- explosion;
- sound;
- muzzle flash/visual behavior;
- flags.

## SPEL

Fields:
- spell type;
- casting type;
- delivery;
- cost;
- equip slot;
- effects array;
- flags.

### Effect Item
Each effect entry stores:
- MGEF;
- magnitude;
- area;
- duration;
- conditions.

Patch semantics:
- MGEF defines native behavior; SPEL effect entry defines actual configured magnitude/duration/conditions.

## MGEF

Fields:
- archetype;
- associated item(s);
- ActorValue;
- magic school;
- flags;
- base cost;
- resist value;
- casting/delivery compatibility;
- visual/audio chain;
- keywords;
- scripts/VMAD.

Patch semantics:
- Archetype and flags are high-risk gameplay semantics.
- Visual-only patch should avoid forwarding unrelated cost/archetype fields.

## ENCH

Fields:
- enchantment type;
- charge/cost-related data;
- effects;
- restrictions/flags.

## ALCH

Used for:
- potions;
- poisons;
- food.

Fields:
- effects;
- value/weight;
- flags;
- consumption sounds;
- keywords;
- model/icon.

## INGR

Fields:
- four effect slots;
- effect visibility/known state;
- value/weight;
- model/icon;
- keywords.

## BOOK

Fields:
- text;
- teaches skill or spell;
- value/weight;
- inventory/world model;
- flags.

## COBJ

Fields:
- component CNTO entries;
- created object CNAM;
- created count NAM1;
- workbench keyword BNAM;
- conditions.

Patch semantics:
- Recipe conflict can often be solved without touching output item's ARMO/WEAP record.

## LVLI

Fields:
- leveled entries;
- level;
- count;
- chance none;
- global;
- flags.

## LVSP

Leveled spell list.

## CONT

Fields:
- base inventory;
- flags;
- open/close sounds;
- model;
- scripts.

Runtime inventory changes live in save/reference state.

## MISC

Fields:
- model/name;
- value/weight;
- keywords.

## SLGM

SoulGem:
- capacity;
- contained/default soul;
- value/model/keywords.

Runtime filled state can also be instance-specific.

## KEYM

Key item.

## SCRL

Scroll magic item:
- spell-like effect entries;
- model/value;
- casting data.

## SHOU / WOOP

Shout ties:
- WordOfPower;
- spells;
- recovery values.

## PERK

Structures:
- rank;
- conditions;
- perk entries;
- Entry Point effects;
- ability grants;
- quest effects.

Patch semantics:
- Perk tree presentation, conditions and engine Entry Points are distinct concerns.

## TXST

TextureSet form:
- diffuse/normal/environment/etc. texture paths;
- flags/material data.

Used by world objects/landscape and can be patched independently of NIF texture paths.

## MATT

MaterialType:
- parent/material relationships;
- friction/restitution;
- sounds/impact semantics.

## SNDR / SNCT / SOPM

Audio:
- SoundDescriptor;
- SoundCategory;
- SoundOutputModel.

Patch semantics:
- Audio routing, category and actual sound files are separate.

## Safe item/magic patch strategy

1. Identify whether conflict is base stats, visuals, keywords, magic behavior, recipe or distribution.
2. Patch only intended fields.
3. Check runtime patchers after static winner.
4. Check perk Entry Points affecting final calculations.
5. Check inventory-instance ExtraData for temper/custom enchantment/poison.
6. Retest crafting/enchanting UI and actual combat behavior.

## Sources

- xEdit/TES5Edit schemas and scripts
- Creation Kit item/magic/perk documentation
