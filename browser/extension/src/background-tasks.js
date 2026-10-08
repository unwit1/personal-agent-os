/*
 * Scheduled tasks: background side.
 *
 * Owns task storage, recording sessions (a dedicated window the operator
 * drives while content/tasks.js records), replays (a tab content/tasks.js
 * drives), schedules (browser.alarms) and the run log. Logins live in the
 * Windows Credential Manager through the native helper; a saved password is
 * released only to the tab that is replaying that task, at the step that
 * needs it. Runs are reported to Agent OS without any secrets.
 *
 * Loaded after background.js and shares its globals (getLocal, setLocal,
 * nativeRequest, bridgeFetch, captureSettings, installId, VERSION).
 */
"use strict";

var TaskCore = globalThis.AgentOsTaskCore;
var TASK_ALARM_PREFIX = "aos-task:";
var REPLAY_STALL_MS = 90000;
var CATCH_UP_MS = 6 * 3600 * 1000;
var recordings = new Map();   // tabId -> { taskId, windowId, steps }
var replays = new Map();      // tabId -> { taskId, runId, steps, index, startedAt, lastProgress, trigger, windowId }
var taskWrite = Promise.resolve();

async function loadTaskStore() {
    return TaskCore.normalizeStore(await getLocal(TaskCore.STORAGE_KEY, null));
}

function mutateTasks(fn) {
    taskWrite = taskWrite.then(async function () {
        var store = await loadTaskStore();
        var result = await fn(store);
        await setLocal(TaskCore.STORAGE_KEY, store);
        return result;
    });
    return taskWrite;
}

function findTask(store, id) {
    var task = store.tasks.find(function (t) { return t.id === id; });
    if (!task) throw new Error("unknown task");
    return task;
}

// -- schedules --------------------------------------------------------------------------

async function scheduleTask(task) {
    await browser.alarms.clear(TASK_ALARM_PREFIX + task.id);
    var next = task.enabled ? TaskCore.plannedRun(task, Date.now()) : null;
    if (next && task.steps.length) browser.alarms.create(TASK_ALARM_PREFIX + task.id, { when: next });
    return next ? new Date(next).toISOString() : null;
}

async function scheduleAllTasks(catchUp) {
    var missed = [];
    await mutateTasks(async function (store) {
        for (var i = 0; i < store.tasks.length; i += 1) {
            var task = store.tasks[i];
            var due = task.nextRunAt ? new Date(task.nextRunAt).getTime() : null;
            if (catchUp && task.enabled && task.steps.length && due && due <= Date.now() && Date.now() - due < CATCH_UP_MS) {
                missed.push(task.id);
            }
            task.nextRunAt = await scheduleTask(task);
        }
    });
    // Firefox was closed at the scheduled time: run once now, one after another.
    for (var j = 0; j < missed.length; j += 1) {
        await runTask(missed[j], "catch-up");
        await waitForReplayToEnd(missed[j]);
    }
}

browser.alarms.onAlarm.addListener(function (alarm) {
    if (alarm.name.indexOf(TASK_ALARM_PREFIX) !== 0) return;
    runTask(alarm.name.slice(TASK_ALARM_PREFIX.length), "schedule");
});

// -- credentials (Windows Credential Manager via the native helper) --------------------------

async function saveCredentials(taskId, username, password) {
    var res = await nativeRequest({ cmd: "credential_set", task_id: taskId, username: username, password: password });
    if (!res || !res.ok) throw new Error("could not save the login: " + (res && res.error || "native helper " + bridgeStatus.native));
    return res;
}

// -- recording --------------------------------------------------------------------------------

async function startRecording(taskId) {
    var store = await loadTaskStore();
    var task = findTask(store, taskId);
    var win = await browser.windows.create({ url: task.startUrl, focused: true, width: 1200, height: 900 });
    var tab = win.tabs[0];
    recordings.set(tab.id, { taskId: task.id, windowId: win.id, steps: [] });
    return { ok: true, windowId: win.id };
}

async function finishRecording(tabId, save) {
    var rec = recordings.get(tabId);
    if (!rec) return { ok: false };
    recordings.delete(tabId);
    if (save) {
        await mutateTasks(async function (store) {
            var task = findTask(store, rec.taskId);
            task.steps = rec.steps.map(TaskCore.normalizeStep).filter(Boolean);
            task.updatedAt = new Date().toISOString();
            task.nextRunAt = await scheduleTask(task);
        });
    }
    browser.windows.remove(rec.windowId).catch(function () {});
    browser.runtime.openOptionsPage();
    return { ok: true, saved: save, count: rec.steps.length };
}

// -- replay -------------------------------------------------------------------------------------

function replayFor(taskId) {
    var found = null;
    replays.forEach(function (entry, tabId) { if (entry.taskId === taskId) found = { tabId: tabId, entry: entry }; });
    return found;
}

function waitForReplayToEnd(taskId) {
    return new Promise(function (resolve) {
        var started = Date.now();
        (function check() {
            if (!replayFor(taskId) || Date.now() - started > 10 * 60000) resolve();
            else setTimeout(check, 1000);
        })();
    });
}

async function runTask(taskId, trigger) {
    var store = await loadTaskStore();
    var task;
    try { task = findTask(store, taskId); } catch (error) { return { ok: false, error: "unknown task" }; }
    if (replayFor(taskId)) return { ok: false, error: "this task is already running" };
    var runId = TaskCore.newId("run-");
    if (!task.steps.length) {
        await logRun(task, { runId: runId, trigger: trigger, status: "failed", error: "No recorded steps yet. Click Record steps first.", startedAt: new Date().toISOString() });
        return { ok: false, error: "no recorded steps" };
    }
    var tab;
    var windowId = null;
    if (task.openInWindow) {
        var win = await browser.windows.create({ url: task.startUrl, focused: false });
        tab = win.tabs[0];
        windowId = win.id;
    } else {
        tab = await browser.tabs.create({ url: task.startUrl, active: false });
    }
    replays.set(tab.id, {
        taskId: task.id, runId: runId, steps: task.steps, index: 0, trigger: trigger,
        startedAt: new Date().toISOString(), lastProgress: Date.now(), windowId: windowId
    });
    return { ok: true, runId: runId, tabId: tab.id };
}

async function finishReplay(tabId, status, detail) {
    var entry = replays.get(tabId);
    if (!entry) return;
    replays.delete(tabId);
    var store = await loadTaskStore();
    var task;
    try { task = findTask(store, entry.taskId); } catch (error) { return; }
    var step = entry.steps[detail && typeof detail.index === "number" ? detail.index : entry.index];
    await logRun(task, {
        runId: entry.runId,
        trigger: entry.trigger,
        status: status,
        startedAt: entry.startedAt,
        stepIndex: detail && typeof detail.index === "number" ? detail.index : entry.index,
        stepLabel: step ? TaskCore.describeStep(step) : "",
        error: detail && detail.error || ""
    });
    // Close after success; keep a failed run's tab open so it can be inspected.
    if (status === "success" && !task.keepOpen) {
        if (entry.windowId) browser.windows.remove(entry.windowId).catch(function () {});
        else browser.tabs.remove(tabId).catch(function () {});
    }
}

async function logRun(task, run) {
    run.taskId = task.id;
    run.taskName = task.name;
    run.finishedAt = new Date().toISOString();
    await mutateTasks(async function (store) {
        TaskCore.addRun(store, run);
        var stored = store.tasks.find(function (t) { return t.id === task.id; });
        if (stored) {
            stored.lastRun = { at: run.finishedAt, status: run.status, error: run.error || "", trigger: run.trigger };
            stored.nextRunAt = await scheduleTask(stored);
        }
    });
    if (run.status === "failed") {
        browser.browserAction.setBadgeBackgroundColor({ color: "#d9534f" });
        browser.browserAction.setBadgeText({ text: "!" });
        browser.browserAction.setTitle({ title: "Agent OS: scheduled task “" + task.name + "” failed: " + (run.error || "") });
    }
    reportTaskRun(run);
}

function reportTaskRun(run) {
    captureSettings().then(async function (settings) {
        await bridgeFetch("/batch", {
            method: "POST",
            body: {
                schema: "agent-os/browser-bridge-batch/v1",
                batch_id: "task-" + run.runId,
                device: settings.device || "",
                events: [{
                    event_id: "scheduled-task:" + run.runId,
                    source: "scheduled-tasks",
                    event_type: "task_run",
                    source_key: "scheduled-task:" + run.taskId,
                    occurred_at: run.finishedAt,
                    device: settings.device || "",
                    // Names, status and step only: never values or credentials.
                    payload: {
                        task_id: run.taskId, task_name: run.taskName, status: run.status, trigger: run.trigger,
                        step_index: run.stepIndex, step: run.stepLabel, error: run.error,
                        started_at: run.startedAt, finished_at: run.finishedAt
                    }
                }]
            }
        });
    }).catch(function () { /* the run log in the extension is the source of truth */ });
}

setInterval(function () {
    replays.forEach(function (entry, tabId) {
        if (Date.now() - entry.lastProgress > REPLAY_STALL_MS) {
            finishReplay(tabId, "failed", { error: "the page stopped responding (no progress for 90s)" });
        }
    });
}, 15000);

browser.tabs.onRemoved.addListener(function (tabId) {
    if (recordings.has(tabId)) recordings.delete(tabId);
    if (replays.has(tabId)) finishReplay(tabId, "failed", { error: "the task's tab was closed" });
});

// -- messages -------------------------------------------------------------------------------------

function senderTab(sender) {
    return sender && sender.tab ? sender.tab.id : -1;
}

async function handleTaskMessage(message, sender) {
    var tabId = senderTab(sender);
    switch (message.type) {
    // content/tasks.js
    case "task-hello": {
        if (recordings.has(tabId)) {
            var rec = recordings.get(tabId);
            var store = await loadTaskStore();
            var task = store.tasks.find(function (t) { return t.id === rec.taskId; });
            return { mode: "record", taskName: task ? task.name : "task", useLogin: Boolean(task && task.hasCredentials), count: rec.steps.length };
        }
        if (replays.has(tabId)) {
            var entry = replays.get(tabId);
            entry.lastProgress = Date.now();
            var replayTask = (await loadTaskStore()).tasks.find(function (t) { return t.id === entry.taskId; });
            return { mode: "replay", steps: entry.steps, index: entry.index, runId: entry.runId, taskName: replayTask ? replayTask.name : "" };
        }
        return null;
    }
    case "task-record-step": {
        var recording = recordings.get(tabId);
        if (!recording) return null;
        var step = TaskCore.normalizeStep(message.step);
        if (step) recording.steps.push(step);
        return { count: recording.steps.length };
    }
    case "task-record-undo": {
        var r = recordings.get(tabId);
        if (!r) return null;
        r.steps.pop();
        return { count: r.steps.length };
    }
    case "task-record-finish":
        return finishRecording(tabId, true);
    case "task-record-cancel":
        return finishRecording(tabId, false);
    case "task-replay-progress": {
        var progress = replays.get(tabId);
        if (!progress) return null;
        progress.index = Math.max(0, Math.min(Number(message.index) || 0, progress.steps.length));
        progress.lastProgress = Date.now();
        return { ok: true };
    }
    case "task-replay-done":
        await finishReplay(tabId, "success", {});
        return { ok: true };
    case "task-replay-fail":
        await finishReplay(tabId, "failed", { index: message.index, error: message.error });
        return { ok: true };
    case "task-credential": {
        // Only the tab replaying a task, at a step that asks for this field.
        var replay = replays.get(tabId);
        var current = replay && replay.steps[replay.index];
        if (!replay || !current || current.type !== "fill" || current.credential !== message.field) {
            return { error: "not allowed" };
        }
        var res = await nativeRequest({ cmd: "credential_get", task_id: replay.taskId, field: message.field });
        if (!res || !res.ok) return { error: res && res.error || "native helper " + bridgeStatus.native };
        return { value: res.value };
    }
    // options page / popup
    case "tasks-get":
        return loadTaskStore();
    case "task-save":
        return mutateTasks(async function (store) {
            var incoming = TaskCore.normalizeTask(message.task);
            var existing = store.tasks.find(function (t) { return t.id === incoming.id; });
            if (existing) {
                incoming.steps = message.task.steps ? incoming.steps : existing.steps;
                incoming.createdAt = existing.createdAt;
                incoming.hasCredentials = existing.hasCredentials;
                incoming.usernameHint = existing.usernameHint;
                incoming.lastRun = existing.lastRun;
            }
            var errors = TaskCore.validateTask(incoming);
            if (errors.length) return { ok: false, error: errors.join(" ") };
            var creds = message.credentials || {};
            if (creds.clear) {
                await nativeRequest({ cmd: "credential_delete", task_id: incoming.id });
                incoming.hasCredentials = false;
                incoming.usernameHint = "";
            } else if (creds.username || creds.password) {
                await saveCredentials(incoming.id, creds.username || "", creds.password || "");
                incoming.hasCredentials = true;
                if (creds.username) incoming.usernameHint = creds.username;
            }
            incoming.updatedAt = new Date().toISOString();
            incoming.nextRunAt = await scheduleTask(incoming);
            store.tasks = store.tasks.filter(function (t) { return t.id !== incoming.id; }).concat([incoming]);
            return { ok: true, task: incoming };
        }).catch(function (error) { return { ok: false, error: String(error.message || error) }; });
    case "task-delete":
        return mutateTasks(async function (store) {
            store.tasks = store.tasks.filter(function (t) { return t.id !== message.id; });
            await browser.alarms.clear(TASK_ALARM_PREFIX + message.id);
            await nativeRequest({ cmd: "credential_delete", task_id: message.id });
            return { ok: true };
        });
    case "task-record-start":
        return startRecording(message.id).catch(function (error) { return { ok: false, error: String(error.message || error) }; });
    case "task-run":
        return runTask(message.id, "manual");
    case "task-clear-badge":
        browser.browserAction.setBadgeText({ text: "" });
        browser.browserAction.setTitle({ title: "Agent OS" });
        return { ok: true };
    default:
        return undefined;
    }
}

browser.runtime.onMessage.addListener(function (message, sender) {
    if (!message || typeof message.type !== "string") return undefined;
    if (message.type.indexOf("task") !== 0) return undefined;
    return handleTaskMessage(message, sender);
});

scheduleAllTasks(true);
