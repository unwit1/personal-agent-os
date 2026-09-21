# The Call of Landfall — quest reconstruction

**Quest:** `zDcdMq00`  
**Title:** The Call of Landfall  
**Source:** `DAc0da.esm:00AA0C`  
**Continuity:** `tes.mod.vicn.dac0da`

## Direct quest structure

Objectives in the QUST record:

1. Ask about the Dwemer giant at the Bards College theater.
2. Go to Solitude Lighthouse.
3. Talk to the Monk.
4. Optionally ask for mission details.
5. Enter the portal.

The opening scene therefore establishes the offshore giant first, then moves the player to a Psijic-linked briefing and finally into the Numidium/time-distortion mission area.

## Offshore crisis

Dialogue reports a gigantic Dwemer construct offshore from Solitude. A speaker says Imperial soldiers and Thalmor investigators have gone missing, and that the Solitude navy has not returned after sailing out against it. These are in-world reports rather than omniscient narration. Evidence: `DAc0da.esm:00AA24`.

The messenger directs the player to Solitude Lighthouse to meet its summoner. Evidence: `DAc0da.esm:00AA28`.

## Lokir messenger

The quest alias table resolves:

- `Lokir` -> `DAc0da.esm:00AA00` / `zDcdUqLokirNew` — **Lokir of These Parts**

When the player asks who the messenger Lokir was, Rolls-On-Roads says the actor was actually **a Daedra he summoned and instructed to assume a form familiar to the player**. Evidence: `DAc0da.esm:00AA56`.

When the player says the figure was merely a familiar-looking Nord, Rolls-On-Roads suggests the player may have a strong impression of that Nord because they witnessed his death. Evidence: `DAc0da.esm:00AA58`.

This means DAc0da is deliberately using the Skyrim opening's Lokir image as a **perception/memory-selected disguise**, not asserting that the historical Lokir survived or returned bodily.

The plugin also contains `DAc0da.esm:00AA01` / `zDcdTemplateLokir`, displayed simply as **Lokir**, as the supporting template form.

## Multiple attempts, multiple "yous"

The Monk speaks as though the current player is one iteration among many. When challenged, he says other versions of the player exist in other time and space but cannot perceive one another. Evidence: `DAc0da.esm:00AA30`, `00AA32`.

He asks the player to help banish Numidium from the current "present." Evidence: `DAc0da.esm:00AA35`.

A branching set of responses records escalating attempt counts: 54, 112, 283, 379, 484, and 643. These are conditional variants and should be preserved as evidence for repeated fate-line attempts, not combined as one literal conversation. Evidence: `DAc0da.esm:00AA4D`, `00AA4E`, `00AA4F`, `00AA50`, `00AA51`, `0044EE`.

The Monk explains that continued failure can cause events to become fixed "beyond fate," making further fate-line switching meaningless; he also reports a Ritemaster theory that a successful line could become the basis for corrections. Evidence: `DAc0da.esm:00AA53`.

## Numidium and temporal damage

The Monk describes the construct as Numidium and says:

- it collapses time around itself on a scale beyond Psijic repair (`DAc0da.esm:00AA37`);
- the mission is intended to prevent something like the Warp in the West (`DAc0da.esm:00AA37`);
- DAc0da's Psijics speculate that this Numidium is a remnant from the Warp in the West (`DAc0da.esm:00AA62`);
- the player is not supposed to defeat Numidium but to remove it from the present (`DAc0da.esm:00AA64`);
- a time breach inside Numidium is spreading its influence (`DAc0da.esm:00AA69`).

The direct operational plan is to enter Numidium, close that breach, and help the Jills repair time. Evidence: `DAc0da.esm:00AA69`.

## Hero, prophecy, and fate

The Monk says the Psijic Order selected the player because of an aptitude connected to the Hero/Event relationship. He attributes the statement **"Each Event is preceded by Prophecy. But without the Hero, there is no Event"** to Zurin Arctus. Evidence: `DAc0da.esm:00AA5B`.

For retrieval purposes this creates a DAc0da node connecting **Hero**, **Event**, **Prophecy**, **Zurin Arctus**, **Numidium**, and repeated fate-line correction. The attribution should remain source-scoped until independently corroborated.

## Jills and the Psijic response

The Monk describes Jills as female dragons tasked with fixing the flow of time. Evidence: `DAc0da.esm:00AA6B`.

He says the Psijics are collectively trying to slow the Numidian effect and that Artaeum is in upheaval, with the Ritemaster personally involved. Evidence: `DAc0da.esm:00AA6D`.

The Monk also reports that the Ritemaster sought help from Daedric Princes and was refused. His possible explanations—waiting for another kalpa or fear of Numidium—are explicitly speculative possibilities and should not be promoted as settled cosmology. Evidence: `DAc0da.esm:00AA66`.

## Transition into The Sea of Causality

The Monk opens a portal into a stormy sea, enchants the player to walk on water, and warns that time is unstable around Numidium. Evidence: `DAc0da.esm:00AA75`, `00AA7B`, `00AA7D`, `00AA7F`, `00AA81`.

This transition leads directly into **The Sea of Causality**.
