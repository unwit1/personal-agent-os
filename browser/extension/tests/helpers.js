"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");

const SRC = path.resolve(__dirname, "..", "src");
const DIST = path.resolve(__dirname, "..", "dist", "agent-os-firefox");

function read(rel, base) {
    return fs.readFileSync(path.join(base || SRC, rel), "utf8");
}

// Minimal WebExtension API double: storage.local with onChanged events,
// runtime messaging with a pluggable background handler, tab messaging.
function makeBrowser(options) {
    const opts = options || {};
    const data = Object.assign({}, opts.storage || {});
    const changeListeners = [];
    const messageListeners = [];
    const clone = (v) => (v === undefined ? undefined : JSON.parse(JSON.stringify(v)));

    function emit(changes) {
        changeListeners.forEach((fn) => fn(changes, "local"));
    }

    const browser = {
        _data: data,
        _messageListeners: messageListeners,
        storage: {
            local: {
                async get(keys) {
                    if (keys == null) return clone(data);
                    const list = Array.isArray(keys) ? keys : [keys];
                    const out = {};
                    list.forEach((k) => { if (k in data) out[k] = clone(data[k]); });
                    return out;
                },
                async set(values) {
                    const changes = {};
                    Object.keys(values).forEach((k) => {
                        changes[k] = { oldValue: clone(data[k]), newValue: clone(values[k]) };
                        data[k] = clone(values[k]);
                    });
                    emit(changes);
                },
                async remove(keys) {
                    const changes = {};
                    (Array.isArray(keys) ? keys : [keys]).forEach((k) => {
                        changes[k] = { oldValue: clone(data[k]), newValue: undefined };
                        delete data[k];
                    });
                    emit(changes);
                }
            },
            onChanged: { addListener: (fn) => changeListeners.push(fn) }
        },
        runtime: {
            getManifest: () => ({ version: "1.0.0-test" }),
            getURL: (p) => "moz-extension://test/" + p,
            async sendMessage(message) {
                if (opts.onBackgroundMessage) return opts.onBackgroundMessage(message, browser);
                return undefined;
            },
            onMessage: { addListener: (fn) => messageListeners.push(fn) }
        }
    };
    return browser;
}

// Deliver a message to the content-script listeners, as tabs.sendMessage would.
async function sendToContent(browser, message) {
    for (const fn of browser._messageListeners) {
        const result = fn(message, {});
        if (result !== undefined) return result;
    }
    return undefined;
}

function makeDom(html, url, browser) {
    const dom = new JSDOM(html, { url, runScripts: "outside-only", pretendToBeVisual: true });
    dom.window.browser = browser;
    if (typeof dom.window.structuredClone !== "function") {
        dom.window.structuredClone = (v) => JSON.parse(JSON.stringify(v));
    }
    return dom;
}

function load(dom, files, base) {
    files.forEach((rel) => dom.window.eval(read(rel, base) + "\n//# sourceURL=" + rel));
}

function tick(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms || 0));
}

async function waitFor(fn, timeoutMs) {
    const started = Date.now();
    while (Date.now() - started < (timeoutMs || 3000)) {
        const value = fn();
        if (value) return value;
        await tick(20);
    }
    throw new Error("timed out waiting for condition");
}

module.exports = { SRC, DIST, read, makeBrowser, sendToContent, makeDom, load, tick, waitFor };
