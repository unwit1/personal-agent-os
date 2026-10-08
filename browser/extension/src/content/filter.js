/*
 * Agent OS content filters: in-page runtime.
 *
 * Finds items with the site adapters, hides those matching a rule, adds a
 * small inline "hide" control to each item, and answers the background
 * page's context-menu and popup queries.
 */
(function () {
    "use strict";

    if (window.top !== window) return;
    var Core = globalThis.AgentOsFilterCore;
    var Sites = globalThis.AgentOsSites;
    if (!Core || !Sites) return;

    var state = Core.normalizeState(null);
    var compiled = [];
    var adapters = [];
    var facetCache = new WeakMap();   // element -> { adapter, facets }
    var processed = new Set();        // live items we have evaluated
    var nexusData = new Map();        // "game:modId" -> API data
    var nexusPending = new Set();
    var lastContext = null;
    var reveal = false;
    var scanTimer = null;
    var started = false;
    var counterEl = null;
    var popoverHost = null;
    var lastHref = location.href;

    function siteSettings(adapter) {
        return state.sites[adapter.scope] || {};
    }

    function loadState() {
        return browser.storage.local.get(Core.STORAGE_KEY).then(function (res) {
            state = Core.normalizeState(res[Core.STORAGE_KEY]);
            compiled = Core.compileRules(state);
        });
    }

    function refreshAdapters() {
        adapters = Sites.adaptersFor(location, document, state.customSites);
    }

    // -- evaluation ---------------------------------------------------------------

    function facetsFor(adapter, el) {
        var cached = facetCache.get(el);
        if (cached && cached.adapter === adapter) return cached.facets;
        var facets;
        try {
            facets = adapter.facets(el, { host: location.hostname, href: location.href }) || {};
        } catch (error) {
            facets = {};
        }
        facetCache.set(el, { adapter: adapter, facets: facets });
        return facets;
    }

    function effectiveFacets(adapter, facets) {
        if (adapter.scope === "nexus" && facets.lookup && nexusData.has(facets.lookup.key)) {
            return adapter.enrich(facets, nexusData.get(facets.lookup.key));
        }
        return facets;
    }

    function targetFor(adapter, el) {
        return adapter.target ? adapter.target(el) : el;
    }

    function hideStyleFor(adapter, el, facets) {
        // Collapsing forum posts keeps a thread readable; feeds just drop items.
        if (facets.kind === "post" && adapter.scope === "xenforo") return "collapse";
        if (facets.kind === "comment") return "collapse";
        return state.hiddenStyle === "collapse" ? "collapse" : "remove";
    }

    function ruleAllowedFor(adapter, facets, result) {
        if (!result) return false;
        if (adapter.scope === "xenforo" && facets.kind === "post") {
            return siteSettings(adapter).hidePostsByAuthor !== false && result.rule && result.rule.field === "author";
        }
        if (facets.kind === "comment") return Boolean(result.rule && result.rule.field === "author");
        return true;
    }

    function evaluateItem(adapter, el) {
        var facets = effectiveFacets(adapter, facetsFor(adapter, el));
        var target = targetFor(adapter, el);
        processed.add(el);
        var settings = siteSettings(adapter);
        var result = null;
        if (state.enabled && settings.enabled !== false) {
            result = Core.evaluate(compiled, facets, {
                scope: adapter.scope,
                host: location.hostname,
                exempt: adapter.exempt ? adapter.exempt(location) : {},
                siteSettings: settings
            });
            if (!ruleAllowedFor(adapter, facets, result)) result = null;
            if (!result) result = shownEarlier(adapter, target, facets);
        }
        applyResult(adapter, el, target, facets, result);
        if (state.showInlineButtons && facets.kind !== "section") ensureButton(adapter, el, target);
        if (state.showInlineButtons && adapter.inlineHides && !result) ensureInlineHides(adapter, el);
        if (adapter.scope === "nexus" && facets.lookup && settings.lookupTags !== false) queueNexusLookup(facets.lookup);
    }

    function applyResult(adapter, el, target, facets, result) {
        var hiddenNow = target.getAttribute("data-aos-hidden");
        if (!result) {
            if (hiddenNow) {
                target.removeAttribute("data-aos-hidden");
                target.removeAttribute("data-aos-reason");
                var bar = target.querySelector(":scope > .aos-collapse-bar");
                if (bar) bar.remove();
            }
            return;
        }
        var style = hideStyleFor(adapter, el, facets);
        setAttr(target, "data-aos-hidden", style);
        setAttr(target, "data-aos-reason", result.reason);
        if (result.rule) setAttr(target, "data-aos-rule", result.rule.id);
        else target.removeAttribute("data-aos-rule");
        var existingBar = target.querySelector(":scope > .aos-collapse-bar");
        if (style !== "collapse") {
            if (existingBar) existingBar.remove();
            return;
        }
        var label = "Hidden by Agent OS · " + result.reason + " · click to show";
        if (!existingBar) {
            var collapseBar = document.createElement("div");
            collapseBar.className = "aos-collapse-bar";
            collapseBar.textContent = label;
            collapseBar.addEventListener("click", function (event) {
                event.preventDefault();
                event.stopPropagation();
                target.toggleAttribute("data-aos-peek");
            });
            target.insertBefore(collapseBar, target.firstChild);
        } else if (existingBar.textContent !== label) {
            // Only touch the DOM on change: our own mutations re-trigger scans.
            existingBar.textContent = label;
        }
    }

    function setAttr(el, name, value) {
        if (el.getAttribute(name) !== value) el.setAttribute(name, value);
    }

    function scan() {
        scanTimer = null;
        if (!adapters.length) return;
        var scanStarted = performance.now();
        if (location.href !== lastHref) {
            // Client-side navigation (Nexus is a single-page app).
            flushPerf("navigate");
            lastHref = location.href;
            perf = newPerf("spa");
            resetBackfill();
            pageLookup = undefined;
            renderPageBar();
        }
        adapters.forEach(function (adapter) {
            var items;
            try {
                items = adapter.items(document, document);
            } catch (error) {
                items = [];
            }
            items.forEach(function (el) { evaluateItem(adapter, el); });
            if (adapter.listing) maybeBackfill(adapter, items);
        });
        processed.forEach(function (el) { if (!el.isConnected) processed.delete(el); });
        updateCounter();
        var spent = performance.now() - scanStarted;
        perf.scans += 1;
        perf.scanMs += spent;
        perf.maxScanMs = Math.max(perf.maxScanMs, spent);
    }

    function scheduleScan(delay) {
        if (scanTimer) return;
        scanTimer = setTimeout(scan, typeof delay === "number" ? delay : 120);
    }

    function reevaluateAll() {
        processed.forEach(function (el) {
            if (!el.isConnected) { processed.delete(el); return; }
            var cached = facetCache.get(el);
            if (cached) evaluateItem(cached.adapter, el);
        });
        scan();
    }

    // -- Nexus API enrichment -----------------------------------------------------

    var nexusTimer = null;

    function queueNexusLookup(lookup) {
        if (!lookup || nexusData.has(lookup.key) || nexusPending.has(lookup.key)) return;
        nexusPending.add(lookup.key);
        if (nexusTimer) return;
        nexusTimer = setTimeout(flushNexusLookups, 250);
    }

    function flushNexusLookups() {
        nexusTimer = null;
        var batch = Array.from(nexusPending).slice(0, 100);
        if (!batch.length) return;
        var items = batch.map(function (key) {
            var parts = key.split(":");
            return { game: parts[0], modId: parts[1], key: key };
        });
        browser.runtime.sendMessage({ type: "nexus-lookup", items: items }).then(function (result) {
            var data = result && result.mods || {};
            batch.forEach(function (key) {
                nexusPending.delete(key);
                nexusData.set(key, data[key] || null);
            });
            reevaluateAll();
            if (nexusPending.size) nexusTimer = setTimeout(flushNexusLookups, 250);
        }).catch(function () {
            batch.forEach(function (key) { nexusPending.delete(key); nexusData.set(key, null); });
        });
    }

    // -- refill paginated lists from the next page ------------------------------
    //
    // When hidden items leave a listing short, items from the following
    // page(s) are appended until it shows as many as Nexus rendered. Items
    // pulled forward are remembered for this tab, so the next page hides
    // them instead of showing them twice.

    var BACKFILL_MAX_PAGES = 6;
    var BACKFILL_SETTLE_MS = 800;
    var backfill = null;
    var shownCache = { key: "", map: {} };

    function listingInfo(adapter) {
        try {
            return adapter.listing && siteSettings(adapter).fillFromNextPage !== false ? adapter.listing(location) : null;
        } catch (error) {
            return null;
        }
    }

    function shownMap(key) {
        if (shownCache.key !== key) {
            var map = {};
            try { map = JSON.parse(sessionStorage.getItem("aos-shown:" + key) || "{}") || {}; } catch (error) { map = {}; }
            shownCache = { key: key, map: map };
        }
        return shownCache.map;
    }

    function recordShown(key, id, page) {
        var map = shownMap(key);
        if (map[id] && map[id] <= page) return;
        map[id] = page;
        var ids = Object.keys(map);
        if (ids.length > 1000) ids.slice(0, ids.length - 1000).forEach(function (k) { delete map[k]; });
        try { sessionStorage.setItem("aos-shown:" + key, JSON.stringify(map)); } catch (error) { /* storage off */ }
    }

    function shownEarlier(adapter, target, facets) {
        if (!facets.id || target.hasAttribute("data-aos-backfill")) return null;
        var info = listingInfo(adapter);
        if (!info) return null;
        var page = shownMap(info.key)[facets.id];
        return page && page < info.page ? { rule: null, matched: "", reason: "Already shown on page " + page } : null;
    }

    function resetBackfill() {
        if (backfill) abortBackfillLoad(backfill, true);
        backfill = null;
        document.querySelectorAll("[data-aos-backfill]").forEach(function (node) { node.remove(); });
    }

    // Stop an in-flight next-page load so it never competes with the page
    // the user is navigating to; it is retried once the page settles.
    function abortBackfillLoad(bf, final) {
        if (!bf || !bf.loading) return;
        if (bf.controller) bf.controller.abort();
        if (bf.frame) bf.frame.remove();
        bf.controller = null;
        bf.frame = null;
        bf.loading = false;
        if (!final && bf.started) {
            bf.nextPage -= 1;
            bf.pagesLoaded -= 1;
        }
        bf.started = false;
        perf.aborted += 1;
        if (!final) {
            // Try again once things are quiet (the click may not navigate at all).
            bf.changedAt = performance.now();
            setTimeout(function () { if (backfill === bf) scheduleScan(0); }, BACKFILL_SETTLE_MS + 50);
        }
    }

    document.addEventListener("pointerdown", function (event) {
        var target = event.target instanceof Element ? event.target : null;
        if (!backfill || !backfill.loading || !target) return;
        if (target.closest("a[href], button") && !target.closest(".aos-hide-btn, .aos-inline-hide")) abortBackfillLoad(backfill, false);
    }, true);

    function isHidden(adapter, el) {
        return targetFor(adapter, el).hasAttribute("data-aos-hidden");
    }

    function maybeBackfill(adapter, items) {
        var info = listingInfo(adapter);
        if (!info) return;
        var native = items.filter(function (el) { return !targetFor(adapter, el).hasAttribute("data-aos-backfill"); });
        if (!native.length) return;
        if (!backfill || backfill.key !== info.key || backfill.page !== info.page) {
            backfill = {
                key: info.key, page: info.page, info: info, adapter: adapter,
                target: 0, nextPage: info.page + 1, pagesLoaded: 0,
                buffer: [], loading: false, exhausted: false, container: null
            };
        }
        var bf = backfill;
        var now = performance.now();
        if (native.length !== bf.nativeCount) {
            bf.nativeCount = native.length;
            bf.changedAt = now;
        }
        bf.target = Math.max(bf.target, native.length);
        bf.container = targetFor(adapter, native[native.length - 1]).parentElement;
        if (!bf.container) return;
        var present = new Set();
        items.forEach(function (el) {
            var id = facetsFor(adapter, el).id;
            if (id) present.add(id);
        });
        var need = bf.target - items.filter(function (el) { return !isHidden(adapter, el); }).length;
        while (need > 0 && bf.buffer.length) {
            var entry = bf.buffer.shift();
            if (entry.id && present.has(entry.id)) continue;
            var shownOn = entry.id ? shownMap(bf.key)[entry.id] : 0;
            if (shownOn && shownOn < bf.page) continue;
            entry.node.setAttribute("data-aos-backfill", String(entry.page));
            bf.container.appendChild(entry.node);
            if (entry.id) {
                present.add(entry.id);
                recordShown(bf.key, entry.id, bf.page);
            }
            need -= 1;
        }
        if (need <= 0 || bf.loading || bf.exhausted || bf.pagesLoaded >= BACKFILL_MAX_PAGES) return;
        // Only fetch once the page has finished loading and its list has
        // stopped changing, during idle time.
        var quietFor = now - (bf.changedAt || 0);
        if (document.readyState !== "complete" || quietFor < BACKFILL_SETTLE_MS) {
            setTimeout(function () { scheduleScan(0); }, Math.max(150, BACKFILL_SETTLE_MS - quietFor));
            return;
        }
        if (!perf.settledMs) perf.settledMs = Math.round(now - perf.start);
        bf.loading = true;
        var idle = typeof requestIdleCallback === "function" ? requestIdleCallback : function (fn) { return setTimeout(fn, 0); };
        idle(function () {
            if (backfill === bf && bf.loading) loadNextPage(bf);
        }, { timeout: 1500 });
    }

    function loadNextPage(bf) {
        bf.loading = true;
        bf.started = true;
        bf.pagesLoaded += 1;
        var pageNo = bf.nextPage;
        bf.nextPage += 1;
        var url = bf.info.pageUrl(pageNo);
        var controller = typeof AbortController === "function" ? new AbortController() : null;
        bf.controller = controller;
        var started = performance.now();
        fetchListingItems(bf.adapter, url, bf, controller, pageNo).then(function (entries) {
            if (controller && controller.signal.aborted) return;
            perf.loads.push({ page: pageNo, ms: Math.round(performance.now() - started), items: entries.length, mode: bf.mode || "" });
            if (!entries.length) bf.exhausted = true;
            entries.forEach(function (entry) {
                entry.page = pageNo;
                bf.buffer.push(entry);
            });
        }).catch(function (error) {
            if (controller && controller.signal.aborted) return;
            console.warn("[Agent OS] could not load the next page", url, error);
            bf.exhausted = true;
        }).then(function () {
            if (controller && controller.signal.aborted) return;
            bf.loading = false;
            bf.started = false;
            bf.controller = null;
            if (backfill === bf) scheduleScan(0);
        });
    }

    function collectListingItems(adapter, doc, url) {
        var items;
        try { items = adapter.items(doc, doc, url) || []; } catch (error) { items = []; }
        return items.map(function (el) {
            var facets = {};
            try { facets = adapter.facets(el, { host: location.hostname, href: url }) || {}; } catch (error) { facets = {}; }
            var node = document.importNode(targetFor(adapter, el), true);
            cleanClone(node);
            return { node: node, id: facets.id || "" };
        });
    }

    function cleanClone(node) {
        // Drop our own controls, the site's (now dead) item menus and markers
        // so both content scripts treat the copy as a fresh item.
        node.querySelectorAll(".aos-hide-btn, .aos-inline-hide, .aos-collapse-bar, .agent-os-card-save, .agent-os-follow-target, [id^='headlessui-menu-button']")
            .forEach(function (child) { child.remove(); });
        [node].concat(Array.from(node.querySelectorAll("*"))).forEach(function (child) {
            Array.from(child.attributes).forEach(function (attr) {
                if (/^data-(aos-|agent-os-)/.test(attr.name)) child.removeAttribute(attr.name);
            });
            child.classList.remove("aos-item", "aos-overlay", "aos-rel");
        });
    }

    function pageFetch(url, controller) {
        // content.fetch makes the request as the page (cookies, same origin).
        return Promise.resolve().then(function () {
            var fetcher = typeof content !== "undefined" && content && typeof content.fetch === "function"
                ? content.fetch.bind(content) : fetch;
            var options = { credentials: "include" };
            if (controller) options.signal = controller.signal;
            return fetcher(url, options);
        }).then(function (response) {
            if (!response.ok) throw new Error("HTTP " + response.status);
            return response.text();
        });
    }

    // -- the page's own list query (Nexus renders its mod list from GraphQL) ----

    var pageListRequest = null;

    function headerObject(headers) {
        var out = {};
        if (!headers) return out;
        if (typeof headers.forEach === "function" && !Array.isArray(headers)) {
            headers.forEach(function (value, key) { out[String(key).toLowerCase()] = String(value); });
        } else if (Array.isArray(headers)) {
            headers.forEach(function (pair) { out[String(pair[0]).toLowerCase()] = String(pair[1]); });
        } else {
            Object.keys(headers).forEach(function (key) { out[key.toLowerCase()] = String(headers[key]); });
        }
        delete out["content-length"];
        return out;
    }

    function notePageRequest(input, init) {
        var url = typeof input === "string" ? input : String(input && input.url || "");
        if (!/graphql/i.test(url) || !init || typeof init.body !== "string") return;
        var nexusAdapter = Sites.byScope.nexus;
        var variables = nexusAdapter.listRequest(JSON.parse(init.body));
        if (!variables) return;
        var info = nexusAdapter.listing(location);
        pageListRequest = {
            url: url,
            headers: headerObject(init.headers),
            credentials: String(init.credentials || "same-origin"),
            variables: JSON.parse(JSON.stringify(variables)),
            key: info ? info.key : ""
        };
    }

    // Watch the page's fetch calls (Firefox content scripts can wrap page
    // functions); the page itself is not changed in any other way.
    (function hookPageRequests() {
        if (!/(^|\.)nexusmods\.com$/i.test(location.hostname)) return;
        var page = window.wrappedJSObject;
        if (!page || typeof exportFunction !== "function" || typeof page.fetch !== "function") return;
        var original = page.fetch;
        page.fetch = exportFunction(function (input, init) {
            try { notePageRequest(input, init); } catch (error) { /* never break the page */ }
            return original.call(page, input, init);
        }, window);
    })();

    function apiListingItems(adapter, bf, pageNo, controller) {
        var request = pageListRequest;
        if (!request || !adapter.nextPageBody || request.key !== bf.key) return null;
        var count = Number(request.variables.count) || 0;
        if (!count) return null;
        var capturedPage = Math.floor((Number(request.variables.offset) || 0) / count) + 1;
        var template = null;
        Array.from(bf.container.children).some(function (child) {
            if (child.hasAttribute("data-aos-backfill") || child.hasAttribute("data-aos-hidden")) return false;
            var entity = child.__aosNexusEntity;
            if (!entity || entity.kind !== "mod") return false;
            template = child;
            return true;
        });
        if (!template) return null;
        var entity = template.__aosNexusEntity;
        var info = { modId: entity.modId, game: entity.game, summary: (nexusData.get(entity.key) || {}).summary || "" };
        var headers = Object.assign({}, request.headers, { "content-type": "application/json" });
        var body = JSON.stringify(adapter.nextPageBody(request.variables, pageNo - capturedPage));
        var fetcher = typeof content !== "undefined" && content && typeof content.fetch === "function"
            ? content.fetch.bind(content) : fetch;
        var options = { method: "POST", headers: headers, body: body, credentials: request.credentials };
        if (controller) options.signal = controller.signal;
        return Promise.resolve().then(function () { return fetcher(request.url, options); }).then(function (response) {
            if (!response.ok) throw new Error("HTTP " + response.status);
            return response.json();
        }).then(function (json) {
            var mods = json && json.data && json.data.mods && json.data.mods.nodes;
            if (!Array.isArray(mods)) throw new Error("no mods in response");
            var entries = [];
            for (var i = 0; i < mods.length; i += 1) {
                var tile = adapter.tileFromApi(template, info, mods[i]);
                if (!tile) throw new Error("could not copy a tile");
                cleanClone(tile);
                entries.push({ node: document.importNode(tile, true), id: adapter.apiEntityKey(mods[i]) });
            }
            bf.mode = "api";
            return entries;
        });
    }

    function fetchListingItems(adapter, url, bf, controller, pageNo) {
        var viaApi = apiListingItems(adapter, bf, pageNo, controller);
        if (viaApi) {
            return viaApi.catch(function (error) {
                if (controller && controller.signal.aborted) throw error;
                console.warn("[Agent OS] next page through the API failed; loading the page instead", error);
                return htmlListingItems(adapter, url, bf, controller);
            });
        }
        return htmlListingItems(adapter, url, bf, controller);
    }

    function htmlListingItems(adapter, url, bf, controller) {
        return pageFetch(url, controller).then(function (html) {
            if (controller && controller.signal.aborted) return [];
            var parseStarted = performance.now();
            var doc = new DOMParser().parseFromString(html, "text/html");
            var entries = collectListingItems(adapter, doc, url);
            perf.parseMs += performance.now() - parseStarted;
            bf.mode = "fetch";
            // Pages rendered in the browser only: load the page in a hidden frame.
            return entries.length ? entries : framedListingItems(adapter, url, bf);
        }, function (error) {
            if (controller && controller.signal.aborted) throw error;
            return framedListingItems(adapter, url, bf);
        });
    }

    function framedListingItems(adapter, url, bf) {
        if (!bf.loading) return Promise.resolve([]);
        bf.mode = "frame";
        return new Promise(function (resolve) {
            var frame = document.createElement("iframe");
            bf.frame = frame;
            frame.setAttribute("aria-hidden", "true");
            frame.tabIndex = -1;
            frame.style.cssText = "position:fixed!important;left:-12000px!important;top:0!important;width:1280px!important;" +
                "height:2400px!important;opacity:0!important;pointer-events:none!important;border:0!important";
            var started = Date.now();
            var last = -1;
            var stable = 0;
            function finish(entries) {
                frame.remove();
                if (bf.frame === frame) bf.frame = null;
                resolve(entries);
            }
            function poll() {
                if (!frame.isConnected) { resolve([]); return; }
                var doc = null;
                try { doc = frame.contentDocument; } catch (error) { doc = null; }
                var count = 0;
                if (doc && doc.readyState !== "loading") {
                    try { count = adapter.items(doc, doc, url).length; } catch (error) { count = 0; }
                }
                stable = count && count === last ? stable + 1 : 0;
                last = count;
                if (count && stable >= 2) { finish(collectListingItems(adapter, doc, url)); return; }
                if (Date.now() - started > 20000) { finish(count ? collectListingItems(adapter, doc, url) : []); return; }
                setTimeout(poll, 500);
            }
            frame.addEventListener("load", function () { setTimeout(poll, 300); }, { once: true });
            frame.src = url;
            (document.body || document.documentElement).appendChild(frame);
        });
    }

    // -- timing log: how long listing pages take to settle and refill -----------
    //
    // Sent to the local Agent OS bridge (source "extension-perf") so slow page
    // changes can be diagnosed from real browsing.

    var perf = newPerf("load");

    function newPerf(kind) {
        return { kind: kind, start: performance.now(), scans: 0, scanMs: 0, maxScanMs: 0, parseMs: 0,
            settledMs: 0, aborted: 0, loads: [], href: location.href };
    }

    function flushPerf(reason) {
        var listing = adapters.some(function (adapter) { return listingInfo(adapter); });
        if (!listing || (!perf.scans && !perf.loads.length)) return;
        var entry = {
            reason: reason, kind: perf.kind, href: perf.href, host: location.hostname,
            elapsed_ms: Math.round(performance.now() - perf.start), settled_ms: perf.settledMs,
            scans: perf.scans, scan_ms: Math.round(perf.scanMs), max_scan_ms: Math.round(perf.maxScanMs),
            parse_ms: Math.round(perf.parseMs), aborted: perf.aborted, loads: perf.loads,
            page_query_seen: Boolean(pageListRequest),
            hidden: hiddenCount(), backfilled: document.querySelectorAll("[data-aos-backfill]").length
        };
        try { browser.runtime.sendMessage({ type: "perf-log", entry: entry }).catch(function () {}); } catch (error) { /* closing */ }
    }

    window.addEventListener("pagehide", function () { flushPerf("pagehide"); });

    // -- page action bar: hide the author/game/category/mod of this page ----------

    var pageBarHost = null;
    var pageLookup;          // undefined: not requested; null: none; object: Nexus API data
    var titleInputOpen = false;

    function findRule(scope, field, value) {
        var probe = Core.normalizeRule({ scope: scope, field: field, value: value });
        for (var i = 0; i < state.rules.length; i += 1) {
            if (Core.sameRule(state.rules[i], probe)) return state.rules[i];
        }
        return null;
    }

    function pageBarModel() {
        var out = { actions: [], titleScope: "" };
        if (!state.enabled || !state.showInlineButtons) return out;
        adapters.forEach(function (adapter) {
            if (siteSettings(adapter).enabled === false) return;
            if (adapter.pageActions) {
                var actions = [];
                try { actions = adapter.pageActions(location, document, pageLookup || null) || []; } catch (error) { actions = []; }
                actions.forEach(function (action) {
                    if (action.lookup && pageLookup === undefined && siteSettings(adapter).lookupTags !== false) requestPageLookup(action.lookup);
                    out.actions.push(Object.assign({ scope: adapter.scope }, action));
                });
            }
            if ((adapter.listing && adapter.listing(location)) || adapter.quickHide) out.titleScope = out.titleScope || adapter.scope;
        });
        return out;
    }

    function requestPageLookup(lookup) {
        pageLookup = null;
        var href = location.href;
        browser.runtime.sendMessage({ type: "nexus-lookup", items: [lookup] }).then(function (result) {
            if (location.href !== href) return;
            var data = result && result.mods && result.mods[lookup.key];
            if (data) {
                pageLookup = data;
                renderPageBar();
            }
        }).catch(function () { /* page works without it */ });
    }

    function renderPageBar() {
        var model = pageBarModel();
        if (!model.actions.length && !model.titleScope) {
            if (pageBarHost) pageBarHost.remove();
            pageBarHost = null;
            return;
        }
        if (!pageBarHost) {
            pageBarHost = document.createElement("div");
            pageBarHost.className = "aos-pagebar-host";
            pageBarHost.attachShadow({ mode: "open" });
        }
        var shadow = pageBarHost.shadowRoot;
        shadow.textContent = "";
        var style = document.createElement("style");
        style.textContent = PAGEBAR_CSS;
        shadow.appendChild(style);
        var bar = document.createElement("div");
        bar.className = "bar";
        model.actions.forEach(function (action) {
            var rule = findRule(action.scope, action.field, action.value);
            var button = document.createElement("button");
            button.type = "button";
            button.className = rule ? "hidden" : "";
            button.textContent = rule ? "✓ Hidden: " + action.label + " · undo" : "⊘ Hide " + action.label;
            button.title = rule ? "Agent OS: show " + action.label + " again" : "Agent OS: hide " + action.label + " everywhere else";
            button.addEventListener("click", function (event) {
                event.preventDefault();
                if (rule) browser.runtime.sendMessage({ type: "filters-remove-rule", id: rule.id });
                else addRule({ scope: action.scope, field: action.field, value: action.value });
            });
            bar.appendChild(button);
        });
        if (model.titleScope) {
            if (titleInputOpen) {
                var form = document.createElement("form");
                var input = document.createElement("input");
                input.type = "text";
                input.placeholder = "Hide titles containing…";
                input.setAttribute("aria-label", "Title word or phrase to hide");
                var add = document.createElement("button");
                add.type = "submit";
                add.textContent = "Hide";
                form.append(input, add);
                form.addEventListener("submit", function (event) {
                    event.preventDefault();
                    var value = input.value.trim();
                    if (!value) return;
                    addRule({ scope: model.titleScope, field: "title", value: value });
                    input.value = "";
                    input.focus();
                });
                input.addEventListener("keydown", function (event) {
                    if (event.key === "Escape") {
                        titleInputOpen = false;
                        renderPageBar();
                    }
                    event.stopPropagation(); // keep site shortcuts (e.g. "/" for search) out
                });
                bar.appendChild(form);
                setTimeout(function () { input.focus(); }, 0);
            } else {
                var open = document.createElement("button");
                open.type = "button";
                open.textContent = "⊘ Hide a title word…";
                open.title = "Agent OS: hide items whose title contains a word or phrase";
                open.addEventListener("click", function (event) {
                    event.preventDefault();
                    titleInputOpen = true;
                    renderPageBar();
                });
                bar.appendChild(open);
            }
        }
        shadow.appendChild(bar);
        if (!pageBarHost.isConnected) document.documentElement.appendChild(pageBarHost);
    }

    var PAGEBAR_CSS = [
        ".bar{display:flex;flex-wrap:wrap;gap:6px;max-width:min(560px,calc(100vw - 28px));",
        "font:600 12px/1 system-ui,-apple-system,Segoe UI,sans-serif}",
        "button,input{font:inherit;border-radius:999px;border:1px solid #3a414b;padding:7px 11px}",
        "button{background:rgba(31,35,41,.92);color:#eef1f4;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.25)}",
        "button:hover{background:#d9534f;border-color:#d9534f}",
        "button.hidden{background:rgba(47,133,90,.92);border-color:#2f855a}",
        "button.hidden:hover{background:#4a5568;border-color:#4a5568}",
        "form{display:flex;gap:4px}",
        "input{background:#1f2329;color:#eef1f4;width:200px;outline:none}",
        "input:focus{border-color:#2d6cdf}"
    ].join("");

    // -- hide icons on an item's author / category lines --------------------------

    function ensureInlineHides(adapter, el) {
        var targets;
        try { targets = adapter.inlineHides(el) || []; } catch (error) { targets = []; }
        targets.forEach(function (spec) {
            var node = spec.node;
            if (node.getAttribute("data-aos-inline") === "1") return;
            node.setAttribute("data-aos-inline", "1");
            var icon = document.createElement("button");
            icon.type = "button";
            icon.className = spec.always ? "aos-inline-hide aos-inline-always" : "aos-inline-hide";
            icon.textContent = "⊘";
            icon.title = adapter.scope === "nexus" ? "Agent OS: hide every mod by " + spec.label : "Agent OS: hide " + spec.label;
            icon.setAttribute("aria-label", "Hide " + spec.label);
            icon.addEventListener("click", function (event) {
                event.preventDefault();
                event.stopPropagation();
                var rule = { scope: adapter.scope, field: spec.field, value: spec.value };
                addRule(rule);
                showUndoToast("Hidden " + spec.label, rule);
            }, true);
            // Inside the link keeps it on the link's own line; `after` puts it
            // right after the link instead (the link stays clickable as is).
            if (spec.after) {
                // After the capture script's hover icon for the same link, if any.
                var ref = node;
                while (ref.nextElementSibling && ref.nextElementSibling.classList.contains("agent-os-hover-icon")) ref = ref.nextElementSibling;
                ref.insertAdjacentElement("afterend", icon);
            } else {
                node.appendChild(icon);
            }
        });
    }

    // -- one-click hide + undo toast ----------------------------------------------

    var toastHost = null;
    var toastTimer = null;

    function quickHide(adapter, el, facets) {
        var rule = { scope: adapter.scope, field: "id", value: String(facets.id), label: facets.title ? "This item: " + facets.title : "" };
        addRule(rule);
        showUndoToast("Hidden " + (facets.title ? "“" + facets.title + "”" : "this item"), rule);
    }

    function showUndoToast(text, rule) {
        if (toastTimer) clearTimeout(toastTimer);
        if (!toastHost) {
            toastHost = document.createElement("div");
            toastHost.className = "aos-toast-host";
            toastHost.attachShadow({ mode: "open" });
        }
        var shadow = toastHost.shadowRoot;
        shadow.textContent = "";
        var style = document.createElement("style");
        style.textContent = ".t{display:flex;gap:12px;align-items:center;font:600 13px/1.3 system-ui,-apple-system,Segoe UI,sans-serif;" +
            "background:rgba(31,35,41,.95);color:#eef1f4;padding:9px 12px;border-radius:8px;box-shadow:0 6px 20px rgba(0,0,0,.35);max-width:min(520px,calc(100vw - 32px))}" +
            "span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}" +
            "button{font:inherit;background:none;border:0;color:#7fb2ff;cursor:pointer;padding:0}";
        var box = document.createElement("div");
        box.className = "t";
        var label = document.createElement("span");
        label.textContent = text;
        var undo = document.createElement("button");
        undo.type = "button";
        undo.textContent = "Undo";
        undo.addEventListener("click", function (event) {
            event.preventDefault();
            var saved = findRule(rule.scope, rule.field, rule.value);
            if (saved) browser.runtime.sendMessage({ type: "filters-remove-rule", id: saved.id });
            hideToast();
        });
        box.append(label, undo);
        shadow.append(style, box);
        if (!toastHost.isConnected) document.documentElement.appendChild(toastHost);
        toastTimer = setTimeout(hideToast, 6000);
    }

    function hideToast() {
        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = null;
        if (toastHost) toastHost.remove();
    }

    // -- inline hide button + popover ---------------------------------------------

    function ensureButton(adapter, el, target) {
        var host = adapter.buttonHost ? adapter.buttonHost(el) : target;
        if (!host || host.querySelector(":scope > .aos-hide-btn")) return;
        var button = document.createElement("button");
        button.type = "button";
        button.className = adapter.quickHide ? "aos-hide-btn aos-quick-hide" : "aos-hide-btn";
        button.textContent = adapter.quickHide ? "✕" : "⊘";
        button.title = adapter.quickHide ? "Agent OS: hide this (Shift+click for more options)" : "Agent OS: hide items like this";
        button.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();
            var cached = facetCache.get(el);
            var facets = effectiveFacets(adapter, cached ? cached.facets : facetsFor(adapter, el));
            if (adapter.quickHide && facets.id && !event.shiftKey) {
                quickHide(adapter, el, facets);
                return;
            }
            openPopover(button, adapter.scope, Core.hideOptionsFor(facets, adapter.scope), target);
        }, true);
        if (host === target) {
            target.classList.add("aos-overlay");
            if (getComputedStyle(target).position === "static") target.classList.add("aos-rel");
        }
        host.classList.add("aos-item");
        host.appendChild(button);
    }

    function closePopover() {
        if (popoverHost) popoverHost.remove();
        popoverHost = null;
        document.removeEventListener("click", outsideClick, true);
    }

    function outsideClick(event) {
        if (popoverHost && !popoverHost.contains(event.target)) closePopover();
    }

    function openPopover(anchor, scope, options, target) {
        closePopover();
        popoverHost = document.createElement("div");
        popoverHost.className = "aos-popover-host";
        var shadow = popoverHost.attachShadow({ mode: "open" });
        var style = document.createElement("style");
        style.textContent = POPOVER_CSS;
        shadow.appendChild(style);
        var box = document.createElement("div");
        box.className = "box";
        var heading = document.createElement("div");
        heading.className = "heading";
        heading.textContent = "Agent OS · hide";
        box.appendChild(heading);
        var list = document.createElement("div");
        list.className = "list";
        if (!options.length) {
            var none = document.createElement("div");
            none.className = "none";
            none.textContent = "Nothing to hide by on this item yet.";
            list.appendChild(none);
        }
        options.forEach(function (option) {
            var item = document.createElement("button");
            item.type = "button";
            item.textContent = option.label;
            item.addEventListener("click", function (event) {
                event.preventDefault();
                event.stopPropagation();
                addRule({ scope: scope, field: option.field, value: option.value });
                closePopover();
            });
            list.appendChild(item);
        });
        box.appendChild(list);
        var footer = document.createElement("div");
        footer.className = "footer";
        var manage = document.createElement("button");
        manage.type = "button";
        manage.textContent = "Manage filters…";
        manage.addEventListener("click", function (event) {
            event.preventDefault();
            browser.runtime.sendMessage({ type: "open-options", hash: "#rules" });
            closePopover();
        });
        footer.appendChild(manage);
        box.appendChild(footer);
        shadow.appendChild(box);
        document.documentElement.appendChild(popoverHost);
        var rect = anchor.getBoundingClientRect();
        var left = Math.min(window.innerWidth - 300, Math.max(8, rect.right - 280));
        var top = rect.bottom + 4;
        if (top + 320 > window.innerHeight) top = Math.max(8, rect.top - 324);
        popoverHost.style.left = left + "px";
        popoverHost.style.top = top + "px";
        setTimeout(function () { document.addEventListener("click", outsideClick, true); }, 0);
    }

    var POPOVER_CSS = [
        ".box{font:13px/1.35 system-ui,-apple-system,Segoe UI,sans-serif;background:#1f2329;color:#eef1f4;",
        "border:1px solid #3a414b;border-radius:8px;box-shadow:0 8px 28px rgba(0,0,0,.35);width:280px;overflow:hidden}",
        ".heading{padding:8px 10px;font-weight:600;border-bottom:1px solid #3a414b;color:#9fb3c8}",
        ".list{max-height:260px;overflow:auto;padding:4px 0}",
        "button{display:block;width:100%;text-align:left;background:none;border:0;color:inherit;font:inherit;",
        "padding:6px 10px;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
        "button:hover,button:focus{background:#2d6cdf;color:#fff;outline:none}",
        ".none{padding:8px 10px;color:#9aa4ae}",
        ".footer{border-top:1px solid #3a414b}",
        ".footer button{color:#9fb3c8}"
    ].join("");

    // -- counter / reveal ---------------------------------------------------------

    function hiddenCount() {
        return document.querySelectorAll("[data-aos-hidden]").length;
    }

    function updateCounter() {
        var count = hiddenCount();
        if (!state.showCounter || !count || !document.body) {
            if (counterEl) counterEl.remove();
            counterEl = null;
            return;
        }
        if (!counterEl) {
            counterEl = document.createElement("button");
            counterEl.type = "button";
            counterEl.className = "aos-counter";
            counterEl.title = "Agent OS filters: click to show or re-hide filtered items";
            counterEl.addEventListener("click", function (event) {
                event.preventDefault();
                setReveal(!reveal);
            });
        }
        if (!counterEl.isConnected) document.body.appendChild(counterEl);
        var label = (reveal ? "👁 " : "⊘ ") + count + " hidden" + (reveal ? " · showing" : "");
        if (counterEl.textContent !== label) counterEl.textContent = label;
    }

    function setReveal(value) {
        reveal = Boolean(value);
        document.documentElement.toggleAttribute("data-aos-reveal", reveal);
        updateCounter();
    }

    // Clicking a revealed item's reason label removes the rule that hid it.
    document.addEventListener("click", function (event) {
        if (!reveal) return;
        var target = event.target;
        if (!(target instanceof Element)) return;
        var hidden = target.closest("[data-aos-hidden]");
        if (!hidden) return;
        var rect = hidden.getBoundingClientRect();
        // The ::before label occupies the top strip of the item.
        if (event.clientY - rect.top > 22) return;
        var ruleId = hidden.getAttribute("data-aos-rule");
        if (!ruleId) return;
        event.preventDefault();
        event.stopPropagation();
        browser.runtime.sendMessage({ type: "filters-remove-rule", id: ruleId });
    }, true);

    // -- rule changes -------------------------------------------------------------

    function addRule(rule) {
        return browser.runtime.sendMessage({ type: "filters-add-rule", rule: rule });
    }

    browser.storage.onChanged.addListener(function (changes, area) {
        if (area !== "local" || !changes[Core.STORAGE_KEY]) return;
        state = Core.normalizeState(changes[Core.STORAGE_KEY].newValue);
        compiled = Core.compileRules(state);
        refreshAdapters();
        if (!state.showInlineButtons) {
            document.querySelectorAll(".aos-hide-btn").forEach(function (b) { b.remove(); });
        }
        if (adapters.length && !started) start();
        reevaluateAll();
        renderPageBar();
    });

    // -- context menu + popup messaging -------------------------------------------

    document.addEventListener("contextmenu", function (event) {
        var target = event.target instanceof Element ? event.target : null;
        lastContext = { item: null, adapter: null, link: null };
        if (!target) return;
        var link = target.closest("a[href]");
        if (link) lastContext.link = { href: link.href, text: link.textContent };
        for (var i = 0; i < adapters.length; i += 1) {
            var adapter = adapters[i];
            var items;
            try { items = adapter.items(document, document); } catch (error) { items = []; }
            for (var j = 0; j < items.length; j += 1) {
                var el = items[j];
                var t = targetFor(adapter, el);
                if (el.contains(target) || t.contains(target)) {
                    lastContext.item = el;
                    lastContext.adapter = adapter;
                    return;
                }
            }
        }
    }, true);

    function contextOptions() {
        var out = [];
        if (!lastContext) return out;
        if (lastContext.item && lastContext.adapter) {
            var adapter = lastContext.adapter;
            var facets = effectiveFacets(adapter, facetsFor(adapter, lastContext.item));
            Core.hideOptionsFor(facets, adapter.scope).forEach(function (option) {
                out.push(Object.assign({ scope: adapter.scope }, option));
            });
        }
        if (lastContext.link) {
            Sites.linkHideOptions(lastContext.link.href, lastContext.link.text, location.href).forEach(function (option) {
                if (!out.some(function (o) { return o.scope === option.scope && o.field === option.field && o.value.toLowerCase() === option.value.toLowerCase(); })) {
                    out.push(option);
                }
            });
        }
        return out.slice(0, 30);
    }

    browser.runtime.onMessage.addListener(function (message) {
        if (!message || typeof message !== "object") return undefined;
        if (message.type === "filters-context-options") {
            return Promise.resolve({ options: contextOptions() });
        }
        if (message.type === "filters-page-stats") {
            var reasons = {};
            document.querySelectorAll("[data-aos-hidden]").forEach(function (el) {
                var reason = el.getAttribute("data-aos-reason") || "rule";
                reasons[reason] = (reasons[reason] || 0) + 1;
            });
            return Promise.resolve({
                scopes: adapters.map(function (a) { return a.scope; }),
                hidden: hiddenCount(),
                items: processed.size,
                reveal: reveal,
                reasons: reasons
            });
        }
        if (message.type === "filters-set-reveal") {
            setReveal(message.reveal);
            return Promise.resolve({ reveal: reveal });
        }
        return undefined;
    });

    // -- startup ------------------------------------------------------------------

    function start() {
        if (started) return;
        started = true;
        var observer = new MutationObserver(function () { scheduleScan(); });
        observer.observe(document.documentElement, { childList: true, subtree: true });
        scheduleScan(0);
        renderPageBar();
        window.addEventListener("popstate", function () { scheduleScan(0); });
    }

    loadState().then(function () {
        refreshAdapters();
        if (adapters.length) start();
        // XenForo is detected from <html id="XF">, so re-check once parsed.
        document.addEventListener("DOMContentLoaded", function () {
            refreshAdapters();
            if (adapters.length) start();
            scheduleScan(0);
            renderPageBar();
        });
    });
})();
