"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const Core = require("../src/lib/filter-core.js");
const plain = (v) => JSON.parse(JSON.stringify(v));
const { makeBrowser, sendToContent, makeDom, load, tick, waitFor } = require("./helpers");

const FILTER_FILES = ["lib/filter-core.js", "lib/sites.js", "content/filter.js"];

// Background double: serialises rule writes the way background.js does.
function backgroundFor(extra) {
    return async function (message, browser) {
        const key = Core.STORAGE_KEY;
        if (message.type === "filters-add-rule" || message.type === "filters-remove-rule") {
            const res = await browser.storage.local.get(key);
            const state = Core.normalizeState(res[key]);
            if (message.type === "filters-add-rule") Core.addRule(state, message.rule);
            else state.rules = state.rules.filter((r) => r.id !== message.id);
            await browser.storage.local.set({ [key]: state });
            return { ok: true };
        }
        return extra ? extra(message, browser) : undefined;
    };
}

const REDDIT_FEED = `<!doctype html><html><body><main>
  <article><shreddit-post subreddit-prefixed-name="r/pics" author="alice" post-title="Cat" id="t3_a"></shreddit-post></article>
  <article><shreddit-post subreddit-prefixed-name="r/news" author="bob" post-title="Headline" id="t3_b"></shreddit-post></article>
  <article><shreddit-ad-post subreddit-prefixed-name="u/brand" post-title="Ad" promoted></shreddit-ad-post></article>
</main></body></html>`;

test("reddit feed: existing rule hides on load, inline rule add hides live, counter + reveal", async () => {
    const state = Core.normalizeState(null);
    Core.addRule(state, { scope: "reddit", field: "subreddit", value: "pics" });
    const browser = makeBrowser({ storage: { [Core.STORAGE_KEY]: state }, onBackgroundMessage: backgroundFor() });
    const dom = makeDom(REDDIT_FEED, "https://www.reddit.com/r/popular/", browser);
    load(dom, FILTER_FILES);
    const doc = dom.window.document;
    const articles = doc.querySelectorAll("article");

    await waitFor(() => articles[0].getAttribute("data-aos-hidden"));
    assert.equal(articles[0].getAttribute("data-aos-hidden"), "remove");
    assert.equal(articles[1].getAttribute("data-aos-hidden"), null);
    assert.equal(articles[2].getAttribute("data-aos-hidden"), "remove", "promoted posts hidden by default");
    assert.ok(articles[1].querySelector(":scope > .aos-hide-btn"), "inline hide button on visible items");
    assert.match(doc.querySelector(".aos-counter").textContent, /2 hidden/);

    // Click ⊘ on r/news and choose "Hide r/news" in the popover.
    articles[1].querySelector(".aos-hide-btn").click();
    const popover = doc.querySelector(".aos-popover-host");
    assert.ok(popover, "popover opens");
    const option = Array.from(popover.shadowRoot.querySelectorAll(".list button")).find((b) => b.textContent === "Hide r/news");
    assert.ok(option, "offers the subreddit");
    option.click();
    await waitFor(() => articles[1].getAttribute("data-aos-hidden"));
    assert.match(doc.querySelector(".aos-counter").textContent, /3 hidden/);

    // Reveal mode and page stats for the popup.
    await sendToContent(browser, { type: "filters-set-reveal", reveal: true });
    assert.ok(doc.documentElement.hasAttribute("data-aos-reveal"));
    const stats = await sendToContent(browser, { type: "filters-page-stats" });
    assert.deepEqual(plain(stats.scopes), ["reddit"]);
    assert.equal(stats.hidden, 3);

    // Removing the rule (e.g. from the options page) unhides immediately.
    const saved = Core.normalizeState(browser._data[Core.STORAGE_KEY]);
    saved.rules = saved.rules.filter((r) => r.value !== "news");
    await browser.storage.local.set({ [Core.STORAGE_KEY]: saved });
    await waitFor(() => !articles[1].getAttribute("data-aos-hidden"));
    dom.window.close();
});

test("subreddit's own page is exempt; collapse style keeps a bar", async () => {
    const state = Core.normalizeState({ hiddenStyle: "collapse" });
    Core.addRule(state, { scope: "reddit", field: "subreddit", value: "pics" });
    Core.addRule(state, { scope: "reddit", field: "author", value: "bob" });
    const browser = makeBrowser({ storage: { [Core.STORAGE_KEY]: state }, onBackgroundMessage: backgroundFor() });
    const dom = makeDom(REDDIT_FEED, "https://www.reddit.com/r/pics/", browser);
    load(dom, FILTER_FILES);
    const articles = dom.window.document.querySelectorAll("article");
    await waitFor(() => articles[1].getAttribute("data-aos-hidden"));
    assert.equal(articles[0].getAttribute("data-aos-hidden"), null, "r/pics visible on r/pics");
    assert.equal(articles[1].getAttribute("data-aos-hidden"), "collapse");
    assert.match(articles[1].querySelector(".aos-collapse-bar").textContent, /Author \/ user: bob/);
    dom.window.close();
});

test("nexus: tag rule applies after API enrichment arrives", async () => {
    const state = Core.normalizeState(null);
    Core.addRule(state, { scope: "nexus", field: "tag", value: "Lore-Friendly" });
    const lookups = [];
    const browser = makeBrowser({
        storage: { [Core.STORAGE_KEY]: state },
        onBackgroundMessage: backgroundFor(async (message) => {
            if (message.type !== "nexus-lookup") return undefined;
            lookups.push(message.items.map((i) => i.key));
            return {
                mods: {
                    "skyrimspecialedition:266": { name: "USSEP", uploader: "Arthmoor", category: "Bug Fixes", tags: ["Lore-Friendly"], adult: false },
                    "skyrimspecialedition:3863": { name: "SkyUI", uploader: "schlangster", category: "User Interface", tags: ["UI"], adult: false }
                }
            };
        })
    });
    const dom = makeDom(`<main>
      <div class="tile" id="a"><a href="/skyrimspecialedition/mods/266"><img></a><h3>USSEP</h3></div>
      <div class="tile" id="b"><a href="/skyrimspecialedition/mods/3863"><img></a><h3>SkyUI</h3></div>
    </main>`, "https://www.nexusmods.com/games/skyrimspecialedition/mods", browser);
    load(dom, FILTER_FILES);
    const doc = dom.window.document;
    await waitFor(() => doc.getElementById("a").getAttribute("data-aos-hidden"));
    assert.equal(doc.getElementById("b").getAttribute("data-aos-hidden"), null);
    assert.deepEqual(plain(lookups[0]).sort(), ["skyrimspecialedition:266", "skyrimspecialedition:3863"]);
    assert.match(doc.getElementById("a").getAttribute("data-aos-reason"), /Lore-Friendly/);
    dom.window.close();
});

test("context menu options combine the item and the link under the cursor", async () => {
    const browser = makeBrowser({ onBackgroundMessage: backgroundFor() });
    const dom = makeDom(`<ol><li class="work blurb group">
        <div class="header module"><h4 class="heading"><a href="/works/9">T</a> by <a rel="author" href="/users/w">w</a></h4>
        <h5 class="fandoms heading"><a class="tag" href="/tags/Fandom/works">Fandom</a></h5></div>
        <ul class="tags"><li class="freeforms"><a class="tag" id="tag" href="/tags/Fluff/works">Fluff</a></li></ul>
      </li></ol>`, "https://archiveofourown.org/works", browser);
    load(dom, FILTER_FILES);
    await tick(200);
    const tag = dom.window.document.getElementById("tag");
    tag.dispatchEvent(new dom.window.MouseEvent("contextmenu", { bubbles: true }));
    const { options } = await sendToContent(browser, { type: "filters-context-options" });
    const labels = options.map((o) => o.label);
    assert.ok(labels.includes("Hide author w"));
    assert.ok(labels.includes("Hide fandom Fandom"));
    assert.ok(labels.includes("Hide tag Fluff"));
    assert.ok(labels.includes("Hide just this item"));
    assert.ok(options.every((o) => o.scope === "ao3"));
    dom.window.close();
});

function nexusTile(id, title, author) {
    return `<div class="group/mod-tile flex flex-col" id="m${id}">
      <div class="relative"><a href="https://www.nexusmods.com/skyrimspecialedition/mods/${id}"><img src="x.png"></a>
        <button id="headlessui-menu-button-${id}">Mod options</button></div>
      <div class="px-3"><a href="https://www.nexusmods.com/skyrimspecialedition/mods/${id}">${title}</a>
        <a href="https://www.nexusmods.com/profile/${author}?gameId=1704">${author}</a></div>
    </div>`;
}

function nexusPage(tiles) {
    return `<!doctype html><html><body><main><div class="grid">${tiles.join("")}</div></main></body></html>`;
}

function nexusBrowser(state, extra) {
    return makeBrowser({
        storage: { [Core.STORAGE_KEY]: state || Core.normalizeState(null) },
        onBackgroundMessage: backgroundFor(async (message) => {
            if (message.type === "nexus-lookup") return { mods: {} };
            return extra ? extra(message) : undefined;
        })
    });
}

test("nexus: one-click hide on the thumbnail's corner, with undo", async () => {
    const browser = nexusBrowser();
    const dom = makeDom(nexusPage([nexusTile(1, "Alpha Armor", "Alice"), nexusTile(2, "Beta Bows", "Bob")]),
        "https://www.nexusmods.com/games/skyrimspecialedition/mods?sort=updated", browser);
    load(dom, FILTER_FILES);
    const doc = dom.window.document;
    const button = await waitFor(() => doc.querySelector("#m1 > .aos-quick-hide"));
    assert.equal(button.textContent, "✕");
    button.click();
    await waitFor(() => doc.getElementById("m1").getAttribute("data-aos-hidden"));
    const rule = Core.normalizeState(browser._data[Core.STORAGE_KEY]).rules[0];
    assert.equal(rule.field, "id");
    assert.equal(rule.value, "skyrimspecialedition:1");
    assert.equal(doc.getElementById("m2").getAttribute("data-aos-hidden"), null);

    const toast = doc.querySelector(".aos-toast-host");
    assert.match(toast.shadowRoot.textContent, /Alpha Armor/);
    toast.shadowRoot.querySelector("button").click();
    await waitFor(() => !doc.getElementById("m1").getAttribute("data-aos-hidden"));

    // Shift+click still opens the full menu.
    doc.querySelector("#m2 > .aos-quick-hide").dispatchEvent(new dom.window.MouseEvent("click", { bubbles: true, shiftKey: true }));
    const labels = Array.from(doc.querySelector(".aos-popover-host").shadowRoot.querySelectorAll(".list button")).map((b) => b.textContent);
    assert.ok(labels.includes("Hide author Bob"));
    dom.window.close();
});

test("nexus: profile page offers 'Hide author' and shows when it is hidden", async () => {
    const browser = nexusBrowser();
    const dom = makeDom(nexusPage([nexusTile(1, "Alpha Armor", "Alice")]), "https://www.nexusmods.com/profile/Alice?gameId=1704", browser);
    load(dom, FILTER_FILES);
    const doc = dom.window.document;
    const host = await waitFor(() => doc.querySelector(".aos-pagebar-host"));
    const button = () => Array.from(host.shadowRoot.querySelectorAll("button")).find((b) => /author Alice/.test(b.textContent));
    assert.equal(button().textContent, "⊘ Hide author Alice");
    button().click();
    await waitFor(() => /✓ Hidden: author Alice/.test(button().textContent));
    const rules = Core.normalizeState(browser._data[Core.STORAGE_KEY]).rules;
    assert.deepEqual(plain(rules.map((r) => [r.scope, r.field, r.value])), [["nexus", "author", "Alice"]]);
    assert.equal(doc.getElementById("m1").getAttribute("data-aos-hidden"), null, "the author's own page still lists their mods");
    button().click();
    await waitFor(() => /⊘ Hide author Alice/.test(button().textContent));
    dom.window.close();
});

test("nexus: game page offers 'Hide game'; title words hide by title only", async () => {
    const browser = nexusBrowser();
    const dom = makeDom(nexusPage([nexusTile(1, "Alpha Armor", "Alice"), nexusTile(2, "Beta Bows", "Bob")]),
        "https://www.nexusmods.com/games/skyrimspecialedition/mods", browser);
    load(dom, FILTER_FILES);
    const doc = dom.window.document;
    const host = await waitFor(() => doc.querySelector(".aos-pagebar-host"));
    const texts = Array.from(host.shadowRoot.querySelectorAll("button")).map((b) => b.textContent);
    assert.ok(texts.includes("⊘ Hide game skyrimspecialedition"));
    Array.from(host.shadowRoot.querySelectorAll("button")).find((b) => /title word/.test(b.textContent)).click();
    const input = await waitFor(() => host.shadowRoot.querySelector("input"));
    input.value = "armor";
    host.shadowRoot.querySelector("form").dispatchEvent(new dom.window.Event("submit", { cancelable: true }));
    await waitFor(() => doc.getElementById("m1").getAttribute("data-aos-hidden"));
    assert.equal(doc.getElementById("m1").getAttribute("data-aos-reason"), "Title term: armor");
    assert.equal(doc.getElementById("m2").getAttribute("data-aos-hidden"), null);
    dom.window.close();
});

test("nexus: hidden items are replaced from the next page, which then skips them", async () => {
    const state = Core.normalizeState(null);
    Core.addRule(state, { scope: "nexus", field: "author", value: "Spammer" });
    const fetched = [];
    const PAGE2 = nexusPage([nexusTile(2, "Beta Bows", "Bob"), nexusTile(4, "Delta Daggers", "Dee"), nexusTile(5, "Echo Elves", "Eve")]);
    const browser = nexusBrowser(state);
    const url = "https://www.nexusmods.com/games/skyrimspecialedition/mods?sort=updated";
    const dom = makeDom(nexusPage([nexusTile(1, "Alpha Armor", "Alice"), nexusTile(2, "Beta Bows", "Bob"), nexusTile(3, "Spam", "Spammer")]), url, browser);
    dom.window.fetch = async (u) => { fetched.push(String(u)); return { ok: true, text: async () => PAGE2 }; };
    load(dom, FILTER_FILES);
    const doc = dom.window.document;
    const added = await waitFor(() => doc.querySelector("[data-aos-backfill]"));
    assert.deepEqual(fetched, [url + "&page=2"]);
    assert.equal(added.id, "m4", "duplicates of items already on the page are skipped");
    assert.equal(added.parentElement.className, "grid");
    assert.equal(added.querySelector("[id^='headlessui-menu-button']"), null, "dead site menus are dropped from copies");
    await waitFor(() => added.querySelector(".aos-quick-hide"));
    await tick(300);
    assert.equal(doc.querySelectorAll("[data-aos-backfill]").length, 1, "only as many as needed");
    const shown = JSON.parse(dom.window.sessionStorage.getItem("aos-shown:/games/skyrimspecialedition/mods?sort=updated"));
    assert.deepEqual(plain(shown), { "skyrimspecialedition:4": 1 });

    // Hiding one more pulls the next buffered item without another fetch.
    doc.querySelector("#m1 > .aos-quick-hide").click();
    await waitFor(() => doc.querySelectorAll("[data-aos-backfill]").length === 2);
    assert.equal(fetched.length, 1);
    dom.window.close();

    // Page 2 hides the item that page 1 already showed.
    const dom2 = makeDom(PAGE2, url + "&page=2", nexusBrowser(state));
    dom2.window.sessionStorage.setItem("aos-shown:/games/skyrimspecialedition/mods?sort=updated", JSON.stringify({ "skyrimspecialedition:4": 1 }));
    dom2.window.fetch = async () => ({ ok: true, text: async () => nexusPage([]) });
    load(dom2, FILTER_FILES);
    const m4 = dom2.window.document.getElementById("m4");
    await waitFor(() => m4.getAttribute("data-aos-hidden"));
    assert.equal(m4.getAttribute("data-aos-reason"), "Already shown on page 1");
    dom2.window.close();
});

test("nexus: hover icons on the author and category lines hide by that value", async () => {
    const browser = nexusBrowser();
    const tile = (id, title, author, category) => nexusTile(id, title, author).replace("</div>\n    </div>",
        `<div class="cat"><a href="https://www.nexusmods.com/games/skyrimspecialedition/mods?categoryName=${category}">${category}</a></div></div>\n    </div>`);
    const dom = makeDom(nexusPage([tile(1, "Alpha", "Alice", "Armour"), tile(2, "Beta", "Bob", "Weapons"), tile(3, "Gamma", "Cid", "Armour")]),
        "https://www.nexusmods.com/games/skyrimspecialedition/mods", browser);
    dom.window.fetch = async () => ({ ok: true, text: async () => nexusPage([]) });
    load(dom, FILTER_FILES);
    const doc = dom.window.document;
    const icon = await waitFor(() => doc.querySelector("#m1 a[href*='categoryName'] > .aos-inline-hide"));
    assert.ok(doc.querySelector("#m1 a[href*='/profile/'] > .aos-inline-hide"), "author line gets an icon too");
    assert.equal(icon.title, "Agent OS: hide every mod by category Armour");
    icon.click();
    await waitFor(() => doc.getElementById("m3").getAttribute("data-aos-hidden"));
    assert.equal(doc.getElementById("m1").getAttribute("data-aos-reason"), "Category: Armour");
    assert.equal(doc.getElementById("m2").getAttribute("data-aos-hidden"), null);
    assert.match(doc.querySelector(".aos-toast-host").shadowRoot.textContent, /Hidden category Armour/);
    dom.window.close();
});

test("nexus: a next-page load waits for the page to settle and stops when a link is pressed", async () => {
    const state = Core.normalizeState(null);
    Core.addRule(state, { scope: "nexus", field: "author", value: "Spammer" });
    const calls = [];
    const dom = makeDom(nexusPage([nexusTile(1, "Alpha", "Alice"), nexusTile(3, "Spam", "Spammer")]),
        "https://www.nexusmods.com/games/skyrimspecialedition/mods", nexusBrowser(state));
    dom.window.fetch = (url, options) => new Promise((resolve, reject) => {
        calls.push({ url: String(url), signal: options && options.signal });
        if (options && options.signal) options.signal.addEventListener("abort", () => reject(new Error("aborted")));
    });
    const started = Date.now();
    load(dom, FILTER_FILES);
    const doc = dom.window.document;
    await waitFor(() => calls.length === 1, 4000);
    assert.ok(Date.now() - started >= 700, "no fetch until the list has been quiet for a moment");
    doc.querySelector("#m1 a").dispatchEvent(new dom.window.MouseEvent("pointerdown", { bubbles: true }));
    assert.equal(calls[0].signal.aborted, true, "pressing a link cancels the background page load");
    await waitFor(() => calls.length === 2, 4000);
    assert.equal(calls[1].url, calls[0].url, "the same page is retried after the page settles again");
    dom.window.close();
});

test("nexus: the next page comes from the page's own list query, copied into real tiles", async () => {
    const state = Core.normalizeState(null);
    Core.addRule(state, { scope: "nexus", field: "author", value: "Spammer" });
    const fullTile = (id, title, author, category) => `<div class="group/mod-tile flex" id="m${id}">
      <div class="relative"><a href="https://www.nexusmods.com/skyrimspecialedition/mods/${id}"><img src="https://staticdelivery.nexusmods.com/mods/1704/images/thumbnails/${id}/t.png"></a></div>
      <div class="px-3"><div><a href="https://www.nexusmods.com/skyrimspecialedition/mods/${id}">${title}</a>
        <a class="flex" href="https://www.nexusmods.com/profile/${author}?gameId=1704"><img src="https://avatars.nexusmods.com/1/100"><span>${author}</span></a></div>
        <div><a href="/games/skyrimspecialedition/mods?categoryName=${category}">${category}</a> <time datetime="2026-10-01T00:00:00Z">5 days ago</time> <time datetime="2023-02-12T00:00:00Z">12 Feb 2023</time></div>
        <p>A long enough summary for ${title} that describes what the mod does in detail.</p></div>
      <div><span>Endorsements</span><span>5</span><span>Downloads</span><span>1.2k</span><span>File size</span><span>3.0MB</span></div>
    </div>`;
    const apiCalls = [];
    const browser = nexusBrowser(state);
    const dom = makeDom(nexusPage([fullTile(1, "Alpha", "Alice", "Armour"), fullTile(2, "Beta", "Bob", "Weapons"), fullTile(3, "Spam", "Spammer", "Armour")]),
        "https://www.nexusmods.com/games/skyrimspecialedition/mods", browser);
    dom.window.wrappedJSObject = dom.window;
    dom.window.exportFunction = (fn) => fn;
    dom.window.fetch = async (url, init) => {
        const body = JSON.parse(init && init.body || "{}");
        if (body.operationName === "AgentOsNextPage") {
            apiCalls.push({ url: String(url), body, headers: init.headers, credentials: init.credentials });
            return { ok: true, json: async () => ({ data: { mods: { nodes: [{
                modId: 77, name: "Next Page Mod", summary: "Fresh summary from the API.", uploader: { name: "Nia", avatar: "" },
                modCategory: { name: "Magic" }, game: { domainName: "skyrimspecialedition" },
                thumbnailUrl: "https://staticdelivery.nexusmods.com/mods/1704/images/thumbnails/77/x.png",
                endorsements: 1500, downloads: 274400, fileSize: 2048, updatedAt: "2026-10-06T00:00:00Z", createdAt: "2026-01-05T00:00:00Z"
            }] } } }) };
        }
        return { ok: true, json: async () => ({ data: {} }) };
    };
    load(dom, FILTER_FILES);
    // The page asks for its list the way Nexus does.
    await dom.window.fetch("https://api-router.nexusmods.com/graphql", {
        method: "POST", credentials: "include", headers: { "Content-Type": "application/json", "x-test": "1" },
        body: JSON.stringify({ query: "query ModsListing($filter: ModsFilter) { mods(filter: $filter) { nodes { modId } } }",
            variables: { filter: { gameDomainName: [{ value: "skyrimspecialedition", op: "EQUALS" }] }, facets: { categoryName: [] }, sort: [{ updatedAt: { direction: "DESC" } }], offset: 0, count: 3 } })
    });
    const doc = dom.window.document;
    const added = await waitFor(() => doc.querySelector("[data-aos-backfill]"), 4000);
    assert.equal(apiCalls.length, 1);
    assert.equal(apiCalls[0].body.variables.offset, 3, "next page after the page's own offset");
    assert.equal(apiCalls[0].body.variables.count, 3);
    assert.equal(apiCalls[0].body.variables.facets, undefined, "category counts are not requested");
    assert.equal(apiCalls[0].headers["x-test"], "1", "the page's own headers are reused");
    assert.equal(apiCalls[0].credentials, "include");
    const links = Array.from(added.querySelectorAll("a")).map((a) => [a.getAttribute("href"), a.textContent.trim()]);
    assert.deepEqual(links[1], ["https://www.nexusmods.com/skyrimspecialedition/mods/77", "Next Page Mod"]);
    assert.equal(links[2][0], "https://www.nexusmods.com/profile/Nia?gameId=1704");
    assert.match(links[2][1], /^Nia/);
    assert.equal(links[3][0], "/games/skyrimspecialedition/mods?categoryName=Magic");
    assert.equal(added.querySelector("img").getAttribute("src"), "https://staticdelivery.nexusmods.com/mods/1704/images/thumbnails/77/x.png");
    assert.equal(added.querySelector("p").textContent, "Fresh summary from the API.");
    assert.equal(added.querySelectorAll("time")[1].textContent, "5 Jan 2026");
    assert.deepEqual(Array.from(added.querySelectorAll("div:last-child > span")).map((s) => s.textContent), ["Endorsements", "1.5k", "Downloads", "274k", "File size", "2.0MB"]);
    dom.window.close();
});

test("old reddit: an always-visible hide icon sits next to each post's subreddit", async () => {
    const browser = makeBrowser({ onBackgroundMessage: backgroundFor() });
    const post = (id, sub) => `<div class="thing link" id="t3_${id}" data-subreddit="${sub}" data-author="u${id}" data-fullname="t3_${id}">
      <p class="title"><a class="title" href="/r/${sub}/comments/${id}/x/">Post ${id}</a></p>
      <p class="tagline">submitted by <a class="author" href="https://old.reddit.com/user/u${id}">u${id}</a> to <a class="subreddit hover" href="https://old.reddit.com/r/${sub}/">r/${sub}</a></p></div>`;
    const dom = makeDom(`<!doctype html><html><body><div id="siteTable">${post("a", "pics")}${post("b", "news")}</div></body></html>`, "https://old.reddit.com/", browser);
    load(dom, FILTER_FILES);
    const doc = dom.window.document;
    const icon = await waitFor(() => doc.querySelector("#t3_a a.subreddit + .aos-inline-hide.aos-inline-always"));
    assert.equal(icon.title, "Agent OS: hide r/pics");
    icon.click();
    await waitFor(() => doc.getElementById("t3_a").getAttribute("data-aos-hidden"));
    assert.equal(doc.getElementById("t3_b").getAttribute("data-aos-hidden"), null);
    assert.equal(Core.normalizeState(browser._data[Core.STORAGE_KEY]).rules[0].field, "subreddit");
    dom.window.close();
});
