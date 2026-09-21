# Evidence pointer pass 14

The library now has a stable citation target independent of Skyrim load order.

## Claim model

Derived lore claims should carry:

1. a normalized `source_id`;
2. the source plugin hash/version checkpoint;
3. record type and EDID where available;
4. an attribution class such as dialogue testimony, authored BOOK, quest objective, record name, or developer/debug evidence;
5. confidence/interpretation status.

## Example distinctions

**Gerhard is Lalanoah's father** is supported by explicit NPC/editor-ID and dialogue context and can be represented as a strong source-backed relationship.

**Yelem's Great Cat is Shezarr** is an attributed metaphysical proposition from Yelem's writings, not an objective identity assertion.

**Ja'cobee's EGG is the same Egg described by Yelem** remains an unresolved hypothesis despite thematic overlap.

This structure allows retrieval to return evidence first and synthesis second, reducing repeated model interpretation and token use.
