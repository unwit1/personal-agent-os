"use strict";

// End to end: real Agent OS bridge server (temp DB) <-> real background.js
// (in a VM with a fake Firefox) <-> real executor.js (in a jsdom "tab").

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const vm = require("node:vm");
const readline = require("node:readline");
const { spawn } = require("node:child_process");
const Core = require("../src/lib/filter-core.js");
const { read, makeBrowser, sendToContent, makeDom, load } = require("./helpers");

function startHarness() {
    const child = spawn(process.env.PYTHON || "python", [path.join(__dirname, "bridge_harness.py")], { stdio: ["ignore", "pipe", "inherit"] });
    const events = [];
    const waiters = [];
    readline.createInterface({ input: child.stdout }).on("line", (line) => {
        let event;
        try { event = JSON.parse(line); } catch (error) { return; }
        events.push(event);
        waiters.slice().forEach((w) => { if (w.name === event.event) { waiters.splice(waiters.indexOf(w), 1); w.resolve(event); } });
    });
    function next(name, timeoutMs) {
        const found = events.find((e) => e.event === name);
        if (found) return Promise.resolve(found);
        return new Promise((resolve, reject) => {
            waiters.push({ name, resolve });
            setTimeout(() => reject(new Error("harness timeout waiting for " + name)), timeoutMs || 30000);
        });
    }
    return { child, next };
}

function fakeFirefox(port, token, tabDom, tabBrowser) {
    const storage = makeBrowser({
        storage: {
            "gm:agent_os_capture_settings_v1": {
                bridgeEnabled: true,
                bridgeEndpoint: "http://127.0.0.1:" + port + "/api/v1/browser/batch",
                bridgeToken: token,
                device: "e2e"
            }
        }
    });
    const timers = new Set();
    const tab = { id: 7, windowId: 1, active: true, url: tabDom.window.location.href, title: "Shop" };
    const listeners = { message: [], webRequest: null };
    const removed = [];
    const noopEvent = { addListener() {} };
    const browser = {
        storage: storage.storage,
        runtime: {
            getManifest: () => ({ version: "1.0.0-e2e" }),
            getURL: (p) => "moz-extension://e2e/" + p,
            sendNativeMessage: () => Promise.reject(new Error("No such native application agent_os_native")),
            onMessage: { addListener: (fn) => listeners.message.push(fn) },
            onInstalled: noopEvent,
            openOptionsPage: () => Promise.resolve()
        },
        tabs: {
            query: async () => [tab],
            get: async () => tab,
            sendMessage: async (tabId, message) => sendToContent(tabBrowser, message),
            create: async (opts) => ({ id: 99, url: opts.url }),
            update: async () => tab,
            reload: async () => {},
            remove: async (id) => { removed.push(id); },
            goBack: async () => {},
            goForward: async () => {},
            onRemoved: noopEvent,
            onUpdated: { addListener() {}, removeListener() {} },
            onActivated: noopEvent
        },
        menus: {
            removeAll: async () => {}, create() {}, update: async () => {}, remove: async () => {}, refresh() {},
            onShown: noopEvent, onClicked: noopEvent
        },
        commands: { onCommand: noopEvent },
        webRequest: { onBeforeRequest: { addListener: (fn) => { listeners.webRequest = fn; } } }
    };
    const context = vm.createContext({
        browser,
        console,
        fetch,
        AbortController,
        URL,
        Blob,
        navigator: { userAgent: "e2e", clipboard: { writeText: async () => {} } },
        setTimeout: (fn, ms) => { const t = setTimeout(fn, ms); timers.add(t); return t; },
        clearTimeout: (t) => clearTimeout(t),
        setInterval: (fn, ms) => { const t = setInterval(fn, ms); timers.add(t); return t; },
        clearInterval: (t) => clearInterval(t)
    });
    context.globalThis = context;
    ["lib/filter-core.js", "lib/sites.js", "background.js"].forEach((file) => vm.runInContext(read(file), context, { filename: file }));
    return {
        storage,
        listeners,
        removed,
        send: (message) => listeners.message[0](message, {}),
        stop: () => timers.forEach((t) => { clearTimeout(t); clearInterval(t); })
    };
}

test("bridge sessions, gated command execution and filter sync against the real bridge", { timeout: 90000 }, async () => {
    const harness = startHarness();
    let firefox;
    try {
        const ready = await harness.next("ready");

        const tabBrowser = makeBrowser();
        const tabDom = makeDom(`<main><h1>Shop</h1><form id="f">
            <input id="q" name="q"><input id="pw" type="password">
            <button id="buy" type="submit">Place order</button></form></main>`, "https://shop.example/cart", tabBrowser);
        let submitted = 0;
        tabDom.window.document.getElementById("f").addEventListener("submit", (e) => { e.preventDefault(); submitted += 1; });
        load(tabDom, ["content/executor.js"]);

        firefox = fakeFirefox(ready.port, ready.token, tabDom, tabBrowser);

        const session = (await harness.next("session")).session;
        assert.match(session.session_id, /^firefox-[a-z0-9]+-tab-7$/);
        assert.equal(session.capabilities.safety_gate, true);
        assert.equal(session.url, "https://shop.example/cart");

        const first = (await harness.next("first")).status;
        assert.equal(first.state, "approval_required", "click on 'Place order' pauses for approval");
        assert.equal(first.result.steps[0].op, "inspect");
        assert.equal(first.result.steps[1].ok, true);
        assert.equal(tabDom.window.document.getElementById("q").value, "skyrim");
        assert.equal(submitted, 0);

        const second = (await harness.next("second")).status;
        assert.equal(second.state, "completed");
        assert.equal(submitted, 1, "approved click submits");

        const third = (await harness.next("third")).status;
        assert.equal(third.state, "failed", "password typing refused even when approved");
        assert.match(third.error, /credential/);

        const fourth = (await harness.next("fourth")).status;
        assert.equal(fourth.state, "completed");
        assert.deepEqual(firefox.removed, [7], "close_tab closes the session's tab");

        // Rule change -> preference snapshot event in the bridge.
        await firefox.send({ type: "filters-add-rule", rule: { scope: "reddit", field: "subreddit", value: "pics" } });
        const rows = (await harness.next("filters", 40000)).rows;
        assert.equal(rows.length, 1);
        assert.equal(rows[0].event_type, "rules_snapshot");
        assert.equal(rows[0].payload.rules[0].value, "pics");

        // old.reddit redirect is wired to webRequest.
        const redirect = firefox.listeners.webRequest({ url: "https://www.reddit.com/r/all/", type: "main_frame" });
        assert.equal(redirect.redirectUrl, "https://old.reddit.com/r/all/");
        const stored = Core.normalizeState(firefox.storage._data[Core.STORAGE_KEY]);
        stored.redirects.oldReddit = false;
        await firefox.storage.storage.local.set({ [Core.STORAGE_KEY]: stored });
        assert.equal(Object.keys(firefox.listeners.webRequest({ url: "https://www.reddit.com/r/all/", type: "main_frame" })).length, 0);

        const status = await firefox.send({ type: "status" });
        assert.equal(status.bridge.state, "ok");
        assert.equal(status.bridge.native, "not installed");
        tabDom.window.close();
    } finally {
        if (firefox) firefox.stop();
        harness.child.kill();
    }
});
