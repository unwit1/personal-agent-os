# Generic Non-Quest VMAD Decoder

## Scope

This checkpoint tests the remaining non-MGEF, non-QUST VMAD records. A record type is accepted as generic only when the generic VMAD parser consumes the entire subrecord byte-for-byte.

## Exact generic records

- 26 / 26 NPC_, ARMO and ACTI records decode with zero trailing bytes and zero failures.
- Record mix: 20 NPC_, 4 ARMO, 2 ACTI.
- 26 script attachments across 7 distinct script names.
- 27 properties: 25 Object and 2 Int32.
- 25 object-property relations resolve to canonical Forms; 0 unresolved targets.
- 5 attachments have supplied PSC source.
- 2 exact imported-baseline comparisons are available and both are identical VMAD forwards.

## PERK boundary discovery

All six supplied PERK VMADs parse a valid generic script/property prefix but retain a record-specific tail afterward. Tail sizes are 87, 89, 97 or 98 bytes.

Those six PERK VMADs are not marked decoded. They are inventoried for a specialized fragment decoder.

The parser invariant established here is:

generic bytes consumed == full VMAD byte length

before a record can be classified as generically decoded. A valid prefix alone is insufficient.

## Rule status

No attachment, property or tail pattern is an approved Simonrim rule.
