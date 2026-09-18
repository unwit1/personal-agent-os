# Initial ecosystem inventory

Inventory date: 2026-09-18

## Projects found

- **HR GUI** — active Git repository with a GitHub remote, canonical project
  guide, compact adapters, handoffs, memory, tests, and repo-local skills.
- **Job Applicant Dashboard** — local non-Git project; contains business data
  artifacts and was not ingested.
- **AutoClick**, **OvertimeParser**, **ScanRenamer**, and **TES Tagger** — local
  projects without Git metadata detected at inventory time. Registered later
  only after ownership, privacy, and active status are reviewed.

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
- GitHub repository creation and push remain pending explicit user authorization.

## Legacy-to-canonical mapping

| Existing source | Canonical owner | Agent OS behavior |
| --- | --- | --- |
| `HR GUI/PROJECT_GUIDE.md` | HR GUI | Retrieve for HR GUI tasks |
| `HR GUI/AGENTS.md`, `CLAUDE.md` | HR GUI | Keep as project adapters |
| `HR GUI/.agents/skills/` | HR GUI | Discover metadata; load only matches |
| `HR GUI/HANDOFF.md`, `docs/HANDOFF.md` | HR GUI | Retrieve latest project state |
| Bootstrap preference seed | Personal Agent OS | Migrated to `profile/preferences.json` |
