"""RenderSession emits bundles through esbuild with minification.

Component `<script>` blocks used to be bundled without `--minify` while the
`[assets] js` path minified; this pins both paths to minify.
"""

from pathlib import Path

from epresso import render as render_mod
from epresso.config import Config
from epresso.css import CSSProcessor
from epresso.render import RenderSession


def _fake_bundle(calls):
    def fake(sources, **kwargs):
        calls.append(kwargs)
        Path(kwargs["outfile"]).write_text("min()")
        return "ok", ""

    return fake


def test_combined_script_bundle_is_minified(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(render_mod, "bundle_js", _fake_bundle(calls))
    session = RenderSession()
    session.add_script("const a = 1;")
    session.write_combined_bundles(tmp_path / "dist", tmp_path / "cache")
    assert calls and calls[0].get("minify") is True


def test_dev_page_scripts_are_minified(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(render_mod, "bundle_js", _fake_bundle(calls))
    session = RenderSession()
    session.add_script("const a = 1;")
    session.write_page_scripts(tmp_path / "dist", tmp_path / "cache")
    assert calls and calls[0].get("minify") is True


def test_css_processor_reports_when_it_does_not_minify(tmp_path):
    # An empty project has no postcss/tailwind config, so epresso minifies the output.
    assert CSSProcessor(Config(root=tmp_path)).minifies is False
