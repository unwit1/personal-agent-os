"""Metrics report for FreeComputeBroker free-request ledger.

Measures useful progress per free request, validator/review acceptance,
paid fallbacks avoided, and estimated paid cost avoided by using free routes
instead of paid alternatives.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from . import free_quota

SCHEMA_VERSION = "agent-os/free-metrics/v1"


def read_ledger(home: Path | None = None) -> list[dict[str, Any]]:
    """Load all free-compute ledger events from orchestrator home."""
    return free_quota.read_events(home)


def report(
    ledger_events: list[dict[str, Any]],
    *,
    prices: dict[str, Any] | None = None,
    paid_model_for: Callable[[str, str], str | None] | None = None
) -> dict[str, Any]:
    """Generate metrics report from free-compute ledger events.

    Args:
        ledger_events: Attempt and verdict events from the free-quota ledger.
        prices: Model prices dict (from model_prices.fetch_prices()["prices"]).
                If None, estimated_paid_cost_avoided_usd will be None.
        paid_model_for: Optional callable(free_model, task_family) -> paid_model_name.
                       If provided, used to price the paid route instead of the free model.

    Returns:
        Dict with metrics: requests, useful_progress_per_request, validator_acceptance,
        review_acceptance, retries, escalations, paid_fallbacks_avoided,
        estimated_paid_cost_avoided_usd, by_task_family, by_model, errors.
    """
    prices = prices or {}

    # Copy events to avoid mutating caller's data
    attempts = [dict(e) for e in ledger_events if e.get("type") != "verdict"]
    verdicts = [e for e in ledger_events if e.get("type") == "verdict"]

    # Build verdict map and apply to copies of attempts
    verdict_map: dict[str, dict[str, Any]] = {}
    for verdict in verdicts:
        event_id = verdict.get("event_id")
        if event_id:
            verdict_map[event_id] = verdict

    attempt_map = {e.get("event_id"): e for e in attempts if e.get("event_id")}
    for event_id, verdict in verdict_map.items():
        if event_id in attempt_map:
            for key in ["validator_passed", "accepted", "escalated"]:
                if key in verdict:
                    attempt_map[event_id][key] = verdict[key]

    # Basic counts
    total_requests = len(attempts)

    # Sum useful units and count accepted results
    total_useful_units = 0
    useful_accepted = []  # For calculating cost avoided
    retries = 0
    escalations = 0
    validated_attempts = []  # where validator_passed is non-null
    reviewed_attempts = []  # where accepted is non-null

    for evt in attempts:
        useful_units = evt.get("useful_units", 0)
        if isinstance(useful_units, (int, float)):
            total_useful_units += useful_units

        if evt.get("retry", 0) > 0:
            retries += 1

        if evt.get("escalated") is True:
            escalations += 1

        # Track validator pass attempts
        if evt.get("validator_passed") is not None:
            validated_attempts.append(evt)

        # Track review/acceptance attempts
        if evt.get("accepted") is not None:
            reviewed_attempts.append(evt)

        # Collect accepted, non-escalated results for cost calculation
        if evt.get("accepted") is True and evt.get("escalated") is not True:
            useful_accepted.append(evt)

    # Calculate rates
    validator_pass_count = sum(1 for e in validated_attempts if e.get("validator_passed") is True)
    validator_acceptance = (
        round(validator_pass_count / len(validated_attempts), 3)
        if validated_attempts
        else None
    )

    review_accept_count = sum(1 for e in reviewed_attempts if e.get("accepted") is True)
    review_acceptance = (
        round(review_accept_count / len(reviewed_attempts), 3)
        if reviewed_attempts
        else None
    )

    # Useful progress per request (accepted useful units / total requests)
    useful_progress_per_request = (
        round(total_useful_units / total_requests, 3)
        if total_requests > 0
        else None
    )

    # Paid fallbacks avoided = accepted results that were never escalated
    paid_fallbacks_avoided = len(useful_accepted)

    # Estimate paid cost avoided
    estimated_paid_cost_avoided_usd = None
    cost_basis = None
    missing_prices = []

    if useful_accepted and prices:
        total_cost = 0.0
        calculated_any = False
        for evt in useful_accepted:
            free_model = evt.get("model")
            task_family = evt.get("task_family", "unknown")
            tokens = evt.get("tokens", {})
            input_tokens = tokens.get("input", 0) if isinstance(tokens, dict) else 0
            output_tokens = tokens.get("output", 0) if isinstance(tokens, dict) else 0

            if not free_model or not (input_tokens or output_tokens):
                continue

            # Determine the paid model to price
            paid_model = None
            if paid_model_for is not None:
                paid_model = paid_model_for(free_model, task_family)

            if paid_model is None:
                if free_model not in missing_prices:
                    missing_prices.append(f"{free_model} (no paid route)")
                continue

            if paid_model not in prices:
                if paid_model not in missing_prices:
                    missing_prices.append(paid_model)
                continue

            model_price = prices[paid_model]
            input_price = float(model_price.get("input") or 0)
            output_price = float(model_price.get("output") or 0)

            # Prices are per million tokens
            cost = (input_tokens * input_price + output_tokens * output_price) / 1e6
            total_cost += cost
            calculated_any = True

        if calculated_any:
            estimated_paid_cost_avoided_usd = round(total_cost, 6)
            cost_basis = "per accepted free result: tokens x price of the paid route that would have run"

    def _group_by_key(key_name: str) -> dict[str, dict[str, Any]]:
        """Group attempt metrics by a top-level event key."""
        groups: dict[str, dict[str, Any]] = {}
        for evt in attempts:
            key = evt.get(key_name, "unknown")
            if key not in groups:
                groups[key] = {"requests": 0, "accepted": 0, "escalated": 0, "useful_units": 0}
            groups[key]["requests"] += 1
            if evt.get("accepted") is True:
                groups[key]["accepted"] += 1
            if evt.get("escalated") is True:
                groups[key]["escalated"] += 1
            useful_units = evt.get("useful_units", 0)
            if isinstance(useful_units, (int, float)):
                groups[key]["useful_units"] += useful_units
        return groups

    by_family = _group_by_key("task_family")
    by_model = _group_by_key("model")

    # Build errors list
    errors = []
    if missing_prices:
        errors.append(
            f"estimated cost incomplete: no price data for models {sorted(missing_prices)}"
        )
    if verdicts and not attempts:
        errors.append("ledger contains verdict lines but no attempt lines")

    # Find an event with unknown event_id in verdict lines
    for verdict in verdicts:
        event_id = verdict.get("event_id")
        if event_id and event_id not in attempt_map:
            errors.append(f"verdict for unknown attempt event_id {event_id}")
            break

    return {
        "schema_version": SCHEMA_VERSION,
        "requests": total_requests,
        "useful_progress_per_request": useful_progress_per_request,
        "validator_acceptance": validator_acceptance,
        "review_acceptance": review_acceptance,
        "retries": retries,
        "escalations": escalations,
        "paid_fallbacks_avoided": paid_fallbacks_avoided,
        "estimated_paid_cost_avoided_usd": estimated_paid_cost_avoided_usd,
        "estimated_paid_cost_basis": cost_basis,
        "by_task_family": by_family,
        "by_model": by_model,
        "errors": errors,
    }
