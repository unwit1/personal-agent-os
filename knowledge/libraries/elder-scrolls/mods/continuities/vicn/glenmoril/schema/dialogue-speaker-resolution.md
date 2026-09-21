# Dialogue speaker resolution schema

Speaker attribution must be evidence-backed and may return one speaker, several eligible speakers, or unresolved.

## Resolution order

1. Explicit INFO speaker field, when present.
2. Scene dialogue action → Actor ID → quest reference alias.
3. INFO condition `GetIsAliasRef` → quest alias.
4. INFO condition `GetIsID` → NPC.
5. INFO condition `GetInFaction` → candidate NPC set.
6. Voice type constraints → unique or candidate NPCs.
7. Quest-wide dialogue conditions as additional filters.

Scene Actor IDs are quest alias IDs; aliases may resolve through forced references, unique actors, created objects, external aliases, or conditions.

## Output

- info_source_id
- dial_source_id
- quest_source_id
- scene_source_id (nullable)
- actor_alias_id (nullable)
- speaker_source_id(s)
- resolution_method
- confidence: exact | constrained | ambiguous | unresolved
- evidence pointers

Never assign a single speaker when the plugin only constrains a candidate set.
