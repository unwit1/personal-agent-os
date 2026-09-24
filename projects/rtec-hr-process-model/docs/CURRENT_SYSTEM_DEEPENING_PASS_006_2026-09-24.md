# Current HR Systems Deepening — Pass 006 — 2026-09-24

## Scope

Pass 006 continues after the historical PST/attachment exhaustion and Pass 005
current-system/Applicant-Agent integration work.

This pass focused on:

- hardening and currentizing the Fillout -> Applicant Dashboard -> Agent OS
  architecture;
- removing stale/personal examples from the Git-tracked Dashboard repository;
- broadening the restricted Agent applicant read surface without exposing raw
  applicant data;
- validating current Kentucky EEO Contract Compliance, unemployment/KUIP,
  workers' compensation and Kentucky OSH process baselines;
- narrowing FMLA tracker authority through Drive revision metadata;
- auditing Attendance Tracker formulas without reading employee row values.

No live applicant rows, employee case rows, restricted self-ID data, medical
details, credentials or exposed public secret values were canonicalized.

## Applicant Dashboard / Agent OS

### Canonical source chain

Current architecture remains:

```text
Fillout
-> configured Google Sheet/Drive bridge
-> process_applications.py
-> normalized application/resume + separate restricted self-ID form
-> download_log.csv
-> dashboard.db
-> restricted Personal Agent OS adapter
```

Historical source evolution is now explicit:

1. April 2026 Google Form prototype;
2. May/June RTEC Google Form iteration;
3. August 6 Fillout scaffold;
4. August 14 Fillout source reconnect;
5. current production Fillout-backed `Employment Application Form` Sheet.

### Dashboard repository cleanup

Canonical documentation was rewritten/currentized:

- `SETUP_INSTRUCTIONS.md`
- `WORKFLOW_HANDOFF.md`
- `CLAUDE.md`
- `README.md`
- `process_applications.py` architecture header
- `docs/AGENT_OS_INTEGRATION.md`

Stale assumptions removed include:

- obsolete `Fillout Applications` source naming;
- fallback resume folder described as primary;
- row number/state-file identity;
- Task Scheduler as the only runtime model;
- old nested-folder architecture;
- historical applicant-name/count examples;
- personal Google account setup examples;
- “no source health alerting” descriptions.

Current Git branch privacy cleanup also replaced known applicant names in
`DEV_NOTES.txt` with synthetic labels and changed person-specific code comments
to role-based HR wording.

### Agent applicant capabilities now implemented

Personal Agent OS exposes:

- `applicant.list`
- `applicant.search`
- `applicant.get_summary`
- `applicant.get_status`
- `applicant.get_document_metadata`
- `applicant.get_timeline`
- `applicant.pending_actions`
- `applicant.openings`
- `applicant.sync_status`
- `applicant.events`
- `applicant.event_ack`

The adapter uses opaque `applicant_ref` values backed by Dashboard
`agent_ref`.

Document metadata:

- application/resume: path-free presence/type/size/modified metadata;
- restricted compliance/self-ID form: presence-only booleans.

Timeline/event reads contain metadata only.

`applicant.openings` exposes organization-level Dashboard opening
configuration and never candidate fit/ranking.

Connector remains `desired` / health `unknown` until a real work-PC smoke
test runs.

## Current Kentucky EEO Contract Compliance

Current official Kentucky Finance guidance establishes:

- apparent low bidders provide required EEO information through the contracting
  agency;
- current process is electronic;
- Contract Compliance reviews the information routed by the contracting agency;
- approved contractors/vendors may bid on covered contracts without refiling
  additional data for one year.

Current KYTC response instructions state:

- Finance does not pre-approve vendors;
- unsolicited submissions are not processed/returned;
- current Finance-developed process/forms are required.

RTEC internal approval evidence remains:

- approval 2025-09-24;
- expiration 2026-09-30;
- no successor approval found in current sources.

Therefore expiration is not modeled as an automatic unsolicited renewal task.
The unresolved trigger is whether RTEC has a current covered procurement,
apparent-low-bidder/selected-contractor event or direct contracting-agency /
Contract Compliance request.

## Kentucky Unemployment / KUIP

Post-launch official verification confirms:

- KUIP Employer/TPA portals are live;
- quarterly wage/tax reporting is now electronic through KUIP;
- employer account maintenance, wage filing, payments and charge statements
  are tax-side KUIP functions;
- current employer identity uses a new 9-digit KEIN;
- during the Benefits & Appeals bridging period, fact finding, claims-related
  correspondence and appeals filing continue in legacy systems.

The June 2026 email describing an August 17 future launch is now superseded by
verified post-launch current state.

RTEC-specific unresolved items remain owner/backup, secure account ownership,
and exact internal routing of tax vs claims/appeals work.

## Kentucky workers' compensation / OSH baseline

Current Kentucky employer baseline now modeled:

- employer keeps workplace injury records;
- work-related/alleged work-related injury or disease must be reported to the
  workers' compensation carrier/benefits administrator within three working
  days of employer notification;
- qualifying lost-time FROI is handled by the carrier/administrator to the
  Department of Workers' Claims;
- DWC receives FROI/SROI electronically from carriers/TPAs via EDI.

Current Kentucky OSH serious incident reporting:

- covered fatality: 8 hours;
- covered hospitalization: 24 hours;
- amputation: 24 hours;
- loss of eye: 24 hours.

Older 72-hour Kentucky language is superseded by the current 24-hour serious
injury rule.

RTEC-specific carrier, TPA/claims administrator, reporting portal, internal
owners, forms, RTW/light-duty and closure workflow remain unresolved.

## FMLA tracker version relationship

Drive revision metadata:

- legacy `FMLA TRACKER.xls` stored modification:
  2026-05-15T18:17:32Z;
- native `FMLA Tracker` first revision:
  2026-05-15T18:17:58Z;
- native second revision:
  2026-05-15T18:18:51Z.

This strongly suggests a near-immediate XLS -> Google Sheets conversion/import,
but no later revisions were observed that prove which copy HR actually treats
as authoritative.

Do not assign authority from timestamps alone.

## Attendance Tracker formula audit

Only formula structure was read; row values were excluded.

Observed formulas:

1. ADP/input normalization:
   - carries employee/supervisor grouping through the export;
   - parses dates/hours;
   - classifies regular/sick/vacation/overtime;
   - groups by employee/supervisor/date;
   - excludes entries matching `SupervisorBlacklist`;
   - surfaces regular-hours shortfalls or sick/vacation days.

2. Reserve Hours Used:
   - if Total Hours < 8, computes `8 - Total Hours`.

3. Reserve Hours Left:
   - looks up hire date and prior reserve state;
   - after hire-date anniversary, sets a 24-hour base and subtracts reserve
     hours used after the anniversary;
   - otherwise subtracts usage from prior carried balance.

No formulas were observed in:

- `Points tracker`;
- `Blacklist`;
- `Previous Months`.

These are therefore manually maintained state/configuration in the inspected
workbook.

Current December 15, 2025 handbook validates:

- six-point attendance system;
- 1/4, 1/2, 1-point absence-duration examples;
- 2/4/6 point discipline milestones;
- 60-day point reduction;
- 365-day point expiration;
- documented FMLA, workers' comp, funeral and jury-duty exclusions;
- three additional unpaid days for promoting good attendance.

The handbook does **not** explicitly validate:

- that those three days are the workbook's `Reserve Hours`;
- a 24-hour hire-date-anniversary reset;
- a universal 8-hour day assumption;
- the SupervisorBlacklist business rule;
- manual Points tracker reconciliation.

These remain validation requirements.

## Mail currentness limitation

The connected Outlook surface returned zero RTEC/ADP/Guardian/Kentucky/Fillout
matches after 2026-06-26. It has not been verified as the RTEC EarthLink work
mailbox, so zero results are not evidence that no later work mail exists.

## Validation state

GitHub-hosted Actions in the relevant repos continue to fail before receiving a
runner (runner ID 0 / no steps), so committed synthetic tests are not claimed
as executed successfully.

Required work-PC validation remains:

```bash
python -m py_compile process_applications.py dashboard_core.py rtec_dashboard.py screening_rules.py
python -m unittest discover -s tests -v
```

Then validate the live restricted Agent connector before moving registry health
from desired/unknown to registered/healthy.
