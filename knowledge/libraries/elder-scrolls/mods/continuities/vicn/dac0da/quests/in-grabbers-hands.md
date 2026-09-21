# In Grabbers' Hands

**Quest:** `zDcdSqPrisoner`  
**Title:** In Grabbers' Hands  
**Source:** `DAc0da.esm:00CEFE`  
**Continuity:** `tes.mod.vicn.dac0da`  
**Evidence mode:** QUST/VMAD/alias/item structure; no directly owned dialogue

## Objective

The quest has one explicit objective:

> Retrieve `Kye` from the target location and **restore your name**.

This wording is now backed by a concrete name/nymic item-and-script structure rather than being only a suggestive quest title.

## Radiant target location

Alias 2, `TargetLoc`, is a **location alias** selected by conditions rather than a fixed DAc0da location.

Its conditions require a base-game **clearable** location and a location containing the base-game **Boss** location-reference type, plus dungeon-type filtering.

This makes **In Grabbers' Hands** a radiant-style excursion into an ordinary qualifying Skyrim dungeon rather than a single bespoke DAc0da cell.

## Player and Boss aliases

- Alias 0, `Player`, is forced to the Skyrim player reference.
- Alias 3, `Boss`, is filled from the selected location's base-game **Boss** reference type.

The Player alias has script:

- `DcdSqPrisonerAliasScript`

The Boss alias has script:

- `DcdNymicStealerAliasScript`

The script name is strong structural evidence that the selected dungeon boss performs the quest's nymic/name-stealing role. The compiled PEX body is **not embedded in the ESM**, so the exact event sequence must remain unresolved unless the scripts are supplied separately.

## Kye = created Book of the Prisoner

Alias 4, `Kye`, is a **Created Object** alias whose base form is:

- `DAc0da.esm:00CF00`
- Editor ID: `zDcdPrisonerBook`
- FULL: **Book of the Prisoner**
- record type: MISC

The alias has the vanilla-style script:

- `defaultsetstageonplayeracquire`
  - `StageToSet = 10`
  - `myQST = zDcdSqPrisoner`

Therefore physically acquiring the Book of the Prisoner advances this quest to stage 10.

The associated `ALCA` value is alias ID 3, matching `Boss`. This is consistent with Kye being created relative to the Boss alias, though the raw ALCA field's low-level semantics are not fully documented and should not be overstated.

## Nymic object

The quest-level script `DcdSqPrisonerQuestScript` has two explicit properties:

- `Boss` -> quest alias 3
- `NymicObj` -> `DAc0da.esm:00CEFF`

`DAc0da.esm:00CEFF` is a MISC record:

- Editor ID: `zdcdItemNamePrisoner`
- FULL: **Bendu Olo Olo**
- model: `architecture\Dac0da\Dwe\Numidium\TotemGND_Nazeem.nif`
- keyword: base-game `VendorItemClutter`

A companion MESG record also exists:

- `DAc0da.esm:00CEFD`
- Editor ID: `zDcdAliasNamePrisoner`
- FULL: **Bendu Olo Olo**

The duplicated placeholder name plus the property name **NymicObj** strongly indicates that DAc0da creates/uses a tangible representation of a name/nymic during this quest.

However, the ESM alone does **not** expose the compiled Papyrus body that would prove exactly when or how the placeholder is replaced with the player's current name. The library should therefore record the mechanic as:

> **structurally implemented name/nymic theft and recovery; exact runtime rename logic pending PEX/source-script access**

rather than claiming an unobserved implementation detail.

## Link back to Numidium Tertius

`zDcdMq04` — **Numidium Tertius** has a quest-script property named `qPrisoner` pointing directly to `zDcdSqPrisoner`.

This proves that **In Grabbers' Hands** is an embedded/linked event within the broader Numidium Tertius machinery, even though it sends the player into a radiant Skyrim dungeon.

## Grabber interpretation boundary

The quest title directly invokes **Grabbers**.

Elsewhere, the Augur says Grabbers can "suck out all sorts of things," and UNSLAAD independently associates Grabbers with Adjacent-Place/Lyg travel.

The additional QUST/VMAD evidence now establishes that DAc0da couples the Grabber quest with:

- a nymic-stealer boss script;
- a named nymic object;
- a Book of the Prisoner;
- an explicit objective to restore the player's name.

That is sufficient to promote **Grabbers <-> stolen name/nymic** from a loose thematic possibility to a strong DAc0da mechanical relationship.

The exact metaphysical meaning of "name," and whether it is identical to any other Vicn work's true-name concept, remains unresolved.
