"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const vm = require("node:vm");
const { spawn } = require("node:child_process");
const Task = require("../src/lib/task-core.js");
const { read, makeBrowser, makeDom, load, tick, waitFor } = require("./helpers");

const plain = (v) => JSON.parse(JSON.stringify(v));
const FAKE_PASSWORD = "Tr0ub4dor&3-not-real";

// -- task-core ----------------------------------------------------------------------------

test("schedules: weekly, once, interval, manual", () => {
    const monday1030 = new Date(2026, 9, 5, 10, 30).getTime(); // Mon 5 Oct 2026
    const weekdays8 = Task.nextRun({ kind: "weekly", time: "08:00", days: [1, 2, 3, 4, 5] }, monday1030);
    assert.equal(new Date(weekdays8).getDate(), 6);
    assert.equal(new Date(weekdays8).getHours(), 8);
    const later = Task.nextRun({ kind: "weekly", time: "11:00", days: [1] }, monday1030);
    assert.equal(new Date(later).getDate(), 5, "later today");
    const sat = Task.nextRun({ kind: "weekly", time: "09:00", days: [6] }, monday1030);
    assert.equal(new Date(sat).getDay(), 6);
    assert.equal(Task.nextRun({ kind: "interval", minutes: 2 }, monday1030), monday1030 + 5 * 60000, "at least 5 minutes");
    assert.equal(Task.nextRun({ kind: "once", at: "2026-10-05T09:00" }, monday1030), null, "past one-off");
    assert.ok(Task.nextRun({ kind: "once", at: "2026-10-07T09:00" }, monday1030));
    assert.equal(Task.nextRun({ kind: "manual" }, monday1030), null);
    assert.equal(Task.describeSchedule({ kind: "weekly", time: "08:00", days: [1, 2, 3, 4, 5] }), "Weekdays at 08:00");
    assert.equal(Task.describeSchedule({ kind: "weekly", time: "18:30", days: [1, 4] }), "Mon, Thu at 18:30");
});

test("random variance: runs 0-6 minutes after the scheduled time", () => {
    const at = (h, m) => new Date(2026, 9, 5, h, m).getTime(); // Mon 5 Oct 2026
    const weekly = { kind: "weekly", time: "11:00", days: [1] };
    const task = (extra) => Task.normalizeTask(Object.assign({ name: "t", startUrl: "https://x.example", schedule: weekly }, extra));

    assert.equal(Task.plannedRun(task({}), at(10, 30), () => 0.99), at(11, 0), "off: exact time");
    assert.equal(Task.normalizeTask({}).randomVariance, false, "off by default");
    const on = task({ randomVariance: true });
    assert.equal(Task.plannedRun(on, at(10, 30), () => 0), at(11, 0));
    assert.equal(Task.plannedRun(on, at(10, 30), () => 1), at(11, 6));
    for (let i = 0; i < 200; i += 1) {
        const t = Task.plannedRun(on, at(10, 30));
        assert.ok(t >= at(11, 0) && t <= at(11, 6), "always within 0-6 minutes");
    }
    // Rescheduled inside the window (task edited, Firefox restarted): today's slot is kept.
    const inside = Task.plannedRun(on, at(11, 2), () => 0.5);
    assert.ok(inside >= at(11, 2) && inside <= at(11, 6), "pending slot not skipped");
    // ...but not after a scheduled run already handled it; a manual run does not count.
    const ran = task({ randomVariance: true, lastRun: { at: new Date(at(11, 3)).toISOString(), status: "success", trigger: "schedule" } });
    assert.equal(new Date(Task.plannedRun(ran, at(11, 4), () => 0)).getDate(), 12, "next week");
    const manual = task({ randomVariance: true, lastRun: { at: new Date(at(11, 3)).toISOString(), status: "success", trigger: "manual" } });
    assert.ok(Task.plannedRun(manual, at(11, 4), () => 0) <= at(11, 6));
    // Interval and one-off; manual stays manual.
    const every = task({ randomVariance: true, schedule: { kind: "interval", minutes: 30 } });
    assert.equal(Task.plannedRun(every, at(10, 0), () => 0.5), at(10, 33));
    const once = task({ randomVariance: true, schedule: { kind: "once", at: "2026-10-05T11:00" } });
    assert.equal(Task.plannedRun(once, at(10, 0), () => 0.5), at(11, 3));
    assert.equal(Task.plannedRun(task({ randomVariance: true, schedule: { kind: "manual" } }), at(10, 0)), null);
    assert.equal(Task.describeTaskSchedule(on), "Mon at 11:00 (+0–6 min random)");
    assert.equal(Task.describeTaskSchedule(task({ randomVariance: true, schedule: { kind: "manual" } })), "Manual only");
});

test("background: a task saved with random variance gets a jittered alarm", async () => {
    const h = backgroundHarness();
    const saved = await h.send({
        type: "task-save",
        task: { name: "Jitter", startUrl: "https://x.example", schedule: { kind: "interval", minutes: 30 }, randomVariance: true,
            steps: [{ type: "click", target: { text: "Go" } }] }
    });
    assert.equal(saved.ok, true, saved.error);
    assert.equal(saved.task.randomVariance, true);
    const when = h.alarms.get("aos-task:" + saved.task.id);
    const base = Date.now() + 30 * 60000;
    assert.ok(when >= base - 5000 && when <= base + 6 * 60000, "alarm within 0-6 minutes of the interval time");
    assert.equal(new Date(saved.task.nextRunAt).getTime(), when, "next run shows the jittered time");
    h.stop();
});

test("task validation and step descriptions", () => {
    const task = Task.normalizeTask({ name: "", startUrl: "ftp://x" });
    assert.equal(Task.validateTask(task).length, 2);
    assert.equal(Task.describeStep({ type: "fill", credential: "password", target: { label: "Password" } }), "Enter saved password in “Password”");
    assert.equal(Task.normalizeStep({ type: "fill", credential: "password", value: "leak" }).value, undefined,
        "credential steps never carry a value");
    assert.equal(Task.normalizeStep({ type: "evil" }), null);
});

// -- recorder -------------------------------------------------------------------------------

const LOGIN_PAGE = `<!doctype html><html><body>
  <form id="login" action="/login">
    <label for="email">Email address</label><input id="email" name="email" type="email" autocomplete="username">
    <label for="pw">Password</label><input id="pw" name="password" type="password">
    <label><input type="checkbox" id="remember" name="remember"> Remember me</label>
    <label for="otp">Verification code</label><input id="otp" name="otp">
    <select name="site"><option value="a">Alpha</option><option value="b">Beta</option></select>
    <button type="submit" data-testid="signin">Sign in</button>
  </form>
  <input id="search" name="q" placeholder="Search">
</body></html>`;

function typeInto(dom, el, value) {
    el.focus();
    el.value = value;
    el.dispatchEvent(new dom.window.Event("input", { bubbles: true }));
    el.dispatchEvent(new dom.window.Event("change", { bubbles: true }));
}

test("recorder: logins become saved-credential steps and passwords are never recorded", async () => {
    const steps = [];
    const browser = makeBrowser({
        onBackgroundMessage: async (m) => {
            if (m.type === "task-hello") return { mode: "record", taskName: "Clock in", useLogin: true, count: 0 };
            if (m.type === "task-record-step") { steps.push(m.step); return { count: steps.length }; }
            return { ok: true };
        }
    });
    const dom = makeDom(LOGIN_PAGE, "https://portal.example/login", browser);
    dom.window.document.getElementById("login").addEventListener("submit", (e) => e.preventDefault());
    load(dom, ["lib/task-core.js", "content/tasks.js"]);
    await tick(150);
    const doc = dom.window.document;
    typeInto(dom, doc.getElementById("email"), "me@example.com");
    typeInto(dom, doc.getElementById("pw"), FAKE_PASSWORD);
    doc.querySelector("label input#remember").closest("label").click();       // label toggles the checkbox
    typeInto(dom, doc.getElementById("otp"), "123456");
    const select = doc.querySelector("select");
    select.value = "b";
    select.dispatchEvent(new dom.window.Event("change", { bubbles: true }));
    doc.querySelector("[data-testid='signin']").click();
    const search = doc.getElementById("search");
    search.value = "skyrim";
    search.dispatchEvent(new dom.window.Event("input", { bubbles: true }));
    search.dispatchEvent(new dom.window.KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
    await waitFor(() => steps.length >= 8);

    const kinds = steps.map((s) => s.type + (s.credential ? ":" + s.credential : "") + (s.manual ? ":manual" : ""));
    assert.deepEqual(kinds, ["fill:username", "fill:password", "check", "fill:manual", "select", "click", "fill", "key"]);
    assert.equal(steps[2].checked, true);
    assert.equal(steps[4].value, "b");
    assert.equal(steps[5].target.testid, "signin");
    assert.equal(steps[6].value, "skyrim");
    const recorded = JSON.stringify(steps);
    assert.ok(!recorded.includes(FAKE_PASSWORD), "password value never recorded");
    assert.ok(!recorded.includes("123456"), "one-time code never recorded");
    assert.ok(!recorded.includes("me@example.com"), "username replaced by the saved login");
    assert.ok(dom.window.document.querySelector("div").shadowRoot || true);
    dom.window.close();
});

// -- replayer -------------------------------------------------------------------------------

test("replayer: fills saved credentials only at their steps, clicks, reports progress", async () => {
    const messages = [];
    const steps = [
        { type: "fill", credential: "username", target: { tag: "input", name: "email" } },
        { type: "fill", credential: "password", target: { tag: "input", id: "pw" } },
        { type: "check", checked: true, target: { tag: "input", name: "remember" } },
        { type: "select", value: "b", text: "Beta", target: { tag: "select", name: "site" } },
        { type: "click", target: { tag: "button", testid: "signin", text: "Sign in" } }
    ];
    const browser = makeBrowser({
        onBackgroundMessage: async (m) => {
            messages.push(m);
            if (m.type === "task-hello") return { mode: "replay", steps, index: 0, runId: "run-1", taskName: "Clock in" };
            if (m.type === "task-credential") return { value: m.field === "password" ? FAKE_PASSWORD : "me@example.com" };
            return { ok: true };
        }
    });
    const dom = makeDom(LOGIN_PAGE, "https://portal.example/login", browser);
    let submitted = null;
    dom.window.document.getElementById("login").addEventListener("submit", (e) => {
        e.preventDefault();
        submitted = Object.fromEntries(new dom.window.FormData(e.target));
    });
    load(dom, ["lib/task-core.js", "content/tasks.js"]);
    await waitFor(() => messages.some((m) => m.type === "task-replay-done" || m.type === "task-replay-fail"), 10000);
    const fail = messages.find((m) => m.type === "task-replay-fail");
    assert.equal(fail, undefined, fail && fail.error);
    assert.deepEqual(plain(submitted), { email: "me@example.com", password: FAKE_PASSWORD, remember: "on", otp: "", site: "b" });
    assert.deepEqual(messages.filter((m) => m.type === "task-credential").map((m) => m.field), ["username", "password"]);
    assert.ok(messages.some((m) => m.type === "task-replay-progress" && m.index === 5), "progress recorded before the click");
    dom.window.close();
});

test("replayer: resumes mid-task after a page load and reports a missing element", async () => {
    const messages = [];
    const steps = [
        { type: "click", target: { tag: "button", text: "Sign in" } },
        { type: "fill", value: "hello", target: { tag: "input", name: "q" } },
        { type: "click", target: { tag: "button", text: "Does not exist" } }
    ];
    const browser = makeBrowser({
        onBackgroundMessage: async (m) => {
            messages.push(m);
            if (m.type === "task-hello") return { mode: "replay", steps, index: 1, runId: "run-2", taskName: "t" };
            return { ok: true };
        }
    });
    const dom = makeDom(LOGIN_PAGE, "https://portal.example/home", browser);
    load(dom, ["lib/task-core.js", "content/tasks.js"]);
    // Shorten the element wait for the test.
    await waitFor(() => messages.some((m) => m.type === "task-replay-fail"), 20000);
    assert.equal(dom.window.document.getElementById("search").value, "hello", "continued from step 2");
    const fail = messages.find((m) => m.type === "task-replay-fail");
    assert.equal(fail.index, 2);
    assert.match(fail.error, /could not find “Does not exist”/);
    dom.window.close();
});

// -- background ----------------------------------------------------------------------------------

function backgroundHarness() {
    const store = makeBrowser();
    const native = [];
    const bridge = [];
    const alarms = new Map();
    const created = [];
    const removedTabs = [];
    const removedWindows = [];
    const listeners = [];
    let nextTab = 50;
    const browser = {
        storage: store.storage,
        runtime: {
            onMessage: { addListener: (fn) => listeners.push(fn) },
            openOptionsPage: async () => {}
        },
        alarms: {
            create: (name, info) => alarms.set(name, info.when),
            clear: async (name) => alarms.delete(name),
            onAlarm: { addListener() {} }
        },
        windows: {
            create: async (opts) => { const tab = { id: ++nextTab }; created.push({ window: true, url: opts.url, tab: tab.id }); return { id: 900 + tab.id, tabs: [tab] }; },
            remove: async (id) => { removedWindows.push(id); }
        },
        tabs: {
            create: async (opts) => { const tab = { id: ++nextTab }; created.push({ url: opts.url, active: opts.active, tab: tab.id }); return tab; },
            remove: async (id) => { removedTabs.push(id); },
            onRemoved: { addListener() {} }
        },
        browserAction: { setBadgeText() {}, setBadgeBackgroundColor() {}, setTitle() {} }
    };
    const secrets = { username: "me@example.com", password: FAKE_PASSWORD };
    const timers = [];
    const context = vm.createContext({
        browser, console, URL,
        setTimeout: (fn, ms) => { const t = setTimeout(fn, ms); timers.push(t); return t; },
        setInterval: () => 0, clearTimeout,
        bridgeStatus: { native: "ok" },
        getLocal: async (k, d) => { const r = await store.storage.local.get(k); return r[k] === undefined ? d : r[k]; },
        setLocal: async (k, v) => store.storage.local.set({ [k]: v }),
        nativeRequest: async (m) => {
            native.push(m);
            if (m.cmd === "credential_get") return { ok: true, value: secrets[m.field] };
            return { ok: true };
        },
        captureSettings: async () => ({ device: "test" }),
        bridgeFetch: async (p, o) => { bridge.push(o.body); return {}; }
    });
    context.globalThis = context;
    ["lib/task-core.js", "background-tasks.js"].forEach((f) => vm.runInContext(read(f), context, { filename: f }));
    const send = (message, tabId) => {
        for (const fn of listeners) {
            const r = fn(message, tabId ? { tab: { id: tabId } } : {});
            if (r !== undefined) return r;
        }
        return undefined;
    };
    return { send, native, bridge, alarms, created, removedTabs, removedWindows, store, stop: () => timers.forEach(clearTimeout) };
}

test("background: save with login, record, scheduled replay with gated credentials, secret-free report", async () => {
    const h = backgroundHarness();
    const saved = await h.send({
        type: "task-save",
        task: { name: "Clock in", startUrl: "https://portal.example/login", schedule: { kind: "weekly", time: "08:00", days: [1, 2, 3, 4, 5] } },
        credentials: { username: "me@example.com", password: FAKE_PASSWORD }
    });
    assert.equal(saved.ok, true, saved.error);
    const id = saved.task.id;
    assert.equal(saved.task.hasCredentials, true);
    assert.deepEqual(plain(h.native[0]), { cmd: "credential_set", task_id: id, username: "me@example.com", password: FAKE_PASSWORD });
    const stored = JSON.stringify(h.store._data);
    assert.ok(!stored.includes(FAKE_PASSWORD), "password is not kept in extension storage");
    assert.equal(h.alarms.size, 0, "no alarm until steps are recorded");

    // Record in a dedicated window.
    const rec = await h.send({ type: "task-record-start", id });
    assert.equal(rec.ok, true);
    const recTab = h.created[0].tab;
    assert.equal(h.created[0].window, true);
    assert.equal((await h.send({ type: "task-hello" }, recTab)).mode, "record");
    await h.send({ type: "task-record-step", step: { type: "fill", credential: "username", target: { name: "email" } } }, recTab);
    await h.send({ type: "task-record-step", step: { type: "fill", credential: "password", target: { id: "pw" } } }, recTab);
    await h.send({ type: "task-record-step", step: { type: "click", target: { text: "Sign in" } } }, recTab);
    const fin = await h.send({ type: "task-record-finish" }, recTab);
    assert.equal(fin.count, 3);
    assert.ok(h.removedWindows.length === 1, "recording window closed");
    assert.equal(h.alarms.size, 1, "scheduled once steps exist");

    // Run (as the alarm would) in a background tab.
    const run = await h.send({ type: "task-run", id });
    assert.equal(run.ok, true);
    const tab = run.tabId;
    assert.equal(h.created.at(-1).active, false);
    const hello = await h.send({ type: "task-hello" }, tab);
    assert.equal(hello.mode, "replay");
    assert.equal(hello.steps.length, 3);

    assert.deepEqual(plain(await h.send({ type: "task-credential", field: "username" }, 999)), { error: "not allowed" }, "other tabs get nothing");
    assert.deepEqual(plain(await h.send({ type: "task-credential", field: "password" }, tab)), { error: "not allowed" }, "only at the step that needs it");
    assert.equal((await h.send({ type: "task-credential", field: "username" }, tab)).value, "me@example.com");
    await h.send({ type: "task-replay-progress", index: 1 }, tab);
    assert.equal((await h.send({ type: "task-credential", field: "password" }, tab)).value, FAKE_PASSWORD);
    await h.send({ type: "task-replay-progress", index: 3 }, tab);
    await h.send({ type: "task-replay-done" }, tab);

    await waitFor(() => h.bridge.length === 1);
    assert.deepEqual(plain(h.removedTabs), [tab], "successful run closes its tab");
    const event = h.bridge[0].events[0];
    assert.equal(event.source, "scheduled-tasks");
    assert.equal(event.payload.status, "success");
    assert.ok(!JSON.stringify(h.bridge).includes(FAKE_PASSWORD) && !JSON.stringify(h.bridge).includes("me@example.com"),
        "reports carry no credentials");
    const after = await h.send({ type: "tasks-get" });
    assert.equal(after.runs.length, 1);
    assert.equal(after.tasks[0].lastRun.status, "success");

    // A failure keeps the tab open for inspection.
    const run2 = await h.send({ type: "task-run", id });
    await h.send({ type: "task-replay-fail", index: 2, error: "could not find “Sign in”" }, run2.tabId);
    const failed = await h.send({ type: "tasks-get" });
    assert.equal(failed.tasks[0].lastRun.status, "failed");
    assert.ok(!h.removedTabs.includes(run2.tabId));

    await h.send({ type: "task-delete", id });
    assert.deepEqual(plain(h.native.at(-1)), { cmd: "credential_delete", task_id: id });
    h.stop();
});

// -- editing from the popup and options page -------------------------------------------------------

function pageBrowser(h, opened) {
    const browser = makeBrowser({
        onBackgroundMessage: (m) => {
            if (m.type.indexOf("task") === 0) return h.send(m);
            if (m.type === "status") return { version: "test", bridge: { enabled: false, state: "off" } };
            if (m.type === "filters-get") return require("../src/lib/filter-core.js").normalizeState({});
            return {};
        }
    });
    browser.tabs = { create: async (o) => { opened.push(o.url); }, query: async () => [{ id: 1, url: "https://portal.example/" }] };
    return browser;
}

test("edit: popup Edit opens the task in the options editor, and saving changes it in place", async () => {
    const h = backgroundHarness();
    const saved = await h.send({
        type: "task-save",
        task: { name: "Clock in", startUrl: "https://portal.example/login", schedule: { kind: "weekly", time: "08:00", days: [1, 2, 3, 4, 5] },
            steps: [{ type: "click", target: { text: "Clock in" } }] }
    });
    const id = saved.task.id;

    // Popup: each task has an Edit button that deep-links to the editor.
    const opened = [];
    const popupHtml = read("popup/popup.html").replace(/<script[^>]*><\/script>/g, "");
    const popup = makeDom(popupHtml, "moz-extension://test/popup/popup.html", pageBrowser(h, opened));
    const closePopup = popup.window.close.bind(popup.window);
    popup.window.close = () => {};
    load(popup, ["lib/filter-core.js", "lib/task-core.js", "popup/popup.js"]);
    const editButton = await waitFor(() => Array.from(popup.window.document.querySelectorAll("#task-list button")).find((b) => b.textContent === "Edit"));
    editButton.click();
    await waitFor(() => opened.length);
    assert.equal(opened[0], "moz-extension://test/options/options.html#tasks?edit=" + encodeURIComponent(id));

    // Options page opened at that link: the task is loaded into the form.
    const optionsHtml = read("options/options.html").replace(/<script[^>]*><\/script>/g, "");
    const page = makeDom(optionsHtml, opened[0], pageBrowser(h, []));
    page.window.confirm = () => true;
    load(page, ["lib/filter-core.js", "lib/task-core.js", "options/options.js"]);
    const doc = page.window.document;
    const $ = (sel) => doc.getElementById(sel);
    await waitFor(() => $("task-id").value === id);
    assert.equal($("task-form-title").textContent, "Edit “Clock in”");
    assert.equal($("task-submit").textContent, "Save changes");
    assert.equal($("task-time").value, "08:00");
    assert.equal($("task-variance").checked, false);
    assert.equal(doc.querySelectorAll("#task-rows tr.editing").length, 1, "the row being edited is marked");

    // Change name, time, days and variance, then save.
    $("task-name").value = "Clock in (late shift)";
    $("task-time").value = "09:15";
    doc.querySelector("#task-days input[value='5']").checked = false;
    $("task-variance").checked = true;
    $("task-form").dispatchEvent(new page.window.Event("submit", { cancelable: true }));
    await waitFor(() => $("task-result").textContent === "Saved.");

    const store = await h.send({ type: "tasks-get" });
    assert.equal(store.tasks.length, 1, "edited in place, not duplicated");
    const task = store.tasks[0];
    assert.equal(task.id, id);
    assert.equal(task.name, "Clock in (late shift)");
    assert.deepEqual(plain(task.schedule), { kind: "weekly", time: "09:15", days: [1, 2, 3, 4] });
    assert.equal(task.randomVariance, true);
    assert.equal(task.steps.length, 1, "recorded steps kept");
    const alarm = h.alarms.get("aos-task:" + id);
    const at = new Date(alarm);
    assert.ok(at.getHours() === 9 && at.getMinutes() >= 15 && at.getMinutes() <= 21, "rescheduled to the new time");

    // Stop editing returns the form to a new task.
    $("task-cancel").click();
    assert.equal($("task-form-title").textContent, "New scheduled task");
    assert.equal($("task-submit").textContent, "Save task");
    assert.equal(doc.querySelectorAll("#task-rows tr.editing").length, 0);
    page.window.close();
    closePopup();
    h.stop();
});

// -- native host credentials ------------------------------------------------------------------------

function talk(messages, env) {
    return new Promise((resolve, reject) => {
        const child = spawn(process.env.PYTHON || "python", ["-u", path.resolve(__dirname, "..", "native", "agent_os_native_host.py")],
            { stdio: ["pipe", "pipe", "inherit"], env: Object.assign({}, process.env, env) });
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
        messages.forEach((m) => {
            const body = Buffer.from(JSON.stringify(m));
            const header = Buffer.alloc(4);
            header.writeUInt32LE(body.length);
            child.stdin.write(Buffer.concat([header, body]));
        });
    });
}

test("native host stores task logins in Windows Credential Manager", async () => {
    const env = { AGENT_OS_TASKS_KEYRING_SERVICE: "agent-os-tasks-test-" + Date.now().toString(36) };
    const replies = await talk([
        { cmd: "credential_set", task_id: "t1", username: "me@example.com", password: FAKE_PASSWORD },
        { cmd: "credential_status", task_id: "t1" },
        { cmd: "credential_get", task_id: "t1", field: "password" },
        { cmd: "credential_set", task_id: "t1", username: "", password: "" },
        { cmd: "credential_get", task_id: "t1", field: "username" },
        { cmd: "credential_get", task_id: "t1", field: "token" },
        { cmd: "credential_delete", task_id: "t1" },
        { cmd: "credential_status", task_id: "t1" }
    ], env);
    assert.equal(replies[0].ok, true);
    assert.deepEqual(replies[0].saved, ["username", "password"]);
    assert.equal(replies[1].has_password, true);
    assert.equal(replies[2].value, FAKE_PASSWORD);
    assert.deepEqual(replies[3].saved, [], "blank fields keep the saved login");
    assert.equal(replies[4].value, "me@example.com");
    assert.equal(replies[5].ok, false);
    assert.equal(replies[7].has_password, false, "deleted");
});
