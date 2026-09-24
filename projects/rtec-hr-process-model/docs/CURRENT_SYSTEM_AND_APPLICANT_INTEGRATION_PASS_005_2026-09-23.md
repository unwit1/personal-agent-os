# Current HR Systems + Applicant Agent Integration — Pass 005 — 2026-09-23

## Scope

Pass 005 moves beyond the exhausted 2016–2026 PST corpus into current RTEC
sources and operational integration:

- current Google Drive HR work products;
- current public ridertec.org surfaces;
- the canonical Job Applicant Dashboard repository;
- the production Fillout-to-Google submission bridge;
- Personal Agent OS connector/MCP architecture.

No live applicant response rows, resumes, applicant notes, restricted self-ID
answers, employee case rows, credentials, or exposed public password values are
stored in GitHub.

## PST status

The historical email source is no longer the main completeness bottleneck.

- 576 unique messages structurally covered.
- 69 attachment-bearing messages.
- 132 recovered attachment occurrences.
- 104 unique attachment hashes after exact deduplication.
- 0 attachment parser errors.
- safe organizational content analyzed;
- restricted case/person records classified but left local;
- generic image layer visually audited.

Remaining currentness gaps require newer authoritative sources rather than
additional PST mining.

## Current restricted trackers

### FMLA

Drive contains both:

- a legacy `FMLA TRACKER.xls`;
- a native Google Sheet conversion with annual tabs through `Active 2026`.

Safe schema analysis proves a current restricted case ledger exists. Which copy
is authoritative still needs explicit designation.

### Attendance

A current `Attendance Tracker` consumes an ADP Employee Daily Totals report and
maintains derived attendance/reserve/FMLA/points views.

The automation target is reconciliation/integration, not another duplicate
tracker.

## Fillout -> Applicant Dashboard architecture

User-confirmed canonical relationship:

```text
Fillout
  -> Google Sheets/Drive bridge
  -> process_applications.py
  -> normalized application PDF + resume
  -> separate restricted Affirmative Action / EEO self-ID PDF
  -> download_log.csv
  -> dashboard.db
  -> Agent OS restricted adapter
```

The populated/current application repository is:

`unwit1/job-applicant-dashboard`

The similarly named `unwit1/applicant-dashboard` repository is empty and is
not the canonical implementation.

## Production Fillout source

The Dashboard's production defaults point to a Google Sheet titled:

`Employment Application Form`

Observed safe structure:

- 154 columns;
- Fillout Submission ID and submission timestamp;
- position/county preference;
- applicant contact/address data;
- references;
- education groups;
- resume upload;
- employment-history groups;
- safety-sensitive driver questions;
- signature;
- four restricted AAP/EEO self-identification fields;
- Fillout repeating-field/control metadata.

Only the header row was inspected. Live applicant response rows were not read.

An older August 6 Drive sheet titled `Fillout Applications` is structurally
empty and is not the Dashboard's production default.

Dashboard code documents a Fillout reconnect to a new Sheet on 2026-08-14. The
importer deliberately deduplicates by Submission ID or legacy name+submission
timestamp, not by Sheet row number, so a source-sheet swap does not reimport all
applicants.

Resume retrieval prefers the direct upload URL in the source row. The
configured Drive resume folder is a fallback.

## Hard privacy boundary

The raw Fillout source row co-locates ordinary application answers and
restricted self-ID fields. Therefore Agent OS MUST NOT connect directly to the
raw Sheet for ordinary recruiting administration.

The Applicant Dashboard remains the normalization/privacy boundary.

Ordinary Agent tools may:

- list/search normalized records;
- summarize minimum-necessary administrative state;
- surface missing document/status/scheduling/follow-up work;
- report sync health;
- consume workflow events;
- prepare user-directed administrative drafts after the user chooses the action.

Ordinary Agent tools must not:

- expose restricted self-ID;
- expose raw source rows;
- expose restricted-form contents/path;
- rank applicants;
- recommend who should be hired/rejected;
- make employment decisions;
- use self-ID in an employment decision.

## Privacy bug found and corrected

Previous `process_applications.run()` behavior:

- exact-matched four restricted AAP/EEO source headers;
- if one changed/missing, warned but continued;
- an unmatched restricted field could therefore become an ordinary application
  Q&A field.

Pass 005 changed this to fail closed.

If any required restricted source header is missing:

- zero new applications are processed;
- a restricted-header-drift error is returned;
- the mapping must be reviewed before processing resumes.

Synthetic regression tests were added.

## Fillout sync health

The Dashboard now writes a metadata-only
`Config/fillout_sync_health.json` snapshot after source checks.

It contains only:

- provider/status;
- last check/success timestamps;
- processed/warning counts;
- safe error category;
- source row count;
- header column count;
- header SHA-256;
- source-config SHA-256.

It deliberately excludes:

- source header labels;
- applicant names/rows;
- warning text;
- raw provider errors;
- local paths;
- credentials.

Agent OS can therefore distinguish:

- healthy;
- degraded;
- unavailable;

without reading applicant data.

## Agent event/outbox seam

`dashboard.db` now has an append-only local `agent_events` outbox.

Initial canonical events:

- `submission_processed`;
- `status_changed`.

Events have:

- opaque event ID;
- current local applicant key;
- event type;
- source component;
- timestamp;
- scalar metadata payload;
- sensitivity class;
- acknowledgment state.

No application text, resumes, notes, restricted self-ID, or document payloads
belong in the event table.

Agent OS can read/acknowledge events without changing applicant workflow state.

## Agent OS adapter

Personal Agent OS now contains:

`src/agent_os/rtec_applicants.py`

MCP tools:

- `applicant.list`
- `applicant.search`
- `applicant.get_summary`
- `applicant.get_status`
- `applicant.pending_actions`
- `applicant.sync_status`
- `applicant.events`
- `applicant.event_ack`

The adapter:

- opens Dashboard SQLite read-only for ordinary tools;
- uses explicit column allowlists;
- never SELECTs all applicant fields for returned DTOs;
- reduces document paths to presence booleans;
- excludes notes, screening fields, restricted-form path/content and raw source
  rows;
- writes only event acknowledgment state.

Connector metadata is registered as:

- ID: `rtec-applicants`
- state: `desired`
- health: `unknown`

It must remain that way until a live work-PC smoke test passes.

## Test status

Synthetic tests were committed for:

- restricted source-header drift;
- privacy-safe sync-health persistence;
- local event/outbox read/ack behavior;
- Agent OS restricted applicant projections and MCP surface.

A lightweight GitHub Actions workflow was added to the Dashboard repository,
but the observed hosted run failed before any runner steps began (zero runner
steps / no runner ID). Therefore tests are **committed but not claimed as
executed successfully** in GitHub-hosted CI.

A live/local test run remains required on the work PC.

## Current public website audit

Current public surfaces show systemic content/version drift.

Observed classes include:

- English/localized EEO role mismatch;
- English/localized driver starting-pay mismatch;
- service-area count inconsistency;
- stale relative-age company copy;
- production demo/unrelated jobs;
- job-board/application navigation mismatch;
- public 401(k) timing that needs plan-booklet reconciliation;
- localized stale bid solicitation;
- superseded public compliance-document revisions.

A public instruction page also exposed credential-like kiosk-exit values. The
values are intentionally not stored.

Remediation requires rotation/removal/cache cleanup plus a broader public
secret scan.

## Public website monitor candidate

A reusable monitor specification now covers:

- named-role currentness;
- English/localized parity;
- recruiting/ATS parity;
- benefit claim currentness;
- service-area parity;
- public compliance-document versions;
- credential-like public exposures with mandatory value redaction;
- sensitive-data intake copy;
- stale relative-age marketing copy;
- production template/demo content.

## Genuine unresolved source gaps

These no longer appear to be hidden in the already-processed PST/Drive/GitHub
sources:

1. current retirement/401(k) recordkeeper/provider and operative plan booklet;
2. current workers-comp carrier/administrator and claim portal/workflow;
3. approved EEO/AAP plan governing after 2024-06-30 and its state approval;
4. Kentucky EEO certification renewal succeeding the approval expiring
   2026-09-30;
5. authoritative live FMLA tracker copy;
6. validation of current Attendance Tracker formulas/exclusion logic;
7. exact current payroll/benefit ownership boundaries;
8. public-site cleanup/ownership and canonical publishing process.

## Next implementation seam

On the work PC:

1. pull latest `job-applicant-dashboard`;
2. run:
   - `python -m py_compile process_applications.py dashboard_core.py`
   - `python -m unittest discover -s tests -v`
3. run one real source check through the existing Dashboard;
4. verify `fillout_sync_health.json` contains metadata only;
5. verify a synthetic/non-production status transition produces an outbox
   event;
6. pull latest `personal-agent-os`;
7. invoke `applicant.sync_status` through local Agent OS MCP;
8. only after successful restricted reads should connector registration move
   from desired/unknown to registered/healthy.

No live applicant should be used as a committed test fixture.
