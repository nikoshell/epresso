"""Validate that the runnable example plugins in examples/plugins/ keep working.

We import the example modules by file path (no install needed), wire them into a
scratch site, build it, and assert their effects — proving the shipped examples
are correct against the current plugin API.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from epresso.site import Site

EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "plugins"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"_ex_{name}", EXAMPLES / f"{name}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _build_with(*plugins, page="<h1>{{ greeting() }}</h1>"):
    import tempfile

    root = Path(tempfile.mkdtemp())
    (root / "pages").mkdir()
    (root / "pages" / "index.html").write_text(page, encoding="utf-8")
    site = Site.load(root)
    for p in plugins:
        site.plugins.register(p)
    site.build()
    return site, (site.config.dir_output() / "index.html").read_text(encoding="utf-8")


def test_greeter_example_adds_global_and_filter():
    g = _load("greeter")
    plugin = g.greeter(text="hi-there", shout=True)
    site, html = _build_with(plugin, page="<p>{{ greeting() }} / {{ 'x' | shout }}</p>")
    assert "HI-THERE / X" in html


def test_watermark_example_stamps_pre_blocks():
    w = _load("watermark")
    plugin = w.watermark(text="Made by epresso")
    site, html = _build_with(plugin, page="<pre>a\nb</pre>")
    assert html.replace("\n", "").endswith('<span class="epresso-mark">Made by epresso</span></pre>')


def test_watermark_does_not_double_stamp_on_repeat():
    w = _load("watermark")
    plugin = w.watermark()
    site, html = _build_with(plugin, page="<pre>one</pre>\n<pre>two</pre>")
    assert html.count("epresso-mark") == 2
    site.build()  # reload + rebuild must not add more stamps
    html2 = (site.config.dir_output() / "index.html").read_text(encoding="utf-8")
    assert html2.count("epresso-mark") == 2


def test_quotes_example_registers_a_collection():
    q = _load("quotes")
    items = [{"id": "a", "data": {"text": "stay deterministic"}}, {"id": "b", "data": {"text": "go incremental"}}]
    plugin = q.quotes(items)
    site, html = _build_with(
        plugin, page="{% for q in get_collection('quotes') %}{{ q.data.text }};{% endfor %}"
    )
    assert "stay deterministic;go incremental;" in html
