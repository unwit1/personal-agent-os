"""Source-actor attribution and personal-profile promotion gates."""
from __future__ import annotations

from typing import Any

ACTOR_STATES = {
    "user",
    "user_confirmed",
    "other_account_user",
    "third_party",
    "organization_archive",
    "automated",
    "unknown",
}
DIRECT_PROFILE_ACTORS = {"user", "user_confirmed"}


def validate_source_actor(value: str | None) -> str | None:
    if value is None:
        return None
    actor = str(value).strip()
    if actor not in ACTOR_STATES:
        raise ValueError(f"unsupported source_actor: {actor}")
    return actor


def profile_promotion_allowed(source_actor: str | None, *, explicitly_confirmed: bool = False) -> tuple[bool, str]:
    """Return whether evidence may directly enter personal canonical state.

    Legacy candidates with no actor metadata are not retroactively rejected;
    new profile/relationship candidate paths should always provide it.
    """
    actor = validate_source_actor(source_actor)
    if explicitly_confirmed:
        return True, "explicit_user_confirmation"
    if actor is None:
        return True, "legacy_actor_unspecified"
    if actor in DIRECT_PROFILE_ACTORS:
        return True, "direct_user_actor"
    return False, f"actor_requires_reconciliation:{actor}"


def attribution_summary(record: dict[str, Any]) -> dict[str, Any]:
    actor = validate_source_actor(record.get("source_actor"))
    allowed, reason = profile_promotion_allowed(actor, explicitly_confirmed=bool(record.get("user_confirmed")))
    return {"source_actor": actor, "promotion_allowed": allowed, "reason": reason}
