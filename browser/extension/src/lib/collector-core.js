/*
 * Agent OS Shopping collector: page reading and human-check detection.
 *
 * Ported from agent-os-shopping's collector userscript (v0.1.5), which this
 * extension replaces. Agent OS Shopping sends recipes of navigate / wait /
 * scroll / extract steps to ONE tab the person chose; this file holds the
 * read-only half that runs in that page. Nothing here clicks, types or
 * submits. Shared by content/collector.js and the Node tests.
 */
(function (root, factory) {
    "use strict";
    if (typeof module === "object" && module.exports) {
        module.exports = factory();
    } else {
        root.AgentOsCollectorCore = factory();
    }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";

    // scroll only moves the page so lazily loaded result grids render.
    var OPS = ["navigate", "wait", "scroll", "extract"];
    var EXTRACT_KINDS = ["jsonld", "next_data", "meta", "tiles", "groups"];
    var CHALLENGE_MARKERS = [
        "captcha", "are you a robot", "robot check", "verify you are human", "press & hold", "press and hold",
        "unusual traffic", "access denied", "request unsuccessful", "bot detection", "enter the characters you see",
        "sorry, we just need to make sure you're not a robot", "powered and protected by"
    ];

    // The command is refused as a whole if any step is not a read-only collector op.
    function validate(actions) {
        if (!Array.isArray(actions) || !actions.length) return "the collector command has no steps";
        for (var i = 0; i < actions.length; i += 1) {
            var action = actions[i] || {};
            if (OPS.indexOf(action.op) === -1) return "unsupported op for the shopping collector: " + action.op;
            if (action.op === "navigate" && !/^https?:\/\//i.test(String(action.url || ""))) {
                return "the collector only opens http(s) pages";
            }
            if (action.op === "extract" && EXTRACT_KINDS.indexOf(action.kind || "jsonld") === -1) {
                return "unsupported extract kind: " + action.kind;
            }
        }
        return "";
    }

    function humanCheckPresent(doc) {
        var body = doc.body ? (doc.body.innerText || doc.body.textContent || "") : "";
        var text = ((doc.title || "") + " " + body.slice(0, 6000)).toLowerCase();
        if (CHALLENGE_MARKERS.some(function (m) { return text.indexOf(m) !== -1; })) return true;
        return Array.from(doc.querySelectorAll("iframe")).some(function (f) { return /captcha|challenge/i.test(f.src || ""); });
    }

    // Field spec: "css", "css@attr", "." (the element itself), ".@lines" (visible text, line breaks as " | ").
    // Alternatives are separated by "|"; every match is checked because pages often hold empty placeholders first.
    function pick(root, spec) {
        var alts = String(spec).split("|").map(function (s) { return s.trim(); }).filter(Boolean);
        for (var a = 0; a < alts.length; a += 1) {
            var alt = alts[a];
            var at = alt.lastIndexOf("@");
            var css = at >= 0 ? alt.slice(0, at).trim() : alt;
            var attr = at >= 0 ? alt.slice(at + 1).trim() : "";
            var nodes;
            try {
                nodes = css && css !== "." ? Array.from(root.querySelectorAll(css)).slice(0, 20) : [root];
            } catch (error) {
                continue;                                    // a bad selector in a recipe must not break the page read
            }
            for (var n = 0; n < nodes.length; n += 1) {
                var node = nodes[n];
                var value = attr === "lines"
                    ? String(node.innerText || node.textContent || "").split("\n")
                        .map(function (l) { return l.trim(); }).filter(Boolean).join(" | ")
                    : attr ? (node.getAttribute(attr) || "") : (node.textContent || "");
                var clean = value.replace(/\s+/g, " ").trim().slice(0, 500);
                if (clean) return clean;
            }
        }
        return "";
    }

    function safeAll(doc, selector) {
        try { return Array.from(doc.querySelectorAll(selector)); } catch (error) { return []; }
    }

    function extract(doc, step) {
        var kind = step.kind || "jsonld";
        var limit = Math.min(Number(step.limit) || 20, 60);
        if (kind === "jsonld") {
            return safeAll(doc, 'script[type="application/ld+json"]').slice(0, 30)
                .map(function (s) { return (s.textContent || "").slice(0, 300000); });
        }
        if (kind === "next_data") {
            var el = doc.getElementById("__NEXT_DATA__");
            return el ? (el.textContent || "").slice(0, 3000000) : "";
        }
        if (kind === "meta") {
            var out = {};
            safeAll(doc, 'meta[property^="og:"], meta[property^="product:"], meta[itemprop]').forEach(function (m) {
                var k = m.getAttribute("property") || m.getAttribute("itemprop");
                if (k && !(k in out)) out[k] = (m.getAttribute("content") || "").slice(0, 500);
            });
            return out;
        }
        var fields = step.fields || {};
        if (kind === "tiles") {
            return safeAll(doc, step.selector || "body").slice(0, limit).map(function (el) {
                var row = {};
                Object.keys(fields).forEach(function (field) { row[field] = pick(el, fields[field]); });
                return row;
            });
        }
        if (kind === "groups") {
            // Grids where one product's parts are sibling cells: start a new group at every child matching "start".
            var rows = [];
            var boxes = safeAll(doc, step.container || "body").slice(0, 20);
            for (var b = 0; b < boxes.length && rows.length < limit; b += 1) {
                var group = null;
                var flush = function () {
                    if (!group || rows.length >= limit) return;
                    var row = {};
                    Object.keys(fields).forEach(function (field) {
                        row[field] = "";
                        for (var g = 0; g < group.length; g += 1) {
                            var v = pick(group[g], fields[field]);
                            if (v) { row[field] = v; break; }
                        }
                    });
                    rows.push(row);
                };
                Array.from(boxes[b].children).slice(0, 400).forEach(function (child) {
                    var isStart = false;
                    try { isStart = child.matches(step.start || "*"); } catch (error) { isStart = false; }
                    if (isStart) { flush(); group = [child]; } else if (group) { group.push(child); }
                });
                flush();
            }
            return rows;
        }
        return null;
    }

    return {
        OPS: OPS,
        EXTRACT_KINDS: EXTRACT_KINDS,
        CHALLENGE_MARKERS: CHALLENGE_MARKERS,
        validate: validate,
        humanCheckPresent: humanCheckPresent,
        pick: pick,
        extract: extract
    };
});
