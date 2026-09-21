# GLENMORIL source-record schema

A normalized source record should expose at least:

```yaml
source_plugin: Glenmoril.esm
source_sha256: 5669018c81acf13147ff489f486963ecc3c57515a73ed9afd210c7ede85e1cc8
source_id: Glenmoril.esm:XXXXXX
observed_form_id: 04XXXXXX
record_type: BOOK
editor_id:
title:
continuity: tes.mod.vicn.glenmoril
provenance_class:
text:
```

## Provenance classes

- `glenmoril-original` — source-specific narrative/lore text
- `reused-official` — copied/reused official Elder Scrolls text
- `debug-structural` — developer/debug evidence
- `mechanical-book-record` — BOOK used primarily as spell/item/mechanic
- `unknown` — classification pending

Derived claims should point to `source_id`, not merely a filename or title.
