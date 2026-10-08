/*
 * Agent OS for Firefox: background page.
 *
 * - Owns the content-filter state (serialised writes from every tab).
 * - Enriches Nexus Mods tiles through the public Nexus GraphQL API (cached).
 * - Proxies GM_xmlhttpRequest for the bundled Universal Capture userscript.
 * - Pairs with the local Agent OS bridge through the native-messaging host
 *   (token handoff + auto-start), registers every tab as a bridge session
 *   and executes queued browser.execute commands.
 * - Builds the dynamic "Agent OS → Hide…" context menu.
 */
"use strict";

var Core = globalThis.AgentOsFilterCore;
var VERSION = browser.runtime.getManifest().version;
var GM_SETTINGS_KEY = "gm:agent_os_capture_settings_v1";
var INSTALL_ID_KEY = "agent_os_install_id";
var NEXUS_CACHE_KEY = "agent_os_nexus_cache_v1";
var NATIVE_HOST = "agent_os_native";
var DEFAULT_BRIDGE = "http://127.0.0.1:8766/api/v1/browser/batch";
var NEXUS_GRAPHQL = "https://api-router.nexusmods.com/graphql";
var NEXUS_TTL_MS = 3 * 24 * 3600 * 1000;
var NEXUS_MISS_TTL_MS = 6 * 3600 * 1000;

// -- small helpers --------------------------------------------------------------

function sleep(ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
}

function nowIso() {
    return new Date().toISOString();
}

async function getLocal(key, fallback) {
    var res = await browser.storage.local.get(key);
    return res[key] === undefined ? fallback : res[key];
}

async function setLocal(key, value) {
    var update = {};
    update[key] = value;
    await browser.storage.local.set(update);
}

// -- filter state (single writer) -------------------------------------------------

var filterWrite = Promise.resolve();

function mutateFilters(fn) {
    filterWrite = filterWrite.then(async function () {
        var state = Core.normalizeState(await getLocal(Core.STORAGE_KEY, null));
        var result = fn(state);
        await setLocal(Core.STORAGE_KEY, state);
        return result;
    });
    return filterWrite;
}

async function getFilters() {
    return Core.normalizeState(await getLocal(Core.STORAGE_KEY, null));
}

// -- capture userscript settings (shared with the GM shim) ------------------------

async function captureSettings() {
    var saved = await getLocal(GM_SETTINGS_KEY, {});
    return Object.assign({
        endpoint: "",
        token: "",
        device: "",
        bridgeEnabled: true,
        bridgeEndpoint: DEFAULT_BRIDGE,
        bridgeCaptureEndpoint: DEFAULT_BRIDGE.replace(/\/batch$/, "/capture"),
        bridgeToken: ""
    }, saved && typeof saved === "object" ? saved : {});
}

async function updateCaptureSettings(patch) {
    var saved = await getLocal(GM_SETTINGS_KEY, {});
    await setLocal(GM_SETTINGS_KEY, Object.assign({}, saved || {}, patch));
}

async function installId() {
    var id = await getLocal(INSTALL_ID_KEY, "");
    if (!id) {
        id = Math.random().toString(36).slice(2, 10);
        await setLocal(INSTALL_ID_KEY, id);
    }
    return id;
}

// -- GM_xmlhttpRequest proxy -------------------------------------------------------

async function gmXhr(message) {
    var controller = new AbortController();
    var timer = message.timeout ? setTimeout(function () { controller.abort(); }, message.timeout) : null;
    var method = String(message.method || "GET").toUpperCase();
    try {
        var response = await fetch(message.url, {
            method: method,
            headers: message.headers || {},
            body: method === "GET" || method === "HEAD" ? undefined : message.data,
            credentials: "include",
            signal: controller.signal
        });
        var text = await response.text();
        var headerLines = [];
        response.headers.forEach(function (value, name) { headerLines.push(name + ": " + value); });
        return {
            status: response.status,
            statusText: response.statusText,
            responseText: text,
            response: text,
            finalUrl: response.url,
            responseHeaders: headerLines.join("\r\n"),
            readyState: 4
        };
    } catch (error) {
        if (error && error.name === "AbortError") return { error: "timeout", status: 0 };
        return { error: "network", status: 0, message: String(error && error.message || error) };
    } finally {
        if (timer) clearTimeout(timer);
    }
}

// -- Nexus Mods enrichment ---------------------------------------------------------

var nexusCache = null;
var nexusSaveTimer = null;

async function loadNexusCache() {
    if (!nexusCache) {
        nexusCache = await getLocal(NEXUS_CACHE_KEY, null) || { games: {}, mods: {} };
        nexusCache.games = nexusCache.games || {};
        nexusCache.mods = nexusCache.mods || {};
    }
    return nexusCache;
}

function saveNexusCacheSoon() {
    if (nexusSaveTimer) return;
    nexusSaveTimer = setTimeout(async function () {
        nexusSaveTimer = null;
        var keys = Object.keys(nexusCache.mods);
        if (keys.length > 6000) {
            keys.sort(function (a, b) { return nexusCache.mods[a].at - nexusCache.mods[b].at; })
                .slice(0, keys.length - 5000)
                .forEach(function (k) { delete nexusCache.mods[k]; });
        }
        await setLocal(NEXUS_CACHE_KEY, nexusCache);
    }, 2000);
}

async function nexusGraphql(query) {
    var response = await fetch(NEXUS_GRAPHQL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query }),
        credentials: "omit"
    });
    if (!response.ok) throw new Error("Nexus API HTTP " + response.status);
    var body = await response.json();
    if (body.errors && !body.data) throw new Error(body.errors[0] && body.errors[0].message || "Nexus API error");
    return body.data || {};
}

async function nexusGameIds(domains) {
    var cache = await loadNexusCache();
    var missing = domains.filter(function (d) { return !cache.games[d]; });
    for (var i = 0; i < missing.length; i += 20) {
        var chunk = missing.slice(i, i + 20);
        var query = "{" + chunk.map(function (domain, index) {
            return "g" + index + ": game(domainName: " + JSON.stringify(domain) + ") { id domainName }";
        }).join(" ") + "}";
        try {
            var data = await nexusGraphql(query);
            chunk.forEach(function (domain, index) {
                var game = data["g" + index];
                if (game && game.id) cache.games[domain] = game.id;
            });
        } catch (error) {
            console.warn("[Agent OS] Nexus game lookup failed", error);
        }
    }
    return cache.games;
}

var nexusInflight = new Map();

async function nexusLookup(items) {
    var cache = await loadNexusCache();
    var now = Date.now();
    var result = {};
    var missing = [];
    items.forEach(function (item) {
        if (!item || !item.game || !item.modId) return;
        var key = String(item.game).toLowerCase() + ":" + item.modId;
        var entry = cache.mods[key];
        if (entry && now - entry.at < (entry.data ? NEXUS_TTL_MS : NEXUS_MISS_TTL_MS)) {
            result[key] = entry.data;
        } else if (nexusInflight.has(key)) {
            missing.push({ key: key, wait: nexusInflight.get(key) });
        } else {
            missing.push({ key: key, game: String(item.game).toLowerCase(), modId: Number(item.modId) });
        }
    });

    var toFetch = missing.filter(function (m) { return !m.wait; });
    if (toFetch.length) {
        var job = (async function () {
            var games = await nexusGameIds(Array.from(new Set(toFetch.map(function (m) { return m.game; }))));
            var domainById = {};
            Object.keys(games).forEach(function (domain) { domainById[games[domain]] = domain; });
            var ids = toFetch.filter(function (m) { return games[m.game]; });
            for (var i = 0; i < ids.length; i += 50) {
                var chunk = ids.slice(i, i + 50);
                var list = chunk.map(function (m) { return "{gameId: " + games[m.game] + ", modId: " + m.modId + "}"; }).join(", ");
                var query = "{ legacyMods(ids: [" + list + "]) { nodes { modId gameId name summary adultContent author " +
                    "uploader { name } modCategory { name } game { domainName name } tags { name } } } }";
                var found = {};
                try {
                    var data = await nexusGraphql(query);
                    ((data.legacyMods || {}).nodes || []).forEach(function (node) {
                        var domain = domainById[node.gameId] || (node.game && node.game.domainName || "").toLowerCase();
                        found[domain + ":" + node.modId] = {
                            name: node.name || "",
                            summary: node.summary || "",
                            adult: Boolean(node.adultContent),
                            author: node.author || "",
                            uploader: node.uploader && node.uploader.name || "",
                            category: node.modCategory && node.modCategory.name || "",
                            gameName: node.game && node.game.name || "",
                            tags: (node.tags || []).map(function (t) { return t.name; }).filter(Boolean)
                        };
                    });
                } catch (error) {
                    console.warn("[Agent OS] Nexus mod lookup failed", error);
                    continue; // leave uncached so it is retried later
                }
                chunk.forEach(function (m) {
                    cache.mods[m.key] = { at: Date.now(), data: found[m.key] || null };
                });
            }
            toFetch.filter(function (m) { return !games[m.game]; }).forEach(function (m) {
                cache.mods[m.key] = { at: Date.now(), data: null };
            });
            saveNexusCacheSoon();
        })();
        toFetch.forEach(function (m) { nexusInflight.set(m.key, job); });
        try {
            await job;
        } finally {
            toFetch.forEach(function (m) { nexusInflight.delete(m.key); });
        }
    }
    await Promise.all(missing.filter(function (m) { return m.wait; }).map(function (m) { return m.wait.catch(function () {}); }));
    missing.forEach(function (m) {
        var entry = cache.mods[m.key];
        result[m.key] = entry ? entry.data : null;
    });
    return { mods: result };
}

// -- native host: bridge pairing + auto-start --------------------------------------

var bridgeStatus = { state: "starting", at: nowIso(), error: "", native: "unknown", lastPair: "" };
var lastNativeAttempt = 0;
var authFailed = false;

async function nativeRequest(message) {
    try {
        var response = await browser.runtime.sendNativeMessage(NATIVE_HOST, message);
        bridgeStatus.native = response && response.ok ? "ok" : "error: " + (response && response.error || "no response");
        return response;
    } catch (error) {
        var text = String(error && error.message || error);
        bridgeStatus.native = /No such native application|not found|manifest/i.test(text)
            ? "not installed"
            : "error: " + text;
        return null;
    }
}

async function pairWithBridge(force) {
    if (!force && Date.now() - lastNativeAttempt < 60000) return false;
    lastNativeAttempt = Date.now();
    var response = await nativeRequest({ cmd: "bridge_config", ensure: true });
    if (!response || !response.ok || !response.token) return false;
    var settings = await captureSettings();
    var patch = {};
    if (!settings.bridgeToken || authFailed || force) patch.bridgeToken = response.token;
    if (response.endpoint && (!settings.bridgeEndpoint || settings.bridgeEndpoint === DEFAULT_BRIDGE || force)) {
        patch.bridgeEndpoint = response.endpoint;
        patch.bridgeCaptureEndpoint = response.endpoint.replace(/\/batch(?:\?.*)?$/, "/capture");
    }
    if (patch.bridgeToken && settings.bridgeEnabled === undefined) patch.bridgeEnabled = true;
    // Settings managed on this machine (.agent-os/browser-extension-settings.json).
    var managed = response.managed_settings && typeof response.managed_settings === "object" ? response.managed_settings : {};
    ["sheetEndpoint", "sheetToken", "sheetMirrorEnabled"].forEach(function (key) {
        if (key in managed && managed[key] !== settings[key]) patch[key] = managed[key];
    });
    if (Object.keys(patch).length) {
        await updateCaptureSettings(patch);
        bridgeStatus.lastPair = nowIso();
    }
    authFailed = false;
    return true;
}

// -- bridge HTTP --------------------------------------------------------------------

function bridgeBase(settings) {
    return String(settings.bridgeEndpoint || DEFAULT_BRIDGE).replace(/\/batch(?:\?.*)?$/, "");
}

async function bridgeFetch(path, options) {
    var settings = await captureSettings();
    if (settings.bridgeEnabled === false) throw Object.assign(new Error("bridge disabled"), { code: "disabled" });
    if (!settings.bridgeToken) throw Object.assign(new Error("bridge not paired"), { code: "unconfigured" });
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, (options && options.timeout) || 8000);
    try {
        var response = await fetch(bridgeBase(settings) + path, {
            method: options && options.method || "GET",
            headers: { "Content-Type": "application/json", "X-Agent-OS-Token": settings.bridgeToken },
            body: options && options.body ? JSON.stringify(options.body) : undefined,
            credentials: "omit",
            signal: controller.signal
        });
        if (response.status === 401) {
            authFailed = true;
            throw Object.assign(new Error("bridge rejected the token"), { code: "unauthorized" });
        }
        var body = await response.json().catch(function () { return {}; });
        if (!response.ok) throw Object.assign(new Error(body.error || "HTTP " + response.status), { code: "http" });
        bridgeStatus.state = "ok";
        bridgeStatus.at = nowIso();
        bridgeStatus.error = "";
        return body;
    } catch (error) {
        var code = error.code || (error.name === "AbortError" ? "timeout" : "unreachable");
        bridgeStatus.state = code;
        bridgeStatus.at = nowIso();
        bridgeStatus.error = String(error.message || error);
        if (code === "unreachable" || code === "unauthorized" || code === "unconfigured" || code === "timeout") {
            pairWithBridge(false);
        }
        throw Object.assign(error, { code: code });
    } finally {
        clearTimeout(timer);
    }
}

// -- filter rules → Agent OS (durable preference snapshot) ---------------------------

var filterSyncTimer = null;

function scheduleFilterSync() {
    if (filterSyncTimer) clearTimeout(filterSyncTimer);
    filterSyncTimer = setTimeout(syncFiltersToAgentOs, 5000);
}

async function syncFiltersToAgentOs() {
    filterSyncTimer = null;
    var state = await getFilters();
    if (!state.syncToAgentOs) return;
    var settings = await captureSettings();
    try {
        await bridgeFetch("/batch", {
            method: "POST",
            body: {
                schema: "agent-os/browser-bridge-batch/v1",
                batch_id: "filters-" + Date.now().toString(36),
                device: settings.device || "",
                events: [{
                    event_id: "content-filters:snapshot:" + (await installId()),
                    source: "content-filters",
                    event_type: "rules_snapshot",
                    source_key: "content-filters",
                    occurred_at: nowIso(),
                    device: settings.device || "",
                    payload: {
                        schema: "agent-os/content-filters/v1",
                        extension_version: VERSION,
                        enabled: state.enabled,
                        rules: state.rules,
                        sites: state.sites,
                        custom_sites: state.customSites
                    }
                }]
            }
        });
    } catch (error) {
        // Retried on the next rule change or bridge recovery.
    }
}

// -- bridge sessions + command execution -------------------------------------------

var SESSION_OPS = ["inspect", "extract", "wait", "click", "type", "scroll", "navigate", "back", "forward", "reload", "open_tab", "close_tab"];
var lastBeat = new Map();
var lastPoll = new Map();
var runningCommands = new Set();
var tickCount = 0;
var bridgeBackoffUntil = 0;
var MAX_SESSION_TABS = 40;
var agentTabs = new Set(); // tabs opened by open_tab (Agent OS work, routines)

// The tabs registered as bridge sessions this tick. Past the cap, tabs Agent OS
// opened come first, then the focused tab, then the most recently used, so a tab
// opened for a command is never starved by a browser full of older tabs.
function sessionTabs(tabs, focusedId) {
    function rank(tab) { return agentTabs.has(tab.id) ? 2 : (tab.id === focusedId ? 1 : 0); }
    return tabs.filter(function (t) { return /^https?:/.test(t.url || ""); })
        .sort(function (a, b) { return rank(b) - rank(a) || (b.lastAccessed || 0) - (a.lastAccessed || 0); })
        .slice(0, MAX_SESSION_TABS);
}

async function sessionIdFor(tabId) {
    return "firefox-" + (await installId()) + "-tab-" + tabId;
}

function siteOf(url) {
    try { return new URL(url).hostname; } catch (error) { return ""; }
}

async function registerSession(tab, focused) {
    await bridgeFetch("/session/heartbeat", {
        method: "POST",
        body: {
            session_id: await sessionIdFor(tab.id),
            url: tab.url,
            title: tab.title || "",
            site: siteOf(tab.url),
            visibility: tab.active ? "visible" : "hidden",
            focused: Boolean(focused),
            user_agent: navigator.userAgent,
            capabilities: {
                client: "agent-os-firefox-extension",
                version: VERSION,
                tab_id: tab.id,
                window_id: tab.windowId,
                ops: SESSION_OPS,
                safety_gate: true,
                content_filters: true,
                capture: true
            }
        }
    });
    lastBeat.set(tab.id, Date.now());
}

function waitForTabComplete(tabId, timeoutMs) {
    return new Promise(function (resolve) {
        var done = false;
        function finish() {
            if (done) return;
            done = true;
            browser.tabs.onUpdated.removeListener(listener);
            resolve();
        }
        function listener(id, info) {
            if (id === tabId && info.status === "complete") setTimeout(finish, 400);
        }
        browser.tabs.onUpdated.addListener(listener);
        setTimeout(finish, timeoutMs || 15000);
    });
}

// A page that reloads or navigates while handling an action never answers; give up instead of hanging.
var TAB_ANSWER_TIMEOUT_MS = 60000;

function withTimeout(promise, ms) {
    return new Promise(function (resolve, reject) {
        var timer = setTimeout(function () { reject(new Error("the page stopped answering (it reloaded or navigated)")); }, ms);
        promise.then(function (value) { clearTimeout(timer); resolve(value); },
            function (error) { clearTimeout(timer); reject(error); });
    });
}

async function sendToTab(tabId, message, attempts) {
    var tries = attempts || 8;
    for (var i = 0; i < tries; i += 1) {
        try {
            var response = await withTimeout(browser.tabs.sendMessage(tabId, message), TAB_ANSWER_TIMEOUT_MS);
            if (response !== undefined) return response;
        } catch (error) {
            if (i === tries - 1) throw error;
        }
        await sleep(500);
    }
    throw new Error("the page did not answer (is it a restricted page?)");
}

async function runCommand(tab, command) {
    if (runningCommands.has(command.command_id)) return;
    runningCommands.add(command.command_id);
    var steps = [];
    var state = "completed";
    var error = "";
    try {
        for (var i = 0; i < command.actions.length; i += 1) {
            var action = command.actions[i];
            var outcome;
            try {
                if (action.op === "navigate") {
                    await browser.tabs.update(tab.id, { url: action.url });
                    await waitForTabComplete(tab.id, action.timeout_ms);
                    outcome = { ok: true, result: { url: action.url } };
                } else if (action.op === "back" || action.op === "forward") {
                    await (action.op === "back" ? browser.tabs.goBack(tab.id) : browser.tabs.goForward(tab.id));
                    await waitForTabComplete(tab.id, action.timeout_ms || 8000);
                    outcome = { ok: true };
                } else if (action.op === "reload") {
                    await browser.tabs.reload(tab.id);
                    await waitForTabComplete(tab.id, action.timeout_ms);
                    outcome = { ok: true };
                } else if (action.op === "close_tab") {
                    await browser.tabs.remove(tab.id);
                    outcome = { ok: true, result: { closed: tab.id } };
                } else if (action.op === "open_tab") {
                    // active: true opens it in front, for pages that only render in a visible tab;
                    // window: true opens it in a separate window so long runs leave the person's window free.
                    var opened = action.window
                        ? (await browser.windows.create({ url: action.url, focused: false, width: 1400, height: 900 })).tabs[0]
                        : await browser.tabs.create({ url: action.url, active: Boolean(action.active) });
                    agentTabs.add(opened.id);
                    outcome = { ok: true, result: { tab_id: opened.id, session_id: await sessionIdFor(opened.id) } };
                } else {
                    outcome = await sendToTab(tab.id, { type: "aos-exec", action: action, approved: Boolean(command.approved_consequential) });
                }
            } catch (stepError) {
                outcome = { ok: false, error: String(stepError && stepError.message || stepError) };
            }
            steps.push(Object.assign({ index: i, op: action.op }, outcome));
            if (outcome.approval_required) { state = "approval_required"; error = outcome.reason; break; }
            if (outcome.blocked) { state = "failed"; error = outcome.reason; break; }
            if (outcome.ok === false) { state = "failed"; error = outcome.error || "step failed"; break; }
        }
        var current = await browser.tabs.get(tab.id).catch(function () { return tab; });
        lastBeat.delete(tab.id);
        await bridgeFetch("/command-result", {
            method: "POST",
            body: {
                command_id: command.command_id,
                state: state,
                error: error,
                result: { steps: steps, url: current.url, title: current.title }
            }
        });
    } catch (reportError) {
        console.warn("[Agent OS] could not run/report command", command.command_id, reportError);
    } finally {
        runningCommands.delete(command.command_id);
    }
}

async function pollCommands(tab) {
    var sessionId = await sessionIdFor(tab.id);
    var body = await bridgeFetch("/commands?session_id=" + encodeURIComponent(sessionId));
    lastPoll.set(tab.id, Date.now());
    (body.commands || []).forEach(function (command) { runCommand(tab, command); });
}

var tickBusy = false;

async function bridgeTick() {
    if (tickBusy) return;
    tickBusy = true;
    try {
        await bridgeTickInner();
    } finally {
        tickBusy = false;
    }
}

async function bridgeTickInner() {
    tickCount += 1;
    if (Date.now() < bridgeBackoffUntil) return;
    var settings = await captureSettings();
    if (settings.bridgeEnabled === false) { bridgeStatus.state = "disabled"; return; }
    if (!settings.bridgeToken) {
        bridgeStatus.state = "unconfigured";
        await pairWithBridge(false);
        return;
    }
    try {
        var focusedTabs = await browser.tabs.query({ active: true, lastFocusedWindow: true });
        var focusedId = focusedTabs[0] ? focusedTabs[0].id : -1;
        var tabs = sessionTabs(await browser.tabs.query({}), focusedId);
        var now = Date.now();
        for (var i = 0; i < tabs.length; i += 1) {
            var tab = tabs[i];
            var focused = tab.id === focusedId;
            if (!lastBeat.has(tab.id) || now - lastBeat.get(tab.id) > (focused ? 10000 : 25000)) {
                await registerSession(tab, focused);
            }
            var pollEvery = focused ? 1500 : (tab.active ? 5000 : 10000);
            if (!lastPoll.has(tab.id) || now - lastPoll.get(tab.id) >= pollEvery) {
                await pollCommands(tab);
            }
        }
    } catch (error) {
        bridgeBackoffUntil = Date.now() + (error.code === "unauthorized" ? 5000 : 20000);
    }
}

browser.tabs.onRemoved.addListener(function (tabId) {
    agentTabs.delete(tabId);
    lastBeat.delete(tabId);
    lastPoll.delete(tabId);
});

browser.tabs.onUpdated.addListener(function (tabId, info) {
    if (info.url || info.title) lastBeat.delete(tabId); // re-register promptly with the new URL
});

browser.tabs.onActivated.addListener(function (info) {
    lastBeat.delete(info.tabId);
});

// -- context menus --------------------------------------------------------------------

var MENU_ROOT = "aos-root";
var MENU_HIDE = "aos-hide";
var hideMenuOptions = new Map();
var hideMenuIds = [];
var menuInstance = 0;

function createMenus() {
    browser.menus.removeAll().then(function () {
        browser.menus.create({ id: MENU_ROOT, title: "Agent OS", contexts: ["all"] });
        browser.menus.create({ id: MENU_HIDE, parentId: MENU_ROOT, title: "Hide…", contexts: ["all"] });
        browser.menus.create({ id: "aos-hide-none", parentId: MENU_HIDE, title: "(right-click a post, mod, story or link)", enabled: false, contexts: ["all"] });
        browser.menus.create({ id: "aos-sep-1", parentId: MENU_ROOT, type: "separator", contexts: ["all"] });
        browser.menus.create({ id: "aos-save", parentId: MENU_ROOT, title: "Save page to Agent OS", contexts: ["page", "selection", "link", "image"] });
        browser.menus.create({ id: "aos-reveal", parentId: MENU_ROOT, title: "Show / re-hide filtered items", contexts: ["all"] });
        browser.menus.create({ id: "aos-options", parentId: MENU_ROOT, title: "Manage filters…", contexts: ["all"] });
    });
}

browser.menus.onShown.addListener(async function (info, tab) {
    if (!info.menuIds || info.menuIds.indexOf(MENU_ROOT) === -1 || !tab) return;
    var instance = ++menuInstance;
    var options = [];
    try {
        var response = await browser.tabs.sendMessage(tab.id, { type: "filters-context-options" });
        options = response && response.options || [];
    } catch (error) {
        options = [];
    }
    if (instance !== menuInstance) return;
    hideMenuIds.forEach(function (id) { browser.menus.remove(id).catch(function () {}); });
    hideMenuIds = [];
    hideMenuOptions.clear();
    browser.menus.update("aos-hide-none", { visible: !options.length });
    options.forEach(function (option, index) {
        var id = "aos-hide-" + instance + "-" + index;
        hideMenuOptions.set(id, option);
        hideMenuIds.push(id);
        browser.menus.create({ id: id, parentId: MENU_HIDE, title: option.label.replace(/&/g, "&&"), contexts: ["all"] });
    });
    browser.menus.refresh();
});

browser.menus.onClicked.addListener(function (info, tab) {
    var option = hideMenuOptions.get(info.menuItemId);
    if (option) {
        mutateFilters(function (state) {
            return Core.addRule(state, { scope: option.scope, field: option.field, value: option.value });
        });
        return;
    }
    if (info.menuItemId === "aos-save" && tab) {
        browser.tabs.sendMessage(tab.id, { type: "gm-menu-run", name: "Agent OS: Save current page" }).catch(function () {});
    } else if (info.menuItemId === "aos-reveal" && tab) {
        browser.tabs.sendMessage(tab.id, { type: "filters-page-stats" }).then(function (stats) {
            return browser.tabs.sendMessage(tab.id, { type: "filters-set-reveal", reveal: !(stats && stats.reveal) });
        }).catch(function () {});
    } else if (info.menuItemId === "aos-options") {
        browser.runtime.openOptionsPage();
    }
});

browser.commands.onCommand.addListener(async function (command) {
    var tabs = await browser.tabs.query({ active: true, currentWindow: true });
    if (!tabs[0]) return;
    if (command === "toggle-reveal") {
        var stats = await browser.tabs.sendMessage(tabs[0].id, { type: "filters-page-stats" }).catch(function () { return null; });
        browser.tabs.sendMessage(tabs[0].id, { type: "filters-set-reveal", reveal: !(stats && stats.reveal) }).catch(function () {});
    } else if (command === "save-page") {
        browser.tabs.sendMessage(tabs[0].id, { type: "gm-menu-run", name: "Agent OS: Save current page" }).catch(function () {});
    }
});

// -- messages from content scripts, popup and options ------------------------------------

browser.runtime.onMessage.addListener(function (message, sender) {
    if (!message || typeof message !== "object") return undefined;
    switch (message.type) {
    case "gm-xhr":
        return gmXhr(message);
    case "clipboard-write":
        return navigator.clipboard.writeText(String(message.text || "")).then(function () { return { ok: true }; });
    case "adp-save-login":
    case "adp-status":
    case "adp-probe-start":
    case "adp-probe-state":
    case "adp-credential":
    case "adp-probe-result":
        return adpMessage(message, sender);
    case "threecx-events":
        // 3CX calls, voicemails and chat counts go to the local bridge only.
        if (!Array.isArray(message.events) || !message.events.length) return Promise.resolve({ ok: false });
        return bridgeFetch("/batch", { method: "POST", body: { events: message.events.slice(0, 500) }, timeout: 20000 })
            .then(function (ack) { return { ok: true, ack: ack }; })
            .catch(function (error) { return { ok: false, error: String(error.message || error) }; });
    case "threecx-voicemail":
        return bridgeFetch("/3cx/voicemail", {
            method: "POST",
            body: { voicemail: message.voicemail, audio_base64: message.audio_base64 },
            timeout: 30000
        }).then(function (result) { return Object.assign({ ok: true }, result); })
            .catch(function (error) { return { ok: false, error: String(error.message || error) }; });
    case "threecx-notify":
        return browser.notifications.create("agent-os-3cx-" + Date.now(), {
            type: "basic",
            iconUrl: browser.runtime.getURL("icons/icon.svg"),
            title: String(message.title || "3CX"),
            message: String(message.message || "")
        }).then(function () { return { ok: true }; }, function (error) { return { ok: false, error: String(error) }; });
    case "perf-log":
        if (!message.entry || typeof message.entry !== "object") return Promise.resolve({ ok: false });
        return bridgeFetch("/batch", {
            method: "POST",
            body: { events: [{
                event_id: "perf:" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8),
                source: "extension-perf",
                event_type: "listing-timing",
                occurred_at: nowIso(),
                payload: Object.assign({ version: browser.runtime.getManifest().version }, message.entry)
            }] }
        }).catch(function () { return { ok: false }; });
    case "nexus-lookup":
        return nexusLookup(message.items || []);
    case "filters-get":
        return getFilters();
    case "filters-add-rule":
        return mutateFilters(function (state) { return { added: Core.addRule(state, message.rule) }; });
    case "filters-remove-rule":
        return mutateFilters(function (state) {
            var before = state.rules.length;
            state.rules = state.rules.filter(function (r) { return r.id !== message.id; });
            return { removed: before - state.rules.length };
        });
    case "filters-replace":
        return mutateFilters(function (state) {
            var next = Core.normalizeState(message.state);
            Object.keys(next).forEach(function (k) { state[k] = next[k]; });
            return { ok: true };
        });
    case "filters-import":
        return mutateFilters(function (state) {
            return { added: Core.importRules(state, message.input, message.defaults) };
        });
    case "routines-list":
    case "routine-runs":
    case "routine-save":
    case "routine-delete":
    case "routine-run":
        return routineRequest(message);
    case "open-tab":
        if (!/^https?:/i.test(String(message.url || ""))) return Promise.resolve({ ok: false });
        return browser.tabs.create({
            url: message.url,
            active: Boolean(message.active),
            openerTabId: sender && sender.tab ? sender.tab.id : undefined
        }).then(function (tab) { return { ok: true, tab_id: tab.id }; });
    case "open-options":
        return browser.runtime.openOptionsPage().then(function () { return { ok: true }; });
    case "status":
        return (async function () {
            var settings = await captureSettings();
            return {
                version: VERSION,
                bridge: Object.assign({}, bridgeStatus, {
                    enabled: settings.bridgeEnabled !== false,
                    paired: Boolean(settings.bridgeToken),
                    endpoint: settings.bridgeEndpoint
                }),
                sessions: lastBeat.size
            };
        })();
    case "bridge-pair":
        return pairWithBridge(true).then(async function (ok) {
            bridgeBackoffUntil = 0;
            if (ok) {
                try { await bridgeFetch("/stats"); } catch (error) { /* status records it */ }
            }
            return { ok: ok, bridge: bridgeStatus };
        });
    default:
        return undefined;
    }
});

browser.storage.onChanged.addListener(function (changes, area) {
    if (area === "local" && changes[Core.STORAGE_KEY]) scheduleFilterSync();
    if (area === "local" && changes[GM_SETTINGS_KEY]) bridgeBackoffUntil = 0;
});

browser.runtime.onInstalled.addListener(function (details) {
    if (details.reason === "install") {
        browser.tabs.create({ url: browser.runtime.getURL("options/options.html#welcome") });
    }
});

// -- AI browser routines (stored and run by Agent OS through the native helper) -------------

var ROUTINE_COMMANDS = {
    "routines-list": "routines_list",
    "routine-runs": "routine_runs",
    "routine-save": "routine_save",
    "routine-delete": "routine_delete",
    "routine-run": "routine_run"
};

async function routineRequest(message) {
    var request = Object.assign({}, message, { cmd: ROUTINE_COMMANDS[message.type] });
    delete request.type;
    var response = await nativeRequest(request);
    if (!response) return { ok: false, error: "Agent OS native helper: " + bridgeStatus.native };
    return response;
}

// Scheduled routines run only while Firefox is open, which is when they can work.
async function routinesTick() {
    if (bridgeStatus.state !== "ok") return;
    await nativeRequest({ cmd: "routines_tick" });
}

setInterval(routinesTick, 60000);

// -- old.reddit.com redirect -------------------------------------------------------------

var redirectSettings = Core.normalizeState(null).redirects;

getFilters().then(function (state) { redirectSettings = state.redirects; });
browser.storage.onChanged.addListener(function (changes, area) {
    if (area === "local" && changes[Core.STORAGE_KEY]) {
        redirectSettings = Core.normalizeState(changes[Core.STORAGE_KEY].newValue).redirects;
    }
});

browser.webRequest.onBeforeRequest.addListener(function (details) {
    if (!redirectSettings.oldReddit) return {};
    var target = globalThis.AgentOsSites.oldRedditRedirect(details.url);
    return target && target !== details.url ? { redirectUrl: target } : {};
}, {
    urls: ["*://reddit.com/*", "*://www.reddit.com/*", "*://new.reddit.com/*", "*://np.reddit.com/*"],
    types: ["main_frame"]
}, ["blocking"]);

// -- ADP: saved sign-in and an unattended sign-in test ------------------------------------
//
// The login lives in Windows Credential Manager (native helper, task id
// ADP_TASK). It is handed out only to the background tab this page opened for
// the test, and only while that tab is on an ADP sign-in page.

var ADP_TASK = "adp-workforce-now";
// Starting from the admin page gets ADP's two-step sign-in (user ID, then password), which accepts
// filled values; the root URL can show a combined form whose password field does not.
var ADP_START_URL = "https://workforcenow.adp.com/theme/admin.html";
var ADP_TIMEOUT_MS = 120000;
var adpProbe = null;

async function adpCredentialStatus() {
    var res = await nativeRequest({ cmd: "credential_status", task_id: ADP_TASK });
    return { hasUsername: Boolean(res && res.has_username), hasPassword: Boolean(res && res.has_password) };
}

async function startAdpProbe() {
    if (adpProbe) return { ok: false, error: "A sign-in test is already running." };
    var status = await adpCredentialStatus();
    if (!status.hasPassword) return { ok: false, error: "Save the ADP sign-in first." };
    // In front: ADP's sign-in form is built from web components that Firefox
    // does not render in a background tab. The tab closes itself when done.
    var tab = await browser.tabs.create({ url: ADP_START_URL, active: true });
    adpProbe = { tabId: tab.id, startedAt: Date.now() };
    adpProbe.timer = setTimeout(function () {
        finishAdpProbe({ status: "timeout", detail: "No sign-in result within two minutes." });
    }, ADP_TIMEOUT_MS);
    return { ok: true };
}

async function finishAdpProbe(result) {
    var probe = adpProbe;
    if (!probe) return;
    adpProbe = null;
    clearTimeout(probe.timer);
    var last = {
        status: String(result.status || "error"),
        detail: String(result.detail || ""),
        page: String(result.page || ""),
        title: String(result.title || ""),
        startedAt: new Date(probe.startedAt).toISOString(),
        finishedAt: nowIso(),
        seconds: Math.round((Date.now() - probe.startedAt) / 1000)
    };
    await browser.storage.local.set({ adp_probe_last: last });
    bridgeFetch("/batch", { method: "POST", body: { events: [{
        event_id: "adp:signin-probe:" + last.finishedAt, source: "adp", event_type: "signin-probe",
        occurred_at: last.finishedAt, payload: last
    }] } }).catch(function () { /* bridge offline: the result is still in extension storage */ });
    browser.notifications.create("agent-os-adp-" + Date.now(), {
        type: "basic",
        iconUrl: browser.runtime.getURL("icons/icon.svg"),
        title: "ADP sign-in test: " + last.status.replace(/_/g, " "),
        message: last.detail || last.page
    }).catch(function () {});
    browser.tabs.remove(probe.tabId).catch(function () {});
}

// Extension pages (the ADP window opens as a popup, so it has a tab too).
function fromExtensionPage(sender) {
    return Boolean(sender && sender.url && sender.url.indexOf(browser.runtime.getURL("")) === 0);
}

async function adpMessage(message, sender) {
    var tabId = sender && sender.tab && sender.tab.id;
    var fromProbe = Boolean(adpProbe && tabId === adpProbe.tabId);
    switch (message.type) {
    case "adp-save-login": {
        if (!fromExtensionPage(sender)) return { ok: false, error: "not allowed" };
        var res = await nativeRequest({ cmd: "credential_set", task_id: ADP_TASK,
            username: String(message.username || ""), password: String(message.password || "") });
        return res && res.ok ? { ok: true } : { ok: false, error: res && res.error || "native helper " + bridgeStatus.native };
    }
    case "adp-status": {
        var stored = await browser.storage.local.get("adp_probe_last");
        return Object.assign(await adpCredentialStatus(), { running: Boolean(adpProbe), last: stored.adp_probe_last || null });
    }
    case "adp-probe-start":
        if (!fromExtensionPage(sender)) return { ok: false, error: "not allowed" };
        return startAdpProbe();
    case "adp-probe-state":
        return { active: fromProbe };
    case "adp-credential": {
        var host = "";
        try { host = new URL(sender.url).hostname.toLowerCase(); } catch (error) { host = ""; }
        if (!fromProbe || !/(^|\.)adp\.com$/.test(host) || (message.field !== "username" && message.field !== "password")) {
            return { error: "not allowed" };
        }
        var cred = await nativeRequest({ cmd: "credential_get", task_id: ADP_TASK, field: message.field });
        return cred && cred.ok ? { value: cred.value } : { error: cred && cred.error || "native helper " + bridgeStatus.native };
    }
    case "adp-probe-result":
        if (fromProbe) await finishAdpProbe(message);
        return { ok: true };
    }
    return undefined;
}

// After an install or update, open the ADP sign-in window once if no login is saved.
if (browser.runtime.onInstalled) browser.runtime.onInstalled.addListener(function () {
    adpCredentialStatus().then(function (status) {
        if (status.hasPassword) return;
        return browser.windows.create({ url: browser.runtime.getURL("adp/login.html"), type: "popup", width: 460, height: 560 });
    }).catch(function () { /* native helper missing */ });
});

// -- 3CX: keep open web client tabs syncing every five minutes ----------------------------
//
// Background tabs can sleep, so an alarm asks each 3CX tab to sync; the tab
// skips the request when it synced recently.

var THREECX_ALARM = "agent-os-3cx-sync";
var THREECX_TABS = ["https://*.3cx.us/*", "https://*.3cx.com/*", "https://*.3cx.eu/*", "https://*.3cx.co.uk/*", "https://*.3cx.ca/*", "https://*.3cx.com.au/*"];

if (browser.alarms) browser.alarms.create(THREECX_ALARM, { periodInMinutes: 5 });
if (browser.alarms) browser.alarms.onAlarm.addListener(function (alarm) {
    if (alarm.name !== THREECX_ALARM) return;
    browser.tabs.query({ url: THREECX_TABS }).then(function (tabs) {
        tabs.forEach(function (tab) {
            browser.tabs.sendMessage(tab.id, { type: "threecx-sync" }).catch(function () { /* not a web client */ });
        });
    });
});

// -- startup ------------------------------------------------------------------------------

createMenus();
pairWithBridge(false).finally(function () {
    setInterval(bridgeTick, 1500);
    bridgeTick();
});
