# Executive applicant workflow contract

Status: binding contract for the implementation tasks of run `run-20261002T170546Z-ece407`
(operator spec, 2026-10-02). It extends `executive-window.md` and
`applicant-executive-design.md`; where it conflicts with them, this document wins for the
features below. Implementers must not change a name, signature, key or id fixed here without
a `needs_decision` report. Anything marked **OPEN QUESTION** is a best guess to be verified
against the Dashboard checkout by the task that first touches it.

## 0. Operator decisions that shape everything

1. **No Outlook, no COM.** The operator's change supersedes the earlier Outlook instruction.
   Nothing in Agent OS imports `win32com`, `pythoncom` or `Outlook.Application`, and the
   Applicant Dashboard's `email_sender` is not used for sending ("hasn't been working").
   Mail goes out over **SMTP submission** and a copy is stored with **IMAP APPEND** to the
   sending account's Sent folder, authenticated with the credential already in the keyring.
2. **Nothing sends without the Send click.** Planning an email only produces a compose
   payload. The only code path that sends is `POST /api/send`, which the operator's Send
   button calls. No registered action, no model tool and no `/api/chat` route sends mail.
3. **The Dashboard stays the system of record.** Executive code reaches it only through
   `DashboardGateway` methods that call the Dashboard's own Python functions. Never raw SQL
   writes, never `UPDATE`/`INSERT` from Agent OS, never edits of `openings_settings.json`
   outside the Dashboard's own save functions.
4. **Privacy.** Only allowlisted applicant fields cross the gateway and reach the window,
   the compose payload, the audit trail or a model prompt (section 5.3). EEO, AAP and
   self-identification data never do.
5. Tests use synthetic data and fakes only: no real mail, SMTP, IMAP, Dashboard database,
   keyring or network. Every test file starts with
   `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))`.

## 1. What already exists (read, do not rebuild)

| Piece | Where | Relied on for |
| --- | --- | --- |
| `DashboardGateway` Protocol, `LocalDashboardGateway`, `SyntheticDashboardGateway`, `_project`, `_review`, `_REVIEWABLE`, `_MATCH_FIELDS` | `executive/gateway.py` | Only boundary to the Dashboard; `ranked(0)` and `match_for(ref)` supply ranking and match reasons |
| `needs_action`, `suggestions`, `_fits`, `_project` (view fields), `REVIEWABLE_STATUSES`, `ADVISORY_LABEL`, `plan_outreach`, `approve_batch`, `send_batch` | `executive/applicants.py` | Ranking rule (`suggestions`), fit rule (`_fits`), interview slot planning |
| `Registry.register_provider/register_action/outstanding/invoke/confirm`, `REGISTRY` | `window/registry.py` | Items, item options, preview then Confirm |
| `Api.get/post`, `make_handler`, session token on every POST, loopback-only bind | `window/server.py` | HTTP surface; `POST /api/send` is added here |
| `PendingStore`, `ItemState`, `window_home()` | `window/confirm.py` | Confirm tokens (15 min TTL), `audit.jsonl`, dismiss/snooze, the window home directory |
| `actions_executive.py` (`executive.plan_interviews`, `.approve_batch`, `.reach_out`), `actions_email.py` (`email.reply_draft`, `email.send`), `actions_items.py` | `window/` | Existing actions; changes in section 9 |
| `providers_applicants.applicant_items`, `providers_mail.mail_items` | `window/` | Work tab applicant groups; mail threads (Work or Personal by scope) |
| `rtec_applicants` (`_project_root`, `_connect_readonly`, `_audit_access`, `_ALLOWED_STATUSES`, `openings_status`, `get_summary`) | `src/agent_os/rtec_applicants.py` | Read-only Dashboard access, local access audit, status allowlist |
| `mail.accounts` (`Account`, `PROVIDERS[...]["future_smtp"]`, `["hosted_future_smtp"]`, `get_secret`, `load_accounts`, `mail_scope`) | `src/agent_os/mail/accounts.py` | SMTP settings and the keyring credential |
| `mcp_server._window_run_schema`, `_window_run` | `src/agent_os/mcp_server.py` | Model tool is generated from the live registry, so registering an action makes it a tool |

Facts that constrain the design:

- `executive_window.run` in the MCP server runs in a **different process** from the window
  server and resolves `item_id` against `registry.outstanding()`. Therefore (a) item ids that
  the UI can act on must resolve through shared registry code (section 5.2), and (b) a compose
  produced by a model-invoked action must reach the window through the **file-backed compose
  store** (section 3.2), not through the HTTP response.
- `mail.imap.ReadOnlyIMAP` refuses every write command and `Account.read_only` is always
  true. The Sent-folder copy therefore uses a **separate, write-capable connection** in
  `mail/send.py`. The read-only guard and the sync path are not changed.
- `PROVIDERS["earthlink"]["future_smtp"]` is `smtpauth.earthlink.net:587 starttls`;
  `hosted_future_smtp` is `smtpauth.hosting.earthlink.net:587 starttls` for addresses on the
  operator's own domain hosted by EarthLink (the same split `default_server` applies to IMAP
  through `own_domains`). iCloud is `smtp.mail.me.com:587 starttls`. These are the defaults.
- The Dashboard status allowlist is `rtec_applicants._ALLOWED_STATUSES`: New, Interested,
  Interview Requested, Clarification Requested, Interviewing, Offered, Denied, Disqualified,
  Hired, Inactive.

## 2. Dashboard names (not verified: OPEN QUESTIONS)

`rtec_applicants._project_root()` resolves to `C:\Users\HR.RTEC\Projects\Job Applicant
Dashboard` and the directory exists on the operator's machine, but the design task's
sandbox refused read access outside its worktree, so **none of the names below were
verified**. The first implementation task with access (the gateway task) must read the
Dashboard read-only, replace each guess, and list the verified names in its handoff. Until
then the `LocalDashboardGateway` methods must isolate every guess in one private helper per
function so a rename is a one-line change, and must raise
`DashboardGatewayError("<operation> is not available in this Dashboard checkout")` rather
than fall back to SQL when a guessed name does not exist.

| Needed | Best guess (OPEN QUESTION) | Known evidence |
| --- | --- | --- |
| Openings settings read | `openings.load_settings() -> dict` | The operator named `openings.py load_settings`; settings live in `Config/openings_settings.json` with keys `transit_driver_groups` (list of group names), `office_positions` (name to bool), `max_drive_minutes`, `nearby_offer_minutes` (`rtec_applicants.openings_status`) |
| Which groups are open today | `openings.evaluate(settings, today=None)` | Named by the operator; presumably returns per-group or per-position open state for a date |
| Open groups reachable from a place | `openings.open_groups_in_range(settings, county_or_origin, ...)` | Named by the operator; used by `opening_match` through `groups`/`group_label` |
| Openings save | `openings.save_settings(settings)` | The operator says "openings.py's own save functions"; there may be several (for example per group or per office position). **Which function closes, adds or removes a group, and whether openings carry a per-county count or are a boolean per group, is unknown.** |
| Area manager for a county | `area_managers.manager_for_county(county) -> manager` | Named by the operator; the manager object's shape (name, email attributes) is unknown, so `manager_for_county` in the gateway normalizes it to `{name, email}` |
| Applicant status update | `database.set_status(applicant_key, status)` or `database.update_applicant_status(...)` | `rtec_applicants` only reads `status`; the Dashboard UI changes it somewhere in its own code |
| Journal / event entry | `database.add_journal_entry(applicant_key, text, ...)` or `events.log_event(...)` | `agent_events` outbox table exists (`event_id`, `event_type`, `source_component`, `payload_json`); a user-facing journal may be separate |
| Email-sent record | `database.record_email_sent(applicant_key, kind, ...)` | The Dashboard has `denial_email_drafted_at` / `denial_email_sent_at` columns, so a recorder for sent mail may exist |

Open questions for the operator or the gateway task, in priority order:

1. **Openings model.** Is an opening a boolean per transit group (county group) or a count
   per county? Section 4.1 normalizes to `open_count`; if the Dashboard only has a boolean,
   `open_count` is 1 or 0, `quit` and `new` both set it to 1, and `close` sets it to 0.
2. **How does a county map to a group?** `group_label` is the Dashboard's label for the group
   that covers the county. If one group covers several counties, closing "X" closes the whole
   group, and the preview in `preview_opening_change` must say so (field `affects`).
3. **Hold.** The Dashboard has no `Hold` status. This contract maps hold to "status
   unchanged, journal note, plus an Executive-side hold ledger" (section 6.3). Confirm.
4. **Status after send.** Section 4.4 maps `outreach` to `Interested` (only from `New`) and
   `interview` to `Interview Requested`. Confirm, or name the Dashboard's own transitions.
5. **Truncated operator message.** The operator's From-account instruction was cut off after
   "default: the work EarthLink account for applicant and manager mai[l]". This contract
   assumes: default From is the work-scope EarthLink account for `outreach`, `interview` and
   `manager` kinds; for `reply` the default is the account the thread arrived on, else the
   personal-scope account. Confirm the rest of that sentence.
6. **Which candidates belong to a county** (section 5.4): the rule uses applicant county or
   county preference, then `match_for(...).groups` / `.group_label`. Verify what `groups`
   contains.

## 3. Compose

### 3.1 Payload

Every action that plans an email returns, as its `result`:

```json
{"compose": {
  "to": "applicant@example.com",
  "subject": "...",
  "body": "...",
  "kind": "outreach",
  "applicant_ref": "ref-opaque",
  "county": "Example"
}}
```

- `to`, `subject`, `body`, `kind` are always present. `to` may be an empty string when the
  address is unknown; the panel then forces the operator to type one.
- `kind` is one of `outreach`, `interview`, `manager`, `reply`.
- `applicant_ref` (optional) is present for every applicant-related kind: `outreach`,
  `interview`, and `manager` (the applicant the manager email is about). It is the opaque
  reference only.
- `county` (optional) is present when known.
- Optional extras (a consumer must ignore unknown keys): `compose_id` (added by the compose
  store, section 3.2), `from_account` (suggested sending account id, section 4.5),
  `in_reply_to` (Message-ID, for `reply`), `thread_id` (for `reply`), `warnings` (list of
  short strings, for example `"no area manager found for Example County"`,
  `"no interview slots available"`), `batch_id` (when produced from an approved outreach
  batch).
- A compose payload never contains EEO or self-ID data, document paths, notes, or any
  applicant field outside the allowlist in section 5.3. The `to` address of an applicant
  comes from `rtec_applicants.get_summary(ref)["email"]`, the same source `send_batch` uses.
- Header injection: `to` (one or more addresses separated by `,` or `;`), `subject` and
  `in_reply_to` must not contain CR or LF. `/api/send` enforces this; handlers should too.

A compose-producing action is **never consequential** (it only drafts). It returns
`{"status": "done", "result": {"compose": {...}}}` through `Registry.invoke`.

### 3.2 Compose store and delivery to the window

New module `window/compose.py`, class `ComposeStore(home)`:

- Files `window_home()/compose/<compose_id>.json`; `compose_id` is
  `"cmp-" + secrets.token_hex(8)`. Atomic write (reuse the `_write_json` pattern in
  `confirm.py`).
- `create(payload: dict) -> dict` stores the compose and returns it with `compose_id` and
  `created_at`; `list() -> list[dict]` returns the open composes oldest first;
  `get(compose_id)`, `discard(compose_id)`; composes expire after 24 hours.
- Every compose-producing action handler calls `ComposeStore.create` before returning, so the
  result already contains `compose.compose_id`. This is what lets a compose made by the
  model, in the MCP process, appear in the window: the window polls `GET /api/compose`.
- `GET /api/compose` returns `{"composes": [compose, ...]}`. `POST /api/compose/discard`
  with `{"compose_id": "..."}` removes one and returns `{"discarded": true}`. The UI opens the
  panel for any compose it has not shown yet; when the UI invoked the action itself it opens
  the panel straight from `result.compose`.
- The store holds drafts only; it contains addresses and message text, so it lives under
  `window_home()` (local, gitignored), is never logged to `audit.jsonl` in full (the audit
  keeps `compose_id`, `kind`, `applicant_ref`, `county` only), and is never sent to a model.

### 3.3 Compose panel (static UI)

An editable panel with **From** (select), **To**, **Subject**, **Body** (textarea), a **Send**
button and a **Discard** button. Fields are plain inputs: the operator may change all of
them. Send posts the *edited* values. While a send is in flight the button is disabled; on
`sent: true` the panel shows "Sent" and closes; on `sent: false` it stays open, shows the
error text verbatim in an error style, and keeps the operator's edits. No auto-send, no
timers, no send on Enter. Applicant, manager and reply composes use the same panel.

## 4. Sending

### 4.1 `POST /api/send`

Token-protected like every POST. Request:

```json
{
  "compose_id": "cmp-0123456789abcdef",
  "from_account": "work-earthlink",
  "to": "applicant@example.com",
  "subject": "...",
  "body": "...",
  "kind": "outreach",
  "applicant_ref": "ref-opaque",
  "county": "Example",
  "in_reply_to": "<message-id>"
}
```

`to`, `subject`, `body`, `kind` are required; the rest are optional. The values in the request
are what is sent (the operator's edits), not what is stored under `compose_id`; `compose_id`
is used to discard the stored draft after success and for audit. Response, always HTTP 200
for a handled send attempt (validation problems keep the existing 400 `{"error": ...}`):

```json
{"sent": true, "message_id": "<generated@host>"}
```
```json
{"sent": false, "error": "NOT SENT: <specific reason>"}
```

Rules:

1. Every failure message starts with the literal prefix `NOT SENT: `. The text is specific and
   safe: it names the stage (`missing credential for account work-earthlink`,
   `SMTP authentication failed`, `SMTP connection failed`, `recipient refused: <address>`,
   `invalid recipient address`, `subject contains a line break`) and never contains the
   credential, the server's raw text if that echoes the login name, or the message body.
2. If SMTP delivery succeeded but the Sent-folder copy failed, the result is still
   `{"sent": true, "message_id": ..., "warning": "Sent, but the copy could not be saved to the Sent folder: <category>"}`.
   The mail was delivered, so it must not be reported as NOT SENT and must not be retried
   automatically.
3. **Applicant status is recorded only after a successful send.** If `sent` is `true` and
   `kind` is `outreach` or `interview` (and `manager` with an `applicant_ref`, journal only,
   section 4.4), the server calls `gateway.record_applicant_sent(applicant_ref, kind, to,
   subject)` and adds `"recorded": {"journal_id": ..., "status": "<new status or null>"}` to
   the response. If recording fails the mail is still `sent: true`; the response adds
   `"record_error": "Sent, but the Dashboard was not updated: <reason>"`, and the Dashboard
   update stays available as a retry through the sent ledger (section 4.6). A failed send
   never touches the Dashboard.
4. No second send of the same `compose_id`: after a successful send the stored compose is
   discarded, and a repeated `compose_id` returns `NOT SENT: this draft was already sent`.
5. The send runs in the handler thread of the window server's own process (`ThreadingHTTPServer`
   handler threads); there is no queue and no background retry.
6. The audit line (`audit.jsonl`) records `{"send": true, "kind", "applicant_ref", "county",
   "from_account", "sent", "message_id"}` only: no addresses, subject or body.

### 4.2 `SendTransport`

New module `src/agent_os/mail/send.py` (importable without network; imports of `smtplib` and
`imaplib` are at module top, no `win32com`, no `pythoncom`):

```python
@dataclass(frozen=True)
class SendResult:
    sent: bool                      # True once SMTP accepted the message
    message_id: str | None          # the Message-ID header we generated
    error: str | None = None        # "NOT SENT: ..." when sent is False
    warning: str | None = None      # set when sent but the Sent-folder copy failed

class SendTransport(Protocol):
    def send(self, to: str, subject: str, body: str) -> SendResult: ...
```

`send` is the whole interface; a transport instance is already bound to one account and,
where relevant, an `in_reply_to`. Construction goes through a factory so the server can pick
the From account per send:

```python
TransportFactory = Callable[[str, str | None], SendTransport]   # (from_account_id, in_reply_to)
```

`SendTransport.send` never raises for delivery or configuration problems; it returns
`SendResult(sent=False, error="NOT SENT: ...")`. Programming errors may still raise and are
turned into `NOT SENT: <ExceptionType>` by the server.

### 4.3 `SmtpImapTransport` and `FakeTransport`

`SmtpImapTransport(account: Account, *, in_reply_to=None, smtp_factory=None, imap_factory=None,
secret_lookup=None, clock=None)`:

1. Build the message with `email.message.EmailMessage`: `From` is `Account.email`, `To`,
   `Subject`, `Date` (`email.utils.formatdate(localtime=True)`), `Message-ID`
   (`email.utils.make_msgid(domain=<domain of From>)`), optional `In-Reply-To` and
   `References`, plain-text UTF-8 body. Reject CR/LF in header values first.
2. Credential from `mail.accounts.get_secret(account)` (keyring first, then the account's
   environment variable; see `_lookup`). A missing credential is
   `NOT SENT: missing credential for account <id>` (no secret in the message).
3. SMTP settings from `smtp_settings(account)` in `mail/accounts.py` (new, small): provider
   `future_smtp`, or `hosted_future_smtp` when the account address is not in `own_domains`
   (mirrors `default_server`); an explicit `smtp_host`, `smtp_port`, `smtp_security` on the
   account (new optional fields, saved by `save_accounts`) override them. `security` is
   `starttls` (587 by default) or `ssl` (465, implicit TLS). TLS is always verified with
   `ssl.create_default_context()`; no fallback to plaintext, ever. Timeout 30 seconds.
4. `login(account.login_name, secret)` then `send_message`. Map `SMTPAuthenticationError` to
   `SMTP authentication failed`, `SMTPRecipientsRefused` to `recipient refused`,
   `SMTPConnectError`/`OSError`/timeout to `SMTP connection failed`, `ssl.SSLCertVerificationError`
   to `TLS certificate could not be verified`, anything else to `SMTP error: <ExceptionType>`.
   Exception text is not copied (servers echo login names).
5. After SMTP accepts, append the same bytes to the Sent folder over a **write-capable** IMAP
   connection (its own `imaplib` connection built with the same TLS rules as `mail.imap.connect`;
   do not use `ReadOnlyIMAP`). Resolve the Sent folder from `LIST` special-use flag `\Sent`,
   else the first existing name among `Sent`, `Sent Items`, `Sent Mail`, `INBOX.Sent`; APPEND with
   flag `\Seen` and the send time. Any failure here sets `SendResult.warning` and leaves
   `sent=True`.
6. No retries. The transport is one-shot per call and keeps no connection.

`FakeTransport(results=None, *, fail_with=None)` (same module, used by tests and any demo):
records every call in `calls` as `(to, subject, body)`; returns
`SendResult(True, "<fake-N@example.invalid>")`, or the queued results, or
`SendResult(False, None, "NOT SENT: <fail_with>")`. It opens no sockets. A matching
`FakeTransportFactory` records `(from_account, in_reply_to)` per call.

Module-level hook for the server: `window/server.py` takes `transport_factory` in `Api`
(default `mail.send.default_transport_factory`, which looks the account up with
`get_account` and returns `SmtpImapTransport`); tests inject the fake. The old
`actions_email.TRANSPORT` callable is removed.

### 4.4 Recording after a successful send

`record_applicant_sent` (section 6.1) applies this table inside the gateway, using only
Dashboard functions:

| `kind` | Dashboard status change | Journal entry |
| --- | --- | --- |
| `outreach` | `New` to `Interested`; any other status unchanged | "Outreach email sent (Executive window)" |
| `interview` | to `Interview Requested` unless already `Interviewing`/`Offered`/`Hired` | "Interview invitation sent (Executive window)" |
| `manager` | none | "Applicant details emailed to area manager (Executive window)" |
| `reply` | none; `/api/send` does not call the gateway for `reply` | none |

The journal text contains the kind, the subject and the recipient address; it never contains
the body. The mapping lives in one constant `SENT_STATUS_BY_KIND` in `executive/gateway.py`
(OPEN QUESTION 4). Every status written must be a member of
`rtec_applicants._ALLOWED_STATUSES`.

### 4.5 From accounts

`GET /api/mail/accounts` returns `{"accounts": [{"account_id", "label", "email", "scope",
"credential_available", "default_for": ["outreach", "interview", "manager"]}]}`, from
`mail.accounts.load_accounts()` and `Account.public()`, enabled accounts only, never a secret.
The compose panel's From select lists these and preselects:

- `outreach`, `interview`, `manager`: the enabled account with `provider == "earthlink"` and
  `mail_scope == "work"` (the work EarthLink account); if there is none, the first enabled
  work-scope account; if none, no preselection and Send is disabled with the message
  "No work mail account is configured".
- `reply`: the account the thread arrived on (`compose.from_account`, set by
  `email.reply_draft` from the thread's scope/account), else the first enabled account in the
  thread's scope.

`/api/send` rejects an unknown or disabled `from_account` with
`NOT SENT: unknown mail account <id>`. If `from_account` is omitted the server applies the
same default rule.

### 4.6 Sent ledger

`window_home()/sent.jsonl`, one JSON line per successful send:
`{"at", "compose_id", "kind", "applicant_ref", "county", "from_account", "message_id",
"recorded": true|false}` (no addresses, no subject, no body). It records the applicant send
on the Executive side ("record it on the applicant"), lets `executive.reach_out` skip
applicants already contacted, and lets a failed Dashboard update be retried:
`Api.retry_records()` re-calls `record_applicant_sent` for lines with `"recorded": false`
and is triggered by `POST /api/send/retry-record` with `{}` (returns `{"retried": n,
"recorded": m}`).

## 5. Counties with openings

### 5.1 Provider

New module `window/providers_counties.py`; `providers_applicants.applicant_items` no longer
emits the `human_review_pending` group (every other reason group is unchanged). Registered in
`builtin.default_registry` as provider `"counties"`:

```python
def county_items(open_counties=None, candidates=None, top_n=None, today=None) -> list[dict]
```

`open_counties` defaults to `gateway.open_counties`, `candidates` to
`applicants.county_candidates`; both are injectable for tests. Output:

1. One standing item **`openings:console`** (always present, even with zero open counties):
   `{"id": "openings:console", "tab": "work", "kind": "openings_console", "title":
   "Openings", "why": "<N> counties with open positions", "source": "openings",
   "context": {"counties": [<county names>]}}`. It is the target for natural-language events
   about a county that has no group yet (section 8).
2. One item per county returned by `open_counties(today)`:
   `{"id": "county:<slug>", "tab": "work", "kind": "county_group", "title": "<County> County:
   <n> opening(s)", "why": "<k> applicants to review, best <top_n> shown", "source":
   "openings", "age_days": <oldest shown>, "context": {"county", "group_label",
   "open_count", "top_n", "total_candidates", "unreviewed_count", "applicants": [row, ...]}}`.
   `<slug>` is the county name casefolded, non-alphanumerics replaced by `-`.
3. A county with zero candidates is still listed (`applicants: []`, why "No applicants to
   review yet").

`row` is exactly: `{"applicant_ref", "name", "position", "status", "submitted", "age_days",
"score", "recommendation", "match_reasons"}`. Nothing else (section 5.3).

`today` defaults to `date.today()`. A gateway failure raises; `Registry.outstanding` already
turns a provider exception into an entry in `errors` without breaking other providers.

### 5.2 Applicant items and shared item resolution

Applicant-level actions need an item to act on, and the model's `executive_window.run` takes
only an `item_id`. An applicant is addressed by the composite id
**`county:<slug>#<applicant_ref>`**. New method on the registry:

```python
Registry.item(item_id: str, state=None) -> dict   # raises KeyError if unknown
```

It first looks for an exact id in `outstanding()`. If the id contains `#`, it resolves the
part before `#` as a `county_group` item, finds the applicant row whose `applicant_ref`
equals the part after `#` in `context.applicants`, and returns a synthesized item:
`{"id": "<composite>", "tab": "work", "kind": "county_applicant", "title": "<name>", "why":
"<county> County, <position>", "source": "openings", "context": {"county", "group_label",
"applicant": row}, "options": [...]}`. The applicant must be in the current group (that is
also the rule that stops a model from acting on an arbitrary ref). `Api._item` and
`mcp_server._window_run` both call `Registry.item`; the option-membership check in
`_window_run` stays. A new `Registry.options_for(item)` is factored out of `outstanding` and
is what `item()` uses.

### 5.3 Review panel and field allowlist

`GET /api/applicant?item_id=<county item id>&applicant_ref=<ref>` returns:

```json
{"item": {composite item with options},
 "review": {
   "applicant_ref": "...", "name": "...", "position": "...", "status": "...",
   "submitted": "...", "county": "...", "city": "...", "email": "...",
   "score": 87, "recommendation": "interview",
   "summary": "...", "strengths": ["..."], "concerns": ["..."],
   "criteria": [{"criterion": "...", "met": "yes", "evidence": "..."}],
   "match": {"match": "...", "alternates": ["..."], "reasons": ["..."], "group_label": "..."},
   "label": "Dashboard AI review: advisory; you decide"
 }}
```

This is built by a new `applicants.applicant_review(ref, *, gateway)` from `gateway.ranked`
(review fields via `_review`/`_review_fields`) and `gateway.match_for`. **Allowlist (the only
fields that may appear in `review`, in a county row, in a compose payload, in an audit line or
in a model prompt):** `applicant_ref`, `name`, `position`, `status`, `submitted`, `county`,
`city`, `email` (review panel and compose `to` only, never in the county list row and never in
prompts), `age_days`, `score`, `recommendation`, `summary`, `strengths`, `concerns`,
`criteria[criterion|met|evidence]`, `match[match|alternates|reasons|group_label]`. **Never**:
race, ethnicity, sex/gender, veteran, disability or any self-ID/AAP field, `aa_pdf_path`, any
document path or file name, notes, denial/disqualification reasons, screening flags, internal
`applicant_key`, source/provenance keys. The existing `_APPLICANT_FIELDS`, `_MATCH_FIELDS` and
`_REVIEW_FIELDS` allowlists in `gateway.py` already enforce this; new code must only read from
their output and tests must include a poisoned-row case (as `test_executive_eeo_firewall.py`
does) asserting no restricted key or value leaks into the review, compose, county rows or
audit.

Each call writes one `rtec_applicants._audit_access("executive.applicant_review",
applicant_ref=ref, metadata={"found": True})`, as `executive.suggestions` does.

The panel shows those fields, then these one-click decision buttons, built from the item's
`options`: Reach out, Invite to interview, Email county manager, Decline, Hold. Clicking a
compose button posts `/api/act` and opens the compose panel; Decline posts `/api/act` and shows
the existing Confirm preview; Hold posts `/api/act` and refreshes the list.

### 5.4 County candidate ranking

New in `executive/applicants.py`:

```python
def county_candidates(county: str, group_label: str | None = None, *, gateway: Any = None,
                      top_n: int | None = None, held: Collection[str] = (),
                      now: datetime | None = None) -> dict[str, Any]
```

Returns `{"county", "group_label", "top_n", "total": <int>, "unreviewed": <int>,
"applicants": [row, ...]}`, using the same logic as `suggestions()`:

1. `ranked = gateway.ranked(0)` (existing Dashboard AI reviews, passive; never starts a
   review). Skip statuses outside `REVIEWABLE_STATUSES`, skip refs in `held`.
2. An applicant belongs to the county if `_norm(applicant.county)` equals `_norm(county)`
   (stripping a trailing "county"), or `_norm(county_preference)` does, or
   `match_for(ref).group_label`/`groups` contains `group_label` (OPEN QUESTION 6), and the
   match is not `pending` (the `_fits` rule: pending never fits).
3. Sort with the `suggestions` key: score descending, `None` scores last; ties by earlier
   `submitted`, then `applicant_ref`. Then keep the first `top_n`.
4. `unreviewed` counts roster applicants (`_reviewable_applicants()`) that belong to the county
   by the same rule but have no review yet (they are not listed, exactly as in
   `suggestions`).
5. One `executive.county_candidates` access audit with `result_count`.

`top_n` is configurable: `window_home()/settings.json` key `"top_n"`, overridden by the
environment variable `AGENT_OS_EXECUTIVE_TOP_N`, default 5, clamped to 1..50. `GET
/api/settings` returns `{"top_n": 5}`; `POST /api/settings` with `{"top_n": 8}` saves it and
returns the new settings. An action param `top_n` overrides it for that call.

### 5.5 Decisions are registered actions

All of these are in section 9; the mapping from review-panel button to action is:

| Button | Action id | Result |
| --- | --- | --- |
| Reach out | `applicant.reach_out` | compose, kind `outreach` |
| Invite to interview | `applicant.invite_interview` | compose, kind `interview` |
| Email county manager | `applicant.email_manager` | compose, kind `manager` |
| Decline | `applicant.decline` | consequential preview, then Confirm sets status `Denied` |
| Hold | `applicant.hold` | one click, journal note and hold ledger |

## 6. Gateway additions

All new methods are added to the `DashboardGateway` Protocol, `LocalDashboardGateway` and
`SyntheticDashboardGateway`. The synthetic gateway implements each over in-memory state and
appends to `calls` like the existing methods; it imports nothing from the Dashboard. All
methods raise `ValueError` for bad arguments, `KeyError("Unknown applicant_ref")` for an
unknown ref, and `DashboardGatewayError` (new, subclass of `RuntimeError`, defined in
`gateway.py`) when the Dashboard checkout or the needed Dashboard function is unavailable.
Return values contain only JSON-safe values (`str`, `int`, `bool`, `None`, `list`, `dict`);
use `applicants._jsonable` for anything else. None of these ever returns an internal
`applicant_key`, a path, or a raw row.

### 6.1 Signatures and return shapes

```python
def open_counties(self, today: date | None = None) -> list[dict[str, Any]]: ...
```
Counties with open positions on `today` (default `date.today()`), via the Dashboard's
`openings.load_settings` / `evaluate` / `open_groups_in_range`. Returns
`[{"county": "Example", "open_count": 2, "group_label": "Example Transit"}, ...]`, sorted by
county name casefolded; `open_count >= 1` always (closed counties are omitted);
`group_label` is `None` when the Dashboard has no label. County names are the Dashboard's own
spelling without a trailing "County".

```python
def manager_for_county(self, county: str) -> dict[str, str] | None: ...
```
Via `area_managers.manager_for_county`. Returns `{"name": "...", "email": "..."}` or `None`
when there is no manager or the manager has no email. Never returns other manager fields
(phone, calendar ids).

```python
def record_applicant_sent(self, applicant_ref: str, kind: str, to_addr: str, subject: str) -> str: ...
```
Called by `/api/send` only after a successful send. Resolves the key locally and applies
section 4.4 using the Dashboard's own status-update and journal/event functions (the
function names are OPEN QUESTIONS, section 2). Returns the **journal id** as a string. `kind`
must be one of `outreach`, `interview`, `manager`; any other raises `ValueError`. It does not
send anything and never writes SQL. The synthetic gateway appends to a `sent_records` list
(`{"id": "synthetic-journal-N", "applicant_ref", "kind", "status_after"}`) and updates the
synthetic applicant's `status`.

```python
def set_applicant_status(self, applicant_ref: str, status: str | None, note: str) -> str: ...
```
For decline and hold. `status` must be a member of `rtec_applicants._ALLOWED_STATUSES` or
`None` (meaning keep the current status and only journal the note; this is hold). `note` is
one short line, no applicant data beyond what the operator typed, at most 500 characters.
Returns the journal id. Declining is `status="Denied"`. Writes through the Dashboard's own
status and journal functions; sends no email (the Dashboard's own denial-email flow is not
triggered by this).

```python
def preview_opening_change(self, county: str, change: str, *, count: int = 1) -> dict[str, Any]: ...
def apply_opening_change(self, county: str, change: str, *, count: int = 1) -> dict[str, Any]: ...
```
`change` is exactly one of `"close"`, `"quit"`, `"new"` (anything else raises `ValueError`).
`count` (default 1, 1..20) is the number of positions for `quit`/`new`, ignored for `close`.
Semantics, in terms of `open_count`: `close` sets it to 0 (the county leaves the open list);
`quit` (a driver left, so a position opened) and `new` both add `count`. If the Dashboard
only models a boolean per group, see OPEN QUESTION 1.

`preview_opening_change` is read-only (it calls `load_settings` and `evaluate` only) and
returns:

```json
{"county": "Example", "change": "quit", "count": 1,
 "before": {"open": true,  "open_count": 1, "group_label": "Example Transit"},
 "after":  {"open": true,  "open_count": 2, "group_label": "Example Transit"},
 "affects": ["Example", "Other"],
 "summary": "A driver quit in Example County: openings 1 to 2."}
```

`affects` lists every county covered by the same Dashboard group (a single-county change gives
a one-element list). An unknown county raises `ValueError("Unknown county: X")`; closing a
county that has no opening raises `ValueError("No open positions in X to close")`.

`apply_opening_change` re-reads the settings, applies the change through the openings
module's own save function(s) (`openings.save_settings` or the more specific one; OPEN
QUESTION), and returns `{"county", "change", "count", "applied": true, "before", "after",
"group": <the open_counties entry for that county after the change, or None when closed>}`.
It is the only gateway method that writes `openings_settings.json`, and it does so only via
the Dashboard's function. Implementations must keep `apply` idempotent per call (a second
`quit` adds again; that is expected, the preview and Confirm guard against accidents).

### 6.2 What does not change

`send_now` stays in the Protocol for the existing batch tests but is **not called** by the
window. The window path never calls `email_sender`.

### 6.3 Hold ledger (Executive side, not a gateway method)

`window_home()/holds.json` maps `applicant_ref` to an ISO expiry (default 14 days, param
`hold_days` 1..90). `county_candidates(..., held=active_holds)` omits held applicants until
the hold expires. Hold also calls `gateway.set_applicant_status(ref, None, "Held by operator
until <date> (Executive window)")` so the Dashboard journal records it. Class
`HoldStore(home)` in `window/holds.py`: `hold(ref, days)`, `active() -> set[str]`,
`release(ref)`.

## 7. Manager email

`applicant.email_manager` builds the compose (`kind="manager"`):

- `to` is `gateway.manager_for_county(county)["email"]`, where `county` is the applicant's
  county from the item context (`county` of the group). If there is no manager the compose
  still opens with `to == ""` and `warnings: ["no area manager found for <County> County"]`,
  so the operator can type an address.
- `subject`: `"Applicant for <position>: <name> (<County> County)"`.
- `body` is a deterministic template (no model call) containing only the allowlisted
  screening fields and match reasons:

```
Hello <manager name>,

<name> applied for <position> and is a candidate for the <County> County opening.

Dashboard screening (advisory):
- Score: <score>/100, recommendation: <recommendation>
- Summary: <summary>
- Strengths: <strength>; <strength>
- Concerns: <concern>; <concern>
- Criteria: <criterion>: <met> (<evidence>) ... one line each
- Match reasons: <reason>; <reason>

Submitted: <submitted>   Status: <status>   City: <city>
```

  No contact details of the applicant other than what the operator chooses to add, no
  documents, no EEO data, no free-text notes. Empty sections are omitted.
- `applicant_ref` and `county` are set on the compose payload. A successful manager send
  records a journal entry only (section 4.4); it does not change the applicant's status.

## 8. Natural-language opening events

### 8.1 Two routes, one action

The chat and the model both end in the same consequential action `county.opening_change`, so
the preview and Confirm are identical:

1. **Deterministic route (preferred, no model).** `Api.post("/api/chat")` first calls
   `opening_events.parse_opening_event(text)`. When it matches, the server invokes
   `registry.invoke("county.opening_change", <county item or openings:console>, params,
   pending)` and returns `{"reply": "<preview sentence>. Click Confirm to apply it.",
   "message": same, "previews": [...], "session_id": null, "error": null}`; the model is not
   called. When nothing matches, the text goes to the connected model as today.
2. **Model route.** The registered action is a model tool through `executive_window.run`
   (`item_id` `openings:console` or `county:<slug>`), and its `description` tells the model
   to use it for statements such as "we closed the opening in X". A consequential action only
   returns `needs_confirmation`; the operator's Confirm click executes it.

### 8.2 Parser

New module `executive/opening_events.py`:

```python
def parse_opening_event(text: str) -> dict[str, Any] | None
# {"change": "close"|"quit"|"new", "county": "Example", "count": 1} or None
```

Pure and deterministic; case-insensitive; it extracts a county name (one to three words,
optional trailing "County", optional "the"), strips punctuation, and returns `None` when
unsure (never guess a county). Required phrase families (tests must cover each, plus
negatives such as "did a driver quit in Example?" being a question and "send an email to the
driver in X" returning `None`):

| change | Examples |
| --- | --- |
| `close` | "we closed the opening in X", "close the opening in X", "the X opening is filled", "we filled the position in X", "no longer hiring in X" |
| `quit` | "a driver quit in X", "we lost a driver in X", "driver in X resigned", "two drivers quit in X" (count 2) |
| `new` | "we have a new opening in X", "new driver opening in X", "open a position in X", "we're hiring in X" |

A trailing question mark or a leading interrogative ("did", "has", "is there", "should we")
means no match.

### 8.3 Flow and refresh

`county.opening_change` (section 9) previews with `gateway.preview_opening_change`; on
Confirm it calls `gateway.apply_opening_change` and then **immediately recomputes that county's
group** with `applicants.county_candidates(county, group_label, ...)`. Its result:

```json
{"applied": true, "county": "Example", "change": "quit", "before": {...}, "after": {...},
 "group": {"id": "county:example", "county": "Example", "open_count": 2,
           "group_label": "...", "applicants": [row, ...], "total": 7, "unreviewed": 1},
 "message": "A driver quit in Example County: openings 1 to 2. Applicants to review below."}
```

`group` is `None` for a closed county. After `POST /api/confirm` the UI refreshes
`/api/items` and scrolls to / highlights `county:<slug>`; the next provider run reflects the
new Dashboard state because `open_counties` always reads the Dashboard.

## 9. Action registry

Every new capability is registered with `register_action`, so each shows as an item option
(by `applies_to` item kind) and as an `executive_window.run` tool (the MCP enum is built from
the live registry). `params_schema` is a JSON-schema object with `properties` (the existing
`email.*` actions use this form; do not use the bare-properties form of `actions_items.py`).
New registrations go in `window/actions_applicants.py` (`register(registry)`, called from
`builtin.default_registry` after the existing three) and `window/actions_counties.py`.

| Action id | Label | applies_to | Consequential | Params | Result |
| --- | --- | --- | --- | --- | --- |
| `applicant.reach_out` | Reach out | `county_applicant` | no | `message` (opt) | `{"compose": {kind "outreach", ...}}` |
| `applicant.invite_interview` | Invite to interview | `county_applicant` | no | `interview_type` (opt, default "phone"), `location` (opt), `duration_minutes` (opt, default 30) | `{"compose": {kind "interview", ...}}` with up to 3 Dashboard-suggested slots in the body when `manager_for`/`suggest_slots` give any, else a body without slots and `warnings: ["no interview slots available"]` |
| `applicant.email_manager` | Email county manager | `county_applicant` | no | `note` (opt, appended to the body) | `{"compose": {kind "manager", ...}}` |
| `applicant.decline` | Decline | `county_applicant` | **yes** | `note` (opt) | preview: `{"applicant_ref","name","from_status","to_status":"Denied"}`; on Confirm: `{"declined": true, "journal_id", "group": <refreshed>}` |
| `applicant.hold` | Hold | `county_applicant` | no | `hold_days` (opt) | `{"held": true, "applicant_ref", "until", "journal_id", "group": <refreshed>}` |
| `county.refresh` | Refresh applicants | `county_group` | no | `top_n` (opt) | the refreshed group dict (section 8.3 `group`) |
| `county.opening_change` | Update opening | `county_group`, `openings_console` | **yes** | `county` (required on the console; defaults to the group's county), `change` (required, `close\|quit\|new`), `count` (opt, 1..20) | preview: section 6.1 preview dict; on Confirm: section 8.3 result |
| `email.reply_draft` (existing, changed) | Reply to thread | `mail_thread` | no | `body` (opt) | `{"compose": {kind "reply", ...}}` plus the legacy top-level `to`, `subject`, `in_reply_to`, `body` keys |
| `email.send` (existing, changed) | Send email | `*` | no | `to`, `subject`, `body`, `in_reply_to` (opt), `kind` (opt, default `reply`) | `{"compose": {...}}`: it opens the compose panel and does **not** send |
| `executive.reach_out` (existing, changed) | Send Outreach | `applicant_group` | no | `batch_id` | `{"composes": [compose, ...], "compose": <first>}`, one `interview` compose per approved batch item whose `applicant_ref` is not in the sent ledger (section 4.6); never calls `gateway.send_now` |

Notes:

- `email.send` and `executive.reach_out` change from consequential to non-consequential: the
  operator's Send click in the compose panel is now the single confirmation, and a Confirm
  preview before a compose panel would be a second, redundant gate. The existing tests for
  `actions_email.py` and `actions_executive.py` are updated by the task that makes the change.
  `executive.plan_interviews` and `executive.approve_batch` are unchanged.
- Declining and opening changes stay consequential, which is why they go through the
  existing `PendingStore` preview and `/api/confirm`.
- Applicant actions validate that the `applicant_ref` in the item context is non-empty and,
  for hold, decline, manager and interview, that the applicant is still in a reviewable
  status (`REVIEWABLE_STATUSES`) via `gateway.ranked`/the roster; otherwise `ValueError`
  with a clear message.
- Every handler returns only JSON-safe data and never includes restricted fields.
- Audit: `Registry.invoke`/`confirm` already write `audit.jsonl` through `PendingStore.audit`;
  compose-producing actions are non-consequential and are audited by the handler with
  `compose_id`, `kind`, `applicant_ref`, `county` (no addresses, subject or body).

## 10. HTTP surface summary

| Route | Method | Purpose |
| --- | --- | --- |
| `/api/items`, `/api/actions`, `/api/pending`, `/api/act`, `/api/confirm`, `/api/dismiss`, `/api/chat`, `/api/option` | existing | `/api/act` and `/api/option` use `Registry.item`; `/api/chat` adds the section 8.1 route |
| `/api/applicant` | GET | review panel data (5.3) |
| `/api/compose` | GET | open composes |
| `/api/compose/discard` | POST | discard one compose |
| `/api/send` | POST | send (4.1) |
| `/api/send/retry-record` | POST | retry Dashboard updates for sent mail (4.6) |
| `/api/mail/accounts` | GET | From choices (4.5) |
| `/api/settings` | GET, POST | `top_n` (5.4) |

All POSTs need the `X-Agent-OS-Token` header (existing behavior). `Api` gains
`transport_factory`, `gateway_factory`, `compose`, `holds` constructor parameters with
defaults, so `build_server(...)` tests can inject fakes. Send runs in the server process.

## 11. Static UI

The window's static files are `gui/executive.html`, `gui/executive.js`, `gui/style.css`
(`STATIC_FILES` in `server.py`; the files live under the repository `gui/` directory, not
inside `window/`). Changes: county group rows with clickable applicants; the review panel
(5.3); the compose panel (3.3); a Confirm preview rendering for `county.opening_change` and
`applicant.decline` (the existing `previews` list); a 5-second `GET /api/compose` poll; and a
top-N control wired to `/api/settings`. No remote assets, no inline secrets; the session token
placeholder mechanism is unchanged.

## 12. Ownership and tests

| Task area | Files | Tests (all synthetic, new files unless noted) |
| --- | --- | --- |
| Transport | `mail/send.py`, `mail/accounts.py` (smtp fields, `smtp_settings`) | `tests/test_mail_send.py`: message headers, STARTTLS and SSL paths with fake `smtplib`/`imaplib` factories, every `NOT SENT:` mapping, no secret in any error string, Sent-folder resolution, warning path, no `win32com` import anywhere (grep test over `src/`) |
| Gateway | `executive/gateway.py` | `tests/test_executive_gateway.py` (extend): the six new methods on the synthetic gateway, status allowlist, count bounds, `DashboardGatewayError`, no internal key in any result |
| Counties and review | `executive/applicants.py`, `window/providers_counties.py`, `window/providers_applicants.py` | ranking and top-N, held exclusion, `human_review_pending` gone, poisoned-row EEO check, row field set exact |
| Actions | `window/actions_applicants.py`, `window/actions_counties.py`, `window/actions_email.py`, `window/actions_executive.py`, `window/compose.py`, `window/holds.py`, `window/registry.py` (`item`, `options_for`), `window/builtin.py` | each action id registered with the right `applies_to`/`consequential`; compose payload keys; manager email body contains only allowlisted fields; decline preview then Confirm calls `set_applicant_status("Denied")`; model-tool enum contains every id |
| Events | `executive/opening_events.py`, `window/server.py` chat route | parser table incl. negatives; chat returns a preview without calling the bridge; Confirm applies and returns the refreshed group |
| Server and UI | `window/server.py`, `gui/executive.*` | `/api/send` success, every failure, status recorded only after success and never after failure, double-send refused, token required, header injection refused, From default; `gui` string checks as in `tests/test_executive_window_gui.py` |
| Docs | this file | `tests/test_executive_window_docs.py` |

Never in any test: real Outlook, SMTP/IMAP, keyring, Dashboard database or network. Protected
control-plane paths are unchanged by this feature. Only the final status node appends to
`projects/personal-agent-os/orchestrator-os/status.json`.

## 13. Validation

```
python -m unittest tests.test_executive_window_docs
python -m unittest discover -s tests -v
python agent.py validate
```
