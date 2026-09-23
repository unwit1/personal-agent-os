# Semantic pass 13 — batch 33: duplicate/encoded book audit

This batch prevents several text-bearing records from being mistaken for distinct lore sources.

## Deep Bible pair

- BOOK 0520D504 — dealsdeepbible
- BOOK 0537195F — dealsdeepbibletransl

The extracted text is byte-for-byte identical.

SHA-256 of full extracted text:
3881fda148c8642b83bfb5524d9d08d4e16e902b51ea14f10b454c7651ff2265

Despite the second editor ID containing "transl", it does not contain a translated English text in the plugin extraction.

The visible content is an Esperanto-like/constructed-language newsletter-style passage rendered in a Daedric font.

Lorekeeper policy:
- preserve both records/placements;
- deduplicate semantic content;
- do not invent a translation from the editor ID;
- do not treat the pair as two independent confirmations of Brethren theology.

## Five magical-school reference books

The following records all contain the exact same ciphertext:
- 053E63DA — restoration reference
- 053E63DB — alteration reference
- 053E63DC — destruction reference
- 053E63DD — illusion reference
- 053E63DE — conjuration reference

Each extracted text has the same SHA-256:
f80c3ea2f3d060ac36272c892f2243ca860a598bdd1cf79c12ec0caadd12c15c

Therefore the text itself does not encode five distinct school-specific treatises in the raw plugin.

Any school-specific gameplay function must come from record identity, placement, scripts, or quest logic rather than distinct readable book prose.

## Significance

Text-bearing-record counts can overstate semantic source diversity.

This batch establishes a deduplication rule:
**identical normalized/full-text hashes are one semantic text instance with multiple record/placement variants unless other metadata materially changes interpretation.**
