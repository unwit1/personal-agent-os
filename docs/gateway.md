# Controlled Agent OS gateway

The enforced path is `request -> begin_task -> worker -> finish_task/abort_task -> response`.
`agent_os.run` owns that sequence. An envelope supplied to a worker already has a
task owner; the worker returns postflight instead of starting another lifecycle.
The envelope does not contain the raw request: the gateway sends it separately,
transiently, to the configured worker.

## CLI and MCP

```powershell
"Improve the form fingerprint matching behavior in HR-GUI." | python agent.py begin-task --source-client codex --token-budget 1200
python agent.py continue-task TASK-ID --prompt-file next-request.txt
python agent.py finish-task TASK-ID --json postflight.json
python agent.py abort-task TASK-ID --error-class interrupted
python agent.py task-status TASK-ID
```

Replace `TASK-ID` with the returned identifier. The request defaults to stdin;
`--prompt-file` accepts a UTF-8 file. Requests need not appear in shell history.
Lifecycle budgets accept 800–32000 estimated tokens. The complete envelope is
measured using the existing four-characters-per-token approximation; the original
request and provider protocol/schema overhead are separate from the context budget.
This is an estimate, not a vendor tokenizer guarantee. Ordinary prompts get no
project context. Ambiguous routing loads no project context; a hint resolves it.
Continuation stays in the original project. Start a new task to change projects.
Unchanged repeated turns check compact freshness metadata and skip recompilation;
new requests receive only changed context fields. After compaction or worker
replacement, use `--reset-context` to send full selective context again.

MCP exposes `agent.begin_task`, `agent.continue_task`, `agent.finish_task`,
`agent.abort_task`, and `agent.task_status`. These require client cooperation.
The older context, search, capture, and session operations remain available.
They are advanced operations and do not prove lifecycle completion.

A minimal postflight file:

```json
{
  "summary": "Documented the gateway workflow",
  "sanitized": true,
  "decisions": [],
  "evidence": ["README.md"],
  "files_changed": ["README.md"],
  "validation": {"status": "passed", "checks": ["Reviewed documented commands"]},
  "remaining": []
}
```

The versioned [postflight schema](../schemas/postflight.schema.json) also accepts
decisions with rationale summaries, evidence, alternatives, risks and uncertainty;
actions; assumptions; lessons; and proposed changes, improvements, memories and
skills. Capture is deterministic: project + material work + nonempty evidence +
`sanitized: true`. File changes produce a change candidate when none was explicitly
proposed. Decisions become review-gated candidates. Evidenced proposals reuse the
existing deduplication and curation systems. No model secretly mines transcripts,
and no observation is automatically promoted to verified memory.

`sanitized: true` attests that every supplied field contains engineering metadata
only. Never include names/records from source documents, payroll details, OCR,
completed fields, credentials, raw prompts, or transcripts. Detectors reject
known sensitive patterns and forbidden fields, but cannot identify all personal
information in arbitrary text. With `sanitized: false`, prose is not persisted and
no durable capture occurs. Sensitive input may still yield a safe abstract
engineering summary. The full response is returned to the caller, not journaled.

## Providers and practical wrappers

```python
import agent_os

class Worker:
    def execute(self, packet):
        # Deliver packet to your configured worker. The result must match
        # packet["result_schema"]: {"response": str, "postflight": {...}}.
        return your_worker(packet)

result = agent_os.run(request, Worker(), source_client="my-client",
                      project_hint="hr-gui", token_budget=2200)
```

Alternatively, `agent-os run --command-json '["python", "worker.py"]'` sends a
JSON execution packet on stdin and expects a result object on stdout. Use an
absolute worker path if it lives outside the routed project. No shell interprets
the request. A resolved project sets the worker's working directory. Unknown
projects use the invoking directory. This provider interface is the only piece
needed to add another vendor; there is no vendor SDK in the core.

`agent-os codex --project hr-gui --prompt-file request.txt` uses `codex exec`, an
ephemeral session, output schema, and final-message file. Installed Codex help was
checked during implementation. `agent-os claude` uses print mode, disabled session
persistence, JSON output and `structured_output` as described in the official
[Claude CLI reference](https://code.claude.com/docs/en/cli-reference). Claude is
not installed on this workstation, so its transport is tested with fixtures.
Both transports have deterministic tests; no paid model run is part of validation.
Neither wrapper adds permission bypass flags or changes the configured model.
Recognized npm launchers are invoked through Node rather than a shell shim.
Missing clients fail after preflight and leave an aborted task.

Workers must return valid postflight, not just exit successfully. Client exit
codes are preserved where representable; interruption returns 130, malformed
output or orchestration failure returns nonzero, and failed validation or pending
independent review returns 3. `--timeout` defaults to 600 seconds and stops the
worker process tree. Provider stdout is not replayed as a successful result after
an execution failure. Native providers' own logging/privacy controls remain their
responsibility. The controlled gateway is not a sandbox for untrusted workers.

## Review and failure recovery

Risk scoring uses the existing review model, with minimum review requirements for
security/privacy/schema/memory/policy paths, architecture/destructive/cross-project
changes, failed validation, and large file sets. Supply `reviewer=callable` to
`agent_os.run` or `finish_task` for an independently configured reviewer. It receives
the task ID, project, explicit postflight and risk; it returns `status` (`pass`,
`pass_with_notes`, `changes_requested`) and string `findings`. The operator must
ensure that reviewer has independent evidence access and permissions. Routine work
does not invoke it. No reviewer is configured by default in CLI/MCP; required
review is reported `unavailable`, never invented. Review receipts survive retries.
Address a finished task's review findings in a new linked task.

`.agent-local/tasks/TASK-*.json` contains hashes, source identifiers, status, compact
context fingerprints and safe recovery data. It contains no prompt or transcript.
Only explicitly sanitized pending postflight may be journaled for retry.
Session and execution metadata are hashed. Ordinary tasks remain local only.
These journals are continuity state, not an index: they cannot be recreated from
Git for unfinished tasks. Keep them locally until work is resolved.

Before capture, postflight is validated and journaled as `postflight_pending`.
Canonical writes use OS file locks across processes, atomic replacement, existing
dedupe keys, deterministic trace paths, and task-specific handoffs. A crash can
leave a partial candidate batch, but never a false finished receipt. Repeating
`finish-task` with the same pending payload completes missing writes without
duplicating them. A different payload is rejected once capture has started.
Use the pending payload from `task-status` to retry; unsanitized payloads must be
resupplied by the caller. Abort leaves a pending postflight recoverable. An
execution abort may be reopened with `continue-task --resume` after checking
partial changes. A preflight failure should be retried as a new task. Forced
process termination cannot execute abort code: inspect the unfinished journal,
then explicitly abort/resume or retry postflight. Storage failure may also prevent
recording an abort; existing atomic records are retained.

Codex final output temporarily transits through an owner-private directory under
`.agent-local/client-transit/`, removed on normal completion/failure. A forced OS
termination may leave that temporary output; it is ignored by Git and indexing.
Default unit tests simulate this transport and inherit the sandbox ACL for fixture
directories because Python 3.14's Windows private-temp ACL excludes the sandbox
identity. Production retains private temporary-directory permissions.

## Enforcement boundaries

| Surface | What is enforced |
| --- | --- |
| `agent_os.run`, `agent-os run`, `codex`, `claude` | Preflight before worker execution; valid postflight before a successful result; abort on handled failures |
| Lifecycle API | Valid state transitions, privacy gates, capture thresholds, dedupe, task IDs and recovery |
| MCP and AGENTS/CLAUDE adapters | Discoverable preferred lifecycle and instructions; clients must call it |
| Direct vendor CLI, hosted ChatGPT or external UI | No interception; integration is best effort unless routed through the gateway |

Canonical decision traces remain unverified task evidence. Reviewed Git-backed
knowledge remains authoritative; local search indexes remain rebuildable. Decision
traces contain explicit summaries, never hidden chain-of-thought.

## Validation and design review

Run `python -m unittest discover -s tests -v` and `python agent.py validate`.
The tests include real local JSON-worker execution, process concurrency, timeout,
privacy, partial retry, CLI/MCP lifecycle, and mocked vendor transports. They also
retain the original context/capture/form-routing tests. Schemas are checked against
the same contracts used at runtime to catch drift.

Implementation review tightened candidate/handoff privacy gates, serialized legacy
capture writes as well as gateway calls, made handoffs collision-resistant, checked
all proposed writes before capture, and preserved unavailable-review states. The
local journal avoids a canonical file for every ordinary prompt. The gateway uses
existing subsystems instead of a second knowledge store. Git commit/push remains
subject to the user's request and the canonical policy.
