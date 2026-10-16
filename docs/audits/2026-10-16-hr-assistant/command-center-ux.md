# Executive window UX audit (HR-manager persona, synthetic data)

Setup: a scratch copy of the repo in `scratchpad/audit-gui/repo`, with stubs for `providers_browser_routines` and `providers_phone`. `providers_phone` is also missing, which was not mentioned in the brief. `serve_synth.py` registers the real actions (openings, applicant decisions/compose, items) on synthetic providers, a fake Dashboard gateway, a fake model bridge (4 s delay) and a failing SMTP transport. It runs in two modes: `ok` and `broken`. Playwright/Chromium was run at 1366x768 (`d*`) and 390x844 (`p*`). Screenshots and `run.json` are in `scratchpad/audit-gui/`.

## Findings (ranked)

1. **BLOCKER: clicking an applicant does nothing except show an error.** Screenshots: `d02-applicant-click.png`, `p04-scrolled-to-chat.png`. The GUI sends `applicant_id: applicant.id` (executive.js:186, 212), but the server reads `applicant_ref`, so you get `ValueError: applicant_ref is required`. Even with that fixed, the panel reads `review.fields` and `review.decisions` (js:190-192), but `_review_panel` returns flat keys plus `available_decisions`. The panel would then show a name with no details and no Decline/Interview buttons. The row also shows `suggestion` (js:172), but the data has `recommendation`. **Fix:** use `applicant.applicant_ref` everywhere. Render score, recommendation, summary, strengths and concerns as a definition list, and build buttons from `available_decisions`. Show the label "AI suggestion — you decide".

2. **HIGH: approving or rejecting is unclear and unsafe.** Screenshot: `d06-pending-previews.png`. The card reads "Preview: applicant.decline: Kittitas - hiring" over raw JSON (`"applicant_ref": "a-102", "new_status": "Denied"`), with buttons "Confirm/Cancel" (js:690-729). The fixed card covers the chat input and the Capture button. It does not take focus and has no `role="alertdialog"`. After Confirm the only feedback is "Done." (`d07-after-confirm.png`). **Fix:** map action_id to plain copy. Title: "Decline Priya Raman (Kittitas)?" Body: "Her status will change to *Denied* in the Applicant Dashboard. No email is sent." Buttons: "Decline applicant" and "Keep as is". Success message: "Priya Raman declined." Add `role="alertdialog"`, `aria-labelledby`, and focus the primary button.

3. **HIGH: card buttons are overloaded and slow.** Screenshot: `d01-first-screen.png`. Each county card has 11 buttons. "Update county openings ⚠" (`openings.event`, `applies_to="*"`) appears on every item, even "Book dentist appointment". Every generic option (Dismiss, Snooze, Decline applicant, Accept) goes through `/api/option`, which is a full LLM call with a 600 s timeout (js:546-551, 588-619). So Dismiss takes as long as a model reply. The card-level "Decline applicant" also has no applicant chosen. **Fix:** skip `openings.event` in the loop at js:538. Call Dismiss/Snooze through `runAction` directly. Hide per-applicant actions at card level, because they belong in the review panel. Collapse the rest under a "More" button.

4. **HIGH: error messages are raw exceptions in a place people miss.** Screenshots: `d10-provider-error.png`, `d11-chat-error.png`. Provider failures show in 12px grey at the top right, for example "applicants: FileNotFoundError: Applicant Dashboard database not found: C:\Users\…\dashboard.db" (html:14, js:78-90). That text also uses the internal word "provider". Chat failures look like a normal reply bubble: "FileNotFoundError: [WinError 2]…" (js:652). Errors stay on screen after later successful actions (js:651 never clears them). There is no retry. **Fix:** add a red banner with `role="alert"`, mapped copy and a Retry button. Example banner: "Couldn't load applicants — the Applicant Dashboard file wasn't found. [Retry] [Details]". For chat: "The assistant isn't available right now. Your message wasn't lost — [Try again]". Add a `bubble error` style and call `clearError()` in `handleChatSend`.

5. **HIGH: phone layout.** Screenshots: `p01-first-screen.png`, `p05-phone-after-chat.png`. The `.executive-container` has `height:100vh; overflow:hidden` (html:61-62) and the sticky topbar adds height on top of that, so the document is 885 px in an 844 px window. The Capture button sits off-screen. Items get a 328 px inner scroll box and chat gets 228 px, giving two nested scroll traps. The desktop window also overflows (809 vs 768, Capture is cut off). **Fix:** use `height: calc(100vh - 41px)`. Under `@media (max-width:1024px)` use `.executive-container{height:auto;overflow:visible}` and `.chat-log{max-height:60vh}`.

6. **MEDIUM: internal terms on the screen.** Screenshot: `d01`. The terms are:
   - "Rank 6 of 6 — priority desc, then age_days desc, then queue item id asc" (js:505)
   - "Source: applicant_executive" and "Candidate memory" (js:513)
   - "…recorded in state.json"
   - "decision_candidate staged from:"
   - "Message the model" (html:42)
   - "Brain dump"
   - "Rescue"
   - "run `agent-os executive rescue` again" (src/agent_os/executive/rescue.py:40)

   **Fix:** drop the ranking clause and show "Priority 1 of 6". Hide source labels that are internal. Use the placeholder "Ask me anything — e.g. 'Draft a job description for an Executive Assistant'". Rename "Brain dump" to "Quick notes" and "Rescue" to "Just one thing". Rescue copy: "Finish this, then press Just one thing again."

7. **MEDIUM: the first screen gives no help.** Screenshot: `d01`. There is no heading, no greeting and no summary such as "3 things need you today", and the empty chat column has no example prompts. **Fix:** add an `<h1>` "Today" with a count line, plus 3-4 suggestion chips in the empty chat: "Find top applicants", "Write a job description", "What needs me today?".

8. **MEDIUM: the busy state is unclear.** Screenshot: `d03-chat-busy.png`. The overlay says only "Loading…" for the whole model call (4.5 s with the fake bridge, minutes when real), with no estimate and no cancel. The user's bubble also stretches to fill the log (the grid has no `align-content:start`, html:136-144). **Fix:** show "Writing a reply… this can take up to a minute" next to the composer. Add `align-content:start` to `.chat-log`.

9. **MEDIUM: Rescue contradicts itself.** Screenshot: `d08-rescue.png`. It shows one item and then "No work items" underneath (js:858-861). **Fix:** hide the list when no item matches. Change "24 other item(s) hidden" to "24 other things are waiting — showing just one."

10. **LOW: accessibility details.**
    - The chat input has no label or aria-label (html:42).
    - The tabs have no `role="tabpanel"`/`aria-controls` and no arrow-key support, and Rescue sits inside the tablist without a tab role (html:21-24).
    - The ⚠ is CSS-only, so screen readers don't hear it. Add `aria-label="(asks before doing)"`.
    - `--warn` #b7791f on white is 3.64:1, which fails for the 13-14px preview title. Use #8a5a12.
    - Default focus rings are visible (`d09-keyboard-focus.png`), which is good. (The "1 applicants" text in the screenshots comes from my synthetic data, not the app.)

Latency: page load is 0.14-0.24 s and items appear instantly. The real cost is the LLM round-trip on every option button (finding 3).
