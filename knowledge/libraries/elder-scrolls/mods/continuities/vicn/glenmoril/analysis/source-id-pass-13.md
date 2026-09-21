# Source-local identifier pass 13

GLENMORIL records need identifiers that remain stable when the plugin's load-order index changes.

## Canonical source ID

Use:

`Glenmoril.esm:<local-formid>`

The raw Form IDs observed in this extraction begin with `04`, but that prefix is load-order dependent. For records belonging to Glenmoril.esm, strip the observed load-order byte and retain the lower 24-bit local Form ID.

Examples:

- raw `04014E8E` → `Glenmoril.esm:014E8E` — Black Book: Debug
- raw `0406EDB1` → `Glenmoril.esm:06EDB1` — Threatening Letter from Ja'zel
- raw `04007733` → `Glenmoril.esm:007733` — The Way is Blocked
- raw `04009B59` → `Glenmoril.esm:009B59` — The Blue Bird
- raw `0401230D` → `Glenmoril.esm:01230D` — Tainted Orphan
- raw `04017530` → `Glenmoril.esm:017530` — Broken Egg
- raw `04017733` → `Glenmoril.esm:017733` — Or the Gospel
- raw `040175EF` → `Glenmoril.esm:0175EF` — Zuzu the Oneiromancer

## Storage rule

Preserve both fields:

- `source_id`: stable plugin-local ID
- `observed_form_id`: raw Form ID from the analyzed load order

Do not use the observed `04` prefix as persistent identity.
