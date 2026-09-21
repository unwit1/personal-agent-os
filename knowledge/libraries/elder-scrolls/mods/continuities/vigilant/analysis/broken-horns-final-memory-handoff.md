# Broken Horns and the final-memory handoff

Continuity: `tes.mod.vigilant`

Primary structural sources:
- `QUST 0251ADBF` / `zzzCHSubQuest13` — **Broken Horns**
- `QUST 0251C038` — **Paravania the Man-Bull** / Memory 13
- `QUST 0242E0B1` — **Memory Guide**
- `FLST 0251D63F` — ordered 13-memory list

## Core finding

**Broken Horns is not simply another Act 4 side quest. It is the structural wrapper/handoff through which the Memory Guide reaches the thirteenth and final memory.**

Memories 1–12 are referenced directly by the Memory Guide.

Dream 13 is different.

The Memory Guide's `Dream13` property points to:

- `0251ADBF` / **Broken Horns**

rather than directly to:

- `0251C038` / **Paravania the Man-Bull**

Broken Horns then stores a property:

- `MemQ13` → Memory 13 / *Paravania the Man-Bull*

Memory 13 points back with:

- `Sq13` → Broken Horns

This reciprocal linkage makes the final memory a quest-within-a-larger-handoff rather than a standalone launch equivalent to Memories 1–12.

## Ordered memory sequence

`FLST 0251D63F` establishes the full memory ordering and places:

13. `0251C038` — *Paravania the Man-Bull*

at the end.

The special Dream13 indirection therefore does **not** mean Broken Horns replaces Memory 13 in the narrative order.

Instead:

**Memory Guide → Broken Horns → Paravania the Man-Bull → Broken Horns**

is the best structural model currently supported.

## Belharza and Morihaus integration

Broken Horns carries several object properties that broaden the final-memory sequence beyond a single dream:

- `MemQ13` → *Paravania the Man-Bull*
- `Sq11` → **Kyne's Dragon**
- `BqMorihaus` → **VS Morihaus**
- `AoMSq03` → **Legacy of Belharza**
- `qGenBLH` → Belharza generic-dialogue quest
- `gBelharzaRelease` → Act 4 Belharza-release global
- multiple Belharza, Morihaus, dragon, portal, shortcut, and barrier references

This structurally places Broken Horns at the junction of:

- Belharza's imprisoned/Man-Bull identity;
- Morihaus;
- the final memory;
- Kyne's Dragon;
- Belharza release state;
- traversal/portal mechanics.

## Belharza scene

`SCEN 0251D636` / `zzzCHSq13Sc01` is a Broken Horns scene whose speaking actor is **Belharza the Man-Bull**.

Belharza's current dossier also anchors:
- `INFO 0251D638`
- `INFO 0251D63A`

to Broken Horns.

This provides direct scene-level evidence that Belharza is an active character in the wrapper quest, not merely a referenced historical figure.

## Amicus Tharn closure

Broken Horns also binds:

- alias **Boss** → `NPC_ 0251D68A` / **Amicus Tharn**

The placed Amicus actor:
- `ACHR 0251D68F`

is in:
- `CELL 0251C043` / **Belharza's Hidden Charnel**

This is the same Belharza-focused space in which the Amicus petition trail culminates.

The physical route graph further connects:

**Second Inquisition Court → First Inquisition Court → Belharza's Hidden Charnel → memory-prison layer**

with the First Inquisition Court also linking directly to the memory-prison cell.

That topology reinforces Broken Horns as a convergence point for historical documents, Belharza's identity, Amicus's ideology, and the final memory handoff.

## Why this matters

The final memory is not merely the thirteenth item in a list.

VIGILANT gives it a larger scaffolding that ties the memory to unresolved First Era identity conflicts:

- Belharza's parentage and mutilation;
- Morihaus's unstable-form testimony;
- Amicus's program of rewriting Belharza and history;
- the Amulet/legitimacy dispute;
- the Order's treatment of non-human peoples;
- the player-facing Prisoner/identity material;
- Belharza's release and later boss/quest states.

That architecture explains why Dream13 receives special orchestration.

## Papyrus limitation

The ESM preserves:
- quest relationships;
- properties;
- aliases;
- scenes;
- stage-fragment presence;
- placements.

It does **not** preserve the executable bodies of the external compiled PEX fragments.

Therefore the current reconstruction can safely state the handoff graph, but not the exact runtime call sequence such as:
- which quest starts first;
- which precise stage invokes Memory 13;
- exactly when Belharza is released;
- exact enable/disable operations for portals and barriers.

Those details remain pending script/BSA ingestion.

## Current classification

**Broken Horns = high-confidence final-memory orchestration wrapper and Belharza/Morihaus convergence quest.**

It should be indexed separately from *Paravania the Man-Bull* while maintaining a bidirectional relationship between them.

## Relationship map

- **Memory Guide Dream13 → Broken Horns**
- **Broken Horns MemQ13 → Paravania the Man-Bull**
- **Paravania the Man-Bull Sq13 → Broken Horns**
- **Broken Horns → binds → Belharza the Man-Bull**
- **Broken Horns → binds Boss → Amicus Tharn**
- **Broken Horns → references → Kyne's Dragon**
- **Broken Horns → references → VS Morihaus**
- **Broken Horns → references → Legacy of Belharza**
- **Broken Horns → tracks → Belharza release state**

## Canon boundary

The final-memory wrapper, Belharza/Morihaus quest architecture, Amicus boss placement, and associated identity reconstruction are VIGILANT-continuity structures.
