/*
 * Scheduled tasks in the page: the step recorder and the replayer.
 *
 * The background page decides whether this tab is recording or replaying a
 * task (task-hello). Both modes survive page loads because progress lives in
 * the background. Passwords are never recorded: typing into a password field
 * becomes an "enter saved password" step, and the value is fetched from the
 * Windows Credential Manager (through the background + native helper) only at
 * the moment a replay fills it.
 */
(function () {
    "use strict";

    if (window.top !== window) return;
    var Task = globalThis.AgentOsTaskCore;
    if (!Task) return;

    var CLICKABLE = "a[href], button, [role='button'], [role='link'], [role='menuitem'], [role='tab'], [role='option'], " +
        "[role='checkbox'], [role='switch'], input[type='submit'], input[type='button'], input[type='image'], " +
        "input[type='reset'], summary, label, [onclick]";
    var SENSITIVE = /(otp|one.?time|2fa|mfa|totp|security.?code|verification.?code|auth.?code|cvv|cvc|csc|card.?number|cc-?num|iban|routing|ssn|social.?security)/i;
    var USERNAME = /(user|e-?mail|login|account|sign.?in|member|customer.?id)/i;

    function clean(text) {
        return String(text == null ? "" : text).replace(/\s+/g, " ").trim();
    }

    function sleep(ms) {
        return new Promise(function (r) { setTimeout(r, ms); });
    }

    function cssEscape(value) {
        return window.CSS && CSS.escape ? CSS.escape(value) : String(value).replace(/[^a-zA-Z0-9_-]/g, "\\$&");
    }

    // Generated ids (react-123, :r4:, long hashes) change between visits.
    function stableId(id) {
        return id && !/\d{3,}|^:r|[0-9a-f]{12,}|^ember|^ext-gen|^mui-|^radix-/i.test(id) ? id : "";
    }

    function cssPath(el) {
        var parts = [];
        var node = el;
        while (node && node.nodeType === 1 && node !== document.documentElement && parts.length < 7) {
            var part = node.tagName.toLowerCase();
            var id = stableId(node.id);
            if (id) { parts.unshift("#" + cssEscape(id)); break; }
            var parent = node.parentElement;
            if (parent) {
                var same = Array.from(parent.children).filter(function (c) { return c.tagName === node.tagName; });
                if (same.length > 1) part += ":nth-of-type(" + (same.indexOf(node) + 1) + ")";
            }
            parts.unshift(part);
            node = parent;
        }
        return parts.join(" > ");
    }

    function labelFor(el) {
        var label = "";
        if (el.id) {
            var forLabel = document.querySelector("label[for='" + cssEscape(el.id) + "']");
            if (forLabel) label = clean(forLabel.textContent);
        }
        if (!label && el.closest && el.closest("label")) label = clean(el.closest("label").textContent);
        return label.slice(0, 80);
    }

    function describe(el) {
        var target = { tag: el.tagName.toLowerCase(), css: cssPath(el) };
        var id = stableId(el.id);
        if (id) target.id = id;
        ["name", "type", "placeholder", "aria-label", "data-testid", "data-test", "data-qa", "data-cy", "autocomplete"].forEach(function (attr) {
            var value = el.getAttribute(attr);
            if (!value) return;
            var key = { "aria-label": "aria", "data-testid": "testid", "data-test": "testid", "data-qa": "testid", "data-cy": "testid" }[attr] || attr;
            if (!target[key]) target[key] = value.slice(0, 120);
        });
        if (el.matches("input, textarea, select")) {
            var label = labelFor(el);
            if (label) target.label = label;
        } else {
            var text = clean(el.innerText || el.textContent || el.getAttribute("value") || "");
            if (text && text.length <= 80) target.text = text;
        }
        return target;
    }

    function visible(el) {
        if (!el || !el.isConnected) return false;
        var style = getComputedStyle(el);
        return style.display !== "none" && style.visibility !== "hidden" && !el.disabled;
    }

    function firstVisible(nodes) {
        for (var i = 0; i < nodes.length; i += 1) if (visible(nodes[i])) return nodes[i];
        return null;
    }

    function query(selector) {
        try { return Array.from(document.querySelectorAll(selector)); } catch (error) { return []; }
    }

    // Try the most stable description first, the structural CSS path last.
    function findOnce(t) {
        if (!t) return null;
        var tag = t.tag || "*";
        var found = null;
        if (t.id) found = firstVisible(query("#" + cssEscape(t.id)));
        if (!found && t.testid) {
            found = firstVisible(query(["data-testid", "data-test", "data-qa", "data-cy"].map(function (a) {
                return "[" + a + "='" + t.testid.replace(/'/g, "\\'") + "']";
            }).join(",")));
        }
        if (!found && t.name) found = firstVisible(query(tag + "[name='" + t.name.replace(/'/g, "\\'") + "']"));
        if (!found && t.aria) found = firstVisible(query(tag + "[aria-label='" + t.aria.replace(/'/g, "\\'") + "']"));
        if (!found && t.label) {
            found = firstVisible(query("input, textarea, select").filter(function (el) { return labelFor(el) === t.label; }));
        }
        if (!found && t.placeholder) found = firstVisible(query(tag + "[placeholder='" + t.placeholder.replace(/'/g, "\\'") + "']"));
        if (!found && t.text) {
            var byText = query(t.tag && t.tag !== "*" ? t.tag : CLICKABLE).filter(function (el) {
                return clean(el.innerText || el.textContent || el.getAttribute("value") || "") === t.text;
            });
            found = firstVisible(byText);
        }
        if (!found && t.css) found = firstVisible(query(t.css));
        return found;
    }

    async function find(target, timeoutMs) {
        var deadline = Date.now() + (timeoutMs || 15000);
        while (Date.now() < deadline) {
            var el = findOnce(target);
            if (el) return el;
            await sleep(250);
        }
        throw new Error("could not find “" + Task.targetLabel(target) + "” on " + location.host + location.pathname);
    }

    function setValue(el, value) {
        el.focus();
        if (el.isContentEditable) {
            el.textContent = value;
        } else {
            var proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
            var desc = Object.getOwnPropertyDescriptor(proto, "value");
            if (desc && desc.set) desc.set.call(el, value); else el.value = value;
        }
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
    }

    // -- recorder ---------------------------------------------------------------------

    var recorder = null;

    function isTextField(el) {
        if (!el || !el.matches) return false;
        if (el.isContentEditable) return true;
        if (el.tagName === "TEXTAREA") return true;
        if (el.tagName !== "INPUT") return false;
        var type = String(el.type || "text").toLowerCase();
        return ["text", "email", "password", "search", "tel", "url", "number", "date", "time", "datetime-local", "month", "week"].indexOf(type) !== -1;
    }

    function fieldKind(el) {
        var type = String(el.type || "").toLowerCase();
        var hints = [el.name, el.id, el.getAttribute("autocomplete"), el.getAttribute("placeholder"),
            el.getAttribute("aria-label"), labelFor(el)].join(" ");
        if (type === "password" || /current-password|new-password/i.test(el.getAttribute("autocomplete") || "")) return "password";
        if (SENSITIVE.test(hints)) return "sensitive";
        if (/username|email/i.test(el.getAttribute("autocomplete") || "") || type === "email" || USERNAME.test(hints)) return "username";
        return "text";
    }

    function send(message) {
        return browser.runtime.sendMessage(message).catch(function () { return null; });
    }

    function recordStep(step) {
        step.url = location.href;
        send({ type: "task-record-step", step: step }).then(function (res) {
            if (res) updateToolbar(res.count, Task.describeStep(step));
        });
    }

    function flushField(el) {
        if (!recorder || !recorder.pending.has(el)) return;
        recorder.pending.delete(el);
        var kind = fieldKind(el);
        var step = { type: "fill", target: describe(el) };
        if (kind === "password") step.credential = "password";
        else if (kind === "sensitive") step.manual = true;
        else if (kind === "username" && recorder.useLogin) step.credential = "username";
        else step.value = el.isContentEditable ? clean(el.textContent) : el.value;
        recordStep(step);
    }

    function flushAll() {
        if (!recorder) return;
        Array.from(recorder.pending.keys()).forEach(flushField);
    }

    function inToolbar(node) {
        return recorder && recorder.host && (node === recorder.host || recorder.host.contains(node));
    }

    function onInput(event) {
        var el = event.target;
        if (inToolbar(el) || !isTextField(el)) return;
        recorder.pending.set(el, true);
    }

    function onChange(event) {
        var el = event.target;
        if (inToolbar(el) || !el.matches) return;
        if (el.tagName === "SELECT") {
            var option = el.options[el.selectedIndex];
            recordStep({ type: "select", target: describe(el), value: el.value, text: option ? clean(option.textContent) : "" });
        } else if (el.matches("input[type='checkbox'], input[type='radio']")) {
            recordStep({ type: "check", target: describe(el), checked: el.checked });
        } else if (isTextField(el)) {
            flushField(el);
        }
    }

    function onKeydown(event) {
        var el = event.target;
        if (inToolbar(el) || event.key !== "Enter" || !isTextField(el) || el.tagName === "TEXTAREA") return;
        recorder.pending.set(el, true);
        flushField(el);
        recordStep({ type: "key", key: "Enter", target: describe(el) });
    }

    function onClick(event) {
        var raw = event.target instanceof Element ? event.target : null;
        if (!raw || inToolbar(raw) || event.button !== 0) return;
        // Focusing a field is not a step; its value is recorded on change.
        if (isTextField(raw) || raw.tagName === "SELECT" || raw.tagName === "OPTION") return;
        // Checkboxes/radios (and their labels) are recorded from their change event.
        if (raw.matches("input[type='checkbox'], input[type='radio']")) return;
        var label = raw.closest("label");
        if (label && label.control && label.control.matches("input[type='checkbox'], input[type='radio']")) return;
        var el = raw.closest(CLICKABLE) || raw;
        flushAll();
        recordStep({ type: "click", target: describe(el) });
    }

    function buildToolbar(state) {
        var host = document.createElement("div");
        host.style.cssText = "position:fixed!important;top:12px!important;right:12px!important;z-index:2147483647!important;";
        var shadow = host.attachShadow({ mode: "open" });
        var style = document.createElement("style");
        style.textContent = [
            ".bar{font:13px/1.35 system-ui,Segoe UI,sans-serif;background:#1f2329;color:#eef1f4;border:1px solid #c0392b;",
            "border-radius:10px;padding:10px 12px;width:300px;box-shadow:0 8px 28px rgba(0,0,0,.35)}",
            ".title{font-weight:700;display:flex;align-items:center;gap:6px}.dot{width:9px;height:9px;border-radius:50%;background:#e74c3c;",
            "animation:p 1.2s infinite}@keyframes p{50%{opacity:.3}}.muted{color:#9aa4ae;font-size:12px;margin:6px 0;min-height:16px}",
            ".row{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}button{font:inherit;font-size:12px;border-radius:6px;border:1px solid #3a414b;",
            "background:#2a3139;color:#eef1f4;padding:4px 8px;cursor:pointer}button.primary{background:#2d6cdf;border-color:#2d6cdf}",
            "button.danger{color:#ff8a80}.hint{font-size:11px;color:#9aa4ae;margin-top:6px}"
        ].join("");
        var bar = document.createElement("div");
        bar.className = "bar";
        var title = document.createElement("div");
        title.className = "title";
        var dot = document.createElement("span");
        dot.className = "dot";
        var name = document.createElement("span");
        name.textContent = "Recording: " + state.taskName;
        title.append(dot, name);
        var status = document.createElement("div");
        status.className = "muted";
        var row = document.createElement("div");
        row.className = "row";
        function button(label, cls, fn) {
            var b = document.createElement("button");
            b.type = "button";
            b.textContent = label;
            if (cls) b.className = cls;
            b.addEventListener("click", function (event) { event.preventDefault(); event.stopPropagation(); fn(); });
            row.appendChild(b);
        }
        button("Undo last", "", function () {
            send({ type: "task-record-undo" }).then(function (res) { if (res) updateToolbar(res.count, "Removed the last step"); });
        });
        button("Add 2s wait", "", function () { recordStep({ type: "wait", ms: 2000 }); });
        button("Finish & save", "primary", function () {
            flushAll();
            setTimeout(function () { send({ type: "task-record-finish" }); }, 150);
        });
        button("Cancel", "danger", function () { send({ type: "task-record-cancel" }); });
        var hint = document.createElement("div");
        hint.className = "hint";
        hint.textContent = state.useLogin
            ? "Type your login as usual: the password is never recorded and is filled from your saved login."
            : "Passwords are never recorded. Save a login on the task to fill them automatically.";
        bar.append(title, status, row, hint);
        shadow.append(style, bar);
        recorder.status = status;
        return host;
    }

    function updateToolbar(count, last) {
        if (!recorder || !recorder.status) return;
        recorder.status.textContent = count + " step" + (count === 1 ? "" : "s") + (last ? " · " + last : "");
    }

    function startRecorder(state) {
        recorder = { pending: new Map(), useLogin: Boolean(state.useLogin), host: null, status: null };
        function mount() {
            if (!document.body) return setTimeout(mount, 100);
            recorder.host = buildToolbar(state);
            document.documentElement.appendChild(recorder.host);
            updateToolbar(state.count || 0, "");
        }
        mount();
        document.addEventListener("input", onInput, true);
        document.addEventListener("change", onChange, true);
        document.addEventListener("keydown", onKeydown, true);
        document.addEventListener("click", onClick, true);
        window.addEventListener("pagehide", flushAll, true);
    }

    // -- replayer ---------------------------------------------------------------------

    async function credential(field) {
        var res = await send({ type: "task-credential", field: field });
        if (!res || res.error || typeof res.value !== "string") {
            throw new Error("saved " + field + " unavailable: " + (res && res.error || "no saved login"));
        }
        return res.value;
    }

    async function pressEnter(el) {
        el.focus();
        var down = new KeyboardEvent("keydown", { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true, cancelable: true });
        el.dispatchEvent(down);
        el.dispatchEvent(new KeyboardEvent("keypress", { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true, cancelable: true }));
        el.dispatchEvent(new KeyboardEvent("keyup", { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true }));
        // Synthetic key events never submit a form; do what the browser would,
        // unless the page handled the key itself.
        await sleep(300);
        if (!down.defaultPrevented && el.isConnected && el.form) {
            if (el.form.requestSubmit) el.form.requestSubmit(); else el.form.submit();
        }
    }

    async function runStep(step, index) {
        if (step.type === "wait") { await sleep(step.ms); return; }
        if (step.type === "navigate") {
            await send({ type: "task-replay-progress", index: index + 1 });
            location.href = step.url;
            await sleep(10000);
            return;
        }
        var el = await find(step.target, 15000);
        if (el.scrollIntoView) el.scrollIntoView({ block: "center" });
        if (step.type === "fill") {
            if (step.manual) throw new Error("this step needs manual entry (one-time code or similar)");
            setValue(el, step.credential ? await credential(step.credential) : step.value);
        } else if (step.type === "select") {
            var option = Array.from(el.options || []).find(function (o) { return o.value === step.value; }) ||
                Array.from(el.options || []).find(function (o) { return clean(o.textContent) === step.text; });
            if (!option) throw new Error("option “" + (step.text || step.value) + "” is gone");
            el.value = option.value;
            el.dispatchEvent(new Event("input", { bubbles: true }));
            el.dispatchEvent(new Event("change", { bubbles: true }));
        } else if (step.type === "check") {
            if (Boolean(el.checked) !== step.checked) el.click();
        } else if (step.type === "click" || step.type === "key") {
            // Record progress first: this action may load a new page.
            await send({ type: "task-replay-progress", index: index + 1 });
            if (step.type === "click") el.click(); else await pressEnter(el);
            await sleep(900);
        }
    }

    async function startReplay(state) {
        document.documentElement.setAttribute("data-agent-os-replaying", "1");
        await sleep(state.index === 0 ? 1200 : 700);
        try {
            for (var i = state.index; i < state.steps.length; i += 1) {
                await send({ type: "task-replay-progress", index: i });
                await runStep(state.steps[i], i);
            }
            await send({ type: "task-replay-done" });
        } catch (error) {
            await send({ type: "task-replay-fail", index: i, error: String(error && error.message || error) });
        }
    }

    send({ type: "task-hello" }).then(function (state) {
        if (!state) return;
        if (state.mode === "record") startRecorder(state);
        else if (state.mode === "replay") startReplay(state);
    });

    globalThis.__agentOsTaskTest = { describe: describe, findOnce: findOnce, fieldKind: fieldKind };
})();
