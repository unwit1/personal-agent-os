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

## Automatic-update distribution

The canonical Agent OS repository is private, and the current GitHub account plan does not allow GitHub Pages to be published from this private repository.

Do not make Personal Agent OS public merely to distribute a userscript.

The preferred setup is a separate public repository containing only the non-secret distributable userscript, for example:

    unwit1/agent-os-userscript

Once that repository exists, the userscript can use public raw GitHub URLs for:

    @updateURL
    @downloadURL

No credentials, endpoint tokens, private Agent OS files, knowledge, or user data belong in that public repository.

## Current test install

Until the public distribution repository exists:

1. Open browser/userscripts/agent-os-universal-capture.user.js in this private repository.
2. Copy the complete file.
3. Open Tampermonkey -> Create a new script.
4. Replace the generated template with the copied file and save.
5. Use the floating + Agent OS button on a supported website.

If an Agent OS endpoint has not been configured, captures are queued safely in Tampermonkey storage.

## Endpoint configuration

Use the Tampermonkey script menu for:

- Agent OS: Configure endpoint
- Agent OS: Configure device token
- Agent OS: Set device label
- Agent OS: Retry queued captures
- Agent OS: Copy queued captures as JSON
- Agent OS: Clear queued captures

Credentials stay in per-browser Tampermonkey storage and are never committed to Git.
