"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { makeBrowser, makeDom, load, waitFor } = require("./helpers");

function adpPage(browser) {
    const dom = makeDom(`<!doctype html><html><body><h1>Welcome to ADP</h1>
        <sdf-input id="login-form_password"></sdf-input><sdf-button id="signBtn">Sign in</sdf-button></body></html>`,
        "https://online.adp.com/signin/v1/?APPID=WFNPortal", browser);
    const doc = dom.window.document;
    // ADP's form fields are web components with the real input inside.
    const shadow = doc.getElementById("login-form_password").attachShadow({ mode: "open" });
    shadow.innerHTML = `<input type="password" autocomplete="current-password">`;
    const button = doc.getElementById("signBtn").attachShadow({ mode: "open" });
    button.innerHTML = `<button>Sign in</button>`;
    dom.window.Element.prototype.getBoundingClientRect = () => ({ width: 120, height: 30, top: 0, left: 0 });
    return dom;
}

test("ADP: the test tab fills the saved password, signs in and reports a verification step", async () => {
    const messages = [];
    const browser = makeBrowser({
        onBackgroundMessage: async (message) => {
            messages.push(message);
            if (message.type === "adp-probe-state") return { active: true };
            if (message.type === "adp-credential") return { value: "s3cret-for-test" };
            return { ok: true };
        }
    });
    const dom = adpPage(browser);
    const doc = dom.window.document;
    const input = doc.getElementById("login-form_password").shadowRoot.querySelector("input");
    let typed = "";
    input.addEventListener("input", () => { typed = input.value; });
    doc.getElementById("signBtn").shadowRoot.querySelector("button").addEventListener("click", () => {
        doc.body.innerHTML = "<p>We sent a code to your phone. Enter the verification code.</p>";
    });
    load(dom, ["content/adp.js"]);
    const result = await waitFor(() => messages.find((m) => m.type === "adp-probe-result"), 6000);
    assert.equal(typed, "s3cret-for-test");
    assert.deepEqual(messages.filter((m) => m.type === "adp-credential").map((m) => m.field), ["password"]);
    assert.equal(result.status, "needs_code");
    assert.ok(!JSON.stringify(result).includes("s3cret"), "the password is never reported");
    dom.window.close();
});

test("ADP: an ordinary ADP tab (not the test tab) does nothing", async () => {
    const messages = [];
    const browser = makeBrowser({
        onBackgroundMessage: async (message) => {
            messages.push(message);
            return message.type === "adp-probe-state" ? { active: false } : { ok: true };
        }
    });
    const dom = adpPage(browser);
    load(dom, ["content/adp.js"]);
    await new Promise((r) => setTimeout(r, 1500));
    assert.deepEqual(messages.map((m) => m.type), ["adp-probe-state"]);
    dom.window.close();
});

function loginPage(browser, query) {
    const html = require("./helpers").read("adp/login.html").replace(/<script[^>]*><\/script>/g, "");
    const dom = makeDom(html, "https://extension.test/adp/login.html" + (query || ""), browser);
    browser.tabs = { removed: [], getCurrent: async () => ({ id: 7 }), remove: async (id) => { browser.tabs.removed.push(id); } };
    return dom;
}

test("ADP: login.html?autostart=1 runs one test, drops the parameter and closes its tab when the result lands", async () => {
    const messages = [];
    const browser = makeBrowser({
        onBackgroundMessage: async (message) => {
            messages.push(message.type);
            return message.type === "adp-status" ? { hasPassword: true, running: false, last: null } : { ok: true };
        }
    });
    const dom = loginPage(browser, "?autostart=1");
    load(dom, ["adp/login.js"]);
    await waitFor(() => messages.includes("adp-probe-start"));
    assert.equal(dom.window.location.search, "", "a reload cannot start it again");
    await browser.storage.local.set({ adp_probe_last: { status: "signed_in", finishedAt: new Date().toISOString() } });
    await waitFor(() => browser.tabs.removed.length);
    assert.deepEqual(browser.tabs.removed, [7]);
    assert.equal(messages.filter((t) => t === "adp-probe-start").length, 1);
    await new Promise((r) => setTimeout(r, 100));
    dom.window.close();
});

test("ADP: autostart is skipped when a test just finished or is running", async () => {
    for (const status of [
        { hasPassword: true, running: false, last: { status: "signed_in", finishedAt: new Date().toISOString() } },
        { hasPassword: true, running: true, last: null }
    ]) {
        const messages = [];
        const browser = makeBrowser({
            onBackgroundMessage: async (message) => { messages.push(message.type); return message.type === "adp-status" ? status : { ok: true }; }
        });
        const dom = loginPage(browser, "?autostart=1");
        load(dom, ["adp/login.js"]);
        await new Promise((r) => setTimeout(r, 200));
        assert.ok(!messages.includes("adp-probe-start"));
        dom.window.close();
    }
});

test("ADP: on a device ADP does not know, both fields share one page; the user ID is filled before the password", async () => {
    const messages = [];
    const browser = makeBrowser({
        onBackgroundMessage: async (message) => {
            messages.push(message);
            if (message.type === "adp-probe-state") return { active: true };
            if (message.type === "adp-credential") return { value: message.field === "username" ? "jdoe-test" : "s3cret-for-test" };
            return { ok: true };
        }
    });
    const dom = makeDom(`<!doctype html><html><body><h1>Welcome to ADP</h1>
        <sdf-input id="login-form_username"></sdf-input><sdf-input id="login-form_password"></sdf-input>
        <sdf-button id="signBtn">Sign in</sdf-button></body></html>`, "https://online.adp.com/signin/v1/?APPID=WFNPortal", browser);
    const doc = dom.window.document;
    doc.getElementById("login-form_username").attachShadow({ mode: "open" }).innerHTML = `<input type="text">`;
    doc.getElementById("login-form_password").attachShadow({ mode: "open" }).innerHTML = `<input type="password">`;
    doc.getElementById("signBtn").attachShadow({ mode: "open" }).innerHTML = `<button>Sign in</button>`;
    dom.window.Element.prototype.getBoundingClientRect = () => ({ width: 120, height: 30, top: 0, left: 0 });
    let submitted = null;
    doc.getElementById("signBtn").shadowRoot.querySelector("button").addEventListener("click", () => {
        submitted = {
            user: doc.getElementById("login-form_username").shadowRoot.querySelector("input").value,
            password: doc.getElementById("login-form_password").shadowRoot.querySelector("input").value
        };
        doc.body.innerHTML = "<p>Enter the verification code we sent you.</p>";
    });
    load(dom, ["content/adp.js"]);
    const result = await waitFor(() => messages.find((m) => m.type === "adp-probe-result"), 8000);
    assert.deepEqual(messages.filter((m) => m.type === "adp-credential").map((m) => m.field), ["username", "password"]);
    assert.deepEqual(submitted, { user: "jdoe-test", password: "s3cret-for-test" });
    assert.equal(result.status, "needs_code");
    dom.window.close();
});

test("ADP: a fill the form did not take is retried, and Sign in is pressed only once ADP enables it", async () => {
    const messages = [];
    const browser = makeBrowser({
        onBackgroundMessage: async (message) => {
            messages.push(message);
            if (message.type === "adp-probe-state") return { active: true };
            if (message.type === "adp-credential") return { value: message.field === "username" ? "jdoe-test" : "s3cret-for-test" };
            return { ok: true };
        }
    });
    const dom = makeDom(`<!doctype html><html><body>
        <sdf-input id="login-form_username" class="is-empty"></sdf-input><sdf-input id="login-form_password" class="is-empty"></sdf-input>
        <sdf-button id="signBtn" class="disabled">Sign in</sdf-button></body></html>`, "https://online.adp.com/signin/v1/", browser);
    const doc = dom.window.document;
    dom.window.Element.prototype.getBoundingClientRect = () => ({ width: 120, height: 30, top: 0, left: 0 });
    const sign = doc.getElementById("signBtn");
    sign.attachShadow({ mode: "open" }).innerHTML = `<button>Sign in</button>`;
    let ignoredPassword = false;
    let clicks = 0;
    ["login-form_username", "login-form_password"].forEach((id) => {
        const host = doc.getElementById(id);
        host.attachShadow({ mode: "open" }).innerHTML = `<input type="${id.endsWith("password") ? "password" : "text"}">`;
        host.addEventListener("input", (e) => {
            // Like ADP once did: the first password value is not taken.
            if (id.endsWith("password") && !ignoredPassword) { ignoredPassword = true; e.composedPath()[0].value = ""; return; }
            host.classList.toggle("is-empty", !e.composedPath()[0].value);
            const ready = ["login-form_username", "login-form_password"].every((h) => !doc.getElementById(h).classList.contains("is-empty"));
            sign.classList.toggle("disabled", !ready);
        });
    });
    sign.shadowRoot.querySelector("button").addEventListener("click", () => {
        clicks += 1;
        if (!sign.classList.contains("disabled")) doc.body.innerHTML = "<p>Enter the verification code we sent you.</p>";
    });
    load(dom, ["content/adp.js"]);
    const result = await waitFor(() => messages.find((m) => m.type === "adp-probe-result"), 10000);
    assert.deepEqual(messages.filter((m) => m.type === "adp-credential").map((m) => m.field), ["username", "password", "password"]);
    assert.equal(clicks, 1, "Sign in pressed once, after it was enabled");
    assert.equal(result.status, "needs_code");
    dom.window.close();
});
