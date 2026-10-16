"""Default registry initialization for the Executive window."""
from __future__ import annotations

from . import (
    actions_applicant_compose,
    actions_applicant_decisions,
    actions_brain_dump,
    actions_candidates,
    actions_coding,
    actions_computer,
    actions_documents,
    actions_email,
    actions_knowledge_gaps,
    actions_projects,
    actions_openings,
    actions_executive,
    actions_items,
    actions_mail_organize,
    providers_applicants,
    providers_brain_dump,
    providers_candidates,
    providers_documents,
    providers_intake,
    providers_knowledge_gaps,
    providers_mail,
    providers_orchestrator,
    providers_projects,
    registry,
)
from ..event_bus import EventBus, DEFAULT_DIR

# Optional providers: a checkout without them still starts the window.
try:
    from . import providers_browser_routines
except ImportError:
    providers_browser_routines = None
try:
    from . import providers_phone
except ImportError:
    providers_phone = None

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
        registry.register_provider("brain_dump", providers_brain_dump.brain_dump_items)
        registry.register_provider("knowledge_gaps", providers_knowledge_gaps.knowledge_gap_items)
        registry.register_provider("memory_candidates", providers_candidates.candidate_items)
        registry.register_provider("documents", providers_documents.document_items)
        if providers_browser_routines is not None:
            registry.register_provider("browser_routines", providers_browser_routines.browser_routine_items)
        if providers_phone is not None:
            registry.register_provider("phone", providers_phone.phone_items)
        registry.register_provider("intake", providers_intake.intake_items)

        # Register actions
        actions_applicant_compose.register(registry.REGISTRY)
        actions_applicant_decisions.register(registry.REGISTRY)
        actions_openings.register(registry.REGISTRY)
        actions_email.register(registry.REGISTRY)
        actions_executive.register(registry.REGISTRY)
        actions_items.register(registry.REGISTRY)
        actions_mail_organize.register(registry.REGISTRY)
        actions_brain_dump.register(registry.REGISTRY)
        actions_knowledge_gaps.register(registry.REGISTRY)
        actions_candidates.register(registry.REGISTRY)
        actions_projects.register(registry.REGISTRY)
        actions_documents.register(registry.REGISTRY)
        actions_coding.register(registry.REGISTRY)
        actions_computer.register(registry.REGISTRY)
        if providers_browser_routines is not None:
            providers_browser_routines.register(registry.REGISTRY)
        if providers_phone is not None:
            providers_phone.register(registry.REGISTRY)

        # Attach the shared local Event Bus
        registry.REGISTRY.attach_event_bus(EventBus(DEFAULT_DIR))

        _initialized = True

    return registry.REGISTRY
