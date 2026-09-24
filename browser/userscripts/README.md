# Agent OS Universal Capture userscript

This directory contains the universal browser capture client for Personal Agent OS.

## Supported sites

The self-contained userscript currently has adapters for:

- Reddit posts
- Amazon product pages
- YouTube videos, including the current playback timestamp
- Nexus Mods detail pages
- Nexus Mods listing cards
- SpaceBattles threads
- Questionable Questing threads
- Generic fallback capture for ordinary HTTP/HTTPS pages

SpaceBattles and Questionable Questing share the XenForo adapter.

Every capture uses the normalized `browser-capture-v1` envelope and includes the current URL, canonical URL, title, description, selected text, capture time, optional device label, source-specific IDs, and adapter metadata when available.

## Automatic Tampermonkey updates

The source userscript declares:

    @updateURL   https://unwit1.github.io/personal-agent-os/agent-os-universal-capture.user.js
    @downloadURL https://unwit1.github.io/personal-agent-os/agent-os-universal-capture.user.js

The private repository is never exposed as the update source. A GitHub Pages workflow publishes only the non-secret built userscript.

The publishing workflow automatically appends the GitHub Actions run number to the source version. For example, source version `3.1.0` may be published as `3.1.0.42`. This means ordinary userscript changes do not require a human to remember to bump the Tampermonkey version.

### One-time GitHub Pages setup

GitHub Pages must use **GitHub Actions** as its source:

1. Open this repository on GitHub.
2. Go to **Settings -> Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. Open **Actions -> Publish Agent OS userscript**.
5. Run the workflow once if it did not automatically redeploy after Pages was enabled.

The expected public installation/update URL is:

    https://unwit1.github.io/personal-agent-os/agent-os-universal-capture.user.js

Only the built userscript, a tiny installation page, and a version marker are deployed. No private Agent OS data, source tree, credentials, or knowledge files are included in the Pages artifact.

> GitHub account note: Pages from a private repository requires a GitHub plan that supports private-repository Pages. If GitHub does not offer Pages for this private repo, use a dedicated public distribution repository instead; do not make the Agent OS repository public.

## Install or replace the Tampermonkey copy

After the Pages workflow has deployed successfully:

1. Open `https://unwit1.github.io/personal-agent-os/agent-os-universal-capture.user.js`.
2. Tampermonkey should open its install/update screen.
3. If your existing script is recognized as the same `@name` + `@namespace`, choose **Update** or **Reinstall**. If Tampermonkey creates a second copy, disable/delete the old `Agent OS Universal Capture` copy after installing the Pages-hosted one.
4. In Tampermonkey Dashboard, confirm the script shows an update URL pointing to `unwit1.github.io`.
5. From that point forward, normal updates are automatic. To force one immediately, use Tampermonkey's **Check for userscript updates** command.

## Endpoint configuration

If an Agent OS endpoint has not been configured, captures are safely queued inside Tampermonkey storage so extraction can be tested immediately.

Use the Tampermonkey script menu for:

- Agent OS: Configure endpoint
- Agent OS: Configure device token
- Agent OS: Set device label
- Agent OS: Retry queued captures
- Agent OS: Copy queued captures as JSON
- Agent OS: Clear queued captures

Configure an endpoint that accepts an HTTP POST with `Content-Type: application/json`.

When a device token is configured, the client sends:

    X-Agent-OS-Token: <device token>

A successful endpoint should return any 2xx response. A JSON response may optionally contain relationship/status values such as `NEW` or `DUPLICATE`.

The intended long-term endpoint is:

    POST /api/v1/browser/capture

Do not commit endpoint credentials or device tokens. They live in Tampermonkey GM storage per browser/device.
