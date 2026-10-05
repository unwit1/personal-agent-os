"""Default registry initialization for the Executive window."""
from __future__ import annotations

from . import (
    actions_applicant_compose,
    actions_applicant_decisions,
    actions_email,
    actions_openings,
    actions_executive,
    actions_items,
    actions_mail_organize,
    providers_applicants,
    providers_mail,
    providers_orchestrator,
    providers_projects,
    registry,
)
from ..event_bus import EventBus, DEFAULT_DIR

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
        registry.register_provider("mail_cleanup", actions_mail_organize.mail_cleanup_items)
        registry.register_provider("projects", providers_projects.project_items)

        # Register actions
        actions_applicant_compose.register(registry.REGISTRY)
        actions_applicant_decisions.register(registry.REGISTRY)
        actions_openings.register(registry.REGISTRY)
        actions_email.register(registry.REGISTRY)
        actions_executive.register(registry.REGISTRY)
        actions_items.register(registry.REGISTRY)
        actions_mail_organize.register(registry.REGISTRY)

        # Attach the shared local Event Bus
        registry.REGISTRY.attach_event_bus(EventBus(DEFAULT_DIR))

        _initialized = True

    return registry.REGISTRY
