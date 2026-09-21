# Staff of Towers and Middle Dawn in VIGILANT

Continuity: `tes.mod.vigilant`

Primary source: user-provided `Vigilant.esm`

This pass asks whether VIGILANT physically recreates the canonical **Staff of Towers / Middle Dawn** machinery, or instead imports that lore as a framework for its own Stone/Tower story.

## Result

The ESM supports a layered answer:

1. VIGILANT embeds multiple official texts explaining Marukhati doctrine, Tower/Stone mechanics, and Dragon Break ritual concepts.
2. VIGILANT adds its own dialogue in which **Marukh commands that a brilliant Stone be made into a Tower**.
3. VIGILANT physically implements **Adabal / Stone-Fire** objects and triggers.
4. The ESM does **not** contain a physical artifact record named **Staff of Towers**, nor named Mnemoli/Hurling Disk ritual machinery.

Current classification:

**Canonical Tower/Dragon-Break concepts are imported as substrate; VIGILANT's Adabal/Stone-Fire → Tower plot is a mod-specific extension built in dialogue, memories, and Stone objects rather than a literal recreation of the Staff of Towers.**

## Canonical imported mechanism

### Fervidius Tharn

VIGILANT embeds:

- `02054ED3` — *On the Detachment of the Sheath from the Integument*
- `024A8AF7` — *Vindication for the Dragon Break*

These supply canonical Marukhati vocabulary including:
- Mnemoli;
- Hurling Disk;
- a circle turned sidewise becoming a Tower;
- the middle dawn;
- untime/unplace;
- Staff of Towers;
- Proper-Life chants;
- ritual Dance;
- reversal of the Roll of Time;
- removal of the Aldmeri Taint.

These texts are official-source reprints. Their concepts should not be treated as inventions of VIGILANT.

### The Exclusionary Mandates and Proper-Life

VIGILANT also embeds:
- `0212905B` — *The Archimonk's Dream*
- `0212905C` — *The Song-Never-Sung-at-Twilight*
- `0212905D` — *The Forty-Third Praise-Song of Alessia*
- `0212905E` — *The Exclusionary Mandates*
- `0212905F` — *The Illusion of Death*

These reinforce the Marukhite ideological/religious layer around:
- unitary Akatosh;
- Proper-Life;
- expungement of the Aldmeri Taint;
- Marukh's visionary relationship with Alessia;
- survival beyond ordinary death.

Again, these are official-source reprints embedded in the mod.

## Aurbic Enigma 4 and the Staff of Towers

VIGILANT contains:

- `BOOK 024A8AFD`
- EditorID: `zzzCHBookESO09`
- title: **Aurbic Enigma 4: The Elden Tree**
- author: **Beredalmo the Signifier**

The text explicitly discusses:
- Towers and their Stones;
- Chim-el-Adabal as White-Gold's Founding-Stone;
- Anumaril's eightfold **Staff of Towers**;
- each staff segment as a semblance of a Tower in its Dance;
- the attempt to use a Tower-segment to rewrite Green-Sap into White-Gold.

The exact VIGILANT transcription is preserved at:

`books/024A8AFD-aurbic-enigma-4-the-elden-tree.txt`

### Placement model

Unlike some story-significant VIGILANT books, this record has no fixed placed BOOK reference.

The ESM references it through general/random book leveled lists including:
- `LVLI 020F86C1` / `zzzCHLitemBook75`
- `LVLI 020E5233` / `zzzCHLitemBook`
- `LVLI 024A8B08` / `zzzCHLitemBookESOALL`

Therefore *Aurbic Enigma 4* functions primarily as **distributed canonical background lore**, not as a uniquely staged clue at one narrative location.

## VIGILANT's Stone → Tower language

### Adabal memory

In `QUST 0205AE03` / **Adabal**, topic:
- `DIAL 0205AE0D`
- EditorID: `zzzCHMeQ05MarukhB01T03`

leads to `INFO 0205AE0E`.

The speaker says it is their mission to wash the Stone with blood and place it in the Tower, and describes sacrificing others for the vision shown by the Stone.

The topic itself is explicitly a **Marukh** branch in the quest structure.

This is VIGILANT-specific ritual language.

### Pepe's account of Marukh

In the Coldharbour main quest:

- `INFO 021303D7`

Pepe recounts finding Marukh in the Colovian jungle, seeing him dance with an apparition of Alessia until dawn, and then hearing Marukh command:

**Make this Stone into a Tower.**

This is one of the clearest bridges between imported Tower metaphysics and VIGILANT's Stone plot.

Pepe's account remains testimony, but the line is directly encoded in the ESM.

## Dance imagery

The word **Dance** operates at several levels in VIGILANT:

### Canonical Marukhati ritual
*Vindication for the Dragon Break* explicitly describes Selectives dancing forward and backward as part of the ritual to reverse the Roll of Time.

### Marukh memory/testimony
Pepe describes Marukh dancing with Alessia's apparition until dawn immediately before the Stone/Tower command.

### Malada
Pepe also says of the floating Malada temple:

- `INFO 0212F861`

that fanatics supposedly brought it there so they could **dance** and drag down the Eight Divines.

This is suggestive of Marukhati ritual practice, but it is still Pepe's explanatory testimony and should not be equated automatically with the exact Staff-of-Towers ritual.

## Physical Stone implementation

### Adabal

VIGILANT contains:
- `MISC 021353DF` / `zzzCHAdabal` — **Adabal**
- `MISC 0205AE01` / `zzzCHAdabalMemory` — **Red Stone**
- `MISC 0206F543` / `zzzCHAdabalMemory2` — **Red Soul Gem**
- `ACTI 0208CA88` / `zzzCHAdabalACT` — **Stone-Fire**
- `STAT 021353D1` / `zzzCHAdabalStatic`
- `ACTI 021353E1` / `zzzCHAdabalSetTrigger`

These show that VIGILANT repeatedly represents the same Stone complex through memory, inventory, activator, and set-trigger forms.

### Adabal and Molag Bal

`NPC_ 0212339D` / **Molag Bal** carries:
- `MISC 021353DF` / **Adabal**

This is direct structural evidence that the later Adabal object is tied to Molag Bal's inventory.

### Stone-Fire placements

`ACTI 0208CA88` / **Stone-Fire** has at least two placed references:
- `REFR 02098547` in `CELL 021353E4` / **Aetherius** (good Aetherius cell)
- `REFR 0208CA89` in `CELL 02088A8D` / **Sancremor Angasel** memory cell

Thus the Stone is not merely discussed; it is physically represented at important late-game/memory locations.

## White-Gold Tower memory: related but separate

VIGILANT also contains:
- `CELL 0228A47A` / **White-Gold Tower**
- location record `02295516` / `zzzCHMemPelinal`

The cell belongs to the **Pelinal memory** location network.

It should therefore not be treated as direct proof that the Marukh Stone/Tower ritual physically occurs in this White-Gold Tower cell.

The existence of a White-Gold memory is relevant to the broader Tower theme, but it is structurally a separate memory layer.

## No physical Staff of Towers record

A focused pass across:
- weapons;
- misc items;
- activators;
- statics;
- armor;
- keys;
- spells;
- magic effects

found no record whose name or EditorID identifies it as:
- Staff of Towers;
- Mnemoli;
- Hurling Disk;
- a Staff-segment artifact.

VIGILANT does contain:
- **Staff of Prophet Marukh**
- numerous Marukh relics/abilities;
- Stone/Adabal objects;
- Tower architecture and memory cells.

Those must not be conflated with the canonical **Staff of Towers**.

## Later Dragon Break testimony

In `QUST 0251FD3E` / **Bald Man-Ape**:

- `INFO 0251FD4F`

Saklas says the Forces of Order are mining for something and that the process previously stopped in the First Era because of past **Dragon Breaks**. He also refers to a singularity that may eventually be resolved.

This is important because VIGILANT links Dragon Break history to its present Greymarch/Order plot.

However:
- the mining target is not explicitly identified here as the Staff of Towers;
- the exact relation between this singularity and the Middle Dawn is not structurally established;
- the statement remains Saklas's testimony.

## Relationship model

Lorekeeper should preserve these relations separately:

- `Fervidius texts --describe--> canonical Marukhati Dragon Break ritual`
- `Aurbic Enigma 4 --describes--> Anumaril's Staff of Towers`
- `Marukh testimony/memory --commands--> Stone → Tower`
- `Adabal/Stone-Fire --physicalized_as--> VIGILANT objects`
- `Saklas --claims--> past Dragon Breaks interrupted Order mining`

Do **not** collapse them into:

- Adabal = Staff of Towers
- Marukh's Stone = one of Anumaril's staff segments
- Greymarch mining = confirmed Staff-of-Towers excavation

No such equation is encoded by the current ESM evidence.

## Interpretation

VIGILANT appears to use official Tower lore as a conceptual grammar.

The canonical texts establish that:
- Towers and Stones can impose stories/rules on reality;
- Tower-like instruments can alter those structures;
- the Marukhati Selective attempted ritual manipulation of Time and Akatosh.

VIGILANT then extends that grammar with a new hidden-history plot:
- a red Stone/Adabal is blood-fed and soul-charged;
- Marukh commands that the Stone become a Tower;
- the Stone persists into Coldharbour/Aetherius;
- later Order activity is discussed in relation to past Dragon Breaks.

That is a strong thematic/metaphysical bridge, but the extension remains `tes.mod.vigilant`, not established TES history.
