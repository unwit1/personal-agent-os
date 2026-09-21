# Script- and record-backed mechanics

Continuity: `tes.mod.clockwork`

Gameplay implementation is **supporting evidence**, not automatically a metaphysical statement.

## Shadow's tunnel slow-time effect

`SPEL 0507FD84` / `CLWShadowSlowTimeSpell` is named **Shadow Under The Mountain** and its description is “Time stood still and she came towards me.” `CLWShadowManage01Quest` directly references the spell through VMAD alongside the Shadow alias and stage markers.

That wording mirrors Camilla's final trail note, so the slow-time haunting is an implemented Shadow effect as well as literary description.

## Generic Gilded downed/reanimation behavior

The principal and ambush Gilded archetypes carry `CLWGildedRes01Script`, which references `CLWGildedReanimateSelf` and the configurable `CLWMCM01GildedDownedSliderGLOB`.

This supports repeated downed/recovery behavior. It does **not** by itself prove unlimited metaphysical resurrection beyond the dialogue about Gilded hearts and death.

## Shadow boss escalation

The final Shadow fight uses multiple encounter forms and progressively stronger Drain Life variants. `CLWSQ04ShadFightPhaseGLOB`, `CLWShadowBleedoutScript`, and `CLWShadowDyingScript` coordinate the encounter, with the dying script advancing phase state and referencing Lamashtu.

## Amalgam's scripted retreat

`NPC_ 0559026E` / `CLWLvlAmalgamCenturionAmbush` carries `CLWAmalgamBleedoutScript`. Its VMAD properties reference the stage-70 scene, paralysis and teleport effects, retreat destination, portcullis/grate controls, and `CLWStory03Quest`.

This directly corroborates the journal sequence in which Amalgam paralyzes the player and retreats behind the barrier.

## Recall to Clockwork Castle

`CLWRecallToCastleSpellEffectScript` links the Recall spell/effect to fast-travel eligibility, a recall marker, the Clockwork Travel Room destination, teleport visuals, and failure handling. This matches Lamashtu's explanation of the spell.

## Steam pipeline state

The ESP stores `CLWSQ02PipeTotal = 10`, an initial pipe count of 0, ten individual repair globals, a **Ruptured Pipeline** activator, and the **Disassembled Dwemer Pipe** item.

## Crystalline-heart object states

The plugin has distinct records for **Crystal Heart (Lamashtu)**, **Crystal Heart (Empty)**, the empty heart inside Amalgam's internals, and the **Soul Transference Machine**. This implementation supports Lahar's explicit empty/darkened-heart replacement instructions.
