/*
 * Tampermonkey-compatible GM_* API for the bundled Universal Capture
 * userscript, backed by browser.storage.local and the background page.
 *
 * GM_getValue is synchronous, so every "gm:" key is preloaded into a cache
 * before the userscript starts (capture.generated.js awaits
 * __agentOsGmReady). Writes update the cache immediately and persist
 * asynchronously; other tabs' writes arrive through storage.onChanged.
 */
(function () {
    "use strict";

    var PREFIX = "gm:";
    var cache = new Map();
    var menu = [];
    var resolveReady;

    globalThis.__agentOsGmReady = new Promise(function (resolve) { resolveReady = resolve; });

    function copy(value) {
        if (value === undefined || value === null || typeof value !== "object") return value;
        try {
            return structuredClone(value);
        } catch (error) {
            return JSON.parse(JSON.stringify(value));
        }
    }

    browser.storage.local.get(null).then(function (all) {
        Object.keys(all || {}).forEach(function (key) {
            if (key.indexOf(PREFIX) === 0) cache.set(key.slice(PREFIX.length), all[key]);
        });
        resolveReady();
    }, function () { resolveReady(); });

    browser.storage.onChanged.addListener(function (changes, area) {
        if (area !== "local") return;
        Object.keys(changes).forEach(function (key) {
            if (key.indexOf(PREFIX) !== 0) return;
            var name = key.slice(PREFIX.length);
            if (changes[key].newValue === undefined) cache.delete(name);
            else cache.set(name, changes[key].newValue);
        });
    });

    globalThis.GM_getValue = function (name, fallback) {
        return cache.has(name) ? copy(cache.get(name)) : fallback;
    };

    globalThis.GM_setValue = function (name, value) {
        var stored = copy(value);
        cache.set(name, stored);
        var update = {};
        update[PREFIX + name] = stored;
        browser.storage.local.set(update).catch(function (error) {
            console.warn("[Agent OS] could not persist", name, error);
        });
    };

    globalThis.GM_deleteValue = function (name) {
        cache.delete(name);
        browser.storage.local.remove(PREFIX + name).catch(function () {});
    };

    globalThis.GM_listValues = function () {
        return Array.from(cache.keys());
    };

    globalThis.GM_registerMenuCommand = function (name, fn) {
        var id = "m" + menu.length;
        menu.push({ id: id, name: String(name), fn: fn });
        return id;
    };

    globalThis.GM_openInTab = function (url, options) {
        var opts = typeof options === "boolean" ? { active: !options } : (options || {});
        var closed = false;
        browser.runtime.sendMessage({ type: "open-tab", url: String(url), active: Boolean(opts.active) });
        return { closed: false, close: function () { closed = true; }, get isClosed() { return closed; } };
    };

    globalThis.GM_setClipboard = function (text) {
        var value = String(text == null ? "" : text);
        navigator.clipboard.writeText(value).catch(function () {
            browser.runtime.sendMessage({ type: "clipboard-write", text: value });
        });
    };

    // Requests go through the background page, which holds the host
    // permissions (loopback bridge, Apps Script) and is not bound by CORS.
    globalThis.GM_xmlhttpRequest = function (details) {
        var aborted = false;
        browser.runtime.sendMessage({
            type: "gm-xhr",
            method: details.method || "GET",
            url: details.url,
            headers: details.headers || {},
            data: details.data == null ? null : String(details.data),
            timeout: details.timeout || 0
        }).then(function (response) {
            if (aborted) return;
            if (!response || response.error === "timeout") {
                if (details.ontimeout) details.ontimeout(response || {});
                else if (details.onerror) details.onerror(response || {});
                return;
            }
            if (response.error) {
                if (details.onerror) details.onerror(response);
                return;
            }
            if (details.onload) details.onload(response);
        }, function (error) {
            if (!aborted && details.onerror) details.onerror({ error: String(error) });
        });
        return { abort: function () { aborted = true; if (details.onabort) details.onabort({}); } };
    };

    browser.runtime.onMessage.addListener(function (message) {
        if (!message || typeof message !== "object") return undefined;
        if (message.type === "gm-menu-list") {
            if (window.top !== window) return undefined;
            return Promise.resolve({
                commands: menu.map(function (item) { return { id: item.id, name: item.name }; })
            });
        }
        if (message.type === "gm-menu-run") {
            if (window.top !== window) return undefined;
            var entry = menu.find(function (item) {
                return item.id === message.id || item.name === message.name;
            });
            if (!entry) return Promise.resolve({ ok: false, error: "unknown command" });
            // Defer so the popup can close before any prompt()/alert() opens.
            setTimeout(function () {
                try { entry.fn(); } catch (error) { console.error("[Agent OS]", entry.name, error); }
            }, 30);
            return Promise.resolve({ ok: true });
        }
        return undefined;
    });
})();
