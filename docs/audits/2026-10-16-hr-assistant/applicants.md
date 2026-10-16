# Audit: "Give me some good applicants for the open Bus Driver opening"

Setup: I made scratch copies of both repos in `scratchpad/audit-applicants/{pao,dash}`. The synthetic `dashboard.db` holds 8 fake applicants and 6 AI reviews. A garage xlsx defines the Laurel, Knox, Whitley and Clay groups. The open groups are Laurel and Knox, plus the Dispatcher office position. The env vars are in `audit-applicants/env.sh`. I stubbed `providers_browser_routines.py` and `providers_phone.py`. `providers_phone` is **also missing from git** (builtin.py:24), and without it the window server will not start.

## 1) What works today
- **County cards in the GUI.** `agent-os executive window --port 8791 --no-open`, then `GET /api/items?tab=work` with the `X-Agent-OS-Token` header, returns `county:Laurel` with Casey 91, Alex 88 and Harper (no score). It also returns `county:Knox`. This ranked list is the only working "good applicants" view, and executive.js:171 renders the scores.
- **Ranking from Python.** `applicants.county_candidates()` and `open_county_groups()` rank correctly by Dashboard AI score.
- **Chat reaches Claude.** `POST /api/chat` calls `claude -p` with the agent-os MCP server and answers in about 11s.
- **Tests pass.** The 38 applicant/executive tests pass.

## 2) Where the user gets stuck
**B1 (blocker): suggestions and planning never match a real opening.** `applicants._fits` (executive/applicants.py:107-115) compares the opening name to `match["match"]`. The real `opening_match.match_for` returns `match` as a **bool**, and `alternates` as `{"group":...}` dicts, which `_opening_name` can't read. Test fixtures use strings (tests/test_executive_suggestions.py:30), so the tests hide the bug.
- Repro: `agent-os executive suggestions "Bus Driver"`, `"Transit Driver"`, `"Dispatcher"` and `"Laurel"` all return `count: 0`. `suggestions "true"` returns all 5 reviewed applicants.
- The same bug blocks planning. `executive plan --opening Laurel --applicant-refs '["ref-k1","ref-k3"]'` returns "no applicant can be planned for this opening" (applicants.py:419). It also affects send-time recheck (applicants.py:542).

**B2 (blocker): chat answers wrongly.** With B1 and M1 in place, chat tells the user false things.
- The Bus Driver request answered: "Dashboard has no AI reviews for Bus Driver applicants... no openings configured."
- The dispatcher question answered: "I can't tell you who to interview... The Dashboard has no AI reviews for dispatcher applicants." In fact the reviews score 84, 65 and 91.
- The model also repeats MCP descriptions that steer it away from ranking (mcp_server.py:558 and 569: "not a ranking... tool").
- There is no natural-language route to ranking at all. `/api/chat` (server.py:173-179) only parses opening open/close events and sends everything else to the LLM. `executive/routing.py` is an event-bus router, not a chat router.

**M1 (major): openings are read from the wrong folder.** `rtec_applicants.openings_status` (rtec_applicants.py:804) reads `_project_root()/Config`. The Dashboard keeps Config under its runtime dir (app_paths.CONFIG_DIR). When the runtime is separate, which is the run_dashboard.bat setup, it returns `configured: False`.

**M2 (major): office positions get no ranking view.** `open_counties` and `county_items` only cover Transit Driver county groups. An open Dispatcher position therefore has no card or ranking.
- Dispatcher-only applicant Emery appears in the **Knox driver** card at 84, ahead of driver Blair at 72. The cause is that `_fits_county` (applicants.py:304) matches on home county regardless of position.

**m1 (minor): "County" suffix and bus-driver synonym.** `county_candidates("Laurel County")` returns 0 because the "County" suffix is not stripped. "Bus Driver" is not mapped to "Transit Driver" in Agent OS. The Dashboard regex happens to catch it because it matches `\bdriver\b`.

## 3) Recommended changes (by user impact)
1. **Fix `_fits` in executive/applicants.py.** Treat `match` as a bool. Map the opening text to Dashboard terms: a county via `match["primary"]`/`groups`/`alternates[].group`, and a position via `openings.match_positions` (so Bus/Transit/Driver become Transit Driver, plus Dispatcher/CSR/Garage Attendant). Update the test fixtures to the real `match_for` shape.
2. **Rewrite `suggestions()` around opening type.** For a position, return ranked `reviewable()` rows whose `match_positions(position)` includes it and whose `match` is true. For a county, delegate to `county_candidates`. Include unreviewed applicants with `score: None`, as the county path already does.
3. **Add a deterministic chat intent in server.py `/api/chat`.** Add a `parse_candidate_query()` next to `actions_openings.parse_opening_event` that recognises "good applicants for X" and "who should I interview for X", and answer from `suggestions()` before falling back to the model.
4. **Clarify the MCP descriptions.** Reword `executive.suggestions` and the `applicant.list` description at mcp_server.py:558 to point the model to `executive.suggestions` for "who to interview" questions.
5. **Fix the openings path.** Use `_runtime_root()` in `openings_status`.
6. **Add office-position cards and fix county filtering.** Add office-position groups to `open_county_groups`/`county_items`, and require a Transit Driver position in `_fits_county`.
7. **Normalise county input.** Strip a trailing "County" in `_clean_opening`/`_norm` for county lookups.
8. **Commit the missing module.** Commit `providers_phone.py`, or guard its import in builtin.py.
