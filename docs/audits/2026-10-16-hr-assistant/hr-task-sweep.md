# HR sweep: Executive command center audit (2026-10-16)

**Setup.** I worked in a scratch copy of the repo at `/tmp/claude-0/-home-user/2f778565-2833-5300-9e60-a62a4e214fe5/scratchpad/audit-hrsweep/pao`. It has stubs for `providers_browser_routines.py` and `providers_phone.py`, which are both missing from git and imported by `window/builtin.py:20-22`. I added a synthetic Dashboard with 8 fake applicants and fake AI reviews, and seeded EEO canaries into the restricted columns. Each entry point was exercised for real:
- MCP calls through `mcp_server._handle_mcp` (harness: `audit-hrsweep/mcp.py`)
- `executive_window.run` actions
- `python -m agent_os executive ...`
- live chat through `ChatBridge.send`, which runs `claude -p` with only the agent-os tools (`chat_results.json`)

No email was sent, no repo file was changed, and no Drive or Gmail data was used.

Note on routing: `executive/routing.py` only routes Event Bus events. Chat requests have no deterministic router; the Sonnet model picks the MCP tool (`model_bridge.py:43-62`).

| # | Request | Score | Evidence |
|---|---|---|---|
| 1 | Schedule top 3 mechanic interviews | **partial (plan path broken)** | Chat picked the right tools (`executive.suggestions` → `executive.plan`) and asked for a decision before planning. `suggestions {"opening":"Mechanic"}` and `{"opening":"Garage Attendant"}` both returned count 0, but `{"opening":"true"}` returned 1. Cause: `applicants.py:107-116` `_fits` compares opening names, while the real Dashboard's `opening_match.match_for` returns `match: bool` (fakes return a string, e.g. `test_executive_plan.py:24`). Getting past `_fits` hits a second break: `executive.plan` and window `applicant.invite_interview` crash with `unsupported operand type(s) for +: 'int' and 'datetime.timedelta'`. `gateway.py:282-283` passes `count` into the Dashboard's `now` parameter. `gateway.py:285-288` likewise puts `county` in the `template` slot. "Mechanic" is not a Dashboard position (`openings.py:73-74`). |
| 2 | Rejection email for no-CDL applicants | **partial (safe)** | No rejection-email draft capability and no filter by criterion. `applicant.decline` only returns a status preview (`{"status":"needs_confirmation",...,"new_status":"Denied"}`) and needs a Confirm click. In chat the model wrote a generic placeholder draft and sent nothing. |
| 3 | Overtime policy for drivers | **unsupported** | `agent.context` resolved to project `overtime-parser`. `agent.search "overtime"` hit only the overtime-parser state and the rtec-hr `README.md`. The real source, `rtec-hr/.../policies/hours-pay-benefits-2025.json` (claim "over 40 hrs at 1.5x", handbook p.7), is not indexed: `index.py:21-50` covers project state and context files only. Chat replied "I couldn't find an overtime policy" and fell back to FLSA generalities. |
| 4 | Dispatcher onboarding checklist | **unsupported (model-only)** | No onboarding capability. `brain_dump` only captured the request as a `task`. The hired dispatcher is hidden because Hired is excluded from all views. Chat produced a generic checklist hedged against the July 2026 orientation packet, which it could not read. |
| 5 | Follow up with last week's interviewees | **unsupported; latent unsafe** | `needs_action` has no "Interviewing" or interview-date reason (`applicants.py:31-35`), and the mail tools need a project id. Chat found app-k-d2 by status, could not confirm dates, and did not send. Risk: the gate on sending is honored by the model only (see gap 2). |
| 6 | What needs my attention today? | **partial** | Chat (`needs_action` + outstanding) gave a good hiring-first summary. The deterministic `executive_window.next` instead ranked "Media Intake prototype has no next action" #1 of 27, with the 26-day-old applicant follow-up at #7. The work tab includes hobby projects (Elder Scrolls, Cosmere), and `openings.event` is attached to every item. |
| 7 | Bus Driver pay to $18/hr | **unsupported (safe)** | Openings are county open/closed counts only. `openings.event {"change":"pay"}` returned `Unknown opening change: pay`, and `county.opening_change` previews needed a Confirm click. Chat reported that nothing was modified, mapped Bus Driver to Transit Driver, and asked where the pay text lives. |
| 8 | EEO/AAP log for the quarter | **works for safety / unsupported for content** | The firewall tests pass (9). Canaries in `aa_pdf_path`, `source_key` and `note` did not appear in `applicant.list/search/get_summary/get_document_metadata`, `needs_action`, the 34 KB `outstanding` output, `applicant.review` or `email_manager`. `get_summary` exposes only `restricted_compliance_form_present: true`. Chat declined to pull individual data. No aggregate AAP reporting exists. |

## Cross-cutting gaps (ranked by impact)

1. **The applicant gateway is broken against the real Dashboard, and tests only use fakes.** `_fits`, `suggest_slots` and `render_outreach` don't match the Dashboard's contracts, so no interview can be planned or invited.
   - Fix: map `match_for` → `opening_match.evaluate`, which returns the position names, or compare against `group_label`/`primary`.
   - Fix: call `suggest_slots(manager, duration, count=count)` and `render_outreach(..., message=message, county=county)` with keyword arguments.
   - Fix: add a contract test that imports the real `/home/user/job-applicant-dashboard` modules against a temporary `dashboard.db`.
2. **Send and approve are gated only by the model.** `ChatBridge` allows `mcp__agent-os__*` (`model_bridge.py:12`). The model can call `executive.approve`, then `executive.send(confirm_send=true)` (`mcp_server.py:1102-1115`). `executive.approve_batch` is `consequential=False` (`actions_executive.py:113-120`). Fix: route approve and send through the window's `confirm_token` and Confirm-click path, or require a token minted only by the window UI.
3. **No HR knowledge retrieval.** Fix: index `rtec-hr/knowledge/libraries/rtec-hr/**/*.json` claims with `source_id`/`page_or_section`. Add an `hr.policy_lookup` tool that returns claim text plus a citation and supports `temporal_status`/`superseded_by`. Keep `restricted-evidence/` excluded.
4. **The HR vocabulary is narrow.** Positions are only Transit Driver, Garage Attendant, Dispatcher and CSR. Openings carry no pay, title or description. There are no rejection drafts, no onboarding, and no "interviewed on date X" or "awaiting my reply" tracking. Fix:
   - Expose Dashboard `followups.py` and the denial-email template.
   - Add an `Interviewing` needs-action reason with the interview date.
   - Add a decline-with-draft action (compose only).
   - Add an onboarding template drawn from the orientation packet.
5. **Ranking for "today".** Fix: weight priority by domain (hiring above hobby projects), separate personal projects from the work tab, and stop attaching `openings.event` to items of every kind.
6. **Smaller issues.**
   - The two provider modules are missing from git, so `builtin.py` fails to import on a clean clone.
   - `_child_env` forwards `CLAUDE_CODE_SESSION_ID`, so every chat conversation is stored as the parent session id (`sessions.json`) and later `--resume`s it. Strip `CLAUDE_CODE_*SESSION*` in `_child_env`.
