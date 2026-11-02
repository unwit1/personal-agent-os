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
| `gpt-6-astra` (codex) | frontier | 0.95 | strong | tier: frontier in its provider's lineup |
| `opus` (claude-code) | reasoning | 0.85 | strong | tier: reasoning in its provider's lineup |
| `gpt-6-sol` (codex) | balanced | 0.6 | medium | tier: balanced in its provider's lineup |
| `sonnet` (claude-code) | balanced | 0.6 | medium | tier: balanced in its provider's lineup |
| `gpt-6-luna` (codex) | fast | 0.35 | weak | tier: fast in its provider's lineup |
| `haiku` (claude-code) | fast | 0.35 | weak | tier: fast in its provider's lineup |

## foreman_ranking

The command returned `foreman_ranking: []`; there are zero ranked entries, scores, or evidence counts to list.

## Findings

- The strategy table has 6 model rows, with tier-derived scores from 0.35 to 0.95; each shows 0 measured plans (N=0), so the score has no plan sample backing and is low-confidence.
- There are 2 detected host models and no active host (`active: null`).
- The foreman ranking has 0 entries and 0 evidence counts; no recommendation is supported by eval samples.
