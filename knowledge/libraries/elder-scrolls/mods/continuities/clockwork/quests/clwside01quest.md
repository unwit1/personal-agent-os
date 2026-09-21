# A Bed of Dust

Quest FormID: `05337FC1`  
Editor ID: `CLWSide01Quest`

## Journal stages

### Stage 10

I've found part of a journal written by someone named Ludwig, who used to live in Clockwork Castle. Lahar may know something about it.

### Stage 20

Someone named Ludwig used to live in Clockwork Castle. Lahar gave me suggestions on where I might find Ludwig's journals: the Master Bedroom, Mage's Study, and Travel Room.

### Stage 30

I have found several of Ludwig's journals. One contained a key belonging to a wardrobe in the Master Bedroom.

### Stage 40

I have found Ludwig's journals; the last was resting on his desiccated corpse in a secret chamber behind the Master Bedroom walls.

## Objectives

- `10` — Ask Lahar about Ludwig's journals
- `20` — Find Ludwig's Journal, Part 1
- `30` — Find Ludwig's Journal, Part 2
- `40` — Find Ludwig's Journal, Part 3
- `50` — Find Ludwig's Journal, Part 4

## Aliases

- `0` **Lahar** → Lahar
- `1` **Journal01** → `REFR 05332EA3`
- `2` **Journal02** → `REFR 05332EA9`
- `3` **Journal03** → `REFR 05332EAB`
- `4` **Journal04** → `REFR 05332EB0`

## Runtime wiring

- Part 1 is placed in the **Master Bedroom**.
- Part 2 is placed in the **Mage's Study**.
- Part 3 is placed in the **Travel Room**.
- Parts 1–3 share `CLWLudwigJournalScript`, per-part read globals, wardrobe-key wiring, and objective/state configuration toward stage 30.
- The Master Bedroom wardrobe and false back panel use `CLWSDQ01DoorScript` with this quest's stage-30 state.
- Both placed variants of Part 4 set the quest to stage **40** when closed/read.

See `../events/optional-quest-runtime.md` for exact refs and script-property evidence.
