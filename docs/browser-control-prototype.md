# Browser Control Prototype

Agent OS can use Firefox pages as a bounded execution surface through the existing
Tampermonkey userscript and loopback browser bridge.

## Architecture

```text
Agent / MCP client
      |
      | browser.sessions / browser.execute / browser.command_status
      v
Agent OS MCP server
      |
      v
browser-bridge.sqlite
      ^
      | authenticated loopback command polling
      |
Firefox + Agent OS Universal Capture userscript
```

The model/client never receives the bridge token. The userscript already holds
that token in Tampermonkey storage and uses it only against the configured local
bridge.

## Enable it

1. Start the local bridge:

   `agent-os browser-bridge`

2. Configure the bridge/token in the Agent OS Universal Capture userscript if it
   is not already configured.

3. In Tampermonkey, choose:

   `Agent OS: Browser control ON/OFF`

   Browser control is off by default. Reload other already-open tabs after
   enabling if you want those tabs to register immediately.

4. Confirm registered sessions:

   `agent-os browser-sessions`

## Manual smoke test

Inspect the current page:

```text
agent-os browser-execute <SESSION_ID> "[{\"op\":\"inspect\"}]"
```

Extract rendered elements:

```text
agent-os browser-execute <SESSION_ID> "[{\"op\":\"extract\",\"selector\":\"a\"}]"
```

Type into an ordinary search field and click an ordinary search button:

```text
agent-os browser-execute <SESSION_ID> "[{\"op\":\"type\",\"selector\":\"input[name=q]\",\"text\":\"Skyrim mods\"},{\"op\":\"click\",\"selector\":\"button[type=submit]\"}]"
```

If a command takes longer than the caller waits, use:

`agent-os browser-command-status <COMMAND_ID>`

instead of issuing a duplicate action.

## MCP tools

The Agent OS MCP server exposes:

- `browser.sessions`: read-only live-session discovery;
- `browser.execute`: bounded DOM/browser actions;
- `browser.command_status`: read-only result polling.

Existing Codex/Claude MCP registrations that point at `agent-os mcp` can use
these tools after restarting/reloading their MCP connection.

## Supported actions

The prototype supports:

- `inspect`
- `extract`
- `wait`
- `click`
- `type`
- `scroll`
- `navigate`
- `back`
- `forward`
- `reload`
- `open_tab`

Navigation/history/reload should be the final action in a command because the
page is about to unload. After cross-site navigation, list sessions again if the
new origin registers a new session ID.

## Safety boundary

There is no arbitrary JavaScript-evaluation command.

The browser-side executor refuses to type into password, payment-card,
one-time-code, banking, SSN, or similar sensitive fields. It also pauses before
recognizable consequential controls such as send, submit, publish, delete,
purchase, pay, transfer, authorize, approve, hire, or reject controls.

A paused command returns `approval_required`. After the user explicitly
approves that exact action, the agent may issue a new command with
`approved_consequential=true`.

This is defense in depth. Site-specific adapters and a future Firefox extension
should add stronger semantic guards for high-impact websites.

## ChatGPT integration

Do not automate `chatgpt.com` as an unofficial API, scrape ChatGPT output, copy
browser authentication cookies, or use a consumer login token as a model API
credential.

The supported architecture is to expose `agent-os mcp` to ChatGPT as an MCP
plugin/app. For a private local server, use OpenAI Secure MCP Tunnel so the
server stays local while ChatGPT can invoke its tools.

The local MCP server command is:

`agent-os mcp`

A tunnel profile therefore points its MCP command at that executable/argument
pair. Once the tunnel is healthy, create a developer-mode ChatGPT plugin/app
using the tunnel, then test `browser.sessions` before enabling
`browser.execute`.

ChatGPT plan/workspace support for custom MCP write actions is controlled by
OpenAI and can differ by account. If the ChatGPT surface only permits read/fetch
MCP tools, `browser.sessions` can work there but `browser.execute` cannot be
used as a write/action tool from that ChatGPT account.

Using a ChatGPT plugin means the model interaction happens in ChatGPT. Agent OS
does not need to call the Responses API to obtain model output. Normal ChatGPT
plan limits still apply, and Secure MCP Tunnel itself requires the OpenAI
Platform tunnel credentials described by OpenAI.

## What this prototype does not control

Tampermonkey controls page content, not Firefox chrome. It does not directly
control:

- Firefox settings pages;
- native extension-management UI;
- native permission dialogs;
- arbitrary browser chrome;
- OS-level file pickers.

A future Firefox WebExtension/native-messaging adapter can reuse the same
`browser.*` API and durable command queue for those capabilities.
