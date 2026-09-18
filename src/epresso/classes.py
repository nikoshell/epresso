"""cn() — merge utility class lists, last conflicting utility wins.

A dependency-free stand-in for `tailwind-merge` / rust-ui's `tw_merge!`, used in
component bodies::

    <button class="{{ cn('px-4 py-2 bg-primary', props.class_name) }}">

The rule for grouping is: **one group per CSS property**. Two utilities may only
be merged when they set the same property, and a shorthand (``p-4``) also removes
the longhands it overrides (``px-6``). Merging anything else silently deletes a
class the author wrote, which is the failure mode this file exists to prevent:

* ``text-2xs text-foreground`` — different properties (size vs colour)
* ``flex-1 flex-col`` — different properties (flex vs flex-direction)
* ``top-0 right-0`` — different properties
* ``outline-2 outline-offset-2 outline-ring`` — the same three-property mistake

Anything not in the table is never merged. An unrecognised utility is kept, so
the worst case is a duplicate that the engine resolves by source order — never a
dropped declaration.

Run the self-check with ``python -m epresso.classes``.
"""

from __future__ import annotations

import re

# ── (pattern, group) — first match wins, so specific rules come first ────────
_RULES: tuple[tuple[str, str], ...] = tuple(
    (rf"(?:{p})", g)
    for p, g in (
        # ── display / position ────────────────────────────────────────────
        (r"block|inline|inline-block|inline-flex|flex|grid|inline-grid|inline-table|flow-root|contents|hidden|list-item|table-cell|table-row|table-caption", "display"),
        (r"static|fixed|absolute|relative|sticky", "position"),
        # `collapse` is Tailwind's `visibility: collapse`, but it is also daisyUI's
        # disclosure component — merging it away would delete the component, so only
        # the two names daisyUI does not use are treated as utilities. `table` and
        # `select-*` collide the same way (display / user-select), so both are dropped
        # from their groups above and below.
        (r"visible|invisible", "visibility"),
        (r"isolate|isolation-auto", "isolation"),
        (r"float-(?:start|end|right|left|none)", "float"),
        (r"clear-(?:start|end|left|right|both|none)", "clear"),
        # ── flex ──────────────────────────────────────────────────────────
        (r"flex-(?:row|row-reverse|col|col-reverse)", "flex-direction"),
        (r"flex-(?:wrap|wrap-reverse|nowrap)", "flex-wrap"),
        (r"flex-(?:grow|grow-0)", "flex-grow"),
        (r"flex-(?:shrink|shrink-0)", "flex-shrink"),
        (r"flex-(?:\d+|auto|initial|none|\[[^\]]*\])", "flex"),
        (r"grow(?:-0)?", "flex-grow"),
        (r"shrink(?:-0)?", "flex-shrink"),
        (r"basis-.*", "flex-basis"),
        (r"order-(?:first|last|none|\d+|\[[^\]]*\])", "order"),
        # ── grid ──────────────────────────────────────────────────────────
        (r"grid-cols-.*", "grid-template-columns"),
        (r"grid-rows-.*", "grid-template-rows"),
        (r"grid-flow-.*", "grid-auto-flow"),
        (r"auto-cols-.*", "grid-auto-columns"),
        (r"auto-rows-.*", "grid-auto-rows"),
        (r"col-span-.*", "grid-column"),
        (r"col-start-.*", "grid-column-start"),
        (r"col-end-.*", "grid-column-end"),
        (r"row-span-.*", "grid-row"),
        (r"row-start-.*", "grid-row-start"),
        (r"row-end-.*", "grid-row-end"),
        (r"place-items-.*", "place-items"),
        (r"place-content-.*", "place-content"),
        (r"place-self-.*", "place-self"),
        (r"items-.*", "align-items"),
        (r"justify-items-.*", "justify-items"),
        (r"justify-self-.*", "justify-self"),
        (r"self-.*", "align-self"),
        (r"justify-.*", "justify-content"),
        (r"content-(?:normal|center|start|end|between|around|evenly|baseline|stretch)", "align-content"),
        # ── spacing / sizing ──────────────────────────────────────────────
        (r"p-.*", "padding"),
        (r"px-.*", "padding-inline"),
        (r"py-.*", "padding-block"),
        (r"pt-.*", "padding-top"),
        (r"pr-.*", "padding-right"),
        (r"pb-.*", "padding-bottom"),
        (r"pl-.*", "padding-left"),
        (r"ps-.*", "padding-inline-start"),
        (r"pe-.*", "padding-inline-end"),
        (r"m-.*", "margin"),
        (r"mx-.*", "margin-inline"),
        (r"my-.*", "margin-block"),
        (r"mt-.*", "margin-top"),
        (r"mr-.*", "margin-right"),
        (r"mb-.*", "margin-bottom"),
        (r"ml-.*", "margin-left"),
        (r"ms-.*", "margin-inline-start"),
        (r"me-.*", "margin-inline-end"),
        (r"space-x-.*", "space-x"),
        (r"space-y-.*", "space-y"),
        (r"gap-x-.*", "column-gap"),
        (r"gap-y-.*", "row-gap"),
        (r"gap-.*", "gap"),
        (r"size-.*", "size"),
        (r"w-.*", "width"),
        (r"min-w-.*", "min-width"),
        (r"max-w-.*", "max-width"),
        (r"h-.*", "height"),
        (r"min-h-.*", "min-height"),
        (r"max-h-.*", "max-height"),
        (r"aspect-.*", "aspect-ratio"),
        # ── inset ─────────────────────────────────────────────────────────
        (r"inset-x-.*", "inset-inline"),
        (r"inset-y-.*", "inset-block"),
        (r"inset-.*", "inset"),
        (r"top-.*", "top"),
        (r"right-.*", "right"),
        (r"bottom-.*", "bottom"),
        (r"left-.*", "left"),
        (r"start-.*", "inset-inline-start"),
        (r"end-.*", "inset-inline-end"),
        (r"z-.*", "z-index"),
        # ── border: width, style, colour, radius ──────────────────────────
        (r"rounded-ss(?:-.*)?", "border-radius-ss"),
        (r"rounded-se(?:-.*)?", "border-radius-se"),
        (r"rounded-es(?:-.*)?", "border-radius-es"),
        (r"rounded-ee(?:-.*)?", "border-radius-ee"),
        (r"rounded-tl(?:-.*)?", "border-radius-tl"),
        (r"rounded-tr(?:-.*)?", "border-radius-tr"),
        (r"rounded-br(?:-.*)?", "border-radius-br"),
        (r"rounded-bl(?:-.*)?", "border-radius-bl"),
        (r"rounded-t(?:-.*)?", "border-radius-t"),
        (r"rounded-r(?:-.*)?", "border-radius-r"),
        (r"rounded-b(?:-.*)?", "border-radius-b"),
        (r"rounded-l(?:-.*)?", "border-radius-l"),
        (r"rounded-s(?:-.*)?", "border-radius-s"),
        (r"rounded-e(?:-.*)?", "border-radius-e"),
        (r"rounded(?:-.*)?", "border-radius"),
        (r"border-x(?:-(?:\d+|\[[^\]]*\])|)", "border-inline-width"),
        (r"border-y(?:-(?:\d+|\[[^\]]*\])|)", "border-block-width"),
        (r"border-t(?:-(?:\d+|\[[^\]]*\])|)", "border-top-width"),
        (r"border-r(?:-(?:\d+|\[[^\]]*\])|)", "border-right-width"),
        (r"border-b(?:-(?:\d+|\[[^\]]*\])|)", "border-bottom-width"),
        (r"border-l(?:-(?:\d+|\[[^\]]*\])|)", "border-left-width"),
        (r"border-s(?:-(?:\d+|\[[^\]]*\])|)", "border-inline-start-width"),
        (r"border-e(?:-(?:\d+|\[[^\]]*\])|)", "border-inline-end-width"),
        (r"border(?:-(?:\d+|\[[^\]]*\])|)", "border-width"),
        (r"border-(?:solid|dashed|dotted|double|hidden|none)", "border-style"),
        (r"border-x-(?:solid|dashed|dotted|double|hidden|none)", "border-inline-style"),
        (r"border-y-(?:solid|dashed|dotted|double|hidden|none)", "border-block-style"),
        (r"border-t-(?:solid|dashed|dotted|double|hidden|none)", "border-top-style"),
        (r"border-r-(?:solid|dashed|dotted|double|hidden|none)", "border-right-style"),
        (r"border-b-(?:solid|dashed|dotted|double|hidden|none)", "border-bottom-style"),
        (r"border-l-(?:solid|dashed|dotted|double|hidden|none)", "border-left-style"),
        (r"border-x-.*", "border-inline-color"),
        (r"border-y-.*", "border-block-color"),
        (r"border-t-.*", "border-top-color"),
        (r"border-r-.*", "border-right-color"),
        (r"border-b-.*", "border-bottom-color"),
        (r"border-l-.*", "border-left-color"),
        (r"border-s-.*", "border-inline-start-color"),
        (r"border-e-.*", "border-inline-end-color"),
        (r"border-.*", "border-color"),
        (r"divide-x.*", "divide-x-width"),
        (r"divide-y.*", "divide-y-width"),
        (r"divide-.*", "divide-color"),
        (r"border-collapse|border-separate", "border-collapse"),
        # ── outline / ring ────────────────────────────────────────────────
        (r"outline-offset-.*", "outline-offset"),
        (r"outline-(?:none|hidden|solid|dashed|dotted|double)", "outline-style"),
        (r"outline(?:-(?:\d+|\[[^\]]*\]))?", "outline-width"),
        (r"outline-.*", "outline-color"),
        (r"ring-offset-(?:\d+|\[[^\]]*\])", "ring-offset-width"),
        (r"ring-offset-.*", "ring-offset-color"),
        (r"ring-inset", "ring-inset"),
        (r"ring(?:-(?:\d+|\[[^\]]*\]))?", "ring-width"),
        (r"ring-.*", "ring-color"),
        # ── typography ────────────────────────────────────────────────────
        (r"text-(?:2xs|xs|sm|base|lg|xl|\d+xl|\[[^\]]*\])", "text-size"),
        (r"text-(?:left|center|right|justify|start|end)", "text-align"),
        (r"text-(?:wrap|nowrap|balance|pretty)", "text-wrap"),
        (r"text-(?:ellipsis|clip)", "text-overflow"),
        # Only colours we can name: the previous catch-all (`text-.*`) also swallowed
        # daisyUI *component* classes — `cn("text-rotate", "text-primary")` deleted
        # `text-rotate`, so `<TextRotate class_name="text-primary">` lost its own base
        # class. An unrecognised `text-<something>` is now left alone (it may be a
        # component class, and not merging is recoverable where deleting is not).
        (r"text-(?:primary|secondary|accent|neutral|info|success|warning|error|base-content|-?content|current|inherit|transparent|black|white)(?:-content)?", "text-color"),
        (r"text-\[[^\]]*\]", "text-color"),
        (r"font-(?:thin|extralight|light|normal|medium|semibold|bold|extrabold|black|\[[^\]]*\])", "font-weight"),
        (r"font-(?:sans|serif|mono|\[[^\]]*\])", "font-family"),
        (r"font-(?:italic|not-italic)", "font-style"),
        (r"font-stretch-.*", "font-stretch"),
        (r"tabular-nums|proportional-nums|diagonal-fractions|stacked-fractions|oldstyle-nums|lining-nums|ordinal|slashed-zero", "font-variant-numeric"),
        (r"leading-.*", "line-height"),
        (r"tracking-.*", "letter-spacing"),
        (r"line-clamp-.*", "line-clamp"),
        (r"indent-.*", "text-indent"),
        (r"align-.*", "vertical-align"),
        (r"whitespace-.*", "white-space"),
        (r"break-(?:normal|words|all|keep)", "word-break"),
        (r"hyphens-.*", "hyphens"),
        (r"truncate|text-truncate", "text-truncate"),
        (r"underline-offset-.*", "text-underline-offset"),
        (r"decoration-(?:\d+|auto|from-font|\[[^\]]*\])", "text-decoration-thickness"),
        (r"decoration-(?:solid|double|dotted|dashed|wavy)", "text-decoration-style"),
        (r"decoration-.*", "text-decoration-color"),
        (r"underline|overline|line-through|no-underline", "text-decoration-line"),
        (r"uppercase|lowercase|capitalize|normal-case", "text-transform"),
        (r"list-(?:disc|decimal|none|\[[^\]]*\])", "list-style-type"),
        (r"list-(?:inside|outside)", "list-style-position"),
        # ── paint ─────────────────────────────────────────────────────────
        (r"bg-none|bg-gradient-.*|bg-\[url\([^\]]*\)\]", "background-image"),
        (r"bg-clip-.*", "background-clip"),
        (r"bg-origin-.*", "background-origin"),
        (r"bg-(?:fixed|local|scroll)", "background-attachment"),
        (r"bg-(?:repeat|no-repeat|repeat-x|repeat-y|repeat-round|repeat-space)", "background-repeat"),
        (r"bg-(?:auto|cover|contain)", "background-size"),
        (r"bg-(?:bottom|center|left|right|top|left-bottom|left-top|right-bottom|right-top)", "background-position"),
        (r"bg-.*", "background-color"),
        (r"fill-.*", "fill"),
        (r"stroke-(?:\d+|\[[^\]]*\])", "stroke-width"),
        (r"stroke-.*", "stroke"),
        (r"(?:backdrop-)?drop-shadow-.*", "drop-shadow"),
        (r"shadow.*", "box-shadow"),
        (r"opacity-.*", "opacity"),
        (r"mix-blend-.*", "mix-blend-mode"),
        (r"bg-blend-.*", "background-blend-mode"),
        (r"blur-.*", "filter-blur"),
        (r"brightness-.*", "filter-brightness"),
        (r"contrast-.*", "filter-contrast"),
        (r"grayscale.*", "filter-grayscale"),
        (r"hue-rotate-.*", "filter-hue-rotate"),
        (r"invert.*", "filter-invert"),
        (r"saturate-.*", "filter-saturate"),
        (r"sepia.*", "filter-sepia"),
        (r"backdrop-.*", "backdrop-filter"),
        # ── transforms ────────────────────────────────────────────────────
        (r"scale-x-.*", "scale-x"),
        (r"scale-y-.*", "scale-y"),
        (r"scale-.*", "scale"),
        (r"rotate-.*", "rotate"),
        (r"translate-x-.*", "translate-x"),
        (r"translate-y-.*", "translate-y"),
        (r"skew-x-.*", "skew-x"),
        (r"skew-y-.*", "skew-y"),
        (r"origin-.*", "transform-origin"),
        (r"transform.*", "transform"),
        # ── transitions / animation ───────────────────────────────────────
        (r"transition-.*|transition", "transition-property"),
        (r"duration-.*", "transition-duration"),
        (r"ease-.*", "transition-timing-function"),
        (r"delay-.*", "transition-delay"),
        (r"animate-.*", "animation"),
        # ── misc interaction ──────────────────────────────────────────────
        (r"overflow-x-.*", "overflow-x"),
        (r"overflow-y-.*", "overflow-y"),
        (r"overflow-.*", "overflow"),
        (r"overscroll-x-.*", "overscroll-behavior-x"),
        (r"overscroll-y-.*", "overscroll-behavior-y"),
        (r"object-(?:contain|cover|fill|none|scale-down)", "object-fit"),
        (r"object-.*", "object-position"),
        (r"cursor-.*", "cursor"),
        (r"pointer-events-.*", "pointer-events"),
        (r"select-(?:none|text|all|auto)", "user-select"),
        (r"resize.*", "resize"),
        (r"appearance-.*", "appearance"),
        (r"accent-.*", "accent-color"),
        (r"caret-.*", "caret-color"),
        (r"snap-.*", "scroll-snap-type"),
        (r"scroll-(?:auto|smooth)", "scroll-behavior"),
        (r"scroll-m[xytbrl]?-.*", "scroll-margin"),
        (r"scroll-p[xytbrl]?-.*", "scroll-padding"),
        (r"touch-.*", "touch-action"),
        (r"table-(?:auto|fixed)", "table-layout"),
        (r"caption-(?:top|bottom)", "caption-side"),
    )
)
_COMPILED = tuple((re.compile(rf"^(?:{p})$"), g) for p, g in _RULES)

# A shorthand removes the longhands it covers (parent → children).
_CONFLICTS: dict[str, tuple[str, ...]] = {
    "size": ("size", "width", "height"),
    "width": ("width", "size"),
    "height": ("height", "size"),
    "padding": ("padding", "padding-inline", "padding-block", "padding-top", "padding-right", "padding-bottom", "padding-left", "padding-inline-start", "padding-inline-end"),
    "padding-inline": ("padding-inline", "padding-left", "padding-right", "padding-inline-start", "padding-inline-end"),
    "padding-block": ("padding-block", "padding-top", "padding-bottom"),
    "margin": ("margin", "margin-inline", "margin-block", "margin-top", "margin-right", "margin-bottom", "margin-left", "margin-inline-start", "margin-inline-end"),
    "margin-inline": ("margin-inline", "margin-left", "margin-right", "margin-inline-start", "margin-inline-end"),
    "margin-block": ("margin-block", "margin-top", "margin-bottom"),
    "gap": ("gap", "column-gap", "row-gap"),
    "inset": ("inset", "inset-inline", "inset-block", "top", "right", "bottom", "left", "inset-inline-start", "inset-inline-end"),
    "inset-inline": ("inset-inline", "left", "right", "inset-inline-start", "inset-inline-end"),
    "inset-block": ("inset-block", "top", "bottom"),
    "border-width": ("border-width", "border-inline-width", "border-block-width", "border-top-width", "border-right-width", "border-bottom-width", "border-left-width", "border-inline-start-width", "border-inline-end-width"),
    "border-inline-width": ("border-inline-width", "border-left-width", "border-right-width", "border-inline-start-width", "border-inline-end-width"),
    "border-block-width": ("border-block-width", "border-top-width", "border-bottom-width"),
    "border-style": ("border-style", "border-inline-style", "border-block-style", "border-top-style", "border-right-style", "border-bottom-style", "border-left-style"),
    "border-color": ("border-color", "border-inline-color", "border-block-color", "border-top-color", "border-right-color", "border-bottom-color", "border-left-color", "border-inline-start-color", "border-inline-end-color"),
    "border-radius": ("border-radius", "border-radius-t", "border-radius-r", "border-radius-b", "border-radius-l",
                      "border-radius-s", "border-radius-e", "border-radius-tl", "border-radius-tr",
                      "border-radius-br", "border-radius-bl", "border-radius-ss", "border-radius-se",
                      "border-radius-es", "border-radius-ee"),
    "border-radius-t": ("border-radius-t", "border-radius-tl", "border-radius-tr"),
    "border-radius-r": ("border-radius-r", "border-radius-tr", "border-radius-br"),
    "border-radius-b": ("border-radius-b", "border-radius-br", "border-radius-bl"),
    "border-radius-l": ("border-radius-l", "border-radius-tl", "border-radius-bl"),
    "outline-width": ("outline-width",),
    "ring-color": ("ring-color",),
    "shadow": ("box-shadow",),
}

# `[&_svg:not([class*='size-'])]:` and friends — any run of bracket-aware segments
# ending in a colon at bracket depth 0.
_SEGMENT = r"(?:[^:\[\]]|\[[^\]]*\])*"


def _split(token: str) -> tuple[str, str]:
    """Return ``(variant_prefix, base_class)`` — uses the *last* depth-0 colon."""
    depth = 0
    cut = -1
    for i, ch in enumerate(token):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth = max(0, depth - 1)
        elif ch == ":" and depth == 0:
            cut = i
    if cut < 0:
        return "", token
    return token[: cut + 1], token[cut + 1 :]


def _group(base: str) -> str | None:
    for pattern, group in _COMPILED:
        if pattern.match(base):
            return group
    return None


def cn(*classes: object) -> str:
    """Join truthy class fragments, keeping the last of each conflicting group."""
    tokens: list[str] = []
    for fragment in classes:
        if fragment:
            tokens.extend(str(fragment).split())

    out: dict[str, str] = {}
    for i, token in enumerate(tokens):
        variants, base = _split(token)
        group = _group(base)
        if group is None:
            # Unknown utilities are never merged: the ordinal keeps its own slot.
            out[f"{variants}__none_{i}"] = token
            continue
        for victim in _CONFLICTS.get(group, (group,)):
            out.pop(f"{variants}{victim}", None)
        out[f"{variants}{group}"] = token
    return " ".join(out.values())


def main() -> int:
    # ── must merge: same property ────────────────────────────────────────
    assert cn("p-4", "p-8") == "p-8"
    assert cn("px-4 py-2", "px-8") == "py-2 px-8"
    assert cn("bg-primary", "bg-red-500") == "bg-red-500"
    assert cn("bg-surface/60", "bg-transparent") == "bg-transparent"
    assert cn("text-sm", "text-lg") == "text-lg"
    assert cn("rounded-md", "rounded-[4px]") == "rounded-[4px]"
    assert cn("shadow-sm", "shadow-none") == "shadow-none"
    assert cn("opacity-50", "opacity-100") == "opacity-100"
    assert cn("dark:bg-a/30", "dark:bg-b/30") == "dark:bg-b/30"
    assert cn("size-4", "size-9") == "size-9"
    assert cn("[&>svg]:size-4", "size-9") == "[&>svg]:size-4 size-9"
    assert cn("[&_svg]:size-4", "[&_svg]:size-6") == "[&_svg]:size-6"
    assert cn("w-4", "w-8") == "w-8"
    assert cn("", None, "p-1", False) == "p-1"

    # ── must merge: shorthand removes the longhand it covers ─────────────
    assert cn("w-fit size-9") == "size-9"
    assert cn("size-9 w-fit") == "w-fit"
    assert cn("h-9 size-6") == "size-6"
    assert cn("px-4", "p-6") == "p-6"
    assert cn("py-2 px-3", "p-5") == "p-5"
    assert cn("top-0 left-0", "inset-4") == "inset-4"
    assert cn("rounded-t-lg", "rounded-lg") == "rounded-lg"

    # ── must NOT merge: different properties that share a prefix ─────────
    assert cn("text-2xs", "text-foreground") == "text-2xs text-foreground"
    assert cn("text-xs", "text-2xs") == "text-2xs"          # both font-size
    assert cn("flex-1", "flex-col") == "flex-1 flex-col"
    assert cn("flex", "hidden") == "hidden"                 # display: last wins
    assert cn("inline-flex", "grid") == "grid"
    assert cn("top-0", "right-0") == "top-0 right-0"
    assert cn("inset-x-0", "inset-y-2") == "inset-x-0 inset-y-2"
    assert cn("border", "border-t-2") == "border border-t-2"
    assert cn("border-2", "border-t") == "border-2 border-t"
    assert cn("border-b-2", "border-b-4") == "border-b-4"
    assert cn("border-b-2", "border-t-2") == "border-b-2 border-t-2"
    assert cn("border-dashed", "border-t-solid") == "border-dashed border-t-solid"
    assert cn("border-border", "border-t-red-500") == "border-border border-t-red-500"
    assert cn("ring-inset", "ring-2") == "ring-inset ring-2"
    assert cn("stroke-2", "stroke-[3px]") == "stroke-[3px]"
    assert cn("origin-center", "transform") == "origin-center transform"
    assert cn("overflow-x-auto", "overflow-y-hidden") == "overflow-x-auto overflow-y-hidden"
    assert cn("outline-2", "outline-offset-2", "outline-ring") == "outline-2 outline-offset-2 outline-ring"
    assert cn("outline-2", "outline-none") == "outline-2 outline-none"
    assert cn("ring-2", "ring-red-500", "ring-offset-2") == "ring-2 ring-red-500 ring-offset-2"
    assert cn("active:translate-x-0", "active:translate-y-0") == "active:translate-x-0 active:translate-y-0"
    assert cn("translate-x-4", "translate-y-2") == "translate-x-4 translate-y-2"
    assert cn("scale-x-50", "scale-y-100") == "scale-x-50 scale-y-100"
    assert cn("col-span-2", "col-start-3") == "col-span-2 col-start-3"
    assert cn("rounded-t-lg", "rounded-b-lg") == "rounded-t-lg rounded-b-lg"
    assert cn("gap-2", "gap-x-4") == "gap-2 gap-x-4"
    assert cn("border-solid", "border-2") == "border-solid border-2"
    assert cn("overflow-hidden", "overflow-x-auto") == "overflow-hidden overflow-x-auto"
    assert cn("bg-primary", "text-primary-foreground") == "bg-primary text-primary-foreground"
    assert cn("min-w-0", "w-full") == "min-w-0 w-full"
    assert cn("bg-cover", "bg-primary") == "bg-cover bg-primary"
    assert cn("transition-colors", "duration-150") == "transition-colors duration-150"
    assert cn("leading-none", "tracking-wide") == "leading-none tracking-wide"
    assert cn("stroke-2", "stroke-current") == "stroke-2 stroke-current"
    print("cn(): all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
