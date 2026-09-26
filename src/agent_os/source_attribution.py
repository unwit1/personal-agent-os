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
SUBJECT_STATES = {"user", "user_confirmed", "third_party", "organization", "mixed", "unknown"}
DIRECT_PROFILE_SUBJECTS = {"user", "user_confirmed"}


def validate_source_actor(value: str | None) -> str | None:
    if value is None:
        return None
    actor = str(value).strip()
    if actor not in ACTOR_STATES:
        raise ValueError(f"unsupported source_actor: {actor}")
    return actor


def validate_subject_relation(value: str | None) -> str | None:
    if value is None:
        return None
    subject = str(value).strip()
    if subject not in SUBJECT_STATES:
        raise ValueError(f"unsupported subject_relation: {subject}")
    return subject


def profile_promotion_allowed(
    source_actor: str | None,
    *,
    subject_relation: str | None = None,
    explicitly_confirmed: bool = False,
    require_subject: bool = False,
) -> tuple[bool, str]:
    """Return whether evidence may directly enter personal canonical state.

    Authorship and subject identity are independent. A user-authored message
    about an applicant, coworker or organization is not evidence about the
    user's biography.
    """
    actor = validate_source_actor(source_actor)
    subject = validate_subject_relation(subject_relation)
    if explicitly_confirmed:
        return True, "explicit_user_confirmation"
    if actor is None:
        if require_subject:
            return False, "profile_candidate_missing_actor"
        return True, "legacy_actor_unspecified"
    if actor not in DIRECT_PROFILE_ACTORS:
        return False, f"actor_requires_reconciliation:{actor}"
    if require_subject:
        if subject is None:
            return False, "profile_candidate_missing_subject"
        if subject not in DIRECT_PROFILE_SUBJECTS:
            return False, f"subject_requires_reconciliation:{subject}"
    return True, "direct_user_actor_and_subject" if require_subject else "direct_user_actor"


def attribution_summary(record: dict[str, Any]) -> dict[str, Any]:
    actor = validate_source_actor(record.get("source_actor"))
    allowed, reason = profile_promotion_allowed(actor, subject_relation=record.get("subject_relation"), explicitly_confirmed=bool(record.get("user_confirmed")), require_subject=bool(record.get("require_subject")))
    return {"source_actor": actor, "subject_relation": record.get("subject_relation"), "promotion_allowed": allowed, "reason": reason}
