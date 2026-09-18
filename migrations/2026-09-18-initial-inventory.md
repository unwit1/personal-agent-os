# Initial ecosystem inventory

Inventory date: 2026-09-18

## Projects found

- **HR GUI** — active Git repository with a GitHub remote, canonical project
  guide, compact adapters, handoffs, memory, tests, and repo-local skills.
- **Job Applicant Dashboard** — active local non-Git project; registered with a
  strict applicant-data boundary. Only compact central state is indexed by default.
- **AutoClick**, **OvertimeParser**, and **TES Tagger** — registered local projects
  with project-specific secret/data exclusions.
- **ScanRenamer** — registered as a candidate because the directory is empty and
  its intended scope cannot safely be inferred from its name.

## Agent infrastructure found

- User-level Codex instructions exist but contained no durable text at inventory time.
- Installed/plugin-provided skills are managed infrastructure and are referenced
  by the client, not copied into this repository.
- HR GUI owns eleven canonical skills under `.agents/skills/`; Personal Agent OS
  discovers them through project routing rather than duplicating them.

## Migration decisions

- HR GUI is the first end-to-end integration because it is active, versioned,
  and already has safe context boundaries.
- Project-specific policy and skills remain project-local. This repository owns
  cross-project routing, preferences, schemas, retrieval, and handoff conventions.
- No legacy file was moved, deleted, or rewritten.
- No HR data, spreadsheets, runtime configuration, logs, or OCR artifacts were read
  or indexed.
- The Personal Agent OS is hosted privately at
  `https://github.com/unwit1/personal-agent-os` and local routing adapters were installed.

## Legacy-to-canonical mapping

| Existing source | Canonical owner | Agent OS behavior |
| --- | --- | --- |
| `HR GUI/PROJECT_GUIDE.md` | HR GUI | Retrieve for HR GUI tasks |
| `HR GUI/AGENTS.md`, `CLAUDE.md` | HR GUI | Keep as project adapters |
| `HR GUI/.agents/skills/` | HR GUI | Discover metadata; load only matches |
| `HR GUI/HANDOFF.md`, `docs/HANDOFF.md` | HR GUI | Retrieve latest project state |
| Bootstrap preference seed | Personal Agent OS | Migrated to `profile/preferences.json` |
