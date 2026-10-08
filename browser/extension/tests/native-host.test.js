"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const vm = require("node:vm");
const { spawn } = require("node:child_process");
const { read, makeBrowser } = require("./helpers");

const HOST = path.resolve(__dirname, "..", "native", "agent_os_native_host.py");

function frame(obj) {
    const body = Buffer.from(JSON.stringify(obj), "utf8");
    const header = Buffer.alloc(4);
    header.writeUInt32LE(body.length, 0);
    return Buffer.concat([header, body]);
}

function talk(messages, env) {
    return new Promise((resolve, reject) => {
        const child = spawn(process.env.PYTHON || "python", ["-u", HOST],
            { stdio: ["pipe", "pipe", "inherit"], env: Object.assign({}, process.env, env || {}) });
        let buffer = Buffer.alloc(0);
        const replies = [];
        child.stdout.on("data", (chunk) => {
            buffer = Buffer.concat([buffer, chunk]);
            while (buffer.length >= 4) {
                const len = buffer.readUInt32LE(0);
                if (buffer.length < 4 + len) break;
                replies.push(JSON.parse(buffer.subarray(4, 4 + len).toString("utf8")));
                buffer = buffer.subarray(4 + len);
            }
            if (replies.length === messages.length) child.stdin.end();
        });
        child.on("exit", () => resolve(replies));
        child.on("error", reject);
        messages.forEach((m) => child.stdin.write(frame(m)));
    });
}

test("native host speaks the Firefox framing protocol", async () => {
    const replies = await talk([{ cmd: "hello" }, { cmd: "bridge_config", ensure: false }, { cmd: "nope" }]);
    assert.equal(replies[0].ok, true);
    assert.match(replies[0].repo, /personal-agent-os$/);
    assert.equal(replies[1].ok, true);
    assert.equal(replies[1].endpoint, "http://127.0.0.1:8766/api/v1/browser/batch");
    assert.ok(replies[1].token.length >= 20, "returns the local bridge token");
    assert.equal(typeof replies[1].running, "boolean");
    assert.equal(typeof replies[1].managed_settings, "object", "machine-managed extension settings");
    assert.equal(replies[2].ok, false);
});

test("native host manages AI browser routines", async () => {
    const home = require("node:fs").mkdtempSync(path.join(require("node:os").tmpdir(), "aos-routines-"));
    const routine = { name: "Digest", instructions: "List new mods.", start_url: "https://www.nexusmods.com/games/stardewvalley/mods", schedule: "daily 08:00" };
    const replies = await talk([
        { cmd: "routine_save", routine },
        { cmd: "routines_list" },
        { cmd: "routines_tick" },
        { cmd: "routine_runs" },
        { cmd: "routine_save", routine: { name: "bad", instructions: "x", start_url: "ftp://x" } },
        { cmd: "routine_run", routine_id: "missing" }
    ], { AGENT_OS_BROWSER_ROUTINES_HOME: home });
    assert.equal(replies[0].ok, true);
    assert.deepEqual(replies[0].routine.allowed_domains, ["nexusmods.com"]);
    assert.ok(replies[0].routine.next_run_at, "scheduled routine has a next run");
    assert.equal(replies[1].routines.length, 1);
    assert.equal(replies[1].routines[0].instructions, "List new mods.");
    assert.deepEqual(replies[2].due, [], "nothing due yet, nothing spawned");
    assert.deepEqual(replies[3].runs, []);
    assert.equal(replies[4].ok, false);
    assert.match(replies[4].error, /start_url/);
    assert.equal(replies[5].ok, false);
    const del = await talk([{ cmd: "routine_delete", routine_id: replies[0].routine.id }, { cmd: "routines_list" }],
        { AGENT_OS_BROWSER_ROUTINES_HOME: home });
    assert.equal(del[0].deleted, true);
    assert.equal(del[1].routines.length, 0);
});

// Hits the public Nexus GraphQL API through background.js's lookup code.
test("nexus lookup against the live API", { skip: !process.env.AOS_NETWORK_TESTS && "set AOS_NETWORK_TESTS=1" }, async () => {
    const storage = makeBrowser();
    const handlers = [];
    const noop = { addListener() {} };
    const timers = [];
    const context = vm.createContext({
        console, fetch, AbortController, URL,
        navigator: { userAgent: "test", clipboard: { writeText: async () => {} } },
        setTimeout: (fn, ms) => { const t = setTimeout(fn, ms); timers.push(t); return t; },
        clearTimeout, setInterval: () => 0, clearInterval: () => {},
        browser: {
            storage: storage.storage,
            runtime: {
                getManifest: () => ({ version: "t" }),
                sendNativeMessage: () => Promise.reject(new Error("No such native application")),
                onMessage: { addListener: (fn) => handlers.push(fn) },
                onInstalled: noop
            },
            tabs: { query: async () => [], onRemoved: noop, onUpdated: noop, onActivated: noop },
            menus: { removeAll: async () => {}, create() {}, onShown: noop, onClicked: noop },
            commands: { onCommand: noop },
            webRequest: { onBeforeRequest: noop }
        }
    });
    context.globalThis = context;
    ["lib/filter-core.js", "lib/sites.js", "background.js"].forEach((f) => vm.runInContext(read(f), context, { filename: f }));
    const result = await handlers[0]({
        type: "nexus-lookup",
        items: [{ game: "skyrimspecialedition", modId: "266" }, { game: "stardewvalley", modId: "2400" }, { game: "skyrimspecialedition", modId: "999999999" }]
    }, {});
    const ussep = result.mods["skyrimspecialedition:266"];
    assert.equal(ussep.uploader, "Arthmoor");
    assert.ok(ussep.tags.includes("Lore-Friendly"));
    assert.equal(ussep.gameName, "Skyrim Special Edition");
    assert.ok(result.mods["stardewvalley:2400"].name);
    assert.equal(result.mods["skyrimspecialedition:999999999"], null);
    timers.forEach(clearTimeout);
});
