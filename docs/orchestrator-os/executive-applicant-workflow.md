# Executive applicant workflow contract

Status: binding contract for the implementation tasks of run `run-20261002T170546Z-ece407`
(operator spec, 2026-10-02). It extends `executive-window.md` and
`applicant-executive-design.md`; where it conflicts with them, this document wins for the
features below. Implementers must not change a name, signature, key or id fixed here without
a `needs_decision` report. Anything marked **OPEN QUESTION** is a best guess to be verified
against the Dashboard checkout by the task that first touches it.

The four lettered contracts the assignment asked for are anchored as **(a)** to **(d)**:

- **(a)** new `DashboardGateway` methods: section 4;
- **(b)** the compose payload: section 5;
- **(c)** `POST /api/send`: section 6;
- **(d)** the `SendTransport` protocol and its transports: section 7.

## 0. Operator decisions that shape everything

1. **No Outlook, no COM.** The operator's change supersedes the earlier Outlook instruction.
   Nothing in Agent OS imports `win32com`, `pythoncom` or `Outlook.Application`, and the
   Applicant Dashboard's `email_sender` is not used for sending ("hasn't been working").
   Mail goes out over **SMTP submission** and a copy is stored with **IMAP APPEND** to the
   sending account's Sent folder, authenticated with the credential already in the keyring.
2. **Nothing sends without the Send click.** Planning an email only produces a compose
   payload. The only code path that sends is `POST /api/send`, which the operator's Send
   button calls. No registered action, no model tool and no `/api/chat` route sends mail.
   This run makes that true for the two existing senders (section 11.1): `executive.reach_out`
   (batch send through `gateway.send_now` / `email_sender`) and `email.send` are removed from
   the registry, and `email.reply_draft` returns a compose payload.
3. **The Dashboard stays the system of record.** Executive code reaches it only through
   `DashboardGateway` methods that call the Dashboard's own Python functions. Never raw SQL
   writes, never `UPDATE`/`INSERT` from Agent OS, never edits of `openings_settings.json`
   outside the Dashboard's own save functions.
4. **Privacy.** Only allowlisted applicant fields cross the gateway and reach the window,
   the compose payload, the audit trail or a model prompt (section 8.3). EEO, AAP and
   self-identification data never do.
5. Tests use synthetic data and fakes only: no real mail, SMTP, IMAP, Dashboard database,
   keyring or network. Every test file starts with
   `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))`.

## 1. Module map (names the implementation tasks build against)

| Module | Owns |
| --- | --- |
| `executive/gateway.py` | the six gateway methods of section 4 (a), `DashboardGatewayError`, `SENT_STATUS_BY_KIND` |
| `executive/applicants.py` | `DEFAULT_TOP_N`, `county_groups`, `county_candidates`, `applicant_review` (section 8): **all owned by the county-candidates task** |
| `executive/window/transport.py` | `SendResult`, `SendTransport`, `SmtpImapTransport`, `FakeTransport`, `default_transport` (section 7 (d)) |
| `executive/window/providers_applicants.py` | `county_items(groups_fn=None)`, `invalidate_county_cache()`, items of kind `county_openings` (section 8.1); the `human_review_pending` group is no longer emitted by `applicant_items` |
| `executive/window/actions_applicant_compose.py` | `applicant.reach_out`, `applicant.invite_interview`, `applicant.email_manager` (sections 5, 9) |
| `executive/window/actions_email.py`, `executive/window/actions_executive.py` | existing actions changed by section 11.1 (owned by the compose-actions task, the owner of `actions_applicant_compose.py`, together with their tests) |
| `executive/window/actions_applicant_decisions.py` | `applicant.review`, `applicant.decline`, `applicant.hold` (section 8.4) |
| `executive/window/actions_openings.py` | `parse_opening_event`, `county.refresh`, `county.opening_change` (section 10) |
| `executive/window/server.py` | `Api(registry, bridge, home, *, transport=None, gateway_factory=None)`, `POST /api/send`, `GET /api/send/accounts`, chat route for opening events |
| `executive/window/builtin.py` | registers the provider and the three action modules |
| `gui/executive.html`, `gui/executive.js`, `gui/style.css` | county groups, review panel, compose panel |

## 2. What already exists (read, do not rebuild)

| Piece | Where | Relied on for |
| --- | --- | --- |
| `DashboardGateway` Protocol, `LocalDashboardGateway`, `SyntheticDashboardGateway`, `_project`, `_review`, `_REVIEWABLE`, `_MATCH_FIELDS` | `executive/gateway.py` | Only boundary to the Dashboard; `ranked(0)` and `match_for(ref)` supply ranking and match reasons |
| `needs_action`, `suggestions`, `_fits`, `_project`, `_review_fields`, `REVIEWABLE_STATUSES`, `ADVISORY_LABEL` | `executive/applicants.py` | Ranking rule (`suggestions`), fit rule (`_fits`) |
| `Registry.register_provider/register_action/outstanding/invoke/confirm`, `REGISTRY` | `window/registry.py` | Items, item options, preview then Confirm |
| `Api.get/post`, `make_handler`, `build_server`, session token on every POST, loopback-only bind | `window/server.py` | HTTP surface |
| `PendingStore`, `ItemState`, `window_home()` | `window/confirm.py` | Confirm tokens, `audit.jsonl` |
| `rtec_applicants` (`_project_root`, `_audit_access`, `_ALLOWED_STATUSES`, `openings_status`, `get_summary`) | `src/agent_os/rtec_applicants.py` | Read-only Dashboard access, access audit, status allowlist |
| `mail.accounts` (`Account`, `PROVIDERS[...]["future_smtp"]`, `["hosted_future_smtp"]`, `get_secret`, `load_accounts`, `mail_scope`) | `src/agent_os/mail/accounts.py` | SMTP defaults and the keyring credential |
| `mcp_server._window_run_schema`, `_window_run` | `src/agent_os/mcp_server.py` | Model tool built from the live registry; registering an action makes it a tool |

Facts that constrain the design:

- `executive_window.run` in the MCP server resolves `item_id` against
  `registry.outstanding()`. Applicant actions therefore act on the **county item** and name
  the applicant with the `applicant_ref` param (section 9); there are no per-applicant item ids.
- `mail.imap.ReadOnlyIMAP` refuses every write command. The Sent-folder copy uses its own
  write-capable connection inside `window/transport.py`; the read-only guard is not changed.
- `PROVIDERS["earthlink"]["future_smtp"]` is `smtpauth.earthlink.net:587 starttls`;
  `hosted_future_smtp` is `smtpauth.hosting.earthlink.net:587 starttls` for the operator's
  own domain hosted by EarthLink (same split `default_server` uses for IMAP). These are the
  defaults.
- The Dashboard status allowlist is `rtec_applicants._ALLOWED_STATUSES`: New, Interested,
  Interview Requested, Clarification Requested, Interviewing, Offered, Denied, Disqualified,
  Hired, Inactive.

## 3. Dashboard names (not verified: OPEN QUESTIONS)

`rtec_applicants._project_root()` resolves to `C:\Users\HR.RTEC\Projects\Job Applicant
Dashboard`, but the design task could not read outside its worktree, so **none of the names
below were verified**. The gateway task must read the Dashboard read-only, replace each guess
and list the verified names in its handoff. Until then `LocalDashboardGateway` isolates every
guess in one private helper per function, and raises
`DashboardGatewayError("<operation> is not available in this Dashboard checkout")` instead of
falling back to SQL when a guessed name does not exist.

| Needed | Best guess (OPEN QUESTION) | Known evidence |
| --- | --- | --- |
| Openings settings read | `openings.load_settings() -> dict` | Named by the operator; `Config/openings_settings.json` has `transit_driver_groups`, `office_positions`, `max_drive_minutes`, `nearby_offer_minutes` (`rtec_applicants.openings_status`) |
| Which groups are open today | `openings.evaluate(settings, today=None)` | Named by the operator |
| Open groups reachable from a place | `openings.open_groups_in_range(settings, county_or_origin, ...)` | Named by the operator; feeds `match_for(...).group_label` |
| Openings save | `openings.save_settings(settings)` | "openings.py's own save functions"; there may be several. Whether openings are a count per county or a boolean per group is unknown |
| Area manager for a county | `area_managers.manager_for_county(county)` | Named by the operator; the manager object's shape is unknown, the gateway normalizes it to `{name, email}` |
| Applicant status update | `database.set_status(applicant_key, status)` or `database.update_applicant_status(...)` | The Dashboard UI changes status somewhere in its own code |
| Journal / event entry | `database.add_journal_entry(applicant_key, text, ...)` or `events.log_event(...)` | `agent_events` table exists (`event_id`, `event_type`, `source_component`, `payload_json`) |

Open questions, in priority order:

1. **Openings model.** Boolean per transit group or count per county? Section 4 normalizes
   to `open_count`; with a boolean model `open_count` is 1 or 0, `quit`/`new` set it to 1 and
   `close` sets it to 0.
2. **County to group.** If one group covers several counties, closing "X" closes the whole
   group, and the preview must say so (field `affects`).
3. **Hold.** The Dashboard has no `Hold` status. Hold is "status unchanged plus a journal
   note" (section 8.4). Confirm.
4. **Status after send.** `outreach` sets `Interested` (only from `New`), `interview` sets
   `Interview Requested`. Confirm, or name the Dashboard's own transitions.
5. **From account.** The operator's message was cut off after "default: the work EarthLink
   account for applicant and manager mai[l]". Assumed: default From is the work-scope
   EarthLink account for `outreach`, `interview`, `manager`; for `reply` the account the
   thread arrived on.
6. **County membership** (section 8.2): what `match_for(...).group_label` contains.

## 4. (a) Gateway additions

All new methods are added to the `DashboardGateway` Protocol, `LocalDashboardGateway` and
`SyntheticDashboardGateway` (in-memory, appends to `calls`, imports nothing from the
Dashboard). They raise `ValueError` for bad arguments, `KeyError("Unknown applicant_ref")`
for an unknown ref, and `DashboardGatewayError` (new, subclass of `RuntimeError`, in
`gateway.py`) when the Dashboard or the needed Dashboard function is unavailable. Return
values are JSON-safe and never contain an internal `applicant_key`, a path or a raw row.

```python
def open_counties(self, today: date | None = None) -> list[dict[str, Any]]: ...
```
Counties with open positions on `today` (default `date.today()`), via
`openings.load_settings` / `evaluate` / `open_groups_in_range`. Returns
`[{"county": "Example", "open_count": 2, "group_label": "Example Transit"}, ...]`, sorted by
county casefolded; closed counties are omitted, so `open_count >= 1`; `group_label` is `None`
when the Dashboard has none. County names are the Dashboard's spelling without "County".

```python
def manager_for_county(self, county: str) -> dict[str, str] | None: ...
```
Via `area_managers.manager_for_county`. Returns `{"name": "...", "email": "..."}`, or `None`
when there is no manager or no email. No other manager fields.

```python
def record_applicant_sent(self, applicant_ref: str, kind: str, to_addr: str, subject: str) -> str: ...
```
Called by `/api/send` **only after a successful send**. Applies `SENT_STATUS_BY_KIND` through
the Dashboard's own status and journal functions and returns the **journal id** as a string.
`kind` is `outreach`, `interview` or `manager`; anything else raises `ValueError`. Never sends,
never writes SQL. The journal text holds the kind, subject and recipient, never the body.

| `kind` | Dashboard status change | Journal entry |
| --- | --- | --- |
| `outreach` | `New` to `Interested`; otherwise unchanged | "Outreach email sent (Executive window)" |
| `interview` | to `Interview Requested` unless already `Interviewing`/`Offered`/`Hired` | "Interview invitation sent (Executive window)" |
| `manager` | none | "Applicant details emailed to area manager (Executive window)" |

```python
def set_applicant_status(self, applicant_ref: str, status: str | None, note: str) -> str: ...
```
For decline and hold. `status` is a member of `rtec_applicants._ALLOWED_STATUSES`, or `None`
(keep status, journal the note only: hold). `note` is one line, at most 500 characters.
Returns the journal id. Decline is `status="Denied"`; it never triggers the Dashboard's
denial-email flow.

```python
def preview_opening_change(self, county: str, change: str, *, count: int = 1) -> dict[str, Any]: ...
def apply_opening_change(self, county: str, change: str, *, count: int = 1) -> dict[str, Any]: ...
```
`change` is exactly `"close"`, `"quit"` or `"new"`; anything else raises `ValueError`. `count`
(1..20, default 1) applies to `quit`/`new`. `close` sets `open_count` to 0; `quit` (a driver
left) and `new` add `count`. The preview is read-only (`load_settings`, `evaluate`) and returns:

```json
{"county": "Example", "change": "quit", "count": 1,
 "before": {"open": true, "open_count": 1, "group_label": "Example Transit"},
 "after":  {"open": true, "open_count": 2, "group_label": "Example Transit"},
 "affects": ["Example"],
 "summary": "A driver quit in Example County: openings 1 to 2."}
```

An unknown county raises `ValueError("Unknown county: X")`; closing a county with no opening
raises `ValueError("No open positions in X to close")`. `apply_opening_change` re-reads the
settings, applies the change only through the openings module's own save function(s), and
returns `{"county", "change", "count", "applied": true, "before", "after", "group": <the
open_counties entry after the change, or None when closed>}`.

`send_now` stays in the Protocol for the existing batch tests but is not called by the window.

## 5. (b) Compose payload

Every compose-producing action returns, as its `result`:

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

- `to`, `subject`, `body`, `kind` are always present; `to` may be `""` when unknown (the panel
  then requires the operator to type one).
- `kind` is one of `outreach`, `interview`, `manager`, `reply`.
- `applicant_ref` (optional) is present for `outreach`, `interview` and `manager` (the
  applicant the manager email is about); `county` (optional) when known.
- Optional extras a consumer must tolerate: `in_reply_to` (for `reply`) and `warnings` (list
  of short strings, for example `"no area manager found for Example County"`).
- An applicant's `to` comes from `applicants.applicant_review(ref, gateway=gateway)["email"]`
  (the gateway's allowlisted `email` field), so `SyntheticDashboardGateway` fakes it in tests.
  Compose actions never call `rtec_applicants.get_summary` or read the Dashboard directly.
- `kind: "reply"` is produced by the existing `email.reply_draft` action on `mail_thread`
  items (section 11.1): `{"compose": {"to": <latest sender>, "subject": "Re: ...", "body":
  <params.body or "">, "kind": "reply", "in_reply_to": <latest message_id>}}`, no
  `applicant_ref`.
- A compose payload never contains EEO or self-ID data, paths, notes, or any field outside the
  section 8.3 allowlist.
- Compose-producing actions are **not consequential** (they only draft) and return
  `{"status": "done", "result": {"compose": {...}}}` through `Registry.invoke`. The UI opens the
  compose panel straight from `result.compose`.

Compose panel: editable **From** (select), **To**, **Subject**, **Body**, a **Send** button
and a **Discard** button. Send posts the edited values to `/api/send`; the button is disabled
while in flight; on `sent: true` the panel shows "Sent" and closes; on `sent: false` it stays
open with the error text verbatim and the operator's edits intact. No auto-send, no timers,
no send on Enter.

## 6. (c) `POST /api/send`

Token-protected like every POST. Request:

```json
{"to": "applicant@example.com", "subject": "...", "body": "...", "kind": "outreach",
 "applicant_ref": "ref-opaque", "county": "Example",
 "from_account": "work-earthlink", "in_reply_to": "<message-id>"}
```

`to`, `subject`, `body`, `kind` are required; the rest are optional. The request values are
what is sent (the operator's edits). Missing required fields or CR/LF in `to`, `subject` or
`in_reply_to` keep the existing HTTP 400 `{"error": ...}`. A handled send attempt is HTTP 200:

```json
{"sent": true, "message_id": "<generated@host>"}
```
```json
{"sent": false, "error": "NOT SENT: <specific reason>"}
```

1. Every failure starts with the literal `NOT SENT: ` and names the stage
   (`missing credential for account <id>`, `SMTP authentication failed`,
   `SMTP connection failed`, `recipient refused`, `unknown mail account <id>`). It never
   contains the credential, raw server text or the body. An exception escaping the transport
   becomes `NOT SENT: <ExceptionType>`.
2. If SMTP accepted the message but the Sent-folder copy failed, the response is still
   `sent: true` with `"warning": "Sent, but the copy could not be saved to the Sent folder"`.
3. **The applicant's status is recorded only after a successful send.** When `sent` is true,
   `kind` is `outreach`, `interview` or `manager`, and `applicant_ref` is present, the server
   calls `gateway_factory().record_applicant_sent(applicant_ref, kind, to, subject)` and adds
   `"journal_id"` to the response. If that fails the mail is still `sent: true` and the
   response adds `"record_error": "Sent, but the Dashboard was not updated: <reason>"`. A failed
   send never touches the Dashboard. `reply` never calls the gateway. After a successful
   `record_applicant_sent` the server calls `providers_applicants.invalidate_county_cache()`.
4. The send runs synchronously in the window server's own handler thread: no queue, no retry.
5. The audit line in `audit.jsonl` is `{"send": true, "kind", "applicant_ref", "county",
   "from_account", "sent", "message_id"}`: no addresses, subject or body.

`GET /api/send/accounts` returns `{"accounts": transport.from_accounts()}` when the transport
has that method, else `{"accounts": []}`; it feeds the From select (section 7).

`Api.__init__(self, registry, bridge, home, *, transport=None, gateway_factory=None)`:
`transport` defaults to `transport.default_transport()`, `gateway_factory` to
`applicants._default_gateway`. `build_server` passes both through so tests inject
`FakeTransport` and `SyntheticDashboardGateway`.

## 7. (d) `SendTransport`

Module `src/agent_os/executive/window/transport.py`; importable without network; no
`win32com`, no `pythoncom`.

```python
@dataclass(frozen=True)
class SendResult:
    sent: bool                   # True once SMTP accepted the message
    message_id: str | None       # the Message-ID header we generated
    error: str | None = None     # "NOT SENT: ..." when sent is False
    warning: str | None = None   # set when sent but the Sent-folder copy failed

class SendTransport(Protocol):
    def send(self, to: str, subject: str, body: str, *,
             from_account: str | None = None, in_reply_to: str | None = None) -> SendResult: ...
```

`send(to, subject, body)` is the required call; the keyword-only arguments default to `None`.
`send` never raises for delivery or configuration problems; it returns
`SendResult(sent=False, message_id=None, error="NOT SENT: ...")`.

`SmtpImapTransport(*, accounts=None, secret_lookup=None, smtp_factory=None, imap_factory=None)`:

1. **From account** (owned by this task). `from_accounts()` returns the enabled accounts from
   `mail.accounts.load_accounts()` as `[{"account_id", "label", "email", "default": bool}]`,
   never a secret. With `from_account=None` the transport uses the default: the enabled
   account with provider `earthlink` and work scope, else the first enabled work-scope
   account (OPEN QUESTION 5). An unknown or disabled id is `NOT SENT: unknown mail account <id>`.
2. Message via `email.message.EmailMessage`: `From`, `To`, `Subject`, `Date`, `Message-ID`
   (`email.utils.make_msgid`), optional `In-Reply-To`/`References`, UTF-8 plain text.
3. Credential from `mail.accounts.get_secret(account)` (the keyring). Missing credential is
   `NOT SENT: missing credential for account <id>`.
4. SMTP host, port and security from the account's provider settings (`future_smtp`, or
   `hosted_future_smtp` for the hosted own domain), with optional per-account overrides.
   **STARTTLS on 587** or implicit TLS on **465**, always with
   `ssl.create_default_context()`; never plaintext. Timeout 30 seconds. `login` then
   `send_message`. Exception text is not copied into errors.
5. After SMTP accepts, **IMAP APPEND** the same bytes to the account's **Sent folder** over a
   separate **write-capable** IMAP connection with the same TLS rules (not `ReadOnlyIMAP`).
   Folder: `LIST` special-use `\Sent`, else the first of `Sent`, `Sent Items`, `Sent Mail`,
   `INBOX.Sent`; flag `\Seen`. A failure here sets `warning` and keeps `sent=True`.
6. One-shot per call: no retries, no kept connection.

`FakeTransport(results=None, *, fail_with=None)`: records each call in `calls` as
`{"to", "subject", "body", "from_account", "in_reply_to"}` and returns
`SendResult(True, "<fake-N@example.invalid>")`, the queued `results`, or
`SendResult(False, None, "NOT SENT: <fail_with>")`. `from_accounts()` returns one synthetic
account. It opens no sockets. `default_transport()` returns `SmtpImapTransport()`.

## 8. Counties with openings

### 8.1 Provider

`providers_applicants.county_items(groups_fn=None) -> list[dict]`, registered in
`builtin.default_registry` as provider `"counties"`. `groups_fn` defaults to

```python
def _default_groups():
    g = applicants._default_gateway()
    return applicants.county_groups(g.open_counties(), gateway=g)
```

and tests inject a function returning synthetic groups. `applicant_items` no longer emits the
`human_review_pending` group; other reason groups are unchanged.

**Short cache.** `Api._item` resolves every `/api/act` (review, compose, hold, decline,
opening change) and every chat opening event through `registry.outstanding()`, which re-runs
**every** provider. So `county_items` caches the built item list in-process for
`COUNTY_CACHE_SECONDS = 30` (one entry, guarded by a lock, keyed by `groups_fn`), and
`providers_applicants.invalidate_county_cache()` drops it. It is invalidated after a confirmed
`applicant.decline`, after `applicant.hold`, after a confirmed `county.opening_change`, and by
`/api/send` after `record_applicant_sent` succeeds. A provider error is not cached.

Per-click cost: within the cache window a click costs **zero** Dashboard calls in the county
provider (the other providers run as they do today; this run does not change them or
`Api._item`). On a cold cache the provider costs one `open_counties()`, one `ranked(0)` and
one `match_for` per reviewable applicant (section 8.2), independent of the number of
counties. A compose or review action then adds one `applicant_review` (one `ranked(0)`, one
`match_for`), and `applicant.email_manager` one `manager_for_county`.

Output:

1. One standing item `{"id": "openings:console", "tab": "work", "kind": "openings_console",
   "title": "Openings", "why": "<N> counties with open positions", "source": "openings",
   "context": {"counties": [...]}}`, present even with zero open counties. It is the target of
   opening events for a county that has no group yet (section 10).
2. One item per open county: `{"id": "county:<slug>", "tab": "work", "kind":
   "county_openings", "title": "<County> County: <n> opening(s)", "why": "<k> applicants to
   review, best <top_n> shown", "source": "openings", "age_days": <oldest shown>, "context":
   {"county", "group_label", "open_count", "top_n", "total", "unreviewed", "applicants":
   [row, ...]}}`. `<slug>` is the county casefolded with non-alphanumerics replaced by `-`. A
   county with no candidates is still listed with `applicants: []`.

`row` is exactly `{"applicant_ref", "name", "position", "status", "submitted", "age_days",
"score", "recommendation", "match_reasons"}`.

### 8.2 Ranking: one pass over the Dashboard data

New in `executive/applicants.py`, owned by the county-candidates task (with
`applicant_review`, section 8.3):

```python
DEFAULT_TOP_N = 5

def county_groups(open_counties: list[dict[str, Any]], *, gateway: Any = None,
                  top_n: int = DEFAULT_TOP_N) -> list[dict[str, Any]]

def county_candidates(county: str, *, gateway: Any = None, top_n: int = DEFAULT_TOP_N,
                      group_label: str | None = None,
                      ranked: list[tuple[dict, dict]] | None = None,
                      matches: dict[str, dict] | None = None) -> dict[str, Any]
```

`county_candidates(county, *, gateway=None, top_n=DEFAULT_TOP_N)` is the binding call form;
everything after `top_n` is keyword-only with a default, so a caller of the short form never
breaks. With `group_label=None` it takes the label from that county's `gateway.open_counties()`
entry (a closed county has none and falls back to the county-name rule of step 3).

`county_groups` does the Dashboard work **once for all counties**:

1. `ranked = gateway.ranked(0)` exactly once (existing reviews, passive).
2. For each ranked applicant in `REVIEWABLE_STATUSES`, `gateway.match_for(ref)` exactly once,
   kept in `matches`.
3. Each applicant is assigned to every open county it belongs to: `_fits(match, group_label)`
   (the existing fit rule; pending never fits), or, when `group_label` is `None`, the
   applicant's own county equals the county by `_norm` (OPEN QUESTION 6).
4. Per county, sort by the `suggestions` key (score descending, `None` last; ties by earlier
   `submitted`, then `applicant_ref`) and keep the first `top_n`. `unreviewed` counts roster
   applicants (`_reviewable_applicants()`) that fit the county but have no review; their
   `match_for` calls are likewise made once each and shared across counties.
5. Returns one dict per county, in `open_counties` order: `{"county", "group_label",
   "open_count", "top_n", "total", "unreviewed", "applicants": [row, ...]}`. One
   `executive.county_groups` access audit with `result_count`.

`county_candidates` returns the same dict for one county (used by refresh after an opening
change). When `ranked`/`matches` are passed it reuses them; otherwise it makes the same single
`ranked(0)` call and one `match_for` per applicant. The cost of the provider is therefore one
`ranked(0)` plus one `match_for` per applicant, independent of the number of counties.

`top_n` is a parameter with the constant `DEFAULT_TOP_N = 5`, clamped to 1..50; actions accept
a `top_n` param that overrides it for that call.

### 8.3 Review data and field allowlist

`applicants.applicant_review(ref, *, gateway=None) -> dict` returns
`{"applicant_ref", "name", "position", "status", "submitted", "county", "city", "email",
"score", "recommendation", "summary", "strengths", "concerns", "criteria":
[{"criterion", "met", "evidence"}], "match": {"match", "alternates", "reasons",
"group_label"}, "label": ADVISORY_LABEL}` from `gateway.ranked`, `_review_fields` and
`gateway.match_for`, and writes one `rtec_applicants._audit_access("executive.applicant_review",
applicant_ref=ref, ...)`.

**Allowlist** (the only fields that may appear in a review, a county row, a compose payload,
an audit line or a model prompt): `applicant_ref`, `name`, `position`, `status`, `submitted`,
`county`, `city`, `email` (review and compose `to` only; never in rows or prompts),
`age_days`, `score`, `recommendation`, `summary`, `strengths`, `concerns`,
`criteria[criterion|met|evidence]`, `match[match|alternates|reasons|group_label]`. **Never**:
race, ethnicity, sex/gender, veteran, disability or any EEO, self-ID or AAP field,
`aa_pdf_path` or any document path, notes, denial reasons, screening flags, internal
`applicant_key`, source keys. The gateway's `_APPLICANT_FIELDS`, `_MATCH_FIELDS` and
`_REVIEW_FIELDS` already enforce this; tests include a poisoned-row case (as
`test_executive_eeo_firewall.py` does).

### 8.4 Review panel and decisions

Clicking an applicant in a county group invokes `applicant.review` on the county item with
`{"applicant_ref": ref}` and renders the result. The panel shows one-click buttons, each a
registered action invoked on the same county item with the same `applicant_ref`:

| Button | Action id | Result |
| --- | --- | --- |
| Reach out | `applicant.reach_out` | compose, kind `outreach` |
| Invite to interview | `applicant.invite_interview` | compose, kind `interview` |
| Email county manager | `applicant.email_manager` | compose, kind `manager` |
| Decline | `applicant.decline` | consequential preview, Confirm sets `Denied` |
| Hold | `applicant.hold` | one click; `set_applicant_status(ref, None, "Held by operator (Executive window)")` |

Hold is a Dashboard journal note only; the applicant stays in the list (OPEN QUESTION 3).

## 9. Manager email

`applicant.email_manager` builds the compose (`kind="manager"`, `applicant_ref`, `county`):

- `to` is `gateway.manager_for_county(county)["email"]`; with no manager the compose opens
  with `to == ""` and `warnings: ["no area manager found for <County> County"]`.
- `subject`: `"Applicant for <position>: <name> (<County> County)"`.
- `body` is a deterministic template (no model call) containing only allowlisted screening
  fields and match reasons; empty sections are omitted:

```
Hello <manager name>,

<name> applied for <position> and is a candidate for the <County> County opening.

Dashboard screening (advisory):
- Score: <score>/100, recommendation: <recommendation>
- Summary: <summary>
- Strengths: <strength>; <strength>
- Concerns: <concern>; <concern>
- Criteria: <criterion>: <met> (<evidence>), one line each
- Match reasons: <reason>; <reason>

Submitted: <submitted>   Status: <status>   City: <city>
```

A successful manager send records a journal entry only (section 4).

## 10. Natural-language opening events

Module `actions_openings.py` holds the parser and both openings actions.

```python
def parse_opening_event(text: str) -> dict[str, Any] | None
# {"change": "close"|"quit"|"new", "county": "Example", "count": 1} or None
```

Pure, deterministic, case-insensitive; extracts a county name (one to three words, optional
"County", optional "the"); returns `None` when unsure, for questions (trailing `?` or a leading
"did", "has", "is there", "should we") and for unrelated text such as "send an email to the
driver in X".

| change | Examples |
| --- | --- |
| `close` | "we closed the opening in X", "the X opening is filled", "we filled the position in X", "no longer hiring in X" |
| `quit` | "a driver quit in X", "we lost a driver in X", "two drivers quit in X" (count 2) |
| `new` | "we have a new opening in X", "new driver opening in X", "we're hiring in X" |

Two routes, one action:

1. **Chat (deterministic, no model).** `Api.post("/api/chat")` first calls
   `parse_opening_event(text)`. On a match it invokes `county.opening_change` on
   `county:<slug>` if that item exists, else on `openings:console`, and returns
   `{"reply": "<preview summary>. Click Confirm to apply it.", "message": same, "previews":
   [...], "error": null}` without calling the model. No match: the text goes to the model as
   today. The chat route catches `ValueError` and `KeyError` from that `county.opening_change`
   invoke (unknown county, nothing open to close, bad count, missing item) and returns HTTP
   200 `{"reply": "<message>", "message": same, "error": null, "previews": [...]}` with the
   exception's message, for example "Unknown county: X". It does not fall through to the
   model and never turns a parsed event into HTTP 400.
2. **Model tool.** `county.opening_change` is an `executive_window.run` tool; its description
   tells the model to use it for statements such as "we closed the opening in X". Being
   consequential, it only returns `needs_confirmation`.

On Confirm, `county.opening_change` calls `gateway.apply_opening_change`, then
`providers_applicants.invalidate_county_cache()`, and then **immediately** recomputes that county's group with `applicants.county_candidates`:

```json
{"applied": true, "county": "Example", "change": "quit", "before": {}, "after": {},
 "group": {"id": "county:example", "county": "Example", "open_count": 2,
           "group_label": "...", "applicants": [], "total": 7, "unreviewed": 1},
 "message": "A driver quit in Example County: openings 1 to 2. Applicants to review below."}
```

`group` is `None` for a closed county. The UI then reloads `/api/items` and highlights
`county:<slug>`.

## 11. Action registry

Each capability is registered with `register_action`, so it shows as an item option (by
`applies_to`) and as an `executive_window.run` tool. `params_schema` is a JSON-schema object
with `properties` (as the `email.*` actions do). Applicant actions require `applicant_ref`,
which must be in the county item's `context.applicants`; otherwise `ValueError`.

| Action id | Module | applies_to | Consequential | Params | Result |
| --- | --- | --- | --- | --- | --- |
| `applicant.review` | `actions_applicant_decisions` | `county_openings` | no | `applicant_ref` | section 8.3 review dict |
| `applicant.reach_out` | `actions_applicant_compose` | `county_openings` | no | `applicant_ref`, `message` (opt) | compose, kind `outreach` |
| `applicant.invite_interview` | `actions_applicant_compose` | `county_openings` | no | `applicant_ref`, `interview_type` (opt, default "phone"), `location` (opt) | compose, kind `interview` |
| `applicant.email_manager` | `actions_applicant_compose` | `county_openings` | no | `applicant_ref`, `note` (opt) | compose, kind `manager` |
| `applicant.decline` | `actions_applicant_decisions` | `county_openings` | **yes** | `applicant_ref`, `note` (opt) | preview `{"applicant_ref", "name", "from_status", "to_status": "Denied"}`; on Confirm `{"declined": true, "journal_id", "group"}` |
| `applicant.hold` | `actions_applicant_decisions` | `county_openings` | no | `applicant_ref`, `note` (opt) | `{"held": true, "applicant_ref", "journal_id"}` |
| `county.refresh` | `actions_openings` | `county_openings` | no | `top_n` (opt) | refreshed group dict |
| `county.opening_change` | `actions_openings` | `county_openings`, `openings_console` | **yes** | `change` (`close\|quit\|new`), `county` (required on the console), `count` (opt, 1..20) | preview: section 4 preview dict; on Confirm: section 10 result |

`builtin.default_registry` calls `register(registry.REGISTRY)` of the three new action modules
after the existing ones. Handlers return only JSON-safe, allowlisted data. Compose actions are
audited with `kind`, `applicant_ref`, `county` only.

### 11.1 Existing senders changed in this run

Owned by the compose-actions task (the owner of `actions_applicant_compose.py`), which also
updates `tests/test_executive_window_actions_email.py`,
`tests/test_executive_window_actions_executive.py` and `tests/test_executive_window_builtin.py`
to match:

| Action id | Change |
| --- | --- |
| `executive.reach_out` | **Unregistered.** `actions_executive.register` registers only `executive.plan_interviews` and `executive.approve_batch`. No window action or model tool reaches `gateway.send_now` / `email_sender`. After a batch is approved the operator sends each applicant with `applicant.reach_out` (compose, then Send). |
| `email.send` | **Unregistered.** The confirm-to-send path and its `TRANSPORT` hook are removed from the registry; the only send path is `POST /api/send`. |
| `email.reply_draft` | Still non-consequential on `mail_thread`; returns the `kind: "reply"` compose payload of section 5 (it may still save the `.eml` draft, which is not part of the contract). |

`ex.send_batch` and `gateway.send_now` stay in the code for the existing batch tests; nothing
in the window, its registry or the model tools calls them.

## 12. Follow-ups (not in this run; no task here implements them)

- A file-backed compose store so a compose produced by the model through
  `executive_window.run` (another process) also opens in the window. In this run the panel
  opens from the result of actions the window itself invokes.
- Hiding held applicants for a period (an Executive-side hold ledger).
- An Executive-side sent ledger with retry of failed Dashboard updates.
- A persisted `top_n` setting and a settings endpoint.
- Per-applicant registry item ids (`Registry.item`), and resolving `/api/act` items without
  re-running every provider.

## 13. Validation

```
python -m unittest tests.test_executive_window_docs
python -m unittest discover -s tests -v
python agent.py validate
```

Never in any test: real Outlook, SMTP/IMAP, keyring, Dashboard database or network. Protected
control-plane paths are unchanged. Only the final status node appends to
`projects/personal-agent-os/orchestrator-os/status.json`.
