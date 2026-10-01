# Applicant Executive contract

Status: implementation contract for the first Personal Executive workflow (2026-10-01).

## Ownership and boundaries

The RTEC Applicant Dashboard is the sole owner of applicant ingestion, records,
opening matches, AI reviews, manager assignment, calendar availability, outreach
rendering, email delivery, and workflow state. Agent OS orchestrates those
existing functions through one `DashboardGateway`; it is not another applicant
tracking system and does not make employment decisions. The Dashboard must remain
usable when Agent OS is offline. The existing read-only
`src/agent_os/rtec_applicants.py` adapter supplies administrative reads, opaque
references, checkout discovery, and local privacy-safe audit behavior.

The gateway is the only place that may see the Dashboard's internal
`applicant_key`. Every Executive-facing gateway operation accepts
`applicant_ref` as its applicant identity. `LocalDashboardGateway` resolves
that reference to the internal key locally before calling a Dashboard function
whose native signature requires the key; the Dashboard signatures stay
unchanged. `ranked` returns projected applicants carrying `applicant_ref`,
never the internal key. `applicant_ref` is the only applicant
identity persisted in Executive batches, logs, audit records, or tool results;
names and contact details may appear as restricted outreach content, never as
lookup keys. Internal keys, source/provenance keys, applicant or source document
filenames and paths, and raw Dashboard rows must not cross the gateway. The
limited path exception is `draft_path`: the generated local outreach draft path
passed to `record_outreach_drafted` after approval. It identifies an Executive
draft, never an applicant or source document, and is not an applicant identity.

The gateway projects applicants onto an explicit allowlist: `applicant_ref`,
name, position, submitted time, status, county/city, and email only in the
send path that needs it. It rejects all other applicant fields, including
`aa_pdf_path`, race/ethnicity, sex/gender self-ID, veteran or disability self-ID,
and other AAP data. Restricted fields must never appear in an Executive result,
outbox file, audit record, or LLM prompt. Compliance/AAP work is a separately
scoped path; it cannot inform candidate fit or interview choices.

## Gateway contract

`DashboardGateway` has exactly these Executive-facing operations. The
Dashboard source column names the native function called inside the local
gateway; any native `applicant` or `applicant_key` argument is resolved there
and is not part of the Executive-facing signature.

| Operation | Dashboard source | Contract |
| --- | --- | --- |
| `ranked(min_score=0)` | `candidate_review.ranked` | Read existing `(applicant, review)` pairs. Reviews provide score 0–100, recommendation `interview`, `maybe`, or `not_a_fit`, and `result_json` summary, strengths, concerns, and criterion evidence (`met`: `yes`, `no`, or `unclear`). |
| `match_for(applicant_ref)` | `opening_match.match_for(applicant)` | Resolve the Dashboard applicant locally; return `match`, `pending`, `primary`, `alternates`, `reasons`, `groups`, `group_label`, and `manager`. |
| `manager_for(applicant_ref)` | `interview_calendar.manager_for_applicant(applicant)` | Resolve the Dashboard applicant locally to find its manager for interview scheduling. |
| `suggest_slots(manager, duration_minutes, count)` | `interview_calendar.suggest_slots` | Return conflict-checked `(datetime, reason)` suggestions. |
| `render_outreach(name, position, slots, interview_type, location, duration_minutes, message, county)` | `interview_outreach.render_outreach` | Return the Dashboard-rendered `(subject, body)`. |
| `record_outreach_drafted(applicant_ref, slots, interview_type, location, duration_minutes, draft_path, area_manager)` | Dashboard draft recorder (native `applicant_key`) | Resolve the key locally and return the Dashboard draft record ID. This is a write and cannot occur while merely planning. |
| `send_now(applicant_ref, kind, to_addr, subject, body)` | `email_sender.send_now(applicant_key, kind, to_addr, subject, body)` | Resolve the key locally, send through Outlook, and return an email ID or raise on failure. |

`LocalDashboardGateway` lazily imports Dashboard modules from the checkout
already discovered by `rtec_applicants`; it adds that checkout to `sys.path`
only inside the gateway. `SyntheticDashboardGateway` supplies synthetic
applicants, reviews, managers, and calendar data in memory and records every
call. Tests and demos use the synthetic gateway and never touch a real
Dashboard, Outlook, or the network.

Review reads are strictly passive. Neither `ranked` nor any Executive path may
call `review_all`, `review_applicant`, or another operation that starts an AI
review or incurs the operator's API cost. Reviewable Dashboard statuses are
`New`, `Interested`, `Interview Requested`, and `Clarification Requested`.

## Read flows

`needs_action()` groups `rtec_applicants.pending_actions()` by its
administrative reason, shows age, and suggests the next administrative step.
It does not convert a pending action into a hiring recommendation.

`suggestions(opening)` reads existing Dashboard AI reviews, filters to the
reviewable statuses and applicants whose Dashboard `match_for` result fits the
requested opening, and orders matches by Dashboard score, best first. Each
suggestion contains score, recommendation, review reasons and criterion
evidence, match reasons, and the label **“Dashboard AI review: advisory; you
decide”**. It reports the count of matching applicants with no existing review
without reviewing them. Every suggestions view writes a local privacy-safe
audit record; audit failure fails the view closed. The operator decides whom
to interview.

## Outreach state and approvals

`plan_outreach(applicant_refs, opening, interview_type, location,
duration_minutes)` resolves each opaque reference, asks the Dashboard for the
manager and conflict-checked slots, and renders proposed subject/body through
the Dashboard. It creates one batch in `PENDING_APPROVAL` under the gitignored
`.agent-local/executive/outbox/`. Planning is a local, reversible draft step:
it neither records a Dashboard draft nor sends mail. Outbox files are local
restricted data; Git-backed memory receives only schema or aggregate data.

The operator's first decision is `approve_batch(batch_id, choices)`. For each
item, the operator confirms offered dates/times, selects different offered
dates/times, or drops that item. At approval, the gateway calls `suggest_slots`
again for the item's manager and duration. Every retained choice, including a
confirmed original offer, must appear in these fresh conflict-checked results;
otherwise the item needs a new choice from the fresh suggestions. Arbitrary
typed times are not approvable under this gateway contract because it has no
separate availability operation. Changed choices cause the Dashboard outreach
to be re-rendered. The approved choices and resulting text are persisted before
the batch moves to `APPROVED`. Approval does not authorize delivery. Before
sending, show the exact recipients, subjects, bodies, and confirmed dates/times
for a distinct send confirmation.

Delivery is dry-run by default. Only an explicit send confirmation may invoke
`send_now`. The send path resolves each internal key locally, verifies the
approved content and recipient, and sends only retained items. A dry run may
prepare drafts and record them through `record_outreach_drafted` after approval,
but must never call `send_now`. The Dashboard remains the owner of any
corresponding draft or email record.

Persist each item's state before and after each send attempt, together with
the returned email ID when available. Continue to preserve successful items
if a later item fails; report the batch as partial with the per-item outcomes.
On restart, never resend an item recorded as sent. If an attempt began but its
outcome is unknown (for example, a crash after Outlook accepted it but before
the email ID was saved), mark it uncertain and require operator reconciliation
before retrying. A raised failure remains visible for correction; a later
retry targets only confirmed unsent items, with a fresh send confirmation.
This prevents a partial failure from silently duplicating mail.

## Validation contract

Synthetic tests must verify the gateway call ledger, passive review reads,
separate approval and send confirmation, dry-run behavior, and recovery after
partial or uncertain delivery. Feed a synthetic applicant with `aa_pdf_path`,
self-ID fields, and source keys through every path and assert those values are
absent from Executive output, the outbox, audit records, and LLM prompts.
