# Mail intelligence: spam filtering and inbox organization (contract)

Status: **binding contract** for the implementation tasks of the "Executive mail intelligence" run
(operator spec 2026-10-02). This file describes code that does not exist yet. Later tasks implement
exactly what is written here; a task that needs to deviate changes this file first, in the same
change, and says why. Where this file and an older doc disagree about this feature (for example the
"read-only" wording in `docs/integrations/mail.md`), this file wins, and the task that lands the code
updates the older doc.

Section numbers match the operator spec and the task graph:

* **Section 1**: spam/bulk classifier (`spam.py`, `spam_eval.py`) and its use in the commitments.
* **Section 2**: inbox categorizer and organization plan (`organize.py`).
* **Section 3**: applying the plan: IMAP moves, the per-account switch, journal and undo
  (`imap_write.py`, `organize_apply.py`, CLI).
* **Section 4**: window integration (`actions_mail_organize.py`).
* **Section 0** (foundations: module map, header columns, `iter_rows`) is shared groundwork, not one of the three spec items.

Operator rules that shape everything below:

* **No Outlook, no COM.** Moves happen over IMAP only (`UID MOVE`, or `UID COPY` plus a flag when
  the server has no MOVE), per account. There is no backend choice: no `choose_backend` function and
  no Outlook branch exist anywhere in this feature.
* **Never delete, never expunge.** Only reversible moves. Every move is journaled with an undo command.
* **Dry-run is the default.** Applying needs the operator's Confirm, one Confirm per category.
* Accounts stay read-only for sync. A new per-account setting `allow_organize` (default **off**) is the
  only thing that lets Agent OS write to an account's mailbox, and the operator turns it on from the window.
* **Nothing disappears silently.** Everything filtered out of the commitments is counted and visible, with its reason.

**Field name (fixed):** the per-account switch is named `allow_organize` (operator wording) everywhere: the
`Account` field, the `accounts.json` key, `Account.public()`, the plan, the window and the CLI. The
`account-allow-moves` task implements it under this name; there is **no** `allow_moves` field or alias.

Goals the contract serves: "filter out the spam from the commitments" and "organize my entire email inbox".

**Scope of this run.** Only what section 5 lists as a step's deliverable is binding for this run. Everything in
section 0.3 is **deferred**: it is described so a later run builds it the same way, but no task in this run
implements it, no test in this run asserts it, and a reviewer must not treat its absence as a defect. Where a task
description and this file differ, this file wins; section 5 lists each task's scope and the overrides.

## 0. Foundations

### 0.1 Module map (who owns what)

| Path | New / changed | Purpose | Section |
|---|---|---|---|
| `src/agent_os/mail/message.py`, `store.py` | changed | Capture four headers (schema v3), `Store.iter_rows`, `Store.mark_source_moved` / `mark_source_present` (`Store.set_headers` deferred, D1) | 0.2 |
| `src/agent_os/mail/imap.py` | unchanged in this run | `ReadOnlyIMAP.fetch_headers` is deferred (D1) | 0.2 |
| `src/agent_os/mail/spam.py` | new | Deterministic spam/bulk classifier `classify`, `known_correspondents` (`classify_with_overrides` deferred, D2) | 1 |
| `src/agent_os/mail/spam_eval.py` | new | `SYNTHETIC` labeled set, `evaluate` (precision/recall), `review_queue` | 1.7 |
| `src/agent_os/mail/organize.py` | new | Categorizer, `CATEGORIES`, `TARGET_FOLDERS`, `categorize`, `build_plan`, `plan_summary`; pure, no I/O except `plan_from_index` | 2 |
| `src/agent_os/mail/imap_write.py` | new | `ImapMover`: a second, separate IMAP wrapper whose allowed command set is exactly the move set; `connect_write` | 3.1 |
| `src/agent_os/mail/organize_apply.py` | new | `Mover` protocol, `apply_plan`, `undo`, journal; the only caller of `imap_write` | 3.3-3.5 |
| `src/agent_os/mail/accounts.py` | changed | `Account.allow_organize`, `set_allow_organize` | 3.2 |
| `src/agent_os/mail/cli.py` | changed | `agent-os mail organize-plan`, `organize-apply`, `organize-undo`, `account organize` (`organize-journal`, `headers-backfill` deferred, D5/D1) | 3.6 |
| `src/agent_os/executive/window/providers_mail.py` | changed | Commitments use the classifier; `mail_filtered` and `mail_review` items | 1.8 |
| `src/agent_os/executive/window/actions_mail_organize.py` | new | Provider `mail_cleanup_items` and the window actions (section 4); `register(registry)` | 4 |
| `src/agent_os/executive/window/builtin.py` | changed | `register_provider("mail_cleanup", actions_mail_organize.mail_cleanup_items)` and `actions_mail_organize.register(registry.REGISTRY)` | 4 |
| tests | new | `tests/test_mail_spam.py`, `tests/test_mail_organize.py`, `tests/test_mail_organize_apply.py`, plus additions to `tests/test_mail.py`, `tests/test_mail_accounts.py`, `tests/test_executive_window_provider_mail.py` | |

Test rules for every task: synthetic data and fakes only (a `FakeIMAP` client object or a fake `Mover`,
temporary directories, injected `search`/`now`); no real mail, Outlook, Dashboard database or network. Every
test file starts with `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))`.

### 0.2 Data the classifier needs (schema v3)

The local index (`mail_messages`) does not store the four headers the classifier uses. The schema task adds:

* `SCHEMA_VERSION = 3`. Four nullable TEXT columns on `mail_messages`: `list_unsubscribe`, `list_id`,
  `precedence`, `auto_submitted`. Added with guarded `ALTER TABLE ... ADD COLUMN` (check `PRAGMA table_info`),
  after the existing migration backup convention. Header values are stored trimmed and cut at 500 characters;
  nothing else from the header block is stored.
* `ParsedMessage` gets the same four fields at the end, default `None`, so existing constructors (PST,
  `_parsed_from_row`, tests) keep working. `message.parse` fills them from the raw message. They are not part
  of `content_hash` or `composite_key`.
* `Store.record` writes them for new logical messages. When a logical message already exists, a NULL column is
  filled and a non-NULL column is never overwritten (first observation wins).
* `Store._summary` (and therefore `mail.search`) returns the four keys, `None` when unknown, so search rows can
  be passed straight to `classify`.
* Existing rows have NULL headers. The classifier treats NULL like "header absent", so old mail is classified
  on the remaining signals (degraded mode). **(deferred, D1)** `agent-os mail headers-backfill [--account ID]` fills them without
  re-downloading bodies, through the new read-only method `ReadOnlyIMAP.fetch_headers(uids)` that issues
  `UID FETCH ... (BODY.PEEK[HEADER.FIELDS (LIST-UNSUBSCRIBE LIST-ID PRECEDENCE AUTO-SUBMITTED)])` and `Store.set_headers`.
  `PEEK` keeps it inside the existing read-only guard (`FORBIDDEN_FETCH` does not match `BODY.PEEK[`).
  PST/archive rows have no headers and stay NULL.
* `Store.iter_rows(*, accounts=None, mailboxes=None, after=None, before=None, senders=None, live_only=True)`
  is a generator over the whole index with no `MAX_LIMIT` cap (search is capped at 50). It yields one **row** per
  live IMAP source (state `present`; archive sources are skipped when `live_only`), shaped as in section 2.1.
  `mail.iter_rows(scope=None, db_path=None, **filters)` is the module-level wrapper (same `_target` rules as `mail.search`).
* `Store.mark_source_moved(source_id)` sets the source's `state` to `missing` (the existing state the sync already
  uses for UIDs that left a mailbox); the logical message is kept. `Store.mark_source_present(source_id)` reverses it for undo.

Folders to sync: spam-folder detection and "known correspondent" detection need the Junk and Sent folders in
the account's `folders` list (default is only `INBOX`). Without them the signals are simply absent: no folder
verdicts, and every sender counts as a first contact. This is a documented degraded mode, not an error.

### 0.3 Deferred (not built in this run)

These items appear further down so the design stays whole, each marked **(deferred, 0.3)** where it appears.
No task of this run implements them; the delivered code must not depend on them.

| Id | Deferred item | What this run does instead |
|---|---|---|
| D1 | Header backfill: `ReadOnlyIMAP.fetch_headers`, `Store.set_headers`, `agent-os mail headers-backfill` | Headers are captured for newly synced mail only; older rows are classified in degraded mode (NULL = absent) |
| D2 | Operator decisions on the review queue: `classify_with_overrides`, `<window_home>/mail-review.json`, the actions `mail.review.human` / `mail.review.bulk` | The review queue is built and shown (`review_queue`, `mail_review` items); every call site uses `classify`, and `review_queue` / `mail_items` take no `overrides` parameter |
| D3 | The `mail.filtered.show` action | The `mail_filtered` item shows the counts and top reasons, and borderline mail is listed as `mail_review` items |
| D4 | Automatic reconciliation of orphaned `pending` journal lines | An orphaned `pending` line is left as written; `undo` skips that `seq` and reports it in `skipped` with reason `no final journal line` |
| D5 | `agent-os mail organize-journal` | The journal file is plain JSON lines; `organize-apply --confirm` prints the `journal_id` and each moved line's `undo.command` |
| D6 | The window action `mail.organize.undo` | Undo runs through `agent-os mail organize-undo` (the `undo.command` in every journal line) |

## 1. Spam/bulk classifier: `src/agent_os/mail/spam.py`

### 1.1 API

```python
VERDICTS = ("human", "bulk", "spam", "review")
HUMAN_MAX = 2      # score <= 2            -> human
REVIEW_MIN = 3     # 3 <= score <= 5       -> review (borderline)
BULK_MIN = 6       # score >= 6            -> bulk (or spam, see 1.4)

def classify(message: dict, *, own: set[str], known: set[str]) -> dict:
    """-> {'verdict': 'human'|'bulk'|'spam'|'review', 'reasons': [str], 'score': int}"""

def known_correspondents(rows, own: set[str]) -> set[str]: ...

def classify_with_overrides(message, *, own, known, overrides: dict) -> dict: ...   # 1.6 (deferred, D2)
```

`message` keys: `sender`, `recipients`, `subject`, `snippet`, `mailbox`, `list_unsubscribe`, `list_id`,
`precedence`, `auto_submitted`. Any key may be missing or `None`; extra keys are ignored (so an index row or
search row is passed as is). `sender` may be `Name <addr>`; the address is parsed with
`email.utils.parseaddr` and lower-cased. `recipients` is the comma-separated string the index stores (a
list/tuple/set of strings is also accepted). `own` and `known` are sets of lower-case addresses; `classify`
never mutates them and never raises on missing or odd values (it raises `TypeError` only when `message` is not a dict).
A header counts as **present** when its value is not `None` and `str(value).strip() != ""`.

Result: `verdict` as below; `reasons` is a non-empty list of short human strings, in signal order (table in 1.3),
followed, for verdict `spam` from the spam rule only, by the reason `unsolicited promotion (no unsubscribe headers)`
(1.4); no other verdict adds a verdict-level reason. Inside `promotional subject (...)` the matched marker labels
are listed in the order of the marker list in 1.3, joined with `, `. `score` is an `int`, never negative. Same
input gives identical output.

`known_correspondents(rows, own)` returns the lower-case addresses that appear in `recipients` (and in `cc`
when the row carries it) of rows whose sender address is in `own`, minus `own` itself. It is the only way the
set `known` is built ("the operator has replied before"; being merely CC'd on someone's mail does not count).
Rows come from `mail.iter_rows(scope, senders=own)`, per scope, so the work and personal indexes stay separate.

### 1.2 Decision order

1. **Own sent mail**: sender address in `own` -> verdict `bulk`, reasons `["own sent mail"]`, score `0`.
   "Bulk" here means "excluded from commitments"; own mail is **never** `spam` and never reaches the spam category.
2. **Server spam folder**: `mailbox` matches (case-insensitive, after splitting on `/`, `.` and `\` and
   taking the last segment, trimmed) one of `junk`, `junk e-mail`, `junk email`, `spam`, `bulk mail`
   -> verdict `spam`, reasons `["in server spam folder (<mailbox>)"]`, score `100`. `INBOX.Junk` and
   `[Gmail]/Spam` match; `Junk Notes` does not. `known` does not override this.
3. Otherwise add up the signals in 1.3, clamp at 0, then apply the thresholds and the spam rule (1.4).

### 1.3 Signals and weights

| # | Signal | Weight | Reason string |
|---|---|---|---|
| 1 | `list_unsubscribe` present | +5 | `has List-Unsubscribe header` |
| 2 | `list_id` present | +5 | `mailing list (List-Id)` |
| 3 | `precedence` is `bulk`, `list` or `junk` (case-insensitive, trimmed) | +4 | `Precedence: <value>` |
| 4 | `auto_submitted` present and its trimmed lower-case value is not `no` | +8 | `auto-generated (Auto-Submitted)` |
| 5 | Sender local part matches the **strong** pattern | +6 | `automated sender address` |
| 5 | Sender local part matches the **weak** pattern (only when not strong) | +2 | `generic sender address (<local>@)` |
| 6 | Sender domain is a bulk-mail sending domain or has a bulk label | +3 | `bulk-mail sending domain (<domain>)` |
| 7 | Subject has promotional markers: +2 per **distinct** marker, at most +4 | +2 / +4 | `promotional subject (<marker>, <marker>)` |
| 8 | Snippet contains the word `unsubscribe` and marker `unsubscribe` was not counted in 7 | +1 | `mentions unsubscribe` |
| 9 | Sender is a **known correspondent** | -4, -2 or 0 (below) | `known correspondent (you replied before)` |
| 10 | Sender is neither in `known` nor in `own` and has a parseable address | +1 | `first contact (you never replied)` |

Caps and exceptions:

* Signals 5 and 6 together contribute at most **+8**.
* Signal 9 (known): the discount is `0` when the message is auto-generated (signal 4) or the sender matches the
  strong pattern; `-2` when any of signals 1, 2, 3 is present (a known address relaying mailing-list mail is
  still suspect); otherwise `-4`. When the discount is `0` signal 9 adds no reason.
* Signals 9 and 10 are mutually exclusive.
* The final score is `max(0, sum)`.
* A missing signal is simply not counted; with no signal at all the reasons are `["no bulk signals"]` (this only
  happens for a sender with no parseable address).

Pattern tables (module constants in `spam.py`; the lists below are the initial contents and may be extended
by later tasks as long as the labeled set in 1.7 still meets its targets):

* **Strong sender** (regex on the lower-case local part, i.e. before `@`, optionally followed by one of `-_.+`
  or a digit and anything): `no-reply` / `noreply` / `no_reply` / `no.reply`, `do-not-reply` / `donotreply` (same
  separators), `mailer-daemon`, `postmaster`, `bounce`, `bounces`, `newsletter`, `newsletters`, `marketing`,
  `promo`, `promos`, `promotion`, `promotions`, `mailer`, `notification`, `notifications`, `notify`, `alert`,
  `alerts`, `autoreply`, `auto-reply`, `automated`. Example matches: `noreply`, `no-reply`, `bounce+8d2f`,
  `notifications`. The pattern is anchored, so `bouncer` and `notifyme` do not match.
* **Weak sender**: `info`, `news`, `hello`, `team`, `support`, `update`, `updates`, `offer`, `offers`, `deal`,
  `deals`, `sales`, `order`, `orders`, `billing`, `account`, `accounts`, `service`, `customercare`,
  `customerservice`, `contact`, `admin`, `press`, `event`, `events`, `careers`, same optional suffix rule.
* **Bulk sending domains** (domain equals or ends with `.` + entry): `sendgrid.net`, `amazonses.com`,
  `mailchimp.com`, `mcsv.net`, `mcdlv.net`, `rsgsv.net`, `constantcontact.com`, `ctctcdn.com`,
  `hubspotemail.net`, `mailgun.org`, `mandrillapp.com`, `sparkpostmail.com`, `sendinblue.com`, `brevo.com`,
  `klaviyomail.com`, `exacttarget.com`, `createsend.com`, `campaign-archive.com`, `mailjet.com`,
  `postmarkapp.com`, `customeriomail.com`. **Bulk labels**: the domain's first label is one of `email`, `e`,
  `em`, `news`, `newsletter`, `newsletters`, `marketing`, `promo`, `promos`, `offers`, `mailer`, `bounce`,
  `bounces`, `mg`, `click` (so `em.brand.com` matches; `mail.earthlink.net` does not).
* **Promotional subject markers** (case-insensitive, word-boundary, subject only; each label counts once):
  `% off` (`\d+\s?%\s*off` or `% off` or `percent off`), `sale`, `deal` (`deal`/`deals`), `discount`, `coupon`,
  `promo` (`promo`/`promotion`/`promo code`), `free shipping`, `limited time` (`limited time`/`limited-time`),
  `last chance`, `act now`, `don't miss`, `exclusive offer` (`exclusive offer|deal|access`), `special offer`,
  `save $` (`save (up to )?\$?\d+`), `clearance`, `bogo`, `order now`, `shop now`, `new arrivals`, `webinar`,
  `unsubscribe`, `newsletter`, `digest` (`weekly digest|daily digest`), `giveaway`, `winner`, `black friday`,
  `cyber monday`.

### 1.4 Verdict thresholds and the spam rule

After clamping:

| Score | Verdict | Meaning |
|---|---|---|
| 0-2 (`<= HUMAN_MAX`) | `human` | likely a person who needs a reply; eligible for commitments |
| 3-5 (`REVIEW_MIN`..`BULK_MIN - 1`) | `review` | **borderline band**: kept out of auto-filtering and shown to the operator |
| >= 6 (`>= BULK_MIN`) | `bulk` | automated, marketing or list mail; filtered out of commitments |

**Spam rule** (refines `bulk`): a result whose score is >= 6 is `spam` instead of `bulk` when **all** hold:
the sender is not in `known`; none of `list_unsubscribe`, `list_id`, `precedence` is present (legitimate bulk
senders carry them, spammers usually do not); and at least two distinct promotional markers matched in the
subject. The reason `unsolicited promotion (no unsubscribe headers)` is appended last. A newsletter with a
`List-Unsubscribe` header is therefore `bulk`, never `spam`.

The review band is exactly scores 3, 4 and 5 for messages that are not own mail and not in a spam folder.
Typical members: an unknown person whose subject says "webinar" (2 + 1 = 3); `info@smallbiz.example` writing
for the first time (2 + 1 = 3); a first-contact message with only `Precedence: list` (4 + 1 = 5); a known
correspondent relaying list mail (5 - 2 = 3). A `review` row is **never moved** by organization (section 2.2)
and never becomes a commitment (1.8); in this run it stays in the review queue, and operator decisions on it
are deferred (1.6, D2).

### 1.5 Worked examples (the test task must include these verbatim)

`own = {"me@example.com"}`, `known = {"pat@corp.com"}`. Every message below has `mailbox="INBOX"` and no
`list_unsubscribe`, `list_id`, `precedence` or `auto_submitted` unless the row says otherwise. The Reasons column
is the exact `reasons` list, in order.

| Message | Score | Verdict | Reasons |
|---|---|---|---|
| `Pat <pat@corp.com>`, "Lunch?" | 0 (-4 clamped) | human | `known correspondent (you replied before)` |
| `Lee <lee@new.org>`, "Lunch?" | 1 | human | `first contact (you never replied)` |
| `noreply@shop.com`, "Your receipt" | 7 (6 + 1) | bulk | `automated sender address`, `first contact (you never replied)` |
| `news@brand.com`, "Spring SALE: 30% off", `list_unsubscribe="<mailto:u@brand.com>"` | 12 (5 + 2 + 4 + 1) | bulk (a list header is present, so not spam) | `has List-Unsubscribe header`, `generic sender address (news@)`, `promotional subject (% off, sale)`, `first contact (you never replied)` |
| `deals@promo-mart.biz`, "Limited time deal: 50% off" | 7 (2 + 4 + 1) | spam | `generic sender address (deals@)`, `promotional subject (% off, deal, limited time)`, `first contact (you never replied)`, `unsolicited promotion (no unsubscribe headers)` |
| `Lee <lee@new.org>`, "Webinar invite?" | 3 (2 + 1) | review | `promotional subject (webinar)`, `first contact (you never replied)` |
| `Pat <pat@corp.com>`, "Webinar notes" | 0 (2 - 4 clamped) | human | `promotional subject (webinar)`, `known correspondent (you replied before)` |
| `info@smallbiz.example`, "Your quote" | 3 (2 + 1) | review | `generic sender address (info@)`, `first contact (you never replied)` |
| `pat@corp.com`, "Out of office", `auto_submitted="auto-replied"` | 8 (no known discount) | bulk | `auto-generated (Auto-Submitted)` |
| `pat@corp.com`, "Minutes from Tuesday", `list_id="<team.corp.com>"` | 3 (5 - 2) | review | `mailing list (List-Id)`, `known correspondent (you replied before)` |
| `me@example.com`, "Re: Lunch?" | 0 | bulk | `own sent mail` |
| `Lee <lee@new.org>`, "Lunch?", `mailbox="Junk E-mail"` | 100 | spam | `in server spam folder (Junk E-mail)` |

### 1.6 Operator decisions on the review queue (deferred, D2)

Not built in this run; described for the later run. The review queue is the set of `review` verdicts. The operator answers per sender: "this is a person" or
"this is bulk". Decisions persist in `<window_home>/mail-review.json`
(`{"human": {"addr": "<iso>"}, "bulk": {"addr": "<iso>"}}`, written with the same atomic temp-file-and-replace
helper as `confirm._write_json`). `classify_with_overrides(message, *, own, known, overrides)` calls `classify`
and then applies, in this precedence: own sent mail (unchanged) > override > the computed result. A `human`
override returns verdict `human`, score `0`, reasons `["operator marked sender as human"]`; a `bulk` override
returns `bulk`, reasons `["operator marked sender as bulk"]`. `classify` itself stays pure and override-free.

### 1.7 Precision, recall and the review queue: `src/agent_os/mail/spam_eval.py`

```python
SYNTHETIC: list[tuple[dict, str]]       # (message, gold label) with label in "human", "bulk", "spam"
SYNTHETIC_OWN: set[str]                 # own addresses the set is written against ({"me@example.com"})
SYNTHETIC_KNOWN: set[str]               # known correspondents the set is written against

def evaluate(cases=SYNTHETIC, *, own=SYNTHETIC_OWN, known=SYNTHETIC_KNOWN) -> dict: ...
def review_queue(rows, *, own, known, limit: int = 100) -> list[dict]: ...
```

`SYNTHETIC` is the synthetic labeled set, kept in the module (not in the test) so the window and CLI can report
the same numbers. All addresses use `example.com`/`.example`/`.org` style test domains; no real mail.

`evaluate(cases, *, own, known)` returns:

```json
{"n": 0, "precision": 0.0, "recall": 0.0, "human_protected": 0.0, "review_rate": 0.0,
 "false_positives": [], "missed": [], "review": [],
 "confusion": {"human": {"human": 0, "bulk": 0, "spam": 0, "review": 0}, "bulk": {}, "spam": {}}}
```

* The positive class is "not a person" (gold `bulk` or `spam`). A prediction is positive when the verdict is
  `bulk` or `spam`.
* `precision = TP / (TP + FP)`: of the mail filtered out, how much really was not a person.
* `recall = TP / gold_positives`: a `review` verdict counts as **not filtered** (a miss), because the operator
  still has to look at it.
* `human_protected = 1 - (gold human predicted bulk or spam) / gold_human`: the share of real person mail that
  stays visible (`human` or `review`).
* `review_rate = review verdicts / n`.
* `false_positives`, `missed` and `review` list `subject`, `score` and `reasons` for inspection. An empty
  denominator gives `1.0`.

`review_queue(rows, ...)` is the operator-review queue for borderline cases: every row whose
`classify` verdict is `review` (the deferred D2 adds an `overrides` parameter later), as `{"message_id", "account_id", "scope", "subject", "sender",
"score", "reasons"}`, highest score first, then newest first, capped at `limit`. The plan (2.3) and the window
(1.8) both use it.

`SYNTHETIC` has at least 60 cases: every signal in 1.3 exercised at least twice, every worked example in 1.5, at
least 15 human cases (including a person writing "sale of the house", a known colleague on a list, a
first-contact recruiter), at least 15 bulk and 10 spam cases. **Acceptance targets** asserted by
`tests/test_mail_spam.py` on `evaluate()`: `precision >= 0.95`, `recall >= 0.85`, `human_protected == 1.0` for
gold human cases that are known correspondents, **no gold-human case ever gets verdict `spam`**, and
`review_rate <= 0.15`. The test prints the metrics, and the implementer pastes the measured numbers into the
section "Measured results" at the bottom of this file.

### 1.8 Use in the window's commitments

`providers_mail.mail_items` keeps its signature (`db_path`, `own_addresses`, `days`, `limit`, `search`, `now`)
and gains `known: set[str] | None = None` (no `overrides` parameter in this run, D2).

* `known=None` means: compute per scope with `known_correspondents(mail.iter_rows(scope, senders=own), own)`
  when the default search is used, or from the rows the injected `search` returned (so tests need no index).
* For each thread's latest message, call `classify`. Only verdict `human` becomes a
  `mail_thread` item. The old `AUTOMATED` regex and the "sender is own" check are removed (the classifier
  covers both); the third point of `_score` ("not automated") becomes "verdict is human" and the `score >= 2`
  gate stays as it is.
* Filtered mail is never silently dropped. The provider also returns, per tab:
  * one `mail_filtered` summary item (section 4.1) with counts of `spam`, `bulk`, `own_sent`, `review` and
    the top reasons, counted over the **window row set**: the latest message of each thread the provider
    considered for that tab (the same rows the commitments are chosen from, within `days`);
  * up to 20 `mail_review` items for the borderline band (`spam_eval.review_queue` over the same window row
    set), newest first.
* Verdict `review` threads are **not** commitments; they live in the review queue.

## 2. Inbox categorizer: `src/agent_os/mail/organize.py`

### 2.1 Row shape (input)

One dict per live IMAP source in the INBOX of every configured account, from both scopes
(`mail.iter_rows`). Other mailboxes (Sent, Junk, folders the operator already made) are used as context only,
they are never moved.

```
id (index message id, "msg_..."), thread_id, message_id (RFC), subject, sender, recipients, date (ISO UTC),
snippet, scope ("work"|"personal"), account_id, provider, mailbox, uidvalidity, uid, source_id, flags,
list_unsubscribe, list_id, precedence, auto_submitted
```

### 2.2 Categories, rule order and target folders

```python
CATEGORIES = ("action_needed", "waiting_on_others", "receipts_finance", "newsletters_promotions",
              "notifications", "hr_applicants", "personal", "spam", "archive_old")

TARGET_FOLDERS = {
    "action_needed": None,            # stays in INBOX, never moved
    "waiting_on_others": None,        # stays in INBOX, never moved
    "receipts_finance": "Agent OS/Receipts",
    "newsletters_promotions": "Agent OS/Newsletters",
    "notifications": "Agent OS/Notifications",
    "hr_applicants": "Agent OS/Applicants",
    "personal": "Agent OS/Personal",
    "spam": "Agent OS/Spam",
    "archive_old": "Agent OS/Archive",
}
```

`target_folder` is `None` exactly for the two categories that stay in the INBOX, and those two have no apply
action. Folder names use `/` here; `organize_apply` converts them to the account's real hierarchy delimiter and
namespace prefix (for example `INBOX.Agent OS.Receipts`). `build_plan(..., folders={...})` can override any
`TARGET_FOLDERS` entry; an override of `None` for a movable category means "report it but do not move it".

`categorize(row, *, own, known, now, thread_last_own=False) -> {"category", "reasons": [str], "verdict", "review": bool}`
evaluates the first matching rule below (it calls `spam.classify` with the row; `known` is the set for the
row's scope). `thread_last_own` is true when the newest message of the row's thread (any folder of the same
scope index) is own sent mail; `build_plan` computes it by grouping rows on `thread_id`.

| Order | Category | Rule |
|---|---|---|
| 0 | (excluded) | Own sent mail (verdict `bulk` with reason `own sent mail`) is never categorized or moved; it is counted in `spam_filtered.own_sent` |
| 1 | `spam` | verdict `spam` (a row already in a server spam folder gets this category but `move = false`: it is already filed) |
| 2 | `hr_applicants` | scope `work`, verdict `bulk` (**never** `human` or `review`: a person writing about an application needs a reply and goes on to rules 6-7), and the subject matches `applicant|application|apply|resume|r[ée]sum[ée]|cv\b|candidate|interview|hiring|recruit|job posting|offer letter|onboarding` or the sender domain is a job board (`indeed.com`, `ziprecruiter.com`, `greenhouse.io`, `lever.co`, `workable.com`, `applytojob.com`, `jobvite.com`, `smartrecruiters.com`) |
| 3 | `receipts_finance` | verdict `bulk` and the subject matches `receipt|invoice|order confirmation|your order|payment|statement|billing|refund|transaction|tax|paid` or the sender local part is `billing|invoice|invoices|receipts?|payments?|orders?` or the domain is `paypal.com`, `stripe.com`, `squareup.com`, `venmo.com` |
| 4 | `notifications` | verdict `bulk`, the sender matches the strong sender pattern or `auto_submitted` is present, and no promotional marker matched the subject |
| 5 | `newsletters_promotions` | verdict `bulk` (everything else that is bulk: list headers, marketing senders, promotional subjects) |
| 6 | `waiting_on_others` | verdict `human` and `thread_last_own` (the operator spoke last) |
| 7 | `action_needed` | **every** row with verdict `review`, whether or not it asks or the operator spoke last (`review = true`); or verdict `human`, the thread's newest message is not own, and the row **asks**: `?` in subject or snippet, or an `own` address is in `recipients` (directly addressed) |
| 8 | `personal` | scope `personal`, verdict `human`, and the row does not ask (no `?`, not directly addressed: a CC or FYI) |
| 9 | `archive_old` | age (against `now`) over **365 days** for any row that reached this point |
| 10 | `action_needed` (default) | anything left, for safety: it stays in the INBOX |

Mail that needs a reply is never moved: rules 1-5 require verdict `spam` or `bulk`, so a verdict-`human` row
reaches rule 6 at the earliest, and a `human` row that asks (a `?`, or the operator directly addressed) and is
not waiting on others always becomes `action_needed` in the INBOX, whatever its subject (an applicant writing
"Interview time?" stays in `action_needed`). Borderline mail is never moved either: rule 6 requires `human`, so a
verdict-`review` row always stops at rule 7, never reaches rules 8-9, and the age overlay below never applies to
it (`action_needed` is never archived). `review = true` is set only by rule 7 and those rows also appear in
`review_queue`.

Age overlay: after rules 1-8, a row whose category is `notifications`, `newsletters_promotions`, `personal` or
`waiting_on_others` and whose age is over 365 days becomes `archive_old`. `spam`, `hr_applicants` and
`receipts_finance` keep their category at any age (records stay findable), and **`action_needed` is never
archived**, which is the whole meaning of "older than 365 days and not action_needed". A row whose date is
missing or unparseable is treated as age 0.

Each categorized row carries short `reasons` (the classifier reasons, plus the matching rule in words, for
example `subject mentions "invoice"`). `reasons` are not part of the plan summary the window shows, but are in
the stored plan for the operator's drill-down.

### 2.3 `build_plan`

```python
def build_plan(rows, *, own: set[str], known: dict[str, set[str]] | set[str], now: datetime | None = None,
               folders: dict[str, str | None] | None = None, allow: dict[str, bool] | None = None,
               sample_size: int = 5) -> dict: ...

def plan_from_index(scopes=("work", "personal"), *, now=None, db_paths=None, folders=None) -> dict: ...
def plan_summary(plan: dict) -> dict: ...
```

`build_plan` is pure (no I/O). `known` is a mapping scope -> set (a plain set applies to every scope). `folders`
overrides entries of `TARGET_FOLDERS`. `allow` maps `account_id` to its `allow_organize` value for display only.
`plan_from_index` is the I/O wrapper: it reads `mail.iter_rows` for each scope that has an index (a scope with no
index is skipped and simply missing from `scopes`), loads `own` from the configured accounts and `known` per
scope, and returns `build_plan(...)`. `plan_summary` returns the plan without `message_ids` and `sources` (this
is what the window shows and what the model is given).

**Plan JSON** (stable keys; every category is always present for every account, with `count: 0` and empty
lists when nothing matched):

```json
{
  "plan_id": "plan_<first 16 hex of sha256(generated_at + per-account counts)>",
  "generated_at": "2026-10-02T12:00:00+00:00",
  "scopes": ["work", "personal"],
  "folders": {"action_needed": null, "receipts_finance": "Agent OS/Receipts", "...": "..."},
  "accounts": {
    "work-earthlink": {
      "scope": "work",
      "email": "me@example.com",
      "allow_organize": false,
      "inbox_total": 120,
      "categories": {
        "action_needed": {"count": 8, "samples": ["Lunch?", "..."], "target_folder": null, "message_ids": ["msg_..."]},
        "waiting_on_others": {"count": 0, "samples": [], "target_folder": null, "message_ids": []},
        "receipts_finance": {"count": 14, "samples": ["Your invoice 104"], "target_folder": "Agent OS/Receipts", "message_ids": ["msg_..."]},
        "newsletters_promotions": {}, "notifications": {}, "hr_applicants": {}, "personal": {}, "spam": {}, "archive_old": {}
      }
    }
  },
  "spam_filtered": {
    "total": 0, "spam": 0, "bulk": 0, "own_sent": 0, "review": 0,
    "by_reason": {"has List-Unsubscribe header": 0},
    "by_account": {"work-earthlink": {"spam": 0, "bulk": 0, "own_sent": 0, "review": 0}}
  },
  "review_queue": [{"message_id": "msg_...", "account_id": "...", "scope": "work", "subject": "...", "sender": "...", "score": 3, "reasons": ["..."]}],
  "skipped": {"archive_sources": 0, "non_inbox": 0}
}
```

Details:

* `count` is the total in the category; `samples` holds up to `sample_size` (5) subjects, newest first, each
  cut at 120 characters; `message_ids` lists **all** index message ids in that category for that account (not
  just the samples). Counts per category sum to `inbox_total`.
* `spam_filtered` covers every row seen by the plan across all mailboxes of the account (including Junk and Sent),
  for the whole index regardless of age: `total = spam + bulk` (own sent mail and review are reported separately,
  not in `total`); `by_reason` counts each reason string once per message and keeps the top 15. It is **not** the
  same row set as the window's `mail_filtered` counts (1.8, 4.3), and the two numbers are not expected to match.
* `review_queue` is `spam_eval.review_queue(...)` over the INBOX rows, capped at 100 entries, highest score first.
* `skipped` counts what the plan could not consider: `archive_sources` (PST/archive observations, which cannot be
  moved) and `non_inbox` (live rows in other mailboxes, used for context and counts only).
* The stored plan (on disk) additionally has `sources`: `{account_id: {message_id: {"source_id", "mailbox",
  "uidvalidity", "uid", "rfc_message_id"}}}`, which `organize_apply` needs. A plan is saved by the caller (CLI or
  window action) at `<window_home>/mail-plans/<plan_id>.json` with the atomic writer. Plans older than **24 hours**
  are refused by apply ("plan is stale, run Organize inbox again"). The plan contains subjects and sender
  addresses only, never bodies and never credentials.

## 3. Applying the plan: `imap_write.py` and `organize_apply.py`

### 3.1 The write boundary: `imap_write.ImapMover`

`ReadOnlyIMAP` (sync) is unchanged and still refuses every write. Writes use a separate wrapper,
`ImapMover` in `src/agent_os/mail/imap_write.py`, created only through
`imap_write.connect_write(account, *, factory=None) -> ImapMover`, which raises `AccountError` unless
`account.allow_organize` is true (checked at connect time, not only at plan time). `organize_apply` is the only
caller. Allowed IMAP commands, and nothing else:

* `LOGIN`, `CAPABILITY`, `LIST`, `LOGOUT`;
* `CREATE` (a missing target folder, one level at a time: `Agent OS`, then `Agent OS/Receipts`; "already
  exists" is not an error) and `SUBSCRIBE` (so clients show the folder);
* `SELECT` read-write on the source folder, and `EXAMINE` for read-only checks;
* `UID SEARCH` (by `HEADER Message-ID` for verification and undo);
* `UID FETCH` with `BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)]`, `FLAGS`, `UID` only (the same `PEEK` rule as sync);
* `UID MOVE` (RFC 6851) when `CAPABILITY` lists `MOVE`;
* otherwise `UID COPY`, followed by `UID STORE <uid> +FLAGS.SILENT ($AgentOSOrganized)` on the source copy, and
  `-FLAGS.SILENT ($AgentOSOrganized)` for undo. These are the only `STORE` forms allowed.

Always refused with `WriteViolation`: `EXPUNGE`, `UID EXPUNGE`, `CLOSE` (it expunges), `DELETE`, `RENAME`,
`APPEND`, any `STORE` that mentions `\Deleted` or anything other than the single keyword above, and any other
command. The wrapper has a test for each refusal (fake client records calls; none of the refused commands may
reach it).

`ImapMover` implements the `Mover` protocol (3.3) on top of those commands. Folder names: `LIST` gives the
hierarchy delimiter and whether existing folders use an `INBOX.` namespace prefix (`INBOX.Agent OS.Receipts`);
`imap_write.resolve_folder(logical_name, delimiter, prefix)` builds the real name. Mailbox names are quoted with
the existing `imap._quote` rule.

Never deleting and never expunging has two consequences the operator should know:

* `UID MOVE` removes only the moved message from the source folder (that is what a move is) and is verified
  afterwards (3.4). It does not expunge anything else.
* The copy fallback leaves the message in **both** folders: the source copy carries the `$AgentOSOrganized`
  keyword so the operator can see which INBOX copies were already filed and remove them in their own mail client.
  If the folder does not allow custom keywords (`PERMANENTFLAGS` lacks `\*` and the keyword), the fallback is
  refused for that account with `error: "server supports neither MOVE nor keyword flags"` and nothing is copied.

### 3.2 `allow_organize` (accounts)

* `Account.allow_organize: bool = False`, persisted in `accounts.json` under the key `allow_organize` (`False` is
  written explicitly). Old files without the key load as `False`. This is the field the `account-allow-moves`
  task adds; it is not named `allow_moves`.
* `accounts.set_allow_organize(account_id, value, path=None) -> Account` is the **only** way to change it.
  `update_account` keeps rejecting it ("read-only mode and identity are fixed" stays true for everything else),
  so no generic edit path can flip write access.
* `Account.public()` adds `"allow_organize": bool`. `"read_only": true` stays and means "the sync path never
  writes". `Account.read_only` (the property) is unchanged.
* The window action `mail.organize.allow` and `agent-os mail account organize <id> --on|--off` are the two ways
  to change it. It is not reachable through the mail MCP tools: agents cannot enable writes or run organize.
  MCP mail tools stay read-only.
* Credentials are the existing keyring or environment secret; nothing in the plan, journal, audit or result
  contains a secret.

### 3.3 The `Mover` protocol (`organize_apply.Mover`)

`apply_plan` and `undo` talk to a mailbox only through this protocol, so tests can pass a fake `Mover` and the
apply logic never sees raw IMAP:

```python
class Mover(Protocol):
    def capabilities(self) -> set[str]: ...                            # upper-case, e.g. {"MOVE", "UIDPLUS"}
    def ensure_folder(self, logical_name: str) -> str: ...            # LIST, CREATE + SUBSCRIBE if missing; returns real name
    def select(self, mailbox: str) -> str: ...                         # SELECT read-write; returns UIDVALIDITY
    def message_ids(self, uids: list[str]) -> dict[str, str]: ...      # uid -> Message-ID header (BODY.PEEK)
    def move(self, uids: list[str], target: str) -> dict[str, str | None]: ...      # UID MOVE; uid -> target uid
    def copy_flag(self, uids: list[str], target: str) -> dict[str, str | None]: ... # UID COPY + keyword
    def unflag(self, uids: list[str]) -> None: ...                     # -FLAGS.SILENT ($AgentOSOrganized)
    def find(self, mailbox: str, rfc_message_id: str) -> str | None: ...           # UID SEARCH HEADER Message-ID
    def close(self) -> None: ...                                       # LOGOUT only, never CLOSE
```

`apply_plan(..., connect=None)` and `undo(..., connect=None)` take `connect(account) -> Mover`; the default is
`imap_write.connect_write`.

### 3.4 `apply_plan`

```python
def apply_plan(plan: dict, category: str, *, accounts: list[str] | None = None, dry_run: bool = True,
               now: datetime | None = None, connect=None, journal_dir: Path | None = None,
               max_moves: int = 500) -> dict: ...
```

`dry_run=True` is the default and performs **no network access at all**: it reads only the plan and the account
settings, and never calls `connect`. Validation that raises before anything moves: unknown category; category
without a target folder (`action_needed`, `waiting_on_others`); a plan older than 24 hours.

Per account, in order:

1. Skip with `skipped_not_enabled` when `allow_organize` is false (dry-run reports it the same way).
2. `connect(account)`, `ensure_folder(target)`, `select(source mailbox)`.
3. For each message (batched in UID sets of at most 100): check `UIDVALIDITY` equals the plan's (mismatch:
   skip all of that mailbox's messages with `uidvalidity changed; run Organize inbox again`); check the UID
   still exists and its `Message-ID` header equals `rfc_message_id` (otherwise skip that message with
   `message changed or gone`).
4. Write a journal line with `status: "pending"` **before** the IMAP command, then the command (`move` when
   `MOVE` is in `capabilities()`, else `copy_flag`), then a final journal line (`moved` / `failed`) with the
   resulting target UID (from the `COPYUID`/`MOVE` response when the server provides it, else `find` in the
   target folder, else `null`).
5. After a move, verify the message is present in the target with `find`; if not, the journal line says
   `unverified` and the account result reports it (it is never retried automatically).
6. Call `Store.mark_source_moved(source_id)` for each moved message so the next plan does not count it again;
   the next sync then confirms the UID is gone from the INBOX.

Result:

```json
{"dry_run": true, "plan_id": "plan_...", "category": "receipts_finance", "journal_id": null,
 "accounts": {"work-earthlink": {"status": "dry_run|moved|skipped_not_enabled|error", "method": "move|copy_flag|null",
              "target_folder": "Agent OS/Receipts", "would_move": 14, "moved": 0, "failed": 0, "remaining": 0,
              "samples": ["..."], "skipped": [{"message_id": "msg_...", "reason": "..."}], "error": null}}}
```

`journal_id` is `null` for a dry-run and `org_<UTC yyyymmddThhmmss>_<4 hex>` for an apply. A dry-run and the
Confirm of the same call report the same `would_move` / `moved` counts when nothing changed on the server.
Failures are per message and per account: one account's connection error never stops the other accounts, and a
failed message is never retried silently.

### 3.5 Journal and undo

Journal: append-only JSON lines at `<scope dir>/organize-journal.jsonl`
(`.agent-local/mail/<scope>/`, gitignored, one journal per scope so the scopes stay separate). One move = one
`pending` line and one final line with the same `seq`:

```json
{"journal_id": "org_20261002T120500_ab12", "seq": 1, "ts": "2026-10-02T12:05:00+00:00", "status": "pending|moved|failed|unverified|undone",
 "plan_id": "plan_...", "category": "receipts_finance", "account_id": "work-earthlink", "scope": "work",
 "message_id": "msg_...", "rfc_message_id": "abc@x",
 "from": {"mailbox": "INBOX", "uidvalidity": "123", "uid": "41"},
 "to": {"mailbox": "Agent OS/Receipts", "uidvalidity": "456", "uid": "7"},
 "method": "move|copy_flag", "error": null,
 "undo": {"command": "agent-os mail organize-undo --journal org_20261002T120500_ab12 --seq 1",
          "steps": ["UID MOVE 7 from Agent OS/Receipts back to INBOX"]}}
```

Every `moved` line carries `undo.command` (a runnable CLI line) and `undo.steps` (plain words). A `pending` line
without a final line (a crash between command and journal) stays as written in this run: `undo` skips that
`seq` with reason `no final journal line`. **(deferred, D4)** A later run reconciles such lines at the start of
the next apply or undo by searching both folders for the `Message-ID` and writing the real final line.

`undo(journal_id, *, seq=None, dry_run=True, connect=None, journal_dir=None) -> dict` reverses one move or a
whole journal: it finds the message in the `to` folder (by `to.uid` when `to.uidvalidity` is unchanged, else by
`find`), then moves it back to `from.mailbox`. For `copy_flag` moves it calls `unflag` on the INBOX copy and
reports that the copy in the target folder remains (a delete would be needed to remove it, and Agent OS never
deletes). Undo is itself journaled (`status: "undone"`, with `undone_of: <seq>`), is dry-run by default, never
creates a second undo for an undo, and is idempotent (a message already back in its source folder is skipped).
In this run undo is run through `agent-os mail organize-undo` (the window action `mail.organize.undo` is
deferred, D6); `Store.mark_source_present` restores the index state.

### 3.6 CLI (`src/agent_os/mail/cli.py`)

Flat, hyphenated subcommands like the existing `import-pst` and `split-scopes`; everything that could move mail is
dry-run unless `--confirm`:

```
agent-os mail organize-plan [--scope work|personal] [--json]          # builds, saves and prints the plan
agent-os mail organize-apply --plan <id> --category <c> [--account <id>] [--confirm]
agent-os mail organize-undo --journal <id> [--seq N] [--confirm]
agent-os mail account organize <account-id> --on|--off              # sets allow_organize
```

Deferred (0.3): `agent-os mail organize-journal [--scope work|personal]` (D5) and
`agent-os mail headers-backfill [--account <id>]` (D1).

### 3.7 Safety invariants (each needs a test)

1. No code path issues `EXPUNGE`, `UID EXPUNGE`, `CLOSE`, `DELETE`, `RENAME`, `APPEND`, or a `STORE` of
   `\Deleted`. Enforced by `ImapMover` and asserted with a recording fake client.
2. With `allow_organize` false, `connect_write` raises and no apply path opens a write connection (fake
   `connect` is never called).
3. The default call (`dry_run=True`) opens no connection at all.
4. Every successful move has a final journal line with `undo.command`; `pending` precedes the IMAP command.
5. A mismatched `UIDVALIDITY` or `Message-ID` moves nothing for that message.
6. `ReadOnlyIMAP` and the sync path are unchanged: the existing read-only tests still pass untouched.
7. No credential, app password or secret appears in the plan, the journal, the audit line, or any result.
8. Work and personal scopes stay separate: plans, known-correspondent sets and journals are per scope; the only
   place both appear together is the operator's own window.
9. Spam and bulk are filtered from commitments only; they are counted in the `mail_filtered` item (window row
   set) and in the plan's `spam_filtered` (whole index). Nothing is deleted, and the spam category is moved to
   `Agent OS/Spam`, not to Trash.
10. A verdict-`review` row is always `action_needed` with `review = true` and is never moved, at any age.
11. An apply Confirm moves only messages of the `plan_id` that was previewed; a missing, different or stale plan
    moves nothing (4.2).
12. A verdict-`human` row that asks is never moved, whatever its subject (rule 2 accepts only `bulk`, 2.2).

## 4. Window integration: `src/agent_os/executive/window/actions_mail_organize.py`

New items and actions are registered through the existing registry. `builtin.default_registry` adds
`registry.register_provider("mail_cleanup", actions_mail_organize.mail_cleanup_items)` and
`actions_mail_organize.register(registry.REGISTRY)`. Providers stay cheap and never touch the network: they read
the local index and the saved plan. Building a plan is an explicit action.

### 4.1 Items

| `kind` | `id` | `tab` | Source | Shows |
|---|---|---|---|---|
| `mail_thread` | `mail:<thread>` | work / personal | `providers_mail.mail_items` | unchanged, but only classifier verdict `human` |
| `mail_filtered` | `mail-filtered:<tab>` | work / personal | `providers_mail.mail_items` | title `N filtered out of commitments (S spam, B bulk)`, `why` lists the top 3 reasons and the review count; `context` = the keys of `spam_filtered` (`total`, `spam`, `bulk`, `own_sent`, `review`, `by_reason`, `by_account`) counted over the window row set of 1.8, not the plan's |
| `mail_review` | `mail-review:<message id>` | work / personal | `providers_mail.mail_items` | borderline mail: `title` = subject, `why` = `borderline (score N): <reasons>`; `context` = `message_id`, `sender`, `subject`, `score`, `reasons` |
| `mail_cleanup` | `mail-cleanup:<tab>` | work / personal | `actions_mail_organize.mail_cleanup_items` | the mail-cleanup group: with a saved plan, `title` = `Mail cleanup: N messages can be organized`, `why` = per-category counts and `whole index: S spam, B bulk` (4.3); `context` = `plan_summary` for that scope (including its `plan_id`) plus `accounts: [{account_id, email, allow_organize}]`. Without a plan: `title` = `Organize inbox`, `why` = `No plan yet. Run Organize inbox to review it.` Always present when the scope has at least one configured account |

`mail_cleanup_items(window_home=None, accounts_path=None, now=None) -> list[dict]` returns one `mail_cleanup`
item per scope with a configured account. For tab `work` it contains only work-scope accounts, for `personal`
only personal-scope accounts. It reads the newest plan file for the scope; it never rebuilds one.

### 4.2 Actions

All ids are namespaced `mail.*` and registered by `actions_mail_organize.register`; params are validated like the
existing actions. "Consequential" actions go through `Registry.invoke`'s preview-then-`/api/confirm` path, so the
preview **is** the dry-run and Confirm performs. Every consequential action is audited by the existing `audit.jsonl`.

| Action id | Label | Applies to | Consequential | Params | What it does |
|---|---|---|---|---|---|
| `mail.organize` | `Organize inbox` | `mail_cleanup` | no | `scope` (optional) | Builds a plan (`plan_from_index`), saves it, returns `plan_summary`. Changes no mail and needs no network; this is the dry-run view. |
| `mail.organize.apply.<category>` | `Organize: <category label>` | `mail_cleanup` | **yes** | `plan_id` (**required**, no default), `accounts` (optional list of account ids) | One action per **movable** category: `receipts_finance`, `newsletters_promotions`, `notifications`, `hr_applicants`, `personal`, `spam`, `archive_old` (seven actions; `action_needed` and `waiting_on_others` have none). Preview (`confirm=False`) = `apply_plan(..., dry_run=True)`: per account, how many messages would move, to which folder, with the samples, plus accounts that are skipped because `allow_organize` is off. Confirm performs the moves. This is the **per-category Confirm button**. |
| `mail.organize.allow` | `Allow organizing` | `mail_cleanup` | **yes** | `account_id`, `allow` (bool) | Sets `allow_organize` on one account (`accounts.set_allow_organize`). Preview text states: "lets Agent OS move (never delete) mail in <email>'s INBOX; syncing stays read-only". |

Deferred actions (0.3), **not registered in this run**: `mail.organize.undo` (D6; `journal_id`, preview lists
what would move back, Confirm runs `undo`), `mail.filtered.show` (D3; `kind`, `limit` <= 50, returns subject,
sender, date and reasons of filtered messages), `mail.review.human` and `mail.review.bulk` (D2; record the
sender in `mail-review.json`, section 1.6).

Confirm rules for the apply actions:

* **The previewed plan is the confirmed plan.** `plan_id` is required: a call without it returns an error
  (`plan_id is required; run Organize inbox and pick the plan shown`) and no preview or confirm token is
  created. The preview refuses a `plan_id` that differs from `item.context.plan_id` (the plan the operator is
  looking at), and returns the `plan_id` it previewed as `preview.plan_id`. `Registry.invoke` stores the params
  with the confirm token, and `Registry.confirm` hands the handler exactly those params, so Confirm loads exactly
  `<window_home>/mail-plans/<plan_id>.json`. Confirm refuses, moving nothing, when that file is missing, stale
  (3.4), or its `plan_id` differs from the requested one. Apply never falls back to the newest plan; a newer plan
  needs a new preview.
* Per-category Confirm is per action call: confirming `receipts_finance` never moves anything in another category.
* A Confirm moves at most **500 messages per account**; the result reports `remaining` and the operator confirms again.
* The plan is re-validated at Confirm time (section 3.4); stale or changed messages are skipped, never forced.
* `allow_organize` off for an account means that account is skipped with `skipped_not_enabled`, in preview and at Confirm.

### 4.3 Ordering and counts

`mail_filtered` and `mail_cleanup` items sort after `mail_thread` items and carry `age_days: null`.

The two filtered counts measure different row sets and are labelled so nobody expects them to match:

* `mail_filtered` (commitments): the latest message of each thread in that tab's window (`days`), as defined in
  1.8. Its title is `N filtered out of commitments (S spam, B bulk)` with `N = S + B`, and its counts reconcile
  with the window: every thread the provider considered has exactly one verdict, so
  `considered = human + review + spam + bulk + own_sent`, where `human` threads are the commitment candidates
  (still subject to the existing `_score` gate) and `review` threads are the review queue (up to 20 shown as items).
* `mail_cleanup` (plan): `spam_filtered` of the saved plan, every row of the whole index for that scope (2.3).
  Its `why` labels it `whole index: S spam, B bulk`.

The window never claims either number equals the other.

## 5. Order of work and acceptance

Each step below is the **complete binding scope** of the task that implements it; nothing in section 0.3 is part
of any step. Where a task description in the run's task graph says something different, the step below wins.
Overrides of task descriptions, binding for every step:

* The per-account switch is `allow_organize` (the `account-allow-moves` task delivers it under that name; no
  `allow_moves` field or alias).
* No Outlook and no COM: moves are IMAP only (`imap_write.ImapMover`); there is no backend selection.
* The classifier result is `{'verdict', 'reasons', 'score'}` from `classify`; the deferred `classify_with_overrides`
  is not called anywhere in this run.
* The window apply actions take a **required** `plan_id` (4.2).
* `hr_applicants` (rule 2) accepts verdict `bulk` only (2.2).

Steps:

1. Foundations: schema v3 (four header columns, captured at sync), `Store.iter_rows`, `mail.iter_rows`,
   `Store.mark_source_moved` / `mark_source_present` (section 0.2), and `Account.allow_organize` with
   `set_allow_organize` (3.2): tests in `test_mail.py`, `test_mail_accounts.py`. Not in scope: D1.
2. Section 1: `spam.py` (`classify`, `known_correspondents`) and `spam_eval.py` (`SYNTHETIC`, `evaluate`,
   `review_queue` without `overrides`) with the worked examples of 1.5 and the targets in 1.7: `test_mail_spam.py`.
   Not in scope: D2.
3. Section 2: `organize.py` (`categorize`, `build_plan`, `plan_from_index`, `plan_summary`, `TARGET_FOLDERS`):
   `test_mail_organize.py` with one test per rule, review rows never moved at any age, human rows that ask never
   moved (including an applicant subject), the age overlay, per-account counts that sum to `inbox_total`,
   `spam_filtered` totals, both scopes, and invariants 10 and 12 of 3.7.
4. Section 3: `imap_write.py`, `organize_apply.py` (`apply_plan`, `undo`, journal) and the CLI commands of 3.6:
   `test_mail_organize_apply.py` with a `FakeIMAP` client under `ImapMover` and a fake `Mover`, covering MOVE, the
   copy fallback, unsupported-keyword refusal, folder creation, UIDVALIDITY change, undo, undo skipping an orphaned
   `pending` line, and invariants 1-8 of 3.7. Not in scope: D4, D5.
5. Section 4: `providers_mail.py` (commitments use `classify`; `mail_filtered` and `mail_review` items over the
   window row set), `actions_mail_organize.py` (`mail_cleanup_items`; actions `mail.organize`,
   `mail.organize.apply.<category>` x7, `mail.organize.allow`), `builtin.py`: tests in
   `test_executive_window_provider_mail.py` (existing cases keep passing), `test_executive_window_registry.py`
   and `test_executive_window_builtin.py` style tests for the new actions (preview does not move; Confirm moves;
   missing or mismatched `plan_id` refused) and invariants 9 and 11 of 3.7. Not in scope: D2, D3, D6.
6. Update `docs/integrations/mail.md` (the read-only statements become "sync is read-only; organizing needs
   `allow_organize`") and fill in "Measured results" below.

Each step runs `python -m unittest discover -s tests -v` and `python agent.py validate` before it is called done.

## Measured results

(To be filled in by the classifier task with the numbers printed by `tests/test_mail_spam.py` on
`spam_eval.evaluate()`: `n`, `precision`, `recall`, `human_protected`, `review_rate`.)
