# Custom magic relationship audit 02

Continuity: tes.mod.vicn.unslaad
Primary source: translated Unslaad.esm 3.0.6

This pass audits custom SPEL/MGEF records carrying lore relationships beyond the already-mapped summon books and item enchantments.

## Staff weapon arts
- Staff of Bormahu -> **Circle of Bormahu**: sunlight healing circle restoring Health.
- Staff of the Jills -> **Circle of the Jills**: blue-sunlight circle restoring Magicka.
- Staff of the World-Eater -> **Flames of Alduin**: explicit Alduin-flame explosion.
- Staff of the Old Knocker -> **Blizzard**: surrounds the caster in a blizzard.

These are direct WEAP VMAD -> SPEL -> MGEF relationships.

## Woodland-Man weapon arts
Woodland Man's Knight Sword/War Axe -> one-handed **Woodland Man's Whisper**.
Woodland Man's Knight Greatsword/Battleaxe -> two-handed **Woodland Man's Whisper**.
Both use **Fortify Health Regeneration**.

## Yngol weapon arts
Yngol's War Axe -> **Yngol's War Cry**: stagger + 10% weapon damage.
Yngol's Battleaxe -> **Yngol's War Cry**: stagger + 15% weapon damage.

## Owl intervention mechanics
**Owl's Interference** -> Slow Time Effect; directly referenced by The Owl Flies at Dusk VMAD.
**Reveal Owl** -> directly referenced by Mq07 VMAD and Gray-Owl combat-AI VMAD.
**Erosion** -> named Owl effect cross-linked with Mq07 Erosio properties/mind trigger.

The internal Owl's-Interference EditorID contains "4thWall"; treat this as developer terminology, not literal in-world proof of fourth-wall metaphysics.

## Dov-Ah-Kiin spectral-dragon support
Dov-Ah-Kiin's custom combat-AI VMAD references:
- **Conjure Spectral Dragon**, whose MGEF summons NPC 031D341E / Spectral Dragon;
- **Splatt Spectral Dragons**, using Call Dragon Arrows.

## Creature-family attack names
- Dagonic Watchers -> **Dagonic Agony**
- Pogaan-Sinak family -> **Mora's Agony**

These strengthen authored Dagon/Mora vocabulary but do not independently establish theology.

## Method boundary
SPEL/MGEF names, player-facing descriptions, and VMAD links are implementation evidence.
Do not infer unseen Papyrus behavior or metaphysical rules from internal EditorIDs alone.
