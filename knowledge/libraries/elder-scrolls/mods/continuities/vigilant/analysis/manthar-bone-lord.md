# Manthar → Bone Lord reconstruction

Continuity: `tes.mod.vigilant`

Primary source: user-provided `Vigilant.esm`

This pass asks a narrow question: **does the ESM explain how the historical sorcerer/architect Manthar became the later Bone Lord manifestation?**

## Historical starting point

`BOOK 020CB0DF` / *The Eight Saints of Cyrod* says Manthar was an Alessian sorcerer and architect who disappeared with Nenyond while exploring ruins uncovered beneath Nenyond's underground priory.

That establishes the historical disappearance, but not an undead transformation.

## Boss identity

The ESM contains:

- `NPC_ 021146D9`
- EditorID: `zzzCHBossBoneLord`
- display name: **Sorcerer Manthar**
- race: `RACE 02080D50` / **Alessian Lawmage Race**
- worn skin: `ARMO 02080D2F` / `zzzCHSkinBoneLord`
- placed reference: `ACHR 021146DA`
- location: **Funeral Temple**

The displayed identity and internal Bone Lord implementation are therefore part of the same NPC record.

## No quest-owned transformation

A direct whole-plugin FormID scan found the Manthar boss base `021146D9` only in:

1. its own NPC record; and
2. the placed actor `ACHR 021146DA`.

The placed actor itself is not referenced by a dedicated quest, scene, or quest-script property. Its only additional structural ownership is the **Funeral Temple** location data.

This is important negative evidence: there is no ESM-level quest record saying “transform Manthar,” “raise Manthar,” or otherwise narrating the transition from missing architect to Bone Lord.

## Boss scripts

The boss NPC's VMAD contains generic encounter scripts:

- `masterambushscript`
- `defaultActivateLinkedRefOnceOnDeath`
- `CHModKarmaOnDeath`

These govern encounter behavior, linked-reference activation, and karma handling.

No Manthar-specific transformation script is attached to the NPC.

This strongly suggests the Bone Lord state is treated as an already-existing encounter form by the time the player reaches him.

## Combat identity

The boss uses the Alessian Lawmage race and Bone Lord skin rather than a generic skeleton identity.

Its spell list includes:

- `zzzBMSpellLamaeAdeptCorrupt` / **Garden of Corruption (Adept)**
- additional master-game spells
- VIGILANT boss-difficulty support

This confirms a magical/necromantic combat presentation but does not identify who or what transformed him.

## Death → summon handoff

The boss death-item list is:

- `LVLI 021280D4` / `zzzCHDeathItemBoneLord`

Among its drops are:

- `BOOK 0213B506` / **Necromancy Tome: Sorcerer Manthar**
- `ARMO 020D957B` / **Sithis' Eye Ring**

The tome teaches:

- `SPEL 0213B505` / **Conjure Sorcerer Manthar**

That spell uses:

- `MGEF 0213B504` / **Conjure Sorcerer Manthar**

The magic effect explicitly summons:

- `NPC_ 0213B503` / `zzzCHSummonBoneLord` — **Sorcerer Manthar**

So the gameplay chain is structurally clear:

**defeat Bone Lord Manthar → obtain his necromancy tome → gain a summonable Bone Lord Manthar form**

This is a post-defeat preservation/replication mechanic, not evidence for the original historical transformation.

## Summon form

The summon NPC `0213B503` retains:

- display name **Sorcerer Manthar**
- **Alessian Lawmage Race**
- **Bone Lord** skin
- much of the boss spell/perk profile

It lacks the boss's death-item list and generic boss encounter VMAD.

That supports treating it as a deliberately stripped-down summon representation of the same encounter identity.

## Sithis' Eye Ring

The Manthar boss can drop **Sithis' Eye Ring**.

Its enchantment:

- `ENCH 020D957E` / **Eye of Sithis**

uses:

- `MGEF 020D957D` / **Twin Souls**

whose effect description allows the caster to summon two creatures.

However, the ring also participates in:

- dedicated crafting recipes;
- a `zzzCHSithisEyeReactionTrigger`;
- multiple Black Hand dialogue conditions.

Therefore the ring belongs to a broader Sithis/Black Hand gameplay system and should **not** be treated as proof that Sithis transformed Manthar.

## Funeral side quest check

The Act 4 quest:

- `QUST 02129BCA` / `zzzCHSubQuest04` — **Funeral**

was checked because of the shared “Funeral” naming.

Its aliases are centered on `Sister` / `SisterDead`, and its VMAD/stages do not structurally reference Manthar's boss base or placed actor.

It is therefore a separate side quest and should not be used to explain Manthar.

## What the ESM proves

### Strong structural facts

- historical Manthar disappears with Nenyond according to the saint text;
- a later NPC is explicitly named **Sorcerer Manthar**;
- that NPC is internally the **Bone Lord** boss;
- he is placed in the Funeral Temple directly connected to Nenyond's priory;
- defeating him can yield the **Necromancy Tome: Sorcerer Manthar**;
- the tome summons a second Bone Lord-form **Sorcerer Manthar**.

### Not established by the ESM

The plugin does not identify:

- who transformed Manthar;
- whether he transformed himself;
- whether the buried ruins caused it;
- whether Coldharbour reconstructed him this way;
- whether the Stone caused it;
- whether Sithis caused it;
- whether the Bone Lord is literally his historical corpse versus a soul/memory/manifestation.

## Current classification

**Historical Manthar → missing in Nenyond ruins → Bone Lord Manthar encounter** is a high-confidence identity sequence.

**The transformation mechanism is intentionally or externally unresolved at ESM-record level.**

The missing explanatory layer is most likely in one of three places:

1. external Papyrus/PEX scripts;
2. environmental storytelling not encoded as named records/dialogue;
3. deliberate ambiguity.

Until the script/BSA layer is ingested, Lorekeeper should preserve the gap rather than fill it with a necromancy/Sithis/Stone theory.
