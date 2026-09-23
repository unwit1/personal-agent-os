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
value. `integration-health` reports each connector under `connector_providers`,
separately from whether each client surface reaches Agent OS.

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
applications, read credential stores, invoke provider APIs, reconcile desired
and actual client configuration, or provision connector tools across surfaces.
Host limitations and unsupported registration states must remain explicit.
Do not treat a discovered registration or a `declared_ready_unverified` result
as proof that a provider is connected through Agent OS.

The next implementation steps are provider adapter registration and execution,
scoped credential resolution inside the adapter boundary, read-only import
proposals for supported client configurations, and idempotent reconciliation
where each host exposes safe configuration APIs.
