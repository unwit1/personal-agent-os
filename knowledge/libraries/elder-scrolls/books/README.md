# Books

Normalized browse index and locally stored book records/texts when appropriate. Each record should identify title, source/game, author where known, continuity, provenance, and source record IDs.


## Work / witness model

Normalized books use stable work identities separately from source-specific witnesses.

- A **work** is the cross-source identity of a text, with a stable ID such as `tes.work.<slug>` for verified official Elder Scrolls works.
- A **witness** is one game record, source-corpus record, or mod-continuity embedding of that work.
- Textual variants, wrappers, spelling changes, annotations, placement, and presentation remain attached to the witness that contains them.
- Creating a work record does **not** elect one witness as the canonical normalized text. `canonical_text_status` stays `not_elected` until an appropriate first-party corpus and comparison policy exist.
- Mod continuities should reference central work IDs rather than copy central work text, while retaining local overlay metadata.

Current machine-readable catalog: `catalog.jsonl`. Individual work records live under `works/`.
