# Skyrim Mod Factory Automation

This directory turns the Skyrim Modding Knowledge Repository into an implementation system.

## Start here

- `mod-factory-architecture.md` — end-to-end idea-to-release pipeline.
- `tool-framework-adapter-matrix.md` — which tool/framework to use and how to automate it.
- `validation-gates.md` — mandatory static/integration/runtime/release checks.
- `implementation-question-preemption.md` — questions Agent OS should resolve before asking the user.
- `autonomous-debug-repair-loop.md` — evidence-driven automated debugging/repair.

## Core principle

The agent should maximize deterministic generation and verification while preserving an explicit boundary around things that still require CK/game/visual/subjective validation.

Every mod project should be driven by a machine-readable manifest and produce a machine-readable build report.
