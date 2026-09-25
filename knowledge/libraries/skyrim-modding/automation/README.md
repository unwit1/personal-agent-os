# Skyrim Mod Factory Automation

This directory turns the Skyrim Modding Knowledge Repository into a practical implementation, validation, testing, debugging, and release system.

## Primary workflow

1. `mod-factory-architecture.md` — idea → requirements → implementation → build → validation → game test → release.
2. `implementation-question-preemption.md` — resolve technical questions before asking the user.
3. `implementation-selection-rules.md` — choose the least invasive correct implementation layer/tool.
4. `mod-archetype-playbooks.md` — translate common mod ideas into likely architecture, checks and tests.
5. `tool-framework-adapter-matrix.md` — tool/framework capability and automation boundaries.
6. `command-line-integration.md` — supported CLI/library launch surfaces.
7. `validation-gates.md` — G00–G23 mandatory quality gates.
8. `schema-oracle-and-differential-validation.md` — xEdit + Mutagen + CK/runtime cross-check strategy.
9. `automated-test-fixture-catalog.md` — F01–F28 reusable regression fixtures.
10. `autonomous-debug-repair-loop.md` — evidence-driven failure classification, safe auto-repair and regression promotion.

## Engineering and source-control surfaces

- `repository-spriggit-ci-strategy.md` — Git/Spriggit/CI/reproducible-build model.
- `framework-analyzer-integration-priorities.md` — integration order for xEdit, Mutagen, Spriggit, MO2, analyzers and framework adapters.
- `schema-triangulation-and-self-checks.md` — additional multi-source self-check strategy.
- `agent-runtime-test-harness.md` — runtime testing architecture.
- `ai-native-modding-stack.md` — AI-assisted/native implementation stack.
- `ai-tool-adapter-matrix.md` — AI/tool boundary mapping.

## Machine-readable surfaces

- `adapters/core-adapters.json` — current core tool adapter registry.
- `analyzer-rule-pack-core.json` — canonical machine-readable bug/analyzer rule pack.
- `analyzers/core-rules.json` — generated compatibility mirror of the canonical pack; do not edit directly.

Repository-wide schemas currently include:
- `schemas/skyrim-mod-project-v1.schema.json`;
- `schemas/skyrim-tool-adapter-v1.schema.json`;
- `schemas/skyrim-mod-build-report-v1.schema.json`;
- `schemas/skyrim-analyzer-rule-v1.schema.json`.

Executable scaffolding lives in `tools/skyrim_mod_factory/`:
- `bootstrap_project.py`;
- `validate_project.py`;
- `plan_project.py`.

## Core principle

Maximize deterministic generation and verification. Keep an explicit boundary around things that still require CK/game/visual/subjective validation.

Every mod project should be driven by a machine-readable manifest, every automated tool invocation should preserve provenance/logs/hashes, and every release candidate should produce a machine-readable build report.

Every validated bug should become one or more of:
- an analyzer rule;
- a fixture;
- a validation gate;
- a regression assertion;
- an adapter error signature.

The long-term objective is for the user to describe a mod idea in natural language and have Agent OS perform almost all low-level architecture selection, generation, checking, rebuilding and debugging automatically.
