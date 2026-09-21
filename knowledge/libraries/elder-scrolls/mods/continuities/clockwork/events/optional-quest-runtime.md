# Optional quest runtime wiring

Continuity: `tes.mod.clockwork`

This page extends the runtime-causality layer to Clockwork's optional player-facing quests.

## A Bed of Dust

Quest: `05337FC1` / `CLWSide01Quest`

### Exact journal placements

| Part | Placed REFR | CELL |
|---|---|---|
| 1 | `05332EA3` | `05013ECF` — Clockwork Castle Master Bedroom |
| 2 | `05332EA9` | `050261BA` — Clockwork Castle Mage's Study |
| 3 | `05332EAB` | `0503C62F` — Clockwork Castle Travel Room |
| 4 | `05332EB0` / alternate `0534C469` | `05013ECF` — Master Bedroom hidden chamber |

This exactly matches Lahar's search guidance for the first three volumes.

### First three journals

Placed refs `05332EA3`, `05332EA9`, and `05332EAB` run `CLWLudwigJournalScript`.

Their properties share:
- *A Bed of Dust* as `myQuest`
- per-journal read globals `CLWLudwigsJournal01ReadGLOB` through `03ReadGLOB`
- `StageToSet = 30`
- the wardrobe key `05337FC5`
- objective completion values 20, 30, and 40 respectively
- journal-part identifiers 1, 2, and 3

Because the Papyrus source body is not embedded in the ESP, Lorekeeper records these as a shared three-journal state machine rather than claiming every individual journal independently forces stage 30.

### Hidden chamber

The Master Bedroom wardrobe and false-panel references `0501497B` and `0501497D` both carry `CLWSDQ01DoorScript`, which references:
- *A Bed of Dust*
- quest-stage configuration 30
- `CLWSDQ01LudwigFound01GLOB`

This is record-level support for the stage-30/key state exposing Ludwig's hidden chamber.

### Fourth journal → completion

Both placed variants of Ludwig's fourth journal, `05332EB0` and `0534C469`, carry `defaultSetStageOnCloseBookNotAlias` configured to set *A Bed of Dust* to **stage 40**.

Stage 40 is the terminal journal entry describing Ludwig's desiccated corpse in the hidden chamber.

## Staff Enchanting

Quest: `057A69D2` / `CLWSide02Quest`

The QUST has only two stages:
- stage **10** — active component-delivery state
- stage **100** — terminal/completed state

### Request dialogue

`INFO 057A69D4` is Lahar's request for:
- 1 Heart Stone from Solstheim
- 3 empty Greater Soul Gems

The dialogue is conditioned on the Staff Enchanting quest being below stage 10 and its fragment directly references `CLWSide02Quest`.

### Delivery dialogue

`INFO 057A69D6` appears only when:
- the quest is at stage 10
- the player has at least 1 `DLC2HeartStone`
- the player has at least 3 `SoulGemGreater`

Its result fragment directly references:
- `CLWSide02Quest`
- `REFR 050299D9` / `CLWStaffEnchanterEP01REF`
- the Heart Stone
- the Greater Soul Gem base
- `GLOB 057A69D1` / `CLWLaharBlankStaffSpawn01`

The Staff Enchanter reference is placed in `CELL 050261BA` / **Clockwork Castle Mage's Study**.

The compiled fragment body is not available from the ESP alone, so Lorekeeper does not invent exact low-level Papyrus statements. The quest stages, item-count conditions, fragment properties, terminal stage 100, and station reference establish the intended runtime transaction without pretending the hidden script body was decoded.
