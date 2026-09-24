# RTEC Applicant Pipeline / Agent OS Integration

Status: **implementation-ready / high priority**  
Updated: 2026-09-23  
Related application: `unwit1/job-applicant-dashboard`

## Goal

Make the RTEC applicant workflow available through Personal Agent OS without
duplicating the existing applicant-ingestion/business logic or leaking
applicant/EEO data into Git-backed memory.

Canonical path:

```text
Fillout
  -> Google Sheet + Drive bridge
  -> job-applicant-dashboard/process_applications.py
  -> application/resume + separate EEO/AAP artifacts
  -> download_log.csv
  -> dashboard.db
  -> local Agent OS applicant adapter
  -> Agent OS Connector Broker / MCP
  -> authorized ChatGPT / Claude / Codex / future surfaces
```

The Applicant Dashboard remains the operational normalization/workflow owner.
Agent OS is the cross-project access/orchestration layer, not a second ATS.

## Why this belongs in Agent OS

The user wants applicant intake and recruiting work accessible to the same
agent that understands current RTEC openings, HR policies, communications,
calendar/tasks, document scanner, and broader work context.

Useful cross-system examples:

- tell the user which new applicants need action;
- summarize a candidate before an interview;
- detect an applicant whose resume/application is missing;
- reconcile applicants against current county openings;
- prepare an interview request or clarification message;
- surface unresolved applicant commitments;
- help assemble a hiring packet after the user chooses to proceed;
- update aggregate AAP workflow state without exposing self-ID to hiring logic;
- warn when Fillout/Google import health becomes stale.

## Current implementation facts

The canonical Dashboard repository already:

- polls the Fillout-backed Google Sheet approximately every five minutes when enabled;
- resolves resume uploads from Google Drive/direct URLs;
- generates normalized application PDFs;
- generates **separate** Affirmative Action/EEO self-ID PDFs;
- uses `download_log.csv` for idempotent processed-row tracking;
- uses `dashboard.db` for applicant workflow state;
- exposes status, notes, denial/disqualification reasons, opening/distance logic,
  email-draft preparation and local document paths;
- deliberately sends no applicant communication automatically.

The Dashboard currently uses the Google Sheet/Drive integration rather than
Fillout's REST API directly.

## Connector-broker model

Create one Agent OS connector/adaptor with conceptual identity:

- provider: `rtec-applicants`
- privacy domain: `work-hr-restricted`
- adapter owner: local Applicant Dashboard bridge
- underlying sources: Fillout via Google bridge + local Dashboard store
- secret handling: Google/service credentials stay inside the Dashboard/local
  adapter boundary and are referenced only through approved local secret/config
  mechanisms; never copied to Git or prompt context.

Do not mark provider health `healthy` or connector registration `registered`
until an actual local adapter passes a live health/read smoke test.

## Provider-neutral tool contract

Read:

- `applicant.list`
- `applicant.search`
- `applicant.get_summary`
- `applicant.get_status`
- `applicant.get_pending_actions`
- `applicant.get_document_metadata`
- `applicant.get_opening_match`
- `applicant.get_timeline`
- `applicant.sync_status`

Controlled execution:

- `applicant.sync_now`
- `applicant.prepare_interview_request`
- `applicant.prepare_clarification`
- `applicant.prepare_offer`
- `applicant.prepare_area_manager_handoff`

The Agent integration remains administrative/supportive. It must not rank applicants, recommend who should be hired or rejected, or make employment decisions. After the user has made an employment decision, the Agent may help prepare the corresponding administrative paperwork or communication for review.

## Event model

The Dashboard adapter should provide an append-only local event/outbox seam.

Events:

- submission_received
- submission_processed
- resume_linked
- resume_missing
- clarification_needed
- application_record_updated
- opening_match_changed
- status_changed
- interview_requested
- offer_prepared
- denied
- disqualified
- hired
- inactive
- sync_failed
- sync_stale

Agent OS consumes them through the normal resumable ingestion ledger and
acknowledges each event idempotently.

## Proactive Agent OS behavior

The Proactive Insight / Personal Executive layers may use these events to
surface:

- new applicants requiring review;
- applications that have sat in New/Interested/Interview Requested too long;
- missing resume/application artifacts;
- clarification requests awaiting response;
- interviews/offers needing follow-up;
- opening changes that make an inactive candidate newly relevant;
- stale Fillout sync or schema drift;
- unresolved hiring commitments mentioned elsewhere in mail/chat.

Do not generate repetitive alerts for unchanged state.

## EEO / self-ID firewall

This is a hard architecture boundary.

Normal hiring tools must not return or use:

- race/ethnicity;
- sex/gender self-ID;
- veteran self-ID;
- disability self-ID;
- other AAP demographic fields.

Those fields may be available only to a separately scoped compliance/AAP path
for authorized aggregate reporting. They must never feed applicant fit,
screening, ranking, recommendation, denial or interview logic.

## Memory boundary

Applicant-specific content must remain local/private:

- applicant name/contact information;
- address;
- resume;
- references;
- employment history;
- application answers;
- notes;
- reasons tied to a named applicant;
- EEO/self-ID;
- attached files.

Git may store:

- schemas;
- business-process rules;
- generalized findings;
- connector metadata;
- test fixtures using synthetic applicants;
- aggregate/non-identifying metrics;
- implementation decisions.

## Sync-health requirements

Expose:

- last source check;
- last successful import;
- source newest timestamp;
- stale/no-new-source warning based on normal operating pattern;
- unprocessed source rows when determinable;
- source header/schema fingerprint;
- missing/broken resume links;
- source permission/auth failure;
- dashboard DB reachability;
- event-outbox depth and oldest unacknowledged event.

Important existing failure mode: the Dashboard documentation states that if the
Fillout-to-Google integrations are disconnected, new submissions can silently
stop. Agent OS integration should explicitly detect this instead of equating
"no new applications" with "healthy."

## Fillout direct webhook

Fillout currently supports REST webhooks on submission. This can later be used
as a wake-up signal:

```text
Fillout submission
-> webhook says "new source activity"
-> local adapter triggers canonical Dashboard sync
-> process_applications.py performs idempotent normalization
-> Dashboard emits submission_processed event
-> Agent OS consumes event
```

The webhook is not authoritative applicant storage and must not create an
applicant independently of the canonical importer.

## Implementation stages

### Stage A — read-only local adapter

- define stable applicant ID independent of display name;
- wrap Dashboard DB reads in a small module;
- return privacy-filtered DTOs;
- add sync-health read;
- add document metadata without reading files by default;
- add synthetic tests.

### Stage B — outbox/event seam

- add append-only event table;
- instrument import/status/flag/opening transitions;
- add idempotent acknowledgment;
- route through Agent OS ingestion ledger.

### Stage C — Agent OS connector adapter

- expose provider-neutral tools through Agent OS MCP;
- register desired connector metadata only after adapter code exists;
- resolve local path/config without hard-coded machine paths;
- prove EEO firewall in tests.

### Stage D — prepared actions

- call existing Dashboard draft/business functions;
- return proposed action + draft artifact;
- require user approval for sends/consequential state changes.

### Stage E — proactive workflows

- new-applicant queue;
- stale-stage follow-up;
- missing-document detection;
- opening-change candidate resurfacing;
- integration-health alerts.

### Stage F — optional Fillout webhook wake-up

- authenticate webhook;
- no applicant persistence in handler;
- trigger canonical sync;
- dedupe/replay safe;
- rate limit;
- health/audit log.

## Acceptance criteria

1. One Fillout submission becomes one normalized Dashboard applicant.
2. Agent OS can find that applicant after Dashboard processing without reading raw Fillout.
3. Replaying source/event data cannot duplicate the applicant.
4. Normal hiring tools cannot retrieve EEO/self-ID fields.
5. Agent OS can detect that Fillout/Google ingestion has stopped or gone stale.
6. Agent OS can prepare user-directed administrative drafts after the user chooses the action, but does not make employment decisions or send automatically.
7. All applicant reads/actions produce local audit records.
8. Git contains no live applicant fixture, resume, EEO response, credentials or local DB.
9. Connector is available to any authorized Agent OS surface through one bridge rather than separate provider setups.
10. Dashboard remains fully usable if Agent OS is offline.

## Cross-project source

Dashboard-side contract:
`unwit1/job-applicant-dashboard/docs/AGENT_OS_INTEGRATION.md`
