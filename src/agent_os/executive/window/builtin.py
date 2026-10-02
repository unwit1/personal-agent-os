"""Default registry initialization for the Executive window."""
from __future__ import annotations

from . import (
    actions_email,
    actions_executive,
    actions_items,
    actions_mail_organize,
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
        registry.register_provider("mail_cleanup", actions_mail_organize.mail_cleanup_items)

        # Register actions
        actions_email.register(registry.REGISTRY)
        actions_executive.register(registry.REGISTRY)
        actions_items.register(registry.REGISTRY)
        actions_mail_organize.register(registry.REGISTRY)

        _initialized = True

    return registry.REGISTRY
