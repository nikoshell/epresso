"""Core BM-25 search index — built and scored at build time, rendered client-side.

Replaces lunr: a Python builder turns each page into search **units** (split by
headings, each with a URL anchor), computes the BM-25 score for every term/doc
pair at build time, and emits a ready-to-merge index. A small vanilla JS client
merges those precomputed per-term scores and adds one client-side signal BM-25
can't express — a boost when the literal typed phrase (not just its words) is
found in a unit — no search library and no BM-25 math in the browser.
"""

from __future__ import annotations

import json
import math
import re
from html import unescape as _unescape
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
    # The source is HTML: entities like "&amp;" must decode to "&" here, or the
    # client's esc() will double-escape them ("&amp;amp;") when it re-renders.
    text = _unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def page_title(html: str) -> str:
    # The tag may carry attributes (scoped components stamp data-epresso-* onto
    # every element, <title> included).
    m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.DOTALL)
    return _unescape(m.group(1).strip()) if m else ""


def split_sections(html: str, url: str) -> list[dict[str, str]]:
    """Split a rendered page's main content into search units at headings.

    Each unit carries ``url``, ``anchor`` (heading slug, '' for the page lead),
    ``title`` (the page's ``<h1>``, or ``<title>`` when it has none), ``crumb``
    (ancestor breadcrumb labels, '' at the root — the current page isn't
    repeated, since it's already ``title``), ``section`` (heading text) and
    ``text`` (plain text) used for BM-25 scoring and client-side snippet
    generation.
    """
    m = re.search(r"<main[^>]*>(.*?)</main>", html, flags=re.DOTALL | re.IGNORECASE)
    main = m.group(1) if m else html
    # Drop the decorative heading-anchor (#) links so section/text has no stray '#'
    main = re.sub(r'<a class="heading-anchor".*?</a>', "", main, flags=re.DOTALL | re.IGNORECASE)

    # Breadcrumbs: kept as page-location metadata (``crumb``, shown under a
    # search result's title) but dropped from the body — chrome, not content
    # worth searching. The current-page crumb is dropped too, since it only
    # repeats the title.
    crumb = ""
    bc = re.search(r'<nav[^>]*\bclass="breadcrumbs"[^>]*>(.*?)</nav>', main, flags=re.DOTALL | re.IGNORECASE)
    if bc:
        _CRUMB_CUR = r'<span[^>]*\bclass="crumb-cur"[^>]*>.*?</span>'
        _CRUMB_SEP = r'<span[^>]*\bclass="crumb-sep"[^>]*>.*?</span>'
        bc_html = re.sub(_CRUMB_CUR, "", bc.group(1), flags=re.DOTALL | re.IGNORECASE)
        bc_html = re.sub(_CRUMB_SEP, " / ", bc_html, flags=re.DOTALL | re.IGNORECASE)
        crumb = re.sub(r"\s*/\s*$", "", _strip_tags(bc_html))
    # Drop breadcrumbs and the prev/next pager: navigation chrome, not content
    # worth searching or showing in a snippet — and if left in, every page's
    # text ends with its *neighbours'* titles, skewing which page ranks first.
    main = re.sub(r'<nav[^>]*\bclass="breadcrumbs"[^>]*>.*?</nav>', "", main, flags=re.DOTALL | re.IGNORECASE)
    main = re.sub(r'<nav[^>]*\bclass="pager"[^>]*>.*?</nav>', "", main, flags=re.DOTALL | re.IGNORECASE)

    # Title: the page's own <h1> reads better than <title>, which carries the
    # site-name suffix themes append. Fall back to <title> when there is none.
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", main, flags=re.DOTALL | re.IGNORECASE)
    title = _strip_tags(h1.group(1)) if h1 else ""
    if not title:
        title = page_title(html)
    # It's already the title — drop it from the body text so a snippet never
    # repeats it (and it doesn't crowd out a real content match). Must happen
    # before finding `heads` below, so their offsets land in the final string.
    if h1:
        main = main[: h1.start()] + main[h1.end() :]

    heads = list(re.finditer(r"<h([1-6])\s+id=\"([^\"]+)\"[^>]*>(.*?)</h\1>", main, flags=re.DOTALL))

    if not heads:
        text = _strip_tags(main)
        return [{"url": url, "anchor": "", "title": title, "crumb": crumb, "section": "", "text": text}] if text else []

    units: list[dict[str, str]] = []
    pre = _strip_tags(main[: heads[0].start()])
    if pre:
        units.append({"url": url, "anchor": "", "title": title, "crumb": crumb, "section": "", "text": pre})
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(main)
        seg = main[h.start() : end]
        section = _strip_tags(h.group(3))
        text = _strip_tags(seg)
        units.append(
            {"url": url, "anchor": h.group(2), "title": title, "crumb": crumb, "section": section, "text": text}
        )
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
