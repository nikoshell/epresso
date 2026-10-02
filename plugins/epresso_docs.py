"""epresso_docs — the ``docs`` collection, from one or many Markdown sources.

Enable it and (optionally) list sources in ``site.toml``::

    plugins = ["epresso_docs"]

    [[plugin.epresso_docs.sources]]
    source = "docs"                       # local dir (relative to the site root)

    [[plugin.epresso_docs.sources]]
    source = "github:org/plugin-a@v1"     # or any git URL; cloned into .cache/repos
    dir = "docs"                          # dir inside it (default: "docs" for git, "." local)
    prefix = "/plugins/a/"                # URL prefix (default "/")
    title = "Plugin A"                    # sidebar group label
    repo_url = ""                         # "view source" base override

All sources merge into one ``docs`` collection (one sidebar, search and
prev/next chain). With no ``sources`` it reads the site's own docs dir, as the
docs theme always has (``[theme] docs_dir`` / ``docs_base`` / ``repo``).

Docs inside another site: set ``base``. Every page then lives under it, and the
plugin layers the docs theme (``theme``, default the bundled one) under the site
and serves its docs page route — the site's own pages and layouts are untouched::

    [plugin.epresso_docs]
    base = "/docs/"
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from epresso.content.docs import DocsLoader, DocsMount
from epresso.docs_source import resolve_docs_source
from epresso.errors import PluginError
from epresso.plugins import Plugin
from epresso.themes import bundled_docs_theme

DOCS_GLOB = "**/*.{md,markdown}"


class Doc(BaseModel):
    """What an author writes in a doc's frontmatter."""

    title: str
    description: str = ""
    draft: bool = False  # shown in dev/preview, excluded from production builds
    private: bool = False  # _-prefixed file: shown in dev/preview, excluded from production


def _blob(repo: str, branch: str, path: str) -> str:
    """GitHub-style "view source" base, or "" without a repo."""
    if not repo:
        return ""
    return "/".join(p.strip("/") for p in (repo, "blob", branch or "main", path) if p.strip("/"))


def _default_mount(config: Any) -> DocsMount:
    """The single source the docs theme read before this plugin existed."""
    theme = config.theme or {}
    root = config.root
    docs_base = theme.get("docs_base")
    if docs_base is None and theme.get("repo"):
        root = (root / str(theme["repo"])).resolve()
    src = resolve_docs_source(
        root,
        docs_dir=str(theme.get("docs_dir", "docs")),
        docs_base=Path(str(docs_base)) if docs_base else None,
    )
    site = config.site
    return DocsMount(
        base=src.base,
        docs_dir=src.docs_dir,
        repo_url=_blob(site.repository, site.branch, src.docs_dir),
    )


def _mount(config: Any, spec: dict[str, Any]) -> DocsMount:
    from epresso.docsgen import materialize_docs_source
    from epresso.gitrepo import default_branch, origin_url
    from epresso.themes import parse_source

    raw = str(spec.get("source", "docs"))
    local = (config.root / raw).resolve()
    if local.is_dir():
        where, is_git = local, False
    else:
        where = materialize_docs_source(raw, config.root / ".cache" / "repos")
        if where is None:
            raise PluginError(f"epresso_docs: source {raw!r} is not a directory or a git source")
        is_git = True
    sub = str(spec.get("dir", "docs" if is_git else ".")).strip("/") or "."
    base = (where / sub).resolve()
    repo_url = str(spec.get("repo_url", ""))
    if not repo_url:
        rel = "" if sub == "." else sub
        if is_git:
            ref = (parse_source(raw) or ("", None))[1]
            repo_url = _blob(origin_url(where), ref or default_branch(where), rel)
        elif base.is_relative_to(config.root):
            path = base.relative_to(config.root).as_posix()
            repo_url = _blob(config.site.repository, config.site.branch, "" if path == "." else path)
    return DocsMount(
        base=base,
        prefix=str(spec.get("prefix", "/")),
        title=str(spec.get("title", "")),
        repo_url=repo_url,
        docs_dir="" if sub == "." else sub,
    )


def _under(base: str, prefix: str) -> str:
    parts = [p for p in f"{base}/{prefix}".split("/") if p]
    return "/" + "/".join(parts) + "/" if parts else "/"


def _adopt_theme_markdown(config: Any, theme: Path) -> None:
    """Under ``base`` the host's ``[markdown]`` renders the docs: take the theme's
    code-block component (e.g. ``DocsHighlight``) unless the host chose its own."""
    import tomllib  # noqa: PLC0415

    try:
        md = tomllib.loads((theme / "site.toml").read_text(encoding="utf-8")).get("markdown", {})
    except (OSError, tomllib.TOMLDecodeError):
        return
    host = config.markdown
    if host.code_component or not md.get("code_component"):
        return
    host.code_component = md["code_component"]
    host.components = list(dict.fromkeys([*host.components, *md.get("components", [])]))


# Branding files picked up from a source's root when [theme] doesn't set them.
BRAND_FILES = {"logo": "logo.svg", "favicon": "favicon.ico", "og_image": "og-image.png"}


def _adopt_branding(config: Any, mounts: list[DocsMount]) -> None:
    """``logo.svg`` / ``favicon.ico`` / ``og-image.png`` next to the docs brand the
    site — the theme itself ships no logo, so projects get their own name, not
    epresso's. An explicit ``[theme]`` key wins; the first source that has a file wins."""
    theme = config.theme
    for key, name in BRAND_FILES.items():
        if theme.get(key):
            continue
        for m in mounts:
            if m.asset_url and (m.base / name).is_file():
                theme[key] = m.asset_url.rstrip("/") + "/" + name
                break


def before_load(caps) -> None:
    opts = caps.options
    sources = opts.get("sources")
    config = caps.config
    mounts = [_mount(config, s) for s in sources] if sources else [_default_mount(config)]
    from dataclasses import replace  # noqa: PLC0415

    base = str(opts.get("base", "")).strip("/")
    if base:
        mounts = [replace(m, prefix=_under(base, m.prefix)) for m in mounts]
        theme = (config.root / str(opts["theme"])).resolve() if opts.get("theme") else bundled_docs_theme()
        caps.add_layer(theme)
        caps.add_route("[...slug].ep", theme / "pages" / "[...slug].ep")
        _adopt_theme_markdown(config, theme)
    # Publish each source's images/files so relative srcs in its Markdown resolve.
    published = []
    content_dir = config.dir_content().resolve()
    for i, m in enumerate(mounts):
        if m.base.resolve().is_relative_to(content_dir):
            published.append(m)  # core already mirrors content/ images (public/content/…)
            continue
        url = _under(base, f"_docs-assets/{i}")
        caps.add_static(m.base, url)
        published.append(replace(m, asset_url=url))
    mounts = published
    _adopt_branding(config, mounts)
    caps.register_collection("docs", loader=DocsLoader(pattern=DOCS_GLOB, mounts=mounts), schema=Doc)


def epresso_docs() -> Plugin:
    return Plugin(name="epresso_docs", hooks={"before_load": before_load})


# Module-level instance so ``plugins = ["epresso_docs"]`` auto-discovers it.
docs = epresso_docs()
