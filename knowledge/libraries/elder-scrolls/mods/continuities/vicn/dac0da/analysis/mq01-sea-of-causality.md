# The Sea of Causality — quest reconstruction

**Quest:** `zDcdMq01`  
**Title:** The Sea of Causality  
**Source:** `DAc0da.esm:004475`  
**Continuity:** `tes.mod.vicn.dac0da`

## Direct quest structure

The QUST record instructs the player to:

- head north;
- optionally speak with Samon;
- defeat a Sload;
- defeat brainwashed people;
- later neutralize a boss.

The quest aliases include `Samon`, `Sload`, multiple enemies, a boss, a victim, an agent, and several Yhagra.

## Akashiya-Samon

Samon explicitly introduces himself as **Akashiya-Samon**, a Dragonguard serving "His Majesty Reman." Evidence: `DAc0da.esm:004489`.

He calls Reman the true Dragonborn and says the Dragonguard protect him while hunting dragons that are his sworn enemies. Evidence: `DAc0da.esm:00448C`.

Samon says his group was on an expedition to Skyrim when a storm struck; a golden dragon flew above/through the storm, and he jumped into the sea to pursue it, eventually washing up in the ship graveyard. Evidence: `DAc0da.esm:004493`.

The quest's Numidium-linked temporal setting makes Samon's presence an important chronology problem, but this pass does not yet assert the exact mechanism by which he reached this time/place.

## Sload encounter

Samon identifies a nearby Sload with three brainwashed slaves and can propose a joint attack. Evidence: `DAc0da.esm:0044B8`, `0044BA`, `0044BC`.

Later scene dialogue shows Sload-side speakers reacting to a person who is not under their mind magic. One speaker calls that person **"the Doom-Driven"** and orders retreat. Evidence: `DAc0da.esm:004506`, `004508`, `00450B`.

Further scene responses refer to a protective barrier, reinforcements, preserving the target's body, and eventually offering freedom and long life in exchange for killing the attackers. Evidence: `DAc0da.esm:004513`, `004515`, `00451A`, `004525`.

Speaker ownership for these unnamed scene topics is not yet fully resolved, so the claims remain attached to the INFO records rather than prematurely assigned to a specific named Sload.

## Golden dragon thread

At the end of Samon's local dialogue chain, he says the golden dragon flew east and that he will follow it. Evidence: `DAc0da.esm:004535`.

This is a direct continuation hook for Samon's later appearances and epilogue quest. It should be joined with the dedicated **Golden Dragon Flight** support quest (`zDcdMqDragon`) in a later pass.

## New retrieval nodes

This quest introduces or strengthens:

- Akashiya-Samon
- Reman
- Dragonguard
- golden dragon
- Sload mind magic
- brainwashed victims
- Doom-Driven
- ship graveyard
- Yhagra

The next pass should test which of these recur in MQ02 and in Samon's epilogue before creating stronger cross-Vicn identity links.
