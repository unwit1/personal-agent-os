"use strict";

// Shopping collector (replaces agent-os-shopping's Tampermonkey collector userscript).
// Unit: collector-core on jsdom pages. E2E: real Agent OS bridge <-> real background scripts
// (VM, fake Firefox) <-> real content/collector.js (jsdom tab), with Shopping's own parser.

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const vm = require("node:vm");
const readline = require("node:readline");
const { spawn } = require("node:child_process");
const { JSDOM } = require("jsdom");
const Core = require("../src/lib/collector-core.js");
const { read, makeBrowser, sendToContent, makeDom, load } = require("./helpers");

const SHOP_PAGE = `<html><head><title>usb c cable - Walmart.com</title>
<script type="application/ld+json">{"@type":"Product","name":"Anker USB-C Cable 6ft","offers":{"price":"12.99","priceCurrency":"USD"}}</script>
<meta property="og:title" content="Search">
</head><body>
<div data-item-id="1"><a href="/ip/1"><span data-automation-id="product-title">Anker USB-C Cable 6ft</span></a>
  <span itemprop="price" content="12.99">$12.99</span><img src="/a.jpg"></div>
<div data-item-id="2"><a href="/ip/2"><span data-automation-id="product-title"></span><span data-automation-id="product-title">Belkin USB-C 3ft</span></a>
  <span itemprop="price" content="9.49">$9.49</span></div>
<div class="tile_group">
  <div><a href="/pd/a-1"><img alt="Grid Cable A" src="/a.png"></a></div><div><span data-testid="splp-prd-brd-nm">Utilitech</span></div>
  <div><span aria-label="Actual Price $5.00">$5.00</span></div>
  <div><a href="/pd/b-2"><img alt="Grid Cable B" src="/b.png"></a></div><div><span aria-label="Actual Price $6.00">$6.00</span></div>
</div>
<form><button id="buy">Place order</button></form>
</body></html>`;

// The live-probed Lowe's recipe from agent-os-shopping browser_collection.RECIPES (sibling-cell grid).
const LOWES_GROUPS = { kind: "groups", container: ".tile_group", start: ':has(a[href*="/pd/"] img[alt])', limit: 30,
    fields: { title: 'a[href*="/pd/"] img@alt', price: '[aria-label^="Actual Price"]@aria-label',
        brand: '[data-testid="splp-prd-brd-nm"]', link: 'a[href*="/pd/"]@href' } };

function page(html, url) {
    return new JSDOM(html, { url: url || "https://www.walmart.com/search?q=usb+c+cable" }).window.document;
}

test("validate: only navigate/wait/scroll/extract, http(s) only, known kinds", () => {
    assert.equal(Core.validate([{ op: "navigate", url: "https://x.test/" }, { op: "extract", kind: "tiles" }]), "");
    assert.match(Core.validate([{ op: "click", selector: "#buy" }]), /unsupported op/);
    assert.match(Core.validate([{ op: "type", selector: "#q", text: "x" }]), /unsupported op/);
    assert.match(Core.validate([{ op: "open_tab", url: "https://x.test" }]), /unsupported op/);
    assert.match(Core.validate([{ op: "navigate", url: "javascript:alert(1)" }]), /http/);
    assert.match(Core.validate([{ op: "extract", kind: "cookies" }]), /extract kind/);
    assert.match(Core.validate([]), /no steps/);
});

test("extract kinds match the userscript (jsonld, meta, tiles with placeholders, groups, next_data)", () => {
    const doc = page(SHOP_PAGE);
    assert.match(Core.extract(doc, { kind: "jsonld" })[0], /Anker USB-C Cable/);
    assert.equal(Core.extract(doc, { kind: "meta" })["og:title"], "Search");
    const tiles = Core.extract(doc, { kind: "tiles", selector: "[data-item-id]",
        fields: { title: "[data-automation-id=product-title]", price: "[itemprop=price]@content", url: "a@href" } });
    assert.deepEqual(tiles.map((t) => t.title), ["Anker USB-C Cable 6ft", "Belkin USB-C 3ft"], "skips empty placeholder nodes");
    assert.equal(tiles[1].price, "9.49");
    const groups = Core.extract(doc, LOWES_GROUPS);
    assert.deepEqual(groups, [
        { title: "Grid Cable A", price: "Actual Price $5.00", brand: "Utilitech", link: "/pd/a-1" },
        { title: "Grid Cable B", price: "Actual Price $6.00", brand: "", link: "/pd/b-2" }
    ]);
    assert.equal(Core.extract(page("<div id='__NEXT_DATA__'>{\"a\":1}</div>"), { kind: "next_data" }), "{\"a\":1}");
    assert.deepEqual(Core.extract(doc, { kind: "tiles", selector: "[[bad", fields: {} }), [], "bad recipe selector does not throw");
});

test("human checks are detected, normal product pages are not", () => {
    assert.equal(Core.humanCheckPresent(page(SHOP_PAGE)), false);
    assert.equal(Core.humanCheckPresent(page("<title>Robot Check</title><p>Enter the characters you see below</p>")), true);
    assert.equal(Core.humanCheckPresent(page("<p>Press &amp; Hold to confirm you are a human</p>")), true);
    assert.equal(Core.humanCheckPresent(page("<iframe src='https://x.test/captcha/1'></iframe>")), true);
});

test("content script answers collector messages and never clicks", async () => {
    const browser = makeBrowser();
    const dom = makeDom(SHOP_PAGE, "https://www.walmart.com/search?q=usb", browser);
    let clicked = 0;
    dom.window.document.getElementById("buy").addEventListener("click", () => { clicked += 1; });
    load(dom, ["lib/collector-core.js", "content/collector.js"]);
    const out = await sendToContent(browser, { type: "aos-collect", action: { op: "extract", kind: "jsonld" } });
    assert.equal(out.ok, true);
    assert.equal(out.step.kind, "jsonld");
    const refused = await sendToContent(browser, { type: "aos-collect", action: { op: "click", selector: "#buy" } });
    assert.equal(refused.ok, false);
    assert.equal(clicked, 0);
    await sendToContent(browser, { type: "aos-collector-badge", text: "idle" });
    assert.equal(dom.window.document.getElementById("agent-os-shopping-collector-badge").textContent, "idle");
    dom.window.close();
});

// ------------------------------------------------------------------------------ e2e

function startHarness() {
    const child = spawn(process.env.PYTHON || "python", [path.join(__dirname, "collector_harness.py")], { stdio: ["ignore", "pipe", "inherit"] });
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
            setTimeout(() => reject(new Error("harness timeout waiting for " + name)), timeoutMs || 45000);
        });
    }
    return { child, next };
}

function fakeFirefox(port, token, tabBrowser) {
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
    const tab = { id: 7, windowId: 1, active: false, url: "https://www.walmart.com/search?q=usb+c+cable", title: "Walmart" };
    const listeners = { message: [], updated: [] };
    const navigations = [];
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
            get: async (id) => { if (id !== tab.id) throw new Error("no tab"); return tab; },
            sendMessage: async (tabId, message) => sendToContent(tabBrowser, message),
            create: async (opts) => ({ id: 99, url: opts.url }),
            update: async (id, props) => {
                if (props.url) navigations.push(props.url);
                setTimeout(() => listeners.updated.slice().forEach((fn) => fn(id, { status: "complete" })), 10);
                return tab;
            },
            reload: async () => {},
            remove: async () => {},
            onRemoved: noopEvent,
            onUpdated: {
                addListener: (fn) => listeners.updated.push(fn),
                removeListener: (fn) => { const i = listeners.updated.indexOf(fn); if (i >= 0) listeners.updated.splice(i, 1); }
            },
            onActivated: noopEvent
        },
        menus: {
            removeAll: async () => {}, create() {}, update: async () => {}, remove: async () => {}, refresh() {},
            onShown: noopEvent, onClicked: noopEvent
        },
        commands: { onCommand: noopEvent },
        webRequest: { onBeforeRequest: noopEvent }
    };
    const context = vm.createContext({
        browser, console, fetch, AbortController, URL, Blob,
        navigator: { userAgent: "e2e", clipboard: { writeText: async () => {} } },
        setTimeout: (fn, ms) => { const t = setTimeout(fn, ms); timers.add(t); return t; },
        clearTimeout: (t) => clearTimeout(t),
        setInterval: (fn, ms) => { const t = setInterval(fn, ms); timers.add(t); return t; },
        clearInterval: (t) => clearInterval(t)
    });
    context.globalThis = context;
    // background-tasks.js is left out: it needs browser.alarms and the collector does not use it.
    ["lib/filter-core.js", "lib/sites.js", "lib/collector-core.js", "background.js", "background-collector.js"]
        .forEach((file) => vm.runInContext(read(file), context, { filename: file }));
    return {
        navigations,
        send: (message) => listeners.message.map((fn) => fn(message, {})).find((r) => r !== undefined),
        stop: () => timers.forEach((t) => { clearTimeout(t); clearInterval(t); })
    };
}

test("collector tab serves Agent OS Shopping through the real bridge, read-only, pausing at human checks",
    { timeout: 120000 }, async () => {
        const harness = startHarness();
        let firefox;
        try {
            const ready = await harness.next("ready");
            const tabBrowser = makeBrowser();
            const tabDom = makeDom(SHOP_PAGE, "https://www.walmart.com/search?q=usb+c+cable", tabBrowser);
            let clicked = 0;
            tabDom.window.document.getElementById("buy").addEventListener("click", () => { clicked += 1; });
            load(tabDom, ["lib/collector-core.js", "content/collector.js"]);
            firefox = fakeFirefox(ready.port, ready.token, tabBrowser);

            const set = await firefox.send({ type: "collector-set", tab_id: 7, on: true });
            assert.equal(set.ok, true);
            const status = await firefox.send({ type: "collector-status", tab_id: 7 });
            assert.equal(status.here, true);

            const session = (await harness.next("session")).session;
            assert.match(session.session_id, /^firefox-[a-z0-9]+-collector-7$/, "a separate session from the tab's normal one");
            assert.equal(session.capabilities.shopping_collector, true);
            assert.deepEqual(session.capabilities.ops, ["navigate", "wait", "scroll", "extract"]);

            const read = await harness.next("read");
            assert.equal(read.status.state, "completed", JSON.stringify(read.status));
            assert.deepEqual(read.status.result.steps.map((s) => s.kind), ["jsonld", "tiles", "groups"]);
            assert.equal(read.status.result.steps[1].data[0].price, "12.99");
            assert.deepEqual(firefox.navigations, ["https://www.walmart.com/search?q=usb+c+cable"]);
            if (Array.isArray(read.parsed)) {
                const titles = read.parsed.map((l) => l.title);
                assert.ok(titles.includes("Anker USB-C Cable 6ft"), "Shopping's parser reads the extension's result: " + titles);
                assert.ok(titles.includes("Belkin USB-C 3ft"));
            }

            const refused = (await harness.next("refused")).status;
            assert.equal(refused.state, "failed");
            assert.match(refused.error, /unsupported op for the shopping collector: click/);
            assert.equal(firefox.navigations.length, 1, "a command with a forbidden step is refused before any step runs");
            assert.equal(clicked, 0);

            await harness.next("go-captcha");
            tabDom.window.document.title = "Robot Check";
            tabDom.window.document.body.textContent = "Enter the characters you see below";
            const captcha = (await harness.next("captcha")).status;
            assert.equal(captcha.state, "approval_required");
            assert.equal(captcha.error, "human_verification_required");
            const badge = tabDom.window.document.getElementById("agent-os-shopping-collector-badge");
            assert.match(badge.textContent, /human check/);

            const pausedSession = await harness.next("paused-session");
            assert.equal(pausedSession.collector, null, "Shopping no longer finds a collector while paused");
            assert.equal(pausedSession.session.capabilities.collector_paused, true);
            const paused = (await harness.next("paused", 30000)).status;
            assert.equal(paused.state, "queued", "a paused collector takes no work");
            assert.equal((await firefox.send({ type: "collector-status", tab_id: 7 })).paused, true);

            await firefox.send({ type: "collector-resume", tab_id: 7 });
            assert.equal((await firefox.send({ type: "collector-status", tab_id: 7 })).paused, false);
            tabDom.window.close();
        } finally {
            if (firefox) firefox.stop();
            harness.child.kill();
        }
    });

// The Tampermonkey collector (agent-os-shopping, v0.1.6+) must stand down when this extension marks the page,
// otherwise two collectors would race for the same bridge commands.
const fs = require("node:fs");
const USERSCRIPT = path.resolve(process.env.AOS_SHOPPING_ROOT || path.join(__dirname, "..", "..", "..", "..", "agent-os-shopping"),
    "browser", "agent-os-shopping-collector.user.js");

test("Tampermonkey collector stands down when the extension marker is present",
    { skip: fs.existsSync(USERSCRIPT) ? false : "agent-os-shopping checkout not found next to personal-agent-os" }, () => {
        function run(marked) {
            const dom = new JSDOM("<html><body><p>shop</p></body></html>", { url: "https://www.walmart.com/", runScripts: "outside-only" });
            if (marked) dom.window.document.documentElement.setAttribute("data-agent-os-shopping-collector", "1");
            const menus = [];
            const requests = [];
            Object.assign(dom.window, {
                GM_registerMenuCommand: (name) => menus.push(name),
                GM_getValue: (k, d) => d, GM_setValue() {},
                GM_getTab: (cb) => cb({}), GM_saveTab() {},   // not a collector tab: menus only, no loop
                GM_xmlhttpRequest: (r) => requests.push(r)
            });
            dom.window.eval(fs.readFileSync(USERSCRIPT, "utf8"));
            return { menus, requests, dom };
        }
        const marked = run(true);
        assert.equal(marked.menus.length, 1);
        assert.match(marked.menus[0], /built into the Agent OS extension/);
        assert.equal(marked.requests.length, 0, "no bridge traffic from the stood-down copy");
        assert.equal(marked.dom.window.document.getElementById("agent-os-shopping-collector-badge"), null);
        const unmarked = run(false);
        assert.ok(unmarked.menus.some((m) => /make this the collector tab/.test(m)), "without the extension it still works");
        marked.dom.window.close();
        unmarked.dom.window.close();
    });
