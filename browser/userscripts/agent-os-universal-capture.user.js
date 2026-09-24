// ==UserScript==
// @name         Agent OS Universal Capture
// @namespace    agent-os
// @version      3.3.1
// @description  Save useful pages and passively index rendered Discord Web messages into Agent OS.
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

    var VERSION = "3.3.1";
    var SETTINGS_KEY = "agent_os_capture_settings_v1";
    var QUEUE_KEY = "agent_os_capture_queue_v1";
    var MAX_QUEUE = 500;

    var DEFAULT_SETTINGS = {
        endpoint: "",
        token: "",
        device: "",
        defaultIntent: "save",
        showFloatingButton: true,
        discordPassiveIndexing: true
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


    // -- Discord passive indexing ---------------------------------------------

    var DISCORD_DB_NAME = "agent_os_discord_index_v1";
    var DISCORD_DB_VERSION = 1;
    var DISCORD_STORE = "messages";
    var discordDbPromise = null;
    var discordSeenFingerprints = new Map();
    var discordSessionNew = 0;
    var discordLastScanAt = 0;
    var discordScanTimer = null;

    function isDiscordWeb() {
        return hostname() === "discord.com" || hostname() === "www.discord.com";
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
            request.onupgradeneeded = function () {
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
            };
            request.onsuccess = function () { resolve(request.result); };
            request.onerror = function () { reject(request.error || new Error("Could not open Discord index")); };
        });
        return discordDbPromise;
    }

    function discordMessageIds(node) {
        if (!node || node.nodeType !== Node.ELEMENT_NODE) return null;
        var raw = String(
            node.id ||
            node.getAttribute("data-list-item-id") ||
            ""
        );
        var match = raw.match(/chat-messages(?:___|-)(\d+)-(\d+)/);
        if (!match) {
            var content = node.querySelector('[id^="message-content-"]');
            var messageMatch = content && String(content.id || "").match(/message-content-(\d+)/);
            var context = discordContext();
            if (!messageMatch || !context) return null;
            return { channel_id: context.channel_id, message_id: messageMatch[1] };
        }
        return { channel_id: match[1], message_id: match[2] };
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
        var content = node.querySelector('#message-content-' + CSS.escape(messageId)) ||
            node.querySelector('[id^="message-content-"]');
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

    function discordReplyTarget(node) {
        var link = node.querySelector('a[href*="/channels/"]');
        if (!link) return "";
        var match = String(link.href || "").match(/\/channels\/[^/]+\/[^/]+\/(\d+)/);
        return match ? match[1] : "";
    }

    function discordRecord(node, fallbackAuthor) {
        var context = discordContext();
        var ids = discordMessageIds(node);
        if (!context || !ids || ids.channel_id !== context.channel_id) return null;

        var messageId = ids.message_id;
        var author = discordAuthor(node, messageId) || fallbackAuthor || "";
        var timeNode = node.querySelector("time[datetime]");
        var timestamp = String(timeNode && timeNode.getAttribute("datetime") || "");
        var text = discordMessageText(node, messageId);
        var urls = discordUrls(node);
        var attachments = discordAttachments(node);

        // Discord can render structural/message placeholders. Skip nodes that
        // carry no useful message evidence at all.
        if (!text && !attachments.length && !urls.length) return null;

        var guildId = context.guild_id;
        var channelId = context.channel_id;
        var messageUrl = "https://discord.com/channels/" +
            encodeURIComponent(guildId) + "/" +
            encodeURIComponent(channelId) + "/" +
            encodeURIComponent(messageId);

        return {
            key: guildId + ":" + channelId + ":" + messageId,
            channel_key: guildId + ":" + channelId,
            schema_version: "discord-message-v1",
            source: "discord-web-rendered",
            guild_id: guildId,
            guild_name: context.guild_name,
            channel_id: channelId,
            channel_name: context.channel_name,
            message_id: messageId,
            author: author,
            timestamp: timestamp,
            text: text,
            urls: urls,
            attachments: attachments,
            reply_to_message_id: discordReplyTarget(node),
            message_url: messageUrl,
            page_title: context.page_title,
            captured_at: new Date().toISOString(),
            device: loadSettings().device || ""
        };
    }

    function discordFingerprint(record) {
        return JSON.stringify([
            record.author,
            record.timestamp,
            record.text,
            record.urls,
            record.attachments,
            record.reply_to_message_id
        ]);
    }

    async function putDiscordRecord(record) {
        var fingerprint = discordFingerprint(record);
        if (discordSeenFingerprints.get(record.key) === fingerprint) return false;
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

    async function scanDiscordMessages() {
        if (!isDiscordWeb() || !loadSettings().discordPassiveIndexing) return;
        var context = discordContext();
        if (!context) return;

        var nodes = Array.from(document.querySelectorAll(
            '[id^="chat-messages-"], [data-list-item-id^="chat-messages___"]'
        ));
        if (!nodes.length) return;

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

    function scheduleDiscordScan(delay) {
        if (!isDiscordWeb() || !loadSettings().discordPassiveIndexing) return;
        if (discordScanTimer) window.clearTimeout(discordScanTimer);
        discordScanTimer = window.setTimeout(function () {
            discordScanTimer = null;
            scanDiscordMessages().catch(function (error) {
                console.warn("[Agent OS] Discord passive scan failed", error);
            });
        }, typeof delay === "number" ? delay : 250);
    }

    async function discordIndexStats() {
        var db = await openDiscordDb();
        return new Promise(function (resolve, reject) {
            var tx = db.transaction(DISCORD_STORE, "readonly");
            var store = tx.objectStore(DISCORD_STORE);
            var countRequest = store.count();
            countRequest.onsuccess = function () {
                resolve({ total: countRequest.result || 0, session_new: discordSessionNew });
            };
            countRequest.onerror = function () { reject(countRequest.error); };
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
        pill.title = "Agent OS passive Discord message index";
        pill.addEventListener("click", async function () {
            var stats = await discordIndexStats();
            var settings = loadSettings();
            window.alert(
                "Agent OS Discord index\n\n" +
                "Passive indexing: " + (settings.discordPassiveIndexing ? "ON" : "OFF") + "\n" +
                "Indexed messages: " + stats.total + "\n" +
                "New this page session: " + stats.session_new + "\n\n" +
                "Only messages rendered in Discord Web are indexed."
            );
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
            pill.textContent = (on ? "Discord Index ● " : "Discord Index ○ ") + stats.total;
            pill.style.opacity = on ? "1" : ".65";
        } catch (error) {
            pill.textContent = "Discord Index !";
        }
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
        var blob = new Blob([JSON.stringify({
            schema_version: "discord-index-export-v1",
            exported_at: new Date().toISOString(),
            current_channel_only: Boolean(currentChannelOnly),
            messages: rows
        }, null, 2)], { type: "application/json" });
        var url = URL.createObjectURL(blob);
        var link = document.createElement("a");
        link.href = url;
        link.download = "agent-os-discord-index" + suffix + ".json";
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.setTimeout(function () { URL.revokeObjectURL(url); }, 5000);
    }

    async function clearDiscordIndex() {
        if (!window.confirm("Clear the entire local Agent OS Discord message index on this browser?")) return;
        var db = await openDiscordDb();
        await new Promise(function (resolve, reject) {
            var tx = db.transaction(DISCORD_STORE, "readwrite");
            tx.objectStore(DISCORD_STORE).clear();
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
        GM_registerMenuCommand("Agent OS: Discord passive indexing ON/OFF", toggleDiscordPassiveIndexing);
        GM_registerMenuCommand("Agent OS: Discord export current channel", function () { exportDiscordIndex(true); });
        GM_registerMenuCommand("Agent OS: Discord export full local index", function () { exportDiscordIndex(false); });
        GM_registerMenuCommand("Agent OS: Discord clear local index", clearDiscordIndex);
    }

    registerMenus();
    addFloatingButton();
    addNexusCardButtons();
    if (isDiscordWeb()) {
        ensureDiscordStatus();
        scheduleDiscordScan(0);
    }

    var scheduled = false;
    var observer = new MutationObserver(function () {
        if (scheduled) return;
        scheduled = true;
        window.setTimeout(function () {
            scheduled = false;
            addFloatingButton();
            addNexusCardButtons();
            if (isDiscordWeb()) {
                ensureDiscordStatus();
                scheduleDiscordScan(100);
            }
        }, 300);
    });

    if (document.documentElement) {
        observer.observe(document.documentElement, { childList: true, subtree: true });
    }

    console.info("[Agent OS] Universal Capture v" + VERSION + " loaded", {
        adapter: buildCapture().metadata.adapter,
        queued: (GM_getValue(QUEUE_KEY, []) || []).length,
        discord_passive_indexing: isDiscordWeb() ? loadSettings().discordPassiveIndexing : undefined
    });
})();
