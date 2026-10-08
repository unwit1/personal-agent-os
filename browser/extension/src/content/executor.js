/*
 * Executes Agent OS bridge DOM actions (browser.execute) in this tab.
 *
 * Safety gate: typing into credential, payment or identity fields is always
 * refused, and clicks that look consequential (submit, send, delete,
 * purchase, ...) return approval_required unless the command carries
 * approved_consequential=true.
 *
 * Pages built from web components (ADP, Salesforce, ...) are read through
 * their shadow roots and same-origin iframes. A selector for an element inside
 * one is written "host >>> inner" (one ">>>" per boundary crossed).
 */
(function () {
    "use strict";

    if (window.top !== window) return;

    var MAX_TEXT = 20000;
    var MAX_INTERACTIVE = 300;
    var MAX_ROOTS = 500;
    var DEEP = " >>> ";
    var INTERACTIVE = "a[href], button, input, select, textarea, [role='button'], [role='link'], [role='menuitem'], " +
        "[role='tab'], [role='treeitem'], [contenteditable='true']";
    var SENSITIVE_FIELD = /pass(word|code|phrase)?|pwd|otp|one.?time|2fa|mfa|totp|verification.?code|security.?code|cvv|cvc|csc|card.?(number|no)|cc-?(number|csc|exp)|credit|debit|iban|routing|account.?(number|no)|sort.?code|ssn|social.?security|tax.?id|passport|driver.?licen|national.?id|\bpin\b|secret|api.?key|token/i;
    var SENSITIVE_AUTOCOMPLETE = /^(current-password|new-password|one-time-code|cc-|transaction-)/i;
    var RISKY_ACTION = /\b(submit|send|post|publish|reply|comment|delete|remove|erase|destroy|discard|archive|trash|buy|purchase|order|checkout|check out|pay|payment|donate|subscribe|unsubscribe|confirm|approve|accept|agree|transfer|withdraw|deposit|sign ?out|log ?out|sign ?up|register|apply|book|reserve|schedule|invite|share|upload|install|uninstall|grant|authori[sz]e|allow|block|report|ban|kick|endorse|vote|follow|unfollow)\b/i;

    var cssEscape = window.CSS && typeof CSS.escape === "function"
        ? function (v) { return CSS.escape(v); }
        : function (v) { return String(v).replace(/[^a-zA-Z0-9_-]/g, "\$&"); };

    function clean(value) {
        return String(value == null ? "" : value).replace(/\s+/g, " ").trim();
    }

    // The shadow root (open or closed: content scripts see both) or same-origin iframe document inside el.
    function innerRoot(el) {
        var shadow = el.openOrClosedShadowRoot || el.shadowRoot;
        if (shadow) return shadow;
        if (el.tagName === "IFRAME" || el.tagName === "FRAME") {
            try { return el.contentDocument || null; } catch (error) { return null; }
        }
        return null;
    }

    // The element a shadow root or iframe document belongs to.
    function hostOf(root) {
        if (root.host) return root.host;
        try { return root.defaultView && root.defaultView.frameElement; } catch (error) { return null; }
    }

    // The page and every shadow root / same-origin iframe document in it, outermost first.
    function allRoots() {
        var roots = [document];
        for (var i = 0; i < roots.length && roots.length < MAX_ROOTS; i += 1) {
            roots[i].querySelectorAll("*").forEach(function (el) {
                var inner = innerRoot(el);
                if (inner && roots.indexOf(inner) === -1) roots.push(inner);
            });
        }
        return roots;
    }

    // First match for a selector; a "host >>> inner" path may start in any root.
    function query(selector) {
        var parts = selector.split(DEEP);
        var el = queryAnywhere(parts[0]);
        for (var i = 1; el && i < parts.length; i += 1) {
            var scope = innerRoot(el);
            el = scope ? scope.querySelector(parts[i]) : null;
        }
        return el;
    }

    // The page first (instant for "iframe#x >>> ..."), then shadow roots / frames one at a time,
    // stopping at the first match; walking every root up front is far too slow on large apps.
    function queryAnywhere(selector) {
        var found = document.querySelector(selector);
        if (found) return found;
        var roots = [document];
        for (var i = 0; i < roots.length && roots.length < MAX_ROOTS; i += 1) {
            var all = roots[i].querySelectorAll("*");
            for (var j = 0; j < all.length; j += 1) {
                var inner = innerRoot(all[j]);
                if (!inner || roots.indexOf(inner) !== -1) continue;
                found = inner.querySelector(selector);
                if (found) return found;
                roots.push(inner);
            }
        }
        return null;
    }

    function queryAll(selector) {
        if (selector.indexOf(DEEP) !== -1) {
            var cut = selector.lastIndexOf(DEEP);
            var host = query(selector.slice(0, cut));
            var scope = host && innerRoot(host);
            return scope ? Array.from(scope.querySelectorAll(selector.slice(cut + DEEP.length))) : [];
        }
        var out = [];
        allRoots().forEach(function (root) { out = out.concat(Array.from(root.querySelectorAll(selector))); });
        return out;
    }

    function cssPath(el) {
        if (!el || el.nodeType !== 1) return "";
        var root = el.getRootNode ? el.getRootNode() : document;
        var local = localPath(el, root);
        var host = root === document ? null : hostOf(root);
        return host ? cssPath(host) + DEEP + local : local;
    }

    function localPath(el, root) {
        if (el.id && root.querySelectorAll("#" + cssEscape(el.id)).length === 1) return "#" + cssEscape(el.id);
        var parts = [];
        var node = el;
        var top = el.ownerDocument.documentElement;
        while (node && node.nodeType === 1 && node !== top && parts.length < 6) {
            var part = node.tagName.toLowerCase();
            var name = node.getAttribute("name");
            if (name) {
                part += "[name=\"" + name.replace(/"/g, "\\\"") + "\"]";
            } else {
                var parent = node.parentElement;
                if (parent) {
                    var same = Array.from(parent.children).filter(function (c) { return c.tagName === node.tagName; });
                    if (same.length > 1) part += ":nth-of-type(" + (same.indexOf(node) + 1) + ")";
                }
            }
            parts.unshift(part);
            if (node.id) { parts[0] = "#" + cssEscape(node.id); break; }
            node = node.parentElement;
        }
        return parts.join(" > ");
    }

    function visible(el) {
        if (!el || el.nodeType !== 1) return false;
        var rect = el.getBoundingClientRect();
        if (!rect.width && !rect.height) return false;
        var style = (el.ownerDocument.defaultView || window).getComputedStyle(el);
        return style.visibility !== "hidden" && style.display !== "none";
    }

    function fieldDescriptor(el) {
        var label = "";
        if (el.id) {
            var scope = el.getRootNode ? el.getRootNode() : document;
            var forLabel = scope.querySelector("label[for=\"" + cssEscape(el.id) + "\"]");
            if (forLabel) label = clean(forLabel.textContent);
        }
        if (!label && el.closest("label")) label = clean(el.closest("label").textContent);
        return [el.getAttribute("type"), el.getAttribute("name"), el.id, el.getAttribute("autocomplete"),
            el.getAttribute("placeholder"), el.getAttribute("aria-label"), label].filter(Boolean).join(" ");
    }

    function isSensitiveField(el) {
        if (!el || !el.matches) return false;
        var type = String(el.getAttribute("type") || "").toLowerCase();
        if (type === "password") return true;
        if (SENSITIVE_AUTOCOMPLETE.test(el.getAttribute("autocomplete") || "")) return true;
        return SENSITIVE_FIELD.test(fieldDescriptor(el));
    }

    function actionLabel(el) {
        var node = el.closest("button, a, input, [role='button'], [role='menuitem'], [role='link']") || el;
        return clean([node.textContent, node.getAttribute("value"), node.getAttribute("aria-label"),
            node.getAttribute("title"), node.getAttribute("name")].filter(Boolean).join(" ")).slice(0, 200);
    }

    function isConsequentialClick(el) {
        var node = el.closest("button, a, input, [role='button'], [role='menuitem']") || el;
        var type = String(node.getAttribute("type") || "").toLowerCase();
        var form = node.form || node.closest("form");
        if ((node.tagName === "BUTTON" && (type === "submit" || (!type && form))) || (node.tagName === "INPUT" && type === "submit")) {
            return "form submission";
        }
        var label = actionLabel(node);
        var match = label.match(RISKY_ACTION);
        if (match) return "\"" + match[0] + "\" action";
        return "";
    }

    function resolve(action) {
        if (action.selector) {
            var el = query(action.selector);
            if (!el) throw new Error("no element matches selector " + action.selector);
            return el;
        }
        if (typeof action.x === "number" && typeof action.y === "number") {
            var hit = document.elementFromPoint(action.x, action.y);
            if (!hit) throw new Error("no element at " + action.x + "," + action.y);
            return hit;
        }
        throw new Error("selector or x/y is required");
    }

    // Rendered text through shadow roots (via their slots) and same-origin iframes.
    function deepText(node, out) {
        if (out.size > MAX_TEXT) return;
        if (node.nodeType === 3) {
            var text = clean(node.nodeValue);
            if (text) { out.parts.push(text); out.size += text.length + 1; }
            return;
        }
        if (node.nodeType === 1) {
            if (/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(node.tagName)) return;
            var view = node.ownerDocument.defaultView;
            if (view && view.getComputedStyle(node).display === "none") return;
            if (node.tagName === "SLOT") {
                var assigned = node.assignedNodes({ flatten: true });
                (assigned.length ? assigned : Array.from(node.childNodes)).forEach(function (c) { deepText(c, out); });
                return;
            }
            var inner = innerRoot(node);
            if (inner) { deepText(inner.body || inner, out); return; }
        }
        Array.from(node.childNodes).forEach(function (c) { deepText(c, out); });
    }

    // Visible label of a control; a web component's label is its rendered (shadow) text.
    function labelOf(el) {
        var text = clean(el.textContent);
        if (!text) {
            var out = { parts: [], size: 0 };
            deepText(el, out);
            text = out.parts.join(" ");
        }
        return clean(text || el.getAttribute("aria-label") || el.getAttribute("placeholder") || "");
    }

    var OUTLINE_MAX = 1500;

    // A compact outline of the composed tree under el (through shadow roots,
    // slots and same-origin iframes): one line per meaningful element.
    function outline(el) {
        var lines = [];
        function own(node) {
            var text = "";
            node.childNodes.forEach(function (c) { if (c.nodeType === 3) text += " " + c.nodeValue; });
            return clean(text).slice(0, 80);
        }
        function walk(node, depth) {
            if (lines.length >= OUTLINE_MAX || node.nodeType !== 1) return;
            if (/^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE|SVG|PATH)$/i.test(node.tagName)) return;
            var view = node.ownerDocument.defaultView;
            if (view && view.getComputedStyle(node).display === "none") return;
            var tag = node.tagName.toLowerCase();
            var role = node.getAttribute("role");
            var label = node.getAttribute("aria-label") || node.getAttribute("title") || "";
            var href = node.getAttribute("href") || "";
            var text = own(node);
            var custom = tag.indexOf("-") !== -1;
            var next = depth;
            if (node.id || role || href || text || label || custom || /^(a|button|input|select|h[1-6]|li|iframe)$/.test(tag)) {
                var line = new Array(depth + 1).join("  ") + tag + (node.id ? "#" + node.id : "") +
                    (role ? "[role=" + role + "]" : "") + (label ? " {" + clean(label).slice(0, 60) + "}" : "") +
                    (text ? " \"" + text + "\"" : "") + (href ? " -> " + href.slice(0, 200) : "");
                lines.push(line);
                next = depth + 1;
            }
            if (tag === "slot") {
                var assigned = node.assignedElements ? node.assignedElements({ flatten: true }) : [];
                (assigned.length ? assigned : Array.from(node.children)).forEach(function (c) { walk(c, next); });
                return;
            }
            var inner = innerRoot(node);
            if (inner) {
                Array.from((inner.body || inner).children).forEach(function (c) { walk(c, next); });
                if (inner.host) return; // light children render through the shadow root's slots
            }
            Array.from(node.children).forEach(function (c) { walk(c, next); });
        }
        walk(el, 0);
        return { lines: lines.join("\n"), truncated: lines.length >= OUTLINE_MAX };
    }

    function pageText(roots) {
        var main = document.querySelector("main, article, [role='main']") || document.body;
        if (!main) return "";
        if (roots.length === 1) return clean(main.innerText).slice(0, MAX_TEXT);
        var out = { parts: [], size: 0 };
        deepText(main, out);
        return out.parts.join("\n").slice(0, MAX_TEXT);
    }

    function inspect() {
        var roots = allRoots();
        var interactive = [];
        var listed = new Set();
        var candidates = [];
        roots.forEach(function (root) { candidates = candidates.concat(Array.from(root.querySelectorAll(INTERACTIVE))); });
        candidates.forEach(function (el) {
            if (interactive.length >= MAX_INTERACTIVE || !visible(el)) return;
            var host = el.getRootNode && hostOf(el.getRootNode());
            if (host && listed.has(host)) return; // the inner button of a listed <x-button>
            listed.add(el);
            var entry = {
                tag: el.tagName.toLowerCase(),
                selector: cssPath(el),
                text: labelOf(el).slice(0, 120)
            };
            if (el.href) entry.href = el.href;
            if (el.matches("input, select, textarea")) {
                entry.type = el.getAttribute("type") || el.tagName.toLowerCase();
                entry.name = el.getAttribute("name") || "";
                entry.sensitive = isSensitiveField(el);
            }
            interactive.push(entry);
        });
        var headings = [];
        roots.forEach(function (root) {
            root.querySelectorAll("h1, h2, h3, [role='heading']").forEach(function (h) {
                var text = clean(h.textContent);
                if (text && headings.length < 40) headings.push(text);
            });
        });
        return {
            url: location.href,
            title: document.title,
            text: pageText(roots),
            headings: headings,
            interactive: interactive
        };
    }

    function extract(action) {
        var nodes = queryAll(action.selector || "body").slice(0, 50);
        return nodes.map(function (el) {
            if (action.attribute) return el.getAttribute(action.attribute);
            if (el.matches("input, textarea, select")) {
                return isSensitiveField(el) ? "[redacted sensitive field]" : el.value;
            }
            return clean(el.innerText || el.textContent).slice(0, MAX_TEXT);
        });
    }

    function sleep(ms) {
        return new Promise(function (r) { setTimeout(r, ms); });
    }

    async function waitFor(action) {
        var timeout = Math.min(Number(action.timeout_ms || 5000), 15000);
        if (!action.selector) { await sleep(timeout); return { waited_ms: timeout }; }
        var started = Date.now();
        while (Date.now() - started < timeout) {
            if (query(action.selector)) return { found: true, waited_ms: Date.now() - started };
            await sleep(400);
        }
        return { found: false, waited_ms: timeout };
    }

    function setNativeValue(el, value) {
        var proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
        var setter = Object.getOwnPropertyDescriptor(proto, "value");
        if (setter && setter.set && el.matches("input, textarea")) setter.set.call(el, value);
        else el.value = value;
    }

    async function runAction(action, approved) {
        switch (action.op) {
        case "inspect":
            if (action.outline) {
                var scope = action.selector ? resolve(action) : document.body;
                return { ok: true, result: Object.assign({ url: location.href, title: document.title }, outline(scope)) };
            }
            return { ok: true, result: inspect() };
        case "extract":
            return { ok: true, result: extract(action) };
        case "wait":
            return { ok: true, result: await waitFor(action) };
        case "scroll": {
            if (action.selector) {
                resolve(action).scrollIntoView({ block: "center" });
            } else {
                window.scrollBy(Number(action.x || 0), Number(action.y || window.innerHeight * 0.8));
            }
            return { ok: true, result: { scrollY: window.scrollY } };
        }
        case "click": {
            var target = resolve(action);
            var risk = isConsequentialClick(target);
            if (risk && !approved) {
                return {
                    approval_required: true,
                    reason: "Paused before a consequential click (" + risk + "): " + actionLabel(target),
                    selector: action.selector || cssPath(target)
                };
            }
            if (target.scrollIntoView) target.scrollIntoView({ block: "center" });
            target.click();
            return { ok: true, result: { clicked: cssPath(target), label: actionLabel(target) } };
        }
        case "type": {
            var field = resolve(action);
            if (isSensitiveField(field)) {
                return { blocked: true, reason: "Refused: credential, payment or identity field (" + fieldDescriptor(field).slice(0, 120) + ")" };
            }
            field.focus();
            if (field.isContentEditable) {
                field.textContent = action.text || "";
            } else {
                setNativeValue(field, action.text || "");
            }
            field.dispatchEvent(new Event("input", { bubbles: true }));
            field.dispatchEvent(new Event("change", { bubbles: true }));
            return { ok: true, result: { typed_into: cssPath(field), length: String(action.text || "").length } };
        }
        default:
            throw new Error("unsupported in-page action: " + action.op);
        }
    }

    browser.runtime.onMessage.addListener(function (message) {
        if (!message || message.type !== "aos-exec") return undefined;
        return runAction(message.action || {}, Boolean(message.approved)).catch(function (error) {
            return { ok: false, error: String(error && error.message || error) };
        });
    });
})();
