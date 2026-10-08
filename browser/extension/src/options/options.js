"use strict";

var Core = globalThis.AgentOsFilterCore;
var $ = function (id) { return document.getElementById(id); };
var GM_SETTINGS_KEY = "gm:agent_os_capture_settings_v1";
var CAPTURE_DEFAULTS = {
    endpoint: "",
    token: "",
    device: "",
    defaultIntent: "save",
    showFloatingButton: true,
    discordPassiveIndexing: true,
    browserJournalEnabled: true,
    bridgeEnabled: true,
    bridgeEndpoint: "http://127.0.0.1:8766/api/v1/browser/batch",
    bridgeToken: "",
    bridgeSyncSeconds: 30
};

var SITE_UI = {
    reddit: [["enabled", "Filter Reddit"], ["hidePromoted", "Hide promoted posts"], ["hideNsfw", "Hide NSFW posts"]],
    nexus: [["enabled", "Filter Nexus Mods"], ["hideAdult", "Hide adult mods"], ["hideTranslations", "Hide translations"],
        ["lookupTags", "Look up tags, uploader and category through the Nexus API (needed for tag rules)"],
        ["fillFromNextPage", "Refill lists from the next page when items are hidden"]],
    ao3: [["enabled", "Filter AO3"], ["maxFandoms", "Hide works with more than N fandoms (0 = off)", "number"],
        ["minWords", "Hide works under N words (0 = off)", "number"], ["hideWip", "Hide works in progress"]],
    xenforo: [["enabled", "Filter XenForo forums"], ["hidePostsByAuthor", "Collapse posts by hidden authors inside threads"]],
    ffn: [["enabled", "Filter FanFiction.net"], ["minWords", "Hide stories under N words (0 = off)", "number"],
        ["hideWip", "Hide incomplete stories"]],
    youtube: [["enabled", "Filter YouTube"], ["hideShorts", "Hide Shorts"]],
    steam: [["enabled", "Filter Steam Workshop"]],
    search: [["enabled", "Filter Google / DuckDuckGo / Bing results"]],
    amazon: [["enabled", "Filter Amazon search"], ["hideSponsored", "Hide sponsored results"]],
    custom: [["enabled", "Filter custom sites"]]
};

// Fields that make sense per site, first one is the default.
var SCOPE_FIELDS = {
    "*": ["title", "keyword", "author", "tag", "domain"],
    reddit: ["subreddit", "title", "keyword", "author", "domain", "flair"],
    nexus: ["title", "tag", "author", "category", "game", "keyword", "id"],
    ao3: ["tag", "fandom", "author", "title", "keyword", "rating", "language", "id"],
    xenforo: ["author", "title", "keyword", "tag", "prefix", "forum", "id"],
    ffn: ["fandom", "author", "tag", "title", "keyword", "rating", "language", "id"],
    youtube: ["channel", "title", "keyword", "id"],
    steam: ["author", "title", "keyword", "id"],
    search: ["domain", "title", "keyword"],
    amazon: ["title", "keyword", "author", "id"],
    custom: ["title", "keyword", "author", "tag"]
};

var state = Core.normalizeState(null);

function option(value, label) {
    var el = document.createElement("option");
    el.value = value;
    el.textContent = label;
    return el;
}

function fillScopes(select, includeAll) {
    Object.keys(Core.SCOPES).forEach(function (scope) {
        if (scope === "*" && !includeAll) return;
        select.appendChild(option(scope, Core.SCOPES[scope]));
    });
}

function fillFields(select, scope) {
    select.textContent = "";
    (SCOPE_FIELDS[scope] || Object.keys(Core.FIELDS)).forEach(function (field) {
        select.appendChild(option(field, Core.FIELDS[field].label));
    });
}

async function save(next) {
    await browser.runtime.sendMessage({ type: "filters-replace", state: next || state });
}

// -- rules table -------------------------------------------------------------------

function renderRules() {
    var query = $("rule-search").value.trim().toLowerCase();
    var scopeFilter = $("rule-filter-scope").value;
    var rows = $("rule-rows");
    rows.textContent = "";
    var shown = state.rules.filter(function (rule) {
        if (scopeFilter && rule.scope !== scopeFilter) return false;
        if (!query) return true;
        return (rule.value + " " + rule.field + " " + rule.scope + " " + (rule.host || "")).toLowerCase().indexOf(query) !== -1;
    }).slice().reverse();
    shown.forEach(function (rule) {
        var tr = document.createElement("tr");
        if (!rule.enabled) tr.className = "disabled";
        var on = document.createElement("input");
        on.type = "checkbox";
        on.checked = rule.enabled;
        on.addEventListener("change", function () {
            rule.enabled = on.checked;
            save();
        });
        var del = document.createElement("button");
        del.type = "button";
        del.className = "link";
        del.textContent = "Remove";
        del.addEventListener("click", function () {
            state.rules = state.rules.filter(function (r) { return r.id !== rule.id; });
            save();
        });
        [on, Core.SCOPES[rule.scope] || rule.scope, (Core.FIELDS[rule.field] || {}).label || rule.field,
            rule.value, rule.host || "", (rule.createdAt || "").slice(0, 10), del].forEach(function (cell) {
            var td = document.createElement("td");
            if (cell instanceof Node) td.appendChild(cell);
            else td.textContent = cell;
            tr.appendChild(td);
        });
        rows.appendChild(tr);
    });
    $("rule-count").textContent = shown.length + " of " + state.rules.length + " rules";
    $("no-rules").hidden = state.rules.length > 0;
}

$("rule-scope").addEventListener("change", function () { fillFields($("rule-field"), $("rule-scope").value); });
$("rule-search").addEventListener("input", renderRules);
$("rule-filter-scope").addEventListener("change", renderRules);
$("add-rule").addEventListener("submit", async function (event) {
    event.preventDefault();
    var value = $("rule-value").value.trim();
    if (!value) return;
    await browser.runtime.sendMessage({
        type: "filters-add-rule",
        rule: { scope: $("rule-scope").value, field: $("rule-field").value, value: value, host: $("rule-host").value.trim() }
    });
    $("rule-value").value = "";
    $("rule-value").focus();
});

// -- site settings -------------------------------------------------------------------

function renderSites() {
    document.querySelectorAll("[data-global]").forEach(function (input) {
        var key = input.getAttribute("data-global");
        if (input.type === "checkbox") input.checked = Boolean(state[key]);
        else input.value = state[key];
    });
    document.querySelectorAll("[data-redirect]").forEach(function (input) {
        input.checked = Boolean(state.redirects[input.getAttribute("data-redirect")]);
    });
    var box = $("site-settings");
    box.textContent = "";
    Object.keys(SITE_UI).forEach(function (scope) {
        var block = document.createElement("div");
        block.className = "site-block";
        var h = document.createElement("h3");
        h.textContent = Core.SCOPES[scope];
        block.appendChild(h);
        var grid = document.createElement("div");
        grid.className = "grid";
        SITE_UI[scope].forEach(function (spec) {
            var key = spec[0];
            var label = document.createElement("label");
            var input = document.createElement("input");
            if (spec[2] === "number") {
                input.type = "number";
                input.min = "0";
                input.value = Number(state.sites[scope][key] || 0);
                label.append(spec[1], input);
            } else {
                input.type = "checkbox";
                input.checked = state.sites[scope][key] !== false && Boolean(state.sites[scope][key]);
                label.className = "switch";
                label.append(input, " " + spec[1]);
            }
            input.addEventListener("change", function () {
                state.sites[scope][key] = input.type === "checkbox" ? input.checked : Number(input.value || 0);
                save();
            });
            grid.appendChild(label);
        });
        block.appendChild(grid);
        box.appendChild(block);
    });

    var rows = $("custom-rows");
    rows.textContent = "";
    state.customSites.forEach(function (site, index) {
        var tr = document.createElement("tr");
        [site.host, site.itemSelector, site.titleSelector || "", site.authorSelector || "", site.tagSelector || ""].forEach(function (value) {
            var td = document.createElement("td");
            td.textContent = value;
            tr.appendChild(td);
        });
        var td = document.createElement("td");
        var del = document.createElement("button");
        del.type = "button";
        del.className = "link";
        del.textContent = "Remove";
        del.addEventListener("click", function () {
            state.customSites.splice(index, 1);
            save();
        });
        td.appendChild(del);
        tr.appendChild(td);
        rows.appendChild(tr);
    });
}

document.querySelectorAll("[data-global]").forEach(function (input) {
    input.addEventListener("change", function () {
        var key = input.getAttribute("data-global");
        state[key] = input.type === "checkbox" ? input.checked : input.value;
        save();
    });
});

document.querySelectorAll("[data-redirect]").forEach(function (input) {
    input.addEventListener("change", function () {
        state.redirects[input.getAttribute("data-redirect")] = input.checked;
        save();
    });
});

$("add-custom").addEventListener("submit", function (event) {
    event.preventDefault();
    var selector = $("custom-item").value.trim();
    try {
        document.createDocumentFragment().querySelector(selector);
    } catch (error) {
        alert("That item selector is not valid CSS.");
        return;
    }
    state.customSites.push({
        host: $("custom-host").value.trim().toLowerCase().replace(/^https?:\/\//, "").replace(/\/.*$/, ""),
        itemSelector: selector,
        titleSelector: $("custom-title").value.trim(),
        authorSelector: $("custom-author").value.trim(),
        tagSelector: $("custom-tags").value.trim(),
        enabled: true
    });
    save();
    $("add-custom").reset();
});

// -- import / export ------------------------------------------------------------------

$("import-scope").addEventListener("change", function () { fillFields($("import-field"), $("import-scope").value); });
$("import-btn").addEventListener("click", async function () {
    var result = await browser.runtime.sendMessage({
        type: "filters-import",
        input: $("import-text").value,
        defaults: { scope: $("import-scope").value, field: $("import-field").value }
    });
    $("import-result").textContent = "Added " + (result && result.added || 0) + " rules.";
});

function exportJson() {
    return JSON.stringify({
        schema: "agent-os/content-filters/v1",
        exported_at: new Date().toISOString(),
        enabled: state.enabled,
        hiddenStyle: state.hiddenStyle,
        sites: state.sites,
        customSites: state.customSites,
        rules: state.rules
    }, null, 2);
}

$("export-btn").addEventListener("click", function () {
    $("import-text").value = exportJson();
    $("import-result").textContent = "Exported " + state.rules.length + " rules.";
});
$("download-btn").addEventListener("click", function () {
    var blob = new Blob([exportJson()], { type: "application/json" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "agent-os-filters-" + new Date().toISOString().slice(0, 10) + ".json";
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 5000);
});

// -- Agent OS / capture settings ---------------------------------------------------------

async function captureSettings() {
    var res = await browser.storage.local.get(GM_SETTINGS_KEY);
    return Object.assign({}, CAPTURE_DEFAULTS, res[GM_SETTINGS_KEY] || {});
}

async function renderCapture() {
    var settings = await captureSettings();
    document.querySelectorAll("[data-capture]").forEach(function (input) {
        var key = input.getAttribute("data-capture");
        if (document.activeElement === input) return;
        if (input.type === "checkbox") input.checked = settings[key] !== false;
        else input.value = settings[key] == null ? "" : settings[key];
    });
}

document.querySelectorAll("[data-capture]").forEach(function (input) {
    input.addEventListener("change", async function () {
        var res = await browser.storage.local.get(GM_SETTINGS_KEY);
        var saved = Object.assign({}, res[GM_SETTINGS_KEY] || {});
        var key = input.getAttribute("data-capture");
        saved[key] = input.type === "checkbox" ? input.checked : input.type === "number" ? Number(input.value || 0) : input.value.trim();
        if (key === "bridgeEndpoint") saved.bridgeCaptureEndpoint = saved.bridgeEndpoint.replace(/\/batch(?:\?.*)?$/, "/capture");
        var update = {};
        update[GM_SETTINGS_KEY] = saved;
        await browser.storage.local.set(update);
    });
});

async function renderStatus() {
    var status = await browser.runtime.sendMessage({ type: "status" });
    $("version").textContent = "v" + status.version;
    var b = status.bridge;
    var el = $("bridge-status");
    var cls = b.state === "ok" ? "ok" : (b.paired ? "bad" : "warn");
    el.className = "status " + cls;
    el.textContent = b.state === "ok"
        ? "Connected to Agent OS at " + b.endpoint + " · " + status.sessions + " tab sessions registered."
        : "Bridge: " + b.state + (b.error ? " (" + b.error + ")" : "") + " · native helper: " + b.native + ".";

    var checks = [
        { ok: b.native === "ok", text: b.native === "ok" ? "Native helper installed" : "Native helper: " + b.native + " (run python browser/extension/tools/install_native_host.py)" },
        { ok: b.paired, text: b.paired ? "Paired with the Agent OS bridge" : "Not paired with the Agent OS bridge yet" },
        { ok: b.state === "ok", text: b.state === "ok" ? "Bridge reachable; captures and journal sync durably" : "Bridge not reachable right now (" + b.state + ")" },
        { ok: state.rules.length > 0, text: state.rules.length + " hide rules" }
    ];
    var list = $("checklist");
    list.textContent = "";
    checks.forEach(function (check) {
        var li = document.createElement("li");
        li.className = check.ok ? "ok" : "bad";
        li.textContent = check.text;
        list.appendChild(li);
    });
}

$("pair-btn").addEventListener("click", async function () {
    $("pair-result").textContent = "Pairing…";
    var result = await browser.runtime.sendMessage({ type: "bridge-pair" });
    $("pair-result").textContent = result && result.ok ? "Paired." : "Could not pair: " + (result && result.bridge && result.bridge.native || "unknown");
    renderCapture();
    renderStatus();
});

// -- AI routines ----------------------------------------------------------------------------

function when(iso) {
    if (!iso) return "—";
    var d = new Date(iso);
    return isNaN(d) ? iso : d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

function badge(status) {
    var span = document.createElement("span");
    span.className = "badge " + (status || "");
    span.textContent = (status || "never run").replace(/_/g, " ");
    return span;
}

function routineStatus(text, cls) {
    var el = $("routine-status");
    el.hidden = !text;
    el.className = "status " + (cls || "");
    el.textContent = text || "";
}

var routineCache = [];

async function renderRoutines() {
    var res = await browser.runtime.sendMessage({ type: "routines-list" });
    if (!res || !res.ok) {
        routineStatus("Routines need the Agent OS native helper: " + (res && res.error || "not available") +
            ". Run python browser/extension/tools/install_native_host.py once.", "bad");
        return;
    }
    routineStatus("");
    routineCache = res.routines || [];
    var rows = $("routine-rows");
    rows.textContent = "";
    routineCache.forEach(function (routine) {
        var tr = document.createElement("tr");
        var name = document.createElement("td");
        var strong = document.createElement("strong");
        strong.textContent = routine.name;
        var url = document.createElement("div");
        url.className = "muted small";
        url.textContent = routine.start_url + (routine.enabled ? "" : " · disabled");
        name.append(strong, url);
        var schedule = document.createElement("td");
        schedule.textContent = routine.schedule || "manual";
        var last = document.createElement("td");
        last.append(badge(routine.last_status), document.createTextNode(" " + (routine.last_run_at ? when(routine.last_run_at) : "")));
        var next = document.createElement("td");
        next.textContent = when(routine.next_run_at);
        var actions = document.createElement("td");
        var box = document.createElement("div");
        box.className = "actions";
        [["Run now", function () { runRoutine(routine); }], ["Edit", function () { editRoutine(routine); }],
            ["Delete", function () { deleteRoutine(routine); }]].forEach(function (spec) {
            var b = document.createElement("button");
            b.type = "button";
            b.textContent = spec[0];
            if (spec[0] === "Delete") b.className = "link";
            b.addEventListener("click", spec[1]);
            box.appendChild(b);
        });
        actions.appendChild(box);
        [name, schedule, last, next, actions].forEach(function (td) { tr.appendChild(td); });
        rows.appendChild(tr);
    });
    $("no-routines").hidden = routineCache.length > 0;
    renderRuns();
}

async function renderRuns() {
    var res = await browser.runtime.sendMessage({ type: "routine-runs", limit: 15 });
    var rows = $("run-rows");
    rows.textContent = "";
    ((res && res.runs) || []).forEach(function (run) {
        var tr = document.createElement("tr");
        var summary = run.summary || run.error || "";
        if (run.findings && run.findings.length) summary += " — " + run.findings.slice(0, 3).join("; ");
        [when(run.started_at), run.routine_name || run.routine_id, badge(run.status), summary].forEach(function (cell) {
            var td = document.createElement("td");
            if (cell instanceof Node) td.appendChild(cell); else td.textContent = cell;
            tr.appendChild(td);
        });
        rows.appendChild(tr);
    });
}

async function runRoutine(routine) {
    var res = await browser.runtime.sendMessage({ type: "routine-run", routine_id: routine.id });
    routineStatus(res && res.ok
        ? "Started “" + routine.name + "” in a background tab. Results appear below and in the Executive window."
        : "Could not start: " + (res && res.error), res && res.ok ? "ok" : "bad");
    setTimeout(renderRoutines, 4000);
}

function editRoutine(routine) {
    $("routine-form-title").textContent = "Edit routine";
    $("routine-id").value = routine.id;
    $("routine-name").value = routine.name;
    $("routine-url").value = routine.start_url;
    $("routine-instructions").value = routine.instructions || "";
    $("routine-schedule").value = routine.schedule || "";
    var start = "";
    try { start = new URL(routine.start_url).hostname.replace(/^www\./, ""); } catch (error) { start = ""; }
    $("routine-domains").value = (routine.allowed_domains || []).filter(function (d) { return d !== start; }).join(", ");
    $("routine-model").value = routine.model || "sonnet";
    $("routine-notify").value = routine.notify || "auto";
    $("routine-tab").value = routine.tab || "personal";
    $("routine-enabled").checked = routine.enabled !== false;
    $("routine-name").focus();
}

function clearRoutineForm(prefillUrl) {
    $("routine-form").reset();
    $("routine-id").value = "";
    $("routine-form-title").textContent = "New routine";
    if (prefillUrl) $("routine-url").value = prefillUrl;
}

async function deleteRoutine(routine) {
    if (!confirm("Delete the routine “" + routine.name + "”?")) return;
    await browser.runtime.sendMessage({ type: "routine-delete", routine_id: routine.id });
    renderRoutines();
}

$("routine-form").addEventListener("submit", async function (event) {
    event.preventDefault();
    var routine = {
        name: $("routine-name").value.trim(),
        start_url: $("routine-url").value.trim(),
        instructions: $("routine-instructions").value.trim(),
        schedule: $("routine-schedule").value.trim().replace(/^manual$/i, ""),
        allowed_domains: $("routine-domains").value.split(/[\s,]+/).filter(Boolean),
        model: $("routine-model").value,
        notify: $("routine-notify").value,
        tab: $("routine-tab").value,
        enabled: $("routine-enabled").checked
    };
    if ($("routine-id").value) routine.id = $("routine-id").value;
    var res = await browser.runtime.sendMessage({ type: "routine-save", routine: routine });
    $("routine-result").textContent = res && res.ok ? "Saved." : "Not saved: " + (res && res.error);
    if (res && res.ok) {
        clearRoutineForm();
        renderRoutines();
    }
});
$("routine-cancel").addEventListener("click", function () { clearRoutineForm(); });

// The popup's "New routine from this page" opens #routines?url=...
(function prefillFromHash() {
    var match = location.hash.match(/^#routines\?url=(.+)$/);
    if (match) clearRoutineForm(decodeURIComponent(match[1]));
})();

// -- Scheduled tasks ----------------------------------------------------------------------------

var TaskCore = globalThis.AgentOsTaskCore;
var taskStore = { tasks: [], runs: [] };
var editingSteps = null;

function taskStatus(text, cls) {
    var el = $("task-status");
    el.hidden = !text;
    el.className = "status " + (cls || "");
    el.textContent = text || "";
}

function buildDayPicker() {
    var box = $("task-days");
    [1, 2, 3, 4, 5, 6, 0].forEach(function (day) {
        var label = document.createElement("label");
        label.className = "day";
        var input = document.createElement("input");
        input.type = "checkbox";
        input.value = String(day);
        input.checked = day >= 1 && day <= 5;
        label.append(input, " " + TaskCore.DAY_NAMES[day]);
        box.appendChild(label);
    });
}

function scheduleFromForm() {
    var kind = (document.querySelector("input[name='task-kind']:checked") || {}).value || "manual";
    if (kind === "weekly") {
        return {
            kind: kind,
            time: $("task-time").value || "08:00",
            days: Array.from($("task-days").querySelectorAll("input:checked")).map(function (i) { return Number(i.value); })
        };
    }
    if (kind === "once") return { kind: kind, at: $("task-at").value };
    if (kind === "interval") return { kind: kind, minutes: Number($("task-minutes").value || 60) };
    return { kind: "manual" };
}

function scheduleToForm(schedule) {
    var s = TaskCore.normalizeSchedule(schedule);
    document.querySelector("input[name='task-kind'][value='" + s.kind + "']").checked = true;
    if (s.kind === "weekly") {
        $("task-time").value = s.time;
        $("task-days").querySelectorAll("input").forEach(function (i) { i.checked = s.days.indexOf(Number(i.value)) !== -1; });
    }
    if (s.kind === "once") $("task-at").value = s.at;
    if (s.kind === "interval") $("task-minutes").value = s.minutes;
}

async function renderTasks() {
    taskStore = await browser.runtime.sendMessage({ type: "tasks-get" });
    var rows = $("task-rows");
    rows.textContent = "";
    taskStore.tasks.forEach(function (task) {
        var tr = document.createElement("tr");
        if (task.id === $("task-id").value) tr.className = "editing";
        var name = document.createElement("td");
        var strong = document.createElement("strong");
        strong.textContent = task.name;
        var sub = document.createElement("div");
        sub.className = "muted small";
        sub.textContent = task.startUrl + (task.hasCredentials ? " · saved login" : "") + (task.enabled ? "" : " · disabled");
        name.append(strong, sub);
        var when = document.createElement("td");
        when.textContent = TaskCore.describeTaskSchedule(task);
        var steps = document.createElement("td");
        steps.textContent = task.steps.length ? String(task.steps.length) : "not recorded";
        var last = document.createElement("td");
        last.append(badge(task.lastRun ? task.lastRun.status : ""), document.createTextNode(task.lastRun ? " " + when_(task.lastRun.at) : ""));
        if (task.lastRun && task.lastRun.error) last.title = task.lastRun.error;
        var next = document.createElement("td");
        next.textContent = task.enabled && task.steps.length ? when_(task.nextRunAt) : "—";
        var actions = document.createElement("td");
        var box = document.createElement("div");
        box.className = "actions";
        [["Run now", function () { runTaskNow(task); }], ["Record steps", function () { recordTask(task.id); }],
            ["Edit", function () { editTask(task); }], ["Delete", function () { deleteTask(task); }]].forEach(function (spec) {
            var b = document.createElement("button");
            b.type = "button";
            b.textContent = spec[0];
            if (spec[0] === "Delete") b.className = "link";
            b.addEventListener("click", spec[1]);
            box.appendChild(b);
        });
        actions.appendChild(box);
        [name, when, steps, last, next, actions].forEach(function (td) { tr.appendChild(td); });
        rows.appendChild(tr);
    });
    $("no-tasks").hidden = taskStore.tasks.length > 0;

    var runRows = $("task-run-rows");
    runRows.textContent = "";
    taskStore.runs.slice().reverse().slice(0, 20).forEach(function (run) {
        var tr = document.createElement("tr");
        var detail = run.status === "success" ? "Completed (" + run.trigger + ")" :
            (run.error || "") + (run.stepLabel ? " — at step " + (Number(run.stepIndex) + 1) + ": " + run.stepLabel : "");
        [when_(run.finishedAt), run.taskName, badge(run.status), detail].forEach(function (cell) {
            var td = document.createElement("td");
            if (cell instanceof Node) td.appendChild(cell); else td.textContent = cell;
            tr.appendChild(td);
        });
        runRows.appendChild(tr);
    });
    if (editingSteps && $("task-id").value) {
        var current = taskStore.tasks.find(function (t) { return t.id === $("task-id").value; });
        if (current && !editingSteps.dirty) { editingSteps = { steps: TaskCore.clone(current.steps), dirty: false }; renderSteps(); }
    }
}

function when_(iso) {
    return typeof when === "function" ? when(iso) : (iso || "—");
}

function editTask(task) {
    $("task-form-title").textContent = "Edit “" + task.name + "”";
    $("task-submit").textContent = "Save changes";
    $("task-cancel").textContent = "Stop editing";
    $("task-id").value = task.id;
    $("task-name").value = task.name;
    $("task-url").value = task.startUrl;
    scheduleToForm(task.schedule);
    $("task-username").value = task.usernameHint || "";
    $("task-password").value = "";
    $("task-password").placeholder = task.hasCredentials ? "saved (leave blank to keep)" : "";
    $("task-login-state").textContent = task.hasCredentials ? "A login is saved in Windows Credential Manager." :
        (TaskCore.needsCredentials(task) ? "The recorded steps need a saved login." : "");
    $("task-clear-login").hidden = !task.hasCredentials;
    $("task-window").checked = task.openInWindow;
    $("task-keep").checked = task.keepOpen;
    $("task-variance").checked = task.randomVariance;
    $("task-enabled").checked = task.enabled;
    editingSteps = { steps: TaskCore.clone(task.steps), dirty: false };
    renderSteps();
    $("task-rows").querySelectorAll("tr").forEach(function (tr, i) {
        tr.classList.toggle("editing", taskStore.tasks[i] && taskStore.tasks[i].id === task.id);
    });
    if ($("task-form-title").scrollIntoView) $("task-form-title").scrollIntoView({ block: "start" });
    $("task-name").focus({ preventScroll: true });
}

function clearTaskForm() {
    $("task-form").reset();
    $("task-id").value = "";
    $("task-password").placeholder = "";
    $("task-login-state").textContent = "";
    $("task-clear-login").hidden = true;
    $("task-form-title").textContent = "New scheduled task";
    $("task-submit").textContent = "Save task";
    $("task-cancel").textContent = "Clear";
    $("task-rows").querySelectorAll("tr.editing").forEach(function (tr) { tr.classList.remove("editing"); });
    editingSteps = null;
    $("task-steps-box").hidden = true;
}

async function saveTaskForm(extra) {
    var id = $("task-id").value;
    var existing = taskStore.tasks.find(function (t) { return t.id === id; });
    var task = {
        id: id || undefined,
        name: $("task-name").value.trim(),
        startUrl: $("task-url").value.trim(),
        schedule: scheduleFromForm(),
        openInWindow: $("task-window").checked,
        keepOpen: $("task-keep").checked,
        randomVariance: $("task-variance").checked,
        enabled: $("task-enabled").checked
    };
    if (existing) task.steps = existing.steps;
    var credentials = {};
    var username = $("task-username").value.trim();
    var password = $("task-password").value;
    if (extra && extra.clearLogin) credentials.clear = true;
    else if (password || (username && username !== (existing && existing.usernameHint))) {
        credentials = { username: username, password: password };
    }
    var res = await browser.runtime.sendMessage({ type: "task-save", task: task, credentials: credentials });
    $("task-password").value = "";
    $("task-result").textContent = res && res.ok ? "Saved." : "Not saved: " + (res && res.error);
    if (res && res.ok) {
        await renderTasks();
        editTask(res.task);
    }
    return res;
}

async function recordTask(id) {
    var res = await browser.runtime.sendMessage({ type: "task-record-start", id: id });
    taskStatus(res && res.ok
        ? "A recording window is open. Do the steps there, then click Finish & save on the red toolbar."
        : "Could not start recording: " + (res && res.error), res && res.ok ? "warn" : "bad");
}

async function runTaskNow(task) {
    var res = await browser.runtime.sendMessage({ type: "task-run", id: task.id });
    taskStatus(res && res.ok ? "Running “" + task.name + "” in a background tab…" : "Could not run: " + (res && res.error),
        res && res.ok ? "ok" : "bad");
    setTimeout(renderTasks, 5000);
}

async function deleteTask(task) {
    if (!confirm("Delete the scheduled task “" + task.name + "” and its saved login?")) return;
    await browser.runtime.sendMessage({ type: "task-delete", id: task.id });
    if ($("task-id").value === task.id) clearTaskForm();
    renderTasks();
}

function renderSteps() {
    var box = $("task-steps-box");
    var list = $("task-steps");
    list.textContent = "";
    if (!editingSteps) { box.hidden = true; return; }
    box.hidden = false;
    if (!editingSteps.steps.length) {
        var li = document.createElement("li");
        li.className = "muted";
        li.textContent = "Nothing recorded yet. Click Save & record steps.";
        list.appendChild(li);
    }
    editingSteps.steps.forEach(function (step, index) {
        var li = document.createElement("li");
        var text = document.createElement("span");
        text.textContent = TaskCore.describeStep(step);
        li.appendChild(text);
        if (step.type === "fill" && !step.manual) {
            var mode = document.createElement("select");
            [["value", "typed text"], ["username", "saved username"], ["password", "saved password"]].forEach(function (o) {
                var opt = document.createElement("option");
                opt.value = o[0];
                opt.textContent = o[1];
                mode.appendChild(opt);
            });
            mode.value = step.credential || "value";
            mode.addEventListener("change", function () {
                if (mode.value === "value") { delete step.credential; step.value = step.value || ""; }
                else { step.credential = mode.value; delete step.value; }
                editingSteps.dirty = true;
                renderSteps();
            });
            li.appendChild(mode);
            if (!step.credential) {
                var input = document.createElement("input");
                input.value = step.value || "";
                input.addEventListener("input", function () { step.value = input.value; editingSteps.dirty = true; });
                li.appendChild(input);
            }
        }
        if (step.type === "wait") {
            var secs = document.createElement("input");
            secs.type = "number";
            secs.min = "1";
            secs.className = "narrow";
            secs.value = String(step.ms / 1000);
            secs.addEventListener("input", function () { step.ms = Math.max(250, Number(secs.value || 1) * 1000); editingSteps.dirty = true; });
            li.appendChild(secs);
        }
        [["↑", -1], ["↓", 1], ["✕", 0]].forEach(function (spec) {
            var b = document.createElement("button");
            b.type = "button";
            b.className = "link";
            b.textContent = spec[0];
            b.addEventListener("click", function () {
                var steps = editingSteps.steps;
                if (spec[1] === 0) steps.splice(index, 1);
                else {
                    var j = index + spec[1];
                    if (j < 0 || j >= steps.length) return;
                    var tmp = steps[index]; steps[index] = steps[j]; steps[j] = tmp;
                }
                editingSteps.dirty = true;
                renderSteps();
            });
            li.appendChild(b);
        });
        list.appendChild(li);
    });
}

$("task-add-wait").addEventListener("click", function () {
    if (!editingSteps) return;
    editingSteps.steps.push({ type: "wait", ms: 2000 });
    editingSteps.dirty = true;
    renderSteps();
});

$("task-save-steps").addEventListener("click", async function () {
    var task = taskStore.tasks.find(function (t) { return t.id === $("task-id").value; });
    if (!task || !editingSteps) return;
    var updated = Object.assign({}, task, { steps: editingSteps.steps });
    var res = await browser.runtime.sendMessage({ type: "task-save", task: updated, credentials: {} });
    $("task-steps-result").textContent = res && res.ok ? "Steps saved." : "Not saved: " + (res && res.error);
    if (res && res.ok) { editingSteps.dirty = false; renderTasks(); }
});

$("task-form").addEventListener("submit", function (event) {
    event.preventDefault();
    saveTaskForm();
});
$("task-record").addEventListener("click", async function () {
    if (!$("task-form").reportValidity()) return;
    var res = await saveTaskForm();
    if (res && res.ok) recordTask(res.task.id);
});
$("task-cancel").addEventListener("click", clearTaskForm);
$("task-clear-login").addEventListener("click", function () { saveTaskForm({ clearLogin: true }); });

browser.storage.onChanged.addListener(function (changes, area) {
    if (area === "local" && changes[TaskCore.STORAGE_KEY]) renderTasks();
});

// #tasks?url=<page> starts a new task there; #tasks?edit=<id> (popup → Edit) opens that task.
function openTaskFromHash() {
    var match = location.hash.match(/^#tasks\?(url|edit)=(.+)$/);
    if (!match) return;
    var value = decodeURIComponent(match[2]);
    if (match[1] === "url") { clearTaskForm(); $("task-url").value = value; return; }
    var task = taskStore.tasks.find(function (t) { return t.id === value; });
    if (task) editTask(task);
}

buildDayPicker();
renderTasks().then(openTaskFromHash);
window.addEventListener("hashchange", openTaskFromHash);
browser.runtime.sendMessage({ type: "task-clear-badge" });

// -- boot --------------------------------------------------------------------------------

async function load() {
    state = await browser.runtime.sendMessage({ type: "filters-get" });
    renderRules();
    renderSites();
}

browser.storage.onChanged.addListener(function (changes, area) {
    if (area !== "local") return;
    if (changes[Core.STORAGE_KEY]) {
        state = Core.normalizeState(changes[Core.STORAGE_KEY].newValue);
        renderRules();
        renderSites();
    }
    if (changes[GM_SETTINGS_KEY]) renderCapture();
});

function markNav() {
    var hash = (location.hash || "#welcome").replace(/\?.*$/, "");
    document.querySelectorAll("nav a").forEach(function (a) { a.classList.toggle("active", a.getAttribute("href") === hash); });
}

window.addEventListener("hashchange", markNav);

fillScopes($("rule-scope"), true);
fillScopes($("rule-filter-scope"), true);
$("rule-filter-scope").querySelector("option[value='*']").textContent = "Rules for all sites";
fillScopes($("import-scope"), true);
$("rule-scope").value = "reddit";
$("import-scope").value = "reddit";
fillFields($("rule-field"), "reddit");
fillFields($("import-field"), "reddit");
markNav();
load().then(renderStatus);
renderRoutines();
setInterval(function () { if ((location.hash || "").indexOf("#routines") === 0) renderRoutines(); }, 15000);
renderCapture();
setInterval(renderStatus, 5000);
