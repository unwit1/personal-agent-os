"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");
const Sites = require("../src/lib/sites.js");
const Core = require("../src/lib/filter-core.js");
const { DIST, makeBrowser, makeDom, load, waitFor } = require("./helpers");

const GENERATED = path.join(DIST, "content", "capture.generated.js");

test("HeroBloks cards hide exact variants, without hiding neighboring cards", () => {
    const html = '<main><div class="grid">' +
        '<div class="card" id="a"><a href="/figures/48416"><img alt="Evil Ahsoka"></a>' +
        '<a href="/figures/48416/printer-toner/ahsoka">Evil Ahsoka</a></div>' +
        '<div class="card" id="b"><a href="/figures/54982"><img alt="Flash"></a></div>' +
        '<a href="https://not-herobloks.com/figures/123">External</a></div></main>';
    const doc = new JSDOM(html, { url: "https://www.herobloks.com/search?q=ahsoka" }).window.document;
    const adapter = Sites.adaptersFor(doc.location, doc, []).find((a) => a.scope === "herobloks");
    assert.ok(adapter);
    assert.equal(adapter.quickHide, true);
    const items = adapter.items(doc);
    assert.equal(items.length, 2);
    assert.equal(items[0].id, "a");
    assert.equal(items[1].id, "b");
    assert.equal(adapter.facets(items[0]).id, "herobloks:figure:48416");
    assert.equal(adapter.facets(items[1]).id, "herobloks:figure:54982");
    const state = Core.normalizeState(null);
    assert.equal(state.sites.herobloks.enabled, true);
    assert.equal(Core.addRule(state, { scope: "herobloks", field: "id", value: "herobloks:figure:48416" }), true);
    assert.equal(Core.addRule(state, { scope: "herobloks", field: "id", value: "herobloks:figure:48416" }), false);
    const context = { scope: "herobloks", host: "www.herobloks.com", siteSettings: state.sites.herobloks };
    assert.ok(Core.evaluate(Core.compileRules(state), adapter.facets(items[0]), context));
    assert.equal(Core.evaluate(Core.compileRules(state), adapter.facets(items[1]), context), null);
});

test("HeroBloks detail page remains accessible while other versions may be filtered", () => {
    const doc = new JSDOM('<main><h1>Evil Ahsoka</h1><a href="/figures/48416/same">same</a>' +
        '<ul><li><a href="/figures/48417">other variant</a></li></ul></main>',
        { url: "https://www.herobloks.com/figures/48416" }).window.document;
    const items = Sites.byScope.herobloks.items(doc);
    assert.equal(items.length, 1);
    assert.equal(Sites.byScope.herobloks.facets(items[0]).id, "herobloks:figure:48417");
});

test("HeroBloks listing Add sends stable metadata and blocks repeat clicks", {
    skip: !fs.existsSync(GENERATED) && "run tools/build.py first"
}, async () => {
    const calls = [];
    const browser = makeBrowser({
        storage: { "gm:agent_os_capture_settings_v1": {
            bridgeEnabled: true, bridgeToken: "test", browserJournalEnabled: false,
            bridgeCaptureEndpoint: "http://127.0.0.1:8766/api/v1/browser/capture" } },
        onBackgroundMessage: async (message) => {
            if (message.type !== "gm-xhr") return undefined;
            calls.push(message);
            return { status: 200, responseText: '{"status":"stored"}' };
        }
    });
    const html = '<html><head><title>HeroBloks</title></head><body><main>' +
        '<div class="card" id="figure"><a href="/figures/48416"><img alt="Evil Ahsoka" src="/img.jpg"></a>' +
        '<h3>Evil Ahsoka</h3></div></main></body></html>';
    const dom = makeDom(html, "https://www.herobloks.com/search?q=ahsoka", browser);
    try {
        dom.window.console.info = () => {};
        load(dom, ["content/gm-shim.js"]);
        load(dom, ["content/capture.generated.js"], DIST);
        const button = await waitFor(() => dom.window.document.querySelector("#figure .aos-herobloks-save"));
        button.click();
        const request = await waitFor(() => calls.find((r) => /\/capture$/.test(r.url)));
        const data = JSON.parse(request.data);
        assert.equal(data.source_id, "herobloks:figure:48416");
        assert.equal(data.content_type, "minifigure");
        assert.equal(data.metadata.figure_id, "48416");
        assert.equal(data.metadata.collection_state, "unclassified");
        assert.equal(data.canonical_url, "https://www.herobloks.com/figures/48416");
        await waitFor(() => button.textContent === "✓ In Agent OS");
        assert.equal(button.disabled, true);
        button.click();
        assert.equal(calls.filter((r) => /\/capture$/.test(r.url)).length, 1);
    } finally {
        dom.window.close();
    }
});

test("HeroBloks Add queues while offline and cannot enqueue twice", {
    skip: !fs.existsSync(GENERATED) && "run tools/build.py first"
}, async () => {
    const browser = makeBrowser({
        storage: { "gm:agent_os_capture_settings_v1": { bridgeEnabled: false, browserJournalEnabled: false } }
    });
    const dom = makeDom('<html><body><div class="card" id="figure">' +
        '<a href="/figures/48416"><img alt="Evil Ahsoka"></a></div></body></html>',
        "https://www.herobloks.com/figures/", browser);
    try {
        dom.window.console.info = () => {};
        load(dom, ["content/gm-shim.js"]);
        load(dom, ["content/capture.generated.js"], DIST);
        const button = await waitFor(() => dom.window.document.querySelector(".aos-herobloks-save"));
        button.click();
        await waitFor(() => button.textContent === "⏳ Queued");
        const queue = browser._data["gm:agent_os_capture_queue_v1"];
        assert.equal(queue.length, 1);
        assert.equal(queue[0].capture.source_id, "herobloks:figure:48416");
        button.click();
        assert.equal(browser._data["gm:agent_os_capture_queue_v1"].length, 1);
    } finally {
        dom.window.close();
    }
});

test("HeroBloks detail Hide and Unhide use persistent filter messages", {
    skip: !fs.existsSync(GENERATED) && "run tools/build.py first"
}, async () => {
    const state = Core.normalizeState(null);
    const messages = [];
    const browser = makeBrowser({
        storage: { "gm:agent_os_capture_settings_v1": { bridgeEnabled: false, browserJournalEnabled: false } },
        onBackgroundMessage: async (message) => {
            messages.push(message);
            if (message.type === "filters-get") return state;
            if (message.type === "filters-add-rule") {
                Core.addRule(state, message.rule);
                return { added: true };
            }
            if (message.type === "filters-remove-rule") {
                state.rules = state.rules.filter((r) => r.id !== message.id);
                return { removed: 1 };
            }
        }
    });
    const dom = makeDom('<html><body><main><h1>Evil Ahsoka</h1></main></body></html>',
        "https://www.herobloks.com/figures/48416", browser);
    try {
        dom.window.console.info = () => {};
        load(dom, ["content/gm-shim.js"]);
        load(dom, ["content/capture.generated.js"], DIST);
        const hide = await waitFor(() => dom.window.document.querySelector("#aos-herobloks-detail-controls button:last-child"));
        await waitFor(() => hide.textContent === "⊘ Hide figure");
        hide.click();
        await waitFor(() => hide.textContent === "↶ Unhide figure");
        assert.equal(state.rules.length, 1);
        assert.equal(state.rules[0].value, "herobloks:figure:48416");
        hide.click();
        await waitFor(() => hide.textContent === "⊘ Hide figure");
        assert.equal(state.rules.length, 0);
        assert.ok(messages.some((m) => m.type === "filters-remove-rule"));
    } finally {
        dom.window.close();
    }
});
