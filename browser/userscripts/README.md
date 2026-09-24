# Agent OS Universal Capture userscript

This directory contains the first universal browser capture client for Personal Agent OS.

## What v3.0.0 supports

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

Every capture uses the normalized browser-capture-v1 envelope and includes the current URL, canonical URL, title, description, selected text, capture time, optional device label, source-specific IDs, and adapter metadata when available.

## Install in Tampermonkey

Because the canonical Personal Agent OS repository is private, do not put a GitHub personal access token into the userscript merely to make private raw-file updates work.

For the first test:

1. Open browser/userscripts/agent-os-universal-capture.user.js in the private GitHub repository.
2. Copy the complete file contents.
3. Open Tampermonkey -> Create a new script.
4. Replace the generated template with the copied file.
5. Save it.
6. Visit a supported page and use the floating + Agent OS button.

If an Agent OS endpoint has not been configured, the capture is safely queued inside Tampermonkey storage so extraction can be tested immediately.

Use the Tampermonkey script menu for:

- Agent OS: Configure endpoint
- Agent OS: Configure device token
- Agent OS: Set device label
- Agent OS: Retry queued captures
- Agent OS: Copy queued captures as JSON
- Agent OS: Clear queued captures

## Endpoint contract

Configure an endpoint that accepts an HTTP POST with Content-Type application/json.

When a device token is configured, the client sends:

    X-Agent-OS-Token: <device token>

A successful endpoint should return any 2xx response. A JSON response may optionally contain relationship/status values such as NEW or DUPLICATE so the browser can show Already Saved.

The intended long-term endpoint is:

    POST /api/v1/browser/capture

Do not commit endpoint credentials or device tokens. They live in Tampermonkey GM storage per browser/device.

## Normalized capture shape

Typical fields:

    schema_version
    source
    site
    content_type
    source_id
    title
    author
    url
    canonical_url
    description
    selected_text
    image
    captured_at
    intent
    device
    metadata

## Private-repo auto-update limitation

Tampermonkey auto-update URLs work best with a URL that can be fetched without interactive GitHub authentication. The canonical repo is private, so a raw.githubusercontent.com URL is not a reliable cross-device update channel by itself.

Do not make the main Agent OS repository public and do not embed a long-lived GitHub token in the script.

The intended distribution follow-up is to publish only the built, non-secret .user.js artifact through a dedicated update channel while continuing to keep source/canonical Agent OS state private. The userscript can then add @updateURL and @downloadURL without changing its capture API or adapter architecture.

## Adapter design

The test build intentionally keeps adapters in one file. That avoids @require/authentication problems while the repository is private.

Once the browser companion has a stable distribution channel, the internal adapter registry can be split into source modules without changing the normalized capture contract.
