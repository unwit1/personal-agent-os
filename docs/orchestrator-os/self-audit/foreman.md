# Foreman strategy evidence

Command: `python -m agent_os orchestrate foreman strategy`

## Host models

| Host | Model | Provider hint | Effort | Source |
|---|---|---|---|---|
| claude | `claude-opus-5-5` | `claude-code` | null | latest Claude Code session (`09ecc8b6-e4e8-4fe6-9c4b-65c08a3f6566.jsonl`) |
| chatgpt | `gpt-6.1-sol` | `codex` | high | `~/.codex/config.toml` |

The active host is `null`.

## Strategy table

Scores are tier-derived; N=0 measured plans.

| Model | Tier | Score | Band | Source |
|---|---|---:|---|---|
| `gpt-6-astra` (codex) | frontier | 0.95 | strong | `~/.codex/config.toml` |
| `opus` (claude-code) | reasoning | 0.85 | strong | latest Claude Code session (`09ecc8b6-e4e8-4fe6-9c4b-65c08a3f6566.jsonl`) |
| `gpt-6-sol` (codex) | balanced | 0.6 | medium | `~/.codex/config.toml` |
| `sonnet` (claude-code) | balanced | 0.6 | medium | latest Claude Code session (`09ecc8b6-e4e8-4fe6-9c4b-65c08a3f6566.jsonl`) |
| `gpt-6-luna` (codex) | fast | 0.35 | weak | `~/.codex/config.toml` |
| `haiku` (claude-code) | fast | 0.35 | weak | latest Claude Code session (`09ecc8b6-e4e8-4fe6-9c4b-65c08a3f6566.jsonl`) |

## foreman_ranking

The command returned `foreman_ranking: []`; there are zero ranked entries, scores, or evidence counts to list.

## Findings

- The strategy table contains 6 model rows with scores from 0.35 to 0.95, sourced from 2 host configs (claude-code session and ~/.codex/config.toml).
- There are 2 detected host models and no active host (`active: null`).
- All 6 band assignments are tier-derived with 0 measured samples (N=0, below 5), so all are low-confidence. The foreman ranking is empty because no `foreman eval` has been run.
