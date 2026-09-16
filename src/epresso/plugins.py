"""Plugin API — a capability registry with named lifecycle hooks.

A plugin is a *named, configurable object* (``Plugin``) exposing an ordered set
of hooks. Each hook receives a narrow :class:`Capabilities` handle — not the raw
``Site`` — so a plugin can only touch the public extension surface epresso
chooses to expose. Contributions are deterministic: plugins are deduplicated by
name, run in ``priority`` order, and re-running a load never double-applies.

Two construction styles are supported:

* **Factory / data style** — the recommended, options-friendly shape::

      from epresso.plugins import Plugin

      def greeter(**opts):
          def on_setup(caps):
              caps.add_global("greeting", opts["text"])

          return Plugin(name="greeter", hooks={"on_setup": on_setup})

* **Subclass style** — ``on_*`` methods are auto-collected into ``hooks``::

      from epresso.plugins import Plugin

      class Greeter(Plugin):
          name = "greeter"

          def on_setup(self, caps):
              caps.add_global("greeting", "hello")

Plugins are discovered from ``[plugins]`` in ``site.toml`` (dotted paths to
installed packages) and/or a project ``plugins.py`` that assigns ``Plugin``
instances to module attributes. Enable options-ful plugins by building them with
a factory in ``plugins.py`` (a dotted-path string cannot carry options).
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .errors import PluginError
from .logger import get_logger

# Bundled plugins ship under the repo's ``plugins/`` dir (dev / ``uv run``); make
# them importable by dotted name so e.g. ``[plugins] = ["epresso_pandoc"]`` works.
_BUNDLED_PLUGINS = Path(__file__).resolve().parents[2] / "plugins"
if _BUNDLED_PLUGINS.is_dir() and str(_BUNDLED_PLUGINS) not in sys.path:
    sys.path.insert(0, str(_BUNDLED_PLUGINS))

# The lifecycle hooks a subclass may implement as ``on_*`` methods. Factory hooks
# may use these same keys (or future namespaced ones) in the ``hooks`` dict.
LIFECYCLE_HOOKS: tuple[str, ...] = (
    "before_load",  # earliest — register collections / markdown extensions here
    "on_setup",     # environment + template globals are ready
    "after_load",   # content is loaded + rendered
    "before_build", # build is about to render routes
    "after_build",  # build finished — receives the BuildResult
    "on_assets",    # before assets/images are written
)

HookFn = Callable[..., Any]



class Plugin:
    """A plugin: identity + an ordered map of lifecycle hooks.

    Attributes
    ----------
    name : str
        Unique name. The manager rejects duplicate names at registration.
    version : str
        Plugin version (shown in diagnostics).
    priority : int
        Lower runs first. Default ``0``; ties keep registration order.
    hooks : dict[str, HookFn]
        Hook name -> callable. A hook is called as ``fn(caps, *phase_args)``.
    enabled : bool
        Set ``False`` to skip this plugin.
    """

    name: str = "plugin"
    version: str = "0.1"
    priority: int = 0

    def __init__(
        self,
        *,
        name: str | None = None,
        hooks: dict[str, HookFn] | None = None,
        version: str | None = None,
        priority: int | None = None,
        enabled: bool = True,
    ) -> None:
        if name is not None:
            self.name = name
        if version is not None:
            self.version = version
        if priority is not None:
            self.priority = priority
        self.enabled = enabled
        self.hooks: dict[str, HookFn] = dict(hooks or {})
        self._collect_subclass_hooks()

    # -- subclass ergonomics -------------------------------------------------
    def _collect_subclass_hooks(self) -> None:
        """Pull any overridden ``on_*`` methods into ``self.hooks`` (bound)."""
        for hook in LIFECYCLE_HOOKS:
            if hook in self.hooks:
                continue
            impl = getattr(type(self), hook, None)
            base = getattr(Plugin, hook, None)
            if impl is not None and impl is not base:
                self.hooks[hook] = getattr(self, hook)

    # no-op defaults so subclasses can override only what they need
    def before_load(self, caps: Capabilities) -> None:
        """Register collections/loaders and markdown extensions."""

    def on_setup(self, caps: Capabilities) -> None:
        """Register template globals/filters and html transforms."""

    def after_load(self, caps: Capabilities) -> None:
        """Read the loaded content store."""

    def before_build(self, caps: Capabilities) -> None:
        """One more chance before routes render."""

    def after_build(self, caps: Capabilities, result: Any) -> None:
        """Inspect the finished build."""

    def on_assets(self, caps: Capabilities) -> None:
        """Inspect/replace the asset pipeline before it writes."""

    def __repr__(self) -> str:
        return f"<Plugin {self.name!r} v{self.version} priority={self.priority} hooks={sorted(self.hooks)}>"


class Capabilities:
    """The narrow handle a hook receives.

    A plugin can only call the methods here — it never touches the raw ``Site``.
    Each capability is validated against the phase it runs in and raises a clear
    :class:`CapabilityError` when used at the wrong time (so a plugin author gets
    a hint instead of silent breakage).

    Note
    ----
    ``add_global`` / ``add_filter`` require the Jinja environment, which exists
    from ``on_setup`` onward. ``register_collection`` / ``add_markdown_extension``
    must happen in ``before_load`` so the collection body / markdown rendering
    can see them.
    """

    _LOAD_PHASE = "before_load"

    def __init__(self, plugin: Plugin, site: Any, phase: str) -> None:
        self.plugin = plugin
        self.site = site
        self.phase = phase
        # a namespaced logger so a plugin's output reads [plugin:<name>] and its
        # debug lines are gated by ``EPRESSO_DEBUG=plugin:<name>`` / ``*``.
        self.logger = get_logger(f"plugin:{plugin.name}")

    # -- identity / context -------------------------------------------------
    @property
    def config(self) -> Any:
        return self.site.config

    # -- templates ----------------------------------------------------------
    def add_global(self, name: str, value: Any) -> None:
        """Expose ``value`` as a template global named ``name``."""
        self._require_env()
        self.site.env.globals[name] = value

    def add_filter(self, name: str, fn: Callable[..., Any]) -> None:
        """Register a Jinja template filter named ``name``."""
        self._require_env()
        self.site.env.filters[name] = fn

    # -- content ------------------------------------------------------------
    def register_collection(
        self,
        name: str,
        *,
        loader: Any | None = None,
        schema: type | None = None,
        glob: str | None = None,
        base: str = "./content",
        generate_id: Callable[[str], str] | None = None,
    ) -> None:
        """Add a content collection (with a loader) before content is loaded.

        Mirrors :func:`epresso.content.collections.define_collection`: pass a
        ``loader`` (a ``LoaderObject``/``PythonLoader``/callable) OR a ``glob``
        pattern. Runs the loader immediately so the collection's entries are in
        the store with rendered bodies like any other collection.
        """
        if self.phase != self._LOAD_PHASE:
            raise CapabilityError(
                "register_collection() must run in the 'before_load' hook so the "
                f"collection can be loaded before content is. (phase is {self.phase!r})",
                plugin=self.plugin.name,
            )
        from .content import define_collection  # local import avoids a cycle
        from .content.loaders import GlobLoader

        col = define_collection(
            name,
            loader=loader,
            schema=schema,
            glob=glob,
            base=base,
            generate_id=generate_id,
        )
        installed = col.install(self.site.store)
        if isinstance(installed.loader, GlobLoader):
            base = self.site.config.source_root()
            installed.loader.base = (base / installed.loader.base).resolve()
        installed.loader.load(self.site.store, installed)

    def add_markdown_extension(self, spec: str) -> None:
        """Register a markdown extension (idempotent) for content rendering."""
        if self.phase != self._LOAD_PHASE:
            raise CapabilityError(
                "add_markdown_extension() must run in the 'before_load' hook so "
                "content bodies render with the extension. (phase is "
                f"{self.phase!r})",
                plugin=self.plugin.name,
            )
        exts = self.site.config.markdown.extensions
        if spec not in exts:
            exts.append(spec)

    # -- markdown pipeline ------------------------------------------------
    def add_markdown_source_transform(self, fn: Callable[[str], str]) -> None:
        """Register a markdown *source* transform (``str -> str``) applied before
        rendering (e.g. Pandoc fenced-code attributes, MkDocs content tabs)."""
        from . import markdown as _md

        _md.register_markdown_transform(fn)

    def add_html_postprocess(self, fn: Callable[[str], str]) -> None:
        """Register an html post-processor (``str -> str``) over rendered output
        (e.g. Pandoc image attributes)."""
        from . import markdown as _md

        _md.register_html_transform(fn)

    def add_markdown_render_transform(self, fn) -> None:
        """Register a render transform ``fn(md, src, depth) -> str`` run before the
        final markdown render (used by features that render inner Markdown, e.g.
        MkDocs Material content tabs)."""
        from . import markdown as _md

        _md.register_markdown_render_transform(fn)

    # -- rendered-output transforms ----------------------------------------
    def transform_html(self, fn: Callable[[str, dict[str, Any]], str]) -> None:
        """Rewrite every rendered HTML route: ``fn(html, ctx) -> html``.

        ``ctx`` carries ``{"path", "params"}`` for the route being rendered. Pure
        functions are preferred so epresso can reason about caching.
        """
        self._require_html_target()
        self.site._html_transforms.append((self.plugin.name, fn))

    def inject_head(self, fragment: str) -> None:
        """Insert ``fragment`` into ``<head>`` of every HTML page."""
        self.transform_html(_make_head_injector(fragment))

    # -- internals ----------------------------------------------------------
    def _require_env(self) -> None:
        if self.site.env is None:
            raise CapabilityError(
                "template capability used before the Jinja environment exists — "
                "register globals/filters from the 'on_setup' hook.",
                plugin=self.plugin.name,
            )

    def _require_html_target(self) -> None:
        if not hasattr(self.site, "_html_transforms"):
            raise CapabilityError("this epresso version has no html-transform target", plugin=self.plugin.name)


class CapabilityError(PluginError):
    """A plugin used a capability at the wrong time or against an unknown target."""

    def __init__(self, message: str, *, plugin: str) -> None:
        super().__init__(f"plugin {plugin!r}: {message}")


def _make_head_injector(fragment: str) -> Callable[[str, dict[str, Any]], str]:
    def _inject(html: str, ctx: dict[str, Any]) -> str:
        if "</head>" in html and fragment not in html:
            return html.replace("</head>", fragment + "</head>", 1)
        return html

    return _inject


class PluginManager:
    """Collects plugins, deduplicates by name, and runs lifecycle hooks."""

    def __init__(self) -> None:
        self.plugins: list[Plugin] = []
        self._names: set[str] = set()

    # -- registration --------------------------------------------------------
    def register(self, plugin: Plugin) -> None:
        if not isinstance(plugin, Plugin):
            raise TypeError(f"expected a Plugin instance, got {type(plugin).__name__!r}")
        if not plugin.name or plugin.name == "plugin":
            raise PluginError(f"plugin needs a unique name: {plugin!r}")
        if plugin.name in self._names:
            raise PluginError(f"duplicate plugin name {plugin.name!r} — rename it or drop one registration")
        self._names.add(plugin.name)
        self.plugins.append(plugin)
        # stable sort by priority: equal priorities keep registration order
        self.plugins.sort(key=lambda p: p.priority)

    # -- hook dispatch -------------------------------------------------------
    def run_hook(self, hook: str, site: Any, *args: Any) -> None:
        """Run ``hook`` across plugins in order, each with a fresh Capabilities."""
        for plugin in self.plugins:
            if not plugin.enabled:
                continue
            fn = plugin.hooks.get(hook)
            if fn is None:
                continue
            caps = Capabilities(plugin, site, hook)
            try:
                fn(caps, *args)
            except CapabilityError:
                raise
            except Exception as e:  # noqa: BLE001
                raise PluginError(f"plugin {plugin.name!r} failed in {hook}: {e}") from e

    # -- discovery -----------------------------------------------------------
    def discover(self, root: Path, config: Any) -> None:
        """Load plugins from ``[plugins]`` config (dotted paths) and ``plugins.py``."""
        for spec in config.plugins:
            for plugin in self._from_spec(spec):
                self.register(plugin)
        self._from_project_file(root)

    def _from_spec(self, spec: str) -> list[Plugin]:
        """Load ``pkg.mod:Name`` or ``pkg.mod`` (all Plugin instances)."""
        module_path, _, attr = spec.partition(":")
        try:
            module = importlib.import_module(module_path)
        except Exception as e:  # noqa: BLE001
            raise PluginError(f"cannot import plugin {spec!r}: {e}") from e
        if attr:
            obj = getattr(module, attr)
            return [obj] if isinstance(obj, Plugin) else list(obj)
        return [v for v in vars(module).values() if isinstance(v, Plugin)]

    def _from_project_file(self, root: Path) -> None:
        path = root / "plugins.py"
        if not path.exists():
            return
        spec = importlib.util.spec_from_file_location("_epresso_plugins", path)
        if spec is None or spec.loader is None:
            return
        module = importlib.util.module_from_spec(spec)
        sys.modules["_epresso_plugins"] = module
        try:
            spec.loader.exec_module(module)
        except Exception as e:  # noqa: BLE001
            raise PluginError(f"cannot load project plugins.py: {e}") from e
        for value in vars(module).values():
            if isinstance(value, Plugin) and value not in self.plugins:
                self.register(value)
