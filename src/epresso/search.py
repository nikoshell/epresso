"""Core BM-25 search index — built and scored at build time, rendered client-side.

Replaces lunr: a Python builder turns each page into search **units** (split by
headings, each with a URL anchor), computes the BM-25 score for every term/doc
pair at build time, and emits a ready-to-merge index. A small vanilla JS client
only merges precomputed scores — no search library or scoring math in the browser.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any

# BM-25 parameters (standard defaults; pagefind uses the same family).
K1 = 1.2
B = 0.75

_TOKEN_RE = re.compile(r"[^\W_]+")


def tokenize(text: str) -> list[str]:
    """Lowercase + split into word tokens (unicode letters/digits)."""
    return _TOKEN_RE.findall((text or "").lower())


def _strip_tags(html: str) -> str:
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def page_title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, flags=re.DOTALL)
    return m.group(1).strip() if m else ""


def split_sections(html: str, url: str) -> list[dict[str, str]]:
    """Split a rendered page's main content into search units at headings.

    Each unit carries ``url``, ``anchor`` (heading slug, '' for the page lead),
    ``title`` (page title), ``section`` (heading text) and ``text`` (plain text)
    used for BM-25 scoring and client-side snippet generation.
    """
    m = re.search(r"<main[^>]*>(.*?)</main>", html, flags=re.DOTALL | re.IGNORECASE)
    main = m.group(1) if m else html
    # Drop the decorative heading-anchor (#) links so section/text has no stray '#'
    main = re.sub(r'<a class="heading-anchor".*?</a>', "", main, flags=re.DOTALL | re.IGNORECASE)

    heads = list(re.finditer(r"<h([1-6])\s+id=\"([^\"]+)\"[^>]*>(.*?)</h\1>", main, flags=re.DOTALL))
    title = page_title(html)

    if not heads:
        text = _strip_tags(main)
        return [{"url": url, "anchor": "", "title": title, "section": "", "text": text}] if text else []

    units: list[dict[str, str]] = []
    pre = _strip_tags(main[: heads[0].start()])
    if pre:
        units.append({"url": url, "anchor": "", "title": title, "section": "", "text": pre})
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(main)
        seg = main[h.start() : end]
        section = _strip_tags(h.group(3))
        text = _strip_tags(seg)
        units.append({"url": url, "anchor": h.group(2), "title": title, "section": section, "text": text})
    return units


def build_index(units: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a BM-25 index over search units, scores precomputed at build time.

    Returns ``{version, units, index}`` where ``index`` is ``term -> [[unitIdx, score], …]``
    sorted by score descending. The client only merges these precomputed scores.
    """
    doc_tokens: list[list[str]] = []
    for u in units:
        searchable = " ".join([u.get("title", ""), u.get("section", ""), u.get("text", "")])
        toks = tokenize(searchable)
        doc_tokens.append(toks)
        u["len"] = len(toks)

    n = max(len(doc_tokens), 1)
    avgdl = sum(len(t) for t in doc_tokens) / n

    raw: dict[str, list[list[int]]] = {}
    for i, toks in enumerate(doc_tokens):
        freq: dict[str, int] = {}
        for t in toks:
            freq[t] = freq.get(t, 0) + 1
        for term, count in freq.items():
            raw.setdefault(term, []).append([i, count])

    index: dict[str, list[list]] = {}
    for term, posts in raw.items():
        idf = math.log(1 + (n - len(posts) + 0.5) / (len(posts) + 0.5))
        scored = []
        for i, tf in posts:
            dl = len(doc_tokens[i])
            denom = tf + K1 * (1 - B + B * dl / avgdl)
            score = idf * (tf * (K1 + 1)) / denom
            scored.append([i, round(score, 4)])
        scored.sort(key=lambda x: x[1], reverse=True)
        index[term] = scored

    return {
        "version": 2,
        "units": units,
        "index": index,
    }


def serialize(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)
