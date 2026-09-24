# Browser Bridge

The Browser Bridge is the local transport boundary between the Universal Capture userscript and Personal Agent OS.

It is intentionally small and dependency-free:

- Python standard-library HTTP server
- loopback-only binding
- per-device/local token
- durable SQLite staging
- idempotent event IDs
- revision-aware updates
- ACK only after SQLite commit
- no direct promotion into canonical knowledge

## Why it exists

The browser should not be the permanent home of high-volume Discord and browsing history.

The intended flow is:

    userscript staging
        -> loopback bridge
        -> durable SQLite inbox
        -> Knowledge Engine ingestion
        -> validated downstream project/profile/task/knowledge state

Once the bridge has durably acknowledged an event, the userscript may safely compact or delete its browser-side staging copy.

## Start the bridge

From an installed Personal Agent OS checkout:

    agent-os browser-bridge

Default address:

    http://127.0.0.1:8766

The startup JSON prints:

- batch endpoint
- manual-capture endpoint
- local bridge token
- SQLite database path

The token persists in:

    .agent-os/browser-bridge.token

The database persists in:

    .agent-os/browser-bridge.sqlite

Both live under the gitignored local Agent OS state directory.

To display the existing token later:

    agent-os browser-bridge-token

To inspect local counts:

    agent-os browser-bridge-status

## Userscript setup

Open the Tampermonkey menu for Agent OS Universal Capture and choose:

    Agent OS: Configure local bridge

Use the default batch endpoint unless the local bridge was started on another loopback port, then paste the token printed by Agent OS.

The userscript will then:

1. batch Browser Journal events automatically;
2. batch Discord records whenever a Discord tab is open;
3. wait for a durable acknowledgement;
4. remove acknowledged Browser Journal events from Tampermonkey storage;
5. replace acknowledged Discord full records with tiny seen markers;
6. retain everything locally if the bridge is offline or the acknowledgement is invalid.

## API

### POST /api/v1/browser/batch

Header:

    X-Agent-OS-Token: <local token>

Body:

    {
      "schema": "agent-os/browser-bridge-batch/v1",
      "batch_id": "...",
      "device": "...",
      "events": [
        {
          "event_id": "...",
          "source": "browser-journal | discord | ...",
          "event_type": "...",
          "source_key": "...",
          "occurred_at": "...",
          "device": "...",
          "payload": {}
        }
      ]
    }

Successful response:

    {
      "schema": "agent-os/browser-bridge-ack/v1",
      "durable": true,
      "acknowledged": ["..."],
      "stored": ["..."],
      "updated": ["..."],
      "duplicates": ["..."]
    }

An event is only safe for browser compaction when its ID is listed in `acknowledged` and `durable` is true.

### POST /api/v1/browser/capture

Accepts one normal Universal Capture payload. Stable identity is derived from site/content type/source ID or canonical URL, so repeated captures update or deduplicate rather than multiplying rows.

### GET /api/v1/browser/stats

Requires the local token and reports local event counts by source/state.

### GET /health

Returns only basic service health and does not expose stored event data.

## Knowledge Engine handoff

The bridge deliberately stops at durable staging.

Read waiting events:

    agent-os browser-bridge-pending --limit 100

After a downstream ingestion worker has durably persisted/promoted those records:

    agent-os browser-bridge-mark-ingested --event-id <id> [--event-id <id> ...]

This two-phase boundary keeps browser transport failures separate from knowledge interpretation and promotion.

Future Knowledge Engine workers should consume this queue through provider-neutral ingestion interfaces rather than writing project/profile state directly from the HTTP request thread.

## Deduplication and revisions

`event_id` is the stable logical identity.

If the same event ID arrives with the same payload hash, it is a duplicate and is still acknowledged because the existing durable row is sufficient.

If the same event ID arrives with changed content, the durable row is updated and returned in `updated`. This is important for edited Discord messages.

The userscript also fingerprint-checks a Discord record again before local compaction. If it changed while the HTTP request was in flight, it remains in IndexedDB and is sent again later.

## Storage

SQLite runs in WAL mode with normal synchronous durability, appropriate for a local staging queue with repeated idempotent delivery.

The bridge database is local high-frequency state and must remain outside Git. Canonical schemas, documentation, code, routing rules, and validated durable knowledge remain Git-backed where appropriate.
