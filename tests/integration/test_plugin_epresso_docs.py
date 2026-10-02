"""epresso_docs plugin: several [[plugin.epresso_docs.sources]] → one docs collection."""

import shutil
from pathlib import Path

from epresso.site import Site
from epresso.themes import bundled_docs_theme


def test_two_sources_build_into_one_docs_site(tmp_path: Path):
    site_dir = tmp_path / "site"
    shutil.copytree(bundled_docs_theme(), site_dir, ignore=shutil.ignore_patterns("dist", ".cache", "__pycache__"))
    for rel, text in {"main/index.md": "# Home\n\nhi\n", "main/guide.md": "# Guide\n\nx\n", "extra/usage.md": "# Usage\n\ny\n"}.items():
        p = site_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    toml = (site_dir / "site.toml").read_text(encoding="utf-8")
    toml += (
        '\n[[plugin.epresso_docs.sources]]\nsource = "main"\n'
        '\n[[plugin.epresso_docs.sources]]\nsource = "extra"\nprefix = "/plugins/x/"\ntitle = "Plugin X"\n'
    )
    (site_dir / "site.toml").write_text(toml, encoding="utf-8")

    site = Site.load(site_dir)
    ids = {e.id for e in site.get_collection("docs")}
    assert {"", "guide", "plugins/x", "plugins/x/usage"} <= ids
    site.build()
    out = site.config.dir_output()
    page = (out / "plugins" / "x" / "usage" / "index.html").read_text(encoding="utf-8")
    assert "Usage" in page
    # the local source links to its path under the site's repository
    assert "/blob/main/extra/usage.md" in page
    assert (out / "guide" / "index.html").exists()


def test_base_puts_docs_under_a_path_in_a_site_with_its_own_layout(tmp_path: Path):
    files = {
        "site.toml": (
            'plugins = ["epresso_docs"]\n[site]\nname = "Host"\n'
            '[plugin.epresso_docs]\nbase = "/docs/"\n'
            '[[plugin.epresso_docs.sources]]\nsource = "manual"\n'
        ),
        # host files named like the theme's old ones must not leak into docs pages
        "layouts/Base.ep": "<html><head><title>{{ props.title }}</title></head><body class=\"host\"><slot/></body></html>\n",
        "components/Icon.ep": "<i>host icon</i>\n",
        "styles/global.css": "body{background:hotpink}\n",
        "pages/index.ep": "---\n---\n<Base title=\"Home\"><h1>host home</h1></Base>\n",
        "manual/index.md": "# Manual\n\nstart\n",
        "manual/guide.md": "# Guide\n\nsteps\n",
    }
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    site = Site.load(tmp_path)
    site.build()
    out = site.config.dir_output()
    home = (out / "index.html").read_text(encoding="utf-8")
    assert "host home" in home and "docs." not in home  # host page: own layout, no docs CSS
    guide = (out / "docs" / "guide" / "index.html").read_text(encoding="utf-8")
    assert "steps" in guide and 'class="host"' not in guide and "host icon" not in guide
    css = guide.split('rel="stylesheet" href="')[1].split('"')[0]
    assert css.startswith("/assets/docs.") and (out / css.lstrip("/")).is_file()
    assert (out / "docs" / "index.html").is_file()  # the manual's index at the base
    assert "/docs/guide/" in (out / "docs" / "index.html").read_text(encoding="utf-8")


def _site(tmp_path: Path, files: dict[str, str | bytes]) -> Site:
    for rel, data in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode())
    site = Site.load(tmp_path)
    site.build()
    return site


def test_relative_images_in_a_source_are_published_and_resolve(tmp_path: Path):
    site = _site(tmp_path, {
        "site.toml": (
            'plugins = ["epresso_docs"]\n[plugin.epresso_docs]\nbase = "/docs/"\n'
            '[[plugin.epresso_docs.sources]]\nsource = "manual"\nprefix = "/m/"\n'
        ),
        "manual/guide/setup.md": "# Setup\n\n![shot](./img/shot.png)\n",
        "manual/guide/img/shot.png": b"\x89PNG fake",
        "manual/dist/junk.txt": "build output\n",
    })
    out = site.config.dir_output()
    html = (out / "docs" / "m" / "guide" / "setup" / "index.html").read_text(encoding="utf-8")
    import re

    src = re.search(r'<img[^>]*src="([^"]+)"[^>]*alt="shot"|<img[^>]*alt="shot"[^>]*src="([^"]+)"', html)
    src = src.group(1) or src.group(2)
    assert src.startswith("/docs/_docs-assets/0/guide/")
    assert (out / src.lstrip("/")).read_bytes() == b"\x89PNG fake"
    assert not list(out.rglob("junk.txt"))  # build dirs inside a source are not published


def test_base_adopts_the_theme_code_component(tmp_path: Path):
    site = _site(tmp_path, {
        "site.toml": 'plugins = ["epresso_docs"]\n[plugin.epresso_docs]\nbase = "/docs/"\n'
        '[[plugin.epresso_docs.sources]]\nsource = "manual"\n',
        "manual/index.md": "# M\n\n```python\nx = 1\n```\n",
    })
    assert site.config.markdown.code_component == "DocsHighlight"
    assert "DocsHighlight" in site.config.markdown.components


def test_base_keeps_a_host_code_component(tmp_path: Path):
    site = _site(tmp_path, {
        "site.toml": 'plugins = ["epresso_docs"]\n[markdown]\ncode_component = "Mine"\ncomponents = ["Mine"]\n'
        '[plugin.epresso_docs]\nbase = "/docs/"\n[[plugin.epresso_docs.sources]]\nsource = "manual"\n',
        "components/Mine.ep": "<pre>mine</pre>\n",
        "manual/index.md": "# M\n\ntext\n",
    })
    assert site.config.markdown.code_component == "Mine"


def test_theme_is_brand_neutral_and_picks_up_project_branding(tmp_path: Path):
    import re

    plain = _site(tmp_path / "plain", {
        "site.toml": 'plugins = ["epresso_docs"]\n[site]\nname = "Acme"\n[plugin.epresso_docs]\nbase = "/docs/"\n'
        '[[plugin.epresso_docs.sources]]\nsource = "manual"\n',
        "manual/index.md": "# M\n\ntext\n",
    })
    out = plain.config.dir_output()
    page = (out / "docs" / "index.html").read_text(encoding="utf-8")
    assert re.search(r'class="brand-name"[^>]*>Acme<', page) and "epresso.svg" not in page
    assert not (out / "epresso.svg").exists() and not (out / "epresso.png").exists()

    branded = _site(tmp_path / "branded", {
        "site.toml": 'plugins = ["epresso_docs"]\n[plugin.epresso_docs]\nbase = "/docs/"\n'
        '[[plugin.epresso_docs.sources]]\nsource = "manual"\n',
        "manual/index.md": "# M\n\ntext\n",
        "manual/logo.svg": "<svg xmlns='http://www.w3.org/2000/svg'/>",
        "manual/favicon.ico": b"\x00ico",
    })
    out = branded.config.dir_output()
    page = (out / "docs" / "index.html").read_text(encoding="utf-8")
    assert 'src="/docs/_docs-assets/0/logo.svg"' in page
    assert re.search(r'rel="icon" href="/docs/_docs-assets/0/favicon.ico"', page)
    assert (out / "docs" / "_docs-assets" / "0" / "favicon.ico").read_bytes() == b"\x00ico"
