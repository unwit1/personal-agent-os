# Shared document intelligence and local extraction cache

Status: foundation implemented (P0.3, steps 1–3)

## Why this layer exists

Several projects need the same expensive primitives from a page: hash it,
decide whether it is blank, pull out embedded text, and only then pay for OCR.
Repeating that per project — and repeating it again on every development run —
is the single largest avoidable cost in document handling.

This layer owns those primitives and a persistent cache for them. It owns **no
business rules**: form types, employee association, naming, and date semantics
stay in the project that understands them (HR-GUI).

No OCR engine is bundled. Callers pass their own extraction and OCR callables,
so the layer stays provider-neutral and is testable without any engine
installed.

## Three constraints

### The cache is an optimization, never canonical state

Every entry point works with the cache absent, disabled, unwritable, or
corrupt. A corrupt entry, a tampered key, or a stale schema version is treated
as a miss. A cache miss costs time; it never changes an answer. Tests assert
that a disabled cache returns byte-identical results.

### The cache is workstation-local and private

It holds derived text from real work documents. It lives in the gitignored
`.agent-local/document-cache/`, and a cache location inside the tracked part of
the repository is **refused structurally** — not by convention:

```python
DocumentCache(root=ROOT / "forms" / "cache")   # raises CachePrivacyError
```

`agent.py validate` additionally asserts `.agent-local/` is gitignored and that
no cache file is tracked. Only counts and sanitized structure cross the
boundary; `cache_status_safe()` deliberately omits even the absolute path.

### Extraction is cached; interpretation is not

The cache key covers only what determines the extracted bytes:

    file_hash, page_index, dpi, rotation, extractor, ocr_engine, preprocess

Classifier, fingerprint, naming, date and packet logic are **excluded by
construction**, so changing how a page is *interpreted* reuses the OCR rather
than paying for it again. This is the difference between a development loop
measured in seconds and one measured in minutes, and it is exactly what
HR-GUI's own performance plan calls for ("Do NOT make final classification the
primary cache").

A test asserts every name in `INTERPRETATION_COMPONENTS` is absent from the
key, so a future change cannot quietly reintroduce the cost.

## Extraction routing

    cache -> embedded text -> OCR

Embedded text is accepted only when it carries enough real words to be
trusted. A page with a handful of words is usually a scanned image with a stray
text layer, and treating that as sufficient would silently trade accuracy for a
second of runtime. A failing extractor or a failing OCR engine degrades the
page; neither crashes the run.

The route taken is reported per page, so cost can be measured rather than
assumed.

## Template signatures

`structural_fingerprint()` builds a signature from an **allowlisted form
vocabulary**, not from repetition.

This was a correction during implementation. The first version used words that
repeat on the page as "boilerplate" anchors — and a test immediately showed a
person's surname leaking into the signature, because a name recurs naturally in
the name field, on the signature line, and inside an email address. Repetition
within a single page is not evidence of structure.

Building anchors from vocabulary alone fixes the leak by construction *and*
produces a better signature: two copies of the same form filled in by different
people yield the **same** value. That is what template reuse needs, and it is
why a template match can never carry another document's employee-specific
values.

## Commands

```powershell
agent-os document-cache-status
agent-os document-cache-prune --max-bytes 536870912 --max-age-days 90
agent-os document-cache-clear
```

Over MCP: `document.cache_status` — counts only, never contents, never a path.

## Measured behaviour

40 pages, simulated OCR at 20 ms/page, 25% of pages carrying embedded text:

| pass | time | OCR pages | cache hits |
|---|---|---|---|
| 1 — cold cache | 0.65 s | 30 | 0 |
| 2 — warm cache (repeat run) | 0.14 s | 0 | 40 |
| 3 — classifier changed | 0.00 s | 0 | 40 |
| 4 — OCR engine upgraded | 0.67 s | 30 | 0 |

Repeat-run speedup **4.5×**, 78% of the work avoided. Pass 3 is the guarantee
that matters most: an interpretation change costs no OCR at all. Pass 4 shows
the cache correctly invalidating when the extracted bytes really would differ.

The absolute numbers scale with real engine cost; the ratios are the point.

## Scope actually delivered

Of the roadmap's five-step HR-GUI optimization path, this implements steps 1–3:

1. ✅ persistent exact-page cache keyed by content hash
2. ✅ dependency/version-aware invalidation
3. ✅ template-level structural signatures (privacy-safe, person-independent)
4. ⬜ targeted field-zone OCR
5. ⬜ bounded concurrency

Steps 4 and 5 need the real scanner, real documents, and measurement on this
machine. They are recorded as debt rather than guessed at, and the roadmap is
explicit that concurrency comes only after measuring the earlier steps.

HR-GUI is a separate repository and was not modified. Wiring its scanner to
this layer is the next concrete step.
