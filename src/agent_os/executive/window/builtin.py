"""Default registry initialization for the Executive window."""
from __future__ import annotations

from . import (
    actions_applicant_compose,
    actions_applicant_decisions,
    actions_email,
    actions_openings,
    actions_executive,
    actions_items,
    providers_applicants,
    providers_mail,
    providers_orchestrator,
    registry,
)

_initialized = False


def default_registry() -> registry.Registry:
    """Return the global REGISTRY after registering default providers and actions.

    Idempotent: calling this multiple times registers each provider and action
    only once.
    """
    global _initialized

    if not _initialized:
        # Register providers
        registry.register_provider("applicants", providers_applicants.applicant_items)
        registry.register_provider("orchestrator", providers_orchestrator.orchestrator_items)
        registry.register_provider("mail", providers_mail.mail_items)
        registry.register_provider("counties", providers_applicants.county_items)

        # Register actions
        actions_applicant_compose.register(registry.REGISTRY)
        actions_applicant_decisions.register(registry.REGISTRY)
        actions_openings.register(registry.REGISTRY)
        actions_email.register(registry.REGISTRY)
        actions_executive.register(registry.REGISTRY)
        actions_items.register(registry.REGISTRY)

        _initialized = True

    return registry.REGISTRY
