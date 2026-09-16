"""epresso configuration — TOML + Pydantic, validated fail-fast."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .errors import ConfigError
from .gitrepo import default_branch as _repo_default_branch
from .gitrepo import origin_url as _repo_origin_url


class SiteConfig(BaseModel):
    name: str = "My Site"
    url: str = "http://localhost:8000"
    language: str = "en"
    description: str = ""
    repository: str = ""  # source repo URL for "view source / edit this page" links
    branch: str = "main"  # default branch for source/edit links
    docs_source: str = ""  # when set, the site is previewing docs from this path (epresso docs --theme)


class BuildConfig(BaseModel):
    output: str = "dist"
    content: str = "content"
    pages: str = "pages"
    layouts: str = "layouts"  # default layout dir (top-level)
    components: str = "components"  # default component dir (top-level)
    styles: str = "styles"  # default global stylesheet dir
    assets: str = "assets"
    static: str = "public"  # files copied verbatim to the output root
    trailing_slash: str = "always"  # always | never | ignore
    clean_urls: bool = True
    compress_html: bool = False  # minify HTML output (safe: skips <pre>/<script>/<style>)
    # Public base path prepended to root-relative URLs at build time (e.g.
    # "/epresso/" for a project GitHub Pages site). Empty = serve at root.
    base: str = ""
    redirects: bool = True  # emit redirect pages from the `redirects` config (Option C)
    # Reserved for future i18n (single-locale for now).


class MarkdownConfig(BaseModel):
    extensions: list[str] = Field(default_factory=list)
    toc_heading: str | None = None
    add_slug_ids: bool = True
    autolink_headings: bool = True
    highlight: bool = True  # Pygments syntax highlighting for fenced code blocks
    components: list[str] = Field(default_factory=list)  # custom component tags to resolve in markdown
    # Optional: a layout name used for direct Markdown pages that don't set one
    # in their front-matter (e.g. Base.ep).
    default_layout: str | None = None
    # Optional: name of a component to render fenced code blocks through at build
    # time (server-side). The component receives ``lang``/``file`` props and the
    # per-line highlighted body as children. When unset, Pygments emits a plain
    # ``<pre class="highlight">`` and a theme enhances it client-side.
    code_component: str | None = None
    # Per-language code-component overrides (e.g. {"tree": "Tree"}); the default
    # above handles any language not listed here.
    code_components: dict[str, str] = Field(default_factory=dict)


class ContentConfig(BaseModel):
    """Content publishing visibility, per active environment.

    ``show_drafts`` / ``show_private`` are optional. When left unset (``None``)
    epresso keeps its historic behaviour: draft/private entries are shown in
    development/preview and hidden in production builds. Set them explicitly
    in ``site.toml`` (the production base) and override in ``site.<env>.toml``
    to control dev vs prod independently:

    .. code-block:: toml

        # site.toml (== production behaviour)
        [content]
        show_drafts  = false
        show_private = false

        # site.development.toml (merged on top for `epresso dev`)
        [content]
        show_drafts  = true
        show_private = true
    """

    show_drafts: bool | None = None
    show_private: bool | None = None


class AssetsConfig(BaseModel):
    hash: bool = True
    # JS/CSS declared per-page in front matter + site-wide here.
    css: list[str] = Field(default_factory=list)
    js: list[str] = Field(default_factory=list)


class Redirects(BaseModel):
    items: list[tuple[str, str]] = Field(default_factory=list)


class RssConfig(BaseModel):
    enabled: bool = False
    collection: str = ""  # content collection to build the feed from
    path: str = "/rss.xml"
    title: str = ""  # defaults to the site name
    description: str = ""  # defaults to the site description
    limit: int = 0  # 0 = all entries
    # URL for each entry; {collection}/{id} are substituted
    url_template: str = "/{collection}/{id}/"


class LlmsConfig(BaseModel):
    """The ``llms.txt`` file (https://llmstxt.org/) generated from page routes."""

    enabled: bool = True
    path: str = "/llms.txt"
    title: str = ""  # defaults to the site name
    description: str = ""  # defaults to the site description


class SeoConfig(BaseModel):
    sitemap: bool = True
    robots: bool = True
    llms: LlmsConfig = Field(default_factory=LlmsConfig)
    rss: RssConfig = Field(default_factory=RssConfig)


class SearchConfig(BaseModel):
    enabled: bool = False
    index: str = "search-index.json"


class DevToolbar(BaseModel):
    """The floating toolbar shown by the development server."""

    enabled: bool = True
    placement: str = "bottom"  # "bottom" | "top"


class DevConfig(BaseModel):
    toolbar: DevToolbar = Field(default_factory=DevToolbar)


class LayersConfig(BaseModel):
    """External component/layout roots, layered under the site's own.

    Each entry is one of:

    * a **directory path** — ``./vendor/components``, ``path:./vendor/lib``;
    * a **Python package** that ships ``components/`` / ``layouts/`` —
      ``pkg:epresso_ui`` (installed, importable);
    * a **git repo** — ``github:owner/repo@v1``, ``git+https://…@main``.
      GitHub repos are fetched as a tarball; other URLs are shallow-cloned.
      Both land in ``.cache/layers/`` and are reused on later builds.

    The site's own ``components/`` and ``layouts/`` are always searched first,
    then layers in declaration order.
    """

    use: list[str] = Field(default_factory=list)


class DocsSection(BaseModel):
    """A docs section built into the site's output under ``base``.

    Declarative equivalent of ``EPRESSO_BASE=/docs/ epresso docs --out dist/docs <source>``.
    Use ``[docs]`` for one section or ``[[docs]]`` for several.
    """

    source: str = "docs"  # Markdown dir (or a project dir with its own site.toml)
    base: str = "/docs/"  # public sub-path within the site
    theme: str = ""  # theme project for bare Markdown (default: bundled docs theme)
    out: str = ""  # output subdir of dist/ (default: derived from base)

    @field_validator("base")
    @classmethod
    def _norm_base(cls, v: str) -> str:
        v = (v or "/docs/").strip()
        return "/" + v.strip("/") + "/"

    @field_validator("out")
    @classmethod
    def _norm_out(cls, v: str) -> str:
        return (v or "").strip().strip("/")


class Config(BaseModel):
    site: SiteConfig = Field(default_factory=SiteConfig)
    build: BuildConfig = Field(default_factory=BuildConfig)
    content: ContentConfig = Field(default_factory=ContentConfig)
    markdown: MarkdownConfig = Field(default_factory=MarkdownConfig)
    assets: AssetsConfig = Field(default_factory=AssetsConfig)
    seo: SeoConfig = Field(default_factory=SeoConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    dev: DevConfig = Field(default_factory=DevConfig)
    docs: list[DocsSection] = Field(default_factory=list)
    redirects: list[dict[str, str | dict]] = Field(default_factory=list)
    plugins: list[str] = Field(default_factory=list)  # dotted paths, e.g. "mypkg:MyPlugin"
    layers: LayersConfig = Field(default_factory=LayersConfig)  # extra component/layout roots
    # Opaque theme configuration. Core only carries this through; themes read
    # and interpret it (e.g. ``[theme] sidebar = "tree"``). Core stays agnostic.
    theme: dict[str, Any] = Field(default_factory=dict)
    env: str | None = None  # active environment name (from --env / EPRESSO_ENV)

    # --- file locations -------------------------------------------------
    root: Path = Field(default_factory=lambda: Path.cwd())

    @field_validator("docs", mode="before")
    @classmethod
    def _docs(cls, v: Any) -> Any:
        """Accept a single ``[docs]`` table or an array ``[[docs]]``."""
        if v is None:
            return []
        return [v] if isinstance(v, dict) else v

    @field_validator("redirects")
    @classmethod
    def _redirects(cls, v: list[dict[str, str | dict]]) -> list[dict[str, str | dict]]:
        for item in v:
            if len(item) != 1:
                raise ValueError("each redirect must be a single {from: to} pair")
            for _src, dst in item.items():
                if isinstance(dst, str):
                    continue
                if isinstance(dst, dict) and set(dst).issubset({"destination", "status"}) and "destination" in dst:
                    continue
                raise ValueError(
                    "redirect target must be a string or {destination, status} (301/302)"
                )
        return v

    def source_root(self) -> Path:
        """Directory that source dirs are resolved against.

        Astro/Nuxt-style: when a top-level ``src/`` directory exists, pages,
        components, layouts, content, styles and assets live inside
        it. ``public/`` (``dir_static``), ``dist/`` (``dir_output``), ``.cache/``
        and project config (``site.toml``, ``content.config.py``) stay at the
        project root either way.
        """
        src = self.root / "src"
        return src if src.is_dir() else self.root

    def dir_content(self) -> Path:
        return self.source_root() / self.build.content

    def dir_pages(self) -> Path:
        return self.source_root() / self.build.pages

    def dir_layouts(self) -> Path:
        return self.source_root() / self.build.layouts

    def dir_components(self) -> Path:
        return self.source_root() / self.build.components

    def dir_styles(self) -> Path:
        return self.source_root() / self.build.styles

    def dir_assets(self) -> Path:
        return self.source_root() / self.build.assets

    def dir_static(self) -> Path:
        return self.root / self.build.static

    def dir_output(self) -> Path:
        return self.root / self.build.output

    def cache_dir(self) -> Path:
        """Incremental cache location (gitignored; NOT cleaned by a clean build)."""
        return self.root / ".cache"


def load_env_file(root: Path, env: str | None) -> dict[str, str]:
    """Load a dotenv-style ``.env.<env>`` file (KEY=VALUE) into a dict.

    Values are trimmed; optional surrounding quotes are stripped. Returns {} if
    the file is absent or ``env`` is None. Does not modify ``os.environ``.
    """
    if not env:
        return {}
    path = root / f".env.{env}"
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            out[key] = value
    return out


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge ``override`` into ``base`` (override wins, dicts merge)."""
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _git_defaults(root: Path) -> tuple[str, str]:
    """Best-effort ``(origin_url, default_branch)`` for a project inside a git repo.

    Delegates to the shared repository adapter (:mod:`epresso.gitrepo`). A cheap
    guard avoids spawning git when there's no ``.git`` at ``root`` or an ancestor
    (keeps the non-repo fast path free of subprocess overhead).
    """
    if not any((p / ".git").exists() for p in (root, *root.parents)):
        return "", ""
    return _repo_origin_url(root), _repo_default_branch(root)


def load_config(root: Path | None = None, env: str | None = None) -> Config:
    """Load site.toml from ``root`` (default cwd). Missing file → defaults.

    If ``env`` is given, ``site.<env>.toml`` is loaded and deep-merged over
    ``site.toml`` (so a per-environment file can override URL, APIs, toggles,
    etc.). ``env`` is recorded on the config for introspection.
    """
    root = (root or Path.cwd()).resolve()
    path = root / "site.toml"
    data: dict[str, Any] = {}
    if path.exists():
        try:
            with path.open("rb") as fh:
                data = tomllib.load(fh)
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(f"invalid site.toml: {e}", path=str(path)) from e
    if env:
        env_path = root / f"site.{env}.toml"
        if env_path.exists():
            try:
                with env_path.open("rb") as fh:
                    data = _deep_merge(data, tomllib.load(fh))
            except tomllib.TOMLDecodeError as e:
                raise ConfigError(f"invalid {env_path.name}: {e}", path=str(env_path)) from e
    if env:
        data = _deep_merge(data, {"env": env})
    # If the project lives in a git repo and ``site.repository`` / ``site.branch``
    # aren't set explicitly in TOML, default them from the repo's ``origin`` URL
    # and HEAD branch (these drive "view source / edit this page" links).
    site_tbl = data.get("site")
    need_repo = not (isinstance(site_tbl, dict) and "repository" in site_tbl)
    need_branch = not (isinstance(site_tbl, dict) and "branch" in site_tbl)
    if need_repo or need_branch:
        url, branch = _git_defaults(root)
        if need_repo and url:
            data.setdefault("site", {})["repository"] = url
        if need_branch and branch:
            data.setdefault("site", {})["branch"] = branch
    try:
        config = Config.model_validate({**data, "root": root})
    except Exception as e:  # noqa: BLE001 — pydantic ValidationError
        raise ConfigError(f"invalid configuration: {e}", path=str(path)) from e
    # EPRESSO_BASE lets the deploy workflow set the public base path (e.g.
    # "/epresso/" for a project GitHub Pages site). Default (unset) = serve at root.
    _base = os.environ.get("EPRESSO_BASE", "").strip("/")
    if _base:
        config.build.base = "/" + _base + "/"
    return config


