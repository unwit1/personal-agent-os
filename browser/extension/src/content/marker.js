// Runs at document_start so a still-installed Tampermonkey copy of the
// Universal Capture userscript can see the extension and stand down.
if (document.documentElement) {
    document.documentElement.setAttribute("data-agent-os-extension", browser.runtime.getManifest().version);
}
