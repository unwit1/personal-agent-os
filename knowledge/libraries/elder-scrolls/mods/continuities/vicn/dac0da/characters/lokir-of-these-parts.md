# Lokir of These Parts

**Continuity:** `tes.mod.vicn.dac0da`  
**NPC:** `DAc0da.esm:00AA00` / `zDcdUqLokirNew`  
**Displayed name:** **Lokir of These Parts**  
**Quest:** `zDcdMq00` — The Call of Landfall  
**Quest alias:** `Lokir`

## What the actor actually is

DAc0da does **not** present this actor as the ordinary historical Nord whose appearance the player recognizes.

When the player asks Rolls-On-Roads who the messenger Lokir was, Rolls answers that Lokir is:

- **a Daedra he summoned**;
- ordered to assume **a form familiar to the player**.

Evidence: `DAc0da.esm:00AA56`.

Rolls asks whether the Daedra appeared as:

- a dead family member;
- a loved one;

and apologizes if so.

When the player says it was merely a familiar-looking Nord, Rolls suggests the player may have formed a strong impression of that Nord—possibly by having **seen his death**. Evidence: `DAc0da.esm:00AA58`.

## Form implementation

The unique NPC form:

- `DAc0da.esm:00AA00`
- Editor ID: `zDcdUqLokirNew`
- FULL: **Lokir of These Parts**

is directly bound to MQ00 alias `Lokir`.

A placed reference `DAc0da.esm:00AA0E` exists in the **Actor Room** control cell.

The actor uses a template form `DAc0da.esm:00AA01`, reinforcing that the visible appearance is an implemented presentation state rather than sufficient proof of underlying identity.

## Identity boundary

The obvious visual/name joke evokes Skyrim's Lokir from the Helgen opening, and Rolls' "perhaps you've seen his death" line strengthens that allusion.

However, DAc0da's own explicit explanation is:

> the messenger is a summoned Daedra wearing a form selected from the player's memory/familiarity.

Therefore the library should model:

- **underlying entity:** summoned Daedra;
- **presented identity/form:** Lokir of These Parts;
- **possible reference to Skyrim's Lokir:** strong allusion, not literal identity.

This is another DAc0da example of **perceived identity being separable from the entity/body underneath**.
