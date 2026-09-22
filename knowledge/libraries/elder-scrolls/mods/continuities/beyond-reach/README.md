# Beyond Reach Lore Continuity

This directory is the Lorekeeper/Personal Agent OS continuity overlay for **Beyond Reach** (`arnima.esm`).

The default claim scope is `tes.mod.beyond-reach`. Material here may reference licensed Elder Scrolls lore, but Beyond Reach-specific claims must not be silently promoted into base TES canon. Conflicts and reinterpretations should retain provenance.

## Current ingestion state

Completed:

- **3,366** QUST/DIAL source records across `data/source-records/lore-records-0001.jsonl` through `0068`
- **196** normalized quest-catalog records
- **3,170** DIAL topic records in the source corpus
- **102** dialogue topics explicitly tagged `[Lore]`, normalized into the lore-topic catalog
- Breton/Evermore main-quest structural index
- Orc-route main-quest structural index
- thematic retrieval map for the explicit lore prompts
- continuity and source manifests
- JSONL quoting repairs for source batches 0057, 0063, and 0064

Current source-record boundary:

- QUST records retain titles, journal entries, objectives, aliases, condition counts, override provenance where available.
- DIAL records retain editor IDs, prompts/titles, quest provenance, and INFO counts.
- **Full INFO response text is not yet present in this continuity directory.**
- BOOK/NOTE text, MESG records, actor/speaker resolution, locations, artifacts, scenes/packages, and final claims remain pending.

## Retrieval guidance

Use the following layers in order:

1. `indexes/lore-topic-retrieval-map.md` for broad subject routing.
2. `indexes/lore-dialogue-topic-catalog/` for exact `[Lore]` prompt FormIDs and quest provenance.
3. `indexes/main-quest-structure.md` or `indexes/orc-main-quest-structure.md` for narrative-route structure.
4. `indexes/quest-catalog/` for lightweight quest lookup.
5. `data/source-records/` when exact raw QUST/DIAL metadata is required.

Do **not** treat a dialogue prompt as the NPC's answer. Prompts that ask about Namira, Direnni history, Orcs, Witchmen, politics, metaphysics, or other subjects are routing evidence until their INFO response records are ingested.

## Next ingestion stages

The highest-value next pass is full **INFO dialogue-response extraction**, including speaker/alias resolution, response text, conditions, quest/topic linkage, and route provenance.

After INFO:

1. BOOK/NOTE full text
2. MESG and other player-facing text
3. NPC/speaker and faction records
4. locations and world/cell mapping
5. artifacts and important items
6. scenes/packages where they clarify chronology or speaker identity
7. character/faction/concept dossiers
8. continuity-scoped evidence-backed claims
9. completeness and retrieval audits

See `continuity.json` and `source-manifest.json` for machine-readable status.
