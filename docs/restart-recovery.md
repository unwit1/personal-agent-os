# Restart-safe recovery and incremental processing

P0.4 makes a work interruption a deterministic local-state problem rather than
a conversation-memory problem. The same recovery packet is usable by any
supported coding agent; an originating provider may be noted as provenance,
but it has no effect on recovery correctness.

## Storage boundary

Canonical Git state contains `schemas/checkpoint-v1.schema.json`, recovery
code, workflow manifests, tests, and this policy. Runtime records live only in
the checkout-local, gitignored `.agent-local/recovery/` directory:

```
.agent-local/recovery/
  checkpoints/<project-id>/<run-id>.json
  ledgers/<stable-source-id>.json
```

Records contain metadata, fixed-length hashes, paths relative to the checkout,
stage status, validation summaries, compact decisions, and exact next actions.
They never contain source file text, private imports, credentials, full prompts,
or conversation transcripts. A checkpoint is capped at 64 KiB and rejects
transcript-like fields recursively.

## Identity and fingerprints

`repository_identity()` normalizes the Git origin remote and hashes it into a
stable repository ID. `stable_project_id()` maps that remote to a registered
project when possible, so a clone or linked worktree does not become a new
project merely because it has a different local path. Sources, items, and
checkpoints use deterministic IDs derived from their semantic identity.

`working_tree_fingerprint()` records the branch, HEAD, upstream merge-base,
modified/staged/untracked/deleted/renamed paths and a SHA-256 digest of Git
diffs plus untracked-file hashes. It stores only the digest—not the diff or
file contents. This makes it possible to distinguish unchanged interrupted
work, later non-overlapping edits, missing checkpointed edits, branch changes,
and HEAD advancement.

## Recovery lifecycle

1. Before broad repository reading, run `python agent.py recovery-status`.
2. If a matching local checkpoint exists, run `recovery-inspect` (or the MCP
   `recovery.inspect`) for its continuation packet.
3. `interrupted_resumable_task` may continue immediately. It names completed
   stages, current stage, validation state, next action, and capability class.
4. `interrupted_task_with_additional_safe_edits` may continue, while preserving
   both the checkpoint and the newer changes.
5. A moved branch/HEAD, changed or missing checkpointed edit, different
   repository, corrupt checkpoint, or uncheckpointed dirty tree is never
   overwritten. The result explains the conflict and requires review.
6. `recovery-resume` returns `resumed: true` only for deterministic safe cases.

P0.1 writes a local recovery checkpoint whenever it saves a workflow run: at
run creation (before work begins), after deterministic or agent stage success,
after validation/failure/escalation, and before its next stage transition.
Completed stages remain complete, validated outputs are reused, and a failed
stage retains partial outputs for retry.

## Incremental connectors

`IncrementalLedger` is a generic local primitive for Drive/archive imports,
mail backfills, text messages, document batches, OCR/extraction, crawls, and
future connectors. It records a stable source ID/fingerprint, stable item ID,
item fingerprint, processor version, status, retry count, cursor, and last
processed marker. A successful item with the same fingerprint and processor
version is skipped; a changed item or processing-version change is reprocessed.
Failed and interrupted items remain retryable while completed siblings are not
duplicated.

Consequential connectors should claim an item before work and mark it complete
only after their durable output boundary. This makes retries explicit and
idempotent rather than assuming an external operation is safe to repeat.

## Interfaces

CLI: `recovery-status`, `recovery-inspect`, `recovery-resume`,
`checkpoint-list`, and `checkpoint-get`.

MCP: `recovery.status`, `recovery.inspect`, `recovery.resume`,
`checkpoint.list`, `checkpoint.get`, and `checkpoint.latest`.

All call the same core functions in `agent_os.recovery`; neither handler embeds
agent-specific recovery logic. Use the compact result first and retrieve an
actual diff only if status says review is needed.

## Current limitation

Recovery state is intentionally checkout-local. Moving to another computer
requires copying the local runtime directory securely or creating a sanitized
handoff/checkpoint there; it is not silently synced to Git because it can
contain private path and work-state metadata.
