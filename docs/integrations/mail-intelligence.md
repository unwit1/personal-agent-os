# Mail intelligence: spam filtering and inbox organization (contract)

Status: **binding contract** for the implementation tasks of the "Executive mail intelligence" run
(operator spec 2026-10-02). This file describes code that does not exist yet. Later tasks implement
exactly what is written here; a task that needs to deviate changes this file first, in the same
change, and says why. Where this file and an older doc disagree about this feature (for example the
"read-only" wording in `docs/integrations/mail.md`), this file wins, and the task that lands the code
updates the older doc.

Operator rules that shape everything below:

* **No Outlook, no COM.** Moves happen over IMAP only (`UID MOVE`, or `UID COPY` plus a flag when
  the server has no MOVE), per account.
* **Never delete, never expunge.** Only reversible moves. Every move is journaled with an undo command.
* **Dry-run is the default.** Applying needs the operator's Confirm, one Confirm per category.
* Accounts stay read-only for sync. A new per-account setting `allow_organize` (default **off**) is the
  only thing that lets Agent OS write to an account's mailbox, and the operator turns it on from the window.
* **Nothing disappears silently.** Everything filtered out of the commitments is counted and visible, with its reason.

Goals the contract serves: "filter out the spam from the commitments" and "organize my entire email inbox".

## 0. Module map (who owns what)

| Path | New / changed | Purpose |
|---|---|---|
| `src/agent_os/mail/spam.py` | new | Deterministic spam/bulk classifier, `known_correspondents`, `evaluate` (precision/recall), operator overrides |
| `src/agent_os/mail/message.py`, `store.py` | changed | Capture four headers (schema v3), `Store.iter_rows`, `Store.set_headers`, `Store.mark_source_moved` |
| `src/agent_os/mail/imap.py` | changed | `ReadOnlyIMAP.fetch_headers` (header backfill, still read-only) |
| `src/agent_os/mail/organize.py` | new | Categorizer, `CATEGORIES`, `build_plan`, `plan_summary`; pure, no I/O except `plan_from_index` |
| `src/agent_os/mail/imap_move.py` | new | `MoveIMAP`: a second, separate IMAP wrapper whose allowed command set is exactly the move set |
| `src/agent_os/mail/organize_apply.py` | new | `apply_plan`, `undo`, journal; the only caller of `MoveIMAP` |
| `src/agent_os/mail/accounts.py` | changed | `Account.allow_organize`, `set_allow_organize` |
| `src/agent_os/mail/cli.py` | changed | `agent-os mail organize plan|apply|undo|journal`, `agent-os mail account organize` |
| `src/agent_os/executive/window/providers_mail.py` | changed | Commitments use the classifier; filtered-summary and review items |
| `src/agent_os/executive/window/providers_mail_cleanup.py` | new | `mail_cleanup` item from the latest saved plan |
| `src/agent_os/executive/window/actions_mail.py` | new | Window actions (section 4); registered in `builtin.py` |
| tests | new | `tests/test_mail_spam.py`, `tests/test_mail_organize.py`, `tests/test_mail_organize_apply.py`, plus additions to `tests/test_mail.py`, `tests/test_mail_accounts.py`, `tests/test_executive_window_provider_mail.py` |

Test rules for every task: synthetic data and fakes only (a `FakeIMAP` client object, temporary
directories, injected `search`/`now`); no real mail, Outlook, Dashboard database or network. Every test
file starts with `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))`.

## 1. Data the classifier needs (schema v3)

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
  on the remaining signals (degraded mode). `agent-os mail headers-backfill [--account ID]` fills them without
  re-downloading bodies, through the new read-only method `ReadOnlyIMAP.fetch_headers(uids)` that issues
  `UID FETCH ... (BODY.PEEK[HEADER.FIELDS (LIST-UNSUBSCRIBE LIST-ID PRECEDENCE AUTO-SUBMITTED)])` and `Store.set_headers`.
  `PEEK` keeps it inside the existing read-only guard (`FORBIDDEN_FETCH` does not match `BODY.PEEK[`).
  PST/archive rows have no headers and stay NULL.
* `Store.iter_rows(*, accounts=None, mailboxes=None, after=None, before=None, senders=None, live_only=True)`
  is a generator over the whole index with no `MAX_LIMIT` cap (search is capped at 50). It yields one **row** per
  live IMAP source (state `present`; archive sources are skipped when `live_only`), shaped as in section 3.1.
  `mail.iter_rows(scope=None, db_path=None, **filters)` is the module-level wrapper (same `_target` rules as `mail.search`).
* `Store.mark_source_moved(source_id)` sets the source's `state` to `missing` (the existing state the sync already
  uses for UIDs that left a mailbox); the logical message is kept. `Store.mark_source_present(source_id)` reverses it for undo.

Folders to sync: spam-folder detection and "known correspondent" detection need the Junk and Sent folders in
the account's `folders` list (default is only `INBOX`). Without them the signals are simply absent: no folder
verdicts, and every sender counts as a first contact. This is a documented degraded mode, not an error.

## 2. Spam/bulk classifier: `src/agent_os/mail/spam.py`

### 2.1 API

```python
VERDICTS = ("human", "bulk", "spam", "review")
HUMAN_MAX = 2      # score <= 2            -> human
REVIEW_MIN = 3     # 3 <= score <= 5       -> review (borderline)
BULK_MIN = 6       # score >= 6            -> bulk (or spam, see 2.4)

def classify(message: dict, *, own: set[str], known: set[str]) -> dict:
    """-> {'verdict': 'human'|'bulk'|'spam'|'review', 'reasons': [str], 'score': int}"""

def known_correspondents(rows, own: set[str]) -> set[str]: ...

def classify_with_overrides(message, *, own, known, overrides: dict) -> dict: ...   # 2.6
def evaluate(cases, *, own, known) -> dict: ...                                       # 2.7
```

`message` keys: `sender`, `recipients`, `subject`, `snippet`, `mailbox`, `list_unsubscribe`, `list_id`,
`precedence`, `auto_submitted`. Any key may be missing or `None`; extra keys are ignored (so an index row or
search row is passed as is). `sender` may be `Name <addr>`; the address is parsed with
`email.utils.parseaddr` and lower-cased. `recipients` is the comma-separated string the index stores (a
list/tuple/set of strings is also accepted). `own` and `known` are sets of lower-case addresses; `classify`
never mutates them and never raises on missing or odd values (it raises `TypeError` only when `message` is not a dict).
A header counts as **present** when its value is not `None` and `str(value).strip() != ""`.

Result: `verdict` as below; `reasons` is a non-empty list of short human strings, in signal order (table in 2.3),
the verdict-level reason (2.4) last; `score` is an `int`, never negative. Same input gives identical output.

`known_correspondents(rows, own)` returns the lower-case addresses that appear in `recipients` (and in `cc`
when the row carries it) of rows whose sender address is in `own`, minus `own` itself. It is the only way the
set `known` is built ("the operator has replied before"; being merely CC'd on someone's mail does not count).
Rows come from `mail.iter_rows(scope, senders=own)`, per scope, so the work and personal indexes stay separate.

### 2.2 Decision order

1. **Own sent mail**: sender address in `own` -> verdict `bulk`, reasons `["own sent mail"]`, score `0`.
   "Bulk" here means "excluded from commitments"; own mail is **never** `spam` and never reaches the spam category.
2. **Server spam folder**: `mailbox` matches (case-insensitive, after splitting on `/`, `.` and `\` and
   taking the last segment, trimmed) one of `junk`, `junk e-mail`, `junk email`, `spam`, `bulk mail`
   -> verdict `spam`, reasons `["in server spam folder (<mailbox>)"]`, score `100`. `INBOX.Junk` and
   `[Gmail]/Spam` match; `Junk Notes` does not. `known` does not override this.
3. Otherwise add up the signals in 2.3, clamp at 0, then apply the thresholds and the spam rule (2.4).

### 2.3 Signals and weights

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
by later tasks as long as the labeled set in 2.7 still meets its targets):

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

### 2.4 Verdict thresholds and the spam rule

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
correspondent relaying list mail (5 - 2 = 3).

### 2.5 Worked examples (the test task must include these verbatim)

`own = {"me@example.com"}`, `known = {"pat@corp.com"}`.

| Message | Score | Verdict | Reasons |
|---|---|---|---|
| `Pat <pat@corp.com>`, "Lunch?" | 0 (-4 clamped) | human | `known correspondent (you replied before)` |
| `Lee <lee@new.org>`, "Lunch?" | 1 | human | `first contact (you never replied)` |
| `noreply@shop.com`, "Your receipt" | 7 (6 + 1) | bulk | `automated sender address`, `first contact (you never replied)` |
| `news@brand.com`, "Spring SALE: 30% off", `List-Unsubscribe` set | 12 (2 + 5 + 4 + 1) | bulk | has a list header, so not spam |
| `deals@promo-mart.biz`, "Limited time deal: 50% off", no headers | 7 (2 + 4 + 1) | spam | three markers, no list headers, unknown sender |
| `Lee <lee@new.org>`, "Webinar invite?" | 3 (2 + 1) | review | `promotional subject (webinar)`, first contact |
| `Pat <pat@corp.com>`, "Webinar notes" | 0 (2 - 4 clamped) | human | |
| `info@smallbiz.example`, "Your quote" | 3 (2 + 1) | review | `generic sender address (info@)`, first contact |
| `pat@corp.com`, `Auto-Submitted: auto-replied` | 8 (no discount) | bulk | `auto-generated (Auto-Submitted)` |
| `sam@x.org` (known), `List-Id` set | 3 (5 - 2) | review | `mailing list (List-Id)`, known correspondent |
| sender `me@example.com` | 0 | bulk | `own sent mail` |
| any sender, `mailbox="Junk E-mail"` | 100 | spam | `in server spam folder (Junk E-mail)` |

### 2.6 Operator decisions on the review queue

The review queue is the set of `review` verdicts. The operator answers per sender: "this is a person" or
"this is bulk". Decisions persist in `<window_home>/mail-review.json`
(`{"human": {"addr": "<iso>"}, "bulk": {"addr": "<iso>"}}`, written with the same atomic temp-file-and-replace
helper as `confirm._write_json`). `classify_with_overrides(message, *, own, known, overrides)` calls `classify`
and then applies, in this precedence: own sent mail (unchanged) > override > the computed result. A `human`
override returns verdict `human`, score `0`, reasons `["operator marked sender as human"]`; a `bulk` override
returns `bulk`, reasons `["operator marked sender as bulk"]`. `classify` itself stays pure and override-free.

### 2.7 Precision and recall: `evaluate`

`evaluate(cases, *, own, known)` takes `cases = [(message, label), ...]` with `label` in `human`, `bulk`, `spam`
(gold) and returns:

```json
{"n": 0, "precision": 0.0, "recall": 0.0, "human_protected": 0.0, "review_rate": 0.0,
 "false_positives": [], "missed": [], "confusion": {"human": {"human": 0, "bulk": 0, "spam": 0, "review": 0}, "bulk": {}, "spam": {}}}
```

* The positive class is "not a person" (gold `bulk` or `spam`). A prediction is positive when the verdict is
  `bulk` or `spam`.
* `precision = TP / (TP + FP)`: of the mail filtered out, how much really was not a person.
* `recall = TP / gold_positives`: a `review` verdict counts as **not filtered** (a miss), because the operator
  still has to look at it.
* `human_protected = 1 - (gold human predicted bulk or spam) / gold_human`: the share of real person mail that
  stays visible (`human` or `review`).
* `review_rate = review verdicts / n`.
* `false_positives` and `missed` list `subject` and `reasons` for inspection. An empty denominator gives `1.0`.

The synthetic labeled set (`tests/test_mail_spam.py`) has at least 60 cases: every signal in 2.3 exercised at
least twice, every worked example in 2.5, at least 15 human cases (including a person writing "sale of the
house", a known colleague on a list, a first-contact recruiter), at least 15 bulk and 10 spam cases. **Acceptance
targets** asserted by the test: `precision >= 0.95`, `recall >= 0.85`, `human_protected == 1.0` for gold
human cases that are known correspondents, **no gold-human case ever gets verdict `spam`**, and
`review_rate <= 0.15`. The test prints the metrics, and the implementer pastes the measured numbers into the
section "Measured results" at the bottom of this file.

### 2.8 Use in the window's commitments

`providers_mail.mail_items` keeps its signature (`db_path`, `own_addresses`, `days`, `limit`, `search`, `now`)
and gains `known: set[str] | None = None` and `overrides: dict | None = None`.

* `known=None` means: compute per scope with `known_correspondents(mail.iter_rows(scope, senders=own), own)`
  when the default search is used, or from the rows the injected `search` returned (so tests need no index).
* For each thread's latest message, call `classify_with_overrides`. Only verdict `human` becomes a
  `mail_thread` item. The old `AUTOMATED` regex and the "sender is own" check are removed (the classifier
  covers both); the third point of `_score` ("not automated") becomes "verdict is human" and the `score >= 2`
  gate stays as it is.
* Filtered mail is never silently dropped. The provider also returns, per tab:
  * one `mail_filtered` summary item (section 4.1) with counts of `spam`, `bulk`, `own_sent`, `review` and
    the top reasons for the same window (`days`);
  * up to 20 `mail_review` items for the borderline band, newest first.
* Verdict `review` threads are **not** commitments until the operator answers; they live in the review queue.

## 3. Inbox categorizer: `src/agent_os/mail/organize.py`

### 3.1 Row shape (input)

One dict per live IMAP source in the INBOX of every configured account, from both scopes
(`mail.iter_rows`). Other mailboxes (Sent, Junk, folders the operator already made) are used as context only,
they are never moved.

```
id (index message id, "msg_..."), thread_id, message_id (RFC), subject, sender, recipients, date (ISO UTC),
snippet, scope ("work"|"personal"), account_id, provider, mailbox, uidvalidity, uid, source_id, flags,
list_unsubscribe, list_id, precedence, auto_submitted
```

### 3.2 Categories, rule order and target folders

```python
CATEGORIES = ("action_needed", "waiting_on_others", "receipts_finance", "newsletters_promotions",
              "notifications", "hr_applicants", "personal", "spam", "archive_old")

DEFAULT_FOLDERS = {
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
entry; an override of `None` for a movable category means "report it but do not move it".

`categorize(row, *, own, known, now, thread_last_own=False) -> {"category", "reasons": [str], "verdict", "review": bool}`
evaluates the first matching rule below (it calls `spam.classify` with the row; `known` is the set for the
row's scope). `thread_last_own` is true when the newest message of the row's thread (any folder of the same
scope index) is own sent mail; `build_plan` computes it by grouping rows on `thread_id`.

| Order | Category | Rule |
|---|---|---|
| 0 | (excluded) | Own sent mail (verdict `bulk` with reason `own sent mail`) is never categorized or moved; it is counted in `spam_filtered.own_sent` |
| 1 | `spam` | verdict `spam` (a row already in a server spam folder gets this category but `move = false`: it is already filed) |
| 2 | `hr_applicants` | scope `work`, verdict `human` or `bulk`, and the subject matches `applicant|application|apply|resume|r[ée]sum[ée]|cv\b|candidate|interview|hiring|recruit|job posting|offer letter|onboarding` or the sender domain is a job board (`indeed.com`, `ziprecruiter.com`, `greenhouse.io`, `lever.co`, `workable.com`, `applytojob.com`, `jobvite.com`, `smartrecruiters.com`) |
| 3 | `receipts_finance` | verdict `bulk` and the subject matches `receipt|invoice|order confirmation|your order|payment|statement|billing|refund|transaction|tax|paid` or the sender local part is `billing|invoice|invoices|receipts?|payments?|orders?` or the domain is `paypal.com`, `stripe.com`, `squareup.com`, `venmo.com` |
| 4 | `notifications` | verdict `bulk`, the sender matches the strong sender pattern or `auto_submitted` is present, and no promotional marker matched the subject |
| 5 | `newsletters_promotions` | verdict `bulk` (everything else that is bulk: list headers, marketing senders, promotional subjects) |
| 6 | `waiting_on_others` | verdict `human` or `review` and `thread_last_own` (the operator spoke last) |
| 7 | `action_needed` | verdict `human` or `review`, and the thread's newest message is not own, and the row **asks**: `?` in subject or snippet, or an `own` address is in `recipients` (directly addressed). Rows with verdict `review` land here with `review = true` and are never moved |
| 8 | `personal` | scope `personal`, verdict `human`, and the row does not ask (no `?`, not directly addressed: a CC or FYI) |
| 9 | `archive_old` | age (against `now`) over **365 days** for any row that reached this point |
| 10 | `action_needed` (default) | anything left, for safety: it stays in the INBOX |

Age overlay: after rules 1-8, a row whose category is `notifications`, `newsletters_promotions`, `personal` or
`waiting_on_others` and whose age is over 365 days becomes `archive_old`. `spam`, `hr_applicants` and
`receipts_finance` keep their category at any age (records stay findable), and **`action_needed` is never
archived**, which is the whole meaning of "older than 365 days and not action_needed". A row whose date is
missing or unparseable is treated as age 0.

Each categorized row carries short `reasons` (the classifier reasons, plus the matching rule in words, for
example `subject mentions "invoice"`). `reasons` are not part of the plan summary the window shows, but are in
the stored plan for the operator's drill-down.

### 3.3 `build_plan`

```python
def build_plan(rows, *, own: set[str], known: dict[str, set[str]] | set[str], now: datetime | None = None,
               folders: dict[str, str | None] | None = None, allow: dict[str, bool] | None = None,
               sample_size: int = 5) -> dict: ...

def plan_from_index(scopes=("work", "personal"), *, now=None, db_paths=None, folders=None) -> dict: ...
def plan_summary(plan: dict) -> dict: ...
```

`build_plan` is pure (no I/O). `known` is a mapping scope -> set (a plain set applies to every scope). `allow`
maps `account_id` to its `allow_organize` value for display only. `plan_from_index` is the I/O wrapper: it
reads `mail.iter_rows` for each scope that has an index (a scope with no index is skipped and simply missing
from `scopes`), loads `own` from the configured accounts and `known` per scope, and returns `build_plan(...)`.
`plan_summary` returns the plan without `message_ids` and `sources` (this is what the window shows and what the
model is given).

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
  so the operator can reconcile it with what the commitments hide: `total = spam + bulk` (own sent mail and
  review are reported separately, not in `total`); `by_reason` counts each reason string once per message and keeps
  the top 15.
* `review_queue` is capped at 100 entries, highest score first.
* `skipped` counts what the plan could not consider: `archive_sources` (PST/archive observations, which cannot be
  moved) and `non_inbox` (live rows in other mailboxes, used for context and counts only).
* The stored plan (on disk) additionally has `sources`: `{account_id: {message_id: {"source_id", "mailbox",
  "uidvalidity", "uid", "rfc_message_id"}}}`, which `organize_apply` needs. A plan is saved by the caller (CLI or
  window action) at `<window_home>/mail-plans/<plan_id>.json` with the atomic writer. Plans older than **24 hours**
  are refused by apply ("plan is stale, run Organize inbox again"). The plan contains subjects and sender
  addresses only, never bodies and never credentials.

## 4. Window integration

New items and actions are registered through the existing registry
(`register_provider` / `register_action`, wired in `builtin.default_registry`). Providers stay cheap and never
touch the network: they read the local index and the saved plan. Building a plan is an explicit action.

### 4.1 Items

| `kind` | `id` | `tab` | Source | Shows |
|---|---|---|---|---|
| `mail_thread` | `mail:<thread>` | work / personal | `providers_mail` | unchanged, but only classifier verdict `human` |
| `mail_filtered` | `mail-filtered:<tab>` | work / personal | `providers_mail` | title `N filtered out of commitments (S spam, B bulk)`, `why` lists the top 3 reasons and the review count; `context` = the `spam_filtered` shape for the window `days` |
| `mail_review` | `mail-review:<message id>` | work / personal | `providers_mail` | borderline mail: `title` = subject, `why` = `borderline (score N): <reasons>`; `context` = `message_id`, `sender`, `subject`, `score`, `reasons` |
| `mail_cleanup` | `mail-cleanup:<tab>` | work / personal | `providers_mail_cleanup` | the mail-cleanup group: with a saved plan, `title` = `Mail cleanup: N messages can be organized`, `why` = per-category counts; `context` = `plan_summary` for that scope plus `accounts: [{account_id, email, allow_organize}]`. Without a plan: `title` = `Organize inbox`, `why` = `No plan yet. Run Organize inbox to review it.` Always present when the scope has at least one configured account |

`mail_cleanup` for tab `work` contains only work-scope accounts, for `personal` only personal-scope accounts.
The provider reads the newest plan file for the scope; it never rebuilds one.

### 4.2 Actions

All ids are namespaced `mail.*`; params are validated like the existing actions. "Consequential" actions go
through `Registry.invoke`'s preview-then-`/api/confirm` path, so the preview **is** the dry-run and Confirm
performs. Every consequential action is audited by the existing `audit.jsonl`.

| Action id | Label | Applies to | Consequential | Params | What it does |
|---|---|---|---|---|---|
| `mail.organize` | `Organize inbox` | `mail_cleanup` | no | `scope` (optional) | Builds a plan (`plan_from_index`), saves it, returns `plan_summary`. Changes no mail and needs no network; this is the dry-run view. |
| `mail.organize.apply.<category>` | `Organize: <category label>` | `mail_cleanup` | **yes** | `plan_id` (default: newest), `accounts` (optional list of account ids) | One action per **movable** category: `receipts_finance`, `newsletters_promotions`, `notifications`, `hr_applicants`, `personal`, `spam`, `archive_old` (seven actions; `action_needed` and `waiting_on_others` have none). Preview (`confirm=False`) = `apply_plan(..., dry_run=True)`: per account, how many messages would move, to which folder, with the samples, plus accounts that are skipped because `allow_organize` is off. Confirm performs the moves. This is the **per-category Confirm button**. |
| `mail.organize.allow` | `Allow organizing` | `mail_cleanup` | **yes** | `account_id`, `allow` (bool) | Sets `allow_organize` on one account (`accounts.set_allow_organize`). Preview text states: "lets Agent OS move (never delete) mail in <email>'s INBOX; syncing stays read-only". |
| `mail.organize.undo` | `Undo organize` | `mail_cleanup` | **yes** | `journal_id` | Preview lists what would move back; Confirm runs `undo`. |
| `mail.filtered.show` | `Show filtered mail` | `mail_filtered` | no | `kind` (`spam`/`bulk`/`review`, optional), `limit` (<= 50) | Returns subject, sender, date and reasons of filtered messages, so nothing is hidden without a way to look. |
| `mail.review.human` | `This is a person` | `mail_review` | no | none | Records the sender in `mail-review.json` under `human` (section 2.6). |
| `mail.review.bulk` | `This is bulk` | `mail_review` | no | none | Records the sender under `bulk`. |

Confirm rules for the apply actions:

* Per-category Confirm is per action call: confirming `receipts_finance` never moves anything in another category.
* A Confirm moves at most **500 messages per account**; the result reports `remaining` and the operator confirms again.
* The plan is re-validated at Confirm time (section 5.3); stale or changed messages are skipped, never forced.
* `allow_organize` off for an account means that account is skipped with `skipped_not_enabled`, in preview and at Confirm.

### 4.3 Ordering and counts

`mail_filtered` and `mail_cleanup` items sort after `mail_thread` items and carry `age_days: null`. The
filtered count shown in the window equals `spam_filtered.total` for the same scope and window, so a reviewer can
reconcile it with the plan.

## 5. Applying moves: `imap_move.py` and `organize_apply.py`

### 5.1 The write boundary

`ReadOnlyIMAP` (sync) is unchanged and still refuses every write. Writes use a separate wrapper,
`MoveIMAP` in `imap_move.py`, created only by `organize_apply` through
`connect_write(account, *, factory=None)`, which raises `AccountError` unless `account.allow_organize` is true
(check at connect time, not only at plan time). Allowed commands, and nothing else:

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

Never deleting and never expunging has two consequences the operator should know:

* `UID MOVE` removes only the moved message from the source folder (that is what a move is) and is verified
  afterwards (5.3). It does not expunge anything else.
* The copy fallback leaves the message in **both** folders: the source copy carries the `$AgentOSOrganized`
  keyword so the operator can see which INBOX copies were already filed and remove them in their own mail client.
  If the folder does not allow custom keywords (`PERMANENTFLAGS` lacks `\*` and the keyword), the fallback is
  refused for that account with `error: "server supports neither MOVE nor keyword flags"` and nothing is copied.

Folder names: `LIST` gives the hierarchy delimiter and whether existing folders use an `INBOX.` namespace prefix
(`INBOX.Agent OS.Receipts`); `resolve_folder(logical_name, delimiter, prefix)` builds the real name. Mailbox
names are quoted with the existing `imap._quote` rule.

### 5.2 `allow_organize` (accounts)

* `Account.allow_organize: bool = False`, persisted in `accounts.json` (`False` is written explicitly). Old
  files without the key load as `False`.
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

### 5.3 `apply_plan`

```python
def apply_plan(plan: dict, category: str, *, accounts: list[str] | None = None, dry_run: bool = True,
               now: datetime | None = None, connect=None, journal_dir: Path | None = None,
               max_moves: int = 500) -> dict: ...
```

`dry_run=True` is the default and performs **no network access at all**: it reads only the plan and the account
settings. `connect` is the injected factory for tests (returns a `MoveIMAP` around a fake client). Validation
that raises before anything moves: unknown category; category without a target folder (`action_needed`,
`waiting_on_others`); a plan older than 24 hours.

Per account, in order:

1. Skip with `skipped_not_enabled` when `allow_organize` is false (dry-run reports it the same way).
2. Connect, `LIST`, create the target folder if missing, `SELECT` the source mailbox.
3. For each message (batched in UID sets of at most 100): check `UIDVALIDITY` equals the plan's (mismatch:
   skip all of that mailbox's messages with `uidvalidity changed; run Organize inbox again`); check the UID
   still exists and its `Message-ID` header equals `rfc_message_id` (otherwise skip that message with
   `message changed or gone`).
4. Write a journal line with `status: "pending"` **before** the IMAP command, then the command, then a final
   journal line (`moved` / `failed`) with the resulting target UID (from `COPYUID`/`MOVE` response when the server
   provides it, else found by `UID SEARCH HEADER Message-ID` in the target folder, else `null`).
5. After a `UID MOVE`, verify the message is present in the target by that search; if not, the journal line says
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

### 5.4 Journal and undo

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
 "undo": {"command": "agent-os mail organize undo --journal org_20261002T120500_ab12 --seq 1",
          "steps": ["UID MOVE 7 from Agent OS/Receipts back to INBOX"]}}
```

Every `moved` line carries `undo.command` (a runnable CLI line) and `undo.steps` (plain words). `pending` lines
without a final line (a crash between command and journal) are reconciled at the start of the next apply or
undo by searching both folders for the `Message-ID` and writing the real final line.

`undo(journal_id, *, seq=None, dry_run=True, connect=None, journal_dir=None) -> dict` reverses one move or a
whole journal: it finds the message in the `to` folder (by `to.uid` when `to.uidvalidity` is unchanged, else by
`Message-ID` search), then `UID MOVE`s it back to `from.mailbox`. For `copy_flag` moves it removes the
`$AgentOSOrganized` keyword from the INBOX copy and reports that the copy in the target folder remains (a
delete would be needed to remove it, and Agent OS never deletes). Undo is itself journaled (`status: "undone"`,
with `undone_of: <seq>`), is dry-run by default, never creates a second undo for an undo, and is idempotent
(a message already back in its source folder is skipped). In the window it is the consequential action
`mail.organize.undo` (Confirm); `Store.mark_source_present` restores the index state.

CLI (`src/agent_os/mail/cli.py`), all dry-run unless `--confirm`:

```
agent-os mail organize plan [--scope work|personal] [--json]          # builds, saves and prints the plan
agent-os mail organize apply --plan <id> --category <c> [--account <id>] [--confirm]
agent-os mail organize undo --journal <id> [--seq N] [--confirm]
agent-os mail organize journal [--scope work|personal]
agent-os mail account organize <account-id> --on|--off
agent-os mail headers-backfill [--account <id>]
```

### 5.5 Safety invariants (each needs a test)

1. No code path issues `EXPUNGE`, `UID EXPUNGE`, `CLOSE`, `DELETE`, `RENAME`, `APPEND`, or a `STORE` of
   `\Deleted`. Enforced by `MoveIMAP` and asserted with a recording fake.
2. With `allow_organize` false, `connect_write` raises and no apply path opens a write connection (fake
   factory is never called).
3. The default call (`dry_run=True`) opens no connection at all.
4. Every successful move has a final journal line with `undo.command`; `pending` precedes the IMAP command.
5. A mismatched `UIDVALIDITY` or `Message-ID` moves nothing for that message.
6. `ReadOnlyIMAP` and the sync path are unchanged: the existing read-only tests still pass untouched.
7. No credential, app password or secret appears in the plan, the journal, the audit line, or any result.
8. Work and personal scopes stay separate: plans, known-correspondent sets and journals are per scope; the only
   place both appear together is the operator's own window.
9. Spam and bulk are filtered from commitments only; they are counted in `spam_filtered` and listed by
   `mail.filtered.show`. Nothing is deleted, and the spam category is moved to `Agent OS/Spam`, not to Trash.

## 6. Order of work and acceptance

1. Schema v3 and `Store.iter_rows` (section 1), `Account.allow_organize` (5.2): tests in `test_mail.py`, `test_mail_accounts.py`.
2. `spam.py` with the labeled set and the targets in 2.7: `test_mail_spam.py`.
3. `organize.py` (`categorize`, `build_plan`, `plan_summary`): `test_mail_organize.py` with one test per rule,
   the age overlay, per-account counts that sum to `inbox_total`, `spam_filtered` reconciliation, both scopes.
4. `imap_move.py`, `organize_apply.py`, CLI: `test_mail_organize_apply.py` with a `FakeIMAP` covering MOVE, the
   copy fallback, unsupported-keyword refusal, folder creation, UIDVALIDITY change, undo, crash reconciliation,
   and every invariant in 5.5.
5. Window: `providers_mail.py` (commitments exclude spam and bulk, filtered summary and review items),
   `providers_mail_cleanup.py`, `actions_mail.py`, `builtin.py`: tests in
   `test_executive_window_provider_mail.py` (existing cases keep passing), `test_executive_window_registry.py`
   and `test_executive_window_builtin.py` style tests for the new actions (preview does not move; Confirm moves).
6. Update `docs/integrations/mail.md` (the read-only statements become "sync is read-only; organizing needs
   `allow_organize`") and fill in "Measured results" below.

Each step runs `python -m unittest discover -s tests -v` and `python agent.py validate` before it is called done.

## Measured results

(To be filled in by the classifier task with the numbers printed by `tests/test_mail_spam.py`: `n`,
`precision`, `recall`, `human_protected`, `review_rate`.)
