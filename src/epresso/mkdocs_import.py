"""Read an MkDocs ``mkdocs.yml`` as a ``docs.toml`` dict.

One mapping, two users: ``epresso docs`` reads ``mkdocs.yml`` live, and
``epresso import mkdocs`` writes the same dict out as ``docs.toml``. Anything
without an epresso equivalent is reported, never silently dropped.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError

# markdown_extensions the epresso_mkdocs plugin (or core markdown) covers.
COVERED_EXTENSIONS = {
    "admonition",
    "pymdownx.details",
    "pymdownx.superfences",
    "pymdownx.tabbed",
    "attr_list",
    "md_in_html",
    "pymdownx.snippets",
    "def_list",
    "footnotes",
    "abbr",
    "pymdownx.tasklist",
    "pymdownx.mark",
    "pymdownx.caret",
    "pymdownx.tilde",
    "pymdownx.keys",
    "pymdownx.highlight",
    "pymdownx.inlinehilite",
    "tables",
    "toc",
    "meta",
    "pymdownx.betterem",
    "pymdownx.smartsymbols",
    "sane_lists",
    "fenced_code",
    "codehilite",
    "pymdownx.magiclink",
}
# plugins: built in (nothing to do) / mapped / the roadmap gap that covers them.
BUILTIN_PLUGINS = {"search", "minify", "social", "optimize"}  # → epresso_social / epresso_optimize (docs theme)
PLUGIN_GAPS = {
    "rss": "use `epresso_docs` + the RSS guide",
    "mkdocstrings": "API reference (planned)",
    "macros": "content reuse (planned)",
}
IGNORED_KEYS = {
    "site_author",
    "copyright",
    "use_directory_urls",
    "strict",
    "watch",
    "dev_addr",
    "repo_name",
    "edit_uri",
    "extra",
    "remote_branch",
    "remote_name",
    "validation",
    "exclude_docs",
    "not_in_nav",
    "hooks",
}


class _Loader(yaml.SafeLoader):
    """SafeLoader that tolerates ``!!python/name:...`` and ``!ENV`` tags
    (common in Material configs) instead of executing or rejecting them."""


def _tolerant(loader: yaml.SafeLoader, suffix: str, node: yaml.Node) -> Any:
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)  # type: ignore[arg-type]


_Loader.add_multi_constructor("tag:yaml.org,2002:python/", _tolerant)
_Loader.add_multi_constructor("!", _tolerant)


def _name(entry: Any) -> str:
    return next(iter(entry)) if isinstance(entry, dict) else str(entry)


def _page_url(md: str) -> str:
    """``guide/old.md`` → ``/guide/old/`` (``index.md`` / ``README.md`` → the dir)."""
    if "://" in md:
        return md
    p = md.strip("/").removesuffix(".md").removesuffix(".markdown")
    if p.rsplit("/", 1)[-1].lower() in {"index", "readme"}:
        p = p.rpartition("/")[0]
    return "/" + p + "/" if p else "/"


def mkdocs_to_docs_config(path: Path) -> tuple[dict, list[str]]:
    """Map ``mkdocs.yml`` to a ``docs.toml`` dict. Returns ``(config, warnings)``.

    Paths in the result are relative to the ``mkdocs.yml`` directory.
    """
    try:
        raw = yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader) or {}  # noqa: S506
    except yaml.YAMLError as e:
        raise ConfigError(f"invalid mkdocs.yml: {e}", path=str(path)) from e
    if not isinstance(raw, dict):
        raise ConfigError("mkdocs.yml must be a mapping", path=str(path))
    warn: list[str] = []
    docs_dir = str(raw.get("docs_dir", "docs")).strip("/") or "."
    cfg: dict[str, Any] = {}
    site: dict[str, Any] = {}
    source: dict[str, Any] = {"source": docs_dir}

    if raw.get("site_name"):
        cfg["title"] = str(raw["site_name"])
    if raw.get("site_url"):
        site["url"] = str(raw["site_url"])
    if raw.get("site_description"):
        site["description"] = str(raw["site_description"])
    if raw.get("repo_url"):
        repo = str(raw["repo_url"]).rstrip("/")
        site["repository"] = repo
        edit = str(raw.get("edit_uri") or f"blob/main/{docs_dir}").strip("/")
        source["repo_url"] = f"{repo}/{edit}"
    if raw.get("nav"):
        source["nav"] = raw["nav"]

    for ext in raw.get("markdown_extensions") or []:
        name = _name(ext)
        if name not in COVERED_EXTENSIONS:
            warn.append(f"markdown_extensions: {name!r} is not supported (its syntax renders as plain text)")

    redirects = []
    for plugin in raw.get("plugins") or []:
        name = _name(plugin)
        opts = plugin[name] if isinstance(plugin, dict) else {}
        if name in BUILTIN_PLUGINS:
            continue
        if name == "blog":
            blog = {
                k: v
                for k, v in (opts or {}).items()
                if k
                in (
                    "blog_dir",
                    "post_url_format",
                    "pagination_per_page",
                    "archive",
                    "categories",
                    "authors_file",
                    "draft",
                    "rss",
                )
            }
            if (opts or {}).get("post_slugify") in ("title", "file"):
                blog["post_slugify"] = opts["post_slugify"]
            cfg["blog"] = blog  # options for epresso_blog (the docs theme enables it)
            continue
        if name == "redirects":
            for old, new in ((opts or {}).get("redirect_maps") or {}).items():
                redirects.append({_page_url(str(old)): _page_url(str(new))})
        elif name in PLUGIN_GAPS:
            warn.append(f"plugins: {name!r} has no equivalent yet — {PLUGIN_GAPS[name]}")
        else:
            warn.append(f"plugins: {name!r} is not supported (skipped)")
    if redirects:
        cfg["redirects"] = redirects

    for key in ("extra_css", "extra_javascript"):
        files = []
        for item in raw.get(key) or []:
            rel = str(item.get("path", "")) if isinstance(item, dict) else str(item)
            if rel:
                files.append(rel if "://" in rel else f"{docs_dir}/{rel}".removeprefix("./"))
        if files:
            cfg[key] = files

    if raw.get("theme"):
        warn.append("theme: ignored — the look comes from the docs theme (or `--theme`)")
    for key in raw:
        if (
            key
            not in {
                "site_name",
                "site_url",
                "site_description",
                "repo_url",
                "docs_dir",
                "nav",
                "theme",
                "markdown_extensions",
                "plugins",
                "extra_css",
                "extra_javascript",
            }
            | IGNORED_KEYS
        ):
            warn.append(f"{key}: not supported (skipped)")

    if site:
        cfg["site"] = site
    cfg["sources"] = [source]
    return cfg, warn


def docs_toml_text(cfg: dict) -> str:
    """Serialise a docs config dict as ``docs.toml`` (scalars/arrays first, then tables)."""
    from .docsgen import _toml_value  # noqa: PLC0415

    lines = ["# Imported from mkdocs.yml by `epresso import mkdocs`."]
    for key, val in cfg.items():
        if key not in ("site", "sources"):
            lines.append(f"{key} = {_toml_value(val)}")
    if cfg.get("site"):
        lines += ["", "[site]", *(f"{k} = {_toml_value(v)}" for k, v in cfg["site"].items())]
    for src in cfg.get("sources", []):
        lines += ["", "[[sources]]", *(f"{k} = {_toml_value(v)}" for k, v in src.items())]
    return "\n".join(lines) + "\n"
