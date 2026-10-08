"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { DIST, makeBrowser, sendToContent, makeDom, load, waitFor } = require("./helpers");

const GENERATED = path.join(DIST, "content", "capture.generated.js");

test("bundled Universal Capture boots on the GM shim and registers its menu", { skip: !fs.existsSync(GENERATED) && "run tools/build.py first" }, async () => {
    const requests = [];
    const browser = makeBrowser({
        storage: {
            "gm:agent_os_capture_settings_v1": {
                bridgeEnabled: true,
                bridgeEndpoint: "http://127.0.0.1:8766/api/v1/browser/batch",
                bridgeToken: "test-token",
                browserJournalEnabled: true
            }
        },
        onBackgroundMessage: async (message) => {
            if (message.type === "gm-xhr") {
                requests.push(message);
                const body = JSON.parse(message.data || "{}");
                const ids = (body.events || []).map((e) => e.event_id);
                return { status: 200, responseText: JSON.stringify({ durable: true, acknowledged: ids }) };
            }
            return undefined;
        }
    });
    const logs = [];
    const dom = makeDom("<!doctype html><html><head><title>Example</title></head><body><p>Hello</p></body></html>",
        "https://example.com/article", browser);
    dom.window.console.info = (...args) => logs.push(args.join(" "));
    load(dom, ["content/gm-shim.js"]);
    load(dom, ["content/capture.generated.js"], DIST);

    await waitFor(() => logs.find((l) => /Universal Capture v[\d.]+ loaded/.test(l)));
    const menu = await sendToContent(browser, { type: "gm-menu-list" });
    const names = menu.commands.map((c) => c.name);
    assert.ok(names.includes("Agent OS: Save current page"));
    assert.ok(names.includes("Agent OS: Configure local bridge"));
    assert.ok(!names.some((n) => /Update this userscript|Browser control/.test(n)), "Tampermonkey-only commands hidden in the extension");
    assert.equal(dom.window.document.getElementById("agent-os-tampermonkey-update"), null, "no Tampermonkey updater button");
    assert.ok(dom.window.document.getElementById("agent-os-universal-save"), "floating save button");

    // Journal rows are written through GM_setValue into extension storage.
    await waitFor(() => Object.keys(browser._data).some((k) => k.startsWith("gm:agent_os_browser_journal_chunk_v1:")), 4000);

    // Saving the page goes through GM_xmlhttpRequest -> background proxy.
    await sendToContent(browser, { type: "gm-menu-run", name: "Agent OS: Save current page" });
    const capture = await waitFor(() => requests.find((r) => /\/capture$/.test(r.url)), 4000);
    assert.equal(capture.headers["X-Agent-OS-Token"], "test-token");
    assert.equal(JSON.parse(capture.data).url, "https://example.com/article");
    dom.window.close();
});

test("a Tampermonkey copy stands down when the extension marker is present", async () => {
    const source = fs.readFileSync(path.resolve(__dirname, "..", "..", "userscripts", "agent-os-universal-capture.user.js"), "utf8");
    const browser = makeBrowser();
    const dom = makeDom("<!doctype html><html data-agent-os-extension='1.0.0'><body></body></html>", "https://example.com/", browser);
    const logs = [];
    dom.window.console.info = (...args) => logs.push(args.join(" "));
    load(dom, ["content/gm-shim.js"]);
    dom.window.eval(source);
    assert.ok(logs.some((l) => /standing down/.test(l)));
    assert.equal(dom.window.document.getElementById("agent-os-universal-save"), null);
    dom.window.close();
});

test("save buttons show items already in Agent OS; sheet rows carry their tab", { skip: !fs.existsSync(GENERATED) && "run tools/build.py first" }, async () => {
    const requests = [];
    const browser = makeBrowser({
        storage: {
            "gm:agent_os_capture_settings_v1": {
                bridgeEnabled: true,
                bridgeEndpoint: "http://127.0.0.1:8766/api/v1/browser/batch",
                bridgeToken: "test-token",
                browserJournalEnabled: false,
                sheetMirrorEnabled: true,
                sheetEndpoint: "https://script.google.com/macros/s/test/exec"
            },
            "gm:agent_os_saved_captures_v1": { "nexus:skyrimspecialedition:1": "2026-10-06T00:00:00Z" }
        },
        onBackgroundMessage: async (message) => {
            if (message.type !== "gm-xhr") return undefined;
            requests.push(message);
            if (/\/capture\/status$/.test(message.url)) {
                const keys = JSON.parse(message.data).keys;
                return { status: 200, responseText: JSON.stringify({ saved: keys.filter((k) => k === "nexus:skyrimspecialedition:2") }) };
            }
            if (/\/capture$/.test(message.url)) return { status: 200, responseText: JSON.stringify({ status: "stored" }) };
            return { status: 200, responseText: "{}" };
        }
    });
    const tile = (id) => `<div class="mod-tile" id="t${id}"><a href="https://www.nexusmods.com/skyrimspecialedition/mods/${id}"><img></a>
        <h3>Mod ${id}</h3><a href="https://www.nexusmods.com/profile/Author${id}">Author${id}</a></div>`;
    const dom = makeDom(`<!doctype html><html><body><main>${tile(1)}${tile(2)}${tile(3)}</main></body></html>`,
        "https://www.nexusmods.com/games/skyrimspecialedition/mods", browser);
    load(dom, ["content/gm-shim.js"]);
    load(dom, ["content/capture.generated.js"], DIST);
    const doc = dom.window.document;
    const button = (id) => doc.querySelector(`#t${id} .agent-os-card-save`);

    await waitFor(() => button(1) && button(1).textContent === "✓ In Agent OS");
    await waitFor(() => button(2).textContent === "✓ In Agent OS", 4000);
    assert.equal(button(3).textContent, "+ Agent OS");

    button(3).click();
    const capture = await waitFor(() => requests.find((r) => /\/capture$/.test(r.url)), 4000);
    assert.equal(JSON.parse(capture.data).author, "Author3");
    await waitFor(() => button(3).textContent === "✓ In Agent OS", 4000);
    assert.ok(browser._data["gm:agent_os_saved_captures_v1"]["nexus:skyrimspecialedition:3"]);
    const sheet = await waitFor(() => requests.find((r) => /script\.google\.com/.test(r.url)), 4000);
    assert.equal(JSON.parse(sheet.data).sheet_tab, "Mod Intake");
    dom.window.close();
});

test("a mod's own page gets no '+ Agent OS' card buttons (tabs, description, requirements)", { skip: !fs.existsSync(GENERATED) && "run tools/build.py first" }, async () => {
    const browser = makeBrowser({ storage: { "gm:agent_os_capture_settings_v1": { browserJournalEnabled: false } }, onBackgroundMessage: async () => undefined });
    const tabs = ["description", "files", "images"].map((t) => `<li><a href="/skyrimspecialedition/mods/194125?tab=${t}">${t}</a></li>`).join("");
    const requirement = `<li class="mod-tile"><a href="/skyrimspecialedition/mods/5"><img></a><a href="/skyrimspecialedition/mods/5">Requirement</a></li>`;
    const dom = makeDom(`<!doctype html><html><body><main><h1>Gelado</h1><ul class="tabs">${tabs}</ul><div class="description"><ul>${requirement}</ul></div></main></body></html>`,
        "https://www.nexusmods.com/skyrimspecialedition/mods/194125", browser);
    try {
        const logs = [];
        dom.window.console.info = (...args) => logs.push(args.join(" "));
        load(dom, ["content/gm-shim.js"]);
        load(dom, ["content/capture.generated.js"], DIST);
        await waitFor(() => logs.find((l) => /Universal Capture v[\d.]+ loaded/.test(l)));
        await new Promise((r) => setTimeout(r, 500));
        assert.equal(dom.window.document.querySelectorAll(".agent-os-card-save").length, 0);
        assert.ok(dom.window.document.getElementById("agent-os-universal-save"), "the page's own save button stays");
    } finally {
        dom.window.close();
    }
});

test("old reddit: small hover icons after the title, user and subreddit; no journal indicator", { skip: !fs.existsSync(GENERATED) && "run tools/build.py first" }, async () => {
    const browser = makeBrowser({ storage: { "gm:agent_os_capture_settings_v1": { browserJournalEnabled: true } }, onBackgroundMessage: async () => undefined });
    const dom = makeDom(`<!doctype html><html><body><div id="siteTable"><div class="thing link" data-fullname="t3_abc">
        <p class="title"><a class="title" href="https://old.reddit.com/r/pics/comments/abc/cat/">Cat</a></p>
        <p class="tagline">submitted by <a class="author" href="https://old.reddit.com/user/alice">alice</a> to <a class="subreddit hover" href="https://old.reddit.com/r/pics/">r/pics</a></p>
        <ul class="flat-list buttons"><li><a href="https://old.reddit.com/r/pics/comments/abc/cat/">comments</a></li></ul>
      </div></div></body></html>`, "https://old.reddit.com/", browser);
    try {
        const logs = [];
        dom.window.console.info = (...args) => logs.push(args.join(" "));
        load(dom, ["content/gm-shim.js"]);
        load(dom, ["content/capture.generated.js"], DIST);
        const doc = dom.window.document;
        await waitFor(() => doc.querySelector("a.title + .agent-os-reddit-post-save.agent-os-hover-icon"));
        assert.equal(doc.querySelector(".agent-os-reddit-post-save").textContent, "＋");
        assert.ok(doc.querySelector("p.title").classList.contains("agent-os-title-host"));
        await waitFor(() => doc.querySelector("a.author + .agent-os-hover-icon[data-agent-os-follow-key='reddit-user:alice']"));
        assert.ok(doc.querySelector("a.subreddit + .agent-os-hover-icon[data-agent-os-follow-key='reddit-subreddit:pics']"));
        assert.equal(doc.querySelectorAll(".flat-list .agent-os-follow-target, .tagline > .agent-os-follow-target:not(.agent-os-hover-icon)").length, 0);
        assert.equal(doc.getElementById("agent-os-browser-journal-status"), null, "journal indicator hidden");
    } finally {
        dom.window.close();
    }
});
