# Dulsa, the unborn child, and St. Dulsa's Charnel

Continuity: `tes.mod.vigilant`

Primary source: user-provided `Vigilant.esm`

## Core finding

VIGILANT takes the very small licensed-lore reference to **Dulsa** in *The Illusion of Death* and builds it into a major hidden-history sequence:

**Dulsa associated with Marukh → pregnant beloved in the Adabal memory → Marukh claims her blood and the unborn child's blood are required → later St. Dulsa cult/relic tradition → crucified remains in St. Dulsa's Charnel → Nail item explicitly says it killed Dulsa and the unborn child.**

The memory mechanics still prevent treating every detail as objective history.

## Canon substrate

`BOOK 0212905F` / *The Illusion of Death* is an official ESO reprint embedded in VIGILANT.

Its Dulsa reference predates VIGILANT's added plot.

Thus the mod is not inventing the name or the existence of a Marukh/Dulsa association; it is **expanding an obscure licensed reference**.

## No Dulsa actor

The *Adabal* quest's `MemoryDulsa` alias is:

- a **location alias**
- alias ID 6
- `ALFL 02383674` → `LCTN zzzCHMemDulsa`

It is not an NPC/reference alias.

A focused NPC inventory/name pass found no `NPC_` record for Dulsa.

The associated `Cliffs of Colovia` memory cell contains:
- Marukh;
- Pepe memory form;
- other memory machinery;

but no Dulsa actor.

This means Marukh's dialogue addresses Dulsa without giving her an independent speaking body in the memory.

## Sacrifice testimony

In *Adabal*, Marukh says the restoration ritual requires:
- Dulsa's blood;
- the blood of the child in her belly.

He explicitly calls the child **my child**.

He later apologizes to:
- Dulsa;
- his **nameless child**.

No separate child form is implemented.

## Charnel body

`CONT 0205AE05` / **St. Dulsa**:
- model: `Clutter\AoM\Cross\crucifixion01.nif`
- placed in `CELL 0204C45B` / **St. Dulsa's Charnel**
- contains **Nail of St. Dulsa**

This gives the sacrifice a physicalized afterlife representation.

Because this is a Coldharbour memory/relic environment, the body should be read as strong implementation evidence for VIGILANT's intended imagery, not necessarily as an untouched archaeological corpse.

## Corpse → memory link

The Dulsa corpse/container VMAD uses:

- `CHHasaamaCorpseScript`
- `myQuest = 0205AE03` / **Adabal**
- `StageTo = 10`

So Dulsa's remains are structurally wired into the memory quest itself.

The same Charnel also contains the **Eye of Marukh** reaction trigger linked to the Adabal quest.

This makes the Charnel a framing/entry site for the memory rather than just optional scenery.

## Murder-nail evidence

`ALCH 020E2597` / **Nail of St. Dulsa** uses:
- `MGEF 020E2591` / **Increase Perk Points**

The effect description states that it is one of the nails said to have claimed the lives of **Dulsa and her unborn child**.

This independently reinforces:
- Dulsa's death;
- the child's death;
- nail/crucifixion imagery.

It is stronger than inferring death solely from Marukh's stated intent.

## Reusable relic system

The Nail also appears in:
- `zzzCHDeathItemMarukhu`
- `zzzCHDeathItemPopeMegus`
- `zzzChDeathItemVarla`
- `zzzCHDeathItemShoggothMother`
- `zzzCHDeathItemArchPriest`
- Priest Nenyond's inventory;
- four scripted relic-pickup activators;
- multiple static relic displays.

Therefore the distributed Nails are a **gameplay relic economy**.

Do not interpret them as multiple separate historically authentic nails.

The corpse-contained Nail is the primary context-bound specimen.

## Separate unused/alternate corpse base

The plugin also contains:

- `ACTI 02052F5C`
- EditorID: `zzzCHDulsaCorpse`
- display name: **St. Dulsa**
- same `crucifixion01.nif` model

No placed reference to this ACTI was found in the current ESM.

The actual Charnel implementation uses the container version `0205AE05`.

## Memory contradiction

The later *Temptation of Marukh* memory contains a Molag-Bal memory-tail actor speaking in a Marukh-like voice.

He says:
- he cannot see beloved Dulsa again;
- he wishes her a happy life.

That statement is incompatible with the preceding sacrifice memory if read as a simple linear chronology.

Since the same quest explicitly includes memory modification, the contradiction is best classified as:

**D-level manipulated/unstable memory evidence.**

## Why Dulsa matters to the Adabal plot

Dulsa is the point where the Stone project changes from abstract doctrine into intimate sacrifice.

The ESM connects:
- Marukh's love;
- pregnancy;
- Al-Esh revelation;
- blood sacrifice;
- restoration of Adabal;
- later saint/relic commemoration.

This gives VIGILANT a deliberate moral inversion of the canonical Marukhite language of Proper-Life and sacred expungement: the supposed restoration of salvation/Tower order begins with the destruction of Marukh's own family.

That thematic reading is interpretation; the individual structural and dialogue links above are the evidence.

## Reliability model

### A — structural
- St. Dulsa Charnel exists.
- crucified St. Dulsa container exists there.
- container holds Nail of St. Dulsa.
- corpse and Eye trigger point to *Adabal* quest.
- no Dulsa NPC or child actor identified.
- key/relic/corpse records exist.

### B/C — character/memory testimony
- Marukh calls Dulsa beloved.
- Marukh says the unborn child is his.
- Marukh says their blood is required.
- Marukh says Al-Esh commanded it.

### Strong item-description assertion
- Nail description says Dulsa and unborn child were killed by such nails.

### D — unstable memory
- later Marukh-like voice wishes Dulsa a happy life after the sacrifice sequence.
- *Temptation of Marukh* explicitly contains memory modification.

## Current conclusion

VIGILANT strongly intends Dulsa and the unnamed unborn child to be the sacrificial victims at the heart of Marukh's restored/fake-Adabal project.

The mod reinforces this not only through Marukh's dialogue but through:
- Dulsa's saint-name;
- her crucified corpse;
- her charnel;
- her key;
- her murder-nail relic;
- direct quest wiring back into the Adabal memory.

The exact historical chronology remains filtered through manipulated memory.


## Aredhel guardian correction

The Charnel guardian `CHBossRenaldRef` points to **Aredhel** (`NPC_ 0204F0A9`). The Renald naming is a legacy internal name; see `analysis/aredhel-renald-identity.md`. Aredhel drops St. Dulsa's Key as encounter gating, not as proof of a historical relationship with Dulsa.
