# Deterministic/cache/skill-first execution routing

P0.5 turns the Agent OS economy policy into a small, provider-neutral route
selector. It chooses a route; it does not invoke a model or execute a skill.
That separation keeps permission, provider, and skill execution under the
calling agent while making the cheaper decision deterministic and testable.

## Route order

For a workflow stage, the selector uses this order:

1. a declared `deterministic` execution path;
2. an existing declared local cache artifact;
3. an explicitly declared available `approved_skill`;
4. a model handoff at the stage's existing provider-neutral capability class.

A missing cache is a normal cache miss. An unsafe cache path outside the
checkout is refused. A skill is never inferred from lexical matching: the
manifest must explicitly name it, and discovery must find that exact skill.

## Workflow contract

Existing manifests remain valid. Non-deterministic stages may optionally add:

```json
{
  "cache": {"path": "local/derived/result.json"},
  "approved_skill": "cheap-route-first"
}
```

`cache.path` is interpreted relative to the checkout and must resolve inside
it. Cache content remains governed by its subsystem privacy boundary; the
dispatcher only checks artifact existence. An approved skill is a reusable
instruction artifact, not permission to make a model call.

`workflow-stage` and `workflow-run` now include an `execution` record with the
selected route and concise reason. For cache and skill routes, the orchestrator
prepares an agent handoff that explicitly says to validate the result before
any model escalation. Deterministic workflow validators continue to run
locally. Failed validation remains the evidence required to escalate a model
capability class.

## Boundaries

P0.5 does not add provider invocation, automatic skill execution, or usage
telemetry. Those require their own authority and belong to later roadmap work.
It does ensure that an available cache or approved reusable method is visible
before the system asks an agent to spend model capability.
