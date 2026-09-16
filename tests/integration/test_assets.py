"""Asset pipeline tests — content-hashing, static passthrough, asset() in templates."""


from epresso.site import Site


def _make(files):
    import tempfile
    from pathlib import Path

    d = tempfile.mkdtemp()
    root = Path(d)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            p.write_text(content, encoding="utf-8")
        else:
            p.write_bytes(content)
    return root, Site.load(root)


def test_asset_resolves_to_hashed_url(tmp_path):
    root, site = _make(
        {
            "assets/css/main.css": "body { color: red; }\n",
            "pages/index.ep": "<link rel=\"stylesheet\" href=\"{{ asset('css/main.css') }}\">",
        }
    )
    site.build()
    out = site.config.dir_output()
    # asset() produced a content-hashed URL
    hashed = [p for p in out.joinpath("assets", "css").rglob("main.*.css")]
    assert len(hashed) == 1
    digest = hashed[0].name.split("main.")[1].split(".css")[0]
    html = (out / "index.html").read_text()
    assert f"/assets/css/main.{digest}.css" in html
    # content matches source (CSS is minified at build time)
    assert "color:red" in hashed[0].read_text()


def test_hash_changes_with_content(tmp_path):
    root, site = _make(
        {
            "assets/js/app.js": "console.log(1);\n",
            "pages/index.ep": "---\n---\nx",
        }
    )
    # register the asset via resolve
    url1 = site.assets.resolve("js/app.js")
    site._do_load()
    # change file
    (root / "assets" / "js" / "app.js").write_text("console.log(2);\n")
    site._do_load()
    url2 = site.assets.resolve("js/app.js")
    assert url1 != url2


def test_static_passthrough(tmp_path):
    root, site = _make(
        {
            "public/favicon.ico": b"\x00fakeico",
            "public/img/logo.png": b"\x89PNGfake",
            "pages/index.md": "---\ntitle: Home\n---\nHi\n",
        }
    )
    site.build()
    out = site.config.dir_output()
    assert (out / "favicon.ico").read_bytes() == b"\x00fakeico"
    assert (out / "img" / "logo.png").read_bytes() == b"\x89PNGfake"


def test_asset_without_hash_config(tmp_path):
    root, site = _make(
        {
            "site.toml": "[assets]\nhash = false\n",
            "assets/css/a.css": "a{}\n",
            "pages/index.ep": "---\n---\nx",
        }
    )
    url = site.assets.resolve("css/a.css")
    assert url == "/assets/css/a.css"


def test_esbuild_missing_falls_back_to_copy(tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    root, site = _make(
        {
            "assets/js/main.js": "console.log('hi');\n",
            "pages/index.ep": "---\n---\nx",
        }
    )
    site.config.assets.js = ["js/main.js"]
    site.build()
    out = site.config.dir_output()
    assert (out / "assets" / "js" / "main.js").exists()  # raw copy fallback
