"""Layers — external component/layout roots from repos, packages or directories.

A layer is a directory shaped like a site root: it contributes ``components/``
and ``layouts/`` (found through the Jinja loader searchpath by
``components._resolve_component_uncached``). Layers are declared in
``site.toml``::

    [layers]
    use = [
      "./vendor/components",                 # directory path
      "pkg:epresso_ui",                      # installed package
      "github:owner/epresso-components@v1",  # repo (tarball, cached)
      "git+https://host/org/repo@main",      # repo (shallow clone, cached)
    ]

The site's own ``components/`` and ``layouts/`` are always searched first, then
layers in declaration order, so a site file with a matching basename overrides a
layer's. Remote sources are fetched once into ``.cache/layers/`` and reused.
"""

from __future__ import annotations

import hashlib
import importlib
import io
import re
import shutil
import subprocess
import tarfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigError
from .themes import _GIT_PREFIXES, _split_ref

_FETCH_TIMEOUT = 60
_MARKER = ".epresso-layer"  # written after a successful fetch (cache validity)


@dataclass(frozen=True)
class Layer:
    """A resolved layer: the declared ``source`` plus the local ``root`` to serve."""

    source: str
    kind: str  # "path" | "pkg" | "repo"
    root: Path
    ref: str | None = None


@dataclass(frozen=True)
class LayerSource:
    raw: str
    kind: str
    value: str  # directory, importable module, or clone URL
    ref: str | None = None


def parse_layer(source: str) -> LayerSource:
    """Classify a ``[layers] use`` entry. Does not touch the filesystem."""
    raw = source.strip()
    if not raw:
        raise ConfigError(
            "empty layer source",
            fix="use a directory path, pkg:<module>, or github:<owner>/<repo>[@ref]",
        )
    if raw.startswith("pkg:"):
        module = raw[4:].strip()
        if not module:
            raise ConfigError("layer source 'pkg:' has no module name")
        return LayerSource(raw, "pkg", module)
    if raw.startswith("path:"):
        path = raw[5:].strip()
        if not path:
            raise ConfigError("layer source 'path:' has no path")
        return LayerSource(raw, "path", path)
    head = raw[4:] if raw.startswith("git+") else raw
    if head.startswith("github:"):
        url = "https://github.com/" + head[len("github:") :]
        url, ref = _split_ref(url)
        return LayerSource(raw, "repo", url, ref)
    if head.startswith(_GIT_PREFIXES):
        url, ref = _split_ref(head)
        return LayerSource(raw, "repo", url, ref)
    return LayerSource(raw, "path", raw)


def resolve_layers(config) -> list[Layer]:
    """Resolve every ``[layers] use`` entry to a local directory (deduped, in order)."""
    layers: list[Layer] = []
    seen: set[Path] = set()
    for source in config.layers.use:
        parsed = parse_layer(source)
        root = _resolve_one(parsed, config.root, config.cache_dir())
        if root in seen:
            continue
        seen.add(root)
        layers.append(Layer(parsed.raw, parsed.kind, root, parsed.ref))
    return layers


def _resolve_one(src: LayerSource, project_root: Path, cache_dir: Path) -> Path:
    if src.kind == "path":
        p = Path(src.value).expanduser()
        p = p.resolve() if p.is_absolute() else (project_root / p).resolve()
        if not p.is_dir():
            raise ConfigError(
                f"layer directory not found: {src.value}",
                path=str(p),
                fix="point at an existing directory, or use github:owner/repo[@ref]",
            )
        return p
    if src.kind == "pkg":
        return _resolve_pkg(src.value)
    return _fetch_repo(src.value, src.ref, cache_dir)


def _resolve_pkg(module: str) -> Path:
    try:
        mod = importlib.import_module(module)
    except Exception as e:  # noqa: BLE001 — any import failure is the user's source
        raise ConfigError(
            f"cannot import layer package {module!r}: {e}",
            fix=f"install it (uv add {module}) or use a path: / repo source",
        ) from e
    location = getattr(mod, "__file__", None)
    if not location:
        raise ConfigError(f"layer package {module!r} has no filesystem location")
    root = Path(location).resolve().parent
    if not (root / "components").is_dir() and not (root / "layouts").is_dir():
        raise ConfigError(
            f"layer package {module!r} has no components/ or layouts/ directory",
            path=str(root),
            fix="a layer package must ship components/ and/or layouts/ next to its __init__",
        )
    return root


def _fetch_repo(url: str, ref: str | None, cache_dir: Path) -> Path:
    ref = ref or "HEAD"
    dest = cache_dir / "layers" / _slug(url, ref)
    if (dest / _MARKER).is_file():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    try:
        if _is_github(url):
            _fetch_tarball(url, ref, tmp)
        else:
            _clone(url, ref, tmp)
        (tmp / _MARKER).write_text(f"{url}@{ref}\n", encoding="utf-8")
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    shutil.rmtree(dest, ignore_errors=True)
    tmp.rename(dest)
    return dest


def _is_github(url: str) -> bool:
    return "github.com/" in url


def _tarball_url(url: str, ref: str) -> str:
    repo = url.split("github.com/", 1)[1].strip("/")
    if repo.endswith(".git"):
        repo = repo[:-4]
    return f"https://github.com/{repo}/archive/{ref}.tar.gz"


def _fetch_tarball(url: str, ref: str, dest: Path) -> None:
    tarball = _tarball_url(url, ref)
    try:
        with urllib.request.urlopen(tarball, timeout=_FETCH_TIMEOUT) as resp:  # noqa: S310
            blob = resp.read()
    except Exception as e:  # noqa: BLE001 — network/HTTP/URL errors are all user-facing
        raise ConfigError(
            f"could not download layer {url}@{ref}: {e}",
            fix="check the URL and ref, or vendor the files and use a path: source",
        ) from e
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tf:
        tf.extractall(dest, filter="data")  # py3.12+: rejects traversal/absolute paths
    _flatten(dest)


def _flatten(dest: Path) -> None:
    """Drop the single ``<repo>-<ref>/`` wrapper a GitHub tarball extracts to."""
    entries = list(dest.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        inner = entries[0]
        for child in list(inner.iterdir()):
            child.rename(dest / child.name)
        inner.rmdir()


def _clone(url: str, ref: str, dest: Path) -> None:
    git = shutil.which("git")
    if not git:
        raise ConfigError(
            f"cannot fetch layer {url!r}: git is not installed",
            fix="install git, or use a github.com URL (fetched as a tarball)",
        )
    cmd = [git, "clone", "--depth=1"]
    if ref != "HEAD":
        cmd += ["--branch", ref]
    cmd += [url, str(dest)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise ConfigError(
            f"could not clone layer {url}@{ref}: {e.stderr.strip() or e}",
            fix="check the URL and ref",
        ) from e
    shutil.rmtree(dest / ".git", ignore_errors=True)


def _slug(url: str, ref: str) -> str:
    base = re.sub(r"^[a-zA-Z]+://", "", url).removesuffix(".git")
    name = re.sub(r"[^A-Za-z0-9._-]+", "__", base)[-60:]
    digest = hashlib.sha256(f"{url}@{ref}".encode()).hexdigest()[:8]
    return f"{name}@{re.sub(r'[^A-Za-z0-9._-]+', '_', ref)}-{digest}"
