"""epresso CLI — a thin client over the epresso Python API."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import typer

from . import __version__, themes
from .deploy import PROVIDERS
from .errors import EpressoError
from .logger import get_logger
from .server import DEFAULT_PORT
from .site import Site

app = typer.Typer(help="epresso — a modern, Python-first static site generator.", no_args_is_help=True)
log = get_logger("cli")


@app.command()
def version() -> None:
    """Print the epresso version."""
    typer.echo(f"epresso {__version__}")


@app.command()
def init(root: Path = typer.Argument(".", help="Project directory")) -> None:
    """Scaffold a new epresso project."""
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "content").mkdir(exist_ok=True)
    (root / "pages").mkdir(exist_ok=True)
    (root / "layouts").mkdir(exist_ok=True)
    (root / "components").mkdir(exist_ok=True)
    (root / "styles").mkdir(exist_ok=True)
    (root / "public").mkdir(exist_ok=True)

    site_toml = root / "site.toml"
    if not site_toml.exists():
        site_toml.write_text(
            '[site]\nname = "My Site"\nurl = "http://localhost:4321"\n\n'
            '[build]\noutput = "dist"\ntrailing_slash = "always"\n',
            encoding="utf-8",
        )

    index_ep = root / "pages" / "index.ep"
    if not index_ep.exists():
        index_ep.write_text(
            '---\n---\n<Base title={site.config.site.name}>\n<h1>Hello, epresso!</h1>\n<p>This is your first page.</p>\n</Base>\n',
            encoding="utf-8",
        )

    base_ep = root / "layouts" / "Base.ep"
    if not base_ep.exists():
        base_ep.write_text(
            '---\n---\n<!doctype html><html lang="{{ site.config.site.language }}"><head>'
            '<meta charset="utf-8"><title>{{ props.title }}</title></head>'
            "<body><main><slot/></main></body></html>\n",
            encoding="utf-8",
        )

    content_config = root / "content.config.py"
    if not content_config.exists():
        content_config.write_text(
            "# Define content collections here, e.g.\n"
            "# from epresso.content import define_collection\n"
            "# from pydantic import BaseModel\n"
            "# class Post(BaseModel):\n"
            "#     title: str\n"
            "#     date: str\n"
            '# posts = define_collection("posts", glob="*.md", base="./content/posts", schema=Post)\n',
            encoding="utf-8",
        )

    typer.echo(f"✅ Created epresso project in {root}")
    typer.echo("   Run `epresso build` to build, or `epresso dev` to preview.")


@app.command()
def new(
    theme: str = typer.Argument(..., help="Theme name: " + ", ".join(themes.list_themes())),
    dest: Path = typer.Argument(..., help="Destination directory"),
) -> None:
    """Scaffold a new project from a theme (git-clone or bundled starter)."""
    try:
        msg = themes.scaffold(theme, dest)
    except (KeyError, FileNotFoundError) as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e
    typer.echo(f"✅ {msg}")
    typer.echo("   Run `epresso build` to build, or `epresso dev` to preview.")


def _resolve_env(cli_env: str | None, command_default: str) -> str:
    """Effective env: explicit --env > EPRESSO_ENV > command default."""
    import os

    return cli_env or os.environ.get("EPRESSO_ENV") or command_default


def _print_perf(result: Any) -> None:
    """Print detailed build-phase timings when ``--perf`` is set."""
    total = result.duration or 1.0
    typer.echo("\n── perf ──")
    for name, secs in sorted(result.perf.items(), key=lambda kv: -kv[1]):
        typer.echo(f"  {name:<16} {secs * 1000:8.1f} ms  ({secs / total * 100:5.1f}%)")
    typer.echo(f"  {'total':<16} {total * 1000:8.1f} ms")
    if result.skipped:
        typer.echo(f"  ({result.skipped} pages served from cache)")


_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


def _make_progress() -> Any:
    """Return a throttled progress callback for the build render loop, or ``None``
    when stdout isn't a terminal (so piped output stays clean).

    an animated spinner combined with a rendered-page count, redrawn in
    place on a single line and cleared by :func:`_end_progress`.
    """
    import sys
    import time

    if not sys.stdout.isatty():
        return None
    last = [0.0]
    idx = [0]

    def cb(done: int, total: int, path: str) -> None:
        now = time.monotonic()
        if now - last[0] < 0.1:
            return
        last[0] = now
        frame = _FRAMES[idx[0] % len(_FRAMES)]
        idx[0] += 1
        sys.stdout.write(f"\r\x1b[K{frame} Rendering {done}/{total}…")
        sys.stdout.flush()

    return cb


def _end_progress() -> None:
    import sys

    if sys.stdout.isatty():
        sys.stdout.write("\r\x1b[K")
        sys.stdout.flush()


def _status(perf: bool, start: float, msg: str) -> None:
    """Echo ``msg`` as an info log, with an elapsed-time prefix when ``--perf``."""
    if perf:
        log.info(f"[{time.monotonic() - start:7.2f}s] {msg}")
    else:
        log.info(msg)


@app.command()
def build(
    root: Path = typer.Argument(".", help="Project directory"),
    clean: bool = typer.Option(True, help="Clean dist before building"),
    env: str | None = typer.Option(None, help="Environment (loads site.<env>.toml + .env.<env>)"),
    perf: bool = typer.Option(False, "--perf", help="Print detailed build-phase timings"),
) -> None:
    """Build the site into dist/."""
    _start = time.monotonic()
    try:
        site = Site.load(root, env=_resolve_env(env, "production"))
        result = site.build(clean=clean, progress=_make_progress())
        _end_progress()
    except EpressoError as e:
        log.error(str(e))
        raise typer.Exit(1) from e
    _status(
        perf,
        _start,
        f"✅ Built {len(result.pages)} pages, {len(result.endpoints)} endpoints "
        f"({result.skipped} cached) from {result.collections} collections "
        f"({result.entries} entries) in {result.duration:.2f}s → {site.config.dir_output()}",
    )
    for w in result.asset_warnings:
        log.warn(f"⚠️ {w}")
    if perf:
        _print_perf(result)


@app.command()
def dev(
    root: Path = typer.Argument(".", help="Project directory"),
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(DEFAULT_PORT, help="Preferred port; the next free port is used if busy"),
    env: str | None = typer.Option(None, help="Environment (loads site.<env>.toml + .env.<env>)"),
) -> None:
    """Run the development server with live reload."""
    try:
        site = Site.load(root, env=_resolve_env(env, "development"))
    except EpressoError as e:
        log.error(str(e))
        raise typer.Exit(1) from e
    from .server import DevServer, find_free_port

    resolved = find_free_port(host, port)
    if resolved != port:
        log.warn(f"⚠️ Port {port} is busy → using {resolved}")
    DevServer(site, host, resolved).run()


@app.command()
def preview(
    root: Path = typer.Argument(".", help="Project directory"),
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(DEFAULT_PORT, help="Preferred port; the next free port is used if busy"),
    env: str | None = typer.Option(None, help="Environment (loads site.<env>.toml + .env.<env>)"),
) -> None:
    """Build then serve the static dist/ output (production preview)."""
    from .server import find_free_port, serve_dist

    site = Site.load(root, env=_resolve_env(env, "production"))
    site.build(progress=_make_progress())
    _end_progress()
    resolved = find_free_port(host, port)
    if resolved != port:
        log.warn(f"⚠️ Port {port} is busy → using {resolved}")
    serve_dist(site.config.dir_output(), host=host, port=resolved, site=site)


@app.command()
def docs(
    root: Path = typer.Argument(None, help="Docs project directory (default: the bundled docs example)"),
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(DEFAULT_PORT, help="Port to serve the docs on"),
    theme: Path | None = typer.Option(None, help="Theme project for bare Markdown (default: the bundled docs theme)"),
    env: str | None = typer.Option(None, help="Environment (loads site.<env>.toml + .env.<env>)"),
    perf: bool = typer.Option(False, "--perf", help="Print detailed build-phase timings"),
) -> None:
    """Build and serve the documentation (default port 4321)."""
    from .docsgen import auto_docs_project  # noqa: PLC0415  (lazy import)

    _start = time.monotonic()
    if root is None:
        root = Path(__file__).resolve().parent.parent.parent / "themes" / "docs"
    root = root.resolve()
    if not (root / "site.toml").exists():
        if root.is_dir():
            # Bare Markdown directory → render with the docs theme (bundled by default).
            if theme is None:
                theme = Path(__file__).resolve().parent.parent.parent / "themes" / "docs"
            _status(perf, _start, f"📖 Rendering docs from {root} with theme {theme}…")
            root = auto_docs_project(root, port, theme)
        else:
            typer.secho(
                f"no docs project at {root} (pass a root, e.g. `epresso docs ./themes/docs`)",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(1)
    from .server import find_free_port, serve_dist

    try:
        site = Site.load(root, env=_resolve_env(env, "production"))
        result = site.build(progress=_make_progress())
        _end_progress()
    except EpressoError as e:
        log.error(str(e))
        raise typer.Exit(1) from e
    _status(perf, _start, "✅ Docs ready, starting server…")
    if perf:
        _print_perf(result)
    resolved = find_free_port(host, port)
    if resolved != port:
        log.warn(f"⚠️ Port {port} is busy → using {resolved}")
    _status(perf, _start, f"📚 Serving docs at http://{host}:{resolved}")
    serve_dist(site.config.dir_output(), host=host, port=resolved, site=site)


@app.command()
def clean(root: Path = typer.Argument(".", help="Project directory")) -> None:
    """Remove the dist/ output and the .cache build cache."""
    from .config import load_config

    cfg = load_config(root)
    removed = False
    out = cfg.dir_output()
    if out.exists():
        shutil_rmtree(out)
        typer.echo(f"Removed {out}")
        removed = True
    cache = cfg.cache_dir()
    if cache.exists():
        shutil_rmtree(cache)
        typer.echo(f"Removed {cache}")
        removed = True
    if not removed:
        typer.echo("Nothing to clean.")


@app.command()
def check(
    root: Path = typer.Argument(".", help="Project directory"),
    env: str | None = typer.Option(None, help="Environment (loads site.<env>.toml + .env.<env>)"),
) -> None:
    """Validate configuration and content; report a summary."""
    try:
        site = Site.load(root, env=_resolve_env(env, "production"))
        routes = site.resolve_routes()
    except EpressoError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e
    typer.echo(f"Collections: {len(site.store.names())}")
    for name in site.store.names():
        typer.echo(f"  {name}: {len(site.store.get_collection(name))} entries")
    typer.echo(f"Routes: {len(routes)}")
    for r in routes:
        typer.echo(f"  {r.path}")
    typer.echo("✅ OK")


@app.command()
def fmt(
    paths: list[Path] = typer.Argument(
        None, help="Files/dirs to format (.ep). Default: current directory (recursive)."
    ),
    check: bool = typer.Option(
        False, "--check", "-c", help="Report files that would change without writing; exit 1 if any."
    ),
    full: bool = typer.Option(
        False, "--full", help="Also format section contents (frontmatter/HTML/CSS/JS). Requires epresso[fmt]."
    ),
) -> None:
    """Format .ep files to the canonical section structure (body → script → style)."""
    from . import fmt as _fmt

    if full and not _fmt._deep_available():
        typer.secho(
            "epresso fmt --full needs the optional formatters, which are not installed.\n"
            "  pip install -e \".[fmt]\"      (or for uv projects: uv sync --extra fmt)\n"
            "Installs: ruff, djhtml, cssbeautifier, jsbeautifier.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    targets = paths if paths else [Path(".")]
    files: list[Path] = []
    seen: set[Path] = set()
    for t in targets:
        t = Path(t)
        if t.is_dir():
            candidates = sorted(p for p in t.rglob("*.ep") if not _ignored_dir(p))
        elif t.suffix == ".ep":
            candidates = [t]
        else:
            typer.secho(f"skip {t} (not a .ep file)", fg=typer.colors.YELLOW, err=True)
            continue
        for p in candidates:
            r = p.resolve()
            if r not in seen:
                seen.add(r)
                files.append(p)

    changed: list[Path] = []
    for f in files:
        try:
            did, kind = _fmt.format_file(f, write=not check, full=full)
        except Exception as e:  # noqa: BLE001
            typer.secho(f"error {f}: {e}", fg=typer.colors.RED, err=True)
            continue
        if did:
            changed.append(f)
            if not check:
                typer.echo(f"formatted {f} ({kind})")

    if check:
        if changed:
            for f in changed:
                typer.echo(f"would format {f}")
            typer.secho(f"{len(changed)} file(s) need formatting", fg=typer.colors.YELLOW, err=True)
            raise typer.Exit(1)
        typer.echo("✅ all .ep files are formatted")
    else:
        typer.echo(f"✅ formatted {len(changed)} file(s)")


def _ignored_dir(path: Path) -> bool:
    """Whether a walk should skip this directory (dependency/build artifacts).
    Underscore-prefixed segments (private/draft) are skipped too."""
    parts = set(path.parts)
    if parts & {".git", "node_modules", ".cache", "dist", "build", "__pycache__", ".venv", "vendor"}:
        return True
    return any(part.startswith("_") for part in path.parts)


@app.command()
def inspect(
    root: Path = typer.Argument(".", help="Project directory"),
    format: str = typer.Option("json", help="Output format: json | dot"),
) -> None:
    """Inspect the build graph (routes + content → route edges)."""
    try:
        site = Site.load(root)
    except EpressoError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e
    if format == "dot":
        typer.echo(site.graph_dot())
    else:
        import json

        typer.echo(json.dumps(site.build_graph(), indent=2))


@app.command()
def deploy(
    root: Path = typer.Argument(".", help="Project directory"),
    provider: str = typer.Option("gh-pages", help="Provider: " + ", ".join(PROVIDERS)),
    remote: str = typer.Option("origin"),
    branch: str = typer.Option("gh-pages"),
    no_push: bool = typer.Option(False, "--no-push", help="Build + commit but do not push"),
) -> None:
    """Build and deploy the site (GitHub Pages by default)."""
    try:
        site = Site.load(root)
    except EpressoError as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e
    try:
        from . import deploy as _deploy

        if provider == "gh-pages":
            msg = _deploy.gh_pages(site, remote=remote, branch=branch, push=not no_push)
        else:
            typer.secho(f"unknown provider {provider!r}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
    except Exception as e:  # noqa: BLE001
        typer.secho(f"deploy failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e
    typer.echo(f"✅ {msg}")


def shutil_rmtree(path: Path) -> None:
    import shutil

    shutil.rmtree(path)


def main() -> None:
    app()
