# Agent OS for Firefox

One extension that replaces the Tampermonkey userscript and the Reddit Subreddit Hider add-on:

- **Capture**: the Universal Capture userscript (`../userscripts/agent-os-universal-capture.user.js`) is bundled unchanged at build time and runs on a GM_* shim (`src/content/gm-shim.js`). That covers per-item save buttons, the browser journal, Discord indexing, Amazon cart import, and every menu command (toolbar popup → *Capture tools*).
- **Content filters**: hide items by rule on Reddit (subreddit, user, domain, flair, keyword, promoted, NSFW), Nexus Mods (tag, uploader/author, category, game, adult, translations — on by default, detected from Nexus's Translation tag, translated-title wording and language-only tags; tags come from the public Nexus GraphQL API and are cached for 3 days), AO3 (tag, fandom, author, rating, warning, category, language, fandom-count, word-count, WIP), XenForo forums such as SpaceBattles, Sufficient Velocity and QQ (author, prefix, tag, forum; posts by hidden authors collapse inside threads), FanFiction.net, YouTube (channel, keyword, Shorts), Steam Workshop, Google/DuckDuckGo/Bing results (domain), Amazon (sponsored), and any custom site defined by CSS selectors.
- **Old Reddit**: `www.`, `new.` and `np.reddit.com` page loads redirect to `old.reddit.com`. Pages old Reddit cannot show are left alone (`/media`, share links `/s/…`, chat, settings). Add `?aos_new=1` to a URL to open it on new Reddit once. You can toggle this in the popup or options.
- **Agent OS bridge**: pairs with `agent-os browser-bridge` through a native-messaging helper (no token pasting), starts the bridge when it is down, registers each tab as a session, and executes `browser.execute` commands. The safety gate always refuses typing into credential, payment or identity fields, and pauses consequential clicks (submit/send/delete/buy…) with `approval_required` unless the command is approved.
- **Preference sync**: rule changes are sent to the bridge as a `content-filters` / `rules_snapshot` event, so Agent OS knows what you hide.

## Scheduled tasks (recorded clicks and sign-ins)

*Options → Scheduled tasks* sets up a task: a name, a start URL, when to run, and optionally a login. When to run can be days of the week at a time, once on a date, every N minutes, or manual only. Tick *Random variance* to start each run at a random moment 0–6 minutes after the set time (re-rolled every run). To change an existing task, click *Edit* next to it in the options page or in the toolbar popup (*Scheduled tasks → Edit*). Saving keeps its recorded steps and saved login. *Save & record steps* opens a dedicated window at the start URL with a red recorder toolbar. Do the task once there, then click *Finish & save*.

- **Recorded:** clicks, typed text, dropdown choices, checkboxes and Enter presses, across page loads. Steps can be reordered, removed, given waits, or switched between typed text and the saved login afterwards.
- **Never recorded:** passwords. Typing into a password field becomes "enter saved password". Username/email fields become "enter saved username" when the task has a saved login. One-time codes and card fields are marked as needing manual entry.
- **Credentials:** saved logins live in Windows Credential Manager (service `agent-os-browser-tasks`) through the native helper, never in extension storage. The background releases a saved value only to the tab replaying that task, at the step that asks for it.
- **Runs:** `browser.alarms` starts the task in a background tab, or its own window if you choose that, and the tab closes after a successful run. A failed run keeps its tab open, shows a red **!** on the toolbar icon and is logged with the step that failed. Runs missed while Firefox was closed run at startup if they are under 6 hours late. Every run is reported to Agent OS as a `scheduled-tasks` / `task_run` event containing names and status only.
- **Limits:** a login that needs a CAPTCHA or a one-time code cannot be automated. Sign-in forms inside iframes and links that open new tabs are not recorded.

## AI browser routines

A routine is a plain-language task, such as "list the 5 newest Skyrim SE mods with authors" or "check my order status every morning", with a start page and an optional schedule (`hourly`, `every 30m`, `daily 08:00`, `weekdays 09:00`, `mon,thu 18:30`). Manage routines in *Options → AI routines*, from the popup (*AI routines → Run* / *New routine from this page*), from the Executive window chat, or through the MCP tools `browser.routines`, `browser.routine_save`, `browser.routine_run`, `browser.routine_runs` and `browser.routine_delete`.

How a run works (`src/agent_os/browser_routines.py`):

1. Agent OS opens a background tab at the start page through the extension.
2. Claude Code runs headless on your subscription (`claude -p`, Sonnet by default; Haiku or Opus per routine) with only the four `browser.*` MCP tools available.
3. A per-run policy, enforced in `browser_control.py` rather than in the prompt, confines the model to its own tab, the routine's allowed domains and its own commands. It cannot open other tabs or approve its own consequential actions.
4. When the safety gate pauses a click (submit, send, buy, delete…), the run stops and an approval item appears in the Executive window. *Approve this action* (with Confirm) allows that exact action once, and the run resumes in the same Claude session. *Decline* ends the run.
5. Results the routine flags, failures and blocked runs (for example, a login being required) appear as Executive items. The tab closes when the run ends.

Schedules are checked once a minute by the extension through the native helper, so routines run while Firefox is open. State lives in `.agent-os/browser-routines/` (gitignored). CLI: `python -m agent_os.browser_routines list|save|run|runs|tick`.

Ways to hide something: hover an item and click **⊘**, or right-click it (or any link to a subreddit, tag, user, game or channel) and pick **Agent OS → Hide…**. The bottom-left pill counts hidden items; click it (or press Alt+Shift+H) to show them with the reason, and click a reason strip to remove that rule.

Saved links ("+ Agent OS") are mirrored to the Google Sheet *Agent OS Intake*, one tab per kind of link, through the Apps Script receiver in `browser/apps-script/agent-os-intake.gs`. Its `/exec` URL is machine-managed in `.agent-os/browser-extension-settings.json` (`sheetEndpoint`), which the native helper hands to the extension, so it never ships in the public build. Browser Journal and Discord events are not sent to the sheet.

Discord messages indexed by the extension are exported by the bridge every minute to `.agent-os/intake/discord/<server>/<channel>/<YYYY-MM>.jsonl` (`discord-intake-v1`, one message per line; `python agent.py discord-export` runs it on demand).

## Build and test

    python tools/build.py              # dist/agent-os-firefox/ and dist/agent-os-firefox-<version>.xpi
    npm install                        # jsdom, used only by the tests
    npm test                           # build plus 30+ unit/jsdom/e2e tests
    npm run lint                       # Mozilla web-ext lint

Optional tests: `AOS_NETWORK_TESTS=1` calls the live Nexus API. `AOS_LIVE_FIXTURES=<dir>` runs the adapters against saved real pages (`sb_forum.html`, `sv_forum.html`, `qq_forum.html`, `ddg.html`). The bridge e2e test runs the real bridge server on a temporary database.

## Install

1. Register the native helper once (per user, no admin rights):

       python tools/install_native_host.py

2. Release Firefox only installs signed extensions. Sign the build as an unlisted (self-distributed) add-on:

       python tools/build.py --sign

   This needs AMO API credentials from https://addons.mozilla.org/developers/addon/api/key/. Store them in Windows Credential Manager (`keyring` service `agent-os-amo`, users `api_key` and `api_secret`) or set `WEB_EXT_API_KEY` / `WEB_EXT_API_SECRET`. The signed `.xpi` lands in `dist/signed/`. Open it in Firefox to install.

   Every code change needs a new signed version (bump `version` in `src/manifest.json`); rule and setting changes do not. `python tools/build.py --sign --install` signs the build, installs it into the default Firefox profile (staged until the next Firefox start if Firefox is running), and opens an update prompt in the running Firefox. `--install-restart` instead installs with no prompt: it force-closes Firefox (crash recovery restores every window and tab), replaces the extension in the profile, clears `addonStartup.json.lz4` so Firefox re-reads it, and starts Firefox again; run it between browser jobs, since open pages reload. Accepting an older pending update prompt downgrades the extension, so check the version afterwards. The native helper (`native/`) runs from the repo, so changes to it apply without re-signing.

   For a quick trial without signing: `about:debugging` → *This Firefox* → *Load Temporary Add-on…* → `dist/agent-os-firefox/manifest.json` (removed when Firefox restarts).

3. Disable the Tampermonkey copy of *Agent OS Universal Capture* and the *Reddit Subreddit Hider* add-on. Userscript v3.13.0+ stands down automatically when it sees the extension, but older copies do not.

If you had a remote (Apps Script) capture endpoint configured in Tampermonkey, enter it again under *Options → Agent OS & capture*. The bridge pairs on its own.

## Layout

    src/manifest.json           MV2 (persistent background, webRequest redirect, native messaging)
    src/background.js           filter state, Nexus API cache, GM_xmlhttpRequest proxy, bridge sessions/commands, menus, redirect
    src/lib/filter-core.js      rule model + matching (shared with tests)
    src/lib/sites.js            site adapters, link-derived hide options, old-Reddit redirect
    src/content/filter.js/.css  in-page hiding, ⊘ buttons, counter, context-menu answers
    src/content/gm-shim.js      Tampermonkey API on browser.storage.local ("gm:" keys)
    src/content/executor.js     bridge DOM actions + safety gate
    src/popup, src/options      toolbar popup and settings page
    native/                     native-messaging host (bridge token handoff + auto-start)
    tools/                      build/sign and native-host installer
