/*
 * Shopping collector, page side. Answers only the background's collector
 * messages for the tab the person chose; it never acts on its own. Reads the
 * page (wait / scroll / extract), reports human checks instead of passing
 * them, and shows the collector badge.
 */
(function () {
    "use strict";
    var Core = globalThis.AgentOsCollectorCore;
    if (!Core || window.__agentOsCollector) return;
    window.__agentOsCollector = true;

    var BADGE_ID = "agent-os-shopping-collector-badge";

    function badge(text, warn) {
        var el = document.getElementById(BADGE_ID);
        if (!text) { if (el) el.remove(); return; }
        if (!el) {
            el = document.createElement("div");
            el.id = BADGE_ID;
            el.setAttribute("role", "status");
            el.style.cssText = "position:fixed;z-index:2147483647;right:12px;bottom:12px;padding:6px 10px;border-radius:8px;" +
                "font:12px system-ui,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.25);max-width:360px;color:#fff";
            (document.body || document.documentElement).appendChild(el);
        }
        el.style.background = warn ? "#8a1c1c" : "#1f4fbf";
        el.textContent = text;
    }

    function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

    async function waitFor(selector, timeoutMs) {
        var until = Date.now() + Math.min(Number(timeoutMs) || 10000, 15000);
        while (Date.now() < until) {
            var found = false;
            try { found = Boolean(document.querySelector(selector || "body")); } catch (error) { found = true; }
            if (found) break;
            await sleep(300);
        }
        await sleep(1500);                       // let client-side rendering settle
    }

    async function run(action) {
        if (action.op === "wait") {
            await waitFor(action.selector, action.timeout_ms);
            return { ok: true };
        }
        if (action.op === "scroll") {
            var times = Math.max(1, Math.min(Number(action.times) || 3, 8));
            for (var i = 0; i < times; i += 1) {
                window.scrollBy(0, Math.round(window.innerHeight * 0.9));
                await sleep(900);
            }
            return { ok: true };
        }
        if (action.op === "extract") {
            if (Core.humanCheckPresent(document)) {
                return { human_check: true, url: location.href };
            }
            return { ok: true, step: { kind: action.kind || "jsonld", data: Core.extract(document, action) } };
        }
        return { ok: false, error: "unsupported in-page collector op: " + action.op };
    }

    browser.runtime.onMessage.addListener(function (message) {
        if (!message || typeof message !== "object") return undefined;
        if (message.type === "aos-collect") {
            return run(message.action || {}).catch(function (error) {
                return { ok: false, error: "collector error: " + String(error && error.message || error) };
            });
        }
        if (message.type === "aos-collector-badge") {
            badge(message.text, Boolean(message.warn));
            return Promise.resolve({ ok: true });
        }
        return undefined;
    });
})();
