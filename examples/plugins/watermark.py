"""Example plugin: stamp every code block with a "Made by epresso" pill.

Demonstrates an *html transform* — a pure function ``fn(html, ctx) -> html`` run
over every rendered page. Where a project might add a "copy" button after each
``<pre>``, this transform instead appends a quiet credit pill inside the block,
reusing the same ``transform_html`` capability.
"""

from epresso.plugins import Plugin


def watermark(*, text: str = "Made by epresso") -> Plugin:
    """Append a ``.epresso-mark`` credit pill to every ``<pre>`` on the page."""

    def on_setup(caps):
        def transform(html: str, ctx: dict) -> str:
            if "</pre>" not in html or "epresso-mark" in html:
                return html  # idempotent: never double-stamp
            pill = f'<span class="epresso-mark">{text}</span>'
            return html.replace("</pre>", pill + "</pre>")

        caps.transform_html(transform)

    return Plugin(name="watermark", hooks={"on_setup": on_setup})
