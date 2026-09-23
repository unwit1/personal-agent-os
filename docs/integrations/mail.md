# Mail: EarthLink + iCloud (read-only, multi-account)

Status: Phase 1 implemented 2026-09-23 (branch `mail-multi-account`).
Supersedes the single-account design in `icloud-mail.md` (kept for history).

Agent OS keeps a **local, searchable copy** of the mail in your EarthLink and
iCloud accounts (and, later, your old PST archive) so Claude, Codex and other
agents can find what they need with one search. Nothing is sent, deleted,
moved or marked as read: access is read-only.

---

## Part 1 — Setting it up

### What you need

- **iCloud:** an Apple *app-specific password*. Create one at
  account.apple.com > Sign-In and Security > App-Specific Passwords. Do **not**
  use your normal Apple Account password.
- **EarthLink:** your EarthLink mailbox password.

Never paste a password into a chat with an agent. You type it into a hidden
prompt; it goes straight into Windows Credential Manager.

### Steps

```powershell
# 1. Tell Agent OS about each mailbox (a short name of your choice + the address)
agent-os mail account add --provider earthlink --id work-earthlink --email you@earthlink.net
agent-os mail account add --provider icloud    --id personal-icloud --email you@icloud.com

# 2. Store each password (hidden prompt; nothing is shown on screen)
agent-os mail account credential work-earthlink
agent-os mail account credential personal-icloud

# 3. Check the logins
agent-os mail health

# 4. First sync: the newest 200 messages of each Inbox
agent-os mail sync

# 5. See what happened
agent-os mail status
agent-os mail search "open enrollment"
```

Run `agent-os mail sync` again whenever you like; it only fetches what is new.

### More folders and older mail

```powershell
agent-os mail account folders work-earthlink --set "INBOX,Sent"
agent-os mail account folders personal-icloud --set "*" --exclude "Junk,Deleted Messages"
agent-os mail sync --backfill 1000      # also index up to 1000 older messages per folder
```

Backfill runs in steps and saves progress continuously, so you can stop it
and run it again later; it continues where it stopped. `mail status` shows,
per folder, how many messages the server has and how many older ones are not
indexed yet.

### Reading the status

`agent-os mail status` answers, per account:

| Question | Field |
|---|---|
| Is it configured? | `credential_available` |
| Did the login work? | `auth.auth_ok`, `auth.auth_error` |
| When did it last sync? | each mailbox's `last_started` / `last_completed` |
| Is it caught up? | `caught_up` (every mailbox finished without error) |
| What failed? | a mailbox's `status: partial` and `error` (for example `auth_failed`, `connection_failed`, `mailbox_unavailable`) |
| Is it using the fast path? | `capability_mode`: `condstore` (server reports changes) or `overlap` (checks recent messages) |

### Troubleshooting

| You see | Do this |
|---|---|
| `credential_missing` | `agent-os mail account credential <id>` |
| `auth_failed` on iCloud | make a new app-specific password and store it again |
| `auth_failed` on EarthLink | check the password in EarthLink webmail, then store it again |
| `connection_failed` / `timeout` | try again later; nothing is lost |
| a folder shows `partial` | run `agent-os mail sync` again; failed messages are retried |

### Privacy

- Mail, the search index and sync state stay in `.agent-local/mail/` on this
  computer, which is never committed to Git.
- Passwords live only in Windows Credential Manager (or, for headless use, an
  environment variable such as `AGENT_OS_MAIL_SECRET_WORK_EARTHLINK`).
- Work mail may contain HR-sensitive information. Nothing from it is copied
  into Agent OS memory automatically.

### Existing iCloud setup

If you set up iCloud with the older `agent-os mail setup icloud`, it becomes
the account `icloud` automatically and keeps using the password you stored
then. An existing local index is upgraded in place; a backup copy is kept
next to it (`index.sqlite3.v1-backup-<date>`).

---

## Part 2 — Developer details

### Modules (`src/agent_os/mail/`)

| Module | Responsibility |
|---|---|
| `accounts.py` | account model, provider defaults, `accounts.json`, secrets (keyring/env), legacy config migration |
| `imap.py` | `ReadOnlyIMAP` (allow-list wrapper), connection, error categories, FETCH parsing |
| `message.py` | RFC822 parsing, UTC dates, body text (HTML fallback), attachments, fingerprints |
| `store.py` | SQLite schema v2, observations/logical messages, dedup, threads, FTS5 search, migration |
| `engine.py` | per-account/per-mailbox incremental sync, ledger batching, status/log |
| `benchmark.py` | synthetic timing harness |
| `cli.py`, `__init__.py` | CLI and the public/MCP API (v1 functions kept) |

### Providers

| Provider | IMAP | Login | Credential |
|---|---|---|---|
| `icloud` | `imap.mail.me.com:993` SSL | email address (override `--username`) | Apple app-specific password |
| `earthlink` | `imap.earthlink.net:993` SSL/TLS | full email address | mailbox password |

SMTP endpoints (`smtp.mail.me.com:587`, `smtpauth.earthlink.net:587`,
STARTTLS) are recorded as `future_smtp` metadata only; no code connects to them.

### Identity

- Live observation: `src_` + hash(`live_imap`, provider, account_id, mailbox,
  UIDVALIDITY, UID). Different accounts, providers or UIDVALIDITY values never
  collide.
- Archive observation: `src_` + hash(`archive`, archive_id, folder, record_key).
- Logical message: `msg_` + hash(normalized content hash, Message-ID), with a
  collision suffix. Thread: `thr_` + hash(thread key).
- `account_id` is a user-chosen opaque ID; the email address is metadata.

### Schema v2 and migration

Tables: `mail_messages` (logical), `mail_sources` (observations; `state`:
`present`, `missing`, `stale_uidvalidity`, `superseded`), `mail_attachments`,
`mail_mailboxes` (sync state), `mail_fts` (FTS5). `PRAGMA user_version = 2`.

A v1 index (`messages`, keyed by mailbox+UID) is migrated when first opened:
file backup, then one transaction creating v2 tables, importing each row as a
`legacy` observation of account `icloud` with **UIDVALIDITY NULL** (never
invented), verifying counts, renaming the old table to `legacy_messages_v1`,
and setting the version. A failure rolls back and leaves the v1 table
untouched. On the first live resync, a legacy row whose UID and content match
a new observation is marked `superseded` (kept for provenance).

### Sync algorithm

See the `engine.py` docstring. Summary: EXAMINE → UIDVALIDITY check (retire
the old namespace on change) → UID SEARCH ALL → new UIDs (newest `limit` on
the first run, then above the high-water mark) + optional backfill below the
backfill mark → metadata-only overlap check of recent known UIDs (size/date
mismatch → refetch; flags updated), or `CHANGEDSINCE` flag updates with
CONDSTORE → known UIDs absent from the complete listing marked `missing` →
bodies in batches with `BODY.PEEK[]`. Per batch: parse, index, **commit
SQLite, then** mark ledger items processed and save the ledger once. State
and counts are saved after every batch. `last_completed` is set only when a
mailbox finished with no error.

UIDNEXT is recorded but used only as a hint. QRESYNC is not used yet.

### Ledger

Each (account, mailbox) has its own `IngestionLedger` under
`.agent-local/mail/ledgers/<account>/`, keyed by
`provider/account/mailbox/UIDVALIDITY/UID` and the raw-message hash.
`IngestionLedger.deferred_saves()` (new) writes the ledger once per batch
instead of after every call, and `claim(item_ids=...)` (new) claims a
specific item without sorting the ledger. The v1 `sync_records()` boundary
is unchanged (same ledger file, keys and per-message saves).

### Dedup and provenance

Evidence order: Message-ID with the same sender, same subject (ignoring
Re:/Fwd:) and dates within two days; exact normalized content hash; composite
date/sender/recipients/subject/body key. Content evidence never merges two
messages that carry different Message-IDs (the same text sent twice is two
emails). A reused Message-ID with different content stays a separate message. Observations are never deleted by dedup. If a source's
own content changes and nothing else shares its old logical message, the old
version is dropped and the new content indexed.

### Threads

References (root) → In-Reply-To (parent's thread) → own Message-ID. A reply
indexed before its parent is moved into the parent's thread when the parent
arrives. Messages with none of these headers are single-message threads;
equal subjects alone never merge.

### Search

FTS5 over subject, sender, recipients, body and attachment filenames/text;
user text is quoted term by term (no FTS syntax injection); LIKE fallback when
FTS5 is unavailable. Filters: accounts, providers, mailboxes, source kinds,
sender, recipient, `after` (inclusive) / `before` (exclusive) ISO dates.
Results carry `id`, `thread_id`, a 400-character snippet, source labels
(`work-earthlink:INBOX`, `pst_archive:pst-2019/Inbox`) and the v1 fields
`uid`, `mailbox`.

### Attachments

Filename, MIME type, size and SHA-256 are indexed for every attachment. Text
of `text/plain`, `text/csv`, `text/markdown` and `text/html` attachments is
extracted (20,000 characters) and searchable. Other types are
`metadata-only`; raw attachment bytes are not stored. PDF/Office extraction
through the shared document layer is the next step (see limits).

### Archive / PST seam

`mail.sync_archive_records(records, archive_id=..., source_kind="pst_archive")`
takes `{"folder", "record_key", "raw"}` records (RFC822 bytes), uses its own
ledger, and shares the index, dedup and search. No PST parser is included.

### MCP and CLI

MCP: `mail.accounts`, `mail.account_status`, `mail.sync` (`account_id`,
`mailbox`, `limit`, `backfill`), `mail.sync_status` (`account_id` optional),
`mail.search` (filters above), `mail.get_message` (`id`, or v1 `uid` +
`mailbox` + optional `account_id`), `mail.get_thread`. No send, delete, move
or flag tool exists.

CLI: `agent-os mail accounts | account add|credential|remove|enable|disable|folders |
setup icloud | health | status | sync | search | show | thread | benchmark`.

### Security

- `ReadOnlyIMAP` refuses every IMAP command outside an allow-list (LOGIN,
  CAPABILITY, LIST, SELECT read-only, UID SEARCH, UID FETCH, LOGOUT) with
  `ReadOnlyViolation`; UID STORE/COPY/MOVE/EXPUNGE and body fetches without
  PEEK are refused.
- Errors are reported as categories; server text (which can echo the login)
  is not passed on. Status, results, logs and `account-state.json` hold
  counts, IDs and categories only.
- Tests inject `THIS_IS_A_TEST_SECRET_DO_NOT_LEAK_12345` and assert it never
  appears in config, status, MCP output, logs or error text.

### Benchmark

`agent-os mail benchmark --messages N` (two synthetic accounts, real engine).
Measured 2026-09-23 on this machine:

| Messages | v1 per-message ledger saves | batched engine |
|---|---|---|
| 500 | 4.2 s (8.4 ms/msg) | 0.74 s (1.5 ms/msg) |
| 1,000 | 11.2 s (11.2 ms/msg) | 1.4 s (1.4 ms/msg) |
| 2,000 | 38.8 s (19.4 ms/msg) | 2.9 s (1.5 ms/msg) |
| 10,020 (2 x 5,010) | — | 23.6 s first import, 0.16 s no-change resync, 0.23 s for a 20-message delta, ~24 ms full-text search, ~19 ms filtered |

The v1 path's per-message cost doubles as the mailbox doubles (quadratic);
the batched engine's stays flat. Numbers vary run to run.

### Tests

`tests/test_mail_accounts.py` (fake IMAP server, synthetic messages): provider
defaults and logins, sanitized auth failure, per-account secrets, legacy
config, secret leakage, read-only enforcement, no UID collisions across
accounts/providers/UIDVALIDITY, idempotent resync with no body fetches,
newest-first limit and backfill, UIDVALIDITY rollover, changed content,
interrupted sync resume, ledger replay after commit, CONDSTORE flags and
missing messages, all-folders with exclusions, search filters, FTS fallback,
threads, reply-before-parent, live+archive provenance, reused Message-ID,
v1 migration, failed migration rollback, legacy supersede, MCP/CLI surfaces.
`tests/test_mail.py` (v1 behaviour) passes unchanged.

### Known limits

- The JSON ledger is rewritten once per batch; for mailboxes of tens of
  thousands of messages a SQLite-backed ledger would scale better.
- QRESYNC (vanished UIDs) is not used; deletions are detected from the full
  UID listing.
- PDF/Office attachment text is not extracted yet.
- No PST parser; only the import seam.
- Send/reply/delete/move/flag are not implemented and must go through a
  separate approval-gated action layer (draft -> approval -> send -> audit).
