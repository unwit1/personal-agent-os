/*
 * Agent OS: ADP sign-in test.
 *
 * Active only in the background tab the extension opens for an ADP sign-in
 * test. On ADP's own sign-in page it fills the saved user ID / password
 * (from Windows Credential Manager, handed out by the background page to
 * this tab only) and reports where it lands: signed in, a verification code
 * is needed, the sign-in was rejected, or nothing happened. It never enters
 * verification codes or clicks past security prompts.
 */
(function () {
    "use strict";

    if (window.top !== window) return;
    if (!/(^|\.)adp\.com$/i.test(location.hostname)) return;

    var acted = {};
    var reported = false;
    var timer = null;

    function send(message) {
        return browser.runtime.sendMessage(message);
    }

    // querySelector that also looks inside (open or closed) shadow roots;
    // ADP's sign-in form is built from web components.
    function deep(selector, root) {
        root = root || document;
        var found = root.querySelector(selector);
        if (found) return found;
        var all = root.querySelectorAll("*");
        for (var i = 0; i < all.length; i += 1) {
            var shadow = all[i].openOrClosedShadowRoot || all[i].shadowRoot;
            if (shadow) {
                found = deep(selector, shadow);
                if (found) return found;
            }
        }
        return null;
    }

    function inputOf(el) {
        if (!el) return null;
        if (el.localName === "input") return el;
        var shadow = el.openOrClosedShadowRoot || el.shadowRoot;
        return (shadow && shadow.querySelector("input")) || el.querySelector("input");
    }

    function shown(el) {
        if (!el) return false;
        var rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    }

    var FILL_TRIES = 2;
    var SUBMIT_WAIT_MS = 15000;
    var REFILL_AFTER_MS = 3000;

    function fill(input, value) {
        input.focus();
        input.value = value;
        input.dispatchEvent(new InputEvent("input", { bubbles: true, composed: true, inputType: "insertText", data: value }));
        input.dispatchEvent(new Event("change", { bubbles: true, composed: true }));
        input.blur();
    }

    // ADP's sdf-input marks itself "is-empty" until it has taken the typed value.
    function registered(host) {
        return !(host.classList && host.classList.contains("is-empty"));
    }

    function enabled(button) {
        return !button.hasAttribute("disabled") && !(button.classList && button.classList.contains("disabled"));
    }

    // Fills one saved-login field; force fills it again (up to FILL_TRIES in all).
    // Returns "absent", "done", "filled" (wait a tick), "stuck" or "failed" (already reported).
    async function fillField(host, field, force) {
        var input = inputOf(host);
        if (!input || !shown(host)) return "absent";
        // "is-empty" is not always updated for password fields, so a value this test filled counts as done.
        if (!force && input.value && (registered(host) || acted[field])) return "done";
        var tries = acted[field] || 0;
        if (tries >= FILL_TRIES) return "stuck";
        var cred = await send({ type: "adp-credential", field: field });
        if (!cred || !cred.value) {
            report("no_credentials", cred && cred.error || (field === "password" ? "No saved ADP password." : "No saved ADP user ID."));
            return "failed";
        }
        acted[field] = tries + 1;
        fill(input, cred.value);
        return "filled";
    }

    function press(button) {
        var shadow = button.openOrClosedShadowRoot || button.shadowRoot;
        var inner = shadow && shadow.querySelector("button");
        (inner || button).click();
    }

    function pageText() {
        var body = document.body;
        return String(body ? body.innerText || body.textContent : "").toLowerCase();
    }

    function report(status, detail) {
        if (reported) return;
        reported = true;
        if (timer) clearInterval(timer);
        send({ type: "adp-probe-result", status: status, detail: detail || "",
            page: location.origin + location.pathname, title: document.title });
    }

    async function step() {
        var text = pageText();
        if (/(^|\.)workforcenow\.adp\.com$/i.test(location.hostname) && !/signin|login/i.test(location.pathname)) {
            if (document.readyState === "complete") report("signed_in", "Reached ADP Workforce Now.");
            return;
        }
        if (deep("input[autocomplete='one-time-code']") ||
                /verification code|verify (your )?identity|one-time (pass)?code|enter the code|we sent (you )?a code|security code/.test(text)) {
            report("needs_code", "ADP asked for a verification code.");
            return;
        }
        if (acted.password && /incorrect|invalid user id|password (is )?(incorrect|invalid)|locked|unable to sign in|try again later/.test(text)) {
            report("rejected", "ADP did not accept the saved sign-in.");
            return;
        }
        // The user ID comes first: on its own page (remembered device) or, on a
        // device ADP does not know yet, above the password on the same page.
        // Buttons are pressed on a later tick, once ADP has taken the values and enabled them.
        var user = deep("#login-form_username");
        var userState = await fillField(user, "username");
        if (userState === "stuck") { report("error", "ADP did not take the saved user ID."); return; }
        if (userState === "failed" || userState === "filled") return;
        var password = deep("#login-form_password");
        var next = deep("#verifUseridBtn");
        if (next && shown(next) && !(password && shown(password))) {
            if (userState === "done" && !acted.next && enabled(next)) { acted.next = true; press(next); }
            return;
        }
        var passwordState = await fillField(password, "password");
        if (passwordState === "stuck") { report("error", "ADP did not take the saved password."); return; }
        if (passwordState !== "done") return;
        var signIn = deep("#signBtn");
        if (acted.forcedSignIn && Date.now() - acted.forcedSignIn > SUBMIT_WAIT_MS) {
            report("error", "ADP kept Sign in disabled after the saved sign-in was filled.");
            return;
        }
        if (!signIn || acted.signIn) return;
        if (enabled(signIn)) { acted.signIn = true; press(signIn); return; }
        acted.waitingSince = acted.waitingSince || Date.now();
        var waited = Date.now() - acted.waitingSince;
        if (waited > REFILL_AFTER_MS && !registered(password) && (acted.password || 0) < FILL_TRIES) {
            acted.waitingSince = 0;
            await fillField(password, "password", true);
            return;
        }
        if (waited > SUBMIT_WAIT_MS) {
            // The disabled look is not always enforced; one press, then the page's answer decides.
            acted.signIn = true;
            acted.forcedSignIn = Date.now();
            press(signIn);
        }
    }

    send({ type: "adp-probe-state" }).then(function (state) {
        if (!state || !state.active) return;
        timer = setInterval(function () {
            step().catch(function (error) { report("error", String(error && error.message || error)); });
        }, 1000);
    });
})();
