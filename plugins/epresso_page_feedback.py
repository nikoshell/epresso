"""Bundled epresso plugin: an Umami-backed "Was this page helpful?" widget.

Renders a small yes/no widget at the bottom of every doc page and records each
vote as an Umami custom event:

    umami.track('page-feedback', { helpful: 'yes' | 'no', page: '/…' })

It activates only when analytics is configured — i.e. when ``UMAMI_WEBSITE_ID``
is set, the same switch that enables the ``epresso_umami`` plugin — so list both
together:

    plugins = ["epresso_umami", "epresso_page_feedback"]

Set ``PAGE_FEEDBACK=off`` in an environment to keep analytics but drop the
widget. With no ``UMAMI_WEBSITE_ID`` the plugin is a no-op, so it is safe to list
unconditionally (local dev and preview deploys stay un-tracked).

Votes are remembered per page in ``localStorage`` (key
``epresso-feedback:<path>``), so a reader is asked once; revisits show the thanks
state. The event uses the JS API rather than ``data-umami-event`` attributes
because Umami suppresses a ``data-umami-event`` element's other listeners, and
this needs its own click handler.

No theme edits: the markup, CSS and script are injected via
``caps.transform_html``, which lands the widget just before the closing
``</article>`` of routes that carry a page slug.
"""

from __future__ import annotations

import os

from epresso.plugins import Plugin

EVENT = "page-feedback"
MARKER = "data-page-feedback"
_CONTAINER = 'class="page-feedback"'
DISABLE_ENV = "PAGE_FEEDBACK"
_OFF = {"0", "false", "off", "no"}

_STYLE = """<style>
.page-feedback {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-md);
    margin-top: var(--space-2xl);
    padding-top: var(--space-lg);
    color: var(--muted);
    font-size: 0.92rem;
}

/* The container sets `display: flex`, which would beat the UA's [hidden]. */
.page-feedback[hidden],
.page-feedback-ask[hidden] {
    display: none;
}

.page-feedback-ask {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-md);
    margin: auto;
}

.page-feedback-q {
    margin: 0;
    color: var(--ink);
    font-weight: 500;
}

.page-feedback-actions {
    display: flex;
    gap: var(--space-sm);
}

.page-feedback-btn {
    font: inherit;
    padding: 0.35rem 0.8rem;
    border: 1px solid var(--line);
    border-radius: var(--radius-sm);
    background: var(--surface);
    color: var(--ink);
    cursor: pointer;
    transition: border-color var(--dur-fast) var(--ease), background var(--dur-fast) var(--ease);
}

.page-feedback-btn:hover {
    border-color: var(--accent);
}

.page-feedback-btn:active {
    transform: translateY(1px);
}

.page-feedback-thanks {
    margin: 0;
}
</style>"""

_MARKUP = f"""<div class="page-feedback" {MARKER} hidden>
    <div class="page-feedback-ask">
        <p class="page-feedback-q">Was this page helpful?</p>
        <div class="page-feedback-actions">
            <button type="button" class="page-feedback-btn" data-feedback="yes">👍 Yes</button>
            <button type="button" class="page-feedback-btn" data-feedback="no">👎 No</button>
        </div>
    </div>
    <p class="page-feedback-thanks" aria-live="polite"></p>
</div>"""

_SCRIPT = """<script>
(function () {
    "use strict";
    var KEY = "epresso-feedback:";
    var EVENT = "page-feedback";
    var THANKS = "Thanks for the feedback.";

    function read(key) {
        try { return localStorage.getItem(key); } catch (e) { return null; }
    }

    function write(key, value) {
        try { localStorage.setItem(key, value); } catch (e) { /* private mode */ }
    }

    function showThanks(el) {
        var ask = el.querySelector(".page-feedback-ask");
        var thanks = el.querySelector(".page-feedback-thanks");
        if (ask) ask.hidden = true;
        if (thanks) thanks.textContent = THANKS;
        el.dataset.voted = "1";
    }

    function reveal() {
        var el = document.querySelector("[data-page-feedback]");
        if (!el) return;
        if (read(KEY + location.pathname)) showThanks(el);
        el.hidden = false;
    }

    document.addEventListener("click", function (e) {
        var btn = e.target && e.target.closest ? e.target.closest("[data-feedback]") : null;
        if (!btn) return;
        var el = btn.closest(".page-feedback");
        if (!el || el.dataset.voted) return;
        var helpful = btn.getAttribute("data-feedback");
        if (window.umami && typeof window.umami.track === "function") {
            window.umami.track(EVENT, { helpful: helpful, page: location.pathname });
        }
        write(KEY + location.pathname, helpful);
        showThanks(el);
    });

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", reveal);
    else reveal();
})();
</script>"""


def _enabled() -> bool:
    """True only when analytics is on and the widget has not been switched off."""
    if not os.environ.get("UMAMI_WEBSITE_ID", "").strip():
        return False
    return os.environ.get(DISABLE_ENV, "").strip().lower() not in _OFF


def _inject(html: str, ctx: dict) -> str:
    """Insert the widget on a doc page; leave every other page untouched."""
    if not _enabled() or not ctx.get("params", {}).get("slug"):
        return html
    if _CONTAINER in html or "</head>" not in html:
        return html
    html = html.replace("</head>", _STYLE + _SCRIPT + "</head>", 1)
    end = html.rfind("</article>")
    if end == -1:
        return html
    return html[:end] + _MARKUP + html[end:]


def epresso_page_feedback() -> Plugin:
    """Return a ``Plugin`` that renders the page-feedback widget."""

    def on_setup(caps):
        caps.transform_html(_inject)

    return Plugin(name="epresso_page_feedback", hooks={"on_setup": on_setup})


# Module-level instance so ``[plugins] = ["epresso_page_feedback"]`` auto-discovers it.
feedback = epresso_page_feedback()
