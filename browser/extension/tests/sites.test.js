"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM, VirtualConsole } = require("jsdom");
const Sites = require("../src/lib/sites.js");

function page(html, url) {
    // Real pages carry CSS jsdom cannot parse; that noise is irrelevant here.
    const dom = new JSDOM(html, { url, virtualConsole: new VirtualConsole() });
    return dom.window.document;
}

function itemsAndFacets(doc, scope) {
    const adapter = Sites.adaptersFor(doc.location, doc, []).find((a) => a.scope === scope);
    assert.ok(adapter, "adapter " + scope + " should match " + doc.location.href);
    return adapter.items(doc, doc).map((el) => ({
        el,
        facets: adapter.facets(el, { host: doc.location.hostname, href: doc.location.href }),
        target: adapter.target ? adapter.target(el) : el
    }));
}

test("reddit: shreddit posts, ads, comments and old reddit things", () => {
    const doc = page(`<main>
      <article><shreddit-post subreddit-prefixed-name="r/pics" author="alice" post-title="A cat"
         domain="i.redd.it" id="t3_a" permalink="/r/pics/comments/a/x/"></shreddit-post></article>
      <article><shreddit-ad-post subreddit-prefixed-name="u/brand" post-title="Buy now" promoted></shreddit-ad-post></article>
      <shreddit-post subreddit-prefixed-name="r/news" author="bob" post-title="Story" domain="example.com" nsfw></shreddit-post>
      <shreddit-comment author="carol" thingid="t1_c"></shreddit-comment>
      <div class="thing link" data-subreddit="gaming" data-author="dave" data-domain="youtube.com" data-promoted="false" data-fullname="t3_d">
        <a class="title">Old title</a><span class="linkflairlabel">Video</span></div>
    </main>`, "https://www.reddit.com/r/popular/");
    const items = itemsAndFacets(doc, "reddit");
    assert.equal(items.length, 5);
    assert.equal(items[0].facets.subreddit, "pics");
    assert.equal(items[0].facets.domain, "", "reddit-hosted media is not a domain facet");
    assert.equal(items[0].target.tagName, "ARTICLE", "hide the feed wrapper, not just the custom element");
    assert.equal(items[1].facets.promoted, true);
    assert.equal(items[2].facets.domain, "example.com");
    assert.equal(items[2].facets.nsfw, true);
    assert.deepEqual(items[3].facets, { author: "carol", id: "t1_c" });
    assert.equal(items[4].facets.subreddit, "gaming");
    assert.deepEqual(items[4].facets.flair, ["Video"]);
    const reddit = Sites.byScope.reddit;
    assert.deepEqual(reddit.exempt(new URL("https://www.reddit.com/r/skyrimmods/")), { subreddit: "skyrimmods" });
    assert.deepEqual(reddit.exempt(new URL("https://www.reddit.com/r/all/")), {});
});

test("nexus: tiles found by link, page's own mod and description links skipped", () => {
    const doc = page(`<main>
      <div class="grid">
        <div class="tile"><a href="/skyrimspecialedition/mods/266"><img src="a.jpg"></a>
          <a href="/skyrimspecialedition/mods/266">USSEP</a> <a href="/users/684492">Arthmoor</a>
          <a href="/games/skyrimspecialedition/mods?categories=95">Bug Fixes</a></div>
        <div class="tile"><a href="https://www.nexusmods.com/stardewvalley/mods/2400"><img src="b.jpg"></a>
          <h3>SMAPI</h3></div>
        <div class="tile"><a href="/games/skyrimspecialedition/collections/abc123"><img src="c.jpg"></a><h3>A collection</h3></div>
      </div>
      <div id="description"><p>Requires <a href="/skyrimspecialedition/mods/12604">SKSE</a></p></div>
    </main>`, "https://www.nexusmods.com/games/skyrimspecialedition/mods");
    const items = itemsAndFacets(doc, "nexus");
    assert.equal(items.length, 3);
    assert.equal(items[0].facets.id, "skyrimspecialedition:266");
    assert.equal(items[0].facets.game, "skyrimspecialedition");
    assert.deepEqual(items[0].facets.author, ["Arthmoor"]);
    assert.deepEqual(items[0].facets.category, ["Bug Fixes"]);
    assert.deepEqual(items[0].facets.lookup, { game: "skyrimspecialedition", modId: "266", key: "skyrimspecialedition:266" });
    assert.equal(items[1].facets.title, "SMAPI");
    assert.equal(items[2].facets.kind, "collection");
    assert.equal(items[2].facets.lookup, null);

    const enriched = Sites.byScope.nexus.enrich(items[0].facets, {
        name: "USSEP", uploader: "Arthmoor", category: "Bug Fixes", gameName: "Skyrim Special Edition",
        tags: ["Lore-Friendly"], adult: false
    });
    assert.deepEqual(enriched.tag, ["Lore-Friendly"]);
    assert.equal(enriched.gameName, "Skyrim Special Edition");

    const modPage = page(`<main><h1>USSEP</h1><a href="/skyrimspecialedition/mods/266?tab=files"><img></a></main>`,
        "https://www.nexusmods.com/skyrimspecialedition/mods/266");
    assert.equal(itemsAndFacets(modPage, "nexus").length, 0, "never hide the mod page itself");
});

test("ao3: work blurbs with fandoms, required tags and stats", () => {
    const doc = page(`<ol class="work index group">
      <li class="work blurb group" id="work_1">
        <div class="header module">
          <h4 class="heading"><a href="/works/123">Title</a> by <a rel="author" href="/users/writer/pseuds/writer">writer</a></h4>
          <h5 class="fandoms heading"><a class="tag" href="/tags/A/works">Fandom A</a>, <a class="tag" href="/tags/B/works">Fandom B</a></h5>
          <ul class="required-tags">
            <li><a class="help symbol question modal" title="Symbols key"><span class="rating-explicit rating" title="Explicit"><span class="text">Explicit</span></span></a></li>
            <li><a><span class="warning-yes warnings" title="Major Character Death"><span class="text">Major Character Death</span></span></a></li>
            <li><a><span class="category-slash category" title="M/M, F/M"><span class="text">M/M, F/M</span></span></a></li>
            <li><a><span class="complete-no iswip" title="Work in Progress"><span class="text">Work in Progress</span></span></a></li>
          </ul>
        </div>
        <ul class="tags commas">
          <li class="warnings"><a class="tag">Major Character Death</a></li>
          <li class="relationships"><a class="tag">A/B</a></li>
          <li class="characters"><a class="tag">Character C</a></li>
          <li class="freeforms"><a class="tag">Angst</a></li>
        </ul>
        <blockquote class="userstuff summary"><p>Summary text</p></blockquote>
        <dl class="stats"><dd class="language">English</dd><dd class="words">12,345</dd></dl>
      </li>
    </ol>`, "https://archiveofourown.org/tags/Fandom%20A/works");
    const [item] = itemsAndFacets(doc, "ao3");
    const f = item.facets;
    assert.equal(f.id, "works:123");
    assert.deepEqual(f.author, ["writer"]);
    assert.deepEqual(f.fandom, ["Fandom A", "Fandom B"]);
    assert.equal(f.fandomCount, 2);
    assert.deepEqual(f.rating, ["Explicit"]);
    assert.deepEqual(f.warning, ["Major Character Death"]);
    assert.deepEqual(f.category, ["M/M", "F/M"]);
    assert.deepEqual(f.tag, ["A/B", "Character C", "Angst"]);
    assert.equal(f.language, "English");
    assert.equal(f.words, 12345);
    assert.equal(f.complete, false);
    assert.equal(Sites.ao3TagFromPath("Harry%20Potter%20*a*%20Co*s*Friends"), "Harry Potter & Co/Friends");
});

test("xenforo: thread rows (SpaceBattles markup) and posts", () => {
    const doc = page(`<html id="XF"><body>
      <div class="structItem structItem--thread js-inlineModContainer js-threadListItem-1140820" data-author="Summertime Madness">
        <div class="structItem-cell structItem-cell--main">
          <div class="structItem-title"><a class="labelLink"><span class="label">Quest</span></a>
            <a href="/threads/trending-stories.1140820/" data-tp-primary="on">Trending Stories</a></div>
          <div class="structItem-minor"><ul class="structItem-parts"><li><a class="username">Summertime Madness</a></li>
            <li><a href="/forums/creative-writing.18/">Creative Writing</a></li></ul></div>
          <span class="structItem-tagBlock"><a class="tagItem">creative writing</a></span>
        </div>
      </div>
      <div class="structItem structItem--thread"><div class="structItem-cell--main">Sticky Threads</div></div>
      <article class="message" data-author="Poster" data-content="post-99"></article>
    </body></html>`, "https://forums.spacebattles.com/forums/creative-writing.18/");
    const items = itemsAndFacets(doc, "xenforo");
    assert.equal(items.length, 2, "collapse-trigger rows without data-author are ignored");
    const thread = items[0].facets;
    assert.equal(thread.title, "Trending Stories");
    assert.equal(thread.author, "Summertime Madness");
    assert.deepEqual(thread.prefix, ["Quest"]);
    assert.deepEqual(thread.tag, ["creative writing"]);
    assert.deepEqual(thread.forum, ["Creative Writing"]);
    assert.equal(thread.id, "forums.spacebattles.com:thread:1140820");
    assert.equal(items[1].facets.kind, "post");
    assert.equal(items[1].facets.author, "Poster");
});

test("ffn: info line parsing", () => {
    const info = "Crossover - Harry Potter & Elder Scroll series - Rated: T - English - Adventure/Hurt/Comfort - Chapters: 12 - Words: 45,210 - Reviews: 10 - Updated: 1h - Published: 2h - Harry P., [Hermione G., Ron W.] - Complete";
    const parsed = Sites.parseFfnInfo(info);
    assert.deepEqual(parsed.fandom, ["Harry Potter", "Elder Scroll series"]);
    assert.deepEqual(parsed.rating, ["T"]);
    assert.equal(parsed.language, "English");
    assert.ok(parsed.tag.includes("Adventure") && parsed.tag.includes("Hurt/Comfort"));
    assert.ok(parsed.tag.includes("Hermione G."));
    assert.equal(parsed.words, 45210);
    assert.equal(parsed.complete, true);
});

test("youtube: lockups, channel handles and shorts", () => {
    const doc = page(`<div>
      <ytd-rich-item-renderer><yt-lockup-view-model>
        <a href="/watch?v=abcdefghijk"></a><h3 title="Video title">Video title</h3>
        <a href="/@SomeChannel">Some Channel</a></yt-lockup-view-model></ytd-rich-item-renderer>
      <ytd-reel-shelf-renderer><ytd-reel-item-renderer><a href="/shorts/zzzzzzzzzzz"></a></ytd-reel-item-renderer></ytd-reel-shelf-renderer>
    </div>`, "https://www.youtube.com/");
    const items = itemsAndFacets(doc, "youtube");
    assert.equal(items.length, 2, "nested lockup counted once");
    assert.deepEqual(items[0].facets.channel, ["Some Channel", "SomeChannel"]);
    assert.equal(items[0].facets.id, "yt:abcdefghijk");
    assert.equal(items[1].facets.short, true);
});

test("search: DuckDuckGo redirect links resolve to the real domain", () => {
    const doc = page(`<div class="result results_links"><h2 class="result__title">
      <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.pinterest.com%2Fpin%2F1">Pin</a></h2>
      <a class="result__snippet">snippet</a></div>`, "https://html.duckduckgo.com/html/?q=x");
    const [item] = itemsAndFacets(doc, "search");
    assert.equal(item.facets.domain, "pinterest.com");
});

test("link hide options", () => {
    const base = "https://www.google.com/search?q=x";
    assert.deepEqual(Sites.linkHideOptions("https://www.reddit.com/r/pics/", "r/pics", base)[0],
        { scope: "reddit", field: "subreddit", value: "pics", label: "Hide r/pics" });
    const ao3 = Sites.linkHideOptions("https://archiveofourown.org/tags/Angst/works", "Angst", "https://archiveofourown.org/works");
    assert.equal(ao3[0].value, "Angst");
    const nexus = Sites.linkHideOptions("https://www.nexusmods.com/games/stardewvalley", "Stardew Valley", "https://www.nexusmods.com/");
    assert.equal(nexus[0].field, "game");
    assert.equal(nexus[0].value, "stardewvalley");
    const yt = Sites.linkHideOptions("https://www.youtube.com/@Chan", "Chan", "https://www.youtube.com/");
    assert.equal(yt[0].value, "Chan");
});

// Optional: run adapters against pages saved from the live sites.
const LIVE = process.env.AOS_LIVE_FIXTURES;
test("live fixtures", { skip: !LIVE && "set AOS_LIVE_FIXTURES to a folder of saved pages" }, () => {
    const cases = [
        ["sb_forum.html", "https://forums.spacebattles.com/forums/creative-writing.18/", "xenforo", 20],
        ["sv_forum.html", "https://forums.sufficientvelocity.com/forums/user-fiction.2/", "xenforo", 20],
        ["qq_forum.html", "https://forum.questionablequesting.com/forums/creative-writing.19/", "xenforo", 15],
        ["ddg.html", "https://html.duckduckgo.com/html/?q=skyrim+mods", "search", 5]
    ];
    cases.forEach(([file, url, scope, min]) => {
        const full = path.join(LIVE, file);
        if (!fs.existsSync(full)) return;
        const doc = page(fs.readFileSync(full, "utf8"), url);
        const items = itemsAndFacets(doc, scope);
        assert.ok(items.length >= min, file + ": expected >= " + min + " items, got " + items.length);
        const withTitle = items.filter((i) => i.facets.title || i.facets.subreddit || i.facets.author).length;
        assert.ok(withTitle >= min, file + ": facets missing (" + withTitle + ")");
        if (scope === "xenforo") assert.ok(items.every((i) => i.facets.author), file + ": every thread has an author");
        if (scope === "search") assert.ok(items.every((i) => i.facets.domain), file + ": every result has a domain");
        console.log(file, items.length, JSON.stringify(items[1].facets).slice(0, 200));
    });
});

test("old.reddit.com redirect", () => {
    const r = Sites.oldRedditRedirect;
    assert.equal(r("https://www.reddit.com/r/popular/"), "https://old.reddit.com/r/popular/");
    assert.equal(r("https://reddit.com/r/x/comments/abc/t/?sort=new"), "https://old.reddit.com/r/x/comments/abc/t/?sort=new");
    assert.equal(r("https://new.reddit.com/user/bob"), "https://old.reddit.com/user/bob");
    assert.equal(r("https://old.reddit.com/r/all"), null, "no loop");
    assert.equal(r("https://www.reddit.com/media?url=x"), null);
    assert.equal(r("https://www.reddit.com/r/pics/s/AbC123"), null, "share links resolve on www first");
    assert.equal(r("https://www.reddit.com/settings/account"), null);
    assert.equal(r("https://www.reddit.com/r/pics/?aos_new=1"), null, "explicit opt-out");
    assert.equal(r("https://i.redd.it/x.png"), null);
});

test("nexus translation detection", () => {
    const t = Sites.nexusTranslation;
    assert.equal(t("SkyUI Russian translation", [], []), true);
    assert.equal(t("SkyUI", ["Russian", "Translation"], []), true, "Nexus Translation tag");
    assert.equal(t("Spolszczenie SkyUI", [], []), true);
    assert.equal(t("Skyrim 汉化", [], []), true);
    assert.equal(t("USSEP - Deutsch", [], []), "Deutsch");
    assert.equal(t("Some mod", ["Brazilian Portuguese"], []), "Brazilian Portuguese", "language-only tags");
    assert.equal(t("Immersive Armors", ["English", "Japanese"], []), false, "multi-language originals stay");
    assert.equal(t("Elder Scrolls Translator Tool", [], []), false);
    assert.equal(t("Realistic Water Two", ["Lore-Friendly"], ["Environmental"]), false);
    const facets = Sites.byScope.nexus.enrich({ title: "SkyUI", author: [], category: [] },
        { name: "SkyUI - Russian", tags: ["Translation"], category: "User Interface" });
    assert.equal(facets.translation, true);
});
