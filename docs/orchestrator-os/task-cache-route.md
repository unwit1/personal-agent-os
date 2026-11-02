# Orchestrator task cache route

Design contract for the P0.5 task cache route: a reviewed, integrated patch
from an earlier run may replace a worker (and its review) for an identical
node, but only after the patch is re-proven on the current tree. This file
pins the operator decision recorded for run `run-20261004T043845Z-cd5fd1`;
implementations must match it, and any change to the key, value, or hit rules
below bumps `TASK_CACHE_POLICY_VERSION`.

The route sits between "deterministic utility" and "model" in the P0.5
economy order. It never replaces a deterministic command, and every miss falls
through to the next declared route (model), so enabling it can only remove
model calls, never add risk the model route would not already carry.

## 1. Key

`TASK_CACHE_POLICY_VERSION = 1`.

The key is the lowercase hex `sha256` of the UTF-8 encoding of this object,
serialized as canonical JSON (`json.dumps(obj, sort_keys=True,
separators=(",", ":"), ensure_ascii=False)`):

```
{
  "policy_version": TASK_CACHE_POLICY_VERSION,
  "goal":       <node goal: strip(), then every whitespace run collapsed to one space>,
  "scope":      <sorted list of the node's scope paths, as declared (forward slashes)>,
  "base_files": {<scope path>: <git object id of that path at the node's base commit, or null if absent>},
  "validators": <the node's validator list, in declared order>,
  "role":       <node role>
}
```

- `base_files` has one entry for every in-scope path. The id comes from
  `git rev-parse <base>:<path>`; for a file this is its blob sha. A path that
  does not exist at the base commit maps to `null`.
- `validators` keeps declared order; reordering validators is a different key.
- Anything not in the object (provider, model class, run id, prompts, context)
  deliberately does not affect the key.

## 2. Value

One entry per key:

```
{
  "schema": "personal-agent/orchestrator-task-cache/v1",
  "policy_version": 1,
  "key": "<sha256 hex>",
  "patch": "<unified diff text from: git diff <base> <node head> -- <scope...>>",
  "validator_evidence": [{"command": "<validator command>", "passed": true}, ...],
  "metadata": {"run_id": "<run id>", "node_id": "<node id>", "created_at": "<UTC ISO-8601>"}
}
```

The patch is the reviewed, integrated change limited to in-scope paths.
`validator_evidence` is the evidence that accompanied that integration; on a
hit it is informational only, because the validators are always re-run (§4).

## 3. Eligibility to record

An entry is written only when all of these hold for the node:

- role is `implementer` or `test_author`;
- `execution_path` is `model`;
- the reviewer verdict is `approved` with no open material findings;
- the node's change was integrated;
- the scoped patch is non-empty and touches only the node's scope paths.

Anything else records nothing. Recording never overwrites an entry that
already exists for the same key.

## 4. Hit

Lookup is by key alone. A found entry is a **hit** that may skip the worker
**and** its review only when, in order:

1. `git apply --check` of the entry's patch succeeds on the node worktree
   (which is at the node's base);
2. the patch applies;
3. every node validator passes on the patched tree.

The node then proceeds to integration with the fresh validator evidence from
step 3 and a review record that cites the cached source
(`metadata.run_id`/`metadata.node_id`) instead of a new reviewer call.

Every other outcome is a **miss**: reset the node worktree to its base, emit
miss telemetry (§7), and continue on the next declared route (`model`). A miss
never fails the node.

## 5. Storage

- One JSON file per key at `<orchestrator state root>/task-cache/<key>.json`,
  where the state root is `orchestrator_home()` (`AGENT_OS_ORCHESTRATOR_HOME`,
  default `.agent-local/orchestrator`).
- Written atomically: write a temp file in the same directory, then
  `os.replace` it onto the final name.
- The cache is derived and rebuildable; deleting the directory only costs
  future hits. It is never committed (`.agent-local/` is git-ignored).
- An unreadable, malformed, or wrong-`policy_version` file is treated as a
  miss with reason `ineligible`, never as an error.

## 6. Policy

Run policy key `task_cache_enabled`, boolean, default `False` (see section 9).
When false the orchestrator neither looks up nor records entries and emits no
task cache telemetry, so existing runs are unchanged.

## 7. Telemetry

On a hit, ledger events:

- `cache_hit` with `what='task patch'`;
- `work_avoided` with `category='task_cache'` and `model_calls_avoided` equal
  to the worker plus reviewer calls skipped (normally 2; 1 when the node would
  not have required review).

On a miss, a `fallback` ledger event to the next route carrying a
`task_cache_miss` reason string from the closed set:

| reason | meaning |
| --- | --- |
| `absent` | no entry exists for the key |
| `apply_failed` | `git apply --check` or the apply itself failed |
| `validator_failed` | the patch applied but a node validator failed |
| `ineligible` | an entry exists but cannot be used: malformed, wrong policy version, touches out-of-scope paths, or the node is not eligible for the route |

No other reason values are emitted.

## 8. Privacy

Entries hold only in-scope repository diff text and validator command/pass
data plus the run/node/time metadata above. They never hold prompts, model
output or transcripts, context packets, goal text, provider identities,
credentials, or secrets. Telemetry carries the key prefix and reason only.

## 9. Operator decisions

### Default

Run policy `task_cache_enabled` stays default `False` and is a per-run opt-in.
The default will only change once hit/miss/fallback ledger evidence (`cache_hit`,
`work_avoided`, `fallback` with `task_cache_miss`) from real runs justifies it.
`TASK_CACHE_POLICY_VERSION` is not bumped by this decision.

### Skill route

All approved skills are instruction-only `SKILL.md` files, so skill execution
stays caller-owned and the orchestrator has no `skill` task route; this closes
the skill-route roadmap item. 

A skill that wants orchestrator execution must ship a runnable command that
passes the existing approved-command gate (equals a project `validation_commands`
entry or fully matches a policy `approved_commands` pattern, no shell
metacharacters, run as an argument list), and a task uses it by declaring
`available_execution_paths: ["deterministic", "model"]` with that command as its
deterministic step, so it runs through the existing deterministic route with
model as the evidence-triggered fallback; no separate skill route or adapter is
added.
