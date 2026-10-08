"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const Core = require("../src/lib/filter-core.js");

function stateWith(rules, sites) {
    const state = Core.normalizeState({ sites: sites || {} });
    rules.forEach((r) => Core.addRule(state, r));
    return state;
}

function hit(state, facets, context) {
    return Core.evaluate(Core.compileRules(state), facets, Object.assign({ host: "www.reddit.com", scope: "reddit" }, context));
}

test("subreddit rules match the whole name, with r/ prefix and wildcards", () => {
    const state = stateWith([
        { scope: "reddit", field: "subreddit", value: "r/pics" },
        { scope: "reddit", field: "subreddit", value: "Blorptown*" }
    ]);
    assert.ok(hit(state, { subreddit: "pics" }));
    assert.ok(hit(state, { subreddit: "PICS" }));
    assert.equal(hit(state, { subreddit: "picsofdogs" }), null);
    assert.ok(hit(state, { subreddit: "blorptownmemes" }));
});

test("keywords match whole words in title and summary only", () => {
    const state = stateWith([{ scope: "*", field: "keyword", value: "elf" }]);
    assert.ok(hit(state, { title: "An elf walks into a bar" }));
    assert.equal(hit(state, { title: "Self-care tips" }), null);
    assert.ok(hit(state, { title: "x", text: "the ELF returns" }, { scope: "ao3" }));
});

test("regex values and domain suffixes", () => {
    const state = stateWith([
        { scope: "search", field: "domain", value: "pinterest.com" },
        { scope: "*", field: "keyword", value: "/\\bAI[- ]generated\\b/" }
    ]);
    assert.ok(hit(state, { domain: "www.pinterest.com" }, { scope: "search" }));
    assert.ok(hit(state, { domain: "uk.pinterest.com" }, { scope: "search" }));
    assert.equal(hit(state, { domain: "notpinterest.com" }, { scope: "search" }), null);
    assert.ok(hit(state, { title: "Some ai-generated slop" }, { scope: "search" }));
});

test("scope and host restrictions", () => {
    const state = stateWith([
        { scope: "xenforo", field: "author", value: "Spammer", host: "spacebattles.com" }
    ]);
    assert.ok(hit(state, { author: "spammer" }, { scope: "xenforo", host: "forums.spacebattles.com" }));
    assert.equal(hit(state, { author: "spammer" }, { scope: "xenforo", host: "forums.sufficientvelocity.com" }), null);
    assert.equal(hit(state, { author: "spammer" }, { scope: "ao3", host: "forums.spacebattles.com" }), null);
});

test("viewing a subreddit or game exempts its own items", () => {
    const state = stateWith([
        { scope: "reddit", field: "subreddit", value: "skyrimmods" },
        { scope: "nexus", field: "game", value: "Skyrim Special Edition" }
    ]);
    assert.equal(hit(state, { subreddit: "skyrimmods" }, { exempt: { subreddit: "skyrimmods" } }), null);
    assert.ok(hit(state, { subreddit: "skyrimmods" }, { exempt: { subreddit: "pics" } }));
    const facets = { game: "skyrimspecialedition", gameName: "Skyrim Special Edition" };
    assert.equal(hit(state, facets, { scope: "nexus", exempt: { game: "skyrimspecialedition" } }), null);
    assert.ok(hit(state, facets, { scope: "nexus" }));
});

test("tag rules cover AO3 warnings, ratings and categories; Nexus tags", () => {
    const state = stateWith([
        { scope: "ao3", field: "tag", value: "Major Character Death" },
        { scope: "nexus", field: "tag", value: "Lore-Friendly" }
    ]);
    assert.ok(hit(state, { warning: ["Major Character Death"] }, { scope: "ao3" }));
    assert.ok(hit(state, { tag: ["Fluff", "Lore-Friendly"] }, { scope: "nexus" }));
});

test("site settings: AO3 fandom limit, word minimum, WIP, Reddit promoted", () => {
    const state = stateWith([]);
    const ao3 = { maxFandoms: 3, minWords: 1000, hideWip: true };
    assert.match(hit(state, { fandomCount: 5 }, { scope: "ao3", siteSettings: ao3 }).reason, /fandoms/);
    assert.match(hit(state, { fandomCount: 1, words: 200 }, { scope: "ao3", siteSettings: ao3 }).reason, /words/);
    assert.match(hit(state, { fandomCount: 1, words: 5000, complete: false }, { scope: "ao3", siteSettings: ao3 }).reason, /progress/);
    assert.equal(hit(state, { fandomCount: 1, words: 5000, complete: true }, { scope: "ao3", siteSettings: ao3 }), null);
    assert.ok(hit(state, { promoted: true }, { siteSettings: { hidePromoted: true } }));
});

test("disabled rules and duplicate adds", () => {
    const state = stateWith([{ scope: "reddit", field: "subreddit", value: "pics" }]);
    assert.equal(Core.addRule(state, { scope: "reddit", field: "subreddit", value: "PICS" }), false);
    state.rules[0].enabled = false;
    assert.equal(hit(state, { subreddit: "pics" }), null);
});

test("imports Subreddit Hider lists, plain text and Agent OS exports", () => {
    const state = Core.normalizeState(null);
    assert.equal(Core.importRules(state, '{"blockedSubreddits":["pics","r/funny"],"blockedKeywords":["spoiler"]}'), 3);
    assert.equal(Core.importRules(state, "aww, gaming\nmemes"), 3);
    assert.equal(Core.importRules(state, "Lore-Friendly", { scope: "nexus", field: "tag" }), 1);
    const exported = JSON.stringify({ rules: state.rules });
    const fresh = Core.normalizeState(null);
    assert.equal(Core.importRules(fresh, exported), 7);
    assert.equal(fresh.rules.find((r) => r.value === "funny").field, "subreddit");
});

test("hide options list every facet once", () => {
    const options = Core.hideOptionsFor({ subreddit: "pics", author: ["bob", "bob"], domain: "imgur.com", id: "t3_x" }, "reddit");
    assert.deepEqual(options.map((o) => o.field), ["subreddit", "author", "domain", "id"]);
});

test("nexus hideTranslations setting (on by default)", () => {
    const state = Core.normalizeState(null);
    assert.equal(state.sites.nexus.hideTranslations, true);
    const result = hit(state, { translation: "Deutsch" }, { scope: "nexus", siteSettings: state.sites.nexus });
    assert.equal(result.reason, "Translation (Deutsch)");
    assert.equal(hit(state, { translation: false }, { scope: "nexus", siteSettings: state.sites.nexus }), null);
});
