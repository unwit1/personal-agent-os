"""Fetch and parse standard model pricing from vendor documentation."""

from __future__ import annotations

import re
import time
import urllib.request
from typing import Any

PRICE_PAGES = [
    {"provider": "claude-code", "url": "https://platform.claude.com/docs/en/about-claude/pricing.md", "parser": "anthropic"},
    {"provider": "codex", "url": "https://developers.openai.com/api/docs/pricing.md", "parser": "openai"},
    # Every open model sold per token (Qwen, DeepSeek, Llama, gpt-oss...), as
    # "vendor/model" ids; listed last so vendor pages win for their own models.
    {"provider": "openrouter", "url": "https://openrouter.ai/api/v1/models", "parser": "openrouter"},
]
FETCH_TIMEOUT = 20
_GPT_ID = re.compile(r"^gpt-[\w.\-]+$")
_PRICE = re.compile(r"\$([\d.]+)")


def _cells(line: str) -> list[str] | None:
    if not line.strip().startswith("|"):
        return None
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _number(cell: str) -> float | None:
    match = _PRICE.search(cell)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def parse_openai(markdown: str) -> dict[str, dict]:
    result: dict[str, dict] = {}
    active = False
    for line in markdown.splitlines():
        cells = _cells(line)
        if cells is None:
            continue
        lower = [cell.casefold() for cell in cells]
        if len(cells) >= 5 and "input" in lower[1] and "cached input" in lower[2] and "output" in lower[4]:
            active = True
            continue
        if active and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        if not active or len(cells) < 5:
            continue
        model = cells[0].split(" ", 1)[0]
        if not _GPT_ID.fullmatch(model) or model in result or any(cells[index] == "-" for index in (1, 2, 4)):
            continue
        values = [_number(cells[index]) for index in (1, 2, 4)]
        if all(value is not None for value in values):
            result[model] = dict(zip(("input", "cached_input", "output"), values))
    return result


def parse_anthropic(markdown: str) -> dict[str, dict]:
    result: dict[str, dict] = {}
    active = False
    for line in markdown.splitlines():
        cells = _cells(line)
        if cells is None:
            continue
        lower = [cell.casefold() for cell in cells]
        if all(any(label.casefold() in cell for cell in lower) for label in ("Base input tokens", "Cache hits and refreshes", "Output tokens")):
            active = True
            continue
        if active and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        if not active or len(cells) < 6:
            continue
        name = cells[0].split(" (", 1)[0].strip()
        if not name.casefold().startswith("claude ") or "mythos" in name.casefold():
            continue
        model = "claude-" + re.sub(r"[ .]+", "-", name[len("Claude "):].casefold())
        if model in result:
            continue
        values = [_number(cells[index]) for index in (1, 4, 5)]
        if all(value is not None for value in values):
            result[model] = dict(zip(("input", "cached_input", "output"), values))
    return result


def parse_openrouter(text: str) -> dict[str, dict]:
    """OpenRouter's public model list (JSON): USD per token -> USD per million."""
    import json

    result: dict[str, dict] = {}
    try:
        data = json.loads(text).get("data") or []
    except (ValueError, AttributeError):
        return result
    for item in data:
        model, pricing = str(item.get("id") or ""), item.get("pricing") or {}
        if not model or ":" in model:  # skip :free / :batch variants; the base id carries the list price
            continue
        try:
            price_in, price_out = float(pricing["prompt"]) * 1e6, float(pricing["completion"]) * 1e6
            cached = float(pricing.get("input_cache_read") or pricing["prompt"]) * 1e6
        except (KeyError, TypeError, ValueError):
            continue
        if price_in < 0 or price_out < 0:  # negative = "varies" (routers)
            continue
        result[model] = {"input": round(price_in, 6), "cached_input": round(cached, 6), "output": round(price_out, 6)}
    return result


def fetch_prices(opener=None) -> dict[str, Any]:
    prices: dict[str, dict] = {}
    checks: list[dict[str, Any]] = []
    for page in PRICE_PAGES:
        started = time.monotonic()
        check: dict[str, Any] = {"provider": page["provider"], "url": page["url"], "ok": False}
        try:
            request = urllib.request.Request(page["url"], headers={"User-Agent": "Mozilla/5.0 (compatible; AgentOS/1)"})
            with (opener or urllib.request.urlopen)(request, timeout=FETCH_TIMEOUT) as response:
                markdown = response.read(3_000_000).decode("utf-8", "replace")
            parsed = globals()[f"parse_{page['parser']}"](markdown)
            for model, values in parsed.items():
                prices.setdefault(model, {**values, "provider": page["provider"], "source": page["url"]})
            check.update(ok=bool(parsed), models=len(parsed), error=None if parsed else "no prices found")
        except Exception as exc:
            check.update(ok=False, models=0, error=f"{type(exc).__name__}: {exc}"[:200])
        check["seconds"] = round(time.monotonic() - started, 2)
        checks.append(check)
    return {"prices": prices, "checks": checks}
