# Slave Trader

- Continuity: `tes.mod.vigilant`
- Primary form: `NPC_ 020CAA71` / `zzzCHlstSlaveTrader` — **Slave Trader**
- Race: `RACE 020B07E1` / **Bone Human Race**
- Placed reference: `ACHR 020CAA72`
- Location: `CELL 020C8FCF` / **Chapel of Arkay Cemetery**
- Final carried document: `BOOK 020C8FCE` / **Slave Trader's Note 8**
- House: `CELL 020B07D1` / **Slave Trader's House**
- Direct source: translated VIGILANT 1.8.2 ESM

## Direct physical implementation

The supplied VIGILANT ESM contains a named **Slave Trader** NPC.

The placed actor:
- uses **Bone Human Race**;
- is placed in the **Chapel of Arkay Cemetery**;
- has ragdoll-state data on the placed reference, supporting a dead/remains presentation;
- directly carries **Slave Trader's Note 8**.

This converts the Slave Trader from an inferred note-author/sarcophagus figure into a concrete ESM actor.

## Unique outfit

The Slave Trader uses `OTFT 020CAA6E` / `zzzCHOutfitSlaveTrader`.

The outfit contains:
- `ARMO 020CAA70` — **Wooden Ring**
- `ARMO 020CA4AB` — **Slave Trader's Coat**
- `ARMO 020CA4AA` — **Slave Trader's Hat**
- `ARMO 02285724` — **Slave Trader's Boots**
- `ARMO 02285725` — **Slave Trader's Gloves**

This is strong structural evidence that the named corpse/remains is deliberately authored as the Slave Trader rather than a generic skeleton.

## Pepe's sarcophagus testimony

In the Coldharbour main quest, Pepe says another living person emerged from the sarcophagus before the player.

Direct dialogue:

> Fools climb out from this sarcophagus every day. I don't remember all of them.
>
> No, wait. There was another one who was still alive like you. I believe he was a slave trader.
>
> But his eyes burned like fire. Yours are as cold as ice.

When the player asks where the slave trader went, Pepe answers:

> I don't know and I don't care.

The ESM does not mechanically point this INFO response to `NPC_ 020CAA71`, so strict identity should remain:

**fiery-eyed sarcophagus Slave Trader ↔ very strong candidate for the named Slave Trader NPC**

rather than a formally proven reference-link.

## Sir Henrik connection

**Knight of Julianos** contains direct Henrik dialogue:

> I don't quite remember. There was something about a slave trader and cheap booze...

When asked where the slave trader went:

> When I woke up again, he was no longer there. What a bastard, to lock me up in this hole...

The same quest contains a package:

- `PACK 02126606`
- EditorID `zzzCHsq07HenikStaySlaverHouse`

This directly connects Henrik's quest implementation to **Slave Trader's House**.

Therefore the Slave Trader is tied not only to the note trail but also to Sir Henrik's recurring imprisonment.

## Slave Trader's House

`CELL 020B07D1` is explicitly named **Slave Trader's House**.

**Slave Trader's Note 2** is physically placed there.

Henrik's quest package naming separately links him to the same house.

## Note 8 and the cemetery endpoint

The named Slave Trader's remains directly carry **Slave Trader's Note 8**.

The note quotes the opening of *Elegy Written in a Country Churchyard*:

> The curfew tolls the knell of parting day.
> The lowing herd winds slowly o'oer the lea,
> The ploughman homeward plods his weary way,
> And leaves the world to darkness and to me.

Its placement on a dead Slave Trader in the **Chapel of Arkay Cemetery** makes the cemetery/death association structurally deliberate.

It is still safest to say the body **carries** the note; authorship is strongly implied by the title/trail but not encoded as a separate author field.

## EditorID / LST clue

The NPC EditorID is:

`zzzCHlstSlaveTrader`

The embedded **lst** is noteworthy because a123999's supplementary background article identifies the VIGILANT Slave Trader with the protagonist/soul from Vicn's earlier **LST Bravil Underground**.

This EditorID is direct implementation evidence compatible with that cross-work interpretation.

However, an EditorID fragment is not by itself enough to establish the full prior-game biography.

Current source-separated model:

- **direct VIGILANT:** named Slave Trader actor, `lst` EditorID, house, outfit, Note 8, cemetery remains, Pepe/Henrik Slave Trader testimony;
- **supplementary:** this figure is the hero/soul from *LST Bravil Underground*.

## Relationship to the note trail

The direct ESM now resolves the final note acquisition paths:

- Note 6 → carried by **Sir Ralvas**
- Note 7 → included in **Marukh's death-item leveled list**
- Note 8 → carried by the named **Slave Trader**

This makes the notes more than eight loose environmental books.

See:
- `analysis/slave-trader-note-trail.md`

## Funeral / grave-name implementation caution

Three graves in the same Chapel of Arkay Cemetery use internal EditorIDs:

- `zzzCHSlaverTomb01` — **Johan's Grave**
- `zzzCHSlaverTomb02` — **Simon's Grave**
- `zzzCHSlaverTomb03` — **Tlass' Grave**

These are the names Martha seeks in **Funeral**.

The `SlaverTomb` EditorID prefix creates an implementation-level connection between the Slave-Trader namespace and the Funeral grave objects.

The current source pass does **not** prove what that connection means narratively.

Do not infer yet that:
- Martha is related to the Slave Trader;
- the Slave Trader is Johan, Simon, or Tlass;
- the Slave Trader created the graves.

Preserve this as a high-value implementation clue for later reconstruction.

## Relationship map

- **Slave Trader → owns/associated with → Slave Trader's House**
- **Slave Trader → carries → Note 8**
- **Slave Trader → dead/remains presentation → Chapel of Arkay Cemetery**
- **Pepe → remembers → fiery-eyed slave trader emerging from sarcophagus**
- **Sir Henrik → remembers being trapped by → slave trader**
- **Sir Henrik → quest package links to → Slave Trader's House**
- **Slave Trader namespace → internal EditorID link → Johan/Simon/Tlass grave activators**
- **a123999 → supplementary identifies → Slave Trader with LST Bravil Underground protagonist/soul**

## Canon boundary

The Slave Trader, note trail, fiery-eyed sarcophagus survivor, and LST-linked interpretation belong to Vicn/VIGILANT continuity.
