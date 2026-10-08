/*
 * Agent OS content filters: per-site adapters.
 *
 * Each adapter finds the hideable items on a page and extracts "facets"
 * (subreddit, author, tags, ...) that filter-core rules match against.
 * Adapters only read the DOM; hiding is done by content/filter.js.
 */
(function (root, factory) {
    "use strict";
    if (typeof module === "object" && module.exports) {
        module.exports = factory();
    } else {
        root.AgentOsSites = factory();
    }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";

    function clean(value) {
        return String(value == null ? "" : value).replace(/\s+/g, " ").trim();
    }

    function text(el, selector) {
        if (!el) return "";
        var node = selector ? el.querySelector(selector) : el;
        return node ? clean(node.textContent) : "";
    }

    function texts(el, selector, limit) {
        var out = [];
        if (!el) return out;
        el.querySelectorAll(selector).forEach(function (node) {
            var value = clean(node.textContent);
            if (value && out.indexOf(value) === -1) out.push(value);
        });
        return limit ? out.slice(0, limit) : out;
    }

    function parseUrl(href, base) {
        try {
            return new URL(href, base || "https://invalid.local/");
        } catch (error) {
            return null;
        }
    }

    function hostOf(href, base) {
        var u = parseUrl(href, base);
        return u ? u.hostname.toLowerCase().replace(/^www\./, "") : "";
    }

    function hostIs(host, domain) {
        host = String(host || "").toLowerCase();
        return host === domain || host.slice(-(domain.length + 1)) === "." + domain;
    }

    function parseCount(value) {
        if (value == null || value === "") return null;
        var match = String(value).replace(/,/g, "").match(/([\d.]+)\s*([kKmM]?)/);
        if (!match) return null;
        var n = parseFloat(match[1]);
        if (/k/i.test(match[2])) n *= 1000;
        if (/m/i.test(match[2])) n *= 1000000;
        return Math.round(n);
    }

    // Outermost matches only, so nested renderers are not handled twice.
    function outermost(nodes, selector) {
        return Array.from(nodes).filter(function (node) {
            var parent = node.parentElement;
            return !(parent && parent.closest && parent.closest(selector));
        });
    }

    // -- Reddit -------------------------------------------------------------------

    var REDDIT_ITEMS = [
        "shreddit-post",
        "shreddit-ad-post",
        "shreddit-comment",
        ".thing.link",
        ".thing.comment",
        "[data-testid='search-post-unit']"
    ].join(",");

    var reddit = {
        scope: "reddit",
        matches: function (loc) { return hostIs(loc.hostname, "reddit.com"); },
        // "Hide subreddit" sits next to the subreddit name on every post.
        inlineHides: function (el) {
            if (el.tagName !== "SHREDDIT-POST" && !(el.classList.contains("thing") && el.classList.contains("link"))) return [];
            var out = [];
            el.querySelectorAll("a.subreddit, a[href^='/r/'], a[href*='reddit.com/r/']").forEach(function (a) {
                var m = String(a.getAttribute("href") || "").match(/\/r\/([^/?#]+)\/?$/i);
                if (!m || /^(all|popular)$/i.test(m[1]) || !clean(a.textContent)) return;
                if (out.some(function (o) { return o.value.toLowerCase() === m[1].toLowerCase(); })) return;
                out.push({ node: a, field: "subreddit", value: m[1], label: "r/" + m[1], always: true, after: true });
            });
            return out;
        },
        items: function (root) { return Array.from(root.querySelectorAll(REDDIT_ITEMS)); },
        target: function (el) {
            if (/^SHREDDIT-(AD-)?POST$/.test(el.tagName)) {
                var article = el.parentElement && el.parentElement.closest("article");
                if (article && article.querySelectorAll("shreddit-post, shreddit-ad-post").length === 1) return article;
            }
            return el;
        },
        kind: function (el) {
            return el.tagName === "SHREDDIT-COMMENT" || (el.classList && el.classList.contains("comment")) ? "comment" : "post";
        },
        facets: function (el) {
            var tag = el.tagName;
            if (tag === "SHREDDIT-COMMENT") {
                return {
                    author: el.getAttribute("author") || "",
                    id: el.getAttribute("thingid") || ""
                };
            }
            if (el.classList.contains("comment")) {
                return {
                    author: el.getAttribute("data-author") || "",
                    id: el.getAttribute("data-fullname") || ""
                };
            }
            if (tag === "SHREDDIT-POST" || tag === "SHREDDIT-AD-POST") {
                var sub = (el.getAttribute("subreddit-prefixed-name") || el.getAttribute("subreddit-name") || "")
                    .replace(/^r\//i, "");
                var domain = el.getAttribute("domain") || hostOf(el.getAttribute("content-href") || "");
                var body = text(el, "[slot='text-body']") || texts(el, "p", 6).join(" ");
                return {
                    subreddit: sub,
                    author: el.getAttribute("author") || "",
                    title: el.getAttribute("post-title") || text(el, "[slot='title']"),
                    text: body,
                    domain: /^self\./i.test(domain) || hostIs(domain, "reddit.com") || hostIs(domain, "redd.it") ? "" : domain,
                    flair: texts(el, "shreddit-post-flair, [slot='post-flair'], flair-tag", 3),
                    nsfw: el.hasAttribute("nsfw") || el.getAttribute("is-nsfw") === "true",
                    promoted: tag === "SHREDDIT-AD-POST" || el.hasAttribute("promoted"),
                    id: el.getAttribute("id") || el.getAttribute("permalink") || ""
                };
            }
            if (el.classList.contains("thing")) {
                var oldDomain = el.getAttribute("data-domain") || "";
                return {
                    subreddit: el.getAttribute("data-subreddit") || "",
                    author: el.getAttribute("data-author") || "",
                    title: text(el, "a.title"),
                    text: text(el, ".usertext-body .md"),
                    domain: /^self\./i.test(oldDomain) || hostIs(oldDomain, "reddit.com") || hostIs(oldDomain, "redd.it") ? "" : oldDomain,
                    flair: texts(el, ".linkflairlabel", 3),
                    nsfw: el.getAttribute("data-nsfw") === "true" || el.classList.contains("over18"),
                    promoted: el.getAttribute("data-promoted") === "true" || el.classList.contains("promoted"),
                    id: el.getAttribute("data-fullname") || ""
                };
            }
            // Search results unit.
            var subLink = el.querySelector("a[href^='/r/']");
            var subMatch = subLink && subLink.getAttribute("href").match(/^\/r\/([^/]+)/);
            return {
                subreddit: subMatch ? subMatch[1] : "",
                title: text(el, "[data-testid='post-title-text'], [data-testid='post-title'], h3"),
                id: (el.querySelector("a[href*='/comments/']") || {}).href || ""
            };
        },
        exempt: function (loc) {
            var sub = loc.pathname.match(/^\/r\/([^/]+)/i);
            var user = loc.pathname.match(/^\/(?:u|user)\/([^/]+)/i);
            var out = {};
            if (sub && !/^(all|popular)$/i.test(sub[1])) out.subreddit = sub[1];
            if (user) out.author = user[1];
            return out;
        }
    };

    // -- Nexus Mods ---------------------------------------------------------------

    var NEXUS_MOD_RE = /^\/(?:games\/)?([a-z0-9_-]+)\/mods\/(\d+)\/?$/i;
    var NEXUS_COLLECTION_RE = /^\/(?:games\/)?([a-z0-9_-]+)\/collections\/([a-z0-9_-]+)\/?$/i;
    var NEXUS_TILE_SELECTOR = [
        "[data-e2e-id='mod-tile']",
        "[data-e2e-id='collection-tile']",
        "[data-testid='mod-tile']",
        ".mod-tile",
        "li.mod-tile",
        "[class*='mod-tile']",
        "[class*='collection-tile']"
    ].join(",");
    var NEXUS_EXCLUDED_AREAS = "header, nav, footer, #description, .mod_description_container, " +
        "[class*='description'], .comment, [class*='comment'], .forum, [class*='changelog'], .bbcode";

    // Translation detection: Nexus's own "Translation" tag, a translations
    // category, translated-title wording, or language tags without English.
    var TRANSLATION_WORDS = /(?:^|[^a-z])(translations?|translated|traduction|traducci[oó]n|tradu[cç][aã]o|traduzione|[üu]bersetzung|vertaling|t[łl]umaczenie|spolszczenie|p[řr]eklad|ford[ií]t[aá]s|[çc]eviri|localization|localisation)(?:$|[^a-z])|перевод|русификац|переклад|українізац|локализац|汉化|漢化|中文|简体|繁體|日本語化|日本語訳|한글|한국어\s*패치/i;
    var LANGUAGE_TITLE = /(?:^|[\s\-–—|(\[])(Deutsch|Español|Espanol|Français|Francais|Italiano|Polski|Português|Portugues|PT-?BR|Русский|Українська|Čeština|Cestina|Magyar|Türkçe|Turkce|Nederlands|Svenska|简体中文|繁體中文|日本語|한국어|ภาษาไทย|Tiếng Việt)(?:$|[\s\-–—|)\]])/i;
    var LANGUAGE_TAGS = ["russian", "german", "french", "spanish", "italian", "polish", "portuguese", "brazilian portuguese",
        "chinese", "simplified chinese", "traditional chinese", "japanese", "korean", "czech", "turkish", "hungarian",
        "ukrainian", "dutch", "swedish", "thai", "vietnamese", "romanian", "greek", "finnish", "danish", "norwegian"];

    function nexusTranslation(title, tags, categories) {
        var lowerTags = (tags || []).map(function (t) { return String(t).toLowerCase(); });
        if (lowerTags.some(function (t) { return /^translations?$/.test(t); })) return true;
        if ((categories || []).some(function (c) { return /translat/i.test(c); })) return true;
        var titleText = String(title || "");
        if (TRANSLATION_WORDS.test(titleText)) return true;
        var lang = titleText.match(LANGUAGE_TITLE);
        if (lang) return lang[1];
        var languages = lowerTags.filter(function (t) { return LANGUAGE_TAGS.indexOf(t) !== -1; });
        if (languages.length && lowerTags.indexOf("english") === -1) {
            return languages[0].replace(/(^|\s)([a-z])/g, function (m, space, c) { return space + c.toUpperCase(); });
        }
        return false;
    }

    function nexusEntityFromHref(href, base) {
        var u = parseUrl(href, base);
        if (!u || !hostIs(u.hostname, "nexusmods.com")) return null;
        var mod = u.pathname.match(NEXUS_MOD_RE);
        if (mod && mod[1].toLowerCase() !== "games") {
            return { kind: "mod", game: mod[1].toLowerCase(), modId: mod[2], key: mod[1].toLowerCase() + ":" + mod[2] };
        }
        var col = u.pathname.match(NEXUS_COLLECTION_RE);
        if (col && col[1].toLowerCase() !== "games") {
            return { kind: "collection", game: col[1].toLowerCase(), slug: col[2], key: "collection:" + col[2] };
        }
        return null;
    }

    function nexusCurrentEntity(loc) {
        return nexusEntityFromHref(loc.href, loc.href);
    }

    var NEXUS_RESERVED = /^(games|users|profile|mods|collections|search|about|news|settings|media|images|videos|account|premium|support)$/i;

    // Author from a profile URL: /profile/<name> (current) or /users/<id> (legacy, no name).
    function nexusProfileName(pathname) {
        var m = String(pathname || "").match(/^\/profile\/([^/?#]+)/i);
        if (!m) return "";
        try { return decodeURIComponent(m[1]); } catch (error) { return m[1]; }
    }

    function nexusGameFromPath(pathname) {
        var m = String(pathname || "").match(/^\/games\/([a-z0-9_-]+)(?:\/|$)/i) ||
            String(pathname || "").match(/^\/([a-z0-9_-]+)(?:\/(?:mods\/?)?)?$/i);
        return m && !NEXUS_RESERVED.test(m[1]) ? m[1].toLowerCase() : "";
    }

    function nexusGameName(doc, game) {
        if (!doc || !game) return game;
        var links = doc.querySelectorAll("a[href$='/games/" + game + "'], a[href$='/games/" + game + "/']");
        for (var i = 0; i < links.length; i += 1) {
            var name = clean(links[i].textContent);
            if (name && name.length < 80) return name;
        }
        return game;
    }

    // Climb from a link to the largest ancestor that still refers to one
    // entity only. That is the tile, whatever Nexus's current markup is.
    function nexusCardFor(link, entity, doc, base) {
        var known = link.closest(NEXUS_TILE_SELECTOR);
        if (known) return known;
        var el = link;
        var depth = 0;
        while (el.parentElement && depth < 8) {
            var parent = el.parentElement;
            if (parent === doc.body || parent === doc.documentElement || parent.tagName === "MAIN") break;
            if (parent.querySelector("h1")) break;
            var other = false;
            var links = parent.querySelectorAll("a[href*='/mods/'], a[href*='/collections/']");
            for (var i = 0; i < links.length; i += 1) {
                var e = nexusEntityFromHref(links[i].getAttribute("href"), base);
                if (e && e.key !== entity.key) { other = true; break; }
            }
            if (other) break;
            el = parent;
            depth += 1;
        }
        if (el === link || !el.querySelector("img")) return null;
        return el;
    }

    // -- Nexus listing pages through the API ---------------------------------
    //
    // The mod list is rendered in the browser from a GraphQL `mods` query.
    // Replaying the page's own query (its filter, sort and page size) with a
    // later offset gives the next page in about half a second; tiles for it
    // are built by copying a tile that is already on the page.

    var NEXUS_MODS_QUERY = "query AgentOsNextPage($filter: ModsFilter, $postFilter: ModsFilter, " +
        "$sort: [ModsSort!], $offset: Int, $count: Int, $viewUserBlockedContent: Boolean, $viewUploaderHidden: Boolean) { " +
        "mods(filter: $filter, postFilter: $postFilter, sort: $sort, offset: $offset, count: $count, " +
        "viewUserBlockedContent: $viewUserBlockedContent, viewUploaderHidden: $viewUploaderHidden) { totalCount nodes { " +
        "modId name summary author uploader { name avatar } modCategory { name } game { domainName } thumbnailUrl " +
        "adultContent endorsements downloads fileSize updatedAt createdAt } } }";
    var NEXUS_QUERY_VARIABLES = ["filter", "postFilter", "sort", "offset", "count", "viewUserBlockedContent", "viewUploaderHidden"];

    // Variables of the page's own mod-list query, from a GraphQL request body.
    function nexusListRequest(body) {
        var ops = Array.isArray(body) ? body : [body];
        for (var i = 0; i < ops.length; i += 1) {
            var op = ops[i];
            if (!op || typeof op.query !== "string" || !/\bmods\s*\(/.test(op.query)) continue;
            var vars = op.variables || {};
            if (typeof vars.count !== "number" && typeof vars.offset !== "number") continue;
            return vars;
        }
        return null;
    }

    function nexusNextPageBody(variables, pagesAhead) {
        var vars = {};
        NEXUS_QUERY_VARIABLES.forEach(function (key) { if (variables[key] !== undefined) vars[key] = variables[key]; });
        var count = Number(vars.count) || 20;
        vars.count = count;
        vars.offset = (Number(vars.offset) || 0) + count * pagesAhead;
        return { operationName: "AgentOsNextPage", query: NEXUS_MODS_QUERY, variables: vars };
    }

    function nexusCount(n) {
        n = Number(n) || 0;
        if (n < 1000) return String(n);
        if (n < 100000) return (n / 1000).toFixed(1) + "k";
        if (n < 1000000) return Math.round(n / 1000) + "k";
        return (n / 1000000).toFixed(1) + "M";
    }

    function nexusSize(kb) {
        kb = Number(kb) || 0;
        if (!kb) return "0B";
        if (kb < 1024) return kb.toFixed(1) + "KB";
        if (kb < 1024 * 1024) return (kb / 1024).toFixed(1) + "MB";
        return (kb / 1024 / 1024).toFixed(1) + "GB";
    }

    var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"];

    function nexusDate(iso) {
        var d = new Date(iso);
        return isNaN(d.getTime()) ? "" : d.getUTCDate() + " " + MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear();
    }

    function nexusAgo(iso) {
        var d = new Date(iso);
        if (isNaN(d.getTime())) return "";
        var s = Math.max(0, (Date.now() - d.getTime()) / 1000);
        var units = [["year", 31536000], ["month", 2592000], ["day", 86400], ["hour", 3600], ["minute", 60]];
        for (var i = 0; i < units.length; i += 1) {
            var n = Math.floor(s / units[i][1]);
            if (n >= 1) return n + " " + units[i][0] + (n === 1 ? "" : "s") + " ago";
        }
        return "just now";
    }

    function textNodes(root) {
        var out = [];
        var walker = root.ownerDocument.createTreeWalker(root, 4 /* NodeFilter.SHOW_TEXT */);
        var node;
        while ((node = walker.nextNode())) if (clean(node.nodeValue)) out.push(node);
        return out;
    }

    function setLinkText(link, value) {
        var nodes = textNodes(link);
        if (!nodes.length) { link.appendChild(link.ownerDocument.createTextNode(value)); return; }
        nodes[0].nodeValue = value;
        nodes.slice(1).forEach(function (node) { node.nodeValue = ""; });
    }

    // Copy `template` (a tile on the page; `info` = {modId, game, summary})
    // for API record `mod`. Returns null when it cannot be copied faithfully.
    function nexusTileFromApi(template, info, mod) {
        if (!mod || !mod.modId || !info || !info.modId) return null;
        var game = (mod.game && mod.game.domainName || info.game || "").toLowerCase();
        var uploader = mod.uploader && mod.uploader.name || mod.author || "";
        var category = mod.modCategory && mod.modCategory.name || "";
        var tile = template.cloneNode(true);
        var titled = false;
        var ownLink = new RegExp("/mods/" + info.modId + "(?:[/?#]|$)");
        tile.querySelectorAll("a[href]").forEach(function (a) {
            var href = a.getAttribute("href");
            if (ownLink.test(href)) {
                a.setAttribute("href", href.replace(/\/([a-z0-9_-]+)\/mods\/\d+/i, "/" + game + "/mods/" + mod.modId));
                if (!a.querySelector("img") && clean(a.textContent)) {
                    setLinkText(a, mod.name);
                    titled = true;
                }
            } else if (/\/profile\/|\/users\//.test(href)) {
                a.setAttribute("href", href.replace(/\/(?:profile\/[^/?#]+|users\/\d+)/, "/profile/" + encodeURIComponent(uploader)));
                setLinkText(a, uploader);
                var avatar = a.querySelector("img");
                if (avatar) {
                    if (mod.uploader && mod.uploader.avatar) avatar.setAttribute("src", mod.uploader.avatar);
                    else avatar.remove();
                    avatar.removeAttribute("srcset");
                }
            } else if (/categoryName=/.test(href)) {
                var u = parseUrl(href, "https://www.nexusmods.com/");
                if (u) {
                    u.searchParams.set("categoryName", category);
                    a.setAttribute("href", u.pathname + u.search);
                }
                setLinkText(a, category);
            }
        });
        if (!titled) return null;
        var thumb = Array.from(tile.querySelectorAll("img")).find(function (img) {
            return Boolean(img.closest("a[href*='/mods/']")) || /\/thumbnails\//.test(img.getAttribute("src") || "");
        });
        if (thumb) {
            if (mod.thumbnailUrl) thumb.setAttribute("src", mod.thumbnailUrl);
            thumb.removeAttribute("srcset");
            thumb.setAttribute("alt", mod.name);
        }
        // Summary: the template's own summary text, else its longest plain text.
        var plain = textNodes(tile).filter(function (node) { return !node.parentElement.closest("a, time, button"); });
        var summaryNode = info.summary
            ? plain.find(function (node) { return clean(node.nodeValue) === clean(info.summary); }) || null
            : null;
        if (!summaryNode) {
            plain.forEach(function (node) {
                if (clean(node.nodeValue).length > 40 && (!summaryNode || node.nodeValue.length > summaryNode.nodeValue.length)) summaryNode = node;
            });
        }
        if (summaryNode) summaryNode.nodeValue = mod.summary || "";
        var times = tile.querySelectorAll("time");
        [[times[0], mod.updatedAt, nexusAgo], [times[1], mod.createdAt, nexusDate]].forEach(function (spec) {
            if (!spec[0] || !spec[1]) return;
            spec[0].setAttribute("datetime", spec[1]);
            spec[0].textContent = spec[2](spec[1]);
        });
        var stats = { "endorsements": nexusCount(mod.endorsements), "downloads": nexusCount(mod.downloads), "file size": nexusSize(mod.fileSize) };
        plain.forEach(function (node) {
            var label = clean(node.nodeValue).toLowerCase();
            if (!Object.prototype.hasOwnProperty.call(stats, label)) return;
            var holder = node.parentElement;
            var own = Array.from(holder.children).filter(function (child) { return clean(child.textContent).toLowerCase() !== label; });
            var value = own.length ? own[own.length - 1]
                : holder.nextElementSibling || (holder.parentElement && holder.parentElement.nextElementSibling);
            if (!value) return;
            var inner = textNodes(value);
            if (inner.length) inner[0].nodeValue = stats[label];
            else value.textContent = stats[label];
        });
        return tile;
    }

    var nexus = {
        scope: "nexus",
        matches: function (loc) { return hostIs(loc.hostname, "nexusmods.com"); },
        // One click on the thumbnail hides that mod (Shift+click: all options).
        quickHide: true,
        listRequest: nexusListRequest,
        nextPageBody: nexusNextPageBody,
        tileFromApi: nexusTileFromApi,
        apiEntityKey: function (mod) {
            return (mod.game && mod.game.domainName || "").toLowerCase() + ":" + mod.modId;
        },
        // Small hide icons next to the author and category links of a tile.
        inlineHides: function (el) {
            var out = [];
            el.querySelectorAll("a[href*='/profile/'], a[href*='/users/']").forEach(function (a) {
                var name = clean(a.textContent);
                if (name) out.push({ node: a, field: "author", value: name, label: "author " + name });
            });
            el.querySelectorAll("a[href*='categoryName='], a[href*='/categories/']").forEach(function (a) {
                var name = clean(a.textContent);
                if (name) out.push({ node: a, field: "category", value: name, label: "category " + name });
            });
            return out;
        },
        // `base` resolves relative links in documents fetched from elsewhere.
        items: function (root, doc, base) {
            doc = doc || root.ownerDocument || root;
            var loc = doc.location && /^https?:/.test(doc.location.href) ? doc.location : null;
            var baseHref = base || (loc ? loc.href : undefined);
            var current = loc ? nexusCurrentEntity(loc) : null;
            var seen = new Set();
            var out = [];
            root.querySelectorAll("a[href*='/mods/'], a[href*='/collections/']").forEach(function (link) {
                var entity = nexusEntityFromHref(link.getAttribute("href"), baseHref);
                if (!entity) return;
                if (current && current.key === entity.key) return;
                if (link.closest(NEXUS_EXCLUDED_AREAS) && !link.closest(NEXUS_TILE_SELECTOR)) return;
                var card = nexusCardFor(link, entity, doc, baseHref);
                if (!card || seen.has(card)) return;
                seen.add(card);
                card.__aosNexusEntity = entity;
                out.push(card);
            });
            return out;
        },
        facets: function (el) {
            var entity = el.__aosNexusEntity || {};
            var titleNode = el.querySelector("[data-e2e-id='mod-tile-title'], [data-e2e-id='collection-tile-title'], h3, h4, h2, [class*='title']");
            var title = titleNode ? clean(titleNode.textContent) : "";
            if (!title) {
                el.querySelectorAll("a[href*='/mods/'], a[href*='/collections/']").forEach(function (a) {
                    var t = clean(a.textContent);
                    if (t.length > title.length) title = t;
                });
            }
            var category = texts(el, "[data-e2e-id='mod-tile-category'], a[href*='categories'], a[href*='category']", 2);
            return {
                translation: nexusTranslation(title, [], category),
                kind: entity.kind || "mod",
                game: entity.game || "",
                title: title,
                author: texts(el, "a[href*='/users/'], a[href*='/profile/'], [data-e2e-id='user-link']", 3),
                category: category,
                id: entity.key || "",
                lookup: entity.kind === "mod" ? { game: entity.game, modId: entity.modId, key: entity.key } : null
            };
        },
        // Merge Nexus API data (tags, uploader, category, adult flag).
        enrich: function (facets, data) {
            if (!data) return facets;
            var out = Object.assign({}, facets);
            out.title = data.name || out.title;
            out.author = [].concat(facets.author || [], data.uploader ? [data.uploader] : [], data.author ? [data.author] : [])
                .filter(function (v, i, a) { return v && a.indexOf(v) === i; });
            out.category = [].concat(facets.category || [], data.category ? [data.category] : [])
                .filter(function (v, i, a) { return v && a.indexOf(v) === i; });
            out.gameName = data.gameName || "";
            out.tag = data.tags || [];
            out.nsfw = Boolean(data.adult);
            out.translation = nexusTranslation(out.title, out.tag, out.category);
            out.text = data.summary || "";
            return out;
        },
        exempt: function (loc) {
            var out = {};
            var game = loc.pathname.match(/^\/(?:games\/)?([a-z0-9_-]+)(?:\/|$)/i);
            if (game && !NEXUS_RESERVED.test(game[1])) out.game = game[1];
            var author = nexusProfileName(loc.pathname);
            if (author) out.author = author;
            return out;
        },
        // Hide buttons for the page itself: the author on a profile, the game
        // on a game page, the category being browsed, and the mod and its
        // author on a mod page (`data` is the Nexus API record for that mod).
        pageActions: function (loc, doc, data) {
            var out = [];
            var u = parseUrl(loc.href);
            if (!u) return out;
            var mod = nexusCurrentEntity(loc);
            if (mod && mod.kind === "mod") {
                out.push({ field: "id", value: mod.key, label: "this mod", lookup: { game: mod.game, modId: mod.modId, key: mod.key } });
                [data && data.uploader, data && data.author].forEach(function (name) {
                    if (name && !out.some(function (o) { return o.field === "author" && o.value === name; })) {
                        out.push({ field: "author", value: name, label: "author " + name });
                    }
                });
                return out;
            }
            var author = nexusProfileName(u.pathname);
            if (author) return [{ field: "author", value: author, label: "author " + author }];
            var game = nexusGameFromPath(u.pathname);
            if (game) out.push({ field: "game", value: game, label: "game " + nexusGameName(doc, game) });
            var category = u.searchParams.get("categoryName");
            if (category) out.push({ field: "category", value: category, label: "category " + category });
            return out;
        },
        // Paginated mod/collection lists, so the runtime can pull the next
        // page's items in when hidden ones leave gaps.
        listing: function (loc) {
            var u = parseUrl(loc.href);
            if (!u || !/^\/(?:(?:games\/[a-z0-9_-]+|profile\/[^/]+)\/)?(?:mods|collections)\/?$|^\/search\/?$/i.test(u.pathname)) return null;
            var page = parseInt(u.searchParams.get("page") || "1", 10);
            if (!(page >= 1)) page = 1;
            u.searchParams.delete("page");
            u.hash = "";
            return {
                key: u.pathname + "?" + u.searchParams.toString(),
                page: page,
                pageUrl: function (n) {
                    var next = new URL(u.href);
                    next.searchParams.set("page", String(n));
                    return next.href;
                }
            };
        }
    };

    // -- AO3 ----------------------------------------------------------------------

    var ao3 = {
        scope: "ao3",
        matches: function (loc) { return hostIs(loc.hostname, "archiveofourown.org") || hostIs(loc.hostname, "ao3.org"); },
        items: function (root) {
            return Array.from(root.querySelectorAll("li.work.blurb, li.bookmark.blurb, li.series.blurb"));
        },
        buttonHost: function (el) { return el.querySelector(".header.module") || el; },
        facets: function (el) {
            var link = el.querySelector("h4.heading a[href*='/works/'], h4.heading a[href*='/series/']");
            var href = link ? link.getAttribute("href") : "";
            var idMatch = href.match(/\/(works|series)\/(\d+)/);
            var authors = texts(el, "h4.heading a[rel='author']");
            if (!authors.length && /\bby\s+Anonymous\b/i.test(text(el, "h4.heading"))) authors = ["Anonymous"];
            var wip = text(el, ".required-tags .iswip .text");
            var words = el.querySelector("dd.words");
            var categories = [];
            texts(el, ".required-tags .category .text").forEach(function (value) {
                value.split(/,\s*/).forEach(function (part) { if (part) categories.push(part); });
            });
            var warnings = texts(el, "ul.tags li.warnings a.tag");
            texts(el, ".required-tags .warnings .text").forEach(function (value) {
                value.split(/,\s*/).forEach(function (part) {
                    if (part && warnings.indexOf(part) === -1) warnings.push(part);
                });
            });
            var fandoms = texts(el, "h5.fandoms a.tag");
            return {
                id: idMatch ? idMatch[1] + ":" + idMatch[2] : "",
                title: link ? clean(link.textContent) : "",
                author: authors,
                fandom: fandoms,
                fandomCount: fandoms.length,
                rating: texts(el, ".required-tags .rating .text"),
                warning: warnings,
                category: categories,
                tag: texts(el, "ul.tags li.relationships a.tag, ul.tags li.characters a.tag, ul.tags li.freeforms a.tag"),
                language: text(el, "dd.language"),
                words: words ? parseCount(words.textContent) : null,
                complete: wip ? /complete/i.test(wip) : null,
                text: text(el, "blockquote.summary")
            };
        },
        exempt: function (loc) {
            var user = loc.pathname.match(/^\/users\/([^/]+)/i);
            return user ? { author: decodeURIComponent(user[1]) } : {};
        }
    };

    // -- XenForo (SpaceBattles, Sufficient Velocity, QQ and any XF2 forum) -------

    function xfThreadId(href) {
        var match = String(href || "").match(/\/threads\/(?:[^/]*\.)?(\d+)/);
        return match ? match[1] : "";
    }

    var xenforo = {
        scope: "xenforo",
        matches: function (loc, doc) {
            var html = doc && doc.documentElement;
            if (html && html.id === "XF") return true;
            return ["spacebattles.com", "sufficientvelocity.com", "questionablequesting.com", "alternatehistory.com"]
                .some(function (d) { return hostIs(loc.hostname, d); });
        },
        items: function (root) {
            return Array.from(root.querySelectorAll(
                ".structItem--thread[data-author], li.block-row[data-author], article.message[data-author]"
            ));
        },
        kind: function (el) { return el.matches("article.message") ? "post" : "thread"; },
        buttonHost: function (el) {
            return el.querySelector(".structItem-title") || el.querySelector(".contentRow-title") ||
                el.querySelector(".message-attribution-opposite") || el;
        },
        facets: function (el, ctx) {
            var host = ctx && ctx.host || "";
            if (el.matches("article.message")) {
                return {
                    kind: "post",
                    author: el.getAttribute("data-author") || "",
                    id: host + ":post:" + (el.getAttribute("data-content") || "").replace(/^post-/, "")
                };
            }
            var link = el.querySelector(".structItem-title a[data-tp-primary='on']") ||
                el.querySelector(".structItem-title a[href*='/threads/']:last-of-type") ||
                el.querySelector(".contentRow-title a[href*='/threads/'], a[href*='/threads/']");
            var title = link ? clean(link.textContent) : text(el, ".contentRow-title");
            var threadId = xfThreadId(link && link.getAttribute("href"));
            return {
                kind: "thread",
                author: el.getAttribute("data-author") || "",
                title: title,
                prefix: texts(el, ".structItem-title .label, .contentRow-title .label"),
                tag: texts(el, ".structItem-tagBlock .tagItem, .contentRow-minor .tagItem"),
                forum: texts(el, ".structItem-parts a[href*='/forums/'], .contentRow-minor a[href*='/forums/']", 2),
                text: text(el, ".contentRow-snippet"),
                id: threadId ? host + ":thread:" + threadId : ""
            };
        },
        exempt: function () { return {}; }
    };

    // -- FanFiction.net -----------------------------------------------------------

    var FFN_LANGUAGES = /^(English|Spanish|French|German|Portuguese|Italian|Indonesian|Polish|Russian|Dutch|Chinese|Japanese|Vietnamese|Filipino|Turkish|Swedish|Czech|Finnish|Norwegian|Danish|Hungarian|Hebrew|Greek|Catalan|Romanian|Korean|Arabic|Thai|Croatian|Serbian|Bulgarian|Slovak|Esperanto|Afrikaans|Albanian|Devanagari|Farsi|Icelandic|Malay|Ukrainian|Latin|Estonian|Latvian|Lithuanian|Hindi|Tagalog|Bengali|Urdu|Tamil|Telugu)$/i;
    var FFN_GENRES = /^(Adventure|Angst|Crime|Drama|Family|Fantasy|Friendship|General|Horror|Humor|Hurt\/Comfort|Mystery|Parody|Poetry|Romance|Sci-Fi|Spiritual|Supernatural|Suspense|Tragedy|Western)(\/|$)/i;

    function parseFfnInfo(info) {
        var parts = info.split(/\s+-\s+/).map(clean).filter(Boolean);
        var out = { fandom: [], rating: [], language: "", tag: [], words: null, complete: false };
        var ratedIndex = -1;
        parts.forEach(function (part, index) {
            var rated = part.match(/^Rated:\s*(?:Fiction\s+)?(.+)$/i);
            if (rated) { out.rating.push(rated[1]); ratedIndex = index; return; }
            var words = part.match(/^Words:\s*([\d,]+)/i);
            if (words) { out.words = parseCount(words[1]); return; }
            if (/^Complete$/i.test(part)) { out.complete = true; return; }
            if (FFN_LANGUAGES.test(part)) { out.language = part; return; }
            if (FFN_GENRES.test(part)) {
                part.replace("Hurt/Comfort", "Hurt-Comfort").split("/").forEach(function (g) {
                    out.tag.push(g.replace("Hurt-Comfort", "Hurt/Comfort"));
                });
                return;
            }
            if (/^(Chapters|Reviews|Favs|Follows|Updated|Published|id):/i.test(part)) return;
            if (ratedIndex === -1) {
                if (/^Crossover$/i.test(part)) return;
                part.split(/\s+&\s+/).forEach(function (f) { if (f) out.fandom.push(f); });
                return;
            }
            // Character / pairing list follows the published date.
            part.replace(/[[\]]/g, ",").split(/,\s*/).forEach(function (c) {
                c = clean(c);
                if (c) out.tag.push(c);
            });
        });
        return out;
    }

    var ffn = {
        scope: "ffn",
        matches: function (loc) { return hostIs(loc.hostname, "fanfiction.net") || hostIs(loc.hostname, "fictionpress.com"); },
        items: function (root) { return Array.from(root.querySelectorAll(".z-list")); },
        facets: function (el) {
            var link = el.querySelector("a.stitle[href*='/s/'], a[href*='/s/']");
            var idMatch = link && link.getAttribute("href").match(/\/s\/(\d+)/);
            var info = text(el, ".z-padtop2.xgray, .xgray");
            var parsed = parseFfnInfo(info);
            var summaryNode = el.querySelector(".z-indent");
            var summary = summaryNode ? clean(summaryNode.textContent.replace(info, "")) : "";
            return {
                id: idMatch ? "ffn:" + idMatch[1] : "",
                title: link ? clean(link.textContent) : "",
                author: texts(el, "a[href^='/u/'], a[href*='fanfiction.net/u/']", 2),
                fandom: parsed.fandom,
                fandomCount: parsed.fandom.length,
                rating: parsed.rating,
                language: parsed.language,
                tag: parsed.tag,
                words: parsed.words,
                complete: info ? parsed.complete : null,
                text: summary
            };
        },
        exempt: function () { return {}; },
        parseInfo: parseFfnInfo
    };

    // -- YouTube ------------------------------------------------------------------

    var YT_ITEMS = [
        "ytd-rich-item-renderer",
        "ytd-video-renderer",
        "ytd-compact-video-renderer",
        "ytd-grid-video-renderer",
        "ytd-playlist-video-renderer",
        "ytd-reel-item-renderer",
        "ytd-reel-shelf-renderer",
        "ytd-rich-section-renderer",
        "yt-lockup-view-model",
        "ytm-shorts-lockup-view-model",
        "ytm-shorts-lockup-view-model-v2"
    ].join(",");

    var youtube = {
        scope: "youtube",
        matches: function (loc) { return hostIs(loc.hostname, "youtube.com"); },
        items: function (root) { return outermost(root.querySelectorAll(YT_ITEMS), YT_ITEMS); },
        facets: function (el) {
            var tag = el.tagName.toLowerCase();
            var isShelf = tag === "ytd-reel-shelf-renderer" ||
                (tag === "ytd-rich-section-renderer" && Boolean(el.querySelector("ytd-rich-shelf-renderer[is-shorts], ytm-shorts-lockup-view-model, ytm-shorts-lockup-view-model-v2, ytd-reel-item-renderer")));
            if (tag === "ytd-rich-section-renderer" && !isShelf) return { kind: "section" };
            var link = el.querySelector("a#video-title-link, a#video-title, a#thumbnail[href], a[href*='/watch?v='], a[href*='/shorts/']");
            var href = link ? link.getAttribute("href") || "" : "";
            var id = (href.match(/[?&]v=([\w-]{6,})/) || href.match(/\/shorts\/([\w-]{6,})/) || [])[1] || "";
            var titleNode = el.querySelector("#video-title, .yt-lockup-metadata-view-model__title, .yt-lockup-metadata-view-model-wiz__title, h3");
            var title = titleNode ? clean(titleNode.getAttribute("title") || titleNode.textContent) : "";
            var channelLinks = el.querySelectorAll("ytd-channel-name a, #channel-name a, a[href^='/@'], a[href^='/channel/']");
            var channels = [];
            channelLinks.forEach(function (a) {
                var name = clean(a.textContent);
                var handle = (a.getAttribute("href") || "").match(/^\/@([^/?#]+)/);
                if (name && channels.indexOf(name) === -1) channels.push(name);
                if (handle && channels.indexOf(decodeURIComponent(handle[1])) === -1) channels.push(decodeURIComponent(handle[1]));
            });
            if (!channels.length) {
                var nameText = text(el, "ytd-channel-name #text, #channel-name #text");
                if (nameText) channels.push(nameText);
            }
            return {
                kind: isShelf ? "shorts-shelf" : "video",
                title: isShelf ? "" : title,
                channel: channels,
                author: channels,
                id: id ? "yt:" + id : "",
                short: isShelf || /\/shorts\//.test(href) || /reel|shorts/.test(tag)
            };
        },
        exempt: function (loc) {
            var handle = loc.pathname.match(/^\/@([^/]+)/);
            return handle ? { channel: decodeURIComponent(handle[1]), author: decodeURIComponent(handle[1]) } : {};
        }
    };

    // -- Steam Workshop -----------------------------------------------------------

    var steam = {
        scope: "steam",
        matches: function (loc) {
            return hostIs(loc.hostname, "steamcommunity.com") && /^\/(workshop|sharedfiles)\//i.test(loc.pathname);
        },
        items: function (root) { return Array.from(root.querySelectorAll(".workshopItem, .workshopItemCollection")); },
        facets: function (el) {
            var link = el.querySelector("a[data-publishedfileid], a[href*='filedetails']");
            var id = link ? link.getAttribute("data-publishedfileid") ||
                ((link.getAttribute("href") || "").match(/[?&]id=(\d+)/) || [])[1] || "" : "";
            return {
                title: text(el, ".workshopItemTitle"),
                author: texts(el, ".workshopItemAuthorName a, .workshop_author_link", 2),
                id: id ? "steam:" + id : ""
            };
        },
        exempt: function () { return {}; }
    };

    // -- Search engines -----------------------------------------------------------

    function decodeResultHref(href, base) {
        var u = parseUrl(href, base);
        if (!u) return "";
        if (/duckduckgo\.com$/.test(u.hostname) && u.searchParams.get("uddg")) return u.searchParams.get("uddg");
        if (/google\./.test(u.hostname) && u.pathname === "/url") return u.searchParams.get("q") || u.searchParams.get("url") || "";
        return u.href;
    }

    var search = {
        scope: "search",
        matches: function (loc) {
            var h = loc.hostname.toLowerCase();
            return /(^|\.)google\.[a-z.]+$/.test(h) && /^\/search/.test(loc.pathname) ||
                hostIs(h, "duckduckgo.com") || hostIs(h, "bing.com") && /^\/search/.test(loc.pathname) ||
                hostIs(h, "search.brave.com") || hostIs(h, "startpage.com");
        },
        items: function (root, doc) {
            doc = doc || root.ownerDocument || root;
            var host = doc.location ? doc.location.hostname : "";
            var out = [];
            var seen = new Set();
            function add(el) { if (el && !seen.has(el)) { seen.add(el); out.push(el); } }
            if (/google\./.test(host)) {
                root.querySelectorAll("#search a h3, #rso a h3").forEach(function (h3) {
                    var item = h3.closest("div.MjjYud") || h3.closest("div.g") || h3.closest("[data-hveid]");
                    add(item);
                });
            } else if (/duckduckgo\.com$/.test(host)) {
                root.querySelectorAll("article[data-testid='result'], li[data-layout='organic'] > article, .result.results_links").forEach(add);
            } else if (/bing\.com$/.test(host)) {
                root.querySelectorAll("li.b_algo").forEach(add);
            } else {
                root.querySelectorAll("#results .snippet[data-type='web'], .w-gl__result, .result").forEach(add);
            }
            return out;
        },
        facets: function (el, ctx) {
            var h3 = el.querySelector("h3");
            var link = el.querySelector("a[data-testid='result-title-a'], a.result__a, h2 a") ||
                (h3 && h3.closest("a")) || el.querySelector("a[href^='http']");
            var href = link ? decodeResultHref(link.getAttribute("href"), ctx && ctx.href) : "";
            var domain = hostOf(href);
            if (!domain || /bing\.com$|duckduckgo\.com$|google\./.test(domain)) {
                var cite = text(el, "cite");
                domain = hostOf(/^https?:/.test(cite) ? cite.split(" ")[0] : "https://" + cite.split(/[\s›/]/)[0]) || domain;
            }
            return {
                title: text(el, "h3, h2, a.result__a"),
                text: text(el, ".VwiC3b, [data-result='snippet'], .result__snippet, .b_caption p, .snippet-description"),
                domain: domain,
                id: href ? "url:" + href : ""
            };
        },
        exempt: function () { return {}; }
    };

    // -- Amazon -------------------------------------------------------------------

    var amazon = {
        scope: "amazon",
        matches: function (loc) { return /(^|\.)amazon\.[a-z.]+$/.test(loc.hostname.toLowerCase()); },
        items: function (root) {
            return Array.from(root.querySelectorAll("div[data-component-type='s-search-result'][data-asin]"));
        },
        facets: function (el) {
            var sponsored = Boolean(el.querySelector(".puis-sponsored-label-text, .s-sponsored-label-text, [aria-label*='Sponsored']")) ||
                /\bSponsored\b/.test(text(el, ".puis-label-popover-default, .s-label-popover-default"));
            return {
                title: text(el, "h2"),
                author: texts(el, ".a-row.a-size-base.a-color-secondary .a-size-base:not(.a-color-secondary), .s-line-clamp-1 .a-size-base-plus", 2),
                id: el.getAttribute("data-asin") ? "asin:" + el.getAttribute("data-asin") : "",
                promoted: sponsored
            };
        },
        exempt: function () { return {}; }
    };

    // -- User-defined sites -------------------------------------------------------

    function customAdapter(site) {
        return {
            scope: "custom",
            custom: site,
            matches: function (loc) { return hostIs(loc.hostname, String(site.host || "").toLowerCase().replace(/^www\./, "")); },
            items: function (root) {
                try { return Array.from(root.querySelectorAll(site.itemSelector)); } catch (error) { return []; }
            },
            facets: function (el) {
                function pick(selector, many) {
                    if (!selector) return many ? [] : "";
                    try { return many ? texts(el, selector) : text(el, selector); } catch (error) { return many ? [] : ""; }
                }
                var link = el.querySelector("a[href]");
                return {
                    title: pick(site.titleSelector) || (link ? clean(link.textContent) : ""),
                    author: pick(site.authorSelector, true),
                    tag: pick(site.tagSelector, true),
                    text: pick(site.textSelector),
                    id: link ? "url:" + link.href : ""
                };
            },
            exempt: function () { return {}; }
        };
    }

    var BUILTIN = [reddit, nexus, ao3, xenforo, ffn, youtube, steam, search, amazon];

    function adaptersFor(loc, doc, customSites) {
        var list = BUILTIN.filter(function (adapter) {
            try { return adapter.matches(loc, doc); } catch (error) { return false; }
        });
        (customSites || []).forEach(function (site) {
            if (!site || !site.host || !site.itemSelector || site.enabled === false) return;
            var adapter = customAdapter(site);
            if (adapter.matches(loc, doc)) list.push(adapter);
        });
        return list;
    }

    // -- Link-derived hide options (right-click on any link) ----------------------

    function ao3TagFromPath(segment) {
        return decodeURIComponent(segment)
            .replace(/\*s\*/g, "/").replace(/\*a\*/g, "&").replace(/\*d\*/g, ".")
            .replace(/\*h\*/g, "#").replace(/\*q\*/g, "?");
    }

    function linkHideOptions(href, linkText, base) {
        var u = parseUrl(href, base);
        if (!u || !/^https?:$/.test(u.protocol)) return [];
        var host = u.hostname.toLowerCase();
        var path = u.pathname;
        var label = clean(linkText);
        var out = [];
        var m;
        if (hostIs(host, "reddit.com")) {
            if ((m = path.match(/^\/r\/([^/]+)\/?$/i)) && !/^(all|popular)$/i.test(m[1])) {
                out.push({ scope: "reddit", field: "subreddit", value: m[1], label: "Hide r/" + m[1] });
            }
            if ((m = path.match(/^\/(?:u|user)\/([^/]+)/i))) out.push({ scope: "reddit", field: "author", value: m[1], label: "Hide u/" + m[1] });
        } else if (hostIs(host, "archiveofourown.org")) {
            if ((m = path.match(/^\/tags\/([^/]+)/))) {
                var tag = ao3TagFromPath(m[1]);
                out.push({ scope: "ao3", field: "tag", value: tag, label: "Hide AO3 tag " + tag });
                out.push({ scope: "ao3", field: "fandom", value: tag, label: "Hide AO3 fandom " + tag });
            }
            if ((m = path.match(/^\/users\/([^/]+)/))) {
                var user = decodeURIComponent(m[1]);
                out.push({ scope: "ao3", field: "author", value: user, label: "Hide AO3 author " + user });
            }
        } else if (hostIs(host, "nexusmods.com")) {
            if ((m = path.match(/^\/(?:games\/)?([a-z0-9_-]+)\/?$/i)) && !NEXUS_RESERVED.test(m[1])) {
                out.push({ scope: "nexus", field: "game", value: m[1].toLowerCase(), label: "Hide Nexus game " + (label || m[1]) });
            }
            var profile = nexusProfileName(path);
            if (profile) out.push({ scope: "nexus", field: "author", value: profile, label: "Hide Nexus author " + profile });
            else if (/\/users\//.test(path) && label) out.push({ scope: "nexus", field: "author", value: label, label: "Hide Nexus author " + label });
            if (/[?&](categories|category)/.test(u.search) || /\/categories\//.test(path)) {
                if (label) out.push({ scope: "nexus", field: "category", value: label, label: "Hide Nexus category " + label });
            }
        } else if (hostIs(host, "youtube.com")) {
            if ((m = path.match(/^\/@([^/]+)/))) {
                var handle = decodeURIComponent(m[1]);
                out.push({ scope: "youtube", field: "channel", value: handle, label: "Hide channel @" + handle });
            }
        } else if (/\/members\/[^/]+\.\d+\/?$/.test(path) && label) {
            out.push({ scope: "xenforo", field: "author", value: label, label: "Hide forum user " + label });
        } else if (/\/forums\/[^/]+\.\d+\/?$/.test(path) && label) {
            out.push({ scope: "xenforo", field: "forum", value: label, label: "Hide forum " + label });
        }
        var domain = host.replace(/^www\./, "");
        var baseHost = base ? hostOf(base) : "";
        if (domain && domain !== baseHost) {
            out.push({ scope: "search", field: "domain", value: domain, label: "Hide " + domain + " in search results" });
            out.push({ scope: "reddit", field: "domain", value: domain, label: "Hide " + domain + " links on Reddit" });
        }
        return out;
    }

    // -- old.reddit.com redirect ---------------------------------------------------

    var NEW_REDDIT_HOST = /^(?:www\.|new\.|np\.)?reddit\.com$/i;
    // Pages old Reddit cannot show: the media viewer, share links (they must
    // resolve on www first), chat, new-style settings and app-only areas.
    var OLD_REDDIT_UNSUPPORTED = /^\/(?:media|poll|chat|notifications|answers|avatar|settings|appeal|premium|coins|reddit-pro|svc|s|community-points|topics|vault)(?:[/?#]|$)|^\/(?:r|u|user)\/[^/]+\/s\//i;

    function oldRedditRedirect(href) {
        var u = parseUrl(href);
        if (!u || !/^https?:$/.test(u.protocol) || !NEW_REDDIT_HOST.test(u.hostname)) return null;
        if (OLD_REDDIT_UNSUPPORTED.test(u.pathname)) return null;
        if (u.searchParams.get("aos_new") === "1") return null; // explicit opt-out per link
        u.protocol = "https:";
        u.hostname = "old.reddit.com";
        return u.href;
    }

    return {
        oldRedditRedirect: oldRedditRedirect,
        BUILTIN: BUILTIN,
        adaptersFor: adaptersFor,
        customAdapter: customAdapter,
        linkHideOptions: linkHideOptions,
        nexusEntityFromHref: nexusEntityFromHref,
        nexusTileFromApi: nexusTileFromApi,
        nexusListRequest: nexusListRequest,
        nexusNextPageBody: nexusNextPageBody,
        nexusCount: nexusCount,
        nexusSize: nexusSize,
        nexusTranslation: nexusTranslation,
        parseFfnInfo: parseFfnInfo,
        ao3TagFromPath: ao3TagFromPath,
        byScope: {
            reddit: reddit, nexus: nexus, ao3: ao3, xenforo: xenforo, ffn: ffn,
            youtube: youtube, steam: steam, search: search, amazon: amazon
        }
    };
});
