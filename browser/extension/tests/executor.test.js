"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const plain = (v) => JSON.parse(JSON.stringify(v));
const { makeBrowser, sendToContent, makeDom, load } = require("./helpers");

function setup() {
    const browser = makeBrowser();
    const dom = makeDom(`<main><h1>Shop</h1>
      <form id="f"><label for="pw">Password</label><input id="pw" type="password">
        <input id="card" name="cardnumber" autocomplete="cc-number">
        <input id="q" name="q" placeholder="Search">
        <button id="buy" type="submit">Place order</button></form>
      <button id="more" type="button">Show more</button>
      <div id="out"></div></main>`, "https://shop.example/", browser);
    dom.window.document.getElementById("more").addEventListener("click", () => {
        dom.window.document.getElementById("out").textContent = "expanded";
    });
    let submitted = 0;
    dom.window.document.getElementById("f").addEventListener("submit", (e) => { e.preventDefault(); submitted += 1; });
    load(dom, ["content/executor.js"]);
    const exec = (action, approved) => sendToContent(browser, { type: "aos-exec", action, approved });
    return { dom, exec, submitted: () => submitted };
}

test("refuses to type into password and payment fields even when approved", async () => {
    const { exec, dom } = setup();
    const pw = await exec({ op: "type", selector: "#pw", text: "hunter2" }, true);
    assert.equal(pw.blocked, true);
    assert.equal(dom.window.document.getElementById("pw").value, "");
    const card = await exec({ op: "type", selector: "#card", text: "4111" }, true);
    assert.equal(card.blocked, true);
    const ok = await exec({ op: "type", selector: "#q", text: "skyrim" });
    assert.equal(ok.ok, true);
    assert.equal(dom.window.document.getElementById("q").value, "skyrim");
});

test("consequential clicks need approval; ordinary clicks do not", async () => {
    const { exec, dom, submitted } = setup();
    const paused = await exec({ op: "click", selector: "#buy" });
    assert.equal(paused.approval_required, true);
    assert.match(paused.reason, /form submission/);
    assert.equal(submitted(), 0);
    const approved = await exec({ op: "click", selector: "#buy" }, true);
    assert.equal(approved.ok, true);
    assert.equal(submitted(), 1);
    const plain = await exec({ op: "click", selector: "#more" });
    assert.equal(plain.ok, true);
    assert.equal(dom.window.document.getElementById("out").textContent, "expanded");
});

test("inspect redacts nothing it should not expose and flags sensitive fields", async () => {
    const { exec } = setup();
    const result = await exec({ op: "inspect" });
    assert.equal(result.ok, true);
    assert.equal(result.result.title, "");
    assert.deepEqual(plain(result.result.headings), ["Shop"]);
    const extract = await exec({ op: "extract", selector: "#pw" });
    assert.deepEqual(plain(extract.result), ["[redacted sensitive field]"]);
    const missing = await exec({ op: "click", selector: "#nope" });
    assert.equal(missing.ok, false);
});

test("web components: inspect, click, extract and the safety gate reach inside shadow roots and same-origin iframes", async () => {
    const browser = makeBrowser();
    const dom = makeDom(`<header><x-nav id="nav"></x-nav></header><main><x-panel id="panel"><span>slotted note</span></x-panel>
        <x-input id="login-form_password"></x-input><iframe id="legacy"></iframe></main>`, "https://wfn.example/theme/admin.html", browser);
    const doc = dom.window.document;
    dom.window.Element.prototype.getBoundingClientRect = () => ({ width: 100, height: 20, top: 0, left: 0 });
    const nav = doc.getElementById("nav").attachShadow({ mode: "open" });
    nav.innerHTML = `<a id="reports" role="menuitem" href="#/Reports">Reports</a><x-button id="run" role="button"></x-button>`;
    nav.getElementById("run").attachShadow({ mode: "open" }).innerHTML = `<button>Run report</button>`;
    let opened = "";
    nav.getElementById("reports").addEventListener("click", (e) => { e.preventDefault(); opened = "reports"; });
    doc.getElementById("panel").attachShadow({ mode: "open" }).innerHTML = `<h2>Report center</h2><slot></slot>`;
    doc.getElementById("login-form_password").attachShadow({ mode: "open" }).innerHTML = `<input type="password">`;
    const frameDoc = doc.getElementById("legacy").contentDocument;
    frameDoc.defaultView.Element.prototype.getBoundingClientRect = () => ({ width: 100, height: 20, top: 0, left: 0 });
    frameDoc.body.innerHTML = `<a id="legacy-link" href="#/Legacy">Legacy report</a>`;
    load(dom, ["content/executor.js"]);
    const exec = (action, approved) => sendToContent(browser, { type: "aos-exec", action, approved });

    const page = plain((await exec({ op: "inspect" })).result);
    const byText = Object.fromEntries(page.interactive.map((i) => [i.text, i.selector]));
    assert.equal(byText["Reports"], "#nav >>> #reports");
    assert.equal(byText["Legacy report"], "#legacy >>> #legacy-link");
    assert.equal(page.interactive.filter((i) => i.text === "Run report").length, 1, "a component and its inner button are listed once");
    assert.ok(page.headings.includes("Report center"));
    assert.match(page.text, /Report center/);
    assert.match(page.text, /slotted note/);

    assert.equal((await exec({ op: "click", selector: "#nav >>> #reports" })).ok, true);
    assert.equal(opened, "reports");
    assert.equal((await exec({ op: "click", selector: "#run >>> button" })).approval_required, true, "deep clicks keep the safety gate");
    assert.deepEqual(plain((await exec({ op: "extract", selector: "#legacy-link" })).result), ["Legacy report"]);
    assert.equal((await exec({ op: "wait", selector: "#reports", timeout_ms: 200 })).result.found, true);
    assert.equal((await exec({ op: "type", selector: "#login-form_password >>> input", text: "x" }, true)).blocked, true);
    assert.equal((await exec({ op: "type", selector: "#login-form_password", text: "x" }, true)).blocked, true);

    const tree = plain((await exec({ op: "inspect", outline: true, selector: "#nav" })).result);
    assert.match(tree.lines, /^x-nav#nav$/m);
    assert.match(tree.lines, /^  a#reports\[role=menuitem\] "Reports" -> #\/Reports$/m);
    assert.match(tree.lines, /^    button "Run report"$/m);
    const whole = plain((await exec({ op: "inspect", outline: true })).result);
    assert.match(whole.lines, /span "slotted note"/);
    assert.match(whole.lines, /a#legacy-link "Legacy report" -> #\/Legacy/);
    dom.window.close();
});
