"use strict";

var Core = globalThis.AgentOsFilterCore;
var $ = function (id) { return document.getElementById(id); };
var activeTab = null;
var pageStats = null;

function bridgeView(bridge) {
    if (!bridge.enabled) return { cls: "", label: "Bridge off" };
    if (bridge.state === "ok") return { cls: "ok", label: "Agent OS connected" };
    if (!bridge.paired) return { cls: "warn", label: "Not paired" };
    if (bridge.state === "starting") return { cls: "warn", label: "Connecting…" };
    return { cls: "bad", label: "Bridge " + bridge.state };
}

async function renderStatus() {
    var status = await browser.runtime.sendMessage({ type: "status" });
    $("version").textContent = "v" + status.version;
    var view = bridgeView(status.bridge);
    $("bridge-dot").className = "dot " + view.cls;
    $("bridge-label").textContent = view.label;
    var needsHelp = status.bridge.state !== "ok" && status.bridge.enabled;
    $("bridge-footer").hidden = !needsHelp;
    if (needsHelp) {
        var native = status.bridge.native === "not installed"
            ? "Native helper not installed (run browser/extension/tools/install_native_host.py)."
            : "Native helper: " + status.bridge.native + ".";
        $("bridge-detail").textContent = (status.bridge.error ? status.bridge.error + ". " : "") + native;
    }
}

async function renderPage() {
    var state = await browser.runtime.sendMessage({ type: "filters-get" });
    $("global-enabled").checked = state.enabled;
    $("old-reddit").checked = Boolean(state.redirects.oldReddit);
    try {
        pageStats = await browser.tabs.sendMessage(activeTab.id, { type: "filters-page-stats" });
    } catch (error) {
        pageStats = null;
    }
    if (!pageStats || !pageStats.scopes.length) {
        $("page-summary").textContent = "No filter adapter for this site.";
        $("page-controls").hidden = true;
        return;
    }
    var scope = pageStats.scopes[0];
    var siteName = Core.SCOPES[scope] || scope;
    $("page-summary").textContent = siteName + ": " + pageStats.hidden + " hidden of " + pageStats.items + " items";
    $("page-controls").hidden = false;
    $("site-label").textContent = "Filter " + siteName.replace(/ \(.*\)$/, "");
    $("site-enabled").checked = state.sites[scope] ? state.sites[scope].enabled !== false : true;
    $("reveal").textContent = pageStats.reveal ? "Re-hide" : "Show hidden";
    var list = $("reasons");
    list.textContent = "";
    Object.keys(pageStats.reasons).sort(function (a, b) { return pageStats.reasons[b] - pageStats.reasons[a]; })
        .slice(0, 12).forEach(function (reason) {
            var li = document.createElement("li");
            var name = document.createElement("span");
            name.textContent = reason;
            var count = document.createElement("span");
            count.textContent = pageStats.reasons[reason];
            li.append(name, count);
            list.appendChild(li);
        });
}

async function renderCommands() {
    var box = $("commands");
    var response;
    try {
        response = await browser.tabs.sendMessage(activeTab.id, { type: "gm-menu-list" });
    } catch (error) {
        return;
    }
    if (!response || !response.commands || !response.commands.length) return;
    box.textContent = "";
    response.commands.forEach(function (command) {
        var button = document.createElement("button");
        button.type = "button";
        button.textContent = command.name.replace(/^Agent OS:\s*/, "");
        button.addEventListener("click", function () {
            browser.tabs.sendMessage(activeTab.id, { type: "gm-menu-run", id: command.id });
            window.close();
        });
        box.appendChild(button);
    });
}

async function updateFilters(fn) {
    var state = await browser.runtime.sendMessage({ type: "filters-get" });
    fn(state);
    await browser.runtime.sendMessage({ type: "filters-replace", state: state });
    setTimeout(renderPage, 300);
}

$("save").addEventListener("click", function () {
    browser.tabs.sendMessage(activeTab.id, { type: "gm-menu-run", name: "Agent OS: Save current page" });
    window.close();
});
$("manage").addEventListener("click", function () {
    browser.runtime.openOptionsPage();
    window.close();
});
$("reveal").addEventListener("click", async function () {
    await browser.tabs.sendMessage(activeTab.id, { type: "filters-set-reveal", reveal: !(pageStats && pageStats.reveal) });
    renderPage();
});
$("site-enabled").addEventListener("change", function (event) {
    var scope = pageStats && pageStats.scopes[0];
    if (!scope) return;
    updateFilters(function (state) { state.sites[scope].enabled = event.target.checked; });
});
$("global-enabled").addEventListener("change", function (event) {
    updateFilters(function (state) { state.enabled = event.target.checked; });
});
$("old-reddit").addEventListener("change", function (event) {
    updateFilters(function (state) { state.redirects.oldReddit = event.target.checked; });
});
$("adp-login").addEventListener("click", function () {
    browser.windows.create({ url: browser.runtime.getURL("adp/login.html"), type: "popup", width: 460, height: 560 });
    window.close();
});

$("pair").addEventListener("click", async function () {
    $("pair").disabled = true;
    $("pair").textContent = "Pairing…";
    await browser.runtime.sendMessage({ type: "bridge-pair" });
    $("pair").disabled = false;
    $("pair").textContent = "Pair with Agent OS";
    renderStatus();
});

async function renderRoutines() {
    var box = $("routine-list");
    var res = await browser.runtime.sendMessage({ type: "routines-list" });
    box.textContent = "";
    if (!res || !res.ok) {
        var note = document.createElement("span");
        note.className = "muted small";
        note.textContent = "Needs the Agent OS native helper.";
        box.appendChild(note);
        return;
    }
    if (!res.routines.length) {
        var empty = document.createElement("span");
        empty.className = "muted small";
        empty.textContent = "No routines yet.";
        box.appendChild(empty);
    }
    res.routines.forEach(function (routine) {
        var row = document.createElement("div");
        row.className = "routine-row";
        var name = document.createElement("span");
        name.textContent = routine.name + (routine.last_status ? " · " + routine.last_status.replace(/_/g, " ") : "");
        name.title = routine.start_url;
        var run = document.createElement("button");
        run.type = "button";
        run.textContent = "Run";
        run.addEventListener("click", async function () {
            run.disabled = true;
            var started = await browser.runtime.sendMessage({ type: "routine-run", routine_id: routine.id });
            run.textContent = started && started.ok ? "Started" : "Failed";
        });
        row.append(name, run);
        box.appendChild(row);
    });
}

async function renderTasks() {
    var box = $("task-list");
    var store = await browser.runtime.sendMessage({ type: "tasks-get" });
    box.textContent = "";
    if (!store || !store.tasks.length) {
        var empty = document.createElement("span");
        empty.className = "muted small";
        empty.textContent = "No scheduled tasks yet.";
        box.appendChild(empty);
        return;
    }
    store.tasks.forEach(function (task) {
        var row = document.createElement("div");
        row.className = "routine-row";
        var name = document.createElement("span");
        var status = task.lastRun ? " · " + task.lastRun.status : "";
        name.textContent = task.name + status;
        name.title = AgentOsTaskCore.describeTaskSchedule(task) + (task.lastRun && task.lastRun.error ? " — " + task.lastRun.error : "");
        var run = document.createElement("button");
        run.type = "button";
        run.textContent = "Run";
        run.disabled = !task.steps.length;
        run.addEventListener("click", async function () {
            run.disabled = true;
            var res = await browser.runtime.sendMessage({ type: "task-run", id: task.id });
            run.textContent = res && res.ok ? "Started" : "Failed";
        });
        var edit = document.createElement("button");
        edit.type = "button";
        edit.textContent = "Edit";
        edit.addEventListener("click", function () {
            browser.tabs.create({ url: browser.runtime.getURL("options/options.html#tasks?edit=" + encodeURIComponent(task.id)) });
            window.close();
        });
        row.append(name, run, edit);
        box.appendChild(row);
    });
}

$("new-task").addEventListener("click", function () {
    var url = activeTab && /^https?:/.test(activeTab.url || "") ? activeTab.url : "";
    browser.tabs.create({ url: browser.runtime.getURL("options/options.html#tasks" + (url ? "?url=" + encodeURIComponent(url) : "")) });
    window.close();
});

$("new-routine").addEventListener("click", function () {
    var url = activeTab && /^https?:/.test(activeTab.url || "") ? activeTab.url : "";
    browser.tabs.create({ url: browser.runtime.getURL("options/options.html#routines" + (url ? "?url=" + encodeURIComponent(url) : "")) });
    window.close();
});

browser.tabs.query({ active: true, currentWindow: true }).then(function (tabs) {
    activeTab = tabs[0];
    renderStatus();
    renderPage();
    renderCommands();
    renderRoutines();
    renderTasks();
});
