// ==UserScript==
// @name         Agent OS Universal Capture
// @namespace    agent-os
// @version      3.10.4
// @description  Save useful pages and passively index rendered Discord Web channel and search-result messages into Agent OS.
// @homepageURL   https://github.com/unwit1/universal-capture-plugin
// @updateURL     https://raw.githubusercontent.com/unwit1/universal-capture-plugin/main/agent-os-universal-capture.user.js
// @downloadURL   https://raw.githubusercontent.com/unwit1/universal-capture-plugin/main/agent-os-universal-capture.user.js
// @author       Agent OS
// @match        http://*/*
// @match        https://*/*
// @run-at       document-idle
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_listValues
// @grant        GM_deleteValue
// @grant        GM_registerMenuCommand
// @grant        GM_xmlhttpRequest
// @grant        GM_setClipboard
// @connect      127.0.0.1
// @connect      localhost
// @connect      script.google.com
// @connect      script.googleusercontent.com
// ==/UserScript==

(function () {
    "use strict";

    var VERSION = "3.10.4";
    var SETTINGS_KEY = "agent_os_capture_settings_v1";
    var QUEUE_KEY = "agent_os_capture_queue_v1";
    var MAX_QUEUE = 500;

    var DEFAULT_SETTINGS = {
        endpoint: "",
        token: "",
        device: "",
        defaultIntent: "save",
        showFloatingButton: true,
        discordPassiveIndexing: true,
        browserJournalEnabled: true,
        browserJournalExcludedDomains: [],
        bridgeEnabled: true,
        bridgeEndpoint: "http://127.0.0.1:8766/api/v1/browser/batch",
        bridgeCaptureEndpoint: "http://127.0.0.1:8766/api/v1/browser/capture",
        bridgeToken: "",
        bridgeAutoCompact: true,
        bridgeSyncSeconds: 30
    };

    function loadSettings() {
        var saved = GM_getValue(SETTINGS_KEY, {});
        return Object.assign({}, DEFAULT_SETTINGS, saved && typeof saved === "object" ? saved : {});
    }

    function saveSettings(settings) {
        GM_setValue(SETTINGS_KEY, settings);
    }

    function hostname() {
        return String(location.hostname || "").toLowerCase();
    }

    function cleanText(value) {
        return String(value || "").replace(/\s+/g, " ").trim();
    }

    function meta(name, attr) {
        var selector = attr === "property"
            ? 'meta[property="' + name + '"]'
            : 'meta[name="' + name + '"]';
        var node = document.querySelector(selector);
        return node ? cleanText(node.getAttribute("content")) : "";
    }

    function canonicalUrl() {
        var canonical = document.querySelector('link[rel="canonical"]');
        var value = canonical && canonical.href ? canonical.href : "";
        return value || meta("og:url", "property") || location.href;
    }

    function selectedText() {
        try {
            return cleanText(window.getSelection ? window.getSelection().toString() : "");
        } catch (error) {
            return "";
        }
    }

    function jsonLdObjects() {
        var out = [];
        document.querySelectorAll('script[type="application/ld+json"]').forEach(function (node) {
            try {
                var parsed = JSON.parse(node.textContent || "");
                if (Array.isArray(parsed)) {
                    out = out.concat(parsed);
                } else if (parsed && typeof parsed === "object") {
                    out.push(parsed);
                }
            } catch (error) {
                // A malformed JSON-LD block should never break capture.
            }
        });
        return out;
    }

    function findJsonLdType(typeName) {
        var wanted = String(typeName || "").toLowerCase();
        var stack = jsonLdObjects().slice();
        while (stack.length) {
            var value = stack.shift();
            if (!value || typeof value !== "object") continue;
            var type = value["@type"];
            var types = Array.isArray(type) ? type : [type];
            if (types.some(function (item) { return String(item || "").toLowerCase() === wanted; })) {
                return value;
            }
            if (Array.isArray(value["@graph"])) {
                stack = stack.concat(value["@graph"]);
            }
        }
        return null;
    }

    function genericCapture() {
        return {
            schema_version: "browser-capture-v1",
            source: "browser",
            site: hostname(),
            content_type: "web_page",
            source_id: "",
            title: cleanText(meta("og:title", "property") || document.title),
            author: cleanText(meta("author") || meta("article:author", "property")),
            url: location.href,
            canonical_url: canonicalUrl(),
            description: cleanText(meta("og:description", "property") || meta("description")),
            selected_text: selectedText(),
            image: cleanText(meta("og:image", "property")),
            captured_at: new Date().toISOString(),
            intent: loadSettings().defaultIntent || "save",
            device: loadSettings().device || "",
            metadata: {
                adapter: "generic",
                language: document.documentElement.lang || "",
                referrer: document.referrer || ""
            }
        };
    }

    function redditAdapter(base) {
        var match = location.pathname.match(/\/r\/([^/]+)\/comments\/([^/]+)/i);
        if (!match) return null;

        var post = document.querySelector("shreddit-post");
        var author = post && post.getAttribute ? post.getAttribute("author") : "";
        var title = post && post.getAttribute ? post.getAttribute("post-title") : "";
        if (!title) {
            var h1 = document.querySelector("h1");
            title = h1 ? h1.textContent : base.title;
        }

        base.site = "reddit";
        base.content_type = "reddit_post";
        base.source_id = "reddit:" + match[2];
        base.title = cleanText(title || base.title);
        base.author = cleanText(author || base.author);
        base.metadata = Object.assign({}, base.metadata, {
            adapter: "reddit",
            subreddit: match[1],
            reddit_post_id: match[2]
        });
        return base;
    }

    function amazonAdapter(base) {
        if (hostname().indexOf("amazon.") === -1) return null;
        var asinMatch = location.pathname.match(/\/(?:dp|gp\/product)\/([A-Z0-9]{10})(?:[/?]|$)/i);
        var asinNode = document.querySelector("#ASIN");
        var asin = asinMatch ? asinMatch[1].toUpperCase() : cleanText(asinNode && asinNode.value);
        if (!asin) return null;

        var product = findJsonLdType("Product") || {};
        var titleNode = document.querySelector("#productTitle");
        var priceNode = document.querySelector(".a-price .a-offscreen");
        var sellerNode = document.querySelector("#sellerProfileTriggerId, #merchant-info");
        var imageNode = document.querySelector("#landingImage");

        base.site = "amazon";
        base.content_type = "product";
        base.source_id = "amazon:" + asin;
        base.title = cleanText((titleNode && titleNode.textContent) || product.name || base.title);
        base.description = cleanText(product.description || base.description);
        base.image = cleanText((imageNode && (imageNode.currentSrc || imageNode.src)) || product.image || base.image);
        base.metadata = Object.assign({}, base.metadata, {
            adapter: "amazon",
            asin: asin,
            price_observed: cleanText((priceNode && priceNode.textContent) || ""),
            seller_observed: cleanText((sellerNode && sellerNode.textContent) || ""),
            brand: cleanText(product.brand && (product.brand.name || product.brand)),
            availability: cleanText(product.offers && product.offers.availability),
            sku: cleanText(product.sku)
        });
        return base;
    }

    function youtubeVideoId() {
        if (hostname() === "youtu.be") {
            return location.pathname.split("/").filter(Boolean)[0] || "";
        }
        if (hostname().indexOf("youtube.com") !== -1) {
            return new URL(location.href).searchParams.get("v") || "";
        }
        return "";
    }

    function youtubeAdapter(base) {
        var videoId = youtubeVideoId();
        if (!videoId) return null;

        var titleNode = document.querySelector("h1.ytd-watch-metadata, h1.title");
        var channelNode = document.querySelector("ytd-channel-name a, #owner-name a");
        var video = document.querySelector("video");
        var url = new URL(location.href);

        base.site = "youtube";
        base.content_type = "youtube_video";
        base.source_id = "youtube:" + videoId;
        base.title = cleanText((titleNode && titleNode.textContent) || meta("og:title", "property") || base.title);
        base.author = cleanText((channelNode && channelNode.textContent) || base.author);
        base.metadata = Object.assign({}, base.metadata, {
            adapter: "youtube",
            video_id: videoId,
            channel: base.author,
            playlist_id: url.searchParams.get("list") || "",
            timestamp_seconds: video && Number.isFinite(video.currentTime) ? Math.floor(video.currentTime) : null
        });
        return base;
    }

    function nexusInfoFromUrl(urlText) {
        try {
            var u = new URL(urlText, location.href);
            if (u.hostname.indexOf("nexusmods.com") === -1) return null;
            var match = u.pathname.match(/^\/([^/]+)\/mods\/(\d+)/i);
            if (!match) return null;
            return { game: match[1], mod_id: match[2], url: u.href };
        } catch (error) {
            return null;
        }
    }

    function nexusAdapter(base) {
        var info = nexusInfoFromUrl(location.href);
        if (!info) return null;

        var h1 = document.querySelector("h1");
        var authorLink = document.querySelector('a[href*="/users/"]');
        var version = "";
        document.querySelectorAll("dt, .label, .stat").forEach(function (node) {
            if (version) return;
            if (/version/i.test(node.textContent || "")) {
                var sibling = node.nextElementSibling;
                if (sibling) version = cleanText(sibling.textContent);
            }
        });

        base.site = "nexusmods";
        base.content_type = "nexus_mod";
        base.source_id = "nexus:" + info.game + ":" + info.mod_id;
        base.title = cleanText((h1 && h1.textContent) || base.title);
        base.author = cleanText((authorLink && authorLink.textContent) || base.author);
        base.metadata = Object.assign({}, base.metadata, {
            adapter: "nexus",
            game: info.game,
            mod_id: info.mod_id,
            version: version
        });
        return base;
    }

    function xenforoAdapter(base) {
        var host = hostname();
        var isSpaceBattles = host.indexOf("spacebattles.com") !== -1;
        var isQQ = host.indexOf("questionablequesting.com") !== -1;
        if (!isSpaceBattles && !isQQ) return null;

        var match = location.pathname.match(/\/threads\/[^/]*\.(\d+)/i);
        if (!match) return null;

        var titleNode = document.querySelector("h1.p-title-value");
        var authorNode = document.querySelector(".message-name .username, .p-description a.username");
        var postMatch = location.hash.match(/post-(\d+)/i);
        var site = isSpaceBattles ? "spacebattles" : "questionablequesting";

        base.site = site;
        base.content_type = "xenforo_thread";
        base.source_id = site + ":thread:" + match[1];
        base.title = cleanText((titleNode && titleNode.textContent) || base.title);
        base.author = cleanText((authorNode && authorNode.textContent) || base.author);
        base.metadata = Object.assign({}, base.metadata, {
            adapter: "xenforo",
            forum: site,
            thread_id: match[1],
            post_id: postMatch ? postMatch[1] : "",
            page: new URL(location.href).searchParams.get("page") || ""
        });
        return base;
    }


    // -- Browser interaction journal ------------------------------------------

    var JOURNAL_CHUNK_PREFIX = "agent_os_browser_journal_chunk_v1:";
    var JOURNAL_CHUNK_MAX_EVENTS = 200;
    var JOURNAL_MAX_TEXT = 20000;
    var JOURNAL_EVENT_TYPES = ["view", "session", "text", "copy", "link"];
    var journalSessionId = Date.now().toString(36) + "-" +
        Math.random().toString(36).slice(2, 10);
    var journalChunkSeq = 0;
    var journalEventSeq = 0;
    var journalLastSavedValues = new WeakMap();
    var journalCurrentRoute = location.href;
    var journalCurrentPage = null;
    var journalPageStartedAt = Date.now();
    var journalActiveStartedAt = document.visibilityState === "visible" ? Date.now() : null;
    var journalActiveMs = 0;
    var journalSessionClosed = false;
    var journalRouteTimer = null;

    function journalEnabled() {
        var settings = loadSettings();
        return Boolean(settings.browserJournalEnabled) && !journalDomainExcluded(hostname());
    }

    function journalDomainExcluded(host) {
        var settings = loadSettings();
        var exclusions = Array.isArray(settings.browserJournalExcludedDomains)
            ? settings.browserJournalExcludedDomains
            : [];
        host = String(host || "").toLowerCase();
        return exclusions.some(function (entry) {
            var wanted = String(entry || "").toLowerCase().replace(/^\.+/, "");
            return wanted && (host === wanted || host.endsWith("." + wanted));
        });
    }

    function journalSafeUrl(urlText) {
        try {
            var u = new URL(urlText, location.href);
            if (u.protocol !== "http:" && u.protocol !== "https:") return "";
            return u.origin + u.pathname;
        } catch (error) {
            return "";
        }
    }

    function journalSearchQuery(urlText) {
        if (journalSensitivePage()) return "";
        try {
            var u = new URL(urlText, location.href);
            var keys = ["q", "query", "search", "search_query", "keyword", "keywords", "k", "term"];
            for (var i = 0; i < keys.length; i += 1) {
                var value = u.searchParams.get(keys[i]);
                if (value) {
                    value = String(value).trim().slice(0, 2000);
                    return journalLooksSecret(value, "search query") ? "" : value;
                }
            }
        } catch (error) {
            // Ignore malformed URLs.
        }
        return "";
    }

    function journalPageSnapshot() {
        return {
            raw_url: location.href,
            url: journalSafeUrl(location.href),
            title: cleanText(document.title).slice(0, 500),
            search_query: journalSearchQuery(location.href),
            referrer: journalSafeUrl(document.referrer)
        };
    }

    function journalChunkKey() {
        return JOURNAL_CHUNK_PREFIX + journalSessionId + ":" + journalChunkSeq;
    }

    function journalChunkKeys() {
        try {
            return GM_listValues().filter(function (key) {
                return String(key).indexOf(JOURNAL_CHUNK_PREFIX) === 0;
            });
        } catch (error) {
            console.warn("[Agent OS] Could not enumerate browser journal chunks", error);
            return [];
        }
    }

    function journalAppendRow(row) {
        if (!journalEnabled()) return false;
        if (!row[7]) {
            journalEventSeq += 1;
            row[7] = "journal:" + journalSessionId + ":" + journalEventSeq + ":" + String(row[0] || Date.now());
        }
        var key = journalChunkKey();
        var chunk = GM_getValue(key, []);
        if (!Array.isArray(chunk)) chunk = [];
        if (chunk.length >= JOURNAL_CHUNK_MAX_EVENTS) {
            journalChunkSeq += 1;
            key = journalChunkKey();
            chunk = [];
        }
        chunk.push(row);
        GM_setValue(key, chunk);
        bridgeScheduleSoon(1500);
        return true;
    }

    function journalAllRows() {
        var rows = [];
        journalChunkKeys().forEach(function (key) {
            var chunk = GM_getValue(key, []);
            if (Array.isArray(chunk)) rows = rows.concat(chunk);
        });
        rows.sort(function (a, b) { return Number(a[0] || 0) - Number(b[0] || 0); });
        return rows;
    }

    function journalRowsInDateRange(fromDate, toDate) {
        var bounds = discordDateRangeBounds(fromDate, toDate);
        return journalAllRows().filter(function (row) {
            var ts = Number(row && row[0] || 0);
            if (!ts) return false;
            if (bounds.start != null && ts < bounds.start) return false;
            if (bounds.end != null && ts > bounds.end) return false;
            return true;
        });
    }

    function journalEventCount() {
        var count = 0;
        journalChunkKeys().forEach(function (key) {
            var chunk = GM_getValue(key, []);
            if (Array.isArray(chunk)) count += chunk.length;
        });
        return count;
    }

    function journalSensitiveContext(text) {
        return /(password|passwd|passcode|\bpin\b|otp|one.?time|2fa|mfa|security.?code|verification.?code|cvv|cvc|card.?number|credit.?card|debit.?card|routing.?number|bank.?account|account.?number|social.?security|\bssn\b|tax.?id|api.?key|private.?key|secret|auth.?token|access.?token|refresh.?token)/i.test(String(text || ""));
    }

    function journalLooksSecret(value, context) {
        var text = String(value || "");
        if (!text) return false;
        if (/-----BEGIN [A-Z ]*PRIVATE KEY-----/.test(text)) return true;
        if (/\b(?:github_pat_|gh[pousr]_|sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{20,})/.test(text)) return true;
        if (/\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/.test(text)) return true;
        if (journalSensitiveContext(context)) return true;
        return false;
    }

    function journalSensitivePage() {
        var path = String(location.pathname || "");
        var host = hostname();
        return /(login|log-in|signin|sign-in|oauth|authorize|checkout|payment|billing|security|two-factor|2fa|mfa)/i.test(path) ||
            /^(accounts\.|login\.|auth\.)/.test(host);
    }

    function journalFieldContext(element) {
        if (!element || element.nodeType !== Node.ELEMENT_NODE) return "";
        var parts = [];
        var id = element.id || "";
        if (id) {
            try {
                var label = document.querySelector('label[for="' + CSS.escape(id) + '"]');
                if (label && cleanText(label.textContent)) parts.push(cleanText(label.textContent));
            } catch (error) {
                // Ignore invalid/generated IDs.
            }
        }
        var wrappingLabel = element.closest && element.closest("label");
        if (wrappingLabel && cleanText(wrappingLabel.textContent)) parts.push(cleanText(wrappingLabel.textContent));
        [
            element.getAttribute && element.getAttribute("aria-label"),
            element.getAttribute && element.getAttribute("placeholder"),
            element.getAttribute && element.getAttribute("name"),
            id
        ].forEach(function (value) {
            value = cleanText(value);
            if (value && parts.indexOf(value) === -1) parts.push(value);
        });
        return cleanText(parts.join(" · ")).slice(0, 300);
    }

    function journalIsSensitiveField(element) {
        if (!element || element.nodeType !== Node.ELEMENT_NODE) return true;
        var tag = String(element.tagName || "").toLowerCase();
        var type = String(element.getAttribute && element.getAttribute("type") || "").toLowerCase();
        var autocomplete = String(element.getAttribute && element.getAttribute("autocomplete") || "").toLowerCase();
        var context = journalFieldContext(element);

        if (tag === "input" && ["password", "hidden"].indexOf(type) !== -1) return true;
        if (/(current-password|new-password|one-time-code|webauthn|cc-|transaction-)/i.test(autocomplete)) return true;
        if (journalSensitiveContext(context)) return true;
        return false;
    }

    function journalEligibleTextField(element) {
        if (!element || element.nodeType !== Node.ELEMENT_NODE) return false;
        if (journalIsSensitiveField(element)) return false;
        if (journalSensitivePage()) return false;
        if (element.isContentEditable) return true;

        var tag = String(element.tagName || "").toLowerCase();
        if (tag === "textarea") return true;
        if (tag !== "input") return false;

        var type = String(element.getAttribute("type") || "text").toLowerCase();
        return ["text", "search", "url", "tel", "email"].indexOf(type) !== -1;
    }

    function journalFieldValue(element) {
        if (!journalEligibleTextField(element)) return "";
        var value = element.isContentEditable
            ? String(element.innerText || element.textContent || "")
            : String(element.value || "");
        value = value.replace(/\r\n/g, "\n").trim();
        if (value.length > JOURNAL_MAX_TEXT) value = value.slice(0, JOURNAL_MAX_TEXT);
        return value;
    }

    function journalRecordPageView(snapshot) {
        if (!journalEnabled()) return;
        snapshot = snapshot || journalPageSnapshot();
        if (!snapshot.url) return;
        journalAppendRow([
            Date.now(),
            0,
            snapshot.url,
            snapshot.title || null,
            null,
            null,
            [snapshot.search_query || null, snapshot.referrer || null]
        ]);
    }

    function journalFinalizeField(element, reason) {
        if (!journalEnabled() || !journalEligibleTextField(element)) return;
        var value = journalFieldValue(element);
        if (!value) return;

        var context = journalFieldContext(element);
        if (journalLooksSecret(value, context)) return;

        var previous = journalLastSavedValues.get(element);
        if (previous === value) return;
        journalLastSavedValues.set(element, value);

        var type = element.isContentEditable
            ? "contenteditable"
            : String(element.getAttribute("type") || element.tagName || "text").toLowerCase();

        journalAppendRow([
            Date.now(),
            2,
            journalSafeUrl(location.href),
            null,
            context || null,
            value,
            [type, reason || "finalized"]
        ]);
    }

    function journalRecordCopy() {
        if (!journalEnabled() || journalSensitivePage()) return;
        var text = selectedText();
        if (!text || text.length < 2) return;
        text = text.slice(0, JOURNAL_MAX_TEXT);
        if (journalLooksSecret(text, "copied text")) return;

        journalAppendRow([
            Date.now(),
            3,
            journalSafeUrl(location.href),
            null,
            null,
            text,
            null
        ]);
    }

    function journalRecordLinkClick(event) {
        if (!journalEnabled()) return;
        var target = event.target && event.target.closest ? event.target.closest("a[href]") : null;
        if (!target) return;
        var href = journalSafeUrl(target.href);
        if (!href) return;

        journalAppendRow([
            Date.now(),
            4,
            journalSafeUrl(location.href),
            null,
            null,
            cleanText(target.textContent || target.getAttribute("aria-label") || "").slice(0, 500) || null,
            href
        ]);
    }

    function journalFlushActiveSegment() {
        if (journalActiveStartedAt != null) {
            journalActiveMs += Math.max(0, Date.now() - journalActiveStartedAt);
            journalActiveStartedAt = null;
        }
    }

    function journalClosePageSession(reason) {
        if (journalSessionClosed || !journalCurrentPage) return;
        journalFlushActiveSegment();
        journalSessionClosed = true;
        if (journalEnabled() && journalActiveMs >= 1000) {
            journalAppendRow([
                Date.now(),
                1,
                journalCurrentPage.url,
                null,
                null,
                null,
                [Math.round(journalActiveMs), reason || "closed"]
            ]);
        }
    }

    function journalStartPageSession() {
        journalCurrentPage = journalPageSnapshot();
        journalCurrentRoute = location.href;
        journalPageStartedAt = Date.now();
        journalActiveMs = 0;
        journalActiveStartedAt = document.visibilityState === "visible" ? Date.now() : null;
        journalSessionClosed = false;
        journalRecordPageView(journalCurrentPage);
        updateJournalStatus();
    }

    function journalHandleRouteChange() {
        if (location.href === journalCurrentRoute) return;
        journalFinalizeField(document.activeElement, "route-change");
        journalClosePageSession("route-change");
        journalStartPageSession();
    }

    function toggleBrowserJournal() {
        var settings = loadSettings();
        settings.browserJournalEnabled = !settings.browserJournalEnabled;
        saveSettings(settings);
        if (settings.browserJournalEnabled) journalStartPageSession();
        updateJournalStatus();
        window.alert("Browser journal is now " + (settings.browserJournalEnabled ? "ON." : "OFF."));
    }

    function toggleJournalCurrentDomainExclusion() {
        var settings = loadSettings();
        var exclusions = Array.isArray(settings.browserJournalExcludedDomains)
            ? settings.browserJournalExcludedDomains.slice()
            : [];
        var host = hostname();
        var index = exclusions.findIndex(function (item) {
            return String(item || "").toLowerCase() === host;
        });
        if (index >= 0) {
            exclusions.splice(index, 1);
        } else {
            exclusions.push(host);
        }
        settings.browserJournalExcludedDomains = exclusions;
        saveSettings(settings);
        updateJournalStatus();
        window.alert(
            host + (index >= 0
                ? " is now included in Browser Journal."
                : " is now excluded from Browser Journal.")
        );
    }

    function ensureJournalStatus() {
        if (!document.body) return null;
        var pill = document.getElementById("agent-os-browser-journal-status");
        if (pill) return pill;

        pill = document.createElement("button");
        pill.id = "agent-os-browser-journal-status";
        pill.type = "button";
        pill.style.position = "fixed";
        pill.style.top = isDiscordWeb() ? "176px" : "134px";
        pill.style.right = "20px";
        pill.style.zIndex = "2147483646";
        pill.style.border = "1px solid rgba(255,255,255,.22)";
        pill.style.borderRadius = "8px";
        pill.style.background = "#20242b";
        pill.style.color = "#fff";
        pill.style.font = "600 12px/1.2 system-ui, -apple-system, Segoe UI, sans-serif";
        pill.style.padding = "7px 10px";
        pill.style.cursor = "pointer";
        pill.title = "Browser Journal status";
        pill.addEventListener("click", function () {
            var settings = loadSettings();
            var excluded = journalDomainExcluded(hostname());
            window.alert(
                "Agent OS Browser Journal\n\n" +
                "Journal: " + (settings.browserJournalEnabled ? "ON" : "OFF") + "\n" +
                "Current domain: " + (excluded ? "EXCLUDED" : "included") + "\n" +
                "Buffered events: " + journalEventCount() + "\n\n" +
                "Text is saved only when finalized (blur/change/submit), not key-by-key. " +
                "Password/payment/security-code fields and secret-like values are excluded."
            );
        });
        document.body.appendChild(pill);
        return pill;
    }

    function updateJournalStatus() {
        var pill = ensureJournalStatus();
        if (!pill) return;
        var settings = loadSettings();
        var excluded = journalDomainExcluded(hostname());
        var on = settings.browserJournalEnabled && !excluded;
        pill.textContent = on ? "Journal ●" : "Journal ○";
        pill.style.opacity = on ? "1" : ".6";
        pill.title = excluded
            ? "Browser Journal: current domain excluded"
            : "Browser Journal: " + (settings.browserJournalEnabled ? "ON" : "OFF");
    }

    function journalPromptDateRange(label) {
        var fromDate = window.prompt(
            label + "\n\nFrom date (YYYY-MM-DD). Leave blank for earliest buffered event:",
            ""
        );
        if (fromDate === null) return null;
        var toDate = window.prompt(
            "Through date (YYYY-MM-DD). Leave blank for latest buffered event:",
            ""
        );
        if (toDate === null) return null;

        fromDate = String(fromDate || "").trim();
        toDate = String(toDate || "").trim();
        var valid = /^\d{4}-\d{2}-\d{2}$/;
        if ((fromDate && !valid.test(fromDate)) || (toDate && !valid.test(toDate))) {
            window.alert("Use YYYY-MM-DD date format.");
            return null;
        }
        return { from: fromDate, to: toDate };
    }

    function journalArchiveCompactRows(rows, metadata) {
        var pages = [];
        var pageIndex = new Map();
        var contexts = [];
        var contextIndex = new Map();

        function pageId(url, title) {
            var key = String(url || "");
            if (!key) return -1;
            if (pageIndex.has(key)) {
                var existing = pages[pageIndex.get(key)];
                if (title && !existing[1]) existing[1] = title;
                return pageIndex.get(key);
            }
            var index = pages.length;
            pages.push([key, title || ""]);
            pageIndex.set(key, index);
            return index;
        }

        function contextId(value) {
            value = String(value || "");
            if (!value) return -1;
            if (contextIndex.has(value)) return contextIndex.get(value);
            var index = contexts.length;
            contexts.push(value);
            contextIndex.set(value, index);
            return index;
        }

        rows.forEach(function (row) {
            pageId(row[2], row[3]);
            if (row[1] === 4 && row[6]) pageId(row[6], "");
            if (row[1] === 0 && Array.isArray(row[6]) && row[6][1]) pageId(row[6][1], "");
            if (row[4]) contextId(row[4]);
        });

        var header = {
            v: 1,
            k: "agent-os-browser-journal",
            e: Math.floor(Date.now() / 1000),
            n: rows.length,
            types: JOURNAL_EVENT_TYPES,
            cols: ["t", "e", "p", "c", "x", "z"],
            p: pages,
            c: contexts
        };
        if (metadata && metadata.from_date) header.from = metadata.from_date;
        if (metadata && metadata.to_date) header.to = metadata.to_date;
        if (metadata && metadata.scope) header.scope = metadata.scope;

        var parts = [JSON.stringify(header), "\n"];
        rows.forEach(function (row) {
            var type = Number(row[1] || 0);
            var extra = row[6];
            if (type === 0 && Array.isArray(extra)) {
                extra = [extra[0] || null, extra[1] ? pageId(extra[1], "") : -1];
            } else if (type === 4 && extra) {
                extra = pageId(extra, "");
            }
            parts.push(JSON.stringify([
                Math.floor(Number(row[0] || 0) / 1000),
                type,
                pageId(row[2], row[3]),
                contextId(row[4]),
                row[5] == null ? null : row[5],
                extra == null ? null : extra
            ]), "\n");
        });

        return new Blob(parts, { type: "application/x-ndjson;charset=utf-8" });
    }

    async function exportBrowserJournalRange(fromDate, toDate) {
        var rows = journalRowsInDateRange(fromDate, toDate);
        var source = journalArchiveCompactRows(rows, {
            from_date: fromDate || null,
            to_date: toDate || null,
            scope: "browser_journal"
        });
        var encoded = await discordGzipBlob(source);
        var stamp = new Date().toISOString().replace(/[:.]/g, "-");
        var rangeLabel = (fromDate || "start") + "_to_" + (toDate || "end");
        var filename = "agent-os-browser-journal-" + rangeLabel + "-" + stamp + encoded.extension;
        downloadDiscordBlob(filename, encoded.blob);
        return {
            count: rows.length,
            filename: filename,
            compressed: encoded.compressed,
            raw_bytes: source.size,
            archive_bytes: encoded.blob.size
        };
    }

    async function compactBrowserJournalRange(fromDate, toDate) {
        var bounds = discordDateRangeBounds(fromDate, toDate);
        var removed = 0;

        journalChunkKeys().forEach(function (key) {
            var chunk = GM_getValue(key, []);
            if (!Array.isArray(chunk)) return;
            var kept = chunk.filter(function (row) {
                var ts = Number(row && row[0] || 0);
                var inRange = ts &&
                    (bounds.start == null || ts >= bounds.start) &&
                    (bounds.end == null || ts <= bounds.end);
                if (inRange) removed += 1;
                return !inRange;
            });
            if (!kept.length) GM_deleteValue(key);
            else if (kept.length !== chunk.length) GM_setValue(key, kept);
        });

        updateJournalStatus();
        return removed;
    }

    async function exportBrowserJournalPrompt() {
        var range = journalPromptDateRange("Export Agent OS Browser Journal");
        if (!range) return;
        var result = await exportBrowserJournalRange(range.from, range.to);
        var savings = result.raw_bytes > 0
            ? Math.max(0, Math.round((1 - (result.archive_bytes / result.raw_bytes)) * 100))
            : 0;
        window.alert(
            "Started browser-journal export of " + result.count + " events.\n\n" +
            result.filename + "\n" +
            "Uncompressed JSONL: " + discordHumanBytes(result.raw_bytes) + "\n" +
            "Archive: " + discordHumanBytes(result.archive_bytes) +
            (result.compressed ? " (" + savings + "% smaller)" : " (gzip unavailable)")
        );
    }

    async function compactBrowserJournalPrompt() {
        var range = journalPromptDateRange("Compact an already-exported Browser Journal range");
        if (!range) return;
        if (!window.confirm(
            "Only compact this range after verifying its archive file exists.\n\n" +
            "This removes buffered browser-journal events in the selected range. Continue?"
        )) return;
        var count = await compactBrowserJournalRange(range.from, range.to);
        window.alert("Removed " + count + " archived browser-journal events from local Tampermonkey storage.");
    }

    async function exportCombinedActivityArchivePrompt() {
        if (!isDiscordWeb()) {
            window.alert(
                "Open Discord Web before making a combined archive so this page can access the Discord IndexedDB. " +
                "Browser Journal exports can be made from any website."
            );
            return;
        }

        var range = journalPromptDateRange("Export combined Discord + Browser Journal archive");
        if (!range) return;

        var discordRows = await discordRecordsInDateRange(range.from, range.to);
        var browserRows = journalRowsInDateRange(range.from, range.to);
        var discordBlob = discordArchiveCompactRows(discordRows, {
            from_date: range.from || null,
            to_date: range.to || null,
            scope: "combined_bundle"
        });
        var browserBlob = journalArchiveCompactRows(browserRows, {
            from_date: range.from || null,
            to_date: range.to || null,
            scope: "combined_bundle"
        });

        var bundleHeader = {
            v: 1,
            k: "agent-os-activity-bundle",
            e: Math.floor(Date.now() / 1000),
            from: range.from || null,
            to: range.to || null,
            discord_messages: discordRows.length,
            browser_events: browserRows.length
        };
        var source = new Blob([
            JSON.stringify(bundleHeader), "\n",
            JSON.stringify({ stream: "discord", format: "agent-os-discord-archive-v1" }), "\n",
            discordBlob,
            JSON.stringify({ stream: "browser", format: "agent-os-browser-journal-v1" }), "\n",
            browserBlob
        ], { type: "application/x-ndjson;charset=utf-8" });

        var encoded = await discordGzipBlob(source);
        var stamp = new Date().toISOString().replace(/[:.]/g, "-");
        var rangeLabel = (range.from || "start") + "_to_" + (range.to || "end");
        var filename = "agent-os-activity-" + rangeLabel + "-" + stamp + encoded.extension;
        downloadDiscordBlob(filename, encoded.blob);

        var savings = source.size > 0
            ? Math.max(0, Math.round((1 - (encoded.blob.size / source.size)) * 100))
            : 0;
        window.alert(
            "Started combined archive download.\n\n" +
            "Discord messages: " + discordRows.length + "\n" +
            "Browser events: " + browserRows.length + "\n" +
            filename + "\n" +
            "Uncompressed JSONL: " + discordHumanBytes(source.size) + "\n" +
            "Archive: " + discordHumanBytes(encoded.blob.size) +
            (encoded.compressed ? " (" + savings + "% smaller)" : " (gzip unavailable)") +
            "\n\nVerify the file before compacting either source."
        );
    }

    async function compactCombinedActivityPrompt() {
        if (!isDiscordWeb()) {
            window.alert("Open Discord Web before compacting a combined Discord + browser range.");
            return;
        }
        var range = journalPromptDateRange("Compact an already-exported combined activity range");
        if (!range) return;
        if (!window.confirm(
            "Verify the combined archive exists before continuing.\n\n" +
            "This will compact Discord messages to seen markers and remove browser-journal events in the selected range. Continue?"
        )) return;

        var discordCount = await compactDiscordDateRange(range.from, range.to);
        var browserCount = await compactBrowserJournalRange(range.from, range.to);
        window.alert(
            "Combined compaction complete.\n\n" +
            "Discord messages compacted: " + discordCount + "\n" +
            "Browser events removed from active buffer: " + browserCount
        );
    }

    function clearBrowserJournal() {
        var keys = journalChunkKeys();
        if (!keys.length) {
            window.alert("Browser Journal is already empty.");
            return;
        }
        if (!window.confirm("Clear " + journalEventCount() + " buffered Browser Journal events? This cannot be undone.")) return;
        keys.forEach(function (key) { GM_deleteValue(key); });
        updateJournalStatus();
    }

    function initializeBrowserJournal() {
        ensureJournalStatus();
        journalStartPageSession();

        document.addEventListener("focusout", function (event) {
            journalFinalizeField(event.target, "blur");
        }, true);
        document.addEventListener("change", function (event) {
            journalFinalizeField(event.target, "change");
        }, true);
        document.addEventListener("submit", function (event) {
            var form = event.target;
            if (!form || !form.querySelectorAll) return;
            form.querySelectorAll("input, textarea, [contenteditable='true']").forEach(function (element) {
                journalFinalizeField(element, "submit");
            });
        }, true);
        document.addEventListener("copy", journalRecordCopy, true);
        document.addEventListener("click", journalRecordLinkClick, true);

        document.addEventListener("visibilitychange", function () {
            if (document.visibilityState === "hidden") {
                journalFlushActiveSegment();
            } else if (!journalSessionClosed && journalActiveStartedAt == null) {
                journalActiveStartedAt = Date.now();
            }
        }, true);

        window.addEventListener("pagehide", function () {
            journalFinalizeField(document.activeElement, "pagehide");
            journalClosePageSession("pagehide");
        }, true);

        journalRouteTimer = window.setInterval(journalHandleRouteChange, 1000);
    }


    // -- Discord passive indexing ---------------------------------------------

    var DISCORD_DB_NAME = "agent_os_discord_index_v1";
    var DISCORD_DB_VERSION = 3;
    var DISCORD_STORE = "messages";
    var DISCORD_SEEN_STORE = "seen";
    var discordDbPromise = null;
    var discordSeenFingerprints = new Map();
    var discordSessionNew = 0;
    var discordLastScanAt = 0;
    var discordScanTimer = null;
    var discordPendingRoots = new Set();
    var discordLastObservedUrl = location.href;

    function isDiscordWeb() {
        return hostname() === "discord.com" || hostname() === "www.discord.com";
    }

    function ensureDiscordIndexingDefault() {
        if (!isDiscordWeb()) return;
        var saved = GM_getValue(SETTINGS_KEY, {});
        if (!saved || typeof saved !== "object" ||
                !Object.prototype.hasOwnProperty.call(saved, "discordPassiveIndexing")) {
            var settings = loadSettings();
            settings.discordPassiveIndexing = true;
            saveSettings(settings);
        }
    }

    function discordContext() {
        var match = location.pathname.match(/^\/channels\/([^/]+)\/([^/]+)/);
        if (!match) return null;

        var guildId = match[1];
        var channelId = match[2];
        var header = document.querySelector('[role="main"] h1, main h1, header h1');
        var channelName = cleanText(header && header.textContent);
        var selectedGuild = document.querySelector(
            '[data-list-item-id^="guildsnav___"][aria-selected="true"], ' +
            'nav[aria-label*="Server"] [aria-selected="true"]'
        );
        var guildName = cleanText(
            selectedGuild && (
                selectedGuild.getAttribute("aria-label") ||
                selectedGuild.getAttribute("title") ||
                selectedGuild.textContent
            )
        );

        return {
            guild_id: guildId,
            channel_id: channelId,
            guild_name: guildName,
            channel_name: channelName,
            page_title: cleanText(document.title)
        };
    }

    function openDiscordDb() {
        if (discordDbPromise) return discordDbPromise;
        discordDbPromise = new Promise(function (resolve, reject) {
            var request = indexedDB.open(DISCORD_DB_NAME, DISCORD_DB_VERSION);
            request.onupgradeneeded = function (event) {
                var db = request.result;
                var store;
                if (!db.objectStoreNames.contains(DISCORD_STORE)) {
                    store = db.createObjectStore(DISCORD_STORE, { keyPath: "key" });
                } else {
                    store = request.transaction.objectStore(DISCORD_STORE);
                }
                if (!store.indexNames.contains("channel_key")) {
                    store.createIndex("channel_key", "channel_key", { unique: false });
                }
                if (!store.indexNames.contains("timestamp")) {
                    store.createIndex("timestamp", "timestamp", { unique: false });
                }
                if (!store.indexNames.contains("captured_at")) {
                    store.createIndex("captured_at", "captured_at", { unique: false });
                }

                var seenStore;
                if (!db.objectStoreNames.contains(DISCORD_SEEN_STORE)) {
                    seenStore = db.createObjectStore(DISCORD_SEEN_STORE, { keyPath: "key" });
                } else {
                    seenStore = request.transaction.objectStore(DISCORD_SEEN_STORE);
                }

                // v3 makes archive markers intentionally tiny. The only fact
                // needed to suppress re-indexing is that this canonical key was
                // already archived. Remove obsolete secondary indexes and
                // rewrite older verbose markers to {key} during the upgrade.
                Array.from(seenStore.indexNames).forEach(function (indexName) {
                    seenStore.deleteIndex(indexName);
                });
                if (event.oldVersion < 3) {
                    var cursorRequest = seenStore.openCursor();
                    cursorRequest.onsuccess = function () {
                        var cursor = cursorRequest.result;
                        if (!cursor) return;
                        cursor.update({ key: String(cursor.primaryKey) });
                        cursor.continue();
                    };
                }
            };
            request.onsuccess = function () { resolve(request.result); };
            request.onerror = function () { reject(request.error || new Error("Could not open Discord index")); };
        });
        return discordDbPromise;
    }

    function discordPermalinkIds(node, expectedMessageId) {
        if (!node || node.nodeType !== Node.ELEMENT_NODE) return null;
        var links = node.querySelectorAll('a[href*="/channels/"]');
        for (var i = 0; i < links.length; i += 1) {
            var href = String(links[i].getAttribute("href") || links[i].href || "");
            var match = href.match(/\/channels\/([^/]+)\/([^/]+)\/(\d+)/);
            if (!match) continue;
            if (expectedMessageId && match[3] !== expectedMessageId) continue;
            return {
                guild_id: match[1],
                channel_id: match[2],
                message_id: match[3]
            };
        }
        return null;
    }

    function discordMessageIds(node) {
        if (!node || node.nodeType !== Node.ELEMENT_NODE) return null;

        var content = node.matches && node.matches('[id^="message-content-"]')
            ? node
            : node.querySelector('[id^="message-content-"]');
        var contentMatch = content && String(content.id || "").match(/message-content-(\d+)/);
        var messageId = contentMatch ? contentMatch[1] : "";

        var permalink = discordPermalinkIds(node, messageId || null);
        if (permalink) return permalink;

        var raw = String(
            node.id ||
            node.getAttribute("data-list-item-id") ||
            ""
        );
        var match = raw.match(/chat-messages(?:___|-)(\d+)-(\d+)/);
        var context = discordContext();

        if (match) {
            return {
                guild_id: context ? context.guild_id : "",
                channel_id: match[1],
                message_id: match[2]
            };
        }

        if (!messageId || !context) return null;
        return {
            guild_id: context.guild_id,
            channel_id: context.channel_id,
            message_id: messageId
        };
    }

    function discordAuthor(node, messageId) {
        var selectors = [
            '#message-username-' + CSS.escape(messageId),
            '[id^="message-username-"]',
            '[class*="username"]'
        ];
        for (var i = 0; i < selectors.length; i += 1) {
            var found = node.querySelector(selectors[i]);
            var text = cleanText(found && found.textContent);
            if (text) return text;
        }
        return "";
    }

    function discordMessageText(node, messageId) {
        var content = node.matches && node.matches('#message-content-' + CSS.escape(messageId))
            ? node
            : node.querySelector('#message-content-' + CSS.escape(messageId));
        content = content || (node.matches && node.matches('[id^="message-content-"]')
            ? node
            : node.querySelector('[id^="message-content-"]'));
        return cleanText(content && content.textContent);
    }

    function discordUrls(node) {
        var out = [];
        node.querySelectorAll('a[href]').forEach(function (link) {
            var href = String(link.href || "").trim();
            if (!href || href.indexOf("javascript:") === 0) return;
            if (out.indexOf(href) === -1) out.push(href);
        });
        return out.slice(0, 50);
    }

    function discordAttachments(node) {
        var out = [];
        node.querySelectorAll(
            'a[href*="cdn.discordapp.com"], a[href*="media.discordapp.net"], a[download]'
        ).forEach(function (link) {
            var href = String(link.href || "").trim();
            if (!href) return;
            var label = cleanText(
                link.getAttribute("download") ||
                link.getAttribute("aria-label") ||
                link.textContent
            );
            if (!out.some(function (item) { return item.url === href; })) {
                out.push({ url: href, label: label });
            }
        });
        return out.slice(0, 25);
    }

    function discordReplyTarget(node, messageId) {
        var links = node.querySelectorAll('a[href*="/channels/"]');
        for (var i = 0; i < links.length; i += 1) {
            var match = String(links[i].href || "").match(/\/channels\/[^/]+\/[^/]+\/(\d+)/);
            if (match && match[1] !== messageId) return match[1];
        }
        return "";
    }

    function discordNodeSurface(node, ids, context) {
        var classText = String(node.className || "");
        var searchish = /search/i.test(classText) ||
            Boolean(node.closest && node.closest(
                '[class*="searchResult"], [class*="search-result"], [data-list-item-id*="search"]'
            ));
        if (!searchish && context && ids && ids.channel_id &&
                ids.channel_id !== context.channel_id) {
            searchish = true;
        }
        return searchish ? "search_results" : "channel";
    }

    function discordNodeChannelName(node, context, surface) {
        if (surface === "channel") return context ? context.channel_name : "";
        var candidate = node.querySelector(
            '[class*="channelName"], [class*="channel-name"], ' +
            '[aria-label*="channel"], a[href*="/channels/"]'
        );
        var label = cleanText(candidate && (
            candidate.getAttribute("aria-label") ||
            candidate.getAttribute("title") ||
            candidate.textContent
        ));
        return label || (context ? context.channel_name : "");
    }

    function discordRecord(node, fallbackAuthor) {
        var context = discordContext();
        var ids = discordMessageIds(node);
        if (!ids) return null;

        var messageId = ids.message_id;
        var guildId = ids.guild_id || (context && context.guild_id) || "";
        var channelId = ids.channel_id || (context && context.channel_id) || "";
        if (!guildId || !channelId || !messageId) return null;

        var author = discordAuthor(node, messageId) || fallbackAuthor || "";
        var timeNode = node.querySelector("time[datetime]");
        var timestamp = String(timeNode && timeNode.getAttribute("datetime") || "");
        var text = discordMessageText(node, messageId);
        var urls = discordUrls(node);
        var attachments = discordAttachments(node);

        if (!text && !attachments.length && !urls.length) return null;

        var surface = discordNodeSurface(node, ids, context);
        var messageUrl = "https://discord.com/channels/" +
            encodeURIComponent(guildId) + "/" +
            encodeURIComponent(channelId) + "/" +
            encodeURIComponent(messageId);

        return {
            key: guildId + ":" + channelId + ":" + messageId,
            channel_key: guildId + ":" + channelId,
            schema_version: "discord-message-v1",
            source: "discord-web-rendered",
            source_surface: surface,
            guild_id: guildId,
            guild_name: context ? context.guild_name : "",
            channel_id: channelId,
            channel_name: discordNodeChannelName(node, context, surface),
            message_id: messageId,
            author: author,
            timestamp: timestamp,
            text: text,
            urls: urls,
            attachments: attachments,
            reply_to_message_id: discordReplyTarget(node, messageId),
            message_url: messageUrl,
            page_title: context ? context.page_title : cleanText(document.title),
            captured_at: new Date().toISOString(),
            device: loadSettings().device || ""
        };
    }

    async function discordSeenRecord(key) {
        var db = await openDiscordDb();
        return new Promise(function (resolve, reject) {
            var tx = db.transaction(DISCORD_SEEN_STORE, "readonly");
            var request = tx.objectStore(DISCORD_SEEN_STORE).get(key);
            request.onsuccess = function () { resolve(request.result || null); };
            request.onerror = function () { reject(request.error); };
        });
    }

    function discordRecordTime(record) {
        var raw = record && (record.timestamp || record.captured_at || record.last_captured_at);
        var value = raw ? new Date(raw).getTime() : NaN;
        return Number.isFinite(value) ? value : null;
    }

    function discordDateRangeBounds(fromDate, toDate) {
        var start = null;
        var end = null;
        if (fromDate) {
            var startDate = new Date(fromDate + "T00:00:00");
            if (!Number.isNaN(startDate.getTime())) start = startDate.getTime();
        }
        if (toDate) {
            var endDate = new Date(toDate + "T23:59:59.999");
            if (!Number.isNaN(endDate.getTime())) end = endDate.getTime();
        }
        return { start: start, end: end };
    }

    function discordRecordInRange(record, bounds) {
        var value = discordRecordTime(record);
        if (value == null) return false;
        if (bounds.start != null && value < bounds.start) return false;
        if (bounds.end != null && value > bounds.end) return false;
        return true;
    }

    function discordFingerprint(record) {
        return JSON.stringify([
            record.author,
            record.timestamp,
            record.text,
            record.urls,
            record.attachments,
            record.reply_to_message_id,
            record.source_surface
        ]);
    }

    async function putDiscordRecord(record) {
        var fingerprint = discordFingerprint(record);
        if (discordSeenFingerprints.get(record.key) === fingerprint) return false;

        // Archived messages keep only a tiny "seen" tombstone. If Discord
        // renders one again later, skip rebuilding the full record.
        var archived = await discordSeenRecord(record.key);
        if (archived) {
            discordSeenFingerprints.set(record.key, fingerprint);
            return false;
        }

        discordSeenFingerprints.set(record.key, fingerprint);

        var db = await openDiscordDb();
        return new Promise(function (resolve, reject) {
            var tx = db.transaction(DISCORD_STORE, "readwrite");
            var store = tx.objectStore(DISCORD_STORE);
            var get = store.get(record.key);
            var wasNew = false;

            get.onsuccess = function () {
                var existing = get.result;
                wasNew = !existing;
                var merged = Object.assign({}, existing || {}, record);
                merged.first_captured_at = existing && existing.first_captured_at
                    ? existing.first_captured_at
                    : record.captured_at;
                merged.last_captured_at = record.captured_at;
                store.put(merged);
            };
            get.onerror = function () { reject(get.error || new Error("Discord index read failed")); };
            tx.oncomplete = function () {
                if (wasNew) discordSessionNew += 1;
                updateDiscordStatus();
                resolve(wasNew);
            };
            tx.onerror = function () { reject(tx.error || new Error("Discord index write failed")); };
        });
    }

    async function processDiscordMessageNodes(nodes) {
        if (!isDiscordWeb() || !loadSettings().discordPassiveIndexing) return;
        if (!nodes || !nodes.length) return;

        var fallbackAuthor = "";
        var writes = [];
        nodes.forEach(function (node) {
            var record = discordRecord(node, fallbackAuthor);
            if (!record) return;
            if (record.author) fallbackAuthor = record.author;
            writes.push(
                putDiscordRecord(record).catch(function (error) {
                    console.warn("[Agent OS] Discord index write failed", error);
                    return false;
                })
            );
        });
        if (writes.length) await Promise.all(writes);
        discordLastScanAt = Date.now();
        updateDiscordStatus();
    }

    async function scanDiscordMessages() {
        if (!isDiscordWeb() || !loadSettings().discordPassiveIndexing) return;
        var nodes = discordRenderedMessageNodes();
        if (!nodes.length) return;
        await processDiscordMessageNodes(nodes);
    }

    function discordCollectMessageNodesFromRoot(root) {
        var out = [];
        var seen = new Set();

        function add(node) {
            if (!node || node.nodeType !== Node.ELEMENT_NODE || seen.has(node)) return;
            seen.add(node);
            out.push(node);
        }

        if (!root || root.nodeType !== Node.ELEMENT_NODE) return out;

        if (root.matches(
            '[id^="chat-messages-"], [data-list-item-id^="chat-messages___"], ' +
            '[class*="searchResult"], [class*="search-result"], [role="listitem"]'
        )) {
            var directContent = root.matches('[id^="message-content-"]')
                ? root
                : root.querySelector('[id^="message-content-"]');
            if (directContent) add(root);
        }

        if (root.matches('[id^="message-content-"]')) {
            var directContainer = root.closest(
                '[id^="chat-messages-"], [data-list-item-id^="chat-messages___"], ' +
                '[class*="searchResult"], [class*="search-result"], [role="listitem"]'
            );
            add(directContainer || root);
        }

        root.querySelectorAll(
            '[id^="chat-messages-"], [data-list-item-id^="chat-messages___"]'
        ).forEach(add);

        root.querySelectorAll('[id^="message-content-"]').forEach(function (content) {
            var container = content.closest(
                '[id^="chat-messages-"], [data-list-item-id^="chat-messages___"], ' +
                '[class*="searchResult"], [class*="search-result"], [role="listitem"]'
            );
            add(container || content);
        });

        return out;
    }

    function queueDiscordMutationRoot(root) {
        if (!root || root.nodeType !== Node.ELEMENT_NODE) return;
        discordPendingRoots.add(root);
    }

    function flushDiscordMutationRoots() {
        if (!isDiscordWeb() || !loadSettings().discordPassiveIndexing) {
            discordPendingRoots.clear();
            return;
        }

        var nodes = [];
        var seen = new Set();
        discordPendingRoots.forEach(function (root) {
            discordCollectMessageNodesFromRoot(root).forEach(function (node) {
                if (!seen.has(node)) {
                    seen.add(node);
                    nodes.push(node);
                }
            });
        });
        discordPendingRoots.clear();

        if (nodes.length) {
            processDiscordMessageNodes(nodes).catch(function (error) {
                console.warn("[Agent OS] Discord incremental scan failed", error);
            });
        }
    }

    function scheduleDiscordMutationFlush(delay) {
        if (!isDiscordWeb() || !loadSettings().discordPassiveIndexing) return;
        if (discordScanTimer) window.clearTimeout(discordScanTimer);
        discordScanTimer = window.setTimeout(function () {
            discordScanTimer = null;
            flushDiscordMutationRoots();
        }, typeof delay === "number" ? delay : 120);
    }

    function scheduleDiscordScan(delay) {
        if (!isDiscordWeb() || !loadSettings().discordPassiveIndexing) return;
        window.setTimeout(function () {
            scanDiscordMessages().catch(function (error) {
                console.warn("[Agent OS] Discord passive scan failed", error);
            });
        }, typeof delay === "number" ? delay : 250);
    }

    async function discordIndexStats() {
        var db = await openDiscordDb();
        return new Promise(function (resolve, reject) {
            var tx = db.transaction([DISCORD_STORE, DISCORD_SEEN_STORE], "readonly");
            var activeRequest = tx.objectStore(DISCORD_STORE).count();
            var archivedRequest = tx.objectStore(DISCORD_SEEN_STORE).count();
            tx.oncomplete = function () {
                resolve({
                    total: activeRequest.result || 0,
                    archived: archivedRequest.result || 0,
                    session_new: discordSessionNew
                });
            };
            tx.onerror = function () { reject(tx.error); };
        });
    }

    function ensureDiscordStatus() {
        if (!isDiscordWeb() || !document.body) return null;
        var pill = document.getElementById("agent-os-discord-index-status");
        if (pill) return pill;

        pill = document.createElement("button");
        pill.id = "agent-os-discord-index-status";
        pill.type = "button";
        pill.style.position = "fixed";
        pill.style.top = "134px";
        pill.style.right = "20px";
        pill.style.zIndex = "2147483646";
        pill.style.border = "1px solid rgba(255,255,255,.22)";
        pill.style.borderRadius = "8px";
        pill.style.background = "#20242b";
        pill.style.color = "#fff";
        pill.style.font = "600 12px/1.2 system-ui, -apple-system, Segoe UI, sans-serif";
        pill.style.padding = "7px 10px";
        pill.style.cursor = "pointer";
        pill.title = "Open the local Agent OS Discord index";
        pill.addEventListener("click", function () {
            openDiscordIndexBrowser().catch(function (error) {
                console.warn("[Agent OS] Could not open Discord index browser", error);
                window.alert("Could not open the local Discord index: " + error);
            });
        });
        document.body.appendChild(pill);
        return pill;
    }

    async function updateDiscordStatus() {
        if (!isDiscordWeb()) return;
        var pill = ensureDiscordStatus();
        if (!pill) return;
        try {
            var stats = await discordIndexStats();
            var on = loadSettings().discordPassiveIndexing;
            pill.textContent = (on ? "Discord Index ● " : "Discord Index ○ ") +
                stats.total + (stats.archived ? " · " + stats.archived + " archived" : "");
            pill.style.opacity = on ? "1" : ".65";
        } catch (error) {
            pill.textContent = "Discord Index !";
        }
    }

    async function discordRecordsInDateRange(fromDate, toDate) {
        var bounds = discordDateRangeBounds(fromDate, toDate);
        var rows = await allDiscordRecords(false);
        return rows.filter(function (row) {
            return discordRecordInRange(row, bounds);
        });
    }

    function discordArchiveTimestampSeconds(value) {
        var ms = value ? new Date(value).getTime() : NaN;
        return Number.isFinite(ms) ? Math.floor(ms / 1000) : 0;
    }

    function discordArchiveCompactRows(rows, metadata) {
        var guilds = {};
        var channels = {};
        var authors = [];
        var authorIndex = new Map();

        function authorId(name) {
            var value = String(name || "");
            if (authorIndex.has(value)) return authorIndex.get(value);
            var index = authors.length;
            authors.push(value);
            authorIndex.set(value, index);
            return index;
        }

        rows.forEach(function (row) {
            if (row.guild_id && !Object.prototype.hasOwnProperty.call(guilds, row.guild_id)) {
                guilds[row.guild_id] = row.guild_name || "";
            }
            if (row.channel_id && !Object.prototype.hasOwnProperty.call(channels, row.channel_id)) {
                channels[row.channel_id] = [row.guild_id || "", row.channel_name || ""];
            }
            authorId(row.author || "");
        });

        var header = {
            v: 1,
            k: "agent-os-discord-archive",
            e: Math.floor(Date.now() / 1000),
            n: rows.length,
            cols: ["m", "c", "a", "t", "x", "r", "u", "f", "s"],
            g: guilds,
            c: channels,
            a: authors
        };
        if (metadata && metadata.from_date) header.from = metadata.from_date;
        if (metadata && metadata.to_date) header.to = metadata.to_date;
        if (metadata && metadata.scope) header.scope = metadata.scope;

        var parts = [JSON.stringify(header), "\n"];
        rows.forEach(function (row) {
            var attachmentUrls = new Set((row.attachments || []).map(function (item) {
                return String(item && item.url || "");
            }));
            var selfUrl = String(row.message_url || "");
            var urls = (row.urls || []).filter(function (url) {
                var value = String(url || "");
                return value && value !== selfUrl && !attachmentUrls.has(value);
            });
            var attachments = (row.attachments || []).map(function (item) {
                return [String(item && item.url || ""), String(item && item.label || "")];
            });

            // Row arrays avoid repeating JSON property names millions of times.
            // The header's cols array documents the stable field order.
            var compact = [
                String(row.message_id || ""),
                String(row.channel_id || ""),
                authorId(row.author || ""),
                discordArchiveTimestampSeconds(row.timestamp || row.captured_at),
                String(row.text || ""),
                row.reply_to_message_id ? String(row.reply_to_message_id) : null,
                urls.length ? urls : null,
                attachments.length ? attachments : null,
                row.source_surface === "search_results" ? 1 : 0
            ];
            parts.push(JSON.stringify(compact), "\n");
        });

        return new Blob(parts, { type: "application/x-ndjson;charset=utf-8" });
    }

    async function discordGzipBlob(sourceBlob) {
        if (typeof CompressionStream !== "function") {
            return {
                blob: sourceBlob,
                compressed: false,
                extension: ".jsonl"
            };
        }

        var stream = sourceBlob.stream().pipeThrough(new CompressionStream("gzip"));
        var compressed = await new Response(stream).blob();
        return {
            blob: compressed,
            compressed: true,
            extension: ".jsonl.gz"
        };
    }

    function downloadDiscordBlob(filename, blob) {
        var url = URL.createObjectURL(blob);
        var link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.setTimeout(function () { URL.revokeObjectURL(url); }, 5000);
    }

    async function downloadDiscordCompactArchive(rows, baseName, metadata) {
        var source = discordArchiveCompactRows(rows, metadata || {});
        var encoded = await discordGzipBlob(source);
        var filename = baseName + encoded.extension;
        downloadDiscordBlob(filename, encoded.blob);
        return {
            count: rows.length,
            filename: filename,
            compressed: encoded.compressed,
            raw_bytes: source.size,
            archive_bytes: encoded.blob.size
        };
    }

    function discordHumanBytes(bytes) {
        var value = Number(bytes || 0);
        if (value < 1024) return value + " B";
        if (value < 1024 * 1024) return (value / 1024).toFixed(1) + " KB";
        if (value < 1024 * 1024 * 1024) return (value / (1024 * 1024)).toFixed(1) + " MB";
        return (value / (1024 * 1024 * 1024)).toFixed(2) + " GB";
    }

    async function exportDiscordDateRange(fromDate, toDate) {
        var rows = await discordRecordsInDateRange(fromDate, toDate);
        var stamp = new Date().toISOString().replace(/[:.]/g, "-");
        var rangeLabel = (fromDate || "start") + "_to_" + (toDate || "end");
        return downloadDiscordCompactArchive(
            rows,
            "agent-os-discord-archive-" + rangeLabel + "-" + stamp,
            {
                from_date: fromDate || null,
                to_date: toDate || null,
                scope: "date_range"
            }
        );
    }

    async function compactDiscordDateRange(fromDate, toDate) {
        var rows = await discordRecordsInDateRange(fromDate, toDate);
        if (!rows.length) return 0;

        var db = await openDiscordDb();
        await new Promise(function (resolve, reject) {
            var tx = db.transaction([DISCORD_STORE, DISCORD_SEEN_STORE], "readwrite");
            var messages = tx.objectStore(DISCORD_STORE);
            var seen = tx.objectStore(DISCORD_SEEN_STORE);
            rows.forEach(function (row) {
                seen.put({ key: row.key });
                messages.delete(row.key);
                discordSeenFingerprints.delete(row.key);
            });

            tx.oncomplete = resolve;
            tx.onerror = function () { reject(tx.error || new Error("Discord compaction failed")); };
        });

        updateDiscordStatus();
        return rows.length;
    }

    async function clearDiscordArchiveMarkers() {
        if (!window.confirm(
            "Clear all Discord archive markers? Previously compacted messages can be indexed again if Discord renders them."
        )) return;

        var db = await openDiscordDb();
        await new Promise(function (resolve, reject) {
            var tx = db.transaction(DISCORD_SEEN_STORE, "readwrite");
            tx.objectStore(DISCORD_SEEN_STORE).clear();
            tx.oncomplete = resolve;
            tx.onerror = function () { reject(tx.error); };
        });
        updateDiscordStatus();
    }

    function closeDiscordIndexBrowser() {
        var existing = document.getElementById("agent-os-discord-index-browser");
        if (existing) existing.remove();
    }

    function escapeDiscordIndexHtml(value) {
        return String(value == null ? "" : value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    async function openDiscordIndexBrowser() {
        closeDiscordIndexBrowser();

        var rows = await allDiscordRecords(false);
        var settings = loadSettings();
        var overlay = document.createElement("div");
        overlay.id = "agent-os-discord-index-browser";
        overlay.style.position = "fixed";
        overlay.style.inset = "0";
        overlay.style.zIndex = "2147483647";
        overlay.style.background = "rgba(0,0,0,.72)";
        overlay.style.display = "flex";
        overlay.style.alignItems = "center";
        overlay.style.justifyContent = "center";
        overlay.style.padding = "24px";

        var panel = document.createElement("div");
        panel.style.width = "min(1100px, 96vw)";
        panel.style.height = "min(780px, 92vh)";
        panel.style.background = "#111318";
        panel.style.color = "#f5f5f5";
        panel.style.border = "1px solid rgba(255,255,255,.18)";
        panel.style.borderRadius = "12px";
        panel.style.boxShadow = "0 24px 80px rgba(0,0,0,.55)";
        panel.style.display = "flex";
        panel.style.flexDirection = "column";
        panel.style.font = "13px/1.45 system-ui, -apple-system, Segoe UI, sans-serif";
        panel.style.overflow = "hidden";

        var header = document.createElement("div");
        header.style.padding = "16px";
        header.style.borderBottom = "1px solid rgba(255,255,255,.12)";
        header.innerHTML =
            '<div style="display:flex;justify-content:space-between;gap:16px;align-items:center">' +
            '<div><div style="font-size:18px;font-weight:800">Agent OS Discord Index</div>' +
            '<div style="opacity:.72;margin-top:3px">Browser IndexedDB → ' +
            escapeDiscordIndexHtml(DISCORD_DB_NAME) + ' → ' +
            escapeDiscordIndexHtml(DISCORD_STORE) +
            ' · ' + rows.length + ' active messages · passive indexing ' +
            (settings.discordPassiveIndexing ? "ON" : "OFF") +
            '</div></div>' +
            '<button id="agent-os-discord-index-close" style="padding:8px 11px;border-radius:8px;border:1px solid rgba(255,255,255,.2);background:#20242b;color:#fff;cursor:pointer">Close</button>' +
            '</div>' +
            '<div style="margin-top:10px;opacity:.7">IndexedDB is browser-managed storage, not a normal filesystem folder. This viewer is the direct browser for those local records.</div>';

        var controls = document.createElement("div");
        controls.style.padding = "12px 16px";
        controls.style.display = "flex";
        controls.style.gap = "8px";
        controls.style.flexWrap = "wrap";
        controls.style.borderBottom = "1px solid rgba(255,255,255,.1)";
        controls.innerHTML =
            '<input id="agent-os-discord-index-filter" placeholder="Filter author, channel, message text…" ' +
            'style="flex:1;min-width:260px;padding:9px;border-radius:8px;border:1px solid rgba(255,255,255,.16);background:#181b22;color:#fff">' +
            '<button id="agent-os-discord-export-channel" style="padding:8px 11px;border-radius:8px;border:1px solid rgba(255,255,255,.2);background:#20242b;color:#fff;cursor:pointer">Export current channel (.jsonl.gz)</button>' +
            '<button id="agent-os-discord-export-all" style="padding:8px 11px;border-radius:8px;border:1px solid rgba(255,255,255,.2);background:#20242b;color:#fff;cursor:pointer">Export all (.jsonl.gz)</button>' +
            '<input id="agent-os-discord-archive-from" type="date" title="Archive from date" style="padding:8px;border-radius:8px;border:1px solid rgba(255,255,255,.16);background:#181b22;color:#fff">' +
            '<input id="agent-os-discord-archive-to" type="date" title="Archive through date" style="padding:8px;border-radius:8px;border:1px solid rgba(255,255,255,.16);background:#181b22;color:#fff">' +
            '<button id="agent-os-discord-export-range" style="padding:8px 11px;border-radius:8px;border:1px solid rgba(255,255,255,.2);background:#20242b;color:#fff;cursor:pointer">Export range (.jsonl.gz)</button>' +
            '<button id="agent-os-discord-compact-range" style="padding:8px 11px;border-radius:8px;border:1px solid rgba(255,255,255,.2);background:#5b2a2a;color:#fff;cursor:pointer">Compact exported range</button>';

        var body = document.createElement("div");
        body.id = "agent-os-discord-index-list";
        body.style.flex = "1";
        body.style.overflow = "auto";
        body.style.padding = "10px 16px 20px";

        panel.appendChild(header);
        panel.appendChild(controls);
        panel.appendChild(body);
        overlay.appendChild(panel);
        document.body.appendChild(overlay);

        var ordered = rows.slice().sort(function (a, b) {
            return String(b.timestamp || b.captured_at).localeCompare(String(a.timestamp || a.captured_at));
        });

        function render(filterText) {
            var needle = cleanText(filterText).toLowerCase();
            var matching = ordered.filter(function (row) {
                if (!needle) return true;
                return [
                    row.author,
                    row.channel_name,
                    row.channel_id,
                    row.guild_name,
                    row.text,
                    row.source_surface
                ].some(function (value) {
                    return String(value || "").toLowerCase().indexOf(needle) !== -1;
                });
            });
            var visible = matching.slice(0, 300);
            body.innerHTML =
                '<div style="opacity:.65;margin:4px 0 10px">Showing ' +
                visible.length + ' of ' + matching.length +
                ' matching records (newest first; viewer caps rendering at 300).</div>' +
                visible.map(function (row) {
                    var when = row.timestamp || row.captured_at || "";
                    var channel = row.channel_name || row.channel_id || "unknown channel";
                    var surface = row.source_surface === "search_results" ? " · SEARCH" : "";
                    return '<div style="padding:10px 0;border-top:1px solid rgba(255,255,255,.08)">' +
                        '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:baseline">' +
                        '<strong>' + escapeDiscordIndexHtml(row.author || "Unknown author") + '</strong>' +
                        '<span style="opacity:.65">#' + escapeDiscordIndexHtml(channel) +
                        escapeDiscordIndexHtml(surface) + '</span>' +
                        '<span style="opacity:.5;margin-left:auto">' + escapeDiscordIndexHtml(when) + '</span>' +
                        '</div>' +
                        '<div style="white-space:pre-wrap;margin-top:5px">' + escapeDiscordIndexHtml(row.text || "") + '</div>' +
                        '<div style="margin-top:5px"><a href="' + escapeDiscordIndexHtml(row.message_url || "#") +
                        '" target="_blank" rel="noreferrer" style="color:#7ab7ff">Open message</a></div>' +
                        '</div>';
                }).join("");
        }

        render("");

        document.getElementById("agent-os-discord-index-close").addEventListener("click", closeDiscordIndexBrowser);
        document.getElementById("agent-os-discord-index-filter").addEventListener("input", function (event) {
            render(event.target.value);
        });
        document.getElementById("agent-os-discord-export-channel").addEventListener("click", function () {
            exportDiscordIndex(true);
        });
        document.getElementById("agent-os-discord-export-all").addEventListener("click", function () {
            exportDiscordIndex(false);
        });
        document.getElementById("agent-os-discord-export-range").addEventListener("click", async function () {
            var fromDate = document.getElementById("agent-os-discord-archive-from").value;
            var toDate = document.getElementById("agent-os-discord-archive-to").value;
            if (!fromDate && !toDate) {
                window.alert("Choose at least a From or Through date for the archive range.");
                return;
            }
            var result = await exportDiscordDateRange(fromDate, toDate);
            var savings = result.raw_bytes > 0
                ? Math.max(0, Math.round((1 - (result.archive_bytes / result.raw_bytes)) * 100))
                : 0;
            window.alert(
                "Started archive download of " + result.count + " indexed Discord messages.\n\n" +
                result.filename + "\n" +
                "Uncompressed JSONL: " + discordHumanBytes(result.raw_bytes) + "\n" +
                "Archive: " + discordHumanBytes(result.archive_bytes) +
                (result.compressed ? " (" + savings + "% smaller)" : " (gzip unavailable; plain JSONL fallback)") +
                "\n\nAfter you verify the archive exists in Downloads, use Compact exported range to remove full message bodies from IndexedDB while keeping tiny seen markers."
            );
        });
        document.getElementById("agent-os-discord-compact-range").addEventListener("click", async function () {
            var fromDate = document.getElementById("agent-os-discord-archive-from").value;
            var toDate = document.getElementById("agent-os-discord-archive-to").value;
            if (!fromDate && !toDate) {
                window.alert("Choose the same exported From/Through date range before compacting.");
                return;
            }
            if (!window.confirm(
                "Only compact this range after you verified its JSON export exists.\n\n" +
                "Compaction deletes full local message bodies for this range and keeps only tiny message-key markers so they will not be indexed again. Continue?"
            )) return;
            var count = await compactDiscordDateRange(fromDate, toDate);
            window.alert("Compacted " + count + " Discord messages. Minimal seen markers remain so they will not be re-indexed.");
            closeDiscordIndexBrowser();
            openDiscordIndexBrowser();
        });
        overlay.addEventListener("click", function (event) {
            if (event.target === overlay) closeDiscordIndexBrowser();
        });
    }

    async function allDiscordRecords(currentChannelOnly) {
        var db = await openDiscordDb();
        var context = discordContext();
        return new Promise(function (resolve, reject) {
            var tx = db.transaction(DISCORD_STORE, "readonly");
            var store = tx.objectStore(DISCORD_STORE);
            var request;
            if (currentChannelOnly && context) {
                request = store.index("channel_key").getAll(context.guild_id + ":" + context.channel_id);
            } else {
                request = store.getAll();
            }
            request.onsuccess = function () {
                var rows = request.result || [];
                rows.sort(function (a, b) {
                    return String(a.timestamp || a.captured_at).localeCompare(String(b.timestamp || b.captured_at));
                });
                resolve(rows);
            };
            request.onerror = function () { reject(request.error); };
        });
    }

    async function exportDiscordIndex(currentChannelOnly) {
        if (!isDiscordWeb()) {
            window.alert("Open Discord Web before exporting the Discord index.");
            return;
        }
        var rows = await allDiscordRecords(Boolean(currentChannelOnly));
        var context = discordContext();
        var suffix = currentChannelOnly && context ? "-" + context.channel_id : "-all";
        var stamp = new Date().toISOString().replace(/[:.]/g, "-");
        var result = await downloadDiscordCompactArchive(
            rows,
            "agent-os-discord-index" + suffix + "-" + stamp,
            { scope: currentChannelOnly ? "current_channel" : "all_active" }
        );
        var savings = result.raw_bytes > 0
            ? Math.max(0, Math.round((1 - (result.archive_bytes / result.raw_bytes)) * 100))
            : 0;
        window.alert(
            "Started export of " + result.count + " messages.\n\n" +
            result.filename + "\n" +
            "Uncompressed JSONL: " + discordHumanBytes(result.raw_bytes) + "\n" +
            "Archive: " + discordHumanBytes(result.archive_bytes) +
            (result.compressed ? " (" + savings + "% smaller)" : " (gzip unavailable; plain JSONL fallback)")
        );
    }

    async function clearDiscordIndex() {
        if (!window.confirm("Clear the entire local Agent OS Discord message index and archive markers on this browser?")) return;
        var db = await openDiscordDb();
        await new Promise(function (resolve, reject) {
            var tx = db.transaction([DISCORD_STORE, DISCORD_SEEN_STORE], "readwrite");
            tx.objectStore(DISCORD_STORE).clear();
            tx.objectStore(DISCORD_SEEN_STORE).clear();
            tx.oncomplete = resolve;
            tx.onerror = function () { reject(tx.error); };
        });
        discordSeenFingerprints.clear();
        discordSessionNew = 0;
        updateDiscordStatus();
    }

    function toggleDiscordPassiveIndexing() {
        var settings = loadSettings();
        settings.discordPassiveIndexing = !settings.discordPassiveIndexing;
        saveSettings(settings);
        updateDiscordStatus();
        if (settings.discordPassiveIndexing) scheduleDiscordScan(0);
        window.alert("Discord passive indexing is now " + (settings.discordPassiveIndexing ? "ON." : "OFF."));
    }


    // -- Durable local Agent OS bridge ----------------------------------------

    var BRIDGE_BATCH_MAX = 100;
    var bridgeSyncTimer = null;
    var bridgeSyncInterval = null;
    var bridgeSyncInFlight = false;
    var bridgeLastStatus = {
        state: "idle",
        at: null,
        acknowledged: 0,
        error: ""
    };

    function bridgeConfigured() {
        var settings = loadSettings();
        return Boolean(
            settings.bridgeEnabled &&
            settings.bridgeEndpoint &&
            settings.bridgeToken
        );
    }

    function bridgeStableHash(value) {
        var text = String(value || "");
        var h1 = 0x811c9dc5;
        var h2 = 0x9e3779b9;
        for (var i = 0; i < text.length; i += 1) {
            var code = text.charCodeAt(i);
            h1 = Math.imul(h1 ^ code, 0x01000193);
            h2 = Math.imul(h2 ^ code, 0x85ebca6b);
        }
        return (h1 >>> 0).toString(16).padStart(8, "0") +
            (h2 >>> 0).toString(16).padStart(8, "0");
    }

    function journalRowEventId(row) {
        if (row && row[7]) return String(row[7]);
        return "journal:legacy:" + bridgeStableHash(JSON.stringify((row || []).slice(0, 7)));
    }

    function bridgeJournalEvent(row) {
        var typeIndex = Number(row && row[1] || 0);
        var timestamp = Number(row && row[0] || 0);
        return {
            event_id: journalRowEventId(row),
            source: "browser-journal",
            event_type: JOURNAL_EVENT_TYPES[typeIndex] || "event",
            source_key: String(row && row[2] || ""),
            occurred_at: timestamp ? new Date(timestamp).toISOString() : "",
            device: loadSettings().device || "",
            payload: {
                timestamp_ms: timestamp || null,
                event_type: JOURNAL_EVENT_TYPES[typeIndex] || "event",
                url: row && row[2] || "",
                title: row && row[3] || null,
                context: row && row[4] || null,
                text: row && row[5] == null ? null : row[5],
                extra: row && row[6] == null ? null : row[6]
            }
        };
    }

    function bridgeDiscordEvent(record) {
        return {
            event_id: "discord:" + String(record.key || ""),
            source: "discord",
            event_type: "message",
            source_key: String(record.key || ""),
            occurred_at: record.timestamp || record.captured_at || "",
            device: loadSettings().device || "",
            payload: record
        };
    }

    function removeAcknowledgedJournalRows(acknowledged) {
        if (!acknowledged || !acknowledged.size) return 0;
        var removed = 0;
        journalChunkKeys().forEach(function (key) {
            var chunk = GM_getValue(key, []);
            if (!Array.isArray(chunk)) return;
            var kept = chunk.filter(function (row) {
                var remove = acknowledged.has(journalRowEventId(row));
                if (remove) removed += 1;
                return !remove;
            });
            if (!kept.length) GM_deleteValue(key);
            else if (kept.length !== chunk.length) GM_setValue(key, kept);
        });
        updateJournalStatus();
        return removed;
    }

    async function discordBridgeRecords(limit) {
        if (!isDiscordWeb()) return [];
        var db = await openDiscordDb();
        return new Promise(function (resolve, reject) {
            var tx = db.transaction(DISCORD_STORE, "readonly");
            var store = tx.objectStore(DISCORD_STORE);
            var index = store.index("captured_at");
            var request = index.openCursor();
            var rows = [];
            request.onsuccess = function () {
                var cursor = request.result;
                if (!cursor || rows.length >= limit) {
                    resolve(rows);
                    return;
                }
                rows.push(cursor.value);
                cursor.continue();
            };
            request.onerror = function () {
                reject(request.error || new Error("Could not read Discord bridge batch"));
            };
        });
    }

    async function compactAcknowledgedDiscord(acknowledged, sentFingerprints) {
        if (!isDiscordWeb() || !acknowledged || !acknowledged.size) return 0;
        var keys = [];
        acknowledged.forEach(function (eventId) {
            if (String(eventId).indexOf("discord:") === 0) {
                keys.push(String(eventId).slice("discord:".length));
            }
        });
        if (!keys.length) return 0;

        var db = await openDiscordDb();
        return new Promise(function (resolve, reject) {
            var tx = db.transaction([DISCORD_STORE, DISCORD_SEEN_STORE], "readwrite");
            var messages = tx.objectStore(DISCORD_STORE);
            var seen = tx.objectStore(DISCORD_SEEN_STORE);
            var compacted = 0;

            keys.forEach(function (key) {
                var get = messages.get(key);
                get.onsuccess = function () {
                    var current = get.result;
                    if (!current) return;
                    var eventId = "discord:" + key;
                    var sentFingerprint = sentFingerprints.get(eventId);
                    if (sentFingerprint && discordFingerprint(current) !== sentFingerprint) {
                        return;
                    }
                    seen.put({ key: key });
                    messages.delete(key);
                    discordSeenFingerprints.delete(key);
                    compacted += 1;
                };
            });

            tx.oncomplete = function () {
                updateDiscordStatus();
                resolve(compacted);
            };
            tx.onerror = function () {
                reject(tx.error || new Error("Could not compact bridge-acknowledged Discord messages"));
            };
        });
    }

    function bridgeScheduleSoon(delay) {
        if (!bridgeConfigured()) return;
        if (bridgeSyncTimer) window.clearTimeout(bridgeSyncTimer);
        bridgeSyncTimer = window.setTimeout(function () {
            bridgeSyncTimer = null;
            bridgeSyncNow(false);
        }, typeof delay === "number" ? delay : 2000);
    }

    async function bridgeBuildBatch() {
        var journalRows = journalAllRows().slice(0, Math.floor(BRIDGE_BATCH_MAX / 2));
        var discordRows = isDiscordWeb()
            ? await discordBridgeRecords(BRIDGE_BATCH_MAX - journalRows.length)
            : [];

        // Give Discord a fair share even when the journal backlog is large.
        if (isDiscordWeb() && journalRows.length >= BRIDGE_BATCH_MAX / 2 &&
                discordRows.length < BRIDGE_BATCH_MAX / 2) {
            journalRows = journalRows.slice(
                0,
                BRIDGE_BATCH_MAX - discordRows.length
            );
        }

        var events = journalRows.map(bridgeJournalEvent);
        var sentFingerprints = new Map();
        discordRows.forEach(function (record) {
            var event = bridgeDiscordEvent(record);
            events.push(event);
            sentFingerprints.set(event.event_id, discordFingerprint(record));
        });

        return {
            events: events.slice(0, BRIDGE_BATCH_MAX),
            sentFingerprints: sentFingerprints
        };
    }

    function bridgeRequest(body) {
        var settings = loadSettings();
        return new Promise(function (resolve, reject) {
            GM_xmlhttpRequest({
                method: "POST",
                url: settings.bridgeEndpoint,
                headers: {
                    "Content-Type": "application/json",
                    "X-Agent-OS-Token": settings.bridgeToken
                },
                data: JSON.stringify(body),
                timeout: 15000,
                onload: function (response) {
                    if (!(response.status >= 200 && response.status < 300)) {
                        reject(new Error("HTTP " + response.status));
                        return;
                    }
                    try {
                        resolve(JSON.parse(response.responseText || "{}"));
                    } catch (error) {
                        reject(new Error("Bridge returned invalid JSON"));
                    }
                },
                onerror: function () { reject(new Error("Bridge unavailable")); },
                ontimeout: function () { reject(new Error("Bridge timeout")); }
            });
        });
    }

    async function bridgeSyncNow(showResult) {
        if (!bridgeConfigured()) {
            if (showResult) {
                window.alert(
                    "Local Agent OS bridge is not configured.\n\n" +
                    "Start it with: agent-os browser-bridge\n" +
                    "Then use the Tampermonkey menu: Agent OS: Configure local bridge."
                );
            }
            return { acknowledged: 0 };
        }
        if (bridgeSyncInFlight) {
            if (showResult) window.alert("A bridge sync is already running.");
            return { acknowledged: 0 };
        }

        bridgeSyncInFlight = true;
        bridgeLastStatus = {
            state: "syncing",
            at: new Date().toISOString(),
            acknowledged: 0,
            error: ""
        };
        try {
            var batch = await bridgeBuildBatch();
            if (!batch.events.length) {
                bridgeLastStatus = {
                    state: "idle",
                    at: new Date().toISOString(),
                    acknowledged: 0,
                    error: ""
                };
                if (showResult) window.alert("Bridge is connected. Nothing is waiting to sync.");
                return { acknowledged: 0 };
            }

            var settings = loadSettings();
            var response = await bridgeRequest({
                schema: "agent-os/browser-bridge-batch/v1",
                batch_id: "browser-" + Date.now().toString(36) + "-" +
                    Math.random().toString(36).slice(2, 8),
                device: settings.device || "",
                events: batch.events
            });
            if (!response || response.durable !== true || !Array.isArray(response.acknowledged)) {
                throw new Error("Bridge did not return a durable acknowledgement");
            }

            var acknowledged = new Set(response.acknowledged.map(String));
            var journalAcknowledged = new Set(
                Array.from(acknowledged).filter(function (id) {
                    return id.indexOf("journal:") === 0;
                })
            );
            var journalRemoved = removeAcknowledgedJournalRows(journalAcknowledged);
            var discordCompacted = 0;
            if (settings.bridgeAutoCompact) {
                discordCompacted = await compactAcknowledgedDiscord(
                    acknowledged,
                    batch.sentFingerprints
                );
            }

            bridgeLastStatus = {
                state: "ok",
                at: new Date().toISOString(),
                acknowledged: acknowledged.size,
                journal_removed: journalRemoved,
                discord_compacted: discordCompacted,
                error: ""
            };

            if (showResult) {
                window.alert(
                    "Agent OS bridge sync complete.\n\n" +
                    "Durably acknowledged: " + acknowledged.size + "\n" +
                    "Browser journal compacted: " + journalRemoved + "\n" +
                    "Discord messages compacted: " + discordCompacted
                );
            }

            if (journalEventCount() > 0 || (isDiscordWeb() && discordCompacted > 0)) {
                bridgeScheduleSoon(2000);
            }
            return bridgeLastStatus;
        } catch (error) {
            bridgeLastStatus = {
                state: "error",
                at: new Date().toISOString(),
                acknowledged: 0,
                error: String(error && error.message || error)
            };
            if (showResult) {
                window.alert(
                    "Agent OS bridge sync failed. Browser data was kept locally.\n\n" +
                    bridgeLastStatus.error
                );
            }
            return bridgeLastStatus;
        } finally {
            bridgeSyncInFlight = false;
        }
    }

    function configureLocalBridge() {
        var settings = loadSettings();
        var endpoint = window.prompt(
            "Agent OS local bridge batch endpoint:",
            settings.bridgeEndpoint || "http://127.0.0.1:8766/api/v1/browser/batch"
        );
        if (endpoint === null) return;
        endpoint = endpoint.trim();

        var token = window.prompt(
            "Agent OS local bridge token.\n\n" +
            "Run 'agent-os browser-bridge-token' or start 'agent-os browser-bridge' to display it.",
            settings.bridgeToken || ""
        );
        if (token === null) return;

        settings.bridgeEndpoint = endpoint;
        settings.bridgeCaptureEndpoint = endpoint.replace(/\/batch(?:\?.*)?$/, "/capture");
        settings.bridgeToken = token.trim();
        settings.bridgeEnabled = Boolean(endpoint && settings.bridgeToken);
        saveSettings(settings);
        initializeBridgeSync();
        bridgeScheduleSoon(200);
        window.alert(
            settings.bridgeEnabled
                ? "Local Agent OS bridge configured. Automatic durable sync is ON."
                : "Bridge configuration is incomplete; automatic sync is OFF."
        );
    }

    function toggleLocalBridge() {
        var settings = loadSettings();
        settings.bridgeEnabled = !settings.bridgeEnabled;
        saveSettings(settings);
        initializeBridgeSync();
        if (settings.bridgeEnabled) bridgeScheduleSoon(200);
        window.alert("Local Agent OS bridge is now " + (settings.bridgeEnabled ? "ON." : "OFF."));
    }

    function showBridgeStatus() {
        var settings = loadSettings();
        window.alert(
            "Agent OS Local Bridge\n\n" +
            "Enabled: " + (settings.bridgeEnabled ? "YES" : "NO") + "\n" +
            "Configured: " + (bridgeConfigured() ? "YES" : "NO") + "\n" +
            "Endpoint: " + (settings.bridgeEndpoint || "(none)") + "\n" +
            "Last state: " + bridgeLastStatus.state + "\n" +
            "Last sync: " + (bridgeLastStatus.at || "(none)") + "\n" +
            "Last acknowledged: " + (bridgeLastStatus.acknowledged || 0) +
            (bridgeLastStatus.error ? "\nError: " + bridgeLastStatus.error : "") +
            "\n\nBuffered browser events: " + journalEventCount() +
            (isDiscordWeb()
                ? "\nDiscord records can sync from this tab."
                : "\nDiscord records sync whenever a Discord tab is open.")
        );
    }

    function initializeBridgeSync() {
        if (bridgeSyncInterval) {
            window.clearInterval(bridgeSyncInterval);
            bridgeSyncInterval = null;
        }
        if (!bridgeConfigured()) return;
        var seconds = Math.max(10, Number(loadSettings().bridgeSyncSeconds || 30));
        bridgeSyncInterval = window.setInterval(function () {
            bridgeSyncNow(false);
        }, seconds * 1000);
        bridgeScheduleSoon(2500);
    }


    function buildCapture() {
        var base = genericCapture();
        var adapters = [redditAdapter, amazonAdapter, youtubeAdapter, nexusAdapter, xenforoAdapter];
        for (var i = 0; i < adapters.length; i += 1) {
            try {
                var adapted = adapters[i](base);
                if (adapted) return adapted;
            } catch (error) {
                console.warn("[Agent OS] adapter failed", adapters[i].name, error);
            }
        }
        return base;
    }

    function queueCapture(capture, reason) {
        var queue = GM_getValue(QUEUE_KEY, []);
        if (!Array.isArray(queue)) queue = [];
        queue.push({
            queued_at: new Date().toISOString(),
            reason: reason || "endpoint-not-configured",
            capture: capture
        });
        if (queue.length > MAX_QUEUE) queue = queue.slice(queue.length - MAX_QUEUE);
        GM_setValue(QUEUE_KEY, queue);
        return queue.length;
    }

    function setButtonState(button, label, kind) {
        if (!button) return;
        button.textContent = label;
        button.dataset.agentOsState = kind || "";
        if (kind === "ok") button.style.background = "#2f855a";
        else if (kind === "error") button.style.background = "#c53030";
        else if (kind === "busy") button.style.background = "#4a5568";
        else button.style.background = "#20242b";
    }

    function sendCapture(capture, button) {
        var settings = loadSettings();
        var endpoint = settings.endpoint || "";
        var token = settings.token || "";

        // Once the local bridge is configured, it is the default durable
        // destination for manual captures unless the user explicitly set a
        // different capture endpoint.
        if (!endpoint && settings.bridgeEnabled && settings.bridgeToken) {
            endpoint = settings.bridgeCaptureEndpoint ||
                String(settings.bridgeEndpoint || "").replace(/\/batch(?:\?.*)?$/, "/capture");
            token = settings.bridgeToken;
        }

        if (!endpoint) {
            var count = queueCapture(capture, "endpoint-not-configured");
            setButtonState(button, "✓ Queued (" + count + ")", "ok");
            window.setTimeout(function () { setButtonState(button, "+ Agent OS", ""); }, 1600);
            return;
        }

        setButtonState(button, "Saving…", "busy");
        var headers = { "Content-Type": "application/json" };
        if (token) headers["X-Agent-OS-Token"] = token;

        GM_xmlhttpRequest({
            method: "POST",
            url: endpoint,
            headers: headers,
            data: JSON.stringify(capture),
            timeout: 15000,
            onload: function (response) {
                if (response.status >= 200 && response.status < 300) {
                    var duplicate = false;
                    try {
                        var body = JSON.parse(response.responseText || "{}");
                        duplicate = String(body.relationship || body.status || "").toLowerCase().indexOf("duplicate") !== -1;
                    } catch (error) {
                        // Success does not require JSON.
                    }
                    setButtonState(button, duplicate ? "✓ Already Saved" : "✓ Saved", "ok");
                } else {
                    var count = queueCapture(capture, "http-" + response.status);
                    setButtonState(button, "Queued after error (" + count + ")", "error");
                }
                window.setTimeout(function () { setButtonState(button, "+ Agent OS", ""); }, 1800);
            },
            onerror: function () {
                var count = queueCapture(capture, "network-error");
                setButtonState(button, "Queued offline (" + count + ")", "error");
                window.setTimeout(function () { setButtonState(button, "+ Agent OS", ""); }, 1800);
            },
            ontimeout: function () {
                var count = queueCapture(capture, "timeout");
                setButtonState(button, "Queued timeout (" + count + ")", "error");
                window.setTimeout(function () { setButtonState(button, "+ Agent OS", ""); }, 1800);
            }
        });
    }

    function saveCurrent(button) {
        var capture = buildCapture();
        sendCapture(capture, button);
    }

    function buttonCss(button) {
        button.type = "button";
        button.style.border = "1px solid rgba(255,255,255,.22)";
        button.style.borderRadius = "8px";
        button.style.background = "#20242b";
        button.style.color = "#fff";
        button.style.font = "600 13px/1.2 system-ui, -apple-system, Segoe UI, sans-serif";
        button.style.padding = "9px 12px";
        button.style.cursor = "pointer";
        button.style.boxShadow = "0 4px 14px rgba(0,0,0,.24)";
        button.style.zIndex = "2147483646";
    }

    function isRedditSite() {
        return hostname() === "reddit.com" ||
            hostname() === "www.reddit.com" ||
            hostname() === "old.reddit.com" ||
            hostname() === "new.reddit.com";
    }

    function isRedditIndividualPost() {
        return isRedditSite() && /\/comments\/[^/]+/i.test(location.pathname);
    }

    function isXenforoCaptureSite() {
        var host = hostname();
        return host === "spacebattles.com" ||
            host.endsWith(".spacebattles.com") ||
            host === "questionablequesting.com" ||
            host.endsWith(".questionablequesting.com");
    }

    function isXenforoIndividualThread() {
        return isXenforoCaptureSite() &&
            /\/threads\/[^/]*\.\d+(?:\/|$)/i.test(location.pathname);
    }

    function shouldShowFloatingButton() {
        if (isRedditSite() || isXenforoCaptureSite()) return false;
        return true;
    }

    function addFloatingButton() {
        var existing = document.getElementById("agent-os-universal-save");

        // Reddit, SpaceBattles, and Questionable Questing use inline
        // entity buttons attached to individual posts/threads instead
        // of one page-wide floating save button.
        if (!loadSettings().showFloatingButton || !shouldShowFloatingButton()) {
            if (existing) existing.remove();
            return;
        }

        if (existing) return;
        if (!document.body) return;

        var button = document.createElement("button");
        button.id = "agent-os-universal-save";
        button.textContent = "+ Agent OS";
        button.setAttribute("aria-label", "Save this page to Agent OS");
        buttonCss(button);
        button.style.position = "fixed";
        button.style.top = "90px";
        button.style.right = "20px";
        button.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();
            saveCurrent(button);
        });
        document.body.appendChild(button);
    }

    function xenforoThreadInfoFromUrl(urlText) {
        try {
            var u = new URL(urlText, location.href);
            var host = String(u.hostname || "").toLowerCase();
            var isSB = host === "spacebattles.com" || host.endsWith(".spacebattles.com");
            var isQQ = host === "questionablequesting.com" || host.endsWith(".questionablequesting.com");
            if (!isSB && !isQQ) return null;
            var match = u.pathname.match(/\/threads\/[^/]*\.(\d+)(?:\/|$)/i);
            if (!match) return null;
            return {
                site: isSB ? "spacebattles" : "questionablequesting",
                thread_id: match[1],
                url: u.origin + u.pathname
            };
        } catch (error) {
            return null;
        }
    }

    function inlineEntityButton(label) {
        var button = document.createElement("button");
        button.type = "button";
        button.textContent = label || "+ Agent OS";
        button.className = "agent-os-inline-save";
        buttonCss(button);
        button.style.position = "relative";
        button.style.top = "auto";
        button.style.right = "auto";
        button.style.display = "inline-flex";
        button.style.alignItems = "center";
        button.style.justifyContent = "center";
        button.style.padding = "6px 9px";
        button.style.margin = "0 4px 0 8px";
        button.style.whiteSpace = "nowrap";
        button.style.fontSize = "12px";
        button.style.lineHeight = "1.1";
        button.style.boxShadow = "0 2px 8px rgba(0,0,0,.18)";
        return button;
    }

    function captureXenforoThreadRow(row, link, button) {
        var info = xenforoThreadInfoFromUrl(link.href);
        if (!info) return;

        var title = cleanText(link.textContent);
        var authorNode = row && row.querySelector
            ? row.querySelector(".username, [data-user-id], .structItem-minor a")
            : null;
        var capture = genericCapture();
        capture.site = info.site;
        capture.content_type = "xenforo_thread";
        capture.source_id = info.site + ":thread:" + info.thread_id;
        capture.title = title || capture.title;
        capture.author = cleanText(authorNode && authorNode.textContent);
        capture.url = info.url;
        capture.canonical_url = info.url;
        capture.metadata = Object.assign({}, capture.metadata, {
            adapter: "xenforo-thread-row",
            forum: info.site,
            thread_id: info.thread_id,
            source_view: isXenforoIndividualThread() ? "thread" : "thread-list"
        });
        sendCapture(capture, button);
    }

    function xenforoPrimaryThreadLink(row) {
        if (!row || !row.querySelector) return null;
        var selectors = [
            ".structItem-title a[href*='/threads/']",
            ".p-title-value a[href*='/threads/']",
            "a[data-tp-primary='on'][href*='/threads/']",
            "a[href*='/threads/']"
        ];
        for (var i = 0; i < selectors.length; i += 1) {
            var links = row.querySelectorAll(selectors[i]);
            for (var j = 0; j < links.length; j += 1) {
                if (xenforoThreadInfoFromUrl(links[j].href)) return links[j];
            }
        }
        return null;
    }

    function xenforoButtonHost(row, link) {
        if (!row) return null;

        // XenForo thread-list rows normally expose a meta cell at the right.
        // Prefer that so the button sits beside the thread rather than
        // floating over the whole forum page.
        var meta = row.querySelector &&
            row.querySelector(".structItem-cell--meta, .structItem-cell.structItem-cell--meta");
        if (meta) return meta;

        var titleContainer = link && link.closest
            ? link.closest(".structItem-title, .p-title-value, h1, h2, h3")
            : null;
        return titleContainer || row;
    }

    function addXenforoThreadButtons() {
        if (!isXenforoCaptureSite() || !document.body) return;

        var handled = new Set();

        // Forum/category/search/list views.
        document.querySelectorAll(
            ".structItem--thread, .structItem[data-author], .structItem"
        ).forEach(function (row) {
            var link = xenforoPrimaryThreadLink(row);
            if (!link) return;
            var info = xenforoThreadInfoFromUrl(link.href);
            if (!info || handled.has(info.thread_id)) return;
            handled.add(info.thread_id);

            if (row.querySelector(".agent-os-xenforo-thread-save")) return;
            var host = xenforoButtonHost(row, link);
            if (!host) return;

            var button = inlineEntityButton("+ Agent OS");
            button.classList.add("agent-os-xenforo-thread-save");
            button.setAttribute("aria-label", "Save thread " + cleanText(link.textContent) + " to Agent OS");
            button.title = "Save this thread to Agent OS";
            button.style.float = "right";
            button.style.marginTop = "4px";
            button.style.marginBottom = "4px";
            button.addEventListener("click", function (event) {
                event.preventDefault();
                event.stopPropagation();
                captureXenforoThreadRow(row, link, button);
            });
            host.appendChild(button);
        });

        // Individual thread page: put the same entity-scoped control next to
        // the thread title instead of showing the global floating button.
        if (isXenforoIndividualThread()) {
            var currentInfo = xenforoThreadInfoFromUrl(location.href);
            var titleHost = document.querySelector(".p-title-value, h1.p-title-value, .p-title h1");
            if (currentInfo && titleHost &&
                    !titleHost.querySelector(".agent-os-xenforo-thread-save")) {
                var titleLink = document.createElement("a");
                titleLink.href = currentInfo.url;
                titleLink.textContent = cleanText(titleHost.childNodes[0] && titleHost.childNodes[0].textContent) ||
                    cleanText(titleHost.textContent) || "Current thread";

                var titleButton = inlineEntityButton("+ Agent OS");
                titleButton.classList.add("agent-os-xenforo-thread-save");
                titleButton.title = "Save this thread to Agent OS";
                titleButton.addEventListener("click", function (event) {
                    event.preventDefault();
                    event.stopPropagation();
                    captureXenforoThreadRow(titleHost, titleLink, titleButton);
                });
                titleHost.appendChild(titleButton);
            }
        }
    }

    function redditPostInfoFromUrl(urlText) {
        try {
            var u = new URL(urlText, location.href);
            var host = String(u.hostname || "").toLowerCase();
            if (["reddit.com", "www.reddit.com", "old.reddit.com", "new.reddit.com"].indexOf(host) === -1) {
                return null;
            }
            var match = u.pathname.match(/\/r\/([^/]+)\/comments\/([^/]+)/i) ||
                u.pathname.match(/\/comments\/([^/]+)/i);
            if (!match) return null;
            return {
                subreddit: match.length > 2 ? match[1] : "",
                post_id: match.length > 2 ? match[2] : match[1],
                url: u.origin + u.pathname
            };
        } catch (error) {
            return null;
        }
    }

    function redditCardLink(card) {
        if (!card || !card.querySelector) return null;
        var candidates = card.querySelectorAll("a[href*='/comments/']");
        for (var i = 0; i < candidates.length; i += 1) {
            if (redditPostInfoFromUrl(candidates[i].href)) return candidates[i];
        }
        return null;
    }

    function captureRedditCard(card, link, button) {
        var info = redditPostInfoFromUrl(link.href);
        if (!info) return;

        var shreddit = card.matches && card.matches("shreddit-post")
            ? card
            : card.querySelector && card.querySelector("shreddit-post");
        var title = cleanText(
            (shreddit && shreddit.getAttribute("post-title")) ||
            (card.querySelector && card.querySelector("h1, h2, h3, [slot='title']") &&
             card.querySelector("h1, h2, h3, [slot='title']").textContent) ||
            link.textContent
        );
        var author = cleanText(
            (shreddit && shreddit.getAttribute("author")) ||
            (card.querySelector && card.querySelector("[data-testid='post_author_link'], a[href*='/user/']") &&
             card.querySelector("[data-testid='post_author_link'], a[href*='/user/']").textContent)
        );

        var capture = genericCapture();
        capture.site = "reddit";
        capture.content_type = "reddit_post";
        capture.source_id = "reddit:" + info.post_id;
        capture.title = title || capture.title;
        capture.author = author;
        capture.url = info.url;
        capture.canonical_url = info.url;
        capture.metadata = Object.assign({}, capture.metadata, {
            adapter: "reddit-post-card",
            subreddit: info.subreddit,
            reddit_post_id: info.post_id,
            source_view: isRedditIndividualPost() ? "post" : "post-list"
        });
        sendCapture(capture, button);
    }

    function addRedditPostButtons() {
        if (!isRedditSite() || !document.body) return;

        var seen = new Set();
        var cards = Array.from(document.querySelectorAll(
            "shreddit-post, article, [data-testid='post-container'], .thing.link"
        ));

        // Individual post pages may have a narrower post container.
        if (isRedditIndividualPost() && !cards.length) {
            var main = document.querySelector("main");
            if (main) cards.push(main);
        }

        cards.forEach(function (card) {
            var link = null;
            if (card.matches && card.matches("shreddit-post")) {
                var permalink = card.getAttribute("permalink") || card.getAttribute("content-href") || "";
                if (permalink) {
                    var synthetic = document.createElement("a");
                    synthetic.href = permalink;
                    synthetic.textContent = card.getAttribute("post-title") || "";
                    if (redditPostInfoFromUrl(synthetic.href)) link = synthetic;
                }
            }
            link = link || redditCardLink(card);
            if (!link && isRedditIndividualPost()) {
                var info = redditPostInfoFromUrl(location.href);
                if (info) {
                    link = document.createElement("a");
                    link.href = info.url;
                    link.textContent = cleanText(document.querySelector("h1") && document.querySelector("h1").textContent);
                }
            }
            if (!link) return;

            var info = redditPostInfoFromUrl(link.href);
            if (!info || seen.has(info.post_id)) return;
            seen.add(info.post_id);

            if (card.querySelector && card.querySelector(".agent-os-reddit-post-save")) return;

            var host = card.querySelector && (
                card.querySelector("[slot='action-row']") ||
                card.querySelector("[data-post-click-location='post-media-content']") ||
                card.querySelector(".flat-list.buttons")
            );
            host = host || card;

            var button = inlineEntityButton("+ Agent OS");
            button.classList.add("agent-os-reddit-post-save");
            button.title = "Save this Reddit post to Agent OS";
            button.style.float = "right";
            button.style.marginTop = "6px";
            button.style.marginBottom = "6px";
            button.addEventListener("click", function (event) {
                event.preventDefault();
                event.stopPropagation();
                captureRedditCard(card, link, button);
            });
            host.appendChild(button);
        });
    }

    function captureNexusCard(card, link, button) {
        var info = nexusInfoFromUrl(link.href);
        if (!info) return;
        var titleNode = card.querySelector("h2, h3, h4, [class*='title']");
        var authorNode = card.querySelector('a[href*="/users/"]');
        var capture = genericCapture();
        capture.site = "nexusmods";
        capture.content_type = "nexus_mod";
        capture.source_id = "nexus:" + info.game + ":" + info.mod_id;
        capture.title = cleanText((titleNode && titleNode.textContent) || link.textContent || "Nexus Mod");
        capture.author = cleanText(authorNode && authorNode.textContent);
        capture.url = info.url;
        capture.canonical_url = info.url;
        capture.metadata = Object.assign({}, capture.metadata, {
            adapter: "nexus-card",
            game: info.game,
            mod_id: info.mod_id
        });
        sendCapture(capture, button);
    }

    function addNexusCardButtons() {
        if (hostname().indexOf("nexusmods.com") === -1) return;
        document.querySelectorAll('a[href*="/mods/"]').forEach(function (link) {
            var info = nexusInfoFromUrl(link.href);
            if (!info) return;
            var card = link.closest("article, li, [class*='card'], [class*='tile'], [class*='mod-tile']");
            if (!card || card.dataset.agentOsCaptureReady === "1") return;
            card.dataset.agentOsCaptureReady = "1";

            var button = document.createElement("button");
            button.textContent = "+ Agent OS";
            button.className = "agent-os-card-save";
            buttonCss(button);
            button.style.padding = "6px 9px";
            button.style.margin = "6px";
            button.addEventListener("click", function (event) {
                event.preventDefault();
                event.stopPropagation();
                captureNexusCard(card, link, button);
            });
            card.appendChild(button);
        });
    }

    function configureEndpoint() {
        var settings = loadSettings();
        var endpoint = window.prompt(
            "Agent OS capture endpoint. Leave blank to queue captures locally.\n\nExamples:\nhttp://127.0.0.1:PORT/api/v1/browser/capture\nhttps://script.google.com/macros/s/.../exec",
            settings.endpoint || ""
        );
        if (endpoint === null) return;
        settings.endpoint = endpoint.trim();
        saveSettings(settings);
        window.alert(settings.endpoint ? "Agent OS endpoint saved." : "Endpoint cleared. Captures will queue locally.");
    }

    function configureToken() {
        var settings = loadSettings();
        var token = window.prompt(
            "Agent OS device token. It is stored only in Tampermonkey storage on this browser. Leave blank when the endpoint does not require one.",
            settings.token || ""
        );
        if (token === null) return;
        settings.token = token.trim();
        saveSettings(settings);
        window.alert(settings.token ? "Device token saved locally." : "Device token cleared.");
    }

    function configureDevice() {
        var settings = loadSettings();
        var device = window.prompt("Optional device label (for example work-pc, home-pc, laptop):", settings.device || "");
        if (device === null) return;
        settings.device = device.trim();
        saveSettings(settings);
    }

    function exportQueue() {
        var queue = GM_getValue(QUEUE_KEY, []);
        if (!Array.isArray(queue)) queue = [];
        var text = JSON.stringify(queue, null, 2);
        GM_setClipboard(text, "text");
        window.alert("Copied " + queue.length + " queued capture(s) to the clipboard as JSON.");
    }

    function retryQueue() {
        var settings = loadSettings();
        var queue = GM_getValue(QUEUE_KEY, []);
        if (!Array.isArray(queue) || !queue.length) {
            window.alert("The Agent OS capture queue is empty.");
            return;
        }

        var endpoint = settings.endpoint || "";
        var token = settings.token || "";
        if (!endpoint && settings.bridgeEnabled && settings.bridgeToken) {
            endpoint = settings.bridgeCaptureEndpoint ||
                String(settings.bridgeEndpoint || "").replace(/\/batch(?:\?.*)?$/, "/capture");
            token = settings.bridgeToken;
        }
        if (!endpoint) {
            window.alert("Configure the local Agent OS bridge or a capture endpoint before retrying the queue.");
            return;
        }

        var items = queue.slice();
        GM_setValue(QUEUE_KEY, []);
        var index = 0;
        var failed = 0;

        function next() {
            if (index >= items.length) {
                window.alert(
                    "Queued captures retry complete.\n\n" +
                    "Submitted: " + (items.length - failed) + "\n" +
                    "Still queued: " + failed
                );
                return;
            }
            var item = items[index++];
            var headers = { "Content-Type": "application/json" };
            if (token) headers["X-Agent-OS-Token"] = token;
            GM_xmlhttpRequest({
                method: "POST",
                url: endpoint,
                headers: headers,
                data: JSON.stringify(item.capture),
                timeout: 15000,
                onload: function (response) {
                    if (!(response.status >= 200 && response.status < 300)) {
                        failed += 1;
                        queueCapture(item.capture, "retry-http-" + response.status);
                    }
                    next();
                },
                onerror: function () {
                    failed += 1;
                    queueCapture(item.capture, "retry-network-error");
                    next();
                },
                ontimeout: function () {
                    failed += 1;
                    queueCapture(item.capture, "retry-timeout");
                    next();
                }
            });
        }
        next();
    }

    function clearQueue() {
        var queue = GM_getValue(QUEUE_KEY, []);
        var count = Array.isArray(queue) ? queue.length : 0;
        if (!count) {
            window.alert("The Agent OS capture queue is already empty.");
            return;
        }
        if (window.confirm("Clear " + count + " queued capture(s)? This cannot be undone.")) {
            GM_setValue(QUEUE_KEY, []);
        }
    }

    function registerMenus() {
        GM_registerMenuCommand("Agent OS: Save current page", function () { saveCurrent(null); });
        GM_registerMenuCommand("Agent OS: Configure endpoint", configureEndpoint);
        GM_registerMenuCommand("Agent OS: Configure device token", configureToken);
        GM_registerMenuCommand("Agent OS: Set device label", configureDevice);
        GM_registerMenuCommand("Agent OS: Retry queued captures", retryQueue);
        GM_registerMenuCommand("Agent OS: Copy queued captures as JSON", exportQueue);
        GM_registerMenuCommand("Agent OS: Clear queued captures", clearQueue);
        GM_registerMenuCommand("Agent OS: Configure local bridge", configureLocalBridge);
        GM_registerMenuCommand("Agent OS: Local bridge ON/OFF", toggleLocalBridge);
        GM_registerMenuCommand("Agent OS: Sync local bridge now", function () { bridgeSyncNow(true); });
        GM_registerMenuCommand("Agent OS: Local bridge status", showBridgeStatus);
        GM_registerMenuCommand("Agent OS: Browser Journal ON/OFF", toggleBrowserJournal);
        GM_registerMenuCommand("Agent OS: Browser Journal include/exclude this domain", toggleJournalCurrentDomainExclusion);
        GM_registerMenuCommand("Agent OS: Browser Journal export range", function () { exportBrowserJournalPrompt(); });
        GM_registerMenuCommand("Agent OS: Browser Journal compact exported range", function () { compactBrowserJournalPrompt(); });
        GM_registerMenuCommand("Agent OS: Export combined Discord + Browser archive", function () { exportCombinedActivityArchivePrompt(); });
        GM_registerMenuCommand("Agent OS: Compact combined exported range", function () { compactCombinedActivityPrompt(); });
        GM_registerMenuCommand("Agent OS: Browser Journal clear local buffer", clearBrowserJournal);
        GM_registerMenuCommand("Agent OS: Discord passive indexing ON/OFF", toggleDiscordPassiveIndexing);
        GM_registerMenuCommand("Agent OS: Discord open local index", function () { openDiscordIndexBrowser(); });
        GM_registerMenuCommand("Agent OS: Discord export current channel", function () { exportDiscordIndex(true); });
        GM_registerMenuCommand("Agent OS: Discord export full local index", function () { exportDiscordIndex(false); });
        GM_registerMenuCommand("Agent OS: Discord clear local index", clearDiscordIndex);
        GM_registerMenuCommand("Agent OS: Discord clear archive markers", clearDiscordArchiveMarkers);
    }

    ensureDiscordIndexingDefault();
    registerMenus();
    addFloatingButton();
    initializeBrowserJournal();
    initializeBridgeSync();
    addNexusCardButtons();
    addXenforoThreadButtons();
    addRedditPostButtons();
    if (isDiscordWeb()) {
        ensureDiscordStatus();
        scheduleDiscordScan(0);
    }

    var scheduled = false;
    var observer = new MutationObserver(function (mutations) {
        var discordActive = isDiscordWeb() && loadSettings().discordPassiveIndexing;

        if (discordActive) {
            mutations.forEach(function (mutation) {
                mutation.addedNodes.forEach(function (node) {
                    if (node && node.nodeType === Node.ELEMENT_NODE) {
                        queueDiscordMutationRoot(node);
                    }
                });
            });
            scheduleDiscordMutationFlush(100);

            // Discord is a single-page app. On route changes do one bounded
            // full scan so already-rendered nodes on the new view are not missed.
            if (location.href !== discordLastObservedUrl) {
                discordLastObservedUrl = location.href;
                scheduleDiscordScan(150);
            }
        }

        if (scheduled) return;
        scheduled = true;
        window.setTimeout(function () {
            scheduled = false;
            addFloatingButton();
            addNexusCardButtons();
            addXenforoThreadButtons();
            addRedditPostButtons();
            ensureJournalStatus();
            if (isDiscordWeb()) ensureDiscordStatus();
        }, 300);
    });

    if (document.documentElement) {
        observer.observe(document.documentElement, { childList: true, subtree: true });
    }

    console.info("[Agent OS] Universal Capture v" + VERSION + " loaded", {
        adapter: buildCapture().metadata.adapter,
        queued: (GM_getValue(QUEUE_KEY, []) || []).length,
        discord_passive_indexing: isDiscordWeb() ? loadSettings().discordPassiveIndexing : undefined,
        browser_journal: loadSettings().browserJournalEnabled,
        browser_journal_domain_excluded: journalDomainExcluded(hostname()),
        bridge_enabled: loadSettings().bridgeEnabled,
        bridge_configured: bridgeConfigured()
    });
})();
