# Proactive Watch Graph

Agent OS treats following as a durable intelligence primitive, not a bookmark list.

A watch target may represent a person/creator, topic, project/repository, book or series, web serial, webcomic, mod author, community, product, feed, or arbitrary page/search. Browser captures with `intent: follow` should be promoted into this graph after normal ingestion/review rules.

Durable definitions live in `knowledge/personal/watching/index.json`. High-frequency observations, fetched pages, feed entries, search results, hashes, and change history should remain in local SQLite so continuous monitoring does not create noisy Git commits.

Each target records a stable identity, type, canonical URL, source/provider metadata, priority, adaptive refresh policy, related projects/topics, search queries, provenance, and notification policy. Collection and notification are deliberately separate: workers may research targets continuously while surfacing only meaningful changes.

## Planned worker pipeline

1. Select active targets due for refresh.
2. Prefer direct structured sources (RSS/Atom, release feeds, APIs) when available.
3. Run provider/site adapters and broader web searches where needed.
4. Normalize observations and deduplicate them against prior observations.
5. Score novelty and relevance to known projects, interests, commitments, and knowledge.
6. Send useful findings through the Knowledge Engine as candidates with provenance.
7. Update last-checked/change state locally.
8. Notify only according to the target's notification policy.

The browser userscript is a capture surface. It should keep emitting provider-neutral `follow_target` records; Agent OS owns scheduling, reconciliation, knowledge promotion, and notifications.
