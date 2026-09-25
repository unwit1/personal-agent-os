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


## Creator identity layer

Creator follows are reconciled through a provider-neutral profile graph under
`knowledge/personal/creators/index.json`. A creator profile can accumulate
confirmed provider accounts, aliases/handles, observed profile links, watch IDs,
cross-provider discovery queries, provenance, and candidate Discord identities.

Automatic association is conservative. Exact provider IDs, exact canonical
account URLs, exact profile links already observed on a confirmed creator page,
and a unique high-confidence handle/alias may identify the same creator across
providers. Display-name-only evidence does not silently merge identities.

When a creator follow arrives through the local browser bridge, Agent OS now:

1. promotes the capture into the proactive watch graph;
2. creates or updates the canonical creator profile;
3. links the watch target back to that creator profile;
4. records aliases and external/profile links already visible on the source page;
5. checks the locally imported Discord message archive for matching author aliases
   and stores those as identity candidates rather than confirmed matches;
6. queues cross-provider discovery for likely official websites, Nexus Mods,
   GitHub, YouTube, Discord, Patreon, Reddit, and direct feeds.

The bridge exposes `POST /api/v1/browser/follow/status` so supported browser
surfaces can resolve an account to an existing creator profile. The userscript
uses that response to show `✓ Following` on another supported site when Agent OS
already knows that account belongs to a followed creator.

Use `agent-os creator-list` to inspect canonical creator profiles and
`agent-os creator-discovery-pending` to see identities waiting for deeper
cross-provider enrichment.

Creator identity and monitoring are intentionally separate. A creator profile is
the canonical person/brand identity; provider-specific watch targets are the
sources polled for releases, uploads, repositories, mods, posts, feeds, and other
activity. The planned worker pipeline below remains responsible for actually
refreshing those sources and notifying on meaningful changes.
