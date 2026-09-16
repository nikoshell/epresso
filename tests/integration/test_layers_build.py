"""A `[layers] use` directory supplies components/layouts to a real build.

The site's own components/layouts are always searched first, so a site file with
a matching basename overrides the layer's.
"""

from __future__ import annotations

from pathlib import Path

from epresso.site import Site

SITE_TOML = '[site]\nname = "Layers"\nurl = "https://example.com"\n\n[layers]\nuse = ["path:./vendor/lib"]\n'
LAYER_CARD = '---\n---\n<style>.card{color:red}</style>\n<div class="card">from layer</div>\n'
LAYER_SHELL = "---\n---\n<section class=\"shell\">{{ content }}</section>\n"
SITE_CARD = '---\n---\n<div class="card site">from site</div>\n'


def _write(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def _project(tmp_path: Path, *, site_component: bool) -> Site:
    files = {
        "site.toml": SITE_TOML,
        "vendor/lib/components/Card.ep": LAYER_CARD,
        "vendor/lib/layouts/Shell.ep": LAYER_SHELL,
        "pages/index.ep": "---\n---\n<Shell><Card /></Shell>\n",
    }
    if site_component:
        files["components/Card.ep"] = SITE_CARD
    _write(tmp_path, files)
    return Site.load(tmp_path)


def test_layer_component_and_layout_render(tmp_path):
    site = _project(tmp_path, site_component=False)
    site.build()
    out = site.config.dir_output()
    html = (out / "index.html").read_text(encoding="utf-8")
    assert "from layer" in html
    assert 'class="shell"' in html
    # the layer component's scoped CSS is emitted like any other component's
    assert list((out / "_scoped").glob("*.css"))


def test_site_component_overrides_layer(tmp_path):
    site = _project(tmp_path, site_component=True)
    site.build()
    html = (site.config.dir_output() / "index.html").read_text(encoding="utf-8")
    assert "from site" in html
    assert "from layer" not in html


def test_resolved_layers_are_exposed_on_the_site(tmp_path):
    site = _project(tmp_path, site_component=False)
    assert [layer.kind for layer in site.layers] == ["path"]
    assert site.layers[0].root == (tmp_path / "vendor" / "lib").resolve()
