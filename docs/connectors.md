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

`connector.reconcile_plan` also reports `native_entry_status` for each
registration, indicating whether the requested native client entry is already
present. The possible status values are: `not_requested` (no `server_name` set),
`unknown_surface` (surface not found in registry), `not_inspectable` (surface
declares no capability to inspect local config), `unreadable` (no declared client
config file exists or the file cannot be parsed), `present` (a server with that
name, matched case-insensitively, already exists in the client config), and
`absent` (no matching server found in the client config). The result includes a
top-level `native_entry_status_counts` field that aggregates the status counts
across all registrations. This check reads only server names, returns no file
paths, commands, arguments, or environment variables, and writes nothing.

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

The read-only MCP tool `connector.conflicts` and CLI equivalent
`python agent.py connector-conflicts [--surface <id>]` report conflicts that could
prevent successful connector provisioning. It checks for three kinds of conflicts:

- **`duplicate_provider_surface`**: A provider appears more than once across
  registrations marked `desired`, `registered`, or `error` for the same surface.
- **`native_server_name_collision`**: Two or more connectors request the same
  `server_name` (native client MCP entry name) for the same surface.
- **`shared_credential_reference`**: Two or more connectors reference the same
  credential store entry; the backend kind is reported only, never the reference
  value.

The result includes the following fields:

- `schema`: version identifier (personal-agent/connector-conflicts/v1)
- `surface_filter`: the surface ID passed on the command line, or `null` if no
  filter was applied
- `read_only`: always `true`
- `count`: total number of conflicts found
- `kind_counts`: breakdown of conflict counts by kind
- `conflicts`: array of conflict records, each with the conflict `kind` and
  `connector_ids` involved, plus per-kind fields:
  - For `duplicate_provider_surface`: `provider_id` and `surface_id`
  - For `native_server_name_collision`: `surface_id` and `server_name`
  - For `shared_credential_reference`: `backend` (the credential store kind
    only, never the reference value)

The CLI equivalent is:

```powershell
python agent.py connector-conflicts
python agent.py connector-conflicts --surface codex-cli
```

This operation is read-only: it writes nothing, appends no events, never returns
secret references, and does not deduplicate or repair conflicts automatically.
Conflict resolution must be handled separately through `connector.register` or
`connector.unregister`.

## Provisioning readiness

The read-only MCP tool `connector.provisioning_readiness` and CLI equivalent
`python agent.py connector-provisioning-readiness [--surface <id>]` combine the
results of `connector.reconcile_plan`, `connector.credential_status`, and
`connector.conflicts` to report whether each registered connector is ready for
provisioning on each surface. The result is a unified readiness report that
lists blockers preventing automatic provisioning.

The result includes one item per registered connector per surface, with the
following fields:

- `connector_id`: the connector identifier
- `surface_id`: the surface identifier for this registration
- `state`: the registration state (`desired`, `registered`, `error`, or `disabled`)
- `action`: the provisioning action required—one of `none`, `investigate`,
  `provision_local_config`, `manual_host_setup`, `undetermined`, or `unknown_surface`
- `credential_status`: whether a credential is configured for this connector
  (`present`, `missing`, `unchecked`, or `not_configured`)
- `readiness`: overall readiness state—one of `ready` (no blockers), `blocked`
  (provisioning is prevented), or `no_action` (no provisioning required)
- `blockers`: list of reasons preventing provisioning, which may include:
  - `unknown_surface`: the surface is not in the surface registry
  - `registration_error`: the registration is in an error state
  - `manual_host_setup`: the host owns its settings and manual setup is required
  - `surface_capability_undetermined`: the surface did not declare whether it can
    inspect or change local configuration
  - `credential_missing`: a configured credential is absent or empty
  - `credential_unchecked`: a configured credential backend is unavailable for
    presence checks
  - `native_entry_absent`: a requested native client entry is not present in the
    local config
  - `native_entry_unverifiable`: the surface cannot inspect local configuration
  - `conflict:<kind>`: a conflict of the specified kind prevents provisioning
    (e.g., `conflict:duplicate_provider_surface`)

The result includes top-level fields:

- `schema`: version identifier (personal-agent/connector-provisioning-readiness/v1)
- `surface_filter`: the surface ID passed on the command line, or `null` if no
  filter was applied
- `read_only`: always `true`
- `readiness_counts`: breakdown of item counts by readiness state
- `blocker_counts`: breakdown of blocker counts by kind

The CLI equivalent is:

```powershell
python agent.py connector-provisioning-readiness
python agent.py connector-provisioning-readiness --surface codex-cli
```

This operation is read-only: it writes nothing and applies no changes. `ready`
means only that the declared state shows no blockers; nothing is applied, no
credentials are resolved, and no providers are contacted. Native entry absence
cannot yet be fixed automatically because writing native client configuration is
waiting on a design decision.

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

## Change events and removal

Agent OS maintains a local append-only event log at `.agent-local/connector-events.jsonl`
(not committed to Git) that records all confirmed registry changes. Each line is a
JSON record with the following fields:

- `schema`: version identifier for the event record format
- `event`: kind of change—one of `connector.added`, `connector.updated`, or `connector.removed`
- `connector_id`: unique connector identifier
- `provider_id`: provider identifier
- `capabilities`: list of connector capabilities
- `surfaces`: list of surface registrations at the time of change
- `at`: ISO 8601 timestamp with timezone

The event log never includes `secret_ref`, `scopes`, `server_name`, or credential values.
Events are written only when a registry change is explicitly confirmed (i.e., when
`confirm_write: true` is passed to `connector.register`, `connector.unregister`, or `connector.prune_stale`).

### Reading connector events

The read-only MCP tool `connector.events` returns a list of recorded connector change
events. Each event carries a stable `seq` field containing its 1-based line number in the
append-only event log. It accepts optional parameters:

- `limit`: number of recent events to return (1–500, default 50)
- `connector_id`: filter to events for a specific connector (optional)
- `after_seq`: return only events after this sequence number (optional). A subscriber such as orchestration or the Personal Executive passes the previous response's `next_after_seq` to receive only newer events, oldest first, up to `limit`.

The response includes the following fields:

- `latest_seq`: the sequence number of the most recent event in the log
- `next_after_seq`: the sequence number to pass as `after_seq` in the next call to continue receiving events
- `has_more`: `true` if more events exist beyond the current result
- `cursor_reset`: `true` when `after_seq` exceeds the log length (e.g. after the local log was reset); the subscriber should then restart from sequence 0
- `items`: the list of matching connector change events, each with a `seq` field

The feed is still poll-based; Agent OS does not push events to subscribers.

The CLI equivalent is:

```powershell
python agent.py connector-events
python agent.py connector-events --limit 50
python agent.py connector-events --connector google-drive-work
python agent.py connector-events --limit 100 --connector rtec-applicants
python agent.py connector-events --after-seq 12
```

### Removing connectors

`connector.unregister` removes a connector from the registry and records a
`connector.removed` event. The operation previews by default and writes only when
the caller sets `confirm_write: true`. Identical repeats are idempotent; removing
a connector that does not exist succeeds with no change.

The CLI equivalent is:

```powershell
python agent.py connector-unregister google-drive-work
python agent.py connector-unregister google-drive-work --confirm-write
```

The unregister operation removes only registry metadata. It does not revoke
credentials, delete secret store entries, edit client configuration, or contact
providers. Credential cleanup must be handled separately.

### Pruning stale registrations

`connector.prune_stale` (MCP) and `connector-prune-stale` (CLI) identify and
remove registrations whose `surface_id` is no longer declared in the surface
registry. A registration becomes stale when the surface it references is removed
from the surface registry; this is the same condition that `connector.reconcile_plan`
reports as `unknown_surface`. The operation previews by default and writes nothing.
With `confirm_write`, only the stale registration entries are removed under the
registry lock. The connector itself is kept even if no registrations remain. One
`connector.updated` event is recorded per changed connector.

The CLI equivalent is:

```powershell
python agent.py connector-prune-stale
python agent.py connector-prune-stale google-drive-work --confirm-write
```

The prune operation is read-only by default. Output never includes secret
references, and the command never revokes credentials, edits client configuration,
or contacts providers.

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
