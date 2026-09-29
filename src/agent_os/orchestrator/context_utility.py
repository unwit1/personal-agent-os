"""Context-utility telemetry (MIE-0009): did the attached context get used?

When a delegated call attaches known inputs (``delegate --attach``, DEC-0018),
this measures, per attached file, whether the model's answer appears to draw on
it -- a deterministic, approximate signal for trimming context that is paid for
but never referenced. It never calls a model.

The signal is intentionally conservative: a file counts as *referenced* when
its name stem appears in the answer, or when it shares a distinctive token (a
word of length >= ``MIN_TOKEN`` that is rare across the attachment set) with
the answer. Distinctive-token matching avoids crediting a file merely for
common words, but it cannot see paraphrase, so the report is labelled
approximate and used only to flag persistently unreferenced attachments.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from ..paths import ROOT
from .store import orchestrator_home

MIN_TOKEN = 6
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_]{%d,}" % (MIN_TOKEN - 1))
CHARS_PER_TOKEN = 4
BOUNDARY = chr(92) + "b"  # regex word boundary


def _tokens(text: str) -> set[str]:
    return {word.lower() for word in _WORD.findall(text)}


def attachment_utility(answer_text: str, attachments: Iterable[str], cwd: Path | str) -> dict[str, Any]:
    """Per-attachment reference signal for one answer. ``attachments`` are
    repo-relative paths under ``cwd`` (as delegate records them)."""
    root = Path(cwd)
    files = []
    for name in attachments:
        path = root / name
        try:
            files.append((name, path.read_text(encoding="utf-8", errors="replace")))
        except OSError:
            continue
    if not files:
        return {"attachments": 0, "referenced": 0, "utilization": None, "attached_tokens_est": 0, "unreferenced": []}
    # A token is distinctive when it occurs in only one attachment.
    doc_freq: Counter[str] = Counter()
    per_file_tokens = {}
    for name, text in files:
        toks = _tokens(text)
        per_file_tokens[name] = toks
        for token in toks:
            doc_freq[token] += 1
    answer_tokens = _tokens(answer_text)
    referenced, unreferenced = [], []
    for name, text in files:
        stem = Path(name).stem.lower()
        stem_hit = len(stem) >= 3 and re.search(BOUNDARY + re.escape(stem) + BOUNDARY, answer_text.lower()) is not None
        distinctive = {token for token in per_file_tokens[name] if doc_freq[token] == 1}
        hit = stem_hit or bool(distinctive & answer_tokens)
        (referenced if hit else unreferenced).append(name)
    attached_chars = sum(len(text) for _, text in files)
    return {
        "attachments": len(files),
        "referenced": len(referenced),
        "utilization": round(len(referenced) / len(files), 3),
        "attached_tokens_est": attached_chars // CHARS_PER_TOKEN,
        "unreferenced": sorted(unreferenced),
        "method": "approximate: stem or distinctive-token match; misses paraphrase",
    }


def report(home: Path | None = None) -> dict[str, Any]:
    """Aggregate context utility across recorded delegations. Reads each
    delegation's outcome.json under the orchestrator home."""
    root = Path(home or orchestrator_home()) / "delegations"
    calls = 0
    utils: list[float] = []
    unref: Counter[str] = Counter()
    seen: Counter[str] = Counter()
    tokens = 0
    for outcome_path in sorted(root.glob("*/outcome.json")):
        try:
            outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cu = outcome.get("context_utility")
        if not isinstance(cu, dict) or not cu.get("attachments"):
            continue
        calls += 1
        tokens += int(cu.get("attached_tokens_est") or 0)
        if cu.get("utilization") is not None:
            utils.append(cu["utilization"])
        for name in outcome.get("attachments") or []:
            seen[name] += 1
        for name in cu.get("unreferenced") or []:
            unref[name] += 1
    trim = [{"attachment": name, "unreferenced_in": count, "attached_in": seen[name]}
            for name, count in unref.most_common() if seen[name] >= 2 and count == seen[name]]
    return {
        "delegations_with_attachments": calls,
        "mean_utilization": round(sum(utils) / len(utils), 3) if utils else None,
        "attached_tokens_est_total": tokens,
        "always_unreferenced": trim,
        "note": "Approximate reference detection (context_utility.attachment_utility); an always-unreferenced attachment is a trim candidate, not proof of waste.",
    }
