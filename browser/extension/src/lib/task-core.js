/*
 * Agent OS scheduled tasks: model, schedules and step descriptions.
 *
 * A scheduled task is a recorded sequence of clicks and form entries that the
 * extension replays at set times. Shared by the background page, the options
 * page, content scripts and the Node tests; no DOM or WebExtension APIs here.
 */
(function (root, factory) {
    "use strict";
    if (typeof module === "object" && module.exports) {
        module.exports = factory();
    } else {
        root.AgentOsTaskCore = factory();
    }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";

    var STORAGE_KEY = "agent_os_tasks_v1";
    var MAX_RUNS = 100;
    var DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    var STEP_TYPES = ["click", "fill", "select", "check", "key", "wait", "navigate"];
    var VARIANCE_MS = 6 * 60000;

    function clone(value) {
        return JSON.parse(JSON.stringify(value));
    }

    function newId(prefix) {
        return (prefix || "t") + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
    }

    function normalizeSchedule(raw) {
        var s = raw && typeof raw === "object" ? raw : { kind: "manual" };
        var kind = ["manual", "weekly", "once", "interval"].indexOf(s.kind) === -1 ? "manual" : s.kind;
        if (kind === "weekly") {
            var time = /^\d{1,2}:\d{2}$/.test(String(s.time || "")) ? s.time : "08:00";
            var days = (Array.isArray(s.days) ? s.days : [0, 1, 2, 3, 4, 5, 6])
                .map(Number).filter(function (d) { return d >= 0 && d <= 6; });
            days = days.filter(function (d, i) { return days.indexOf(d) === i; }).sort();
            return { kind: kind, time: time, days: days.length ? days : [0, 1, 2, 3, 4, 5, 6] };
        }
        if (kind === "once") return { kind: kind, at: String(s.at || "") };
        if (kind === "interval") return { kind: kind, minutes: Math.max(5, Math.round(Number(s.minutes) || 60)) };
        return { kind: "manual" };
    }

    function nextRun(schedule, afterMs) {
        var s = normalizeSchedule(schedule);
        var after = typeof afterMs === "number" ? afterMs : Date.now();
        if (s.kind === "interval") return after + s.minutes * 60000;
        if (s.kind === "once") {
            var at = new Date(s.at).getTime();
            return isFinite(at) && at > after ? at : null;
        }
        if (s.kind === "weekly") {
            var parts = s.time.split(":").map(Number);
            var base = new Date(after);
            for (var offset = 0; offset < 8; offset += 1) {
                var day = new Date(base.getFullYear(), base.getMonth(), base.getDate() + offset, parts[0], parts[1], 0, 0);
                if (day.getTime() > after && s.days.indexOf(day.getDay()) !== -1) return day.getTime();
            }
        }
        return null;
    }

    // When a task should next run. With randomVariance on, each run lands at a
    // random moment 0-6 minutes after its scheduled time. A weekly/one-off slot
    // from the last 6 minutes is still pending (for example, the task was edited
    // or Firefox restarted inside the window) unless a scheduled run handled it.
    function plannedRun(task, nowMs, random) {
        var now = typeof nowMs === "number" ? nowMs : Date.now();
        var s = normalizeSchedule(task && task.schedule);
        if (!task || !task.randomVariance) return nextRun(s, now);
        var base = null;
        if (s.kind === "weekly" || s.kind === "once") {
            var recent = nextRun(s, now - VARIANCE_MS);
            var last = task.lastRun;
            var handled = last && last.trigger !== "manual" && new Date(last.at).getTime() >= recent;
            if (recent !== null && recent <= now && !handled) base = recent;
        }
        if (base === null) base = nextRun(s, now);
        if (base === null) return null;
        var earliest = Math.max(base, now);
        var roll = (typeof random === "function" ? random : Math.random)();
        return Math.round(earliest + roll * (base + VARIANCE_MS - earliest));
    }

    function describeSchedule(schedule) {
        var s = normalizeSchedule(schedule);
        if (s.kind === "interval") return "Every " + s.minutes + " minutes";
        if (s.kind === "once") return s.at ? "Once on " + s.at.replace("T", " at ") : "Once (no time set)";
        if (s.kind === "weekly") {
            var days = s.days;
            var label;
            if (days.length === 7) label = "Every day";
            else if (days.join() === "1,2,3,4,5") label = "Weekdays";
            else if (days.join() === "0,6") label = "Weekends";
            else label = days.map(function (d) { return DAY_NAMES[d]; }).join(", ");
            return label + " at " + s.time;
        }
        return "Manual only";
    }

    function describeTaskSchedule(task) {
        var text = describeSchedule(task.schedule);
        return task.randomVariance && normalizeSchedule(task.schedule).kind !== "manual" ? text + " (+0–6 min random)" : text;
    }

    function normalizeStep(raw) {
        if (!raw || typeof raw !== "object" || STEP_TYPES.indexOf(raw.type) === -1) return null;
        var step = { type: raw.type };
        if (raw.target && typeof raw.target === "object") step.target = raw.target;
        if (raw.url) step.url = String(raw.url);
        if (raw.type === "fill") {
            if (raw.credential === "username" || raw.credential === "password") step.credential = raw.credential;
            else if (raw.manual) step.manual = true;
            else step.value = String(raw.value == null ? "" : raw.value);
        }
        if (raw.type === "select") {
            step.value = String(raw.value == null ? "" : raw.value);
            if (raw.text) step.text = String(raw.text);
        }
        if (raw.type === "check") step.checked = Boolean(raw.checked);
        if (raw.type === "key") step.key = raw.key === "Tab" ? "Tab" : "Enter";
        if (raw.type === "wait") step.ms = Math.max(250, Math.min(Math.round(Number(raw.ms) || 2000), 120000));
        return step;
    }

    function normalizeTask(raw) {
        var t = raw && typeof raw === "object" ? raw : {};
        var task = {
            id: t.id || newId("task-"),
            name: String(t.name || "").trim(),
            startUrl: String(t.startUrl || "").trim(),
            schedule: normalizeSchedule(t.schedule),
            steps: (Array.isArray(t.steps) ? t.steps : []).map(normalizeStep).filter(Boolean),
            openInWindow: Boolean(t.openInWindow),
            keepOpen: Boolean(t.keepOpen),
            randomVariance: Boolean(t.randomVariance),
            enabled: t.enabled !== false,
            hasCredentials: Boolean(t.hasCredentials),
            usernameHint: String(t.usernameHint || ""),
            createdAt: t.createdAt || new Date().toISOString(),
            updatedAt: t.updatedAt || new Date().toISOString(),
            lastRun: t.lastRun || null,
            nextRunAt: t.nextRunAt || null
        };
        return task;
    }

    function validateTask(task) {
        var errors = [];
        if (!task.name) errors.push("Give the task a name.");
        if (!/^https?:\/\//i.test(task.startUrl)) errors.push("The start URL must begin with http:// or https://.");
        if (task.schedule.kind === "once" && !isFinite(new Date(task.schedule.at).getTime())) errors.push("Pick a date and time.");
        return errors;
    }

    function needsCredentials(task) {
        return task.steps.some(function (s) { return s.type === "fill" && s.credential; });
    }

    function normalizeStore(raw) {
        var s = raw && typeof raw === "object" ? raw : {};
        return {
            version: 1,
            tasks: (Array.isArray(s.tasks) ? s.tasks : []).map(normalizeTask),
            runs: (Array.isArray(s.runs) ? s.runs : []).slice(-MAX_RUNS)
        };
    }

    function targetLabel(target) {
        if (!target) return "element";
        var label = target.text || target.label || target.aria || target.placeholder || target.name || target.id || target.tag || "element";
        label = String(label).replace(/\s+/g, " ").trim();
        return label.length > 50 ? label.slice(0, 47) + "…" : label;
    }

    function describeStep(step) {
        var where = "“" + targetLabel(step.target) + "”";
        switch (step.type) {
        case "click": return "Click " + where;
        case "fill":
            if (step.credential) return "Enter saved " + step.credential + " in " + where;
            if (step.manual) return "Needs manual entry in " + where + " (cannot be automated)";
            return "Type “" + (step.value.length > 40 ? step.value.slice(0, 37) + "…" : step.value) + "” in " + where;
        case "select": return "Choose “" + (step.text || step.value) + "” in " + where;
        case "check": return (step.checked ? "Tick " : "Untick ") + where;
        case "key": return "Press " + step.key + " in " + where;
        case "wait": return "Wait " + (step.ms / 1000) + "s";
        case "navigate": return "Go to " + step.url;
        default: return step.type;
        }
    }

    function addRun(store, run) {
        store.runs.push(run);
        if (store.runs.length > MAX_RUNS) store.runs = store.runs.slice(-MAX_RUNS);
    }

    return {
        STORAGE_KEY: STORAGE_KEY,
        DAY_NAMES: DAY_NAMES,
        newId: newId,
        clone: clone,
        normalizeSchedule: normalizeSchedule,
        VARIANCE_MS: VARIANCE_MS,
        nextRun: nextRun,
        plannedRun: plannedRun,
        describeSchedule: describeSchedule,
        describeTaskSchedule: describeTaskSchedule,
        normalizeStep: normalizeStep,
        normalizeTask: normalizeTask,
        validateTask: validateTask,
        needsCredentials: needsCredentials,
        normalizeStore: normalizeStore,
        describeStep: describeStep,
        targetLabel: targetLabel,
        addRun: addRun
    };
});
