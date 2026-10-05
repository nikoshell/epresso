"""Bundled epresso plugin: social cards (``og:image`` PNGs, 1200×630).

Enable it from ``site.toml`` (the docs theme does)::

    plugins = ["epresso_social"]

    [plugin.epresso_social]
    cards = "sections"        # "sections" (default) | "all" | "collection"
    background = "#0f1117"    # card colours
    color = "#e8ecf1"
    accent = "#3ecf8e"
    logo = "logo.png"         # PNG (an SVG logo is skipped: the site name shows instead)
    background_image = ""     # PNG drawn under the text
    font = ""                 # .ttf/.otf/.woff2 (default: Space Grotesk + IBM Plex Sans)
    dev = false               # also draw cards in dev / non-production builds

    [plugin.epresso_social.titles]   # "collection" mode: card titles per collection
    docs = "Documentation"

After render, every HTML page gets ``og:image`` / ``twitter:image`` pointing at
``/social/<key>.png`` (and ``twitter:card = summary_large_image``). Pages that
set their own image keep it. ``sections`` draws one card per top-level URL
segment (titled by that section's landing page), ``collection`` one per content
collection, ``all`` one per page; the homepage and plain pages get the site card.
Cards are drawn with Pillow (``pip install 'epresso[images]'``) and cached in
``.cache/social/``; without Pillow the plugin warns once and changes nothing.
"""

from __future__ import annotations

import hashlib
import html as _html
import re
from pathlib import Path
from typing import Any

from epresso.plugins import Plugin

VERSION = "1"
W, H = 1200, 630
PAD = 80
MODES = {"sections", "all", "collection"}
DEFAULTS = {"background": "#0f1117", "color": "#e8ecf1", "accent": "#3ecf8e"}

_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
_DESC = re.compile(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', re.I)
_OG_IMAGE = re.compile(r'<meta[^>]+property="og:image"[^>]+content="([^"]*)"[^>]*>', re.I)
_TW_IMAGE = re.compile(r'<meta[^>]+name="twitter:image"[^>]*>\s*', re.I)
_TW_CARD = re.compile(r'<meta[^>]+name="twitter:card"[^>]*>\s*', re.I)


def _has_pillow() -> bool:
    try:
        import PIL  # noqa: F401, PLC0415

        return True
    except ImportError:
        return False


def _fonts_dir() -> Path | None:
    from epresso.themes import bundled_docs_theme  # noqa: PLC0415

    d = bundled_docs_theme() / "public" / "docs-theme" / "fonts"
    return d if d.is_dir() else None


def _font(path: str | Path | None, size: int, weight: int = 400):
    from PIL import ImageFont  # noqa: PLC0415

    if path:
        try:
            font = ImageFont.truetype(str(path), size)
        except OSError:
            return ImageFont.load_default(size)
        try:  # variable fonts (the bundled ones) start at their lightest weight
            axes = font.get_variation_axes()
            font.set_variation_by_axes(
                [float(max(a["minimum"] or 0, min(a["maximum"] or weight, weight))) for a in axes]
            )
        except OSError:
            pass  # a static font
        return font
    return ImageFont.load_default(size)


def _wrap(draw, text: str, font, width: int, max_lines: int) -> tuple[list[str], bool]:
    """Greedy word wrap; returns (lines, truncated)."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines[:max_lines], len(lines) > max_lines


def _ellipsize(draw, line: str, font, width: int) -> str:
    while line and draw.textlength(line + "…", font=font) > width:
        line = line[:-1].rstrip()
    return line + "…"


def draw_card(title: str, description: str, site_name: str, opts: dict[str, Any], root: Path) -> bytes:
    """Draw one 1200×630 PNG card and return its bytes."""
    import io  # noqa: PLC0415

    from PIL import Image, ImageDraw  # noqa: PLC0415

    bg, fg, accent = (str(opts.get(k) or v) for k, v in DEFAULTS.items())
    img = Image.new("RGB", (W, H), bg)
    if opts.get("background_image"):
        try:
            under = Image.open(root / str(opts["background_image"])).convert("RGB")
            img.paste(under.resize((W, H)))
        except OSError:
            pass
    draw = ImageDraw.Draw(img)
    fonts = _fonts_dir()
    head_font = opts.get("font") and root / str(opts["font"]) or (fonts and fonts / "SpaceGrotesk.woff2")
    body_font = opts.get("font") and root / str(opts["font"]) or (fonts and fonts / "IBMPlexSans.woff2")
    inner = W - 2 * PAD

    # top: logo (PNG) + site name
    x = PAD
    logo = str(opts.get("logo") or "")
    if logo.lower().endswith(".png") and (root / logo.lstrip("/")).is_file():
        mark = Image.open(root / logo.lstrip("/")).convert("RGBA")
        mark.thumbnail((64, 64))
        img.paste(mark, (PAD, PAD), mark)
        x += mark.width + 20
    draw.text((x, PAD + 32), site_name, font=_font(head_font, 34, 600), fill=accent, anchor="lm")

    # title: largest size that fits in 3 lines
    title = title or site_name
    for size in (76, 68, 60, 52, 46):
        tf = _font(head_font, size, 700)
        lines, cut = _wrap(draw, title, tf, inner, 3)
        if not cut:
            break
    if cut:
        lines[-1] = _ellipsize(draw, lines[-1], tf, inner)
    y = 210
    for line in lines:
        draw.text((PAD, y), line, font=tf, fill=fg)
        y += int(size * 1.15)

    # description: 2 lines, ellipsis
    if description:
        df = _font(body_font, 30)
        dlines, cut = _wrap(draw, description, df, inner, 2)
        if cut:
            dlines[-1] = _ellipsize(draw, dlines[-1], df, inner)
        y += 24
        for line in dlines:
            draw.text((PAD, y), line, font=df, fill=fg)
            y += 42

    draw.rectangle((0, H - 12, W, H), fill=accent)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def _slug(key: str) -> str:
    return re.sub(r"[^a-z0-9/]+", "-", key.lower()).strip("-/").replace("/", "--") or "site"


class _Social:
    """Per-build state: which card each page uses, and what each card says."""

    def __init__(self, caps) -> None:
        self.caps = caps
        self.site = caps.site
        self.opts = dict(caps.options)
        mode = str(self.opts.get("cards", "sections"))
        if mode not in MODES:
            from epresso.errors import PluginError  # noqa: PLC0415

            raise PluginError(f"epresso_social: cards = {mode!r} (use one of {', '.join(sorted(MODES))})")
        self.mode = mode
        self.cards: dict[str, dict[str, str]] = {}  # slug -> {title, description}
        self.landing: dict[str, dict[str, str]] = {}  # section -> landing page title/desc
        self._collection_of: dict[int, str] | None = None
        docs = self.site.config.plugin.get("epresso_docs", {})
        self.base = str(docs.get("base", "")).strip("/")

    # -- card selection ----------------------------------------------------
    def _collection(self, data: Any) -> str:
        if data is None:
            return ""
        if self._collection_of is None:
            self._collection_of = {id(e): name for name, col in self.site.store.collections.items() for e in col.all()}
        return self._collection_of.get(id(data), "")

    def _section(self, path: str) -> str:
        parts = [p for p in path.strip("/").split("/") if p]
        if self.base and parts[:1] == [self.base]:
            parts = parts[1:]
        return parts[0] if parts else ""

    def key_for(self, path: str, title: str, desc: str, data: Any) -> tuple[str, dict[str, str]]:
        site = self.site.config.site
        site_card = {"title": site.name, "description": site.description or ""}
        if self.mode == "all":
            return _slug(path), {"title": title, "description": desc}
        if self.mode == "collection":
            name = self._collection(data)
            if not name:
                return "site", site_card
            titles = self.opts.get("titles") or {}
            return _slug(name), {"title": str(titles.get(name) or name.replace("-", " ").title()), "description": ""}
        sec = self._section(path)
        if not sec:
            return "site", site_card
        if path.strip("/").split("/")[-1] == sec:  # the section's own landing page
            self.landing[sec] = {"title": title, "description": desc}
        return _slug(sec), {"title": sec.replace("-", " ").title(), "description": "", "section": sec}

    # -- html transform ----------------------------------------------------
    def transform(self, html: str, ctx: dict[str, Any]) -> str:
        if "</head>" not in html or ctx.get("path", "").startswith("/404"):
            return html
        site_url = (self.site.config.site.url or "").rstrip("/")
        theme_og = str((self.site.config.theme or {}).get("og_image") or "")
        og = _OG_IMAGE.search(html)
        if og and (not theme_og or not og.group(1).endswith(theme_og.lstrip("/"))):
            return html  # the page set its own image
        tm = _TITLE.search(html)
        title = _html.unescape(tm.group(1)).strip() if tm else ""
        name = self.site.config.site.name
        title = re.sub(rf"\s*[·|–-]\s*{re.escape(name)}\s*$", "", title) if name else title
        dm = _DESC.search(html)
        desc = _html.unescape(dm.group(1)) if dm else ""
        slug, card = self.key_for(ctx.get("path", "/"), title, desc, ctx.get("data"))
        self.cards.setdefault(slug, card)
        url = f"{site_url}/social/{slug}.png"
        tags = (
            f'<meta property="og:image" content="{url}">'
            f'<meta property="og:image:width" content="{W}"><meta property="og:image:height" content="{H}">'
            f'<meta name="twitter:card" content="summary_large_image">'
            f'<meta name="twitter:image" content="{url}">'
        )
        html = _OG_IMAGE.sub("", html, count=1) if og else html
        html = _TW_IMAGE.sub("", html)
        html = _TW_CARD.sub("", html)
        return html.replace("</head>", tags + "</head>", 1)

    # -- drawing -------------------------------------------------------------
    def write(self) -> int:
        out = self.site.config.dir_output() / "social"
        cache = self.site.config.cache_dir() / "social"
        out.mkdir(parents=True, exist_ok=True)
        cache.mkdir(parents=True, exist_ok=True)
        root = self.site.config.root
        name = self.site.config.site.name
        opts = {**self.opts, "logo": self.opts.get("logo") or (self.site.config.theme or {}).get("logo", "")}
        for slug, card in self.cards.items():
            sec = card.get("section")
            if sec and sec in self.landing:
                card = {**card, **self.landing[sec]}
            payload = repr((VERSION, card.get("title"), card.get("description"), name, sorted(opts.items())))
            cached = cache / (hashlib.sha256(payload.encode()).hexdigest()[:20] + ".png")
            if not cached.is_file():
                cached.write_bytes(draw_card(card["title"], card["description"], name, opts, root))
            (out / f"{slug}.png").write_bytes(cached.read_bytes())
        return len(self.cards)


def epresso_social() -> Plugin:
    """Return the ``Plugin`` that adds social-card ``og:image`` PNGs."""
    state: dict[str, _Social] = {}
    warned = [False]

    def _drawing(caps) -> bool:
        return caps.site._production or bool(caps.options.get("dev"))

    def on_setup(caps):
        if not _has_pillow():
            if not warned[0]:
                caps.logger.warn("Pillow is not installed — no social cards (pip install 'epresso[images]')")
                warned[0] = True
            return
        state["s"] = _Social(caps)
        caps.transform_html(lambda html, ctx: state["s"].transform(html, ctx))

    def before_build(caps):
        if "s" in state:
            state["s"].cards.clear()
            state["s"].landing.clear()
            state["s"]._collection_of = None

    def after_build(caps, result):
        s = state.get("s")
        if s is None or not s.cards:
            return
        if not _drawing(caps):
            return
        n = s.write()
        caps.logger.info(f"social cards: {n}")

    return Plugin(
        name="epresso_social",
        hooks={"on_setup": on_setup, "before_build": before_build, "after_build": after_build},
    )


# Module-level instance so ``plugins = ["epresso_social"]`` auto-discovers it.
social = epresso_social()
