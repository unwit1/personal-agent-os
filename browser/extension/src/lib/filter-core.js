/*
 * Agent OS content filters: rule model and matching.
 *
 * Shared by the background page, content scripts, the options page and the
 * Node test suite, so it must stay free of DOM and WebExtension APIs.
 */
(function (root, factory) {
    "use strict";
    if (typeof module === "object" && module.exports) {
        module.exports = factory();
    } else {
        root.AgentOsFilterCore = factory();
    }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";

    var STORAGE_KEY = "agent_os_filters_v1";

    // Facet fields a rule can target. "keyword" searches title + text.
    var FIELDS = {
        subreddit: { label: "Subreddit", prefix: "r/" },
        author: { label: "Author / user", prefix: "" },
        domain: { label: "Domain", prefix: "" },
        flair: { label: "Flair", prefix: "" },
        keyword: { label: "Keyword (title/summary)", prefix: "" },
        title: { label: "Title term", prefix: "" },
        tag: { label: "Tag", prefix: "" },
        fandom: { label: "Fandom", prefix: "" },
        category: { label: "Category", prefix: "" },
        game: { label: "Game", prefix: "" },
        rating: { label: "Rating", prefix: "" },
        language: { label: "Language", prefix: "" },
        channel: { label: "Channel", prefix: "" },
        prefix: { label: "Thread prefix", prefix: "" },
        forum: { label: "Forum / board", prefix: "" },
        id: { label: "Specific item", prefix: "" }
    };

    var SCOPES = {
        "*": "All sites",
        reddit: "Reddit",
        nexus: "Nexus Mods",
        ao3: "AO3",
        xenforo: "XenForo forums (SpaceBattles, SV, QQ, ...)",
        ffn: "FanFiction.net",
        youtube: "YouTube",
        steam: "Steam Workshop",
        search: "Search engines",
        amazon: "Amazon",
        custom: "Custom sites"
    };

    var DEFAULT_SITE_SETTINGS = {
        reddit: { enabled: true, hidePromoted: true, hideNsfw: false },
        nexus: { enabled: true, hideAdult: false, hideTranslations: true, lookupTags: true, fillFromNextPage: true },
        ao3: { enabled: true, maxFandoms: 0, minWords: 0, hideWip: false },
        xenforo: { enabled: true, hidePostsByAuthor: true },
        ffn: { enabled: true, minWords: 0, hideWip: false },
        youtube: { enabled: true, hideShorts: false },
        steam: { enabled: true },
        search: { enabled: true },
        amazon: { enabled: true, hideSponsored: false },
        custom: { enabled: true }
    };

    var DEFAULT_STATE = {
        version: 1,
        enabled: true,
        hiddenStyle: "remove", // "remove" | "collapse"
        showInlineButtons: true,
        showCounter: true,
        syncToAgentOs: true,
        redirects: { oldReddit: true },
        sites: DEFAULT_SITE_SETTINGS,
        customSites: [],
        rules: []
    };

    function clone(value) {
        return JSON.parse(JSON.stringify(value));
    }

    function normalizeState(raw) {
        var state = Object.assign(clone(DEFAULT_STATE), raw && typeof raw === "object" ? raw : {});
        var sites = clone(DEFAULT_SITE_SETTINGS);
        var savedSites = raw && raw.sites && typeof raw.sites === "object" ? raw.sites : {};
        Object.keys(sites).forEach(function (key) {
            sites[key] = Object.assign(sites[key], savedSites[key] || {});
        });
        state.sites = sites;
        state.redirects = Object.assign(clone(DEFAULT_STATE.redirects), raw && raw.redirects || {});
        state.rules = Array.isArray(state.rules) ? state.rules.filter(validRule).map(normalizeRule) : [];
        state.customSites = Array.isArray(state.customSites) ? state.customSites : [];
        return state;
    }

    function validRule(rule) {
        return rule && typeof rule === "object" && FIELDS[rule.field] &&
            typeof rule.value === "string" && rule.value.trim();
    }

    function normalizeValue(field, value) {
        var text = String(value == null ? "" : value).trim();
        if (field === "subreddit") text = text.replace(/^\/?r\//i, "");
        if (field === "author") text = text.replace(/^\/?u(ser)?\//i, "").replace(/^@/, "");
        if (field === "channel") text = text.replace(/^@/, "");
        if (field === "domain") text = text.replace(/^https?:\/\//i, "").replace(/^www\./i, "").replace(/\/.*$/, "");
        return text;
    }

    function ruleId() {
        return "r" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
    }

    function normalizeRule(rule) {
        var out = {
            id: rule.id || ruleId(),
            scope: SCOPES[rule.scope] ? rule.scope : "*",
            field: rule.field,
            value: normalizeValue(rule.field, rule.value),
            host: rule.host ? String(rule.host).trim().toLowerCase().replace(/^www\./, "") : "",
            enabled: rule.enabled !== false,
            note: rule.note ? String(rule.note) : "",
            label: rule.label ? String(rule.label) : "",
            createdAt: rule.createdAt || new Date().toISOString()
        };
        return out;
    }

    function makeRule(scope, field, value, extra) {
        return normalizeRule(Object.assign({ scope: scope, field: field, value: value }, extra || {}));
    }

    function sameRule(a, b) {
        return a.scope === b.scope && a.field === b.field && (a.host || "") === (b.host || "") &&
            a.value.toLowerCase() === b.value.toLowerCase();
    }

    function addRule(state, rule) {
        var normalized = normalizeRule(rule);
        var exists = state.rules.some(function (item) { return sameRule(item, normalized); });
        if (!exists) state.rules.push(normalized);
        return !exists;
    }

    // -- pattern compilation ---------------------------------------------------

    function escapeRegex(text) {
        return text.replace(/[.+?^${}()|[\]\\]/g, "\\$&");
    }

    // A value is a regex when written /like this/i; otherwise "*" is a
    // wildcard. Keywords match anywhere; every other field matches the
    // whole value (so "skyrim*" matches "skyrimmods" but "skyrim" does not).
    function compileMatcher(rule) {
        var value = rule.value;
        var regexMatch = value.match(/^\/(.+)\/([a-z]*)$/i);
        if (regexMatch) {
            try {
                var re = new RegExp(regexMatch[1], regexMatch[2].indexOf("i") === -1 ? regexMatch[2] + "i" : regexMatch[2]);
                return function (candidate) { return re.test(candidate); };
            } catch (error) {
                return function () { return false; };
            }
        }
        var lowered = value.toLowerCase();
        if (rule.field === "keyword" || rule.field === "title") {
            if (lowered.indexOf("*") === -1) {
                // Whole-word-ish containment so "elf" does not hide "self".
                var wordRe = new RegExp("(^|[^a-z0-9])" + escapeRegex(lowered) + "($|[^a-z0-9])", "i");
                return function (candidate) { return wordRe.test(candidate); };
            }
            var kwRe = new RegExp(escapeRegex(lowered).replace(/\\\*/g, "*").replace(/\*/g, ".*"), "i");
            return function (candidate) { return kwRe.test(candidate); };
        }
        if (rule.field === "domain") {
            if (lowered.indexOf("*") === -1) {
                return function (candidate) {
                    var host = String(candidate).toLowerCase().replace(/^www\./, "");
                    return host === lowered || host.slice(-(lowered.length + 1)) === "." + lowered;
                };
            }
        }
        if (lowered.indexOf("*") !== -1) {
            var globRe = new RegExp("^" + escapeRegex(lowered).replace(/\\\*/g, "*").replace(/\*/g, ".*") + "$", "i");
            return function (candidate) { return globRe.test(String(candidate)); };
        }
        return function (candidate) { return String(candidate).toLowerCase() === lowered; };
    }

    function hostMatches(ruleHost, host) {
        if (!ruleHost) return true;
        var h = String(host || "").toLowerCase().replace(/^www\./, "");
        return h === ruleHost || h.slice(-(ruleHost.length + 1)) === "." + ruleHost;
    }

    function compileRules(state) {
        return (state.rules || []).filter(function (rule) { return rule.enabled !== false; })
            .map(function (rule) {
                return { rule: rule, test: compileMatcher(rule) };
            });
    }

    function asList(value) {
        if (value == null || value === "") return [];
        return Array.isArray(value) ? value.filter(function (v) { return v != null && v !== ""; }) : [value];
    }

    function candidatesFor(field, facets) {
        if (field === "keyword") {
            return asList(facets.title).concat(asList(facets.text));
        }
        if (field === "title") return asList(facets.title);
        if (field === "tag") {
            // Ratings, warnings and categories are tags too on AO3 and Nexus.
            return asList(facets.tag).concat(asList(facets.warning), asList(facets.rating), asList(facets.category));
        }
        if (field === "author") return asList(facets.author);
        if (field === "game") return asList(facets.game).concat(asList(facets.gameName));
        return asList(facets[field]);
    }

    /*
     * Returns the first matching rule (or synthetic site-setting reason) for
     * an item, or null. `context` carries the scope, host and per-page
     * exemptions such as the subreddit currently being browsed.
     */
    function evaluate(compiled, facets, context) {
        var scope = context.scope;
        var host = context.host;
        var exempt = context.exempt || {};
        for (var i = 0; i < compiled.length; i += 1) {
            var entry = compiled[i];
            var rule = entry.rule;
            if (rule.scope !== "*" && rule.scope !== scope) continue;
            if (!hostMatches(rule.host, host)) continue;
            if (rule.field === "id" && rule.scope === "*") continue;
            var candidates = candidatesFor(rule.field, facets);
            // Browsing r/foo, a user's page or a game's section shows that
            // thing's own items even when it is hidden elsewhere.
            if (exempt[rule.field]) {
                var exemptValue = String(exempt[rule.field]).toLowerCase();
                if (candidates.some(function (c) { return String(c).toLowerCase() === exemptValue; })) continue;
            }
            for (var j = 0; j < candidates.length; j += 1) {
                var candidate = String(candidates[j]);
                if (entry.test(candidate)) {
                    return { rule: rule, matched: candidate, reason: describeRule(rule) };
                }
            }
        }
        var settingReason = evaluateSiteSettings(context.siteSettings || {}, facets, scope);
        if (settingReason) return { rule: null, matched: "", reason: settingReason };
        return null;
    }

    function evaluateSiteSettings(settings, facets, scope) {
        if (settings.hidePromoted && facets.promoted) return "Promoted post";
        if (settings.hideSponsored && facets.promoted) return "Sponsored result";
        if (settings.hideNsfw && facets.nsfw) return "NSFW";
        if (settings.hideAdult && facets.nsfw) return "Adult content";
        if (settings.hideShorts && facets.short) return "YouTube Short";
        if (settings.hideTranslations && facets.translation) return "Translation" + (facets.translation === true ? "" : " (" + facets.translation + ")");
        if (settings.maxFandoms && facets.fandomCount > Number(settings.maxFandoms)) {
            return "More than " + settings.maxFandoms + " fandoms";
        }
        if (settings.minWords && facets.words != null && facets.words < Number(settings.minWords)) {
            return "Under " + settings.minWords + " words";
        }
        if (settings.hideWip && facets.complete === false) return "Work in progress";
        return "";
    }

    function describeRule(rule) {
        var field = FIELDS[rule.field] || { label: rule.field, prefix: "" };
        if (rule.label) return rule.label;
        var value = rule.field === "subreddit" ? "r/" + rule.value : rule.value;
        return field.label + ": " + value + (rule.host ? " (" + rule.host + ")" : "");
    }

    // Options offered by the inline "hide" menu for one item.
    function hideOptionsFor(facets, scope) {
        var out = [];
        function push(field, values, labelPrefix) {
            asList(values).forEach(function (value) {
                var text = String(value).trim();
                if (!text) return;
                if (out.some(function (o) { return o.field === field && o.value.toLowerCase() === text.toLowerCase(); })) return;
                out.push({ field: field, value: text, label: labelPrefix + text });
            });
        }
        push("subreddit", facets.subreddit, "Hide r/");
        push("author", facets.author, scope === "youtube" ? "Hide channel " : "Hide author ");
        push("channel", facets.channel, "Hide channel ");
        push("game", facets.game, "Hide game ");
        push("category", facets.category, "Hide category ");
        push("fandom", facets.fandom, "Hide fandom ");
        push("forum", facets.forum, "Hide forum ");
        push("prefix", facets.prefix, "Hide prefix ");
        push("flair", facets.flair, "Hide flair ");
        push("language", facets.language, "Hide language ");
        push("domain", facets.domain, "Hide domain ");
        push("rating", facets.rating, "Hide rating ");
        push("tag", facets.warning, "Hide warning ");
        push("tag", facets.tag, "Hide tag ");
        if (facets.id) {
            out.push({ field: "id", value: String(facets.id), label: "Hide just this item" });
        }
        return out;
    }

    function parseCount(text) {
        if (text == null) return null;
        var match = String(text).replace(/,/g, "").match(/([\d.]+)\s*([kKmM]?)/);
        if (!match) return null;
        var n = parseFloat(match[1]);
        if (match[2] === "k" || match[2] === "K") n *= 1000;
        if (match[2] === "m" || match[2] === "M") n *= 1000000;
        return Math.round(n);
    }

    // Accepts our export format, a Reddit Subreddit Hider list, or plain
    // newline/comma separated subreddit names.
    function importRules(state, input, defaults) {
        var added = 0;
        var parsed = null;
        if (typeof input === "string") {
            var trimmed = input.trim();
            if (/^[[{]/.test(trimmed)) {
                try { parsed = JSON.parse(trimmed); } catch (error) { parsed = null; }
            }
            if (parsed == null) {
                trimmed.split(/[\n,]+/).forEach(function (line) {
                    var value = line.trim();
                    if (!value) return;
                    if (addRule(state, makeRule(defaults && defaults.scope || "reddit", defaults && defaults.field || "subreddit", value))) added += 1;
                });
                return added;
            }
        } else {
            parsed = input;
        }
        if (Array.isArray(parsed)) {
            parsed.forEach(function (item) {
                if (typeof item === "string") {
                    if (addRule(state, makeRule(defaults && defaults.scope || "reddit", defaults && defaults.field || "subreddit", item))) added += 1;
                } else if (validRule(item)) {
                    if (addRule(state, item)) added += 1;
                }
            });
            return added;
        }
        if (parsed && typeof parsed === "object") {
            if (Array.isArray(parsed.rules)) added += importRules(state, parsed.rules, defaults);
            if (Array.isArray(parsed.blockedSubreddits)) {
                parsed.blockedSubreddits.forEach(function (v) { if (addRule(state, makeRule("reddit", "subreddit", v))) added += 1; });
            }
            if (Array.isArray(parsed.blockedKeywords)) {
                parsed.blockedKeywords.forEach(function (v) { if (addRule(state, makeRule("reddit", "keyword", v))) added += 1; });
            }
            if (parsed.sites && typeof parsed.sites === "object") {
                Object.keys(parsed.sites).forEach(function (key) {
                    if (state.sites[key]) Object.assign(state.sites[key], parsed.sites[key]);
                });
            }
            if (Array.isArray(parsed.customSites)) {
                parsed.customSites.forEach(function (site) {
                    if (site && site.host && site.itemSelector) state.customSites.push(site);
                });
            }
        }
        return added;
    }

    return {
        STORAGE_KEY: STORAGE_KEY,
        FIELDS: FIELDS,
        SCOPES: SCOPES,
        DEFAULT_STATE: DEFAULT_STATE,
        normalizeState: normalizeState,
        normalizeRule: normalizeRule,
        normalizeValue: normalizeValue,
        makeRule: makeRule,
        addRule: addRule,
        sameRule: sameRule,
        compileRules: compileRules,
        compileMatcher: compileMatcher,
        evaluate: evaluate,
        describeRule: describeRule,
        hideOptionsFor: hideOptionsFor,
        parseCount: parseCount,
        importRules: importRules,
        hostMatches: hostMatches
    };
});
