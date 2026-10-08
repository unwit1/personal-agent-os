/* Agent OS: ADP sign-in window (save login, run the sign-in test). */
(function () {
    "use strict";

    var $ = function (id) { return document.getElementById(id); };
    var LABELS = {
        running: "Testing… a background ADP tab is signing in.",
        signed_in: "Signed in to ADP without any input.",
        needs_code: "ADP asked for a verification code, so sign-in cannot finish unattended yet.",
        rejected: "ADP did not accept the saved user ID or password.",
        no_credentials: "No saved ADP sign-in.",
        timeout: "Nothing happened within two minutes.",
        error: "The test failed."
    };

    function showResult(last) {
        var el = $("result");
        if (!last) { el.textContent = "Not run yet."; el.removeAttribute("data-status"); return; }
        el.dataset.status = last.status;
        var when = last.finishedAt ? new Date(last.finishedAt).toLocaleString() : "";
        el.textContent = (LABELS[last.status] || last.status) + (last.detail ? " " + last.detail : "") + (when ? " (" + when + ")" : "");
    }

    function refresh() {
        browser.runtime.sendMessage({ type: "adp-status" }).then(function (status) {
            status = status || {};
            $("saved").textContent = status.hasPassword
                ? "A sign-in is saved" + (status.hasUsername ? " (user ID and password)." : " (password only).")
                : "No sign-in saved yet.";
            showResult(status.running ? { status: "running" } : status.last);
        });
    }

    $("form").addEventListener("submit", function (event) {
        event.preventDefault();
        var username = $("username").value.trim();
        var password = $("password").value;
        if (!password) { $("saved").textContent = "Enter the password."; return; }
        browser.runtime.sendMessage({ type: "adp-save-login", username: username, password: password }).then(function (res) {
            $("password").value = "";
            if (!res || !res.ok) { $("saved").textContent = "Could not save: " + (res && res.error || "unknown error"); return; }
            return browser.runtime.sendMessage({ type: "adp-probe-start" });
        }).then(refresh);
    });

    $("test").addEventListener("click", function () {
        browser.runtime.sendMessage({ type: "adp-probe-start" }).then(function (res) {
            if (res && !res.ok) $("saved").textContent = res.error;
            refresh();
        });
    });

    // login.html?autostart=1 (opened by Agent OS) runs the test once, unattended, then closes this tab.
    var AUTOSTART_GAP_MS = 60000;
    var autostarted = false;

    browser.storage.onChanged.addListener(function (changes, area) {
        if (area !== "local" || !changes.adp_probe_last) return;
        refresh();
        if (autostarted) browser.tabs.getCurrent().then(function (tab) { if (tab) browser.tabs.remove(tab.id); });
    });
    refresh();

    if (new URLSearchParams(location.search).get("autostart") === "1") {
        // A reload or restored tab must not sign in again.
        history.replaceState(null, "", location.pathname);
        browser.runtime.sendMessage({ type: "adp-status" }).then(function (status) {
            var last = status && status.last;
            var recent = last && last.finishedAt && Date.now() - Date.parse(last.finishedAt) < AUTOSTART_GAP_MS;
            if (!status || status.running || recent) return;
            autostarted = true;
            $("test").click();
        });
    }
})();
