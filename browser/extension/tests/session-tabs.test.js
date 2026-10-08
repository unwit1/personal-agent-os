"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const { read, makeBrowser } = require("./helpers");

// background.js in a VM with an inert Firefox; only sessionTabs is exercised.
function loadBackground() {
    const noopEvent = { addListener() {}, removeListener() {} };
    const browser = {
        storage: makeBrowser({ storage: { "gm:agent_os_capture_settings_v1": { bridgeEnabled: false } } }).storage,
        runtime: {
            getManifest: () => ({ version: "test" }), getURL: (p) => "moz-extension://t/" + p,
            sendNativeMessage: () => Promise.reject(new Error("none")),
            onMessage: noopEvent, onInstalled: noopEvent, openOptionsPage: async () => {}
        },
        tabs: { query: async () => [], onRemoved: noopEvent, onUpdated: noopEvent, onActivated: noopEvent },
        menus: { removeAll: async () => {}, create() {}, update: async () => {}, remove: async () => {}, refresh() {}, onShown: noopEvent, onClicked: noopEvent },
        commands: { onCommand: noopEvent },
        webRequest: { onBeforeRequest: noopEvent }
    };
    const timers = [];
    const context = vm.createContext({
        browser, console, URL, fetch, AbortController, Blob,
        navigator: { userAgent: "t", clipboard: { writeText: async () => {} } },
        setTimeout: (fn, ms) => { const t = setTimeout(fn, ms); timers.push(t); return t; },
        clearTimeout,
        setInterval: () => 0, clearInterval() {}
    });
    context.globalThis = context;
    ["lib/filter-core.js", "lib/sites.js", "background.js"].forEach((f) => vm.runInContext(read(f), context, { filename: f }));
    return { context, stop: () => timers.forEach(clearTimeout) };
}

test("bridge sessions: past the 40-tab cap, Agent OS tabs and the focused tab still register", () => {
    const { context, stop } = loadBackground();
    try {
        const tabs = [{ id: 0, url: "about:blank", lastAccessed: 9999 }];
        for (let i = 1; i <= 45; i += 1) tabs.push({ id: i, url: "https://site.test/" + i, lastAccessed: 1000 + i });
        tabs.push({ id: 112, url: "https://workforcenow.adp.com/", lastAccessed: 0 });
        context.agentTabs.add(112);
        const chosen = context.sessionTabs(tabs, 2).map((t) => t.id);
        assert.equal(chosen.length, 40);
        assert.deepEqual(chosen.slice(0, 3), [112, 2, 45], "agent tab, focused tab, then most recently used");
        assert.ok(!chosen.includes(0), "non-web tabs are never sessions");
        assert.ok(!chosen.includes(1), "the least recently used tab is the one dropped");
    } finally {
        stop();
    }
});
