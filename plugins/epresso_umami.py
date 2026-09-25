"""Bundled epresso plugin: Umami analytics.

Injects the Umami tracking snippet into ``<head>`` of every rendered page:

    <script defer src="https://cloud.umami.is/script.js"
            data-website-id="…"></script>

Enable it from a project's ``site.toml`` and supply the website id through the
environment — it is public (it ships in the page), but keeping it out of the
tree lets the same source build with and without analytics:

    plugins = ["epresso_umami"]

    # real env, or .env.<env> with EPRESSO_ENV=<env>
    UMAMI_WEBSITE_ID=00000000-0000-0000-0000-000000000000

Self-hosted Umami:

    UMAMI_SCRIPT_URL=https://umami.example.com/script.js

With no ``UMAMI_WEBSITE_ID`` the plugin is a no-op, so it is safe to list
unconditionally (local dev and preview deploys stay un-tracked).
"""

from __future__ import annotations

import html
import os

from epresso.plugins import Plugin

DEFAULT_SCRIPT_URL = "https://cloud.umami.is/script.js"


def epresso_umami() -> Plugin:
    """Return a ``Plugin`` that injects the Umami tracking snippet."""

    def on_setup(caps):
        website_id = os.environ.get("UMAMI_WEBSITE_ID", "").strip()
        if not website_id:
            caps.logger.debug("UMAMI_WEBSITE_ID not set; no analytics snippet injected")
            return
        src = os.environ.get("UMAMI_SCRIPT_URL", "").strip() or DEFAULT_SCRIPT_URL
        caps.inject_head(
            f'<script defer src="{html.escape(src, quote=True)}" '
            f'data-website-id="{html.escape(website_id, quote=True)}"></script>'
        )

    return Plugin(name="epresso_umami", hooks={"on_setup": on_setup})


# Module-level instance so ``[plugins] = ["epresso_umami"]`` auto-discovers it.
umami = epresso_umami()
