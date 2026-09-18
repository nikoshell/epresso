"""Variant — declare a prop's class mapping once, resolve it generically.

The authoring API is the `Annotated` metadata: a prop says which values it accepts
and what each one renders as, and the resolver turns the model into one class
string. There are no per-component ``size_class`` / ``shape_class`` helpers.

    from typing import Annotated

    from _lib.variants import Variant, VariantProps

    VARIANT = Variant({"default": "", "primary": "btn-primary", "error": "btn-error"})

    class Props(VariantProps):
        base: ClassVar[str] = "btn"                        # invariant classes
        variant: Annotated[VARIANT.literal(), VARIANT] = "default"
        label: str = ""

and the body is then just::

    <button class="{{ props.classes }}">{{ props.label }}</button>

``VARIANT.literal()`` builds the ``Literal[...]`` **from the mapping's keys**, so the
accepted values cannot drift from the classes they resolve to — the split you get
from hand-writing a shared ``Literal`` and a separate map is that a component
silently accepts a value it never maps (and renders nothing). Pydantic still
validates, so a bad value stays a build-time error.

``classes`` is a pydantic ``computed_field``, not a plain ``@property``: epresso
hands the template ``Props.model_dump()`` (``components.py``), and ``model_dump``
includes computed fields but not properties. A plain ``@property`` renders empty.
Use the bare ``@computed_field`` — pydantic wraps the method into a property itself,
so a trailing ``@property`` is redundant — and never put ``@property`` *above* it,
which silently leaves a plain property that ``model_dump`` drops.

The order inside ``classes`` is: ``base``, then the variants **in field-declaration
order**, then ``extra_classes()``, then ``class_name``. ``cn`` only merges utilities
it can attribute to a CSS property, so a later fragment wins a real conflict (``p-4``
beats ``p-2``) while daisyUI component modifiers like ``btn-sm``/``btn-lg`` are simply
both emitted — the same behaviour the old per-component ``cn(...)`` calls had.

Run the self-check with ``python -m epresso.variants``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from pydantic import BaseModel, Field, computed_field

from .classes import cn  # re-exported: components import {Variant, VariantProps, cn}

if TYPE_CHECKING:
    from markupsafe import Markup


def spread(attrs: dict[str, str] | None) -> Markup:
    """``attrs`` -> `` minlength="8" pattern="…"``, for the ``attrs`` escape hatch.

    The typed props say what a component *means*; this carries what daisyUI's own markup has
    that no prop covers — validation attributes (``minlength``, ``pattern``), ``popovertarget``,
    ``tabindex``. Keys are emitted as given, values are escaped, and an empty value becomes a
    bare attribute (``popover``, not ``popover=""``).

    Registered as the ``spread`` template global, so a body reads::

        <button class="{{ props.classes }}"{{ spread(props.attrs) }}>
    """
    from markupsafe import Markup, escape

    parts = []
    for key, value in (attrs or {}).items():
        if value is None or value == "":
            parts.append(f" {key}")
        else:
            parts.append(f' {key}="{escape(str(value))}"')
    return Markup("".join(parts))


__all__ = ["Variant", "VariantProps", "cn", "resolve_variants", "spread"]


class Variant:
    """A prop's value → class mapping.

    Built from a mapping and/or keywords (``Variant({"2xl": "text-2xl"})``,
    ``Variant(sm="btn-sm")``); keys that are not identifiers need the mapping form.
    An unmapped value resolves to ``""`` rather than raising, so a value that is
    legal for a shared type but meaningless for this component renders nothing
    instead of a stray class.
    """

    def __init__(self, values: dict[str, str] | None = None, /, **keywords: str) -> None:
        self.values: dict[str, str] = {**(values or {}), **keywords}

    def resolve(self, value: str | None) -> str:
        if value is None:
            return ""
        return self.values.get(value, "")

    def __getitem__(self, value: str) -> str:
        """Mapping access, so a template can still write ``SIZE[props.size]``.

        Unlike :meth:`resolve` an unknown key raises, which is what you want in a
        body: a ``Literal`` derived from :meth:`literal` makes it unreachable, and
        anything else is a bug worth seeing rather than silently dropping a class.
        """
        return self.values[value]

    def keys(self):
        return self.values.keys()

    def literal(self) -> object:
        """``Literal[...]`` of this mapping's keys."""
        return Literal[tuple(self.values)]

    def __repr__(self) -> str:  # keeps assertion failures readable
        return f"Variant({self.values!r})"


def resolve_variants(props: BaseModel) -> dict[str, str]:
    """Every ``Annotated[..., Variant]`` field of ``props``, resolved to a class.

    Reads pydantic's already-resolved ``model_fields`` metadata instead of
    ``get_type_hints``: component frontmatter is ``exec``'d into a bare namespace
    (``components.py``), so re-resolving annotations means guessing where the names
    came from, and this runs on every render. Field order is preserved, which is
    what makes the composed class string deterministic.
    """
    resolved: dict[str, str] = {}
    for name, field in type(props).model_fields.items():
        variant = next((meta for meta in field.metadata if isinstance(meta, Variant)), None)
        if variant is not None:
            resolved[name] = variant.resolve(getattr(props, name))
    return resolved


class VariantProps(BaseModel):
    """Base model for a component whose modifiers come from variant metadata.

    Subclasses set ``base`` and declare ``Annotated[..., Variant]`` fields; the
    template reads ``props.classes``.
    """

    base: ClassVar[str] = ""
    class_name: str = ""
    # Extra attributes for the element the component renders, for what daisyUI's markup needs
    # and no typed prop covers (`minlength`, `pattern`, `popovertarget`, `tabindex`, …).
    # Templates emit them with `spread(props.attrs)`; keys are literal, values are escaped.
    attrs: dict[str, str] = Field(default_factory=dict)

    def root_variants(self) -> list[str]:
        """Variant classes for the root element — every variant field, in order.

        Override when some variants belong to an inner element instead (a Chat's
        bubble, an Avatar's media box): those stay out of ``classes`` and are either
        put on that element directly or exposed as a second computed field.
        """
        return [c for c in resolve_variants(self).values() if c]

    def extra_classes(self) -> str:
        """Component-specific classes appended after the variants (e.g. state)."""
        return ""

    @computed_field
    def classes(self) -> str:
        return cn(self.base, *self.root_variants(), self.extra_classes(), self.class_name)


def main() -> int:
    from typing import Annotated, get_args

    from pydantic import ValidationError

    # ── Variant.resolve ──────────────────────────────────────────────────
    v = Variant({"default": "", "2xl": "text-2xl"}, sm="btn-sm", lg="btn-lg")
    assert v.resolve("2xl") == "text-2xl", v
    assert v.resolve("lg") == "btn-lg", v
    assert v.resolve("default") == "", v
    assert v.resolve(None) == "", v
    assert v.resolve("nope") == "", v  # unknown -> nothing, never a stray class
    assert list(Variant({"a": "x", "b": "y"}).values) == ["a", "b"]  # order preserved

    # ── mapping access (a body may still write ``SIZE[props.size]``) ──────
    assert v["lg"] == "btn-lg" and v["default"] == "", v
    try:
        v["nope"]
    except KeyError:
        pass
    else:
        raise AssertionError("__getitem__ should raise on an unmapped key")
    assert list(v.keys()) == ["default", "2xl", "sm", "lg"], list(v.keys())

    # ── literal() drives validation ──────────────────────────────────────
    assert get_args(Variant({"a": "1", "b": "2"}).literal()) == ("a", "b")
    assert get_args(v.literal()) == ("default", "2xl", "sm", "lg")

    class M(VariantProps):
        base: ClassVar[str] = "btn"
        variant: Annotated[v.literal(), v] = "default"  # pyright: ignore[reportInvalidTypeForm]

    assert M(variant="lg").classes == "btn btn-lg", M(variant="lg").classes
    assert M().classes == "btn", M().classes
    try:
        _ = M(variant="nope").classes
    except ValidationError:
        pass
    else:
        raise AssertionError("unknown variant value should not validate")

    # ── composition order: base, variants in declaration order, extra, class_name ──
    A = Variant({"default": "", "primary": "btn-primary"})
    B = Variant({"default": "", "wide": "btn-wide"})
    C = Variant({"default": "", "sm": "btn-sm", "lg": "btn-lg"})

    class Ordered(VariantProps):
        base: ClassVar[str] = "btn"
        variant: Annotated[A.literal(), A] = "default"  # pyright: ignore[reportInvalidTypeForm]
        shape: Annotated[B.literal(), B] = "default"  # pyright: ignore[reportInvalidTypeForm]
        size: Annotated[C.literal(), C] = "default"  # pyright: ignore[reportInvalidTypeForm]

        def extra_classes(self) -> str:
            return "btn-disabled"

    got = Ordered(variant="primary", shape="wide", size="lg", class_name="mt-4").classes
    assert got == "btn btn-primary btn-wide btn-lg btn-disabled mt-4", got
    # class_name is appended last, so it wins conflicts cn can attribute to a property
    got = Ordered(class_name="p-4 p-2").classes
    assert got == "btn btn-disabled p-2", got
    got = Ordered(size="sm", class_name="mt-4").classes
    assert got == "btn btn-sm btn-disabled mt-4", got
    assert Ordered().classes == "btn btn-disabled", Ordered().classes

    # ── root_variants() keeps an inner element's variants off the root ────
    class Inner(VariantProps):
        base: ClassVar[str] = "chat"
        side: Annotated[A.literal(), A] = "default"  # pyright: ignore[reportInvalidTypeForm]
        bubble: Annotated[B.literal(), B] = "default"  # pyright: ignore[reportInvalidTypeForm]

        def root_variants(self) -> list[str]:
            return [resolve_variants(self)["side"]]

    got = Inner(side="primary", bubble="wide").classes
    assert got == "chat btn-primary", got
    # ...while the inner element can still read its own variant
    assert Inner(bubble="wide").bubble == "wide", Inner(bubble="wide").bubble

    # ── a component with no Variant fields still works ───────────────────
    class Plain(VariantProps):
        base: ClassVar[str] = "avatar"
        label: str = ""

    assert Plain(class_name="m-1").classes == "avatar m-1", Plain(class_name="m-1").classes

    # ── model_dump carries `classes` (a plain @property would not) ───────
    assert "classes" in M(variant="lg").model_dump(), M(variant="lg").model_dump()

    # ── spread: attrs render as attributes, escaped, empty as bare ───────
    assert str(spread({"min": "1", "disabled": ""})) == ' min="1" disabled', spread({"min": "1", "disabled": ""})
    assert str(spread({"title": 'a "b"'})) == ' title="a &#34;b&#34;"', spread({"title": 'a "b"'})
    assert str(spread(None)) == "", spread(None)
    assert str(spread({})) == "", spread({})

    print("✓ variants: resolve, literal-driven validation, order, class_name wins, computed_field, spread")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
