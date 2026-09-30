"""Reflective optimization of a foreman's planning instructions (GEPA-style, subsumed).

Prior art: PA-gepa (GEPA, MIT, https://github.com/gepa-ai/gepa) -- reflective
prompt evolution: run the candidate, show a stronger "reflection" model the
failures with the metric's feedback, let it rewrite the instructions, keep the
best. Operator policy is to subsume rather than depend, so this is a small
loop over Agent OS's own pieces:

* candidate  = the planner addendum a foreman gets (foreman_strategy playbooks);
* rollout    = ``foreman_eval.run`` on the **dev** split only, with the same
  deterministic strategy the engine applies (merge, role normalization, guard);
* metric     = judgement accuracy after the strategy, then fewer tasks;
* reflection = one call to a stronger model (per token, not a subscription)
  that sees the plans and the scorer's verdicts and must write *general*
  rules, never case-specific ones;
* acceptance = strictly better on dev; the **held-out** split is scored once
  at the end, for the baseline and the winner, and is never shown to the
  reflector.

This is also the "weak foreman asks a strong model how to improve" path: the
winning addendum can be saved as the weak band's playbook for that model.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import foreman_eval

MAX_ADDENDUM_WORDS = 160
REFLECTION_RULES = (
    "Rewrite the planning instructions below so this planner makes better plans. Rules:\n"
    "- Write general rules about decomposition, task count and capability classes. Never mention the specific goals, files or task ids shown.\n"
    f"- At most {MAX_ADDENDUM_WORDS} words, plain sentences, no preamble.\n"
    "- Keep what already works; fix the failure patterns you see.\n"
    "Answer with the new instructions only."
)


def feedback(rows: list[dict[str, Any]], cases: dict[str, dict[str, Any]]) -> str:
    """What the reflector sees: per dev case, the plan shape and the scorer's verdict."""
    lines = []
    for row in rows:
        case = cases.get(row["case"]) or {}
        verdict = "PASS" if (row.get("guarded") or row).get("passed") else "FAIL"
        judged = row.get("guarded") or row
        why = []
        if row.get("error"):
            why.append(f"invalid plan: {row['error'][:160]}")
        if judged.get("over"):
            why.append(f"over-provisioned tasks: {judged['over']}")
        if judged.get("under"):
            why.append(f"no task at {case.get('floor_any')} or stronger although the goal needs it")
        if judged.get("tasks") is not None and not judged.get("count_ok"):
            low, high = case.get("tasks", [None, None])
            why.append(f"{judged['tasks']} tasks; a good plan here has {low}-{high}")
        classes = judged.get("classes")
        lines.append(f"- [{verdict}] goal: {case.get('goal', '')[:220]}\n  plan: {len(classes or [])} tasks, classes {classes}\n  "
                     + ("; ".join(why) if why else "good"))
    return "\n".join(lines)


def reflect(addendum: str, rows: list[dict[str, Any]], cases: dict[str, dict[str, Any]], ask: Callable[[str], str]) -> str:
    prompt = (f"{REFLECTION_RULES}\n\nCurrent instructions:\n\"\"\"\n{addendum or '(none)'}\n\"\"\"\n\n"
              f"How plans made with them scored (development cases):\n{feedback(rows, cases)}\n")
    text = (ask(prompt) or "").strip().strip('"').strip()
    words = text.split()
    return " ".join(words[:MAX_ADDENDUM_WORDS])


def score_key(summary: dict[str, Any], rows: list[dict[str, Any]]) -> tuple[float, float, int]:
    """Higher is better: accuracy after the strategy, then validity, then fewer tasks."""
    tasks = sum(((row.get("guarded") or row).get("tasks") or 0) for row in rows)
    return (summary.get("guarded_accuracy") or 0.0, summary.get("valid_plans") or 0.0, -tasks)


def optimize(*, planner_call: Callable[[str], dict[str, Any]], ask: Callable[[str], str], baseline: str, iterations: int = 4,
             strategy: dict[str, Any] | None = None, out_dir: Path | None = None) -> dict[str, Any]:
    """``planner_call(prompt) -> runner answer`` (the cheap foreman);
    ``ask(prompt) -> text`` (the reflector). Returns the history and the
    held-out comparison of baseline vs winner."""
    strategy = strategy if strategy is not None else {"guard": True}
    dev_cases = {case["id"]: case for case in foreman_eval.CASES}

    def evaluate(addendum: str, split: str) -> dict[str, Any]:
        def runner(prompt: str, workdir: Path) -> dict[str, Any]:
            return planner_call(prompt + ("\n\n" + addendum + "\n" if addendum else ""))

        report = foreman_eval.run("optimize", runner=runner, split=split, strategy_override=strategy,
                                  out_dir=(out_dir or Path(".")) / "rollouts")
        return report

    history = []
    best_text, best_report = baseline, evaluate(baseline, "dev")
    best_key = score_key(best_report["summary"], best_report["cases"])
    history.append({"candidate": 0, "accepted": True, "key": best_key, "summary": best_report["summary"], "addendum": best_text})
    for index in range(1, iterations + 1):
        child = reflect(best_text, best_report["cases"], dev_cases, ask)
        if not child or child == best_text:
            history.append({"candidate": index, "accepted": False, "reason": "no new candidate"})
            continue
        report = evaluate(child, "dev")
        key = score_key(report["summary"], report["cases"])
        accepted = key > best_key
        history.append({"candidate": index, "accepted": accepted, "key": key, "summary": report["summary"], "addendum": child})
        if accepted:
            best_text, best_report, best_key = child, report, key
    holdout = {"baseline": evaluate(baseline, "holdout")["summary"], "winner": evaluate(best_text, "holdout")["summary"] if best_text != baseline else None}
    result = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "baseline": baseline, "winner": best_text,
              "improved_on_dev": best_text != baseline, "history": history, "holdout": holdout}
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"optimize-{uuid.uuid4().hex[:6]}.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


def openrouter_caller(model: str, key: str, opener=None, max_tokens: int = 4096) -> Callable[[str], dict[str, Any]]:
    """A foreman_eval runner answer from one OpenRouter chat completion."""
    import time

    from .adapters.base import extract_structured
    from .foreman_deploy import OPENROUTER_BASE, _http

    def call(prompt: str) -> dict[str, Any]:
        started = time.monotonic()
        status, payload = _http(opener, "POST", f"{OPENROUTER_BASE}/v1/chat/completions", headers={"authorization": f"Bearer {key}"},
                                body={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}, timeout=300)
        seconds = round(time.monotonic() - started, 1)
        if status != 200 or not isinstance(payload, dict):
            return {"outcome": "failed", "detail": f"HTTP {status}: {str(payload)[:200]}", "seconds": seconds, "usage": {}}
        text = str((((payload.get("choices") or [{}])[0]).get("message") or {}).get("content") or "")
        usage = payload.get("usage") or {}
        return {"outcome": "completed", "structured": extract_structured(text), "text": text, "seconds": seconds, "model": model,
                "usage": {"input_tokens": usage.get("prompt_tokens"), "output_tokens": usage.get("completion_tokens"), "model_resolved": payload.get("model"),
                          "cost_usd": usage.get("cost")}}

    return call


def openrouter_asker(model: str, key: str, opener=None) -> Callable[[str], str]:
    call = openrouter_caller(model, key, opener, max_tokens=2048)
    return lambda prompt: call(prompt).get("text") or ""
