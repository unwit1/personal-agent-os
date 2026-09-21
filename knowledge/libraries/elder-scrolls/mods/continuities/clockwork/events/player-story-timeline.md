# Clockwork narrative timeline

Continuity: `tes.mod.clockwork`

This file reconstructs the player-facing story in narrative order from quest journals, dialogue, and written sources. It distinguishes **pre-player events**, **player-observed events**, and **later reinterpretations** so Lorekeeper can answer both chronological and spoiler-aware questions.

## Before the player

### The Chlodovech era

The dated human history of Clockwork Castle is recorded separately in [Ludwig / Clockwork Castle dated timeline](ludwig-clockwork-timeline.md). The major arc is:

1. The Chlodovech family builds the castle around a planned Velothi trade route.
2. The family mausoleum breaches Dwemer ruins in 4E 18.
3. Ludwig meets Lamashtu and Lahar and learns the complex below is Nurndural.
4. Gilded assistance transforms the castle with steam heat, plumbing, pneumatic tubes, and the Travel Machine.
5. Most Gilded withdraw below; Ludwig becomes increasingly isolated.
6. Ludwig dies hidden inside the castle.

### Camilla and Isidor

Evidence: `BOOK 0505F158`, `05065F4A`, `05066A37`, `05070265`, `05070266`.

- A landslide uncovers ruins near Cragwallow Slope.
- Camilla recruits Isidor for a treasure-hunting expedition.
- Isidor does not arrive before Camilla enters the tunnels alone.
- Camilla discovers Dwemer ruins and repeatedly glimpses an unidentified woman/presence.
- Her notes shift from excitement to fear, inability to leave, and apparent psychological paralysis.
- She ultimately waits among bones for death.
- Later story evidence identifies the same tunnel-stalking presence as Shadow, but Camilla herself never names it.

## Player entry

### 1. Foot Of The Mountain — `QUST 0505F6C9`

- **Stage 10:** Isidor attacks the player and is killed/defeated. His death script directly sets this stage; the objective targets `IsidorAlias`.
- **Stage 20:** the player finds Camilla's note.
- **Stage 30:** the note points to newly exposed ruins near Cragwallow Slope.
- **Objective 40:** the player enters the Velothi Mountain Tunnels.

Narrative function: gives the player Camilla/Isidor's trail and pulls them into the same route where Camilla encountered Shadow.

### 2. Shadow Under The Mountain — `QUST 050632CC`

- **Stage 10:** the player enters the newly exposed ruins.
- **Stage 20:** the entry collapses behind the player.
- **Stage 30:** the player escapes the tunnels into an isolated mountain valley; the route back collapses again.
- **Stage 200:** the player discovers Clockwork Castle in the valley.

Narrative function: establishes physical entrapment and the haunted-tunnel threat before the Gilded are understood.

## Clockwork Castle

### 3. Steam-Powered — `QUST 052908C1`

#### Arrival and apparent escape route

- **Stage 10:** Lahar greets the player and identifies the estate as Clockwork Castle.
- **Stage 20:** Lahar brings the player to Lamashtu.
- **Stage 30:** Lamashtu says the Travel Machine can return the player to Skyrim.
- **Stages 40–60:** Lahar demonstrates that the machine is nonfunctional because castle steam power has failed.

#### Descent into Nurndural

- **Stage 70:** Lahar explains that the main steam pipeline beneath the castle is breached.
- **Stage 80:** Lamashtu gives the mausoleum key.
- **Stage 90:** the player enters Nurndural and repairs ten pipeline ruptures.
- **Stages 100–120:** steam power and the Travel Machine are restored.

#### The second form of entrapment

- **Stage 130:** the repaired Travel Machine works mechanically, but the player cannot make themself leave.
- **Stage 140:** Lamashtu begins explaining that the Gilded were once living Dwemer, then becomes incoherent.

Narrative function: replaces a mundane mechanical obstacle with a supernatural/psychological one and opens the Gilded-origin mystery.

### 4. Crystalline Heart — `QUST 05506BB5`

#### Lamashtu's failure

- **Stages 10–20:** Lahar examines Lamashtu after her breakdown.
- **Stage 30:** Lahar says her crystalline soul-gem heart is failing and suggests finding an empty replacement from Amalgam.

#### Search for Amalgam

- **Stage 40:** the player follows music through Nurndural.
- **Stage 50:** a remote voice speaks through a wall-mounted speaker horn and directs the player to the Sickness Ward.
- **Stage 60:** the voice directs the player to the southern commissary.
- **Stage 70:** the player finds the hostile Amalgam encounter.
- **Stage 80:** Amalgam paralyzes the player and retreats behind a portcullis.
- **Stages 90–110:** the Unfinished Note, lever-handle pickup, and repaired lever are each script-wired to advance the quest through stages 90, 100, and 110.
- **Stage 120:** the ballista breaches the barrier.
- **Stage 130:** the player obtains an empty/darkened crystalline heart from Amalgam.

#### Heart replacement

- **Stages 140–150:** Lahar guides a scripted multi-step transfer. A dedicated scene-phase global tracks opening Lamashtu's chest, removing her old heart, placing the replacement, activating the Soul Transference Machine, retrieving the filled heart, and reinstalling it.

#### First Shadow explanation

- **Stage 160:** Lamashtu says her death coincided with Kagrenac striking the Heart of Lorkhan; she initially interprets the accident as her soul splitting, with one half entering the crystalline heart and the other becoming Shadow.
- She identifies Shadow as the force preventing the player's departure through the Travel Machine.

Narrative function: links the Gilded experiment, Amalgam's heart-hoarding, Lamashtu's death, and the player-haunting Shadow into one causal story—while still presenting Lamashtu's account as testimony.

### 5. I Against I — `QUST 0508DA63`

#### Hunt for Shadow

- **Stage 10:** Lamashtu proposes defeating and soul-trapping Shadow so they can be reunited.
- **Stage 20:** the player accompanies Lamashtu into Nurndural, toward Direction of Flow.
- **Stage 30:** they reach the Animoculotory.
- **Stage 40:** they find and fight Shadow.
- **Stage 50:** Shadow is defeated and drawn into Lamashtu.

#### Reinterpretation

After the reunion, Lamashtu revises her earlier "two halves" model. In `INFO 05788344`, she says the encounter felt like looking at her reflection: she and Shadow were both copies of the living Lamashtu rather than two complementary halves that restored the original.

In `INFO 0578D460`, she interprets Shadow's behavior as loneliness and says Shadow kept the player close for that reason, likely doing something similar to Ludwig.

#### Resolution

- **Stages 60–70:** the player and Lamashtu return to Clockwork Castle.
- **Stage 200:** the player is free to leave. Lamashtu teaches the Recall to Clockwork Castle spell and offers the castle as a home.

Narrative function: resolves the escape problem but deliberately complicates the identity question. The story's final metaphysical answer is not "the original Lamashtu is restored"; it is that machine-Lamashtu and Shadow are copies descended from a dead person.

## Optional side stories

### A Bed of Dust — `QUST 05337FC1`

The player collects Ludwig's four journals, reconstructing the human history of the castle and eventually discovering Ludwig's desiccated body in a hidden chamber behind the Master Bedroom.

### Staff Enchanting — `QUST 057A69D2`

The player can supply Lahar with a Heart Stone and three empty Greater Soul Gems so he can build a Staff Enchanter in the Mage's Study.

## Narrative state transitions

The core escape problem changes form three times:

1. **Physical:** tunnel collapse prevents retreat.
2. **Mechanical:** failed steam power disables the Travel Machine.
3. **Supernatural/compulsive:** after repair, Shadow prevents the player from leaving.

The core Lamashtu/Shadow interpretation also changes:

1. **Unknown stalker** in the tunnels.
2. **Lamashtu's missing half** after *Crystalline Heart*.
3. **Independent copy/reflection of the same dead original** after *I Against I*.

Those transitions should be preserved in spoiler-aware retrieval rather than flattening later knowledge backward into earlier scenes.

## Runtime-causality companion

For record-level triggers and state transitions beneath this narrative ordering, see [runtime-causality.md](runtime-causality.md). The runtime layer is intentionally separate so implementation evidence does not get mistaken for character knowledge or metaphysical lore.
