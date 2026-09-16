"""epresso CLI — a thin client over the epresso Python API."""

from __future__ import annotations

import sys
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


# -- project templates (`epresso new`) --------------------------------------
# key -> menu label; the dict order is the prompt order.
TEMPLATES: dict[str, str] = {
    "basic": "A basic, helpful starter project",
    "blog": "Use the blog template",
    "docs": "Use the docs template",
    "minimal": "Use the minimal (empty) template",
}
DEFAULT_TEMPLATE = "basic"


def _scaffold_basic(root: Path) -> None:
    """The default project: dirs, site.toml, a page + Base layout."""
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    for d in ("content", "pages", "layouts", "components", "styles", "public"):
        (root / d).mkdir(exist_ok=True)

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


def _scaffold_minimal(root: Path) -> None:
    """The smallest buildable project: site.toml + one bare page."""
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "pages").mkdir(exist_ok=True)
    site_toml = root / "site.toml"
    if not site_toml.exists():
        site_toml.write_text(
            '[site]\nname = "My Site"\nurl = "http://localhost:4321"\n\n[build]\noutput = "dist"\n',
            encoding="utf-8",
        )
    index_ep = root / "pages" / "index.ep"
    if not index_ep.exists():
        index_ep.write_text("---\n---\n<h1>Hello, epresso!</h1>\n", encoding="utf-8")


def _is_interactive() -> bool:
    """Whether both stdin and stdout are a terminal (only then prompt)."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def _prompt_dest(default: str = ".") -> Path:
    return Path(typer.prompt("Where should we create your new project?", default=default))


def _prompt_template() -> str:
    keys = list(TEMPLATES)
    typer.echo("How would you like to start your new project?")
    for i, key in enumerate(keys, 1):
        suffix = " (recommended)" if key == DEFAULT_TEMPLATE else ""
        typer.echo(f"  {i}. {TEMPLATES[key]}{suffix}")
    while True:
        raw = typer.prompt("Choice", default="1").strip()
        if raw in TEMPLATES:
            return raw
        if raw.isdigit() and 1 <= int(raw) <= len(keys):
            return keys[int(raw) - 1]
        typer.secho("Choose one of the numbers above.", fg=typer.colors.YELLOW, err=True)


def _scaffold(template: str, dest: Path) -> str:
    """Scaffold ``template`` at ``dest`` (a template key, theme, URL, or path)."""
    if template == "basic":
        _scaffold_basic(dest)
        return f"Created a basic project in {dest.resolve()}"
    if template == "minimal":
        _scaffold_minimal(dest)
        return f"Created a minimal project in {dest.resolve()}"
    return themes.scaffold(template, dest)


@app.command()
def init(root: Path = typer.Argument(".", help="Project directory")) -> None:
    """Scaffold a new epresso project."""
    _scaffold_basic(root)
    typer.echo(f"✅ Created epresso project in {root.resolve()}")
    typer.echo("   Run `epresso build` to build, or `epresso dev` to preview.")


@app.command()
def new(
    template: str | None = typer.Argument(
        None,
        help="Template (" + ", ".join(TEMPLATES) + "), a theme name, a git URL, or a directory path",
    ),
    dest: Path | None = typer.Argument(None, help="Destination directory (prompted when omitted)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip prompts: basic template, current directory"),
) -> None:
    """Scaffold a new project (interactive when template/destination are omitted)."""
    interactive = _is_interactive() and not yes
    if template is None:
        if not interactive:
            if not yes:
                typer.secho(
                    "no template given; pass a template/URL/path, or use -y for the basic starter",
                    fg=typer.colors.RED,
                    err=True,
                )
                raise typer.Exit(1)
            template = DEFAULT_TEMPLATE
        else:
            if dest is None:
                dest = _prompt_dest()
            template = _prompt_template()
    if dest is None:
        if interactive:
            dest = _prompt_dest()
        elif yes:
            dest = Path(".")
        else:
            typer.secho("destination required; pass a directory or use -y", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)

    try:
        msg = _scaffold(template, dest)
    except (KeyError, FileNotFoundError) as e:
        typer.secho(str(e), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from e
    typer.echo(f"✅ {msg}")
    typer.echo("   Run `epresso build` to build, or `epresso dev` to preview.")


def _resolve_env(cli_env: str | None, command_default: str) -> str:
    """Effective env: explicit --env > EPRESSO_ENV > command default."""
    import os

    return cli_env or os.environ.get("EPRESSO_ENV") or command_default


def _frame_label(code: Any) -> str:
    """Human label for one cProfile frame: ``path:line(name)``, or the raw
    string for builtins (which cProfile reports by name, not as a code object)."""
    if isinstance(code, str):
        return code
    try:
        where = Path(code.co_filename).relative_to(Path.cwd())
    except ValueError:
        where = Path(code.co_filename).name
    return f"{where}:{code.co_firstlineno}({code.co_name})"


def _print_profile(prof: Any, out: Path, top: int = 20) -> None:
    """Print the hottest frames from a :class:`cProfile.Profile`, by self time.

    Self time (not cumulative) is what you want first: it points at the code
    actually burning CPU, instead of the entry point that called it. The full
    stats go to ``out`` for ``python -m pstats``.

    ``getstats()`` returns ``_lsprof.profiler_entry`` records — note the field is
    ``inlinetime`` (self) vs ``totaltime`` (cumulative); the older
    ``(func, (cc, nc, tt, ct, callers))`` tuple shape is gone. One record is the
    profiler's own enable/disable bookkeeping and is filtered out.
    """
    rows = []
    for entry in prof.getstats():
        label = _frame_label(entry.code)
        if "_lsprof" in label:
            continue
        rows.append((entry.inlinetime, entry.callcount, label))
    total = sum(tt for tt, _calls, _label in rows) or 1.0
    rows.sort(reverse=True)
    typer.echo(f"\n\u2500\u2500 profile (top {top} by self time) \u2500\u2500")
    typer.echo(f"  {'ms':>9}  {'%':>5}  {'calls':>9}  function")
    for tt, calls, label in rows[:top]:
        typer.echo(f"  {tt * 1000:9.1f}  {tt / total * 100:5.1f}  {calls:9d}  {label}")
    typer.echo(f"\n  full stats \u2192 {out}")
    typer.echo(f"  inspect with: python -m pstats {out}")


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


def _join_base(main: str, section: str) -> str:
    parts = [p for p in ((main or "").strip("/"), (section or "").strip("/")) if p]
    return "/" + "/".join(parts) + "/" if parts else "/"


def _build_docs_sections(site: Site) -> None:
    """Build each ``[docs]`` section into ``<dist>/<out>`` with its base."""
    import os
    import shutil

    sections = site.config.docs
    if not sections:
        return
    from .docsgen import auto_docs_project

    out_dir = site.config.dir_output()
    for sec in sections:
        src = (site.config.root / sec.source).resolve()
        if not src.is_dir():
            log.error(f"docs section source not found: {src}")
            raise typer.Exit(1)
        eff_base = _join_base(site.config.build.base, sec.base)
        out = sec.out or sec.base.strip("/")
        prev = os.environ.get("EPRESSO_BASE")
        os.environ["EPRESSO_BASE"] = eff_base
        try:
            if (src / "site.toml").is_file():
                child = Site.load(src, env=site.config.env)
            else:
                theme = (
                    Path(sec.theme)
                    if sec.theme
                    else Path(__file__).resolve().parent.parent.parent / "themes" / "docs"
                )
                tmp = Path(auto_docs_project(src, DEFAULT_PORT, theme))
                child = Site.load(tmp, env=site.config.env)
            child.build()
            target = out_dir / out
            if target.exists():
                shutil.rmtree(target)
            target.mkdir(parents=True, exist_ok=True)
            for item in child.config.dir_output().iterdir():
                if item.is_dir():
                    shutil.copytree(item, target / item.name)
                else:
                    shutil.copy2(item, target / item.name)
            log.info(f"  ✓ docs {sec.base} → {target}")
        finally:
            if prev is None:
                os.environ.pop("EPRESSO_BASE", None)
            else:
                os.environ["EPRESSO_BASE"] = prev


@app.command()
def build(
    root: Path = typer.Argument(".", help="Project directory"),
    clean: bool = typer.Option(True, help="Clean dist before building"),
    env: str | None = typer.Option(None, help="Environment (loads site.<env>.toml + .env.<env>)"),
    perf: bool = typer.Option(False, "--perf", help="Print detailed build-phase timings"),
    profile: bool = typer.Option(False, "--profile", help="Run the build under cProfile and print the hottest frames"),
    profile_out: Path = typer.Option(
        Path("epresso-profile.pstats"), "--profile-out", help="Where --profile writes its stats file"
    ),
) -> None:
    """Build the site into dist/."""
    _start = time.monotonic()
    prof: Any = None

    def _load_and_build() -> Any:
        site = Site.load(root, env=_resolve_env(env, "production"))
        return site, site.build(clean=clean, progress=_make_progress())

    try:
        if profile:
            import cProfile

            prof = cProfile.Profile()
            site, result = prof.runcall(_load_and_build)
        else:
            site, result = _load_and_build()
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
    _build_docs_sections(site)
    if perf:
        _print_perf(result)
    if prof is not None:
        profile_out.parent.mkdir(parents=True, exist_ok=True)
        prof.dump_stats(profile_out)
        _print_profile(prof, profile_out)


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

    log.info(f"🚀 Development server for {root.resolve()} (env: {site.config.env or 'default'})…")
    resolved = find_free_port(host, port)
    if resolved != port:
        log.warn(f"⚠️ Port {port} is busy → using {resolved}")
    log.info(f"📚 Serving dev server at http://{host}:{resolved}")
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
    out: Path | None = typer.Option(None, "--out", help="Write a static production build to this directory instead of serving"),
) -> None:
    """Build the documentation; serve it (default port 4321) or write it with --out."""
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

    if out is not None:
        import shutil as _sh

        src = site.config.dir_output()
        out = out.resolve()
        if out.exists():
            _sh.rmtree(out)
        _sh.copytree(src, out)
        _status(perf, _start, f"✅ Built docs → {out}")
        return
    _status(perf, _start, "✅ Docs ready, starting server…")
    if perf:
        _print_perf(result)
    resolved = find_free_port(host, port)
    if resolved != port:
        log.warn(f"⚠️ Port {port} is busy → using {resolved}")
    _status(perf, _start, f"📚 Serving docs at http://{host}:{resolved}")
    serve_dist(site.config.dir_output(), host=host, port=resolved, site=site)


@app.command()
def serve(
    root: Path = typer.Argument(".", help="Project directory"),
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(DEFAULT_PORT, help="Preferred port; the next free port is used if busy"),
) -> None:
    """Serve an already-built dist/ directory (no build)."""
    from .config import load_config
    from .server import find_free_port, serve_dist

    dist = load_config(root).dir_output()
    if not dist.is_dir():
        log.error(f"no built site at {dist} — run `epresso build` first")
        raise typer.Exit(1)
    resolved = find_free_port(host, port)
    if resolved != port:
        log.warn(f"⚠️ Port {port} is busy → using {resolved}")
    log.info(f"📚 Serving dist at http://{host}:{resolved}")
    serve_dist(dist, host=host, port=resolved)


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
def layers(
    root: Path = typer.Argument(".", help="Project directory"),
    env: str | None = typer.Option(None, help="Environment (loads site.<env>.toml + .env.<env>)"),
) -> None:
    """List the external component/layout layers resolved from site.toml."""
    from .config import load_config
    from .layers import resolve_layers

    try:
        cfg = load_config(root, env=_resolve_env(env, "production"))
        resolved = resolve_layers(cfg)
    except EpressoError as e:
        log.error(str(e))
        raise typer.Exit(1) from e
    if not resolved:
        typer.echo("No layers (add [layers] use = [...] to site.toml).")
        return
    typer.echo("Layers (the site's own components/ + layouts/ win; then these in order):")
    for layer in resolved:
        ref = f"@{layer.ref}" if layer.ref else ""
        typer.echo(f"  {layer.kind:<5} {layer.source}{ref}\n        → {layer.root}")


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
def lsp() -> None:
    """Run the .ep Language Server (diagnostics + formatting) over stdio."""
    from . import lsp as _lsp

    raise typer.Exit(_lsp.serve())


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
    expand: bool = typer.Option(
        False,
        "--expand",
        help="Reflow the body: one child per line for markup-only elements, Jinja blocks spread, lone {{ … }} on its own line.",
    ),
    stdin: bool = typer.Option(
        False,
        "--stdin",
        help="Read one .ep source from stdin and write the formatted result to stdout (for editor integrations).",
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

    if stdin:
        if check:
            typer.secho("epresso fmt --stdin cannot be combined with --check", fg=typer.colors.RED, err=True)
            raise typer.Exit(2)
        src = sys.stdin.read()
        out = _fmt.format_full(src, expand=expand or full) if full else _fmt.format_text(src, expand=expand)
        typer.echo(out, nl=False)
        return

    targets = paths if paths else [Path(".")]
    files: list[Path] = []
    seen: set[Path] = set()
    for t in targets:
        t = Path(t)
        if t.is_dir():
            # rglob("*.ep") also matches the `.ep/` dev-cache *directory*.
            candidates = sorted(p for p in t.rglob("*.ep") if p.is_file() and not _ignored_dir(p))
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
            did, kind = _fmt.format_file(f, write=not check, full=full, expand=expand or full)
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


def dev_server() -> None:
    """Console-script alias: serve the project in the current directory.

    Lets a theme project run ``uv run --project <epresso> dev`` instead of
    spelling out the ``epresso`` subcommand.
    """
    sys.argv = [sys.argv[0], "dev", "."]
    app()
