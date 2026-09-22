"""Selective retrieval of durable personal profile context.

The profile is durable, Git-reviewable state about the user: stable working
preferences and long-lived personal/work context. It is useful precisely
because it is always available -- and useless if answering "fix a scanner bug"
drags in meal planning and leisure interests.

So the profile is never injected whole. It is flattened into individually
addressable facts carrying domain, provenance, confidence, sensitivity and
recency, and only the slice a task actually touches is compiled in, inside an
explicit budget, with diagnostics explaining why each fact was chosen.

Three rules shape everything here:

- relevance is earned, not assumed: a fact enters a packet only above a
  relevance floor, so a task with no personal dimension gets no profile at all;
- provenance survives: an explicit user statement is distinguishable from
  something merely derived from a scan, and the stronger record wins a
  duplicate;
- privacy is enforced at retrieval, not at authorship: anything that trips the
  privacy gate is dropped from the packet regardless of what is on disk.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable, Iterable

from .ingestion import IngestionLedger, stable_item_id, stable_stage_id, stable_work_id
from .paths import ROOT
from .privacy import privacy_findings
from .storage import load_json, write_json


PREFERENCES_PATH = ROOT / "profile" / "preferences.json"
USER_CONTEXT_PATH = ROOT / "profile" / "user-context.json"

# `profile/drive-derived-context.json` is deliberately absent. It is a large
# derived index, not durable curated context, and loading it would reintroduce
# exactly the bulk injection this module exists to prevent.
CANONICAL_SOURCES = (PREFERENCES_PATH, USER_CONTEXT_PATH)
PROFILE_LOCAL_DIR = ROOT / ".agent-local" / "profile"
PROFILE_LEDGER_PATH = PROFILE_LOCAL_DIR / "ingestion.json"
PROFILE_CACHE_PATH = PROFILE_LOCAL_DIR / "facts.json"
PROFILE_CACHE_SCHEMA = "personal-agent/profile-index-cache/v1"
PROFILE_PROCESSOR_VERSION = "profile-index@1"

# Sections that describe the privacy regime itself, or that exist only as
# bookkeeping, are never retrievable context.
STRUCTURAL_KEYS = {"schema_version", "updated_at", "provenance", "context_indexes", "purpose"}
RESTRICTED_DOMAINS = {"privacy"}

# Confidence ranks a record's standing. An explicit statement outranks a seed,
# which outranks something inferred from a scan.
CONFIDENCE_ORDER = ("derived", "seeded", "stated")

# Domain vocabulary keeps retrieval cheap and deterministic: a task mentioning
# dinner should reach household planning without a model deciding that it does.
DOMAIN_TERMS: dict[str, tuple[str, ...]] = {
    "preferences": ("preference", "behaviour", "behavior", "workflow", "agent os", "policy", "convention", "default"),
    "goals": ("goal", "objective", "ambition", "plan", "roadmap"),
    "assistance_priorities": ("priority", "prioritise", "prioritize", "assistance", "help", "focus"),
    "work_context": (
        "work", "job", "hr", "employer", "role", "responsibility", "automation", "employee",
        "scanner", "scanning", "ocr", "personnel", "payroll", "applicant", "onboarding", "timesheet",
    ),
    "current_projects_and_interests": ("project", "interest", "building", "side project"),
    "information_sources_to_eventually_integrate": ("integration", "source", "connector", "ingest", "feed"),
    "behavioral_workflow_notes": ("commitment", "continuity", "proactivity", "resume", "follow up"),
    "household_planning": ("household", "meal", "meals", "dinner", "grocery", "groceries", "cooking", "housing", "rent", "home"),
    "financial_assistant_goals": ("finance", "financial", "money", "budget", "spending", "savings", "cost"),
    "leisure_interests": ("leisure", "hobby", "hobbies", "game", "gaming", "reading", "music", "film"),
    "research_and_learning_context": ("research", "learning", "study", "academic", "course"),
    "digital_usage_observations": ("email", "gmail", "spreadsheet", "ebook", "browser", "app usage"),
}

_TOKEN = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "when", "what",
    "how", "should", "would", "could", "does", "are", "was", "were", "have",
    "has", "not", "its", "their", "there", "then", "than", "about",
}


def _tokens(value: str) -> set[str]:
    return {token for token in _TOKEN.findall(value.casefold()) if len(token) > 3 and token not in _STOPWORDS}


def _normalize(value: str) -> str:
    return " ".join(_TOKEN.findall(value.casefold()))


def _confidence_of(statuses: Iterable[str]) -> str:
    """Rank a source's provenance statuses into one confidence label."""
    best = "derived"
    for status in statuses:
        folded = str(status).casefold()
        if "user_stated" in folded or folded == "stated":
            return "stated"
        if "seed" in folded:
            best = "seeded"
    return best


def _statement(path: str, value: Any) -> str | None:
    """Render one leaf as a readable statement, or skip it when it says nothing."""
    label = path.split(".")[-1].replace("_", " ")
    if isinstance(value, bool):
        # A false flag is a real preference, but reads as noise unless labelled.
        return f"{label}: {'yes' if value else 'no'}"
    if isinstance(value, (int, float)):
        return f"{label}: {value}"
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        return text if len(text) > len(label) + 8 else f"{label}: {text}"
    return None


def _walk(node: Any, source: str, domain: str, path: str, facts: list[dict[str, Any]]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in STRUCTURAL_KEYS:
                continue
            _walk(value, source, domain, f"{path}.{key}" if path else str(key), facts)
        return
    if isinstance(node, list):
        for index, value in enumerate(node):
            if isinstance(value, (dict, list)):
                _walk(value, source, domain, f"{path}[{index}]", facts)
            else:
                statement = _statement(path, value)
                if statement:
                    facts.append({"source": source, "domain": domain, "path": f"{path}[{index}]", "statement": statement})
        return
    statement = _statement(path, node)
    if statement:
        facts.append({"source": source, "domain": domain, "path": path, "statement": statement})


def _fact_id(source: str, path: str) -> str:
    return "PF-" + hashlib.sha256(f"{source}\0{path}".encode("utf-8")).hexdigest()[:12]


def _facts_from_data(path: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten one canonical source into addressable facts."""
    source = path.name
    updated_at = str(data.get("updated_at", ""))
    confidence = _confidence_of(item.get("status", "") for item in data.get("provenance", []) if isinstance(item, dict))
    provenance = [
        str(item.get("source", "")) for item in data.get("provenance", []) if isinstance(item, dict) and item.get("source")
    ]
    collected: list[dict[str, Any]] = []
    if source == PREFERENCES_PATH.name:
        _walk(data.get("preferences", {}), source, "preferences", "", collected)
    else:
        for key, value in data.items():
            if key in STRUCTURAL_KEYS:
                continue
            _walk(value, source, str(key), str(key), collected)
    for fact in collected:
        sensitive = fact["domain"] in RESTRICTED_DOMAINS or fact["path"].split(".")[0] in RESTRICTED_DOMAINS
        findings = privacy_findings(fact["statement"])
        fact.update(
            {
                "id": _fact_id(source, fact["path"]),
                "updated_at": updated_at,
                "confidence": confidence,
                "provenance": provenance,
                "sensitivity": "restricted" if (sensitive or findings) else "personal",
                "privacy_findings": findings,
            }
        )
    return collected


def _load_fact_cache(path: Path) -> dict[str, dict[str, Any]]:
    try:
        state = load_json(path)
    except (OSError, ValueError):
        return {}
    if not isinstance(state, dict) or state.get("schema") != PROFILE_CACHE_SCHEMA:
        return {}
    sources = state.get("sources")
    return dict(sources) if isinstance(sources, dict) else {}


def index_facts_incremental(
    sources: Iterable[Path] = CANONICAL_SOURCES,
    *,
    ledger_path: Path | None = None,
    cache_path: Path | None = None,
    processor_version: str = PROFILE_PROCESSOR_VERSION,
    before_parse: Callable[[Path], None] | None = None,
) -> dict[str, Any]:
    """Index canonical profile sources through a restart-safe local ledger.

    The ledger records only source names, hashes, state and checkpoints. The
    derived fact cache stays in the gitignored local directory (or the caller's
    fixture path), so a completed source can be reused without reparsing while
    changed content is deterministically requeued.
    """
    source_paths = tuple(Path(path) for path in sources)
    target_ledger = Path(ledger_path or PROFILE_LEDGER_PATH)
    target_cache = Path(cache_path or PROFILE_CACHE_PATH)
    ledger = IngestionLedger(
        target_ledger,
        source="profile-source",
        work_id=stable_work_id("profile-index", "canonical-sources"),
        stage_id=stable_stage_id(stable_work_id("profile-index", "canonical-sources"), "facts"),
        processor_version=processor_version,
    )
    cached_sources = _load_fact_cache(target_cache)
    facts: list[dict[str, Any]] = []
    present: set[str] = set()
    stats = {
        "checked": 0,
        "queued": 0,
        "reprocessed": 0,
        "resumed": 0,
        "skipped": 0,
        "repaired": 0,
        "errors": 0,
        "cache_errors": 0,
    }

    for path in source_paths:
        if not path.exists():
            continue
        stats["checked"] += 1
        source_key = path.name
        present.add(source_key)
        raw = path.read_bytes()
        queued = ledger.enqueue(source_key, content=raw, processor_version=processor_version)
        item_id = str(queued["item_id"])
        item = ledger.get(item_id)
        cached = cached_sources.get(source_key)
        if (
            queued["action"] == "duplicate"
            and queued["status"] == "processed"
            and isinstance(cached, dict)
            and cached.get("fingerprint") == item.get("fingerprint")
            and isinstance(cached.get("facts"), list)
        ):
            facts.extend(cached["facts"])
            stats["skipped"] += 1
            ledger.checkpoint(source_key, **stats)
            continue

        if queued["action"] == "queued":
            stats["queued"] += 1
        elif queued["action"] == "requeued":
            stats["reprocessed"] += 1

        claimed = ledger.claim(1)
        if claimed:
            claimed_item = claimed[0]
            if claimed_item["item_id"] != item_id:
                raise RuntimeError(f"profile ledger claimed an unexpected item: {claimed_item['item_id']}")
            if int(claimed_item.get("attempts", 0)) > 1:
                stats["resumed"] += 1
        elif queued["action"] == "duplicate":
            # A completed ledger item with a missing local cache is a repair;
            # its source is still safe to parse without changing ledger state.
            stats["repaired"] += 1
        else:
            continue

        try:
            if before_parse is not None:
                before_parse(path)
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("profile source must contain a JSON object")
            source_facts = _facts_from_data(path, data)
            cached_sources[source_key] = {"fingerprint": item["fingerprint"], "facts": source_facts}
            try:
                write_json(target_cache, {"schema": PROFILE_CACHE_SCHEMA, "sources": cached_sources})
            except OSError:
                stats["cache_errors"] += 1
            if claimed:
                ledger.complete(item_id, output_refs=(f"profile-cache:{source_key}",))
            facts.extend(source_facts)
            ledger.checkpoint(source_key, **stats)
        except (OSError, ValueError, UnicodeError) as exc:
            stats["errors"] += 1
            if claimed:
                ledger.fail(item_id, str(exc), retryable=True)
            ledger.checkpoint(source_key, **stats)

    stale = set(cached_sources) - present
    for source_key in stale:
        cached_sources.pop(source_key, None)
    if stale:
        try:
            write_json(target_cache, {"schema": PROFILE_CACHE_SCHEMA, "sources": cached_sources})
        except OSError:
            stats["cache_errors"] += 1
    stats["facts"] = len(facts)
    return {"facts": facts, "stats": stats, "checkpoint": ledger.status()["checkpoint"]}


def index_facts() -> list[dict[str, Any]]:
    """Flatten the canonical profile sources into addressable facts.

    Deterministic: the same files always produce the same facts in the same
    order, so retrieval is testable without a model in the loop.
    """
    return list(index_facts_incremental()["facts"])


def retrievable_facts() -> list[dict[str, Any]]:
    """Facts that may ever enter a compiled packet.

    Privacy is enforced here rather than at the call site, so no caller can
    reach restricted material by forgetting to filter.
    """
    return [fact for fact in index_facts() if fact["sensitivity"] != "restricted"]


def _domain_hits(task_tokens: set[str], normalized_task: str, domain: str) -> int:
    padded = f" {normalized_task} "
    hits = 0
    for term in DOMAIN_TERMS.get(domain, ()):
        if " " in term or len(term) <= 3:
            # Short and multi-word terms are filtered out of the token set, so
            # they are matched on word boundaries in the normalized task.
            if f" {term} " in padded:
                hits += 1
        elif term in task_tokens:
            hits += 1
    return hits


def score_fact(task: str, fact: dict[str, Any]) -> dict[str, Any]:
    """Score one fact against a task and explain the score.

    The explanation is the diagnostic surface: it shows which words earned the
    match, never a hidden rationale.
    """
    task_tokens = _tokens(task)
    normalized_task = _normalize(task)
    statement_tokens = _tokens(fact["statement"]) | _tokens(fact["path"].replace(".", " ").replace("_", " "))
    overlap = sorted(task_tokens & statement_tokens)
    hits = _domain_hits(task_tokens, normalized_task, fact["domain"])
    score = 3 * len(overlap) + 2 * hits
    # One shared generic word ("variable", "plan") routes coding questions into
    # whichever personal fact happens to use it. Relevance needs either domain
    # vocabulary or more than one term in common.
    distinctive = hits >= 1 or len(overlap) >= 2
    reasons = []
    if overlap:
        reasons.append("matched terms: " + ", ".join(overlap[:5]))
    if hits:
        reasons.append(f"domain vocabulary: {fact['domain']}")
    return {
        "score": score,
        "matched_terms": overlap,
        "domain_hits": hits,
        "distinctive": distinctive,
        "why": "; ".join(reasons),
    }


def _descending(value: str) -> tuple[int, ...]:
    """Sort a YYYY-MM-DD string newest-first under an ascending comparison."""
    return tuple(-int(part) for part in _TOKEN.findall(value or "") if part.isdigit())


def _dedupe(scored: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Collapse overlapping facts, preferring the stronger, newer record.

    Two sources can say the same thing with different standing. The explicit,
    newer statement should win, and the loser should be reported rather than
    silently vanishing.
    """
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    order = sorted(
        scored,
        key=lambda item: (
            -item["score"],
            -CONFIDENCE_ORDER.index(item["fact"]["confidence"]),
            _descending(item["fact"]["updated_at"]),
            item["fact"]["id"],
        ),
    )
    for candidate in order:
        text = _normalize(candidate["fact"]["statement"])
        superseded_by = None
        for existing in kept:
            other = _normalize(existing["fact"]["statement"])
            if text == other or text in other or other in text:
                superseded_by = existing["fact"]["id"]
                break
        if superseded_by:
            dropped.append({**candidate, "superseded_by": superseded_by})
        else:
            kept.append(candidate)
    return kept, dropped


def compact_profile(
    task: str,
    limit: int = 5,
    minimum_score: int = 3,
    char_budget: int = 900,
) -> dict[str, Any]:
    """Retrieve only the profile slice this task touches, with diagnostics.

    Returns an empty selection rather than a weak one: a task with no personal
    dimension should carry no profile context at all.
    """
    scored = []
    for fact in retrievable_facts():
        assessment = score_fact(task, fact)
        if assessment["score"] >= minimum_score and assessment["distinctive"]:
            scored.append({"fact": fact, **assessment})
    kept, dropped = _dedupe(scored)
    selected: list[dict[str, Any]] = []
    used = 0
    for item in kept:
        fact = item["fact"]
        entry = {
            "id": fact["id"],
            "domain": fact["domain"],
            "statement": fact["statement"],
            "confidence": fact["confidence"],
            "source": fact["source"],
            "updated_at": fact["updated_at"],
            "why": item["why"],
        }
        cost = len(entry["statement"]) + 80
        if len(selected) >= limit or used + cost > char_budget:
            break
        selected.append(entry)
        used += cost
    return {
        "facts": selected,
        "diagnostics": {
            "indexed": len(retrievable_facts()),
            "considered": len(scored),
            "selected": len(selected),
            "deduplicated": len(dropped),
            "minimum_score": minimum_score,
            "limit": limit,
            "char_budget": char_budget,
            "domains": sorted({item["domain"] for item in selected}),
            "full_profile_loaded": False,
        },
    }


def profile_status() -> dict[str, Any]:
    """Describe what is indexed without printing the profile itself."""
    facts = index_facts()
    domains: dict[str, int] = {}
    for fact in facts:
        domains[fact["domain"]] = domains.get(fact["domain"], 0) + 1
    return {
        "sources": [path.name for path in CANONICAL_SOURCES if path.exists()],
        "excluded_sources": ["drive-derived-context.json"],
        "facts": len(facts),
        "retrievable": len(retrievable_facts()),
        "restricted": len([fact for fact in facts if fact["sensitivity"] == "restricted"]),
        "domains": dict(sorted(domains.items())),
    }
