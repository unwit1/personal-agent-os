# Dialogue corpus output specification

Each resolved dialogue row should contain:

- speaker display name
- speaker source ID
- speaker base/reference IDs where distinct
- quest
- scene
- scene action
- DIAL source ID
- INFO source ID
- prompt / RNAM override when present
- response text
- response number
- conditions
- previous INFO / PNAM
- resolution method
- confidence

## Character aggregate

For each character generate:
- exact resolved line count
- constrained candidate line count
- quests spoken in
- scenes spoken in
- high-frequency topics/entities
- source-ID list

## Storage

Keep the deterministic row corpus in structured data and derive human-readable character pages from it. Do not make prose pages the canonical dialogue store.
