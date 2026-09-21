# Continuities and consumers

The Knowledge Library is setting-agnostic. Each setting gets its own directory under `knowledge/`; the retrieval/evidence engine remains generic.

## Continuity graph

Continuity is independent of source reliability. A claim may be strongly supported inside a fan/project continuity without being asserted as base canon. Continuities use explicit relationships: `extends`, `forks_from`, `adapts`, `compatible_with`, `conflicts_with`, and `supersedes`.

Overlays are composable only when explicitly selected. Selecting Beyond Skyrim does not select VICN, and vice versa. Retrieval packets should eventually expose active continuity and the originating continuity/module for every returned claim/evidence item.

## Consumer adapters

External projects may consume rich lore evidence without inheriting the lore ontology. Knowledge Framework is the first consumer example. KF owns its intentionally simple gameplay taxonomy; Lorekeeper only retrieves compact evidence and maps against allowed KF tags. It must never invent a KF tag.

Confirmed mappings are durable and reusable. Model/rule suggestions remain derived candidates until reviewed, so repeated tagging does not repeatedly spend model tokens and uncertain guesses do not silently become taxonomy truth.

## Intended KF flow

1. Receive a KF book/item plus the allowed KF taxonomy.
2. Select the setting and active continuity overlays.
3. Reuse a confirmed mapping when one exists.
4. Otherwise retrieve a small evidence packet from the lore library.
5. Map only to allowed KF tags, using deterministic/rule-based matches first.
6. Escalate ambiguous cases only when needed.
7. Persist reviewed mappings for reuse.
