/*
 * Agent OS Shopping collector: background side.
 *
 * Replaces agent-os-shopping's Tampermonkey collector userscript. The person
 * marks ONE tab as the collector (popup or right-click menu). That tab gets a
 * second bridge session, separate from its normal Agent OS session, that:
 *
 *   - advertises capabilities.shopping_collector, which is how Agent OS
 *     Shopping finds it (browser_collection.AgentOSBrowserClient);
 *   - accepts only navigate / wait / scroll / extract, and refuses a whole
 *     command containing anything else (no click, type, open_tab...);
 *   - pauses on a CAPTCHA or "verify you are human" page and reports
 *     approval_required instead of trying to pass it;
 *   - answers in the userscript's result shape: { url, title, steps: [{ kind, data }] }.
 *
 * Pacing and daily caps stay in Agent OS Shopping, which already enforces them.
 *
 * Loaded after background.js and shares its globals (getLocal, setLocal,
 * bridgeFetch, installId, waitForTabComplete, sendToTab, VERSION).
 */
"use strict";

var CollectorCore = globalThis.AgentOsCollectorCore;
var COLLECTOR_KEY = "agent_os_shopping_collector_v1";
var COLLECTOR_COMMAND_LIMIT_MS = 120000;
var collectorBusy = new Set();
var collectorBeat = new Map();
var collectorPoll = new Map();
var collectorWrite = Promise.resolve();

async function collectorState() {
    var state = await getLocal(COLLECTOR_KEY, null);
    return state && typeof state === "object" && state.tabs ? state : { tabs: {} };
}

function mutateCollector(fn) {
    collectorWrite = collectorWrite.then(async function () {
        var state = await collectorState();
        var result = await fn(state);
        await setLocal(COLLECTOR_KEY, state);
        return result;
    });
    return collectorWrite;
}

async function collectorSessionId(tabId) {
    return "firefox-" + (await installId()) + "-collector-" + tabId;
}

function collectorBadge(tabId, text, warn) {
    return browser.tabs.sendMessage(tabId, { type: "aos-collector-badge", text: text, warn: Boolean(warn) })
        .catch(function () { /* page still loading; the badge is re-sent when it completes */ });
}

var COLLECTOR_IDLE = "Agent OS Shopping collector tab - idle";
var COLLECTOR_PAUSED = "Agent OS Shopping paused: this site is asking for a human check. Handle it yourself if you like, " +
    "then choose 'Resume Shopping collector' in the Agent OS menu.";

async function setCollector(tabId, on) {
    var tab = await browser.tabs.get(tabId);
    if (on && !/^https?:/i.test(tab.url || "")) throw new Error("open a normal web page first");
    await mutateCollector(function (state) {
        if (on) {
            Object.keys(state.tabs).forEach(function (id) { delete state.tabs[id]; });   // one collector tab at a time
            state.tabs[tabId] = { paused: false, since: nowIso() };
        } else {
            delete state.tabs[tabId];
        }
    });
    collectorBeat.delete(tabId);
    collectorPoll.delete(tabId);
    if (!on) {
        try {   // tell Agent OS right away instead of letting the session go stale
            await bridgeFetch("/session/heartbeat", { method: "POST", body: await collectorHeartbeat(tab, { stopped: true }) });
        } catch (error) { /* offline: the session expires on its own */ }
    }
    await collectorBadge(tabId, on ? COLLECTOR_IDLE : "Agent OS Shopping collector stopped in this tab");
    return { ok: true, collector: on };
}

async function resumeCollector(tabId) {
    await mutateCollector(function (state) { if (state.tabs[tabId]) state.tabs[tabId].paused = false; });
    collectorBeat.delete(tabId);
    await collectorBadge(tabId, COLLECTOR_IDLE);
    return { ok: true };
}

async function collectorHeartbeat(tab, extra) {
    var paused = Boolean(extra && extra.paused);
    var stopped = Boolean(extra && extra.stopped) || paused;
    return {
        session_id: await collectorSessionId(tab.id),
        url: tab.url,
        title: tab.title || "",
        site: (function () { try { return new URL(tab.url).hostname; } catch (error) { return ""; } })(),
        visibility: tab.active ? "visible" : "hidden",
        focused: false,
        user_agent: navigator.userAgent,
        capabilities: {
            client: "agent-os-firefox-extension",
            version: VERSION,
            tab_id: tab.id,
            shopping_collector: !stopped,     // Shopping only picks a session with this set
            collector_paused: paused,
            collector_version: 2,
            ops: stopped ? [] : CollectorCore.OPS.slice()
        }
    };
}

async function reportCollector(commandId, state, result, error) {
    await bridgeFetch("/command-result", {
        method: "POST",
        body: { command_id: commandId, state: state, result: result, error: error || "" }
    });
}

async function pauseCollector(tabId) {
    await mutateCollector(function (state) { if (state.tabs[tabId]) state.tabs[tabId].paused = true; });
    await collectorBadge(tabId, COLLECTOR_PAUSED, true);
    var tab = await browser.tabs.get(tabId).catch(function () { return null; });
    if (tab) {   // withdraw the collector capability now, so Shopping stops sending work instead of timing out
        await bridgeFetch("/session/heartbeat", { method: "POST", body: await collectorHeartbeat(tab, { paused: true }) })
            .catch(function () { /* offline: the session goes stale on its own */ });
    }
}

// Runs one Shopping command in the collector tab. Never throws; always reports.
async function runCollectorCommand(tabId, command) {
    if (collectorBusy.has(tabId)) return;
    collectorBusy.add(tabId);
    var actions = command.actions || [];
    var steps = [];
    var started = Date.now();
    try {
        var problem = CollectorCore.validate(actions);
        if (problem) {
            await reportCollector(command.command_id, "failed", null, problem);
            return;
        }
        for (var i = 0; i < actions.length; i += 1) {
            if (Date.now() - started > COLLECTOR_COMMAND_LIMIT_MS) throw new Error("collector command expired");
            var action = actions[i];
            if (action.op === "navigate") {
                await collectorBadge(tabId, "Agent OS Shopping: loading " + new URL(action.url).hostname + " ...");
                await browser.tabs.update(tabId, { url: action.url });
                await waitForTabComplete(tabId, 20000);
                continue;
            }
            var outcome = await sendToTab(tabId, { type: "aos-collect", action: action });
            if (outcome && outcome.human_check) {
                await pauseCollector(tabId);
                await reportCollector(command.command_id, "approval_required", { url: outcome.url }, "human_verification_required");
                return;
            }
            if (!outcome || outcome.ok === false) throw new Error(outcome && outcome.error || "the page did not answer");
            if (outcome.step) steps.push(outcome.step);
        }
        var tab = await browser.tabs.get(tabId);
        await reportCollector(command.command_id, "completed", { url: tab.url, title: tab.title, steps: steps });
        await collectorBadge(tabId, COLLECTOR_IDLE);
    } catch (error) {
        var current = await browser.tabs.get(tabId).catch(function () { return {}; });
        await reportCollector(command.command_id, "failed", { url: current.url || "" }, String(error && error.message || error))
            .catch(function () { /* bridge down: Shopping times the command out */ });
        await collectorBadge(tabId, "Agent OS Shopping collector tab - idle (last command failed)");
    } finally {
        collectorBusy.delete(tabId);
    }
}

// Called from bridgeTickInner (background.js) once the bridge is paired.
async function collectorTick() {
    var state = await collectorState();
    var ids = Object.keys(state.tabs);
    var now = Date.now();
    for (var i = 0; i < ids.length; i += 1) {
        var key = ids[i];
        var tabId = Number(key);
        var entry = state.tabs[key];
        var tab = await browser.tabs.get(tabId).catch(function () { return null; });
        if (!tab) {                                    // closed, or ids changed after a browser restart
            await mutateCollector(function (s) { delete s.tabs[key]; });
            continue;
        }
        if (entry.paused) continue;                    // no heartbeat: Shopping sees no collector until you resume
        if (!collectorBeat.has(tabId) || now - collectorBeat.get(tabId) > 20000) {
            await bridgeFetch("/session/heartbeat", { method: "POST", body: await collectorHeartbeat(tab) });
            collectorBeat.set(tabId, now);
        }
        if (collectorBusy.has(tabId) || (collectorPoll.has(tabId) && now - collectorPoll.get(tabId) < 3000)) continue;
        collectorPoll.set(tabId, now);
        var body = await bridgeFetch("/commands?session_id=" + encodeURIComponent(await collectorSessionId(tabId)));
        var command = (body.commands || [])[0];       // one at a time, like the userscript
        if (command) runCollectorCommand(tabId, command);
    }
}

async function collectorStatus(tabId) {
    var state = await collectorState();
    var ids = Object.keys(state.tabs);
    var entry = state.tabs[tabId];
    return {
        ok: true,
        here: Boolean(entry),
        paused: Boolean(entry && entry.paused),
        elsewhere: !entry && ids.length > 0,
        tab_id: ids.length ? Number(ids[0]) : null
    };
}

function collectorMessage(message, sender) {
    var tabId = Number(message.tab_id || (sender && sender.tab && sender.tab.id));
    if (!tabId) return Promise.resolve({ ok: false, error: "no tab" });
    var work;
    if (message.type === "collector-set") work = setCollector(tabId, Boolean(message.on));
    else if (message.type === "collector-resume") work = resumeCollector(tabId);
    else work = collectorStatus(tabId);
    return work.catch(function (error) { return { ok: false, error: String(error && error.message || error) }; });
}

browser.tabs.onRemoved.addListener(function (tabId) {
    mutateCollector(function (state) { delete state.tabs[tabId]; });
    collectorBeat.delete(tabId);
    collectorPoll.delete(tabId);
});

// A reload or navigation removes the in-page badge; put it back once the page is ready.
browser.tabs.onUpdated.addListener(async function (tabId, info) {
    if (info.status !== "complete") return;
    var state = await collectorState();
    var entry = state.tabs[tabId];
    if (!entry || collectorBusy.has(tabId)) return;
    collectorBadge(tabId, entry.paused ? COLLECTOR_PAUSED : COLLECTOR_IDLE, entry.paused);
});
