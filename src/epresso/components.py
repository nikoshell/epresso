"""Component system — server-rendered, tag-based components.

``{% component "Name", key=value %}`body`{% endcomponent %}`` renders a
component with the given kwargs plus ``content`` (the rendered body) and the
curated globals.

A component is resolved as ``templates/components/<Name>.ep`` first, then
``templates/components/<Name>.html``.

``.ep`` components are single files with a Python frontmatter (``--- … ---``)
that may declare a strict Pydantic ``Props`` model and/or a ``props()`` helper,
plus a Jinja body. Props are validated against the model, so no unvalidated
kwargs reach the template. A ``<style>`` block in the body is extracted and
scoped to the component's rendered output.

``.html`` components are plain Jinja templates (backwards compatible).
"""

from __future__ import annotations

import contextvars
import re
from pathlib import Path
from types import CodeType
from typing import Any

from jinja2 import nodes
from jinja2.ext import Extension
from markupsafe import Markup

from .errors import TemplateError

# Parse + compiled-template cache for .ep components: keyed by
# (path, mtime, env id) so repeated instances (e.g. one per code block) don't
# re-read/exec/compile the component. mtime makes it dev-safe.
_COMPONENT_CACHE: dict[tuple[str, float, int], tuple[str, str, str, str, str, CodeType | None, Any]] = {}
# Resolved-component cache: name -> (path, kind), keyed by (name, env id).
_RESOLVE_CACHE: dict[tuple[str, int], tuple[Path, str] | None] = {}


def _scope_hash(name: str) -> str:
    import hashlib

    return hashlib.sha1(("component:" + name).encode()).hexdigest()[:8]


# ---- author-scope tracking (an element is scoped to its author) ----------
# An element's scope is the component whose template *authored* it, not the one
# that renders it. A render-scope stack tracks the component currently emitting
# markup; when a `{% component %}` block captures its caller body, that body is
# tagged with the top-of-stack (author) scope before being handed to the child,
# so a receiver never re-stamps caller-authored content.
_AUTHOR_SCOPE: contextvars.ContextVar[list[str] | None] = contextvars.ContextVar(
    "epresso_author_scope", default=None
)


def _push_author(scope: str) -> None:
    cur = _AUTHOR_SCOPE.get()
    if cur is None:
        cur = []
        _AUTHOR_SCOPE.set(cur)
    cur.append(scope)


def _pop_author() -> None:
    cur = _AUTHOR_SCOPE.get()
    if cur:
        cur.pop()


def _current_author() -> str | None:
    cur = _AUTHOR_SCOPE.get()
    return cur[-1] if cur else None





def _resolve_component(env: Any, name: str) -> tuple[Path, str] | None:
    """Cached component resolution (scans are avoided on repeated renders)."""
    key = (name, id(env))
    hit = _RESOLVE_CACHE.get(key)
    if key in _RESOLVE_CACHE:
        return hit
    result = _resolve_component_uncached(env, name)
    if len(_RESOLVE_CACHE) >= 1000:
        _RESOLVE_CACHE.clear()
    _RESOLVE_CACHE[key] = result
    return result


def _resolve_component_uncached(env: Any, name: str) -> tuple[Path, str] | None:
    """Return (path, kind) for a component, or None. kind in {'epresso','html'}.

    Searches the top-level ``components/`` and ``layouts/`` dirs (the default
    structure) plus the legacy ``templates/components`` + ``templates/layouts``
    subdirs for back-compat.
    """
    from jinja2 import ChoiceLoader

    site = env.globals.get("site")
    comp_roots: list[Path] = []
    layout_roots: list[Path] = []
    if site is not None:
        comp_roots.append(site.config.dir_components())
        layout_roots.append(site.config.dir_layouts())

    loader = env.loader
    searchpaths: list[Path] = []
    if isinstance(loader, ChoiceLoader):
        for sub in loader.loaders:
            sp = getattr(sub, "searchpath", None)
            if sp:
                searchpaths.extend(Path(p) for p in sp)
    elif loader is not None:
        sp = getattr(loader, "searchpath", None)
        if sp:
            searchpaths.extend(Path(p) for p in sp)
    for base in searchpaths:
        comp_roots.append(base / "components")
        layout_roots.append(base / "layouts")

    # 1) components/ roots
    for root in comp_roots:
        if not root.exists():
            continue
        for ext, kind in ((".ep", "epresso"), (".html", "html")):
            p = root / f"{name}{ext}"
            if p.is_file():
                return p, kind
    # 2) layouts/ roots (layout components, e.g. <BaseLayout>)
    for root in layout_roots:
        if not root.exists():
            continue
        for ext, kind in ((".ep", "epresso"), (".html", "html")):
            p = root / f"{name}{ext}"
            if p.is_file():
                return p, kind
    # 3) fallback: md/ wrappers + recursive basename (components/ui/Button.ep)
    for root in comp_roots:
        md_p = root / "md" / f"{name}.ep"
        if md_p.is_file():
            return md_p, "epresso"
    for root in comp_roots:
        if not root.exists():
            continue
        for kind, ext in (("epresso", ".ep"), ("html", ".html")):
            try:
                matches = [p for p in root.rglob(f"*{ext}") if p.stem == name]
            except OSError:
                continue
            if matches:
                return matches[0], kind
    return None


_FRAGMENT_OPEN = re.compile(r"<\s*Fragment\b([^>]*?)>", re.IGNORECASE | re.DOTALL)
_FRAGMENT_CLOSE = re.compile(r"</\s*Fragment\s*>", re.IGNORECASE)


def _find_fragment_close(text: str, start: int) -> tuple[int, int] | None:
    """Return (start, end) of the ``</Fragment>`` matching the ``<Fragment>`` that
    ends at ``start``, accounting for nested Fragments."""
    depth = 1
    i = start
    while i < len(text):
        mo = _FRAGMENT_OPEN.search(text, i)
        mc = _FRAGMENT_CLOSE.search(text, i)
        if mo is None and mc is None:
            return None
        if mo is not None and (mc is None or mo.start() < mc.start()):
            depth += 1
            i = mo.end()
        else:
            assert mc is not None
            depth -= 1
            if depth == 0:
                return mc.start(), mc.end()
            i = mc.end()
    return None


def _extract_slots(content: str) -> tuple[str, dict[str, str]]:
    """Split rendered children into a default slot (``content``) plus named slots.

    Each ``<Fragment slot="name">…</Fragment>`` child contributes its inner HTML to
    ``slots[name]`` and is removed from the default ``content`` — mirroring
    named slots. ``<Fragment>`` blocks without a ``slot`` attribute are
    left untouched.
    """
    slots: dict[str, str] = {}
    out: list[str] = []
    i = 0
    n = len(content)
    while i < n:
        m = _FRAGMENT_OPEN.search(content, i)
        if m is None:
            out.append(content[i:])
            break
        sm = re.search(r'\bslot\s*=\s*["\']([^"\']+)["\']', m.group(1))
        if sm is None:
            out.append(content[i : m.end()])
            i = m.end()
            continue
        close = _find_fragment_close(content, m.end())
        if close is None:
            out.append(content[i : m.end()])
            i = m.end()
            continue
        cstart, cend = close
        slots[sm.group(1)] = content[m.end() : cstart]
        # keep the default content *before* this named-slot fragment (drop the
        # fragment itself), so text interleaved between fragments is preserved.
        out.append(content[i : m.start()])
        i = cend
    return "".join(out), slots


def _expand_slots(body: str) -> str:
    """Expand ``<slot />`` / ``<slot name="X" />`` template tags.

    ``<slot />`` renders the default slot (``content``); ``<slot name="X" />``
    renders the named slot (``slot('X')``). A non-empty body between the open
    and close tag is used as fallback when the slot is empty.

    Requires ``content`` / ``slot()`` in the render context — i.e. inside a
    component (or a layout rendered via ``{% component %}`).
    """

    # named slot with fallback content
    def _named_fallback(m: re.Match[str]) -> str:
        name, fallback = m.group(1), m.group(2)
        return f"{{% if slot({name!r}) %}}{{{{ slot({name!r}) | safe }}}}{{% else %}}{fallback}{{% endif %}}"

    body = re.sub(
        r'<slot\s+name\s*=\s*["\']([^"\']+)["\']\s*>([\s\S]*?)</slot>',
        _named_fallback,
        body,
    )
    # self-closing named slot
    body = re.sub(
        r'<slot\s+name\s*=\s*["\']([^"\']+)["\']\s*/>',
        lambda m: f"{{{{ slot({m.group(1)!r}) | safe }}}}",
        body,
    )
    # default slot with fallback content
    body = re.sub(
        r"<slot\s*>([\s\S]*?)</slot>",
        lambda m: f"{{% if content %}}{{{{ content | safe }}}}{{% else %}}{m.group(1)}{{% endif %}}",
        body,
    )
    # self-closing default slot
    body = re.sub(r"<slot\s*/>", "{{ content | safe }}", body)
    return body


def _parse_component(path: Path, environment: Any):
    """Parse a .ep component once per (path, mtime, env) and cache it.

    Returns ``(frontmatter, body, scoped_css, scripts, global_css, fm_code,
    compiled)`` where ``fm_code`` is the compiled (not executed) frontmatter and
    ``compiled`` is the pre-compiled Jinja body template. The frontmatter is only
    *compiled* here so syntax errors surface at parse time; it is *executed* per
    render in :func:`_render_epresso_component` with ``site``/``props`` in scope
    because it may compute values from the current site.
    """
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0.0
    key = (str(path), mtime, id(environment))
    hit = _COMPONENT_CACHE.get(key)
    if hit is not None:
        return hit
    from .document import parse_document
    from .enforce import ensure_components

    doc = parse_document(path.read_text(encoding="utf-8"), "ep")
    ensure_components(doc.body, label=str(path))
    frontmatter, body, scoped_css, scripts, global_css = (
        doc.frontmatter,
        doc.body,
        doc.scoped_css,
        doc.scripts,
        doc.global_css,
    )
    fm_code = None
    if frontmatter.strip():
        try:
            fm_code = compile(frontmatter, str(path), "exec")
        except Exception as e:  # noqa: BLE001
            raise TemplateError(f"error in component {path.name!r} frontmatter: {e}") from e
    compiled = environment.from_string(_expand_slots(body))
    parsed = (frontmatter, body, scoped_css, scripts, global_css, fm_code, compiled)
    if len(_COMPONENT_CACHE) >= 500:
        _COMPONENT_CACHE.clear()
    _COMPONENT_CACHE[key] = parsed
    return parsed


def _render_epresso_component(
    site: Any, session: Any, name: str, path: Path, content: str, kwargs: dict[str, Any], environment: Any
) -> str:
    _frontmatter, _body, scoped_css, scripts, global_css, fm_code, compiled = _parse_component(path, environment)
    # Execute the frontmatter per render with `site` and the raw
    # passed props in scope, so components can compute values (e.g. config
    # lookups) at the top level and reference them straight in the body.
    namespace: dict[str, Any] = {"site": site, "props": dict(kwargs)}
    if fm_code is not None:
        try:
            exec(fm_code, namespace)
        except Exception as e:  # noqa: BLE001
            raise TemplateError(f"error in component {name!r} frontmatter: {e}") from e

    props_model = namespace.get("Props")
    props = dict(kwargs)
    if props_model is not None:
        try:
            validated = props_model.model_validate(props)
        except Exception as e:  # noqa: BLE001
            raise TemplateError(f"invalid props for component {name!r}: {e}") from e
        props = validated.model_dump()

    # A component is scoped only when it declares a scoped <style>: it is then
    # wrapped in a `data-epresso-*` div and its selectors are rewritten. A
    # component with no scoped CSS (or only <style is:global>) renders unscoped —
    # no wrapper. Use <style is:global> or linked CSS for layout shells and other
    # global styles.
    content_str, slots = _extract_slots(content)
    slots = {k: Markup(v) for k, v in slots.items()}
    scope = _scope_hash(name)
    ctx: dict[str, Any] = {
        # backward-compat: expose raw kwargs at top level (as .html components
        # did), plus the new validated ``props`` dict and curated globals.
        # Globals are spread FIRST so that explicit component props override
        # them — e.g. a ``url`` prop must shadow the curated ``url()`` global
        # method, otherwise ``{{ url }}`` renders the method repr.
        **environment.globals,
        **kwargs,
        "site": site,
        "props": props,
        "content": Markup(content_str),
        "slots": slots,
        "slot": lambda name: slots.get(name, Markup("")),
    }
    # Expose frontmatter top-level names (helpers/constants/computed values) to
    # the template body, so e.g. a ``render_tree`` helper or a ``base`` value is
    # usable as ``{{ render_tree(content) }}`` / ``{{ base }}``.
    for _k, _v in namespace.items():
        if _k in ("Props", "site", "props") or _k.startswith("_"):
            continue
        ctx.setdefault(_k, _v)
    _push_author(scope)
    try:
        try:
            html = compiled.render(**ctx)
        except Exception as e:  # noqa: BLE001
            raise TemplateError(f"error rendering component {name!r}: {e}") from e

        if scoped_css.strip():
            rendered_css = environment.from_string(scoped_css).render(**ctx)
            session.add_scoped_css(scope, rendered_css)
            from .scoped import inject_scope_attr

            html = inject_scope_attr(html, scope)
        if global_css.strip():
            rendered = environment.from_string(global_css).render(**ctx)
            style = session.dedup_global_css(rendered)
            if style:
                # Global CSS lands in the <head> for full-document components (layout
                # shells), so a <style is:global> in a layout emits valid HTML; for
                # leaf components it is inlined at the component's position.
                if "</head>" in html:
                    html = html.replace("</head>", style + "</head>", 1)
                else:
                    html = f"{style}{html}"
        if scripts.strip():
            session.add_script(scripts)
    finally:
        _pop_author()
    return html


def _render_component(environment: Any, name: str, content: str, kwargs: dict[str, Any]) -> str:
    site = environment.globals.get("site")
    session = environment.globals.get("_render_session")
    resolved = _resolve_component(environment, name)
    if resolved is None:
        raise TemplateError(f"component {name!r} not found (expected templates/components/{name}.ep or .html)")
    path, kind = resolved
    if kind == "epresso":
        return _render_epresso_component(site, session, name, path, content, kwargs, environment)
    # plain .html component
    tmpl_name = f"components/{name}.html"
    content_str, slots = _extract_slots(content)
    slots = {k: Markup(v) for k, v in slots.items()}
    ctx: dict[str, Any] = {
        **kwargs,
        "content": Markup(content_str),
        "slots": slots,
        "slot": lambda name: slots.get(name, Markup("")),
    }
    if site is not None:
        ctx["site"] = site
    try:
        return environment.get_template(tmpl_name).render(**ctx)
    except Exception as e:  # noqa: BLE001
        raise TemplateError(f"error rendering component {name!r}: {e}") from e


class ComponentExtension(Extension):
    """Jinja tag: ``{% component "Card", title=x %}…{% endcomponent %}``."""

    tags = {"component"}

    def parse(self, parser):  # noqa: D102
        lineno = next(parser.stream).lineno
        name = parser.parse_primary()
        # consume the comma separating the name from the first kwarg
        parser.stream.skip_if("comma")
        kwargs: list[nodes.Keyword] = []
        while parser.stream.current.type != "block_end":
            key = parser.parse_assign_target(name_only=True)
            parser.stream.expect("assign")
            value = parser.parse_expression()
            kwargs.append(nodes.Keyword(key.name, value, lineno=value.lineno))
            parser.stream.skip_if("comma")
        body = parser.parse_statements(("name:endcomponent",), drop_needle=True)
        call = self.call_method("_render", [name], kwargs=kwargs)
        node = nodes.CallBlock(call, [], [], body)
        node.set_lineno(lineno)
        return node

    def _render(self, name, caller, **kwargs):  # noqa: ANN001
        content = Markup(caller()) if caller else Markup("")
        # Caller body is authored by the template currently rendering (top of the
        # author stack); tag it with that scope so the receiving component never
        # re-stamps it (author scoping). Nested component output is already
        # scoped and is skipped.
        author = _current_author()
        if author and content:
            from .scoped import inject_scope_attr

            content = Markup(inject_scope_attr(str(content), author))
        return _render_component(self.environment, name, content, kwargs)


def install(env: Any) -> None:
    """Register the component extension on a Jinja environment."""
    env.add_extension(ComponentExtension)
