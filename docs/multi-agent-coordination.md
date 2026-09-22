# Working alongside other agents

## The incident this exists for

On 2026-09-22 two agents worked the same scanner repository within the same
hour. One was measuring a document corpus: establish a baseline, change the
classifier, re-measure. The other landed eight commits in between, one of which
held an entire packet for review whenever any single page lacked a confident
form type.

The first agent's re-measurement collapsed from 64 documents to 1. It spent
some time working out whether its own change had caused that, and came close to
reporting it as its own regression. The plan notes gave it away in the end —
the failure was on *form type*, which that agent's change did not touch.

Both agents were working carefully. Both were committing sound work. Neither
had any way to see the other, and the measurement between them was silently
invalidated.

## What this is, and what it deliberately is not

It is **visibility**, not locking.

Nothing here can stop a write, and pretending otherwise would make things
worse: an agent that believes it holds an exclusive lock takes bigger risks
than one that knows it does not. So a claim is always recorded, an overlap is
always reported, and no call ever refuses to proceed.

Two agents wanting the same file is a conversation, not a race to be arbitrated
by a tool. What the tool owes them is enough detail — who, what, since when,
which paths — to have that conversation.

## Using it

```powershell
# Before you start: who is already here?
agent-os work-check hr-gui --scope "modules/scanner/engine/src"

# Announce what you are about to do
agent-os work-claim hr-gui "auditing zones against the verified corpus" `
    --agent claude-opus-5 `
    --scope "modules/scanner/engine/src/zone_learn.py" `
    --scope "scripts/zone_learn_run.py"

# During long work, keep it alive and collect replies
agent-os work-heartbeat WC-364477f0cd

# Negotiate rather than race
agent-os work-message WC-364477f0cd "I need cli.py too - can we split it?" --from-agent codex

# When you are done
agent-os work-release WC-364477f0cd --note "zones audited, nothing changed"

# What is happening right now
agent-os work-status
```

Over MCP: `work.check`, `work.claim`, `work.status`, `work.heartbeat`,
`work.release`, `work.message`.

`work-claim` and `work-check` exit non-zero on overlap, so a script can gate on
them without parsing output.

## The part that actually prevents a repeat

Asking an agent to remember to check is a convention, and conventions fail
quietly. So `agent.context` — the preflight every routed surface already calls
before substantial work — now reports active claims for the resolved project
whether or not anyone asked:

```json
"active_work": {
  "warning": "another agent has announced work on this project",
  "claims": [
    {"agent": "codex", "task": "refactoring the router",
     "scope": ["src/agent_os"], "since": "2026-09-22T16:56:40Z"}
  ],
  "advice": "check scope overlap before editing; message them rather than racing"
}
```

An agent that pulls project context now sees the colleague editing it. A
preflight that describes the repository but not the person in it is describing
an empty room.

## Reaching an agent that never announced itself

Messages attach to a claim, which is no help when the agent you need has not
adopted the protocol yet -- the common case while it is still spreading. A
**note** attaches to the project instead, so it waits in the inbox until
somebody picks the work up and survives the sender's session ending.

```powershell
agent-os work-note hr-gui "Question about _unknown_form_reason ..." `
    --from-agent claude-opus-5 `
    --about "modules/scanner/engine/src/rename_pipeline.py::_unknown_form_reason"

agent-os work-inbox --project hr-gui          # exits non-zero when notes wait
agent-os work-ack WN-5152b28f8b --agent codex --reply "good catch, changing it"
```

`agent.context` reports waiting notes as `messages_for_you` without being
asked, alongside `active_work`.

## Delegating bounded tasks

Claims describe overlapping work; they do not assign or track a unit of work.
For that, the local registry also supports deterministic delegated tasks:

```powershell
agent-os work-delegate personal-agent-os fixture-review "Review the fixture" `
    --from-agent luna --to-agent codex --scope "tests" `
    --depends-on WT-0123456789ab
agent-os work-tasks --project personal-agent-os
agent-os work-task-claim WT-0123456789ab --agent codex
agent-os work-task-complete WT-0123456789ab --agent codex `
    --validation "focused tests passed" --result "review packet ready"
```

Add `--review-required` to `work-delegate` when completion must wait for an
approved independent peer review. Without that opt-in flag, existing and new
tasks retain the normal completion behavior.

The task ID is stable for a `(project, task_key)` pair, so retrying delegation
is idempotent. Dependencies are checked before claiming, completion is limited
to the assigned agent, and non-empty validation evidence is required. Task
records contain bounded summaries, paths, IDs, and validation metadata; they do
not carry prompts, transcripts, documents, or secrets. The queue is advisory
and machine-local like claims, but it gives agents a resumable handoff instead
of relying on chat memory.

Peer code evaluation is a separate protocol from task completion: the current
`review` command selects a risk level, while the coordination review record
persists the independent verdict and validation evidence.

For a review-gated task, `approved` is the only completion-enabling verdict;
`changes_requested` and `blocked` leave the task in progress. Review records
remain linked to the stable task ID and are not replaced by task completion.
The approval must be requested by the delegated task's requester and submitted
by an agent who is neither that requester nor the assigned worker.

## Independent peer review

Delegated work can request a review linked to exactly one stable identity:
either a delegated task ID or a commit fingerprint.

```powershell
agent-os work-review-request personal-agent-os fixture-review `
    --from-agent luna --task-id WT-0123456789ab --reviewer codex `
    --changed-file src/agent_os/coordination.py
agent-os work-reviews --project personal-agent-os --status requested
agent-os work-review-submit WR-0123456789ab --agent codex `
    --verdict approved --validation "focused and full tests passed"
```

Review requests are idempotent for a project, review key, and linked identity.
The requester cannot submit the verdict, an assigned reviewer cannot be
replaced, findings are capped and length-limited, and every final verdict needs
non-empty validation evidence. An approval is recorded evidence, not an
automatic merge or promotion decision.

Note excerpts in the preflight are capped at 400 characters and three notes,
with a pointer to read them in full. A note is written by another agent and can
be any length; dropping it whole into every preflight would let one verbose
colleague dominate the packet it rides along with.

## Seeing it from the Codex CLI

The Codex adapters (`~/.codex/AGENTS.md` and
`~/.codex/skills/personal-agent-os/SKILL.md`) instruct the agent to read the
inbox and check scope before substantial edits, and -- importantly -- to
**surface what it finds to you verbatim** rather than acting on it silently.
You need to see that agents are talking, not just that one of them decided
something.

To look yourself at any time:

```powershell
agent-os work-status                  # who is working, and unread note counts
agent-os work-inbox                   # every waiting note, all projects
agent-os work-inbox --project hr-gui --all   # including acknowledged ones
```

## Design decisions worth knowing

**Claims are machine-local, not in Git.** Two agents pushing claim files would
collide on precisely the thing claims exist to prevent, and a claim is
worthless a day later. They live in `~/.agent-os/work-claims.json`
(`AGENT_OS_CLAIMS` overrides), written atomically so simultaneous writers
cannot shred the file.

**Claims expire.** An agent that crashes must not hold ground for ever, so a
claim carries a lease (90 minutes by default) and goes stale without a
heartbeat. Expiry is evaluated on read, so a dead session stops blocking even
if nothing tidies up after it.

**Scope overlap is generous.** A directory covers everything beneath it, globs
match both ways, and a claim with no scope claims everything. False overlaps
cost a message; missed overlaps cost a day of invalidated measurement.

**A corrupt registry degrades to empty** rather than raising. Coordination
failing must never block the work it is meant to support.

## Known limits

- It covers agents **on this machine that chose to announce themselves**. An
  agent that never calls it is invisible, and so is one on another machine.
  `work-status` says so in its own output rather than implying coverage it does
  not have.
- Overlap is computed on declared scope, not on what an agent actually edits.
  An agent that claims narrowly and edits widely will not be caught.
- There is no cross-machine registry. A shared one would need a service, and
  the failure this addresses was two agents on one workstation.
