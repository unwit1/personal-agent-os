// Runs at document_start so a still-installed Tampermonkey copy of the
// Universal Capture and Shopping collector userscripts can see the extension and stand down.
if (document.documentElement) {
    document.documentElement.setAttribute("data-agent-os-extension", browser.runtime.getManifest().version);
    // The Shopping collector userscript (agent-os-shopping v0.1.6+) stands down when it sees this.
    document.documentElement.setAttribute("data-agent-os-shopping-collector", "1");
}
