# DAc0da environmental insight / activator index

**Continuity:** `tes.mod.vicn.dac0da`  
**Source:** `DAc0da.esm`

This index maps lore-bearing MESG records to the ACTI records and placed references that expose them in the world.

It distinguishes:

- **environmental insights** — discovered by interacting with a placed activator;
- **system/manager messages** — invoked from quest scripts rather than found as world objects;
- **branch summaries** — invoked by ending logic.

## Atmora / Sea of Causality insights

| MESG | ACTI / displayed interactable | Placed ref | Cell / location |
|---|---|---|---|
| `00471C` Aeonstone | `00471B` **Aeonstone** | `004723` | `zDcdTharnShip` / **Tharn's Hideout** |
| `00471D` Tsa Rat | `004720` **Tsa the Dozing Rat** | `004728` | `zDcdDozingRatInn` / **Dozing Rat Inn** |
| `00471E` Star Men 1 | `004721` **Star Man's Serpent** | `00476F` | `DcdForelgrim15` / **Forelgrim** |
| `00471F` Star Men 2 | `004722` **Star Man's Serpent** | `004772` | `DcdForelgrimC01` / **Forelgrim** |
| `00475B` Hans/Herma-Mora | `00475C` **Hare Mound** | `00475D` | `DcdHareMound01` / **Hare Mound** |
| `00477B` Serpent warning | `00477C` **Serpent's Rule** | `004780` | `DcdRoadToHarakk02` / **Road to the Fallen Star** |
| `004B7C` fallen Jill | `004B7E` **Fallen Jill** | `004B80` | `DcdHarakk10` / **Stranded Harakk** |
| `004B7D` Milk Tree diagnostic | `004B7F` **Burnt Corpse** | `004B81` | `DcdHarakk10` / **Stranded Harakk** |
| `005121` Beynhaal parchment | `005123` **Beynhaal** | `005125` | `DcdKalpicShip06` / **Crash Site** |
| `005122` smiling masks | `005124` **Mask of Scorn** | `005126` | `DcdKalpicShip06` / **Crash Site** |
| `005132` Snow-Drake doll | `005133` **Snow Drake Doll** | `005134` | `zDcdDozingRatInn` / **Dozing Rat Inn** |
| `005148` Nahd/Dervish text | `005149` **Strange Poster** | `00514A` | `zDcdTharnShip` / **Tharn's Hideout** |
| `0060F6` Maid dissolution | `0060F7` **Mnemolichite** | `0060F8` | `DcdRevenantGate04` / **Worm Hole** |

### Structural significance

The two Hist/Jill messages are physically adjacent in the same **Stranded Harakk** cell:

- **Fallen Jill**
- **Burnt Corpse** carrying the Milk Tree / Wheelian-rip diagnostic

This makes the Milk Tree text direct environmental context for the fallen Jill encounter, not a free-floating lore message.

Likewise, the **Mask of Scorn** is physically paired with the Beynhaal aftermath at the **Crash Site**, strengthening its relevance to that Atmoran sacrifice/cultural-collapse thread.

## Y.E.L.E.M. dream-circuit records

Two Kagrenac messages are exposed through identically named interactables:

| MESG | ACTI | Placed ref | Location |
|---|---|---|---|
| `0093D1` | `0093D5` **Dream Circuit Y.E.L.E.M.** | `0093D6` | **Numidium Diaphragm** |
| `0093CE` | `0093CF` **Dream Circuit Y.E.L.E.M.** | `0093D0` | **Numidium Diaphragm** |

These are the records discussing:

- whether animunculi can dream;
- life as raw recurrence;
- a dreaming machine generating new mortals;
- dreamer and dreamed forgetting one another;
- finite mortal pattern inside infinite recursion;
- imitation of an Altmer mirror theory.

The repeated **Y.E.L.E.M.** activator name makes the dream-machine material a concrete named subsystem inside Numidium.

Do not automatically identify Y.E.L.E.M. with GLENMORIL's Yelem without further source-specific evidence, although the rare name makes cross-retrieval appropriate.

## Kagrenac record route through Numidium

| MESG | ACTI title | Placed ref | Numidium compartment |
|---|---|---|---|
| `0093D2` | **Kagrenac's Record: Dies Irae** | `00B57A` | **Anu[s]midium** |
| `0093D3` | **Kagrenac's Record: Blue Star** | `00B588` | **Numidium Arteria** |
| `0093D4` | **Kagrenac's Record: Red Moment** | `00B58B` | **Numidium Iecur** |
| `00B57B` | **Kagrenac's Record: Tools** | `00B582` | **Numidium Cavitas** |
| `00B57C` | **Kagrenac's Record: Anumidium** | `00B583` | **Numidium Cavitas** |
| `00B57F` | **Kagrenac's Record: Idol of Gods** | `00B589` | **Numidium Vena** |
| `00B58D` | **Kagrenac's Record: Victory** | `00B58F` | **Numidium Diaphragm** |

The seven records are therefore **distributed environmental discoveries** across Numidium rather than one contiguous book or speech.

That distribution matters for interpretation: the player reconstructs DAc0da's Kagrenac philosophy while physically moving through the machine.

See `analysis/kagrenac-insight-records.md`.

## Dumac's ZERO SUM N0 route through Dwemereth

| MESG | ACTI title | Placed ref | Cell |
|---|---|---|---|
| `00B69D` | **Dumac's Record: Z** | `00B6AD` | `DcdDwemerethSw02` |
| `00B69E` | **Dumac's Record: E** | `00B6AE` | `DcdDwemerethSe04` |
| `00B69F` | **Dumac's Record: R** | `00B6B0` | `DcdDwemerethNW05` |
| `00B6A0` | **Dumac's Record: O** | `00B6B2` | `DcdDwemerethCU01` |
| `00B6A1` | **Dumac's Record: S** | `00B6B8` | `DcdDwemerethCU03` |
| `00B6A2` | **Dumac's Record: U** | `00B6B4` | unnamed Dwemereth exterior cell at grid (1, 0) |
| `00B6A3` | **Dumac's Record: M** | `00B6BD` | `DcdDwemerethCU03` |
| `00B6A4` | **Dumac's Record: N** | `00B6BF` | `DcdMantellaTower02` |
| `00B6A5` | **Dumac's Record: 0** | `00B6C1` | `DcdMantellaTower03` |

The sequence physically begins scattered across **Dwemereth**, converges in its central cells, and ends inside the **Mantella Tower**.

This environmental ordering supports the existing interpretation that the player is reconstructing the Dumac/Nerevar/Kagrenac dispute while approaching the Mantella/Dumac climax.

See `analysis/dumac-records-zero-sum.md`.

## Script/manager messages with no ACTI

Several important MESG records are not exposed through placed ACTI records.

### Pan-Argonia bad ending

MESG `00CA5C`, **Bad Ending: Pan-Argonia**, is referenced directly by the VMAD script on:

- QUST `00CA5B` — `zDcdMqArgoEnd` / **Pan-Argonia**

It is therefore an ending-summary message invoked by quest logic.

### Mnemolichite / Ghost Hand system

MESG records:

- `00D13F` — Ghost Hand / Mnemolic Sign menu
- `00D140` — Mnemolichite absorption explanation
- `00D4C2` — Blueshifting progress
- `00D4C3` — Mnemolic Sign gain

are all referenced by the VMAD script on:

- QUST `00D139`
- Editor ID: `zDcdQManagerSkyshard`
- FULL: **Skyshards**
- script: `DcdSkyshardQuestScript`

Its script-property names include:

- `MsgMenuAbsorb`
- `MsgMenuSkillUp`
- `MsgGainFragments`
- `MsgGainPoints`
- `gShardRate`
- `gShardCount`
- `gShardPoints`
- `gShardPointsEarned`
- `gShardPointsSpent`

Despite the quest's implementation name **Skyshards**, the visible DAc0da interface calls the resource **Mnemolic Sign** and the process **Blueshifting**.

These records should therefore be treated as **system-level progression/ontology messages**, not environmental inscriptions.

## Retrieval rule

When answering “where is this lore found?”:

- use the placed ACTI/cell mapping for environmental insight records;
- use quest/script ownership for system and ending messages;
- preserve the difference between what a character says and what an environmental/system message states.

This prevents DAc0da's environmental lore from being flattened into ordinary dialogue provenance.
