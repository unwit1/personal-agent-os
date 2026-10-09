# Universal intake

Every data source connected to Agent OS feeds one pipeline:

```
connected source  ->  scoped, readable directory  ->  intake queue (per scope)  ->  consumers
(mail, 3CX, ambient       (Documents/HR/Correspondence,     .agent-local/intake/        engine: Ingester Engine KB
 recordings, iPhone        Documents/Personal/...)          <scope>/queue.sqlite3       classify: model review of
 texts, report folders,                                                                  undecided spam/work flags
 any connected folder)                                                                   promote: PII-free company
                                                                                         knowledge for RTEC-HR review
```

Work and personal never share a directory, a queue or a knowledge base. The scheduled task
**AgentOS Intake** runs `python -m agent_os intake run` every 15 minutes:

1. `mail sync` for every enabled account (read-only IMAP).
2. Rebuild each scope's correspondence directory (`agent_os.mail.directory`): one Markdown file per
   distinct message, `index.csv`, `search.html`, `Flagged.md`, `COVERAGE.md`, `People/`, `people.json`,
   `manifest.jsonl`. Only changed files are rewritten.
3. Rebuild HR GUI dossiers (their **Correspondence** section reads `people.json`).
4. `collect`: every adapter records its items in the scope's queue. New or changed content is queued again.
5. `classify` (`intake/classify.py`): up to `classify_batch` undecided mail per scope (flag `review`, plus work mail
   from personal-address senders who are not employees) goes to the model (Claude Code CLI on the subscription,
   API keys stripped, Haiku, minimal context; SSN/phone/DOB-like numbers masked). Decisions land in
   `.agent-local/mail/<scope>/flag-overrides.json`; the next directory export applies them.
6. `promote` (`intake/promote.py`): `promote_batches` x 25 human work emails are distilled into organisation-level
   statements (policies, procedures, systems, vendors, benefits, compliance, forms, roles). A deterministic screen
   drops anything with contact details, ID numbers, or names of people who are not current staff. Survivors go to
   `.agent-local/intake/work/knowledge-candidates.jsonl` (status `candidate`) for review before any RTEC-HR change.
7. `drain`: up to `engine_batch` pending items per scope go to that scope's Ingester Engine knowledge base
   (one drain per scope at a time: `drain.lock`).

## Scopes and targets (`.agent-local/intake/settings.json`)

| Scope | Directory | Engine knowledge base (local, never in Git) |
|---|---|---|
| work | `Documents/HR/Correspondence` (+ `Phone Log/`, `Recordings/`) | `Documents/HR Automation Local/Knowledge/rtec-work` (hr-v1, strict-pii) |
| personal | `Documents/Personal/Correspondence` (+ `Messages/`, `Recordings/`) | `Documents/Personal/Knowledge` (general-v1, standard-private) |

The RTEC-HR repository holds **no PII**: policies, processes, company facts and current staff roles only.
Nothing reaches it automatically; the `promote` consumer only marks work items whose derived,
PII-free knowledge may be proposed as reviewable candidates.

## Flags (mail)

`work`, `automated` (applicants, billing, HR/benefit systems), `personal`, `not_work` (personal mail in a work
mailbox; model decision), `bulk`, `spam`, `review`. `spam`, `bulk` and `not_work` are skipped by the Engine with
a visible reason; only `work` mail feeds `promote`.
Rules: the deterministic classifier in `mail/spam.py` and `mail/organize.py`, plus organisation context
(internal domains are never spam, employee addresses are work, known vendor domains are automated,
throwaway TLDs / padded or promotional sender names are spam). `review` items get a `classify` delivery
for model review. Flags never delete or move mail; spam and bulk get an explicit `skipped` engine delivery.

## Sources

| Adapter | Scope | Items |
|---|---|---|
| `mail` | per account | one per distinct message (manifest of the correspondence directory) |
| `3cx` | work | voicemails (audio) and one call-log file per day |
| `ambient` | `ambient_scope` (default personal; a capture may carry its own `scope`) | one transcript file per recording |
| `iphone` | personal | one file per conversation per day |
| `folders` | per folder | every readable file in a connected folder (`agent-os intake connect-folder NAME PATH --scope work`) |

Add a source with `@adapter("name")` in `agent_os/intake/adapters.py`, yielding `Item`s that point at
a readable file. Nothing else changes: queue, consumers and the scheduled task pick it up.

## Mail found on this PC

`agent-os mail import-pst PATH` (Outlook PST/OST) and `agent-os mail import-files PATH` (.eml, .msg,
zip exports, Thunderbird/mbox) put every copy into the work index; copies merge at message level
(Message-ID, content hash, composite key). `agent_os.mail.dedupe.merge_near_duplicates` folds export
copies whose converter dropped the Message-ID into the original (same sender, subject, minute, body).

## Commands

```
python -m agent_os intake run [--no-sync] [--no-drain] [--drain-limit N]
python -m agent_os intake status
python -m agent_os intake drain --scope work --limit 500
python -m agent_os intake classify --scope work --limit 200
python -m agent_os intake promote --batches 4
python -m agent_os intake connect-folder adp-reports "C:\...\reports" --scope work --kind report
```
