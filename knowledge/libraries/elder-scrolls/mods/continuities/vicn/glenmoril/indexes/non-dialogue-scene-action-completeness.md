# GLENMORIL non-dialogue SCEN action completeness

Source: raw `Glenmoril.esm`  
SHA-256: `5669018c81acf13147ff489f486963ecc3c57515a73ed9afd210c7ede85e1cc8`

This ledger opens the next ingestion frontier after closure of direct dialogue, BOOK, and MESG exact-text layers.

## Deterministic SCEN inventory

- SCEN records: **314**
- all parsed scene actions: **2,211**
- dialogue actions (type 0): **1,578**
- package actions (type 1): **461**
- timer actions (type 2): **172**
- non-dialogue actions requiring exact normalization: **633**

## Scene coverage shape

- scenes with dialogue actions: **282**
- scenes with no dialogue actions: **32**
- scenes with package actions: **139**
- scenes with timer actions: **131**
- scenes with both package and timer actions: **53**
- scenes containing only non-dialogue actions: **31**
- scenes with zero parsed actions: **1**

## Structural interpretation

The parser currently resolves:
- type 0 as dialogue actions, with actor alias and DIAL linkage;
- type 1 as package actions, with actor alias and PACK linkage;
- type 2 as timer actions, with actor alias and timing payload.

The direct-dialogue corpus already accounts for type-0 text. The new exact backlog is therefore **461 package actions + 172 timer actions = 633 non-dialogue actions**.

## Next normalization pass

For every non-dialogue action preserve:
- scene source ID / EditorID;
- owning quest source ID / EditorID;
- action index;
- action type;
- actor alias ID and resolved alias name where available;
- package FormID/source ID/EditorID for type 1;
- timer value for type 2;
- start/end phase fields;
- raw structural fields needed for later chronology reconstruction.

After exact preservation, promote only chronology/relationship claims supported by package targets, scene ordering, scripts, or corroborating text.
