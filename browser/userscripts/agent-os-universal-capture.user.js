// ==UserScript==
// @name         Agent OS Universal Capture
// @namespace    agent-os
// @version      3.2.0
// @description  Save useful pages from Reddit, Amazon, YouTube, Nexus Mods, XenForo forums, and the general web into the Agent OS browser inbox.
// @homepageURL   https://github.com/unwit1/universal-capture-plugin
// @updateURL     https://raw.githubusercontent.com/unwit1/universal-capture-plugin/main/agent-os-universal-capture.user.js
// @downloadURL   https://raw.githubusercontent.com/unwit1/universal-capture-plugin/main/agent-os-universal-capture.user.js
// @author       Agent OS
// @match        http://*/*
// @match        https://*/*
// @run-at       document-idle
// @grant        GM_getValue
// @grant        GM_setValue
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

    var VERSION = "3.2.0";
    var SETTINGS_KEY = "agent_os_capture_settings_v1";
    var QUEUE_KEY = "agent_os_capture_queue_v1";
    var MAX_QUEUE = 500;

    var DEFAULT_SETTINGS = {
        endpoint: "",
        token: "",
        device: "",
        defaultIntent: "save",
        showFloatingButton: true
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
        if (!settings.endpoint) {
            var count = queueCapture(capture, "endpoint-not-configured");
            setButtonState(button, "✓ Queued (" + count + ")", "ok");
            window.setTimeout(function () { setButtonState(button, "+ Agent OS", ""); }, 1600);
            return;
        }

        setButtonState(button, "Saving…", "busy");
        var headers = { "Content-Type": "application/json" };
        if (settings.token) headers["X-Agent-OS-Token"] = settings.token;

        GM_xmlhttpRequest({
            method: "POST",
            url: settings.endpoint,
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

    function addFloatingButton() {
        if (!loadSettings().showFloatingButton) return;
        if (document.getElementById("agent-os-universal-save")) return;
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
        if (!settings.endpoint) {
            window.alert("Configure an Agent OS endpoint before retrying the queue.");
            return;
        }

        var items = queue.slice();
        GM_setValue(QUEUE_KEY, []);
        var index = 0;

        function next() {
            if (index >= items.length) {
                window.alert("Queued captures were submitted. Any failures were placed back in the queue.");
                return;
            }
            var item = items[index++];
            var headers = { "Content-Type": "application/json" };
            if (settings.token) headers["X-Agent-OS-Token"] = settings.token;
            GM_xmlhttpRequest({
                method: "POST",
                url: settings.endpoint,
                headers: headers,
                data: JSON.stringify(item.capture),
                timeout: 15000,
                onload: function (response) {
                    if (!(response.status >= 200 && response.status < 300)) {
                        queueCapture(item.capture, "retry-http-" + response.status);
                    }
                    next();
                },
                onerror: function () {
                    queueCapture(item.capture, "retry-network-error");
                    next();
                },
                ontimeout: function () {
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
    }

    registerMenus();
    addFloatingButton();
    addNexusCardButtons();

    var scheduled = false;
    var observer = new MutationObserver(function () {
        if (scheduled) return;
        scheduled = true;
        window.setTimeout(function () {
            scheduled = false;
            addFloatingButton();
            addNexusCardButtons();
        }, 300);
    });

    if (document.documentElement) {
        observer.observe(document.documentElement, { childList: true, subtree: true });
    }

    console.info("[Agent OS] Universal Capture v" + VERSION + " loaded", {
        adapter: buildCapture().metadata.adapter,
        queued: (GM_getValue(QUEUE_KEY, []) || []).length
    });
})();
