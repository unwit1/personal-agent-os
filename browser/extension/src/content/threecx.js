/*
 * Agent OS: 3CX web client sync.
 *
 * Runs in an open 3CX web client tab. It notes the web client's own
 * MyPhoneSession header (kept in memory only) and, every five minutes, asks
 * the PBX for this extension's voicemail box and call history with the same
 * protobuf requests the web client uses. New voicemail audio is downloaded.
 * Everything goes to the local Agent OS bridge only (employee data stays on
 * this computer). The unread-chat counter raises a desktop notification.
 */
(function () {
    "use strict";

    if (window.top !== window) return;
    var X = globalThis.AgentOs3cx;
    if (!X || !/(^|\.)3cx\.[a-z.]+$/i.test(location.hostname)) return;

    var SYNC_EVERY_MS = 5 * 60 * 1000;
    var STATE_KEY = "threecx_sync_state_v1";
    var session = "";
    var syncing = false;
    var lastSyncAt = 0;
    var lastError = "";

    // -- the web client's session (from its own requests) ------------------------

    function headerValue(headers, name) {
        if (!headers) return "";
        name = name.toLowerCase();
        if (typeof headers.get === "function") return headers.get(name) || "";
        var found = "";
        if (Array.isArray(headers)) {
            headers.forEach(function (pair) { if (String(pair[0]).toLowerCase() === name) found = String(pair[1]); });
        } else {
            Object.keys(headers).forEach(function (key) { if (key.toLowerCase() === name) found = String(headers[key]); });
        }
        return found;
    }

    function notePageRequest(input, init) {
        var url = typeof input === "string" ? input : String(input && input.url || "");
        if (url.indexOf(X.ENDPOINT) === -1) return;
        noteSession(headerValue(init && init.headers, "MyPhoneSession") || headerValue(input && input.headers, "MyPhoneSession"));
    }

    function noteSession(value) {
        value = String(value || "");
        if (!value || value === session) return;
        var first = !session;
        session = value;
        if (first) setTimeout(function () { sync("session"); }, 3000);
    }

    (function hookPageRequests() {
        var page = window.wrappedJSObject;
        if (!page || typeof exportFunction !== "function") return;
        if (typeof page.fetch === "function") {
            var original = page.fetch;
            page.fetch = exportFunction(function (input, init) {
                try { notePageRequest(input, init); } catch (error) { /* never break the page */ }
                return original.call(page, input, init);
            }, window);
        }
        // The web client's MyPhone calls go through Angular's HttpClient (XHR).
        var proto = page.XMLHttpRequest && page.XMLHttpRequest.prototype;
        if (proto && typeof proto.setRequestHeader === "function") {
            var setHeader = proto.setRequestHeader;
            proto.setRequestHeader = exportFunction(function (name, value) {
                try {
                    if (String(name).toLowerCase() === "myphonesession") noteSession(value);
                } catch (error) { /* never break the page */ }
                return setHeader.call(this, name, value);
            }, window);
        }
    })();

    // -- PBX requests -------------------------------------------------------------

    function post(bytes) {
        var fetcher = typeof content !== "undefined" && content && typeof content.fetch === "function"
            ? content.fetch.bind(content) : fetch;
        return fetcher(X.ENDPOINT, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Accept": "application/octet-stream",
                "Content-Type": "application/octet-stream",
                "MyPhoneSession": session,
                "ngsw-bypass": "bypass"
            },
            body: bytes
        }).then(function (response) {
            if (!response.ok) throw new Error("3CX answered HTTP " + response.status);
            return response.arrayBuffer();
        }).then(function (buffer) {
            return X.decodeResponse(new Uint8Array(buffer));
        });
    }

    function loadState() {
        return browser.storage.local.get(STATE_KEY).then(function (res) {
            var state = res[STATE_KEY] || {};
            state.downloaded = state.downloaded || {};
            return state;
        });
    }

    function saveState(state) {
        var update = {};
        update[STATE_KEY] = state;
        return browser.storage.local.set(update);
    }

    function send(message) {
        return browser.runtime.sendMessage(message);
    }

    async function sync(reason) {
        if (!session || syncing) return { ok: false, reason: session ? "busy" : "no-session" };
        syncing = true;
        try {
            var me = X.myInfoRecord((await post(X.myInfoRequest())).MyInfo);
            if (!me.extension) throw new Error("3CX did not return this extension");
            var history = (await post(X.callHistoryRequest(me.extension, 100, 0))).CallHistory || {};
            var calls = (history.Records || []).map(function (record) { return X.callRecord(record, me.extension); });
            var state = await loadState();
            var downloaded = 0;
            for (var i = 0; i < me.voicemails.length; i += 1) {
                var vm = me.voicemails[i];
                if (state.downloaded[vm.id] || !vm.filename) continue;
                var file = (await post(X.voicemailFileRequest(vm))).FileResult || {};
                if (!file.Content || !file.Content.length) continue;
                var saved = await send({ type: "threecx-voicemail", voicemail: Object.assign({ extension: me.extension }, vm), audio_base64: X.base64(file.Content) });
                if (saved && saved.ok) {
                    state.downloaded[vm.id] = saved.path || true;
                    downloaded += 1;
                }
            }
            var now = new Date().toISOString();
            var events = calls.map(function (call) {
                return { event_id: "3cx:call:" + call.id, source: "3cx", event_type: "call", source_key: String(call.id),
                    occurred_at: call.started_at || now, payload: Object.assign({ extension: me.extension }, call) };
            }).concat(me.voicemails.map(function (vm) {
                return { event_id: "3cx:voicemail:" + vm.id, source: "3cx", event_type: "voicemail", source_key: String(vm.id),
                    occurred_at: vm.received_at || now,
                    payload: Object.assign({ extension: me.extension, audio_path: typeof state.downloaded[vm.id] === "string" ? state.downloaded[vm.id] : "" }, vm) };
            }));
            if (events.length) await send({ type: "threecx-events", events: events });
            state.extension = me.extension;
            state.lastSyncAt = now;
            await saveState(state);
            lastSyncAt = Date.now();
            lastError = "";
            return { ok: true, reason: reason, calls: calls.length, voicemails: me.voicemails.length, downloaded: downloaded };
        } catch (error) {
            lastError = String(error && error.message || error);
            console.warn("[Agent OS] 3CX sync failed", error);
            return { ok: false, error: lastError };
        } finally {
            syncing = false;
        }
    }

    setInterval(function () {
        if (Date.now() - lastSyncAt >= SYNC_EVERY_MS) sync("timer");
    }, 60 * 1000);

    // -- unread chats -------------------------------------------------------------

    var lastUnread = null;

    function badgeCount(selector) {
        var link = document.querySelector(selector);
        var badge = link && link.querySelector(".badge");
        var n = badge ? parseInt(badge.textContent, 10) : 0;
        return isFinite(n) ? n : 0;
    }

    function checkUnread() {
        var unread = badgeCount("a[href='#/chat']");
        if (lastUnread !== null && unread > lastUnread) {
            var at = new Date().toISOString();
            send({ type: "threecx-notify", title: "New 3CX message", message: unread + " unread chat message" + (unread === 1 ? "" : "s") });
            send({ type: "threecx-events", events: [{ event_id: "3cx:chat-unread:" + at, source: "3cx", event_type: "chat_unread",
                occurred_at: at, payload: { unread: unread, previous: lastUnread, page_title: document.title } }] });
        }
        lastUnread = unread;
    }

    setInterval(checkUnread, 10 * 1000);

    browser.runtime.onMessage.addListener(function (message) {
        if (!message || typeof message !== "object") return undefined;
        if (message.type === "threecx-sync") {
            return Date.now() - lastSyncAt >= (message.force ? 0 : SYNC_EVERY_MS - 30000) ? sync("alarm") : Promise.resolve({ ok: true, skipped: true });
        }
        if (message.type === "threecx-status") {
            return Promise.resolve({ session: Boolean(session), lastSyncAt: lastSyncAt, lastError: lastError, unread: lastUnread });
        }
        return undefined;
    });
})();
