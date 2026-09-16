"""Docs theme search overlay: a literal typed phrase should outrank the same
words scattered independently (plain BM-25 can't tell those apart)."""

from pathlib import Path

_SRC = (
    Path(__file__).resolve().parents[2]
    / "themes"
    / "docs"
    / "components"
    / "patterns"
    / "SearchOverlay.ep"
).read_text(encoding="utf-8")


def test_phrase_boost_wired():
    assert "var PHRASE_BOOST = 1000;" in _SRC
    assert "if (toks.length > 1) {" in _SRC
    assert 'hay.indexOf(phrase) !== -1' in _SRC
    assert "scores[i] += PHRASE_BOOST;" in _SRC
    # scoped to the units already surfaced by token matching, not every unit
    assert "Object.keys(scores).forEach(" in _SRC
    # single-word queries are untouched: bag-of-words already handles them
    assert "toks.length > 1" in _SRC


def test_title_highlighting_and_breadcrumb_line_wired():
    assert "function highlightAll(text, term) {" in _SRC
    assert 'esc(title) + "</span>"' not in _SRC  # title goes through highlightAll now
    assert 'highlightAll(title, term) + "</span>"' in _SRC
    # crumb › section share one dimmed line; › only appears between two present parts
    assert 'crumbParts.join(\' <span class="sr-sep">&gt;</span> \')' in _SRC
    assert "if (u.crumb) crumbParts.push(esc(u.crumb));" in _SRC
    assert '.sr-crumb' in _SRC and '.sr-section' in _SRC and '.sr-sep' in _SRC
