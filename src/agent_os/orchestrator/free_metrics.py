"""Metrics report for FreeComputeBroker free-request ledger.

Measures useful progress per free request, validator/review acceptance,
paid fallbacks avoided, and estimated paid cost avoided by using free routes
instead of paid alternatives.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import free_quota

SCHEMA_VERSION = "agent-os/free-metrics/v1"


def read_ledger(home: Path | None = None) -> list[dict[str, Any]]:
    """Load all free-compute ledger events from orchestrator home."""
    return free_quota.read_events(home)


def report(
    ledger_events: list[dict[str, Any]],
    *,
    prices: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate metrics report from free-compute ledger events.

    Args:
        ledger_events: Attempt and verdict events from the free-quota ledger.
                      Attempt events have no 'type' field; verdict events have type='verdict'.
                      Accepted attempt events should have a 'paid_route' field:
                      {"model": str, "provider": str|None, "subscription": bool}.
        prices: Model prices dict mapping model name to {"input": float, "output": float}.
                If None, estimated_paid_cost_avoided_usd will be None with 'no prices supplied' note.

    Returns:
        Dict with metrics: requests, useful_progress_per_request, validator_acceptance,
        review_acceptance, retries, escalations, paid_fallbacks_avoided,
        estimated_paid_cost_avoided_usd, estimated_paid_cost_basis,
        estimated_paid_cost_coverage, by_task_family, by_model, errors.

        estimated_paid_cost_basis: "per accepted free result: tokens x price of the paid route that would have run"
        estimated_paid_cost_coverage: {"priced": int, "accepted": int} count of events that were priced vs total accepted
    """
    prices_was_none = prices is None
    prices = prices or {}

    # Copy events to avoid mutating caller's data
    # Attempt events have no 'type' field; verdict events have type='verdict'
    attempts = [dict(e) for e in ledger_events if e.get("type") is None]
    verdicts = [e for e in ledger_events if e.get("type") == "verdict"]

    # Collect errors early
    errors = []

    # Build verdict map and track unknown event_ids (R5-1)
    verdict_map: dict[str, dict[str, Any]] = {}
    attempt_map = {e.get("event_id"): e for e in attempts if e.get("event_id")}

    for verdict in verdicts:
        event_id = verdict.get("event_id")
        if not event_id:
            errors.append(f"verdict for unknown event_id: no event_id provided")
        elif event_id not in attempt_map:
            errors.append(f"verdict for unknown event_id {event_id}")
        else:
            verdict_map[event_id] = verdict

    # Apply verdicts to copies of attempts
    for event_id, verdict in verdict_map.items():
        if event_id in attempt_map:
            for key in ["validator_passed", "accepted", "escalated"]:
                if key in verdict:
                    attempt_map[event_id][key] = verdict[key]

    # Basic counts
    total_requests = len(attempts)

    def _is_useful(evt: dict[str, Any]) -> bool:
        """Check if event is accepted and not escalated."""
        return evt.get("accepted") is True and evt.get("escalated") is not True

    # Sum useful units only for accepted results
    total_useful_units = 0
    useful_accepted = []  # For calculating cost avoided
    retries = 0
    escalations = 0
    validated_count = 0
    validated_pass_count = 0
    reviewed_count = 0
    reviewed_accept_count = 0

    for evt in attempts:
        if evt.get("retry", 0) > 0:
            retries += 1

        if evt.get("escalated") is True:
            escalations += 1

        # Track validator pass attempts
        if evt.get("validator_passed") is not None:
            validated_count += 1
            if evt.get("validator_passed") is True:
                validated_pass_count += 1

        # Track review/acceptance attempts
        if evt.get("accepted") is not None:
            reviewed_count += 1
            if evt.get("accepted") is True:
                reviewed_accept_count += 1

        # Collect accepted, non-escalated results for cost calculation and useful units
        if _is_useful(evt):
            useful_accepted.append(evt)
            useful_units = evt.get("useful_units", 0)
            if isinstance(useful_units, (int, float)):
                total_useful_units += useful_units

    # Calculate rates
    validator_acceptance = (
        round(validated_pass_count / validated_count, 3)
        if validated_count > 0
        else None
    )

    review_acceptance = (
        round(reviewed_accept_count / reviewed_count, 3)
        if reviewed_count > 0
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

    # Validate prices structure (R5-4)
    prices_invalid = False
    if prices is not None and not isinstance(prices, dict):
        errors.append("invalid prices: expected mapping of model -> {input, output}")
        prices_invalid = True
        prices = {}
    else:
        # Validate per-model entries
        if prices:
            for model, price_entry in list(prices.items()):
                if not isinstance(price_entry, dict):
                    errors.append(f"invalid prices for model {model}: expected dict with input/output fields")
                    del prices[model]
                else:
                    for key in ["input", "output"]:
                        val = price_entry.get(key)
                        if val is not None:
                            if isinstance(val, bool) or not isinstance(val, (int, float)):
                                errors.append(f"invalid price for {model}/{key}: expected number, got {type(val).__name__}")
                                del prices[model]
                                break
                            elif val < 0:
                                errors.append(f"invalid price for {model}/{key}: negative price")
                                del prices[model]
                                break

    # Estimate paid cost avoided using per-event paid_route (R5-2, R5-3)
    estimated_paid_cost_avoided_usd = None
    cost_basis = "per accepted free result: tokens x price of the paid route that would have run"
    estimated_paid_cost_coverage = None

    if useful_accepted:
        # If prices was None, report that upfront
        if prices_was_none:
            errors.append("no prices supplied")

        # Don't add granular unpriced errors if prices were invalid
        suppress_unpriced_errors = prices_was_none or prices_invalid

        total_cost = 0.0
        priced_count = 0
        unpriced_reasons = {}  # Track reasons for unpriced events

        for evt in useful_accepted:
            paid_route = evt.get("paid_route")
            if not paid_route:
                if not suppress_unpriced_errors:
                    unpriced_reasons.setdefault("no paid_route", 0)
                    unpriced_reasons["no paid_route"] += 1
                continue

            if not isinstance(paid_route, dict):
                if not suppress_unpriced_errors:
                    unpriced_reasons.setdefault("invalid paid_route", 0)
                    unpriced_reasons["invalid paid_route"] += 1
                continue

            model = paid_route.get("model")
            subscription = paid_route.get("subscription", False)

            if subscription:
                # Subscription routes cost 0
                priced_count += 1
                continue

            # Get tokens
            tokens = evt.get("tokens", {})
            input_tokens = tokens.get("input", 0) if isinstance(tokens, dict) else 0
            output_tokens = tokens.get("output", 0) if isinstance(tokens, dict) else 0

            if not (input_tokens or output_tokens):
                if not suppress_unpriced_errors:
                    unpriced_reasons.setdefault("missing tokens", 0)
                    unpriced_reasons["missing tokens"] += 1
                continue

            if not model:
                if not suppress_unpriced_errors:
                    unpriced_reasons.setdefault("no model in paid_route", 0)
                    unpriced_reasons["no model in paid_route"] += 1
                continue

            # Check if model has prices
            if prices_invalid or model not in prices:
                if not suppress_unpriced_errors:
                    unpriced_reasons.setdefault(f"no price for {model}", 0)
                    unpriced_reasons[f"no price for {model}"] += 1
                continue

            model_price = prices[model]
            if not isinstance(model_price, dict):
                if not suppress_unpriced_errors:
                    unpriced_reasons.setdefault(f"invalid price for {model}", 0)
                    unpriced_reasons[f"invalid price for {model}"] += 1
                continue

            input_price = model_price.get("input")
            output_price = model_price.get("output")

            # Check for None or missing prices
            if input_price is None or output_price is None:
                if not suppress_unpriced_errors:
                    unpriced_reasons.setdefault(f"incomplete price for {model}", 0)
                    unpriced_reasons[f"incomplete price for {model}"] += 1
                continue

            try:
                input_price = float(input_price)
                output_price = float(output_price)
            except (ValueError, TypeError):
                if not suppress_unpriced_errors:
                    unpriced_reasons.setdefault(f"invalid price type for {model}", 0)
                    unpriced_reasons[f"invalid price type for {model}"] += 1
                continue

            # Prices are per million tokens
            cost = (input_tokens * input_price + output_tokens * output_price) / 1e6
            total_cost += cost
            priced_count += 1

        # Add aggregated errors for unpriced reasons (but not if already reported no prices)
        if not prices_was_none:
            for reason, count in unpriced_reasons.items():
                errors.append(f"unpriced events ({reason}): {count}")

        # Set cost and coverage only if we have priced events
        if priced_count > 0:
            estimated_paid_cost_avoided_usd = round(total_cost, 6)

        estimated_paid_cost_coverage = {
            "priced": priced_count,
            "accepted": len(useful_accepted)
        }
    else:
        # No accepted results
        if prices_was_none:
            errors.append("no prices supplied")

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
            # Only count useful_units for accepted, non-escalated results
            if _is_useful(evt):
                useful_units = evt.get("useful_units", 0)
                if isinstance(useful_units, (int, float)):
                    groups[key]["useful_units"] += useful_units
        return groups

    by_family = _group_by_key("task_family")
    by_model = _group_by_key("model")

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
        "estimated_paid_cost_basis": cost_basis if estimated_paid_cost_avoided_usd is not None else None,
        "estimated_paid_cost_coverage": estimated_paid_cost_coverage,
        "by_task_family": by_family,
        "by_model": by_model,
        "errors": errors,
    }
