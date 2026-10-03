# Connector registry

Agent OS keeps provider-neutral connector metadata in
[`connectors/registry.json`](../connectors/registry.json), validated against
[`schemas/connector-registry-v1.schema.json`](../schemas/connector-registry-v1.schema.json).
The registry describes provider identity, declared capabilities and scopes,
provider health, privacy domain, client registration state, and an optional
reference to a local credential store. Credential values do not belong in the
registry or in Git.

## Current discovery

The MCP tool `connector.list` returns the configured connector metadata and
whether a credential reference is configured. It never returns the reference
value. The read-only MCP tool `connector.import_candidates` inventories MCP
server names and executable basenames from the client registration files
declared by the surface registry. It omits full paths, command arguments,
environment entries, and credentials. Results are unclassified proposals for
review; each has a stable ID for the server/executable pair and combines the
surfaces where it appears. They are not imported or written to the canonical
registry.
`integration-health` reports each connector under `connector_providers`,
separately from whether each client surface reaches Agent OS.

The read-only MCP tool `connector.reconcile_plan` and CLI equivalent
`python agent.py connector-reconcile-plan [--surface <id>]` generate a
read-only plan listing one action per registered connector: `none` (already
registered/disabled/unsupported), `investigate` (error state),
`provision_local_config` (surface declares capability to change local config),
`manual_host_setup` (host owns its settings), `undetermined` (capability not
declared), or `unknown_surface`. The result always has `applied: false`,
reports whether a credential reference is configured (never its value), and
writes nothing. It resolves no credentials and contacts no providers.

## Bridge vs native registrations

A connector counts as registered on a surface when its provider is reachable
through that surface's Agent OS bridge. A registration may set the optional
`server_name` (pattern: `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`) to request a
native client MCP entry as well. That entry is provisioned only where the
surface's local config can be inspected and changed (surfaces that report
`provision_local_config` capability).

`connector.reconcile_plan` reports `native_server_name` and
`native_entry_requested` for each registration without applying anything.
Any future client-config change will be preview-first and requires an explicit
`confirm_write` flag.

The read-only MCP tool `connector.credential_status` and CLI equivalent
`python agent.py connector-credential-status [--surface <id>]` report whether
a credential is configured for each registered connector. For `env:` backend
references, the status is `present` if the environment variable is non-empty,
or `missing` if absent or empty. For `windows-credential` references, the
status is `present` if the credential exists in Windows Credential Manager
(generic credentials) or `missing` if not found, or `unchecked` if the probe
is unavailable on the host. For `macos-keychain` references, the status is
`present` if found via `security find-generic-password` (without retrieving the
password) or `missing` if not found, or `unchecked` if the probe is unavailable.
`keyring` and `secret-service` backends report `unchecked`. Connectors without a
credential reference report `not_configured`. Output never includes credential
values or reference names, and no provider APIs are contacted.

`connector.register` validates a metadata descriptor and previews it by default.
It writes only when the caller sets `confirm_write: true`. New entries must
start with provider health `unknown` and client registrations `desired`; only
adapters may report verified states. Replacing an existing ID also requires
`replace_existing: true`. Identical repeats are idempotent. The write is
serialized across local processes and atomically replaces the registry file.
This operation stores metadata only; it does not resolve or copy credentials,
connect to a provider, or make a connector callable.

The same discovery report is available without MCP:

```powershell
python agent.py connector-import-candidates
python agent.py connector-import-candidates --surface codex-cli
python agent.py connector-reconcile-plan
python agent.py connector-reconcile-plan --surface codex-cli
python agent.py connector-credential-status
python agent.py connector-credential-status --surface codex-cli
```

Registering metadata from a reviewed JSON descriptor also previews by default:

```powershell
python agent.py connector-register connector.json
python agent.py connector-register connector.json --confirm-write
python agent.py connector-register connector.json --confirm-write --replace-existing
```

The last form updates an existing connector with the same ID. The descriptor
must use the v1 connector shape, start with unknown provider health and desired
surface registrations, and contain no credential values. The write updates only
the canonical metadata registry; provider setup and invocation remain separate.

Each connector's `surface_readiness` entries describe the checks for that
surface:

- `blocked` includes reasons such as an unreachable Agent OS surface, a missing
  or non-registered connector registration, or provider health other than
  `healthy`;
- `declared_ready_unverified` means the registry reports a healthy provider,
  registered client, and reachable Agent OS surface. It does not mean that a
  provider API call was made or that a tool invocation succeeded.

The registry's health is declared metadata. Integration health does not contact
provider APIs. The readiness report omits credential references and never
resolves them.

## Not implemented yet

The current broker slice does not import connector settings from client
applications, read credential stores, invoke provider APIs, apply reconciliation
to client configuration (only a read-only plan exists), or provision connector
tools across surfaces.
Host limitations and unsupported registration states must remain explicit.
Do not treat a discovered registration or a `declared_ready_unverified` result
as proof that a provider is connected through Agent OS.

Presence checks for `keyring` and `secret-service` backends and actual
credential resolution remain open.

The next implementation steps are provider adapter registration and execution,
scoped credential resolution inside the adapter boundary, read-only import
proposals for supported client configurations, and idempotent reconciliation
where each host exposes safe configuration APIs.
