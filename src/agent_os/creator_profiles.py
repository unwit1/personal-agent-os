"""Creator identity profiles for Agent OS.

Following a creator should create one durable, provider-neutral identity profile
that can accumulate accounts, aliases, external links, Discord evidence, watch
targets, and discovery work across sites.

Git stores the compact canonical profile graph. High-frequency observations and
message bodies stay in local stores such as the browser-bridge SQLite database.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse, urlunparse

from .paths import ROOT

CREATOR_DIR = ROOT / "knowledge" / "personal" / "creators"
CREATOR_INDEX = CREATOR_DIR / "index.json"
SCHEMA = "agent-os/creator-profiles/v1"

_CREATOR_SITES = (
    "youtube",
    "nexusmods",
    "github",
    "discord",
    "patreon",
    "reddit",
    "twitch",
    "ko-fi",
    "itch",
    "substack",
    "medium",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_alias(value: str) -> str:
    value = str(value or "").strip().casefold()
    value = value.removeprefix("@")
    return re.sub(r"[^a-z0-9]+", "", value)


def _canonical_url(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return ""
    try:
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            return value
        host = parsed.netloc.casefold()
        if host.startswith("www."):
            host = host[4:]
        path = re.sub(r"/+$", "", parsed.path or "/") or "/"
        return urlunparse((parsed.scheme.casefold(), host, path, "", "", ""))
    except ValueError:
        return value


def _load() -> dict[str, Any]:
    if not CREATOR_INDEX.exists():
        return {"schema_version": SCHEMA, "profiles": []}
    value = json.loads(CREATOR_INDEX.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("creator profile index must contain an object")
    value.setdefault("schema_version", SCHEMA)
    value.setdefault("profiles", [])
    return value


def _save(value: dict[str, Any]) -> None:
    CREATOR_DIR.mkdir(parents=True, exist_ok=True)
    CREATOR_INDEX.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _site_alias_from_url(site: str, url: str) -> str:
    try:
        parsed = urlparse(url)
        path = parsed.path or ""
    except ValueError:
        return ""
    site = str(site or "").casefold()
    patterns = {
        "youtube": (r"^/@([^/]+)", r"^/user/([^/]+)", r"^/c/([^/]+)"),
        "github": (r"^/([^/]+)",),
        "reddit": (r"^/(?:user|u)/([^/]+)",),
        "patreon": (r"^/(?:c/)?([^/]+)",),
        "twitch": (r"^/([^/]+)",),
        "ko-fi": (r"^/([^/]+)",),
    }
    for pattern in patterns.get(site, ()):
        match = re.search(pattern, path, re.I)
        if match:
            return match.group(1)
    return ""


def _extract_aliases(capture: dict[str, Any]) -> list[dict[str, Any]]:
    metadata = dict(capture.get("metadata") or {})
    site = str(capture.get("site") or "").casefold()
    out: list[dict[str, Any]] = []

    def add(value: Any, confidence: str, source: str) -> None:
        text = str(value or "").strip()
        normalized = normalize_alias(text)
        if not text or not normalized:
            return
        if any(item["normalized"] == normalized for item in out):
            return
        out.append({
            "value": text,
            "normalized": normalized,
            "confidence": confidence,
            "source": source,
            "site": site,
        })

    supplied = metadata.get("aliases") or []
    if isinstance(supplied, str):
        supplied = [supplied]
    if isinstance(supplied, list):
        for value in supplied:
            if isinstance(value, dict):
                add(
                    value.get("value") or value.get("alias") or value.get("handle"),
                    str(value.get("confidence") or "high"),
                    str(value.get("source") or "capture_metadata"),
                )
            else:
                add(value, "high", "capture_metadata")

    for key in ("handle", "username", "creator_slug", "route_id", "repository_owner"):
        if metadata.get(key):
            add(metadata[key], "high", f"metadata:{key}")

    alias_from_url = _site_alias_from_url(
        site,
        str(capture.get("canonical_url") or capture.get("url") or ""),
    )
    if alias_from_url:
        add(alias_from_url, "high", "profile_url")

    identity_confidence = str(metadata.get("identity_confidence") or "")
    display_confidence = "low" if identity_confidence == "display-name-only" else "medium"
    add(capture.get("author"), display_confidence, "author")
    add(capture.get("title"), display_confidence, "title")
    return out


def _extract_links(capture: dict[str, Any]) -> list[dict[str, Any]]:
    metadata = dict(capture.get("metadata") or {})
    values: list[Any] = list(metadata.get("profile_links") or [])
    primary = capture.get("canonical_url") or capture.get("url")
    if primary:
        values.insert(0, primary)

    out: list[dict[str, Any]] = []
    for value in values:
        if isinstance(value, dict):
            url = str(value.get("url") or "").strip()
            kind = str(value.get("kind") or "profile")
            label = str(value.get("label") or "")
            confidence = str(value.get("confidence") or "observed")
        else:
            url = str(value or "").strip()
            kind = "profile"
            label = ""
            confidence = "observed"
        canonical = _canonical_url(url)
        if not canonical or any(x["canonical_url"] == canonical for x in out):
            continue
        out.append({
            "url": url,
            "canonical_url": canonical,
            "kind": kind,
            "label": label,
            "confidence": confidence,
            "source_site": str(capture.get("site") or ""),
        })
    return out


def _identity_seed(capture: dict[str, Any]) -> str:
    source_id = str(capture.get("source_id") or "").strip()
    if source_id:
        return source_id
    canonical = _canonical_url(str(capture.get("canonical_url") or capture.get("url") or ""))
    if canonical:
        return canonical
    aliases = _extract_aliases(capture)
    if aliases:
        return "alias:" + aliases[0]["normalized"]
    return "creator:" + str(capture.get("title") or capture.get("author") or "unknown").casefold()


def _find_profile(
    data: dict[str, Any],
    capture: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    source_id = str(capture.get("source_id") or "").strip()
    canonical = _canonical_url(str(capture.get("canonical_url") or capture.get("url") or ""))
    aliases = _extract_aliases(capture)
    high_aliases = {x["normalized"] for x in aliases if x["confidence"] == "high"}

    for profile in data["profiles"]:
        for account in profile.get("accounts") or []:
            if source_id and source_id == str(account.get("source_id") or ""):
                return profile, "source_id"
            if canonical and canonical == str(account.get("canonical_url") or ""):
                return profile, "account_url"
        if canonical:
            for link in profile.get("links") or []:
                if canonical == str(link.get("canonical_url") or ""):
                    return profile, "profile_link"

    if high_aliases:
        matches = []
        for profile in data["profiles"]:
            existing = {
                str(alias.get("normalized") or "")
                for alias in profile.get("aliases") or []
                if str(alias.get("confidence") or "") == "high"
            }
            if high_aliases & existing:
                matches.append(profile)
        if len(matches) == 1:
            return matches[0], "high_confidence_alias"

    return None, None


def _search_queries(display_name: str, aliases: list[dict[str, Any]]) -> list[str]:
    terms: list[str] = []
    if display_name:
        terms.append(display_name)
    terms.extend(
        alias["value"]
        for alias in aliases
        if alias.get("confidence") == "high"
    )
    terms = list(dict.fromkeys(x for x in terms if x))[:5]
    queries: list[str] = []
    for term in terms:
        quoted = f'"{term}"'
        queries.extend([
            f"{quoted} Nexus Mods",
            f"{quoted} GitHub",
            f"{quoted} YouTube",
            f"{quoted} website",
            f"{quoted} Discord",
            f"{quoted} Patreon",
        ])
    return list(dict.fromkeys(queries))[:30]


def _merge_dict_list(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
    key,
) -> list[dict[str, Any]]:
    result = list(existing)
    positions = {key(item): index for index, item in enumerate(result)}
    for item in incoming:
        identity = key(item)
        if not identity:
            continue
        if identity in positions:
            current = dict(result[positions[identity]])
            current.update({k: v for k, v in item.items() if v not in (None, "", [], {})})
            result[positions[identity]] = current
        else:
            positions[identity] = len(result)
            result.append(item)
    return result


def upsert_creator_follow(
    capture: dict[str, Any],
    *,
    watch_id: str | None = None,
    discord_matches: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    metadata = dict(capture.get("metadata") or {})
    target_type = str(metadata.get("follow_target_type") or capture.get("content_type") or "")
    if target_type != "creator":
        raise ValueError("creator profile requires a creator follow target")

    data = _load()
    profile, matched_by = _find_profile(data, capture)
    now = _now()
    aliases = _extract_aliases(capture)
    links = _extract_links(capture)
    source_id = str(capture.get("source_id") or "").strip()
    url = str(capture.get("canonical_url") or capture.get("url") or "").strip()
    site = str(capture.get("site") or "").strip().casefold()
    display_name = str(capture.get("author") or capture.get("title") or "").strip()

    if profile is None:
        seed = _identity_seed(capture)
        profile = {
            "creator_id": "creator-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16],
            "display_name": display_name or source_id or url,
            "status": "followed",
            "aliases": [],
            "accounts": [],
            "links": [],
            "watch_ids": [],
            "search_queries": [],
            "discord_candidates": [],
            "possible_matches": [],
            "discovery": {
                "status": "queued",
                "reason": "new_creator_follow",
                "requested_at": now,
                "last_enriched_at": None,
            },
            "created_at": now,
            "updated_at": now,
        }
        data["profiles"].append(profile)
        matched_by = "new_profile"

    profile["status"] = "followed"
    if display_name and (
        not profile.get("display_name")
        or len(display_name) > len(str(profile.get("display_name") or ""))
    ):
        profile["display_name"] = display_name

    account = {
        "site": site,
        "source_id": source_id,
        "url": url,
        "canonical_url": _canonical_url(url),
        "handle": _site_alias_from_url(site, url),
        "status": "followed",
        "confidence": "confirmed",
        "observed_at": now,
        "provenance": {
            "source": "browser_follow",
            "captured_at": capture.get("captured_at"),
            "discovered_from": metadata.get("discovered_from") or capture.get("url"),
        },
    }
    profile["accounts"] = _merge_dict_list(
        list(profile.get("accounts") or []),
        [account],
        lambda item: str(item.get("source_id") or "") or str(item.get("canonical_url") or ""),
    )
    profile["aliases"] = _merge_dict_list(
        list(profile.get("aliases") or []),
        aliases,
        lambda item: str(item.get("normalized") or ""),
    )
    profile["links"] = _merge_dict_list(
        list(profile.get("links") or []),
        links,
        lambda item: str(item.get("canonical_url") or ""),
    )

    if watch_id:
        profile["watch_ids"] = list(dict.fromkeys(list(profile.get("watch_ids") or []) + [watch_id]))

    queries = _search_queries(str(profile.get("display_name") or ""), list(profile.get("aliases") or []))
    profile["search_queries"] = list(dict.fromkeys(list(profile.get("search_queries") or []) + queries))

    if discord_matches:
        normalized = []
        for match in discord_matches:
            if not isinstance(match, dict):
                continue
            normalized.append({
                "author": str(match.get("author") or ""),
                "normalized": normalize_alias(str(match.get("author") or "")),
                "message_count": int(match.get("message_count") or 0),
                "last_seen": match.get("last_seen"),
                "sample_message_url": match.get("sample_message_url"),
                "confidence": str(match.get("confidence") or "candidate"),
                "status": "candidate",
            })
        profile["discord_candidates"] = _merge_dict_list(
            list(profile.get("discord_candidates") or []),
            normalized,
            lambda item: str(item.get("normalized") or ""),
        )

    profile["discovery"] = dict(profile.get("discovery") or {})
    profile["discovery"].update({
        "status": "queued",
        "reason": "follow_added_or_updated",
        "requested_at": now,
        "desired_sources": [
            "official_website",
            "youtube",
            "nexusmods",
            "github",
            "discord",
            "patreon",
            "reddit",
            "rss_atom",
        ],
    })
    profile["updated_at"] = now
    _save(data)
    return {
        "creator_id": profile["creator_id"],
        "display_name": profile.get("display_name"),
        "matched_by": matched_by,
        "status": profile.get("status"),
        "accounts": profile.get("accounts") or [],
        "aliases": profile.get("aliases") or [],
        "links": profile.get("links") or [],
        "watch_ids": profile.get("watch_ids") or [],
        "search_queries": profile.get("search_queries") or [],
        "discord_candidates": profile.get("discord_candidates") or [],
        "discovery": profile.get("discovery") or {},
    }


def follow_status(target: dict[str, Any]) -> dict[str, Any]:
    capture = {
        "site": target.get("site"),
        "source_id": target.get("source_id"),
        "url": target.get("canonical_url") or target.get("url"),
        "canonical_url": target.get("canonical_url") or target.get("url"),
        "title": target.get("title"),
        "author": target.get("author"),
        "content_type": "follow_target",
        "metadata": dict(target.get("metadata") or {}),
    }
    profile, matched_by = _find_profile(_load(), capture)
    if profile is None or profile.get("status") != "followed":
        return {"followed": False, "matched_by": None, "creator_id": None}
    return {
        "followed": True,
        "matched_by": matched_by,
        "creator_id": profile.get("creator_id"),
        "display_name": profile.get("display_name"),
        "accounts": profile.get("accounts") or [],
        "aliases": profile.get("aliases") or [],
    }


def list_profiles(*, status: str | None = None) -> list[dict[str, Any]]:
    profiles = list(_load()["profiles"])
    if status:
        profiles = [x for x in profiles if x.get("status") == status]
    return sorted(profiles, key=lambda x: str(x.get("display_name") or "").casefold())


def pending_discovery() -> list[dict[str, Any]]:
    return [
        profile
        for profile in list_profiles(status="followed")
        if str((profile.get("discovery") or {}).get("status") or "") in {"queued", "needs_refresh"}
    ]
