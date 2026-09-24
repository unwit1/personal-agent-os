# Model value routing

Status: design (2026-09-24). Implementation tasks T1–T3 below are fully
specified so a `fast` model can implement each without design decisions.

## Goal

Route each capability tier to a model from price and benchmark evidence, and
keep that current as vendors ship models, without a person running anything.

- **Design tiers** (`reasoning`, `frontier`): the model with the highest
  `intelligence_index` wins; price only breaks ties.
- **Implementation tiers** (`fast`, `balanced`): the lowest effective price
  wins. Quality is enforced by validators and the escalation ladder.
- A tier changes only when every provider's model for that tier has the
  evidence the rule needs; otherwise the tier is reported as `needs_evidence`
  and its configured costs are left alone.

## Evidence store (T1)

File: `orchestrator_home() / "models" / "evidence.json"` (local, not in Git).

```json
{
  "models": {
    "gpt-6-sol": {
      "provider": "codex",
      "price": {"input": 2.0, "cached_input": 0.2, "output": 10.0},
      "benchmarks": {"intelligence_index": 48, "coding_index": 57},
      "sources": ["https://developers.openai.com/api/docs/pricing.md"],
      "updated_at": "2026-09-24T15:00:00+00:00"
    }
  }
}
```

Prices are USD per 1M tokens, standard (not batch/flex) short-context rates.
Benchmark values are numbers or absent; never strings.

## Module `src/agent_os/orchestrator/model_value.py` (T1)

```python
CACHE_SHARE = 0.9    # share of input tokens served from cache (runs measure ~0.94)
OUTPUT_RATIO = 0.02  # output tokens per input token (runs measure ~0.012)
DESIGN_TIERS = ("reasoning", "frontier")
IMPLEMENTATION_TIERS = ("fast", "balanced")

def evidence_path() -> Path
def load_evidence() -> dict            # {"models": {}} when missing or invalid JSON
def save_evidence(evidence: dict) -> None   # creates parent dirs, indent=1
def record_evidence(model_id: str, *, provider: str | None = None,
                    price: dict | None = None, benchmarks: dict | None = None,
                    source: str | None = None) -> dict
    # load, merge (price/benchmarks dicts are merged key by key, None values
    # ignored), append source to "sources" if new, set updated_at=now(), save,
    # return the entry.
def effective_price(price: dict) -> float | None
    # None unless input, cached_input and output are all numbers.
    # (1 - CACHE_SHARE) * input + CACHE_SHARE * cached_input + OUTPUT_RATIO * output,
    # rounded to 6 places.
def resolve_model(provider_id: str, model: str, evidence: dict) -> str | None
    # model itself if it is a key of evidence["models"].
    # Otherwise, for provider "claude-code" and a bare alias such as "sonnet":
    # the evidence key with the highest agent_os.orchestrator.models.version_key
    # among keys whose family (version_key(key)[0]) is f"claude-{model}".
    # Otherwise None.
def tier_costs(registry_providers: list[dict], evidence: dict) -> dict
```

`tier_costs` input is `ProviderRegistry().providers` (each has `id`,
`models: {tier: model}`, `costs: {tier: number}`). It returns:

```python
{
  "costs": {"codex": {"fast": 0.0595, ...}, "claude-code": {...}},  # only tiers that changed rule
  "tiers": {"reasoning": {"status": "ok" | "needs_evidence", "winner": "claude-code",
                          "models": {"claude-code": "claude-opus-5-5", "codex": "gpt-6-sol"},
                          "missing": ["codex:gpt-6-sol intelligence_index"]}, ...}
}
```

Per tier present in any provider's `models`:
- resolve each provider's model; missing resolution, missing price, or (design
  tiers) missing `intelligence_index` adds an entry to `missing` and makes the
  tier `needs_evidence` (no costs emitted for that tier);
- implementation tier cost = `effective_price(price)`;
- design tier cost = `round((100 - intelligence_index) + effective_price / 1000, 6)`;
- `winner` = provider with the lowest cost (first in list order on a tie).

## Module `src/agent_os/orchestrator/model_prices.py` (T2)

```python
PRICE_PAGES = [
  {"provider": "claude-code", "url": "https://platform.claude.com/docs/en/about-claude/pricing.md", "parser": "anthropic"},
  {"provider": "codex", "url": "https://developers.openai.com/api/docs/pricing.md", "parser": "openai"},
]
def parse_openai(markdown: str) -> dict[str, dict]
def parse_anthropic(markdown: str) -> dict[str, dict]
def fetch_prices(opener=None) -> dict   # {"prices": {model: {..., "provider", "source"}}, "checks": [...]}
```

Both parsers return `{model_id: {"input": float, "cached_input": float, "output": float}}`
and keep only the **first** row seen for a model (later tables are batch/flex).

- `parse_openai`: markdown table rows `| gpt-6-sol | $2.00 | $0.20 | $2.50 | $10.00 | ...`.
  Use a table only when its header row's cells 1, 2 and 4 contain "input",
  "cached input" and "output" (case-insensitive). Model id = cell 0 up to the
  first space; keep only ids matching `^gpt-[\w.\-]+$`. Cells: 1 input,
  2 cached input, 4 output. Skip a row when any of those three is "-".
- `parse_anthropic`: table whose header contains "Base input tokens",
  "Cache hits and refreshes" and "Output tokens". Row name cell such as
  `Claude Opus 5.5` or `Claude Opus 4 ([retired, ...](...))`: drop any text from
  " (" onward, then `Claude Opus 5.5` -> `claude-opus-5-5` (lowercase, spaces
  and dots to hyphens). Skip names containing "Mythos". Price cell such as
  `$2 / MTok<sup>3</sup>`: the first `\$([\d.]+)` number.
- `fetch_prices`: `urllib.request` GET with a browser User-Agent and a
  20 s timeout; any exception becomes a check with `ok: false` and never raises.

Fixtures: `tests/fixtures/pricing/openai.md`, `tests/fixtures/pricing/anthropic.md`.
Expected from them: `gpt-6-sol` = 2.0/0.2/10.0, `gpt-6-luna` = 0.1/0.01/0.5,
`gpt-5.6-terra` output 12.0, `claude-sonnet-5` = 2/0.2/10, `claude-opus-5-5` = 4/0.2/20,
`claude-haiku-4-5` = 1/0.1/5, no key containing "mythos".

## Wiring (T3, depends on T1 and T2)

In `models.refresh()`, after proposals are computed and only when `online` is true:
1. `model_prices.fetch_prices()`; for each price call `model_value.record_evidence(model, provider=..., price=..., source=url)`; append its checks to `checks`.
2. `result = model_value.tier_costs(registry.providers, model_value.load_evidence())`.
3. When `result["costs"]` differs from the registry's current costs for those
   provider tiers, write them into the registry file (`capabilities.registry_path()`)
   under each provider's `costs`, after copying the file to `<name>.bak-value`, and
   add a notice `{"kind": "routing_costs_updated", "text": "...", "at": stamp}`.
4. Store `result["tiers"]` in the catalog as `catalog["value"]`, and include it in `view()`.

Scheduling: `service.create()` and `service.start_recommended()` start
`models.refresh_if_stale()` in a daemon thread (same pattern as `cli.py` gui).

Benchmarks are not parsed from web pages (no stable free source). They enter
through `record_evidence(..., benchmarks=...)` from an automated research step
(next stage) or a trial, each with a source URL.
