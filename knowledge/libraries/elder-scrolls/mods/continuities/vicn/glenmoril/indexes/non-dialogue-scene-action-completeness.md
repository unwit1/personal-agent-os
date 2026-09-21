# GLENMORIL non-dialogue SCEN action completeness

Source: raw `Glenmoril.esm`  
SHA-256: `5669018c81acf13147ff489f486963ecc3c57515a73ed9afd210c7ede85e1cc8`

This ledger tracks the non-dialogue SCEN frontier after closure of direct dialogue, BOOK, and MESG exact-text layers.

## Deterministic SCEN inventory

- SCEN records: **314**
- all parsed scene actions: **2,211**
- dialogue actions (type 0): **1,578**
- package actions (type 1): **461**
- timer actions (type 2): **172**
- non-dialogue actions: **633**

## Exact-normalization status

- package actions normalized: **461 / 461**
- timer actions normalized: **172 / 172**
- total non-dialogue actions normalized: **633 / 633**
- owning quest links resolved: **633 / 633**
- actor alias names resolved: **633 / 633**
- package references preserved: **461 / 461**
- timer values decoded: **172 / 172**
- GLENMORIL package EditorIDs joined: **428**
- Skyrim master-package references retained by exact source ID: **33**

## Scene coverage shape

- scenes with dialogue actions: **282**
- scenes with no dialogue actions: **32**
- scenes with package actions: **139**
- scenes with timer actions: **131**
- scenes with both package and timer actions: **53**
- scenes containing only non-dialogue actions: **31**
- scenes with zero parsed actions: **1**

## Preserved fields

Every normalized non-dialogue action retains:
- scene source ID / EditorID;
- owning quest source ID / EditorID;
- action index and type;
- actor alias ID and resolved alias name;
- start/end phase fields and action flags;
- exact package source reference and local EditorID where available, or exact timer duration.

See `schema/non-dialogue-scene-action.md` and `indexes/non-dialogue-scene-action-normalization.md`.

## Next pass

Structural normalization is closed. The next pass should reconstruct scene choreography/chronology from package targets, phase ordering, timers, scripts, and corroborating text. Narrative claims should not be inferred from EditorIDs or package names alone.