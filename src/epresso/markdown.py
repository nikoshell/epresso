"""Markdown rendering + a thin AST pass for headings and image extraction.

Uses markdown-it-py; produces ``RenderedContent`` with ``html`` and metadata
(headings, image_paths) — analogous to other renderers' ``rendered.metadata``.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from markdown_it import MarkdownIt

from .content import store as _store
from .errors import ContentError
from .jsxattrs import parse_jsx_attrs

# Plugin-registered markdown extensions. Pandoc / MkDocs features are opt-in via
# plugins (epresso.plugins); core stays agnostic until a plugin registers a
# source transform / html post-processor.
_MD_SOURCE_TRANSFORMS: list = []
_MD_HTML_POST: list = []


def register_markdown_transform(fn) -> None:
    """Register a source transform ``str -> str`` applied before markdown rendering."""
    _MD_SOURCE_TRANSFORMS.append(fn)


def register_html_transform(fn) -> None:
    """Register an html post-processor ``str -> str`` applied to rendered output."""
    _MD_HTML_POST.append(fn)


def _apply_source_transforms(src: str) -> str:
    for fn in _MD_SOURCE_TRANSFORMS:
        src = fn(src)
    return src


_MD_RENDER_TRANSFORMS: list = []


def register_markdown_render_transform(fn) -> None:
    """Register a render transform ``fn(md, src, depth) -> str`` (markdown-in,
    markdown-with-raw-html out) run before the final render (e.g. content tabs)."""
    _MD_RENDER_TRANSFORMS.append(fn)


def _apply_render_transforms(md, src: str, depth: int) -> str:
    for fn in _MD_RENDER_TRANSFORMS:
        src = fn(md, src, depth)
    return src


def render_fragment(md, src: str, depth: int = 0) -> str:
    """Render a markdown fragment (dedented tab content) through source transforms,
    render transforms (tabs), then markdown-it. Depth guards recursion."""
    src = _apply_source_transforms(src)
    if depth < 12:
        src = _apply_render_transforms(md, src, depth)
    return md.render(src)


def _renderer(config_markdown: Any, component_names: tuple[str, ...] = (), component_renderer=None) -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": True, "linkify": True, "typographer": True})
    md.enable("table")
    # Basic GitHub-ish extensions enabled via commonmark + extras.
    try:
        md.enable("strikethrough")
    except Exception:  # noqa: BLE001
        pass
    # Syntax highlighting for fenced code blocks (Pygments by default).
    if getattr(config_markdown, "highlight", True):
        cc = getattr(config_markdown, "code_component", None) or None
        comps = getattr(config_markdown, "code_components", None) or {}
        if cc or comps:
            md.options["highlight"] = (
                lambda code, lang, attrs: _pygments_highlight(code, lang, attrs, cc, comps)
            )
            # When a code component is set, unwrap markdown-it's auto <pre><code>
            # wrapper so the component owns the code-block markup (markdown-it
            # only returns highlight output bare when it starts with ``<pre``).
            md.renderer.rules["fence"] = _make_component_fence_renderer()  # type: ignore[attr-defined]
        else:
            md.options["highlight"] = _pygments_highlight
    if component_names and component_renderer:
        md.inline.ruler.before("html_inline", "epresso_components", _make_component_rule(component_names))
        # markdown-it RendererProtocol lacks a typed `rules` dict
        md.renderer.rules["md_component"] = _make_component_renderer(component_renderer, md.renderer)  # type: ignore[attr-defined]
        md.renderer.rules["html_block"] = _make_html_block_renderer(component_names, component_renderer, md.renderer)  # type: ignore[attr-defined]
    return md


def _fence_file(attrs: str) -> str:
    """Extract an optional filename from a fenced-code info string.

    Accepts ``title="..."``/``file="..."``/``name="..."`` (quoted or bare), but
    ignores Pandoc class tokens (leading ``.``) so ``{.py .no-copy}`` never reads
    ``.no-copy`` as a filename.
    """
    attrs = (attrs or "").strip()
    if not attrs:
        return ""
    m = re.search(r"(?:title|file|name)=\"?([^\"\s]+)\"?", attrs)
    if m:
        return m.group(1)
    if any(t.startswith(".") for t in attrs.split()) or " " in attrs or "=" in attrs:
        return ""
    return attrs


def _split_code_lines(html: str) -> str:
    """Split Pygments token HTML into per-line ``<span class="code-line">`` blocks.

    Keeps open/close token spans intact across newlines (server-side counterpart
    of the client-side split used by the code-block theme).
    """
    token_re = re.compile(r"(</?[a-zA-Z][^>]*>)|([^<]+)")
    lines: list[str] = [""]
    stack: list[str] = []
    for m in token_re.finditer(html):
        tag, text = m.group(1), m.group(2)
        if tag:
            if tag.startswith("</"):
                if stack:
                    stack.pop()
                lines[-1] += tag
            else:
                stack.append(tag)
                lines[-1] += tag
        elif text:
            parts = text.split("\n")
            for i, part in enumerate(parts):
                lines[-1] += part
                if i < len(parts) - 1:
                    closes = "".join(
                        "</" + t[1:].split(" ")[0].split(">")[0] + ">"
                        for t in reversed(stack)
                    )
                    lines[-1] += closes
                    lines.append("".join(stack))
    return "".join(f'<span class="code-line">{line}</span>' for line in lines)


def _pygments_highlight(
    code: str, lang: str, attrs: str, code_component: str | None = None, code_components: dict[str, str] | None = None
) -> str:
    """Highlight a fenced code block with Pygments; fall back to plain pre/code.

    When ``code_component`` (or a per-language ``code_components`` entry) is set,
    EVERY fenced block is emitted as a component placeholder so it gets the
    terminal header + line numbers server-side.
    """
    from markupsafe import escape
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name
    from pygments.util import ClassNotFound

    # Pandoc classes may arrive as leading-dot tokens (in lang or the attrs tail):
    # _pandoc_fence_info lifts the first .class to `lang`, but a class-only block
    # (no language, e.g. `{.no-copy}`) reaches here with lang=".no-copy".
    classes: list[str] = []
    if lang and lang.startswith("."):
        classes.append(lang[1:])
        lang = ""
    for _t in (attrs or "").split():
        if _t.startswith("."):
            classes.append(_t[1:])

    file_attr = _fence_file(attrs)

    # Resolve the component for this language: per-language override, else default.
    component = ((code_components or {}).get(lang) or None) or code_component

    # Determine the highlighted body (or escaped plain text for no/unknown lang).
    if not lang:
        body = escape(code)
    elif component and lang == "tree":
        body = escape(code)  # tree listings are plain text; Tree parses them
    elif lang.lower() in ("epresso", "ep"):
        from .highlight import EpressoLexer, register

        register()
        body = highlight(code, EpressoLexer(), HtmlFormatter(nowrap=True))
    else:
        try:
            lexer = get_lexer_by_name(lang)
        except ClassNotFound:
            body = escape(code)
        else:
            body = highlight(code, lexer, HtmlFormatter(nowrap=True))

    if component:
        props = {"lang": lang, "file": file_attr}
        if classes:
            props["classes"] = " ".join(classes)
        return component_placeholder(
            component,
            props,
            _split_code_lines(body),
        )

    # Default (non-component) rendering.
    extra = (" " + " ".join(classes)) if classes else ""
    if not lang:
        if not classes:
            return f"<pre><code>{body}</code></pre>"
        return f'<pre class="highlight{escape(extra)}"><code>{body}</code></pre>'
    data = f' data-file="{escape(file_attr)}"' if file_attr else ""
    # ``highlight`` class lets the Pygments stylesheet (``pygments_css()``) match.
    return f'<pre class="highlight{escape(extra)}"{data}><code class="language-{escape(lang)}">{body}</code></pre>'


def pygments_css(theme: str = "default", selector: str = ".highlight") -> str:
    """Return the Pygments CSS for one theme (link it in your layout).

    ``selector`` lets you scope the rules (e.g. under ``html[data-theme="light"]``)
    so a light palette can be served for the light theme. Prefer
    :func:`pygments_css_pair` when a site has both palettes: it needs no scoping.
    """
    from pygments.formatters import HtmlFormatter

    return HtmlFormatter(style=theme).get_style_defs(selector)


# Colours inside a value, for pairing the light and dark palettes.
_COLOUR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\)")
_COLOUR_PROPS = {
    "color",
    "background",
    "background-color",
    "border-color",
    "border-top-color",
    "border-right-color",
    "border-bottom-color",
    "border-left-color",
    "outline",
    "outline-color",
    "text-decoration-color",
    "caret-color",
}


def _css_blocks(css: str) -> dict[str, list[tuple[str, str]]]:
    """Split Pygments' generated CSS into ``{selector: [(property, value), …]}``."""
    out: dict[str, list[tuple[str, str]]] = {}
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        decls = out.setdefault(match.group(1).strip(), [])
        for decl in match.group(2).split(";"):
            if ":" in decl:
                prop, value = decl.split(":", 1)
                decls.append((prop.strip(), value.strip()))
    return out


def _pair(prop: str, light: str, dark: str) -> str:
    """One ``light-dark()`` declaration: pair the colours, keep the rest.

    Falls back to the light value when a shorthand's colours don't line up
    (nothing to pair) — with palettes that mirror each other, as epresso's do,
    that doesn't happen.
    """
    if prop in _COLOUR_PROPS:
        return f"light-dark({light}, {dark})"
    light_colours, dark_colours = _COLOUR_RE.findall(light), _COLOUR_RE.findall(dark)
    if not light_colours or len(light_colours) != len(dark_colours):
        return light
    for light_colour, dark_colour in zip(light_colours, dark_colours, strict=True):
        light = light.replace(light_colour, f"light-dark({light_colour}, {dark_colour})", 1)
    return light


def pygments_css_pair(light: str = "default", dark: str = "default", selector: str = ".highlight") -> str:
    """Pygments CSS where every colour is ``light-dark(light, dark)``.

    One stylesheet instead of one per theme, scoped by ``html[data-theme=…]``: the
    palette follows ``color-scheme`` — the OS preference, or whatever the page
    sets — exactly like an epresso theme's own ``light-dark()`` design tokens. So
    no attribute has to be published by script, and the code palette can't drift
    from the page palette. Non-colour declarations are taken from ``light``.
    """
    light_blocks = _css_blocks(pygments_css(light, selector))
    dark_blocks = _css_blocks(pygments_css(dark, selector))
    rules = []
    for selector_text, light_decls in light_blocks.items():
        dark_decls = dict(dark_blocks.get(selector_text, []))
        body = ""
        for prop, light_value in light_decls:
            dark_value = dark_decls.get(prop)
            value = _pair(prop, light_value, dark_value) if dark_value and dark_value != light_value else light_value
            body += f"  {prop}: {value};\n"
        rules.append(f"{selector_text} {{\n{body}}}\n")
    return "\n".join(rules)



def _headings_and_images_from_tokens(tokens: list) -> tuple[list[dict[str, Any]], list[str]]:
    """Collect heading + image metadata from an already-parsed token stream.

    Runs over the same tokens the renderer renders, so the body is parsed once.
    """
    headings: list[dict[str, Any]] = []
    images: list[str] = []
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and tok.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(tok.tag[1])
            # inline token follows
            title = ""
            if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                title = tokens[i + 1].content
            slug = slugify(title)
            headings.append({"depth": level, "slug": slug, "text": title})
        if tok.type == "inline":
            for child in tok.children or []:
                if child.type == "image":
                    src = child.attrs.get("src") if child.attrs else None
                    if src:
                        images.append(str(src))
    return headings, images


def slugify(text: str) -> str:
    import re

    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug or ""


def heading_text(text: str) -> str:
    """Clean a heading's raw markdown for display: strip inline HTML/images/links."""
    text = re.sub(r"<[^>]+>", "", text)                    # inline HTML / <img>
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)   # markdown image
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # markdown link -> label
    return re.sub(r"\s+", " ", text).strip()


def first_heading(body: str) -> str | None:
    """The text of the first ``# heading`` in ``body``, or ``None``."""
    m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    return heading_text(m.group(1)) if m else None


def strip_first_h1(body: str) -> str:
    """Remove the leading ``# H1`` line from ``body``."""
    m = re.search(r"^#\s+.+\s*$", body, re.MULTILINE)
    if m:
        return body[: m.start()] + body[m.end():]
    return body


def headings(md: MarkdownIt, body: str) -> list[dict]:
    """Extract a doc's ToC headings -> ``[{depth, slug, text}]`` (text cleaned for display)."""
    tokens = md.parse(body)
    out: list[dict] = []
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and tok.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            raw = tokens[i + 1].content if (i + 1 < len(tokens) and tokens[i + 1].type == "inline") else ""
            text = heading_text(raw)
            out.append({"depth": int(tok.tag[1]), "slug": slugify(text), "text": text})
    return out


# ── Custom component tags in markdown (e.g. <Button url="…">…) ──────────────
#
# Mirrors MDX's `components` map: an allow-listed tag like <Button url="…">text
# </Button> is captured at token level (children stay real markdown tokens), and
# the renderer emits a placeholder that the site expands to the epresso component
# output at template time (when the Jinja env is available).

_COMPONENT_TAG_RE = __import__("re").compile(
    r"<(?P<name>[A-Za-z][A-Za-z0-9]*)(?P<attrs>[^>]*?)(?P<selfclose>/?)\s*>"
)


def _parse_attrs(s: str) -> dict[str, Any]:
    attrs: dict[str, Any] = {}
    for key, value in parse_jsx_attrs(s):
        attrs[key] = True if value is True else str(value)
    return attrs


def _make_component_rule(component_names: tuple[str, ...]):
    import re as _re

    names = set(component_names)

    def _rule(state, silent):
        if state.src[state.pos] != "<":
            return False
        m = _COMPONENT_TAG_RE.match(state.src, state.pos)
        if not m:
            return False
        name = m.group("name")
        if name not in names:
            return False
        attrs_str = m.group("attrs")
        selfclose = m.group("selfclose") == "/"
        if selfclose:
            inner, end = "", m.end()
        else:
            close_re = _re.compile(r"</" + _re.escape(name) + r"\s*>", _re.I)
            cm = close_re.search(state.src, m.end())
            if not cm:
                return False
            inner, end = state.src[m.end() : cm.start()], cm.end()
        if silent:
            return True
        parsed = state.md.parseInline(inner, state.env)
        # parseInline returns a single `inline` wrapper token; use its children
        if len(parsed) == 1 and parsed[0].type == "inline":
            parsed = parsed[0].children or []
        token = state.push("md_component", "", 0)
        token.meta = {"name": name, "attrs": _parse_attrs(attrs_str), "children": parsed}
        token.block = False
        state.pos = end
        return True

    return _rule


def _make_component_renderer(component_renderer, renderer):
    def _render(tokens, idx, options, env):
        meta = tokens[idx].meta
        children = renderer.renderInline(meta["children"], options, env)
        return component_renderer(meta["name"], meta["attrs"], children)

    return _render


def _make_component_fence_renderer():
    """Fence renderer that unwraps markdown-it's auto ``<pre><code>`` wrapper
    when the highlight option emitted a component placeholder (so the code
    component renders its own markup instead of being nested in ``<pre>``).
    """
    from markdown_it.renderer import RendererHTML

    default_fence = RendererHTML().fence

    def _render(tokens, idx, options, env):
        out = default_fence(tokens, idx, options, env)
        if "<!--epresso-md:" in out:
            start = out.index("<!--epresso-md:")
            end = out.rindex("</code></pre>")
            return out[start:end] + "\n"
        return out

    return _render


def _make_html_block_renderer(component_names, component_renderer, renderer):
    """Handle self-closing component tags that land in ``html_block``
    (e.g. ``<YouTube id="…"/>`` on its own line) as components."""

    names = set(component_names)

    def _render(tokens, idx, options, env):
        content = tokens[idx].content.strip()
        m = _COMPONENT_TAG_RE.match(content)
        if m and m.group("name") in names and m.group("selfclose") == "/":
            return component_renderer(m.group("name"), _parse_attrs(m.group("attrs")), "")
        # non-component html_block -> pass the raw HTML through (renderToken would
        # emit a stray "< />" for these)
        return tokens[idx].content

    return _render


def component_placeholder(name: str, attrs: dict[str, Any], children: str) -> str:
    """Emit a deterministic placeholder the site expands at template time."""
    import json

    return (
        f'<!--epresso-md:{json.dumps({"name": name, "props": attrs})}-->'
        f"{children}<!--/epresso-md-->"
    )


_MD_COMPONENT_RE = __import__("re").compile(
    r"<!--epresso-md:(\{.*?\})-->(.*?)<!--/epresso-md-->", __import__("re").S
)


def expand_placeholders(html: str, component_renderer) -> str:
    """Expand ``<!--epresso-md:{…}-->children<!--/epresso-md-->`` placeholders."""

    def _repl(m):
        import json

        meta = json.loads(m.group(1))
        return component_renderer(meta["name"], meta["props"], m.group(2))

    return _MD_COMPONENT_RE.sub(_repl, html)


def _rewrite_relative_images(html: str, base: str) -> str:
    """Prefix relative ``src="…"`` in rendered markdown with ``base``.

    Rewrites ``src="./x.jpg"`` / ``src="x.jpg"`` (no scheme, not already
    absolute) to ``src="{base}x.jpg"``. Skips external, protocol-relative,
    root-relative and data URIs.
    """
    import re

    def _repl(m: re.Match[str]) -> str:
        src = m.group(1)
        if src.startswith(("http://", "https://", "//", "data:", "#", "/")):
            return m.group(0)
        rel = src[2:] if src.startswith("./") else src
        return f'src="{base}{rel}"'

    return re.sub(r'src="([^"]+)"', _repl, html)


# ── backend dispatch ───────────────────────────────────────────────────────
#
# `[markdown] backend` selects the renderer. "native" is the pure-Python
# markdown-it-py pipeline below. "rust" is an optional accelerator that is not
# part of this distribution yet, so selecting it fails loudly instead of quietly
# rendering with a different engine (which would make builds non-reproducible).
# Registering a real backend later is one line here.
_BACKENDS: dict[str, Callable[..., _store.RenderedContent]] = {}


def _backend(name: str) -> Callable[..., _store.RenderedContent]:
    fn = _BACKENDS.get(name)
    if fn is None:
        raise ContentError(
            f"markdown backend {name!r} is not available in this installation",
            fix='install the markdown accelerator, or set [markdown] backend = "native"',
        )
    return fn


def render_markdown(
    body: str,
    config_markdown: Any,
    image_base: str | None = None,
    component_names: tuple[str, ...] = (),
    component_renderer=None,
    link_resolver=None,
) -> _store.RenderedContent:
    """Render a Markdown body through the configured backend.

    ``config_markdown.backend`` selects the renderer — ``"native"`` (the built-in
    markdown-it-py pipeline) or ``"rust"`` (the optional accelerator, which must
    be installed). Everything else is forwarded to the backend unchanged.
    """
    name = getattr(config_markdown, "backend", "native") or "native"
    return _backend(name)(
        body,
        config_markdown,
        image_base=image_base,
        component_names=component_names,
        component_renderer=component_renderer,
        link_resolver=link_resolver,
    )


def _render_native(
    body: str,
    config_markdown: Any,
    image_base: str | None = None,
    component_names: tuple[str, ...] = (),
    component_renderer=None,
    link_resolver=None,
) -> _store.RenderedContent:
    """Render a Markdown body to HTML, extracting heading + image metadata.

    ``image_base`` (optional) is a URL prefix for relative image srcs — e.g.
    ``/content/pages/community-organisers-summit/`` — so ``./photo.jpg`` in the
    source resolves to ``/content/…/photo.jpg`` (mirrors a framework's relative-image
    handling against the source content directory).

    ``component_names`` / ``component_renderer`` enable the custom-component
    pass: allow-listed tags are captured and handed to ``component_renderer``.

    ``link_resolver`` (optional) resolves GitHub/wiki-style links
    (``[[Page]]``, ``[wiki_page:Page]``, and relative ``.md`` links) to URLs.
    """
    if not body:
        return _store.RenderedContent(html="", metadata={"headings": [], "image_paths": []})
    if link_resolver is not None:
        body = _expand_wiki_links(body, link_resolver)
        body = _expand_wiki_page(body, link_resolver)
    md = _renderer(config_markdown, tuple(component_names or ()), component_renderer)
    # Normalize self-closing tags written with a space after the slash
    # ("<br/ >", "<img/ >") — markdown-it's html_inline rejects those, so they'd
    # be escaped as literal text.
    import re as _re

    body = _re.sub(r"<(\w+)\s*/\s*>", r"<\1/>", body)
    body = _apply_source_transforms(body)
    body = _apply_render_transforms(md, body, 0)
    # Parse once: render from the token stream and read heading/image metadata
    # from those same tokens, rather than parsing the body a second time.
    env: dict[str, Any] = {}
    tokens = md.parse(body, env)
    html = md.renderer.render(tokens, md.options, env)
    for _fn in _MD_HTML_POST:
        html = _fn(html)
    if image_base:
        html = _rewrite_relative_images(html, image_base.rstrip("/") + "/")
    if link_resolver is not None:
        html = _rewrite_markdown_links(html, link_resolver)
    headings, images = _headings_and_images_from_tokens(tokens)
    if headings and getattr(config_markdown, "add_slug_ids", True):
        html = _inject_heading_ids(
            html, headings, autolink=getattr(config_markdown, "autolink_headings", True)
        )
    return _store.RenderedContent(
        html=html,
        metadata={"headings": headings, "image_paths": images},
    )


_BACKENDS["native"] = _render_native


_WIKI_LINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
_WIKI_PAGE = re.compile(r"\[wiki_page:([^\]]+)\]")


def _expand_wiki_links(body: str, resolver) -> str:
    """Turn ``[[Page]]`` / ``[[Page|Label]]`` into markdown links when resolvable."""

    def _repl(m: re.Match[str]) -> str:
        page = m.group(1).strip()
        label = m.group(2)
        url = resolver.resolve(page)
        if url is None:
            return m.group(0)
        text = (label or page).strip()
        return f"[{text}]({url})"

    return _WIKI_LINK.sub(_repl, body)


def _expand_wiki_page(body: str, resolver) -> str:
    """Turn ``[wiki_page:Page]`` into a markdown link when resolvable."""

    def _repl(m: re.Match[str]) -> str:
        page = m.group(1).strip()
        url = resolver.resolve(page)
        if url is None:
            return m.group(0)
        return f"[{page}]({url})"

    return _WIKI_PAGE.sub(_repl, body)


def _rewrite_markdown_links(html: str, resolver) -> str:
    """Rewrite relative ``href`` links (``.md`` or bare page names) to resolved URLs."""

    def _repl(m: re.Match[str]) -> str:
        url = resolver.resolve(m.group(1))
        if url is None:
            return m.group(0)
        return f'href="{url}"'

    return re.sub(r'href="([^"]*)"', _repl, html)


def _inject_heading_ids(html: str, headings: list[dict], autolink: bool = False) -> str:
    """Add ``id="<slug>"`` (and, when ``autolink``, a ``#`` anchor link) to each heading.

    The ``headings`` list is produced by :func:`_headings_and_images_from_tokens` in
    document order; slugs are generated with :func:`slugify`. This powers
    in-page tables of contents (``[\u2191](\u2191)`` anchors). Headings that
    already carry an ``id`` are left untouched. ``autolink`` wraps each heading in
    a GitHub-style ``#`` link (shown on hover via CSS).
    """
    import re as _re

    if not headings:
        return html
    idx = 0

    def _repl(m: _re.Match[str]) -> str:
        nonlocal idx
        if idx >= len(headings):
            return m.group(0)
        tag, attrs, content = m.group(1), m.group(2), m.group(3)
        slug = headings[idx].get("slug", "")
        idx += 1
        if not slug or "id=" in attrs:
            return m.group(0)
        anchor = (
            f'<a class="heading-anchor" href="#{slug}" '
            f'aria-label="Link to this section"><span aria-hidden="true">#</span></a>'
            if autolink
            else ""
        )
        return f'<h{tag} id="{slug}"{attrs}>{anchor}{content}</h{tag}>'

    return _re.sub(r"<h([1-6])([^>]*)>(.*?)</h\1>", _repl, html, flags=_re.DOTALL)
