"""Plugin API tests — capability registry: hooks, ordering, dedup, phases,
contributions (globals/filters/collections/markdown-ext/html transforms)."""

from epresso.errors import PluginError
from epresso.plugins import CapabilityError, Plugin
from epresso.site import Site


def _make(files):
    import tempfile
    from pathlib import Path

    d = tempfile.mkdtemp()
    root = Path(d)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root, Site.load(root)


def _build(files, *plugins, page="index.html"):
    """Create a site with the given page(s), register plugins, then build."""
    root, site = _make(files)
    for p in plugins:
        site.plugins.register(p)
    site.build()
    return site


def _out(site, rel="index.html") -> str:
    return (site.config.dir_output() / rel).read_text(encoding="utf-8")


# -- construction + ordering -----------------------------------------------


def test_factory_plugin_adds_template_global():
    def greeter():
        def on_setup(caps):
            caps.add_global("greeting", lambda: "hello-from-plugin")

        return Plugin(name="greeter", hooks={"on_setup": on_setup})

    site = _build({"pages/index.ep": "---\n---\n<p>{{ greeting() }}</p>"}, greeter())
    assert "hello-from-plugin" in _out(site)


def test_subclass_style_collects_method_hooks():
    class Greeter(Plugin):
        name = "greeter"

        def on_setup(self, caps):
            caps.add_global("greeting", lambda: "subclass-hello")

    site = _build({"pages/index.ep": "---\n---\n{{ greeting() }}"}, Greeter())
    assert "subclass-hello" in _out(site)


def test_priority_determines_run_order():
    order = []

    def mk(name, priority, tag):
        def on_setup(caps):
            order.append(tag)

        return Plugin(name=name, priority=priority, hooks={"on_setup": on_setup})

    _build({"pages/index.ep": "---\n---\nx"}, mk("low", priority=0, tag="low"), mk("high", priority=10, tag="high"))
    assert order == ["low", "high"]


def test_later_higher_priority_filter_overrides_earlier():
    def on_setup_low(caps):
        caps.add_filter("shout", lambda s: s)

    def on_setup_high(caps):
        caps.add_filter("shout", lambda s: str(s).upper())

    site = _build(
        {"pages/index.ep": "---\n---\n{{ 'hi' | shout }}"},
        Plugin(name="identity", priority=0, hooks={"on_setup": on_setup_low}),
        Plugin(name="shouter", priority=10, hooks={"on_setup": on_setup_high}),
    )
    assert "HI" in _out(site)


def test_duplicate_plugin_name_rejected():
    root, site = _make({"pages/index.ep": "---\n---\nx"})
    site.plugins.register(Plugin(name="dup", hooks={}))
    try:
        site.plugins.register(Plugin(name="dup", hooks={}))
        raise AssertionError("expected PluginError for duplicate name")
    except PluginError:
        pass


def test_disabled_plugin_skipped():
    def on_setup(caps):
        caps.add_global("greeting", lambda: "SHOULD-NOT-APPEAR")

    site = _build(
        {"pages/index.ep": "---\n---\n{{ greeting() if greeting else 'none' }}"},
        Plugin(name="off", enabled=False, hooks={"on_setup": on_setup}),
    )
    assert "SHOULD-NOT-APPEAR" not in _out(site)


# -- capabilities -----------------------------------------------------------


def test_html_transform_rewrites_rendered_page():
    seen = {}

    def on_setup(caps):
        def transform(html, ctx):
            seen["path"] = ctx["path"]
            return html + "\n<!-- transformed -->"

        caps.transform_html(transform)

    site = _build({"pages/index.ep": "---\n---\n<p>body</p>"}, Plugin(name="t", hooks={"on_setup": on_setup}))
    assert "<!-- transformed -->" in _out(site)
    assert seen["path"] == "/"  # index route path


def test_inject_head_inserts_fragment():
    def on_setup(caps):
        caps.inject_head('<meta name="x" content="1">')

    site = _build(
        {"pages/index.ep": "---\n---\n<html><head><title>t</title></head><body>hi</body></html>"},
        Plugin(name="meta", hooks={"on_setup": on_setup}),
    )
    out = _out(site)
    assert out.index('<meta name="x" content="1">') < out.index("</head>")


def test_html_transform_disables_route_reuse_but_build_is_idempotent():
    def on_setup(caps):
        def transform(html, ctx):
            return html + "<!-- t -->"

        caps.transform_html(transform)

    site = _build({"pages/index.ep": "---\n---\n<p>a</p>"}, Plugin(name="t", hooks={"on_setup": on_setup}))
    site.build()  # second build must not double-apply (transforms reset each load)
    assert _out(site).count("<!-- t -->") == 1


def test_register_collection_before_load_populates_store():
    def before_load(caps):
        caps.register_collection(
            "teams",
            loader=lambda: [{"id": "a", "data": {"name": "alpha"}}],
        )

    site = _build(
        {"pages/index.ep": "---\n---\n<span>{{ get_collection('teams') | length }} teams</span>"},
        Plugin(name="teams", hooks={"before_load": before_load}),
    )
    assert "1 teams" in _out(site)
    assert site.get_collection("teams")[0].data["name"] == "alpha"


def test_register_collection_wrong_phase_raises_capability_error():
    def on_setup(caps):
        caps.register_collection("teams", loader=lambda: [])

    root, site = _make({"pages/index.ep": "---\n---\nx"})
    site.plugins.register(Plugin(name="bad", hooks={"on_setup": on_setup}))
    try:
        site.build()
        raise AssertionError("expected CapabilityError")
    except CapabilityError:
        pass


def test_markdown_extension_registration_is_idempotent():
    def before_load(caps):
        caps.add_markdown_extension("markdown.extensions.extra")

    site = _build(
        {"pages/index.ep": "---\n---\nx"},
        Plugin(name="md1", hooks={"before_load": before_load}),
        Plugin(name="md2", hooks={"before_load": before_load}),
    )
    site.build()  # reload path must not duplicate the extension
    assert site.config.markdown.extensions.count("markdown.extensions.extra") == 1


def test_plugin_error_wrapped_with_name():
    def on_setup(caps):
        raise ValueError("boom")

    root, site = _make({"pages/index.ep": "---\n---\nx"})
    site.plugins.register(Plugin(name="exploder", hooks={"on_setup": on_setup}))
    try:
        site.build()
        raise AssertionError("expected PluginError")
    except PluginError as e:
        assert "exploder" in str(e)
        assert "boom" in str(e)


# -- discovery --------------------------------------------------------------


def test_project_plugins_py_hooks_run_in_order(tmp_path):
    root, site = _make(
        {
            "plugins.py": (
                "from epresso.plugins import Plugin\n"
                "calls = []\n"
                "class Tracer(Plugin):\n"
                "    name='tracer'\n"
                "    def before_load(self, caps): calls.append('before_load')\n"
                "    def after_load(self, caps): calls.append('after_load')\n"
                "    def before_build(self, caps): calls.append('before_build')\n"
                "    def after_build(self, caps, result): calls.append('after_build')\n"
                "    def on_setup(self, caps): calls.append('on_setup')\n"
                "tracer = Tracer()\n"
            ),
            "pages/index.ep": "---\n---\nhi",
        }
    )
    assert len(site.plugins.plugins) == 1
    site.build()
    import sys

    calls = sys.modules["_epresso_plugins"].calls
    assert calls.index("on_setup") < calls.index("before_build")
    assert calls.index("before_load") < calls.index("after_load")
    assert calls.index("before_build") < calls.index("after_build")
