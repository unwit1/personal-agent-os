# iCloud Mail Connector Architecture

> **Superseded 2026-09-23** by `docs/integrations/mail.md` (multi-account
> iCloud + EarthLink, read-only). This document is kept as the original design
> record.

Status: planned / implementation-ready
Privacy class: personal communications; local-first
Provider: Apple iCloud Mail via IMAP/SMTP

## Goal

Add an iCloud Mail provider to Personal Agent OS so agents can selectively retrieve
relevant mail without copying the mailbox into GitHub or normal agent memory.
The connector must be usable across supported clients through Agent OS/MCP while
keeping raw mail and credentials local.

## Authentication

Use an Apple **app-specific password**, not the user's normal Apple Account password.

Required local secrets:

- `ICLOUD_EMAIL` — full iCloud Mail address.
- `ICLOUD_APP_PASSWORD` — Apple-generated app-specific password.

These values MUST NOT be committed, written to canonical memory, candidate memory,
handoffs, logs, Google Docs, telemetry, or prompts. Production implementations
should prefer the OS credential store/keychain; environment variables are an
acceptable bootstrap mechanism.

Connection defaults:

- IMAP: `imap.mail.me.com:993`, implicit TLS.
- SMTP: `smtp.mail.me.com:587`, STARTTLS.
- Username: full iCloud Mail address.

Provider settings must remain configurable rather than hard-coded into retrieval
logic.

## Safety model

Initial capability is **read-only**. Sending, replying, forwarding, deleting,
moving, marking mail, or changing mailbox state must be disabled until separately
implemented and explicitly enabled.

Future outbound mail must use the Agent OS consequential-action approval boundary:
draft/preparation may be automatic, but sending requires explicit user approval by
default.

## Local data boundary

Raw message bodies, attachments, headers containing personal addresses, mailbox
state, and the searchable mail index stay local and gitignored.

Git may contain only:

- connector code and schemas;
- provider configuration templates without credentials;
- retrieval/ranking policy;
- redacted tests and fixtures;
- documentation and durable architectural decisions.

Do not mirror raw personal email to Google services as a fallback.

## Retrieval design

1. Authenticate locally over TLS.
2. Incrementally synchronize message metadata and text needed for search.
3. Store the derived index in a gitignored local data directory/database.
4. Track provider UID/UIDVALIDITY (or equivalent durable cursors) so subsequent
   syncs fetch only changes.
5. Normalize messages into a provider-neutral mail record.
6. Search/rank locally before model invocation.
7. Return only the smallest relevant excerpts/metadata needed for the user's task.
8. Fetch attachments or full bodies only on demand.
9. Treat quoted history and signatures as lower-value retrieval material when
   practical.

The implementation should support future providers (Outlook, Gmail, etc.) behind
the same provider-neutral interface rather than making iCloud special throughout
the application.

## Proposed provider interface

- `connect()`
- `health()`
- `sync(cursor=None)`
- `search(query, filters=None, limit=...)`
- `get_message(message_id, include_body=False)`
- `get_thread(thread_id)`
- `get_attachment(message_id, attachment_id)`

Mutating methods belong in a separate capability/interface so a read-only provider
cannot accidentally expose them.

## Proposed MCP surface

Read-only tools should eventually include:

- `mail.search`
- `mail.get_message`
- `mail.get_thread`
- `mail.sync_status`

Responses should be token-budgeted, identify the provider/account without exposing
credentials, and distinguish indexed snippets from freshly fetched full content.

## Suggested repository layout

```text
agent_os/
  integrations/
    mail/
      base.py
      models.py
      icloud.py
      index.py
      service.py
schemas/
  mail-message.schema.json
policy/
  MAIL_PRIVACY_POLICY.md
tests/
  fixtures/mail/          # synthetic/redacted only
  test_icloud_mail.py
  test_mail_privacy.py
```

Adapt names to the repository's existing Python package layout during
implementation rather than creating a competing architecture.

## Bootstrap UX

Provide a setup command such as:

```powershell
agent-os mail setup icloud
```

It should:

1. ask for the iCloud email address;
2. securely request the Apple app-specific password without echoing it;
3. save credentials to the supported local secret store;
4. test IMAP authentication;
5. report success/failure without printing secrets;
6. initialize the local mail index.

A noninteractive environment-variable path may also be supported.

## Validation / tests

Before enabling the integration:

- secret scanning proves credentials cannot enter tracked files/logs;
- TLS is mandatory;
- authentication errors are sanitized;
- sync is incremental and idempotent;
- deleted/changed remote messages are handled predictably;
- malformed MIME cannot crash indexing;
- HTML mail is converted/sanitized safely;
- attachments are not automatically sent to a model;
- retrieval obeys result/token limits;
- read-only mode performs no mailbox mutations;
- all fixtures are synthetic.

## Implementation sequence

1. Inspect existing package/config/secret-store patterns.
2. Add provider-neutral mail models and read-only interface.
3. Add secure local credential handling or integrate the existing secret store.
4. Implement iCloud IMAP connection and health check.
5. Implement incremental synchronization.
6. Implement local indexing/search.
7. Add the read-only MCP tools.
8. Add CLI setup/status/sync commands.
9. Add privacy/security tests and synthetic fixtures.
10. Update README and canonical policy where appropriate.
11. Validate on a local machine using the user's app-specific password.

## Definition of done

After code is implemented and merged, a fresh machine should require only the
repository plus local setup. The user supplies their iCloud address and Apple
app-specific password locally; Agent OS verifies the connection and builds its
local index. No password or raw mailbox content is committed to GitHub.
