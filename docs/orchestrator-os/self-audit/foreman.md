# Foreman strategy evidence

Command: `python -m agent_os orchestrate foreman strategy`

## Host models

| Host | Model | Provider hint | Effort | Source |
|---|---|---|---|---|
| claude | `claude-opus-5-5` | `claude-code` | null | latest Claude Code session (`09ecc8b6-e4e8-4fe6-9c4b-65c08a3f6566.jsonl`) |
| chatgpt | `gpt-6.1-sol` | `codex` | high | `~/.codex/config.toml` |

The active host is `null`.

## Strategy table

The command reported no cost or sample-size fields for these strategy rows.

| Model | Tier | Score | Band |
|---|---|---:|---|
| `gpt-6-astra` (codex) | frontier | 0.95 | strong |
| `opus` (claude-code) | reasoning | 0.85 | strong |
| `gpt-6-sol` (codex) | balanced | 0.6 | medium |
| `sonnet` (claude-code) | balanced | 0.6 | medium |
| `gpt-6-luna` (codex) | fast | 0.35 | weak |
| `haiku` (claude-code) | fast | 0.35 | weak |

## foreman_ranking

The command returned `foreman_ranking: []`; there are zero ranked entries, scores, or evidence counts to list.

## Findings

- The strategy table contains 6 model rows, with scores from 0.35 to 0.95; it provides no cost or sample-size values, so cost and empirical evidence strength cannot be assessed from this output.
- There are 2 detected host models and no active host (`active: null`).
- The foreman ranking contains 0 recommendations. Therefore no recommendation has a sample count to assess, and none can be identified as low-confidence based on fewer than 5 samples.
