---
name: compile-project-context
description: Build the smallest sufficient evidence-based task packet when starting or resuming work in a registered project.
---

# Compile project context

Run `agent-os context <project> "<task>"` before meaningful project work.

Use the returned project policy, current state, latest relevant checkpoint/handoff,
exact search matches, and matched skills. Apply `context-budgeter` so the packet
contains only information needed for the current task or workflow stage.

Inspect additional files only when the packet points to them or when a concrete
execution/validation gap remains. Do not preload future-stage context, full
transcripts, or unrelated project history. Never replace project-local authority
with cross-project memory.

When a valid staged-work checkpoint exists, use it rather than reconstructing
completed work. If the project has uncommitted work, preserve it and determine
whether it overlaps the requested task before editing.

After material changes, validate the affected scope and write a compact handoff
or stage checkpoint.
